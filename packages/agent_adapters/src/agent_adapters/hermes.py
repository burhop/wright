import os
import time
import json
from typing import AsyncIterator
import httpx
from httpx_sse import aconnect_sse
import structlog

from .base import (
    BaseAgentEngine,
    AgentStreamEvent,
    AgentChatRequest,
    AgentSessionInfo,
    AgentChatMessage,
    AgentCommand,
)

logger = structlog.get_logger(__name__)


class HermesAdapter(BaseAgentEngine):
    """Concrete implementation of BaseAgentEngine that proxies to Hermes Native API (Constitution §2)."""

    def __init__(self, base_url: str, api_key: str, db_path: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.db_path = db_path
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self._active_clients = {}  # session_id -> httpx.AsyncClient

    async def check_health(self) -> dict:
        """Return {"state": "connected"|"disconnected", "latencyMs": float}."""
        import asyncio
        start_time = time.perf_counter()
        for attempt in range(2):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/health",
                        headers=self.headers,
                        timeout=5.0
                    )
                    latency = (time.perf_counter() - start_time) * 1000.0
                    if response.status_code == 200:
                        return {"state": "connected", "latencyMs": latency}
            except Exception as e:
                logger.debug("Hermes health check attempt %d failed: %s", attempt + 1, e)
            if attempt == 0:
                await asyncio.sleep(0.5)
        return {"state": "disconnected", "latencyMs": 0.0}

    def _to_epoch_ms(self, val) -> int:
        if not val:
            return 0
        if val < 10000000000:  # Seconds to milliseconds
            return int(val * 1000)
        return int(val)

    def _get_workspace_from_db(self, session_id: str) -> str | None:
        if not self.db_path or not os.path.exists(self.db_path):
            return None
        import sqlite3
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT local_path FROM engineering_workspaces WHERE session_id = ?",
                (session_id,),
            )
            row = cursor.fetchone()
            conn.close()
            if row:
                return row["local_path"]
        except Exception as e:
            logger.debug("Failed to query workspace from database", session_id=session_id, error=str(e))
        return None

    async def create_session(
        self, workspace: str | None = None, instructions: str | None = None
    ) -> AgentSessionInfo:
        """Create a new agent session."""
        async with httpx.AsyncClient() as client:
            payload = {}
            if workspace:
                payload["workspace"] = workspace
            if instructions:
                # Standard OpenAI system message import for native API
                payload["instructions"] = instructions

            response = await client.post(
                f"{self.base_url}/api/sessions",
                json=payload,
                headers=self.headers,
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            # Support both direct return or nested 'session' key if wrapper exists
            session = data.get("session", data)
            session_id = session.get("session_id", session.get("id"))
            return AgentSessionInfo(
                session_id=session_id,
                title=session.get("title") or "Untitled",
                created_at=self._to_epoch_ms(session.get("created_at", 0)),
                updated_at=self._to_epoch_ms(session.get("updated_at", 0)),
                message_count=session.get("message_count", 0),
                workspace=workspace or self._get_workspace_from_db(session_id),
            )

    async def list_sessions(self) -> list[AgentSessionInfo]:
        """List all sessions for this adapter's profile."""
        import asyncio
        for attempt in range(2):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/api/sessions",
                        headers=self.headers,
                        timeout=10.0,
                    )
                    response.raise_for_status()
                    data = response.json()
                    sessions = data if isinstance(data, list) else (data.get("data") or data.get("sessions") or [])

                    result = []
                    for s in sessions:
                        session_id = s.get("session_id", s.get("id"))
                        if not session_id:
                            continue
                        result.append(
                            AgentSessionInfo(
                                session_id=session_id,
                                title=s.get("title") or "Untitled",
                                created_at=self._to_epoch_ms(s.get("created_at", 0)),
                                updated_at=self._to_epoch_ms(s.get("updated_at", 0)),
                                message_count=s.get("message_count", 0),
                                workspace=self._get_workspace_from_db(session_id),
                            )
                        )
                    return result
            except Exception as e:
                logger.debug("Hermes list_sessions attempt %d failed: %s", attempt + 1, e)
                if attempt == 0:
                    await asyncio.sleep(0.5)
                else:
                    raise

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session. Returns True if deleted."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/api/sessions/{session_id}",
                    headers=self.headers,
                    timeout=10.0,
                )
                return response.status_code in (200, 204)
        except Exception:
            logger.exception("Failed to delete session %s", session_id)
        return False

    async def _build_messages(self, request: AgentChatRequest) -> list[dict]:
        """Fetch chat history and append the current user message to construct messages list."""
        history = await self.get_chat_history(request.session_id)
        messages = []
        for msg in history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # Determine the workspace path for the session and prefix the user message
        workspace_path = await self.get_session_workspace(request.session_id)
        message_content = request.message
        if workspace_path:
            message_content = f"[Workspace::v1: {workspace_path}] {message_content}"

        messages.append({
            "role": "user",
            "content": message_content
        })
        return messages

    async def stream_chat(
        self, request: AgentChatRequest
    ) -> AsyncIterator[AgentStreamEvent]:
        """Stream chat via Hermes native OpenAI-compatible API."""
        messages = await self._build_messages(request)
        session_id = request.session_id

        client = httpx.AsyncClient()
        self._active_clients[session_id] = client

        try:
            headers = {**self.headers, "X-Hermes-Session-Id": session_id}
            async with aconnect_sse(
                client,
                "POST",
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": "hermes",
                    "messages": messages,
                    "stream": True,
                    "session_id": session_id,
                },
                headers=headers,
                timeout=60.0,
            ) as event_source:
                event_source.response.raise_for_status()
                async for sse in event_source.aiter_sse():
                    event_type = sse.event
                    # hermes.tool.progress custom event
                    if event_type == "hermes.tool.progress":
                        try:
                            data = json.loads(sse.data)
                            yield AgentStreamEvent(type="progress", data=data)
                        except Exception:
                            logger.warn("Failed to parse hermes.tool.progress event data", data=sse.data)
                    elif sse.data == "[DONE]":
                        yield AgentStreamEvent(type="stream_end", data={})
                    else:
                        try:
                            chunk = json.loads(sse.data)
                            choices = chunk.get("choices", [])
                            if not choices:
                                continue
                            delta = choices[0].get("delta", {})
                            if delta.get("content"):
                                yield AgentStreamEvent(type="token", data={"text": delta["content"]})
                            if delta.get("tool_calls"):
                                yield AgentStreamEvent(type="tool", data={"tool_calls": delta["tool_calls"]})
                        except Exception:
                            logger.warn("Failed to parse completion chunk data", data=sse.data)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (502, 503):
                yield AgentStreamEvent(type="error", data={"message": "LLM model unavailable"})
            else:
                yield AgentStreamEvent(
                    type="error",
                    data={"message": f"HTTP error {exc.response.status_code}: {exc.response.text}"}
                )
        except Exception as exc:
            yield AgentStreamEvent(type="error", data={"message": str(exc)})
        finally:
            self._active_clients.pop(session_id, None)
            await client.aclose()

    async def get_session_workspace(self, session_id: str) -> str | None:
        """Retrieve the workspace path for a given session ID."""
        # Query local SQLite database first
        workspace = self._get_workspace_from_db(session_id)
        if workspace:
            return workspace

        # Fallback to native sessions API
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/sessions/{session_id}",
                    headers=self.headers,
                    timeout=5.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("workspace")
        except Exception as e:
            logger.debug("Failed to query workspace for session from native API: %s", e)

        # Fallback to list
        try:
            sessions = await self.list_sessions()
            for s in sessions:
                if s.session_id == session_id:
                    return s.workspace
        except Exception:
            pass
        return None

    async def save_context(self, session_id: str, workspace_id: str) -> bool:
        """No-op for Hermes — context is persisted server-side automatically."""
        logger.debug(
            "save_context is a no-op for Hermes (session=%s, workspace=%s)",
            session_id,
            workspace_id,
        )
        return True

    async def load_context(self, session_id: str, workspace_id: str) -> dict | None:
        """No-op for Hermes — context is persisted server-side automatically."""
        logger.debug(
            "load_context is a no-op for Hermes (session=%s, workspace=%s)",
            session_id,
            workspace_id,
        )
        return None

    async def get_chat_history(self, session_id: str) -> list[AgentChatMessage]:
        """Retrieve chat history from Hermes Native API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/sessions/{session_id}/messages",
                    headers=self.headers,
                    timeout=10.0,
                )
                if response.status_code == 404:
                    logger.debug("No session/history found for session %s", session_id)
                    return []
                response.raise_for_status()
                data = response.json()
                messages = data if isinstance(data, list) else (data.get("data") or data.get("messages") or [])

                result = []
                for idx, msg in enumerate(messages):
                    role = msg.get("role", "assistant")
                    if role == "system":
                        continue

                    msg_id = msg.get("id", msg.get("message_id", ""))
                    if not msg_id:
                        msg_id = f"msg-{session_id}-{idx}"

                    content = msg.get("content", "")
                    if isinstance(content, list):
                        parts = []
                        for item in content:
                            if isinstance(item, str):
                                parts.append(item)
                            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                                parts.append(item["text"])
                        content = "".join(parts)
                    elif not isinstance(content, str):
                        content = str(content) if content is not None else ""

                    timestamp = self._to_epoch_ms(msg.get("timestamp", msg.get("created_at", 0)))

                    result.append(
                        AgentChatMessage(
                            id=msg_id,
                            role=role,
                            content=content,
                            timestamp=timestamp,
                            trace_id=msg.get("trace_id"),
                        )
                    )
                return result
        except Exception as e:
            logger.error("Failed to fetch chat history for session %s: %s", session_id, e)
            return []

    async def get_commands(self) -> list[AgentCommand]:
        """Retrieve the available slash commands from Hermes."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/commands",
                    headers=self.headers,
                    timeout=5.0,
                )
                response.raise_for_status()
                data = response.json()
                cmds = data if isinstance(data, list) else (data.get("data") or data.get("commands") or [])
                return [
                    AgentCommand(name=c["name"], description=c.get("description", ""))
                    for c in cmds
                ]
        except Exception as e:
            logger.debug("Failed to fetch commands from Hermes API, falling back to local registry file: %s", e)
            try:
                commands_path = os.path.join(os.path.dirname(__file__), "hermes-slash-commands.json")
                if os.path.exists(commands_path):
                    with open(commands_path, "r") as f:
                        data = json.load(f)
                        cmds = data.get("flat", []) if isinstance(data, dict) else data
                        return [
                            AgentCommand(name=c["name"], description=c.get("description", ""))
                            for c in cmds
                        ]
            except Exception as le:
                logger.error("Failed to load local commands fallback: %s", le)
            return []

    async def cancel_chat(self, session_id: str) -> bool:
        """Cancel an active response stream by aborting the client request."""
        client = self._active_clients.get(session_id)
        if client:
            try:
                await client.aclose()
                return True
            except Exception as e:
                logger.error("Error closing http client on cancellation", error=str(e))
        return False
