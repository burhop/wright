import time
import json
import logging
from typing import AsyncIterator
import httpx
from httpx_sse import aconnect_sse

from .base import (
    BaseAgentEngine,
    AgentStreamEvent,
    AgentChatRequest,
    AgentChatStartResponse,
    AgentSessionInfo,
    AgentChatMessage,
    AgentCommand,
)

logger = logging.getLogger(__name__)


class HermesAdapter(BaseAgentEngine):
    """Concrete implementation of BaseAgentEngine that proxies to Hermes WebUI API (Constitution §2)."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        # The 'hermes_profile' cookie ensures all requests are isolated to the 'wright' profile
        self.headers = {
            "Cookie": "hermes_profile=wright",
            "Content-Type": "application/json",
        }

    async def check_health(self) -> dict:
        """Return {"state": "connected"|"disconnected", "latencyMs": float}."""
        import asyncio
        start_time = time.perf_counter()
        for attempt in range(2):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.base_url}/health", timeout=5.0)
                    latency = (time.perf_counter() - start_time) * 1000.0
                    if response.status_code == 200:
                        return {"state": "connected", "latencyMs": latency}
            except Exception as e:
                logger.debug("Hermes health check attempt %d failed: %s", attempt + 1, e)
            if attempt == 0:
                await asyncio.sleep(0.5)
        return {"state": "disconnected", "latencyMs": 0.0}

    async def create_session(
        self, workspace: str | None = None, instructions: str | None = None
    ) -> AgentSessionInfo:
        """Create a new agent session."""
        async with httpx.AsyncClient() as client:
            if instructions:
                messages = [{"role": "system", "content": instructions}]
                payload = {
                    "title": "Untitled",
                    "workspace": workspace,
                    "messages": messages,
                }
                url = f"{self.base_url}/api/session/import"
            else:
                payload = {}
                if workspace:
                    payload["workspace"] = workspace
                url = f"{self.base_url}/api/session/new"

            response = await client.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            session = data["session"]
            return AgentSessionInfo(
                session_id=session["session_id"],
                title=session.get("title", "Untitled"),
                created_at=int(session.get("created_at", 0) * 1000),
                updated_at=int(session.get("updated_at", 0) * 1000),
                message_count=session.get("message_count", 0),
                workspace=session.get("workspace"),
            )

    async def list_sessions(self) -> list[AgentSessionInfo]:
        """List all sessions for this adapter's profile."""
        import asyncio
        for attempt in range(2):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/api/sessions?all_profiles=0",
                        headers=self.headers,
                        timeout=10.0,
                    )
                    response.raise_for_status()
                    data = response.json()
                    sessions = data.get("sessions", [])

                    result = []
                    for s in sessions:
                        result.append(
                            AgentSessionInfo(
                                session_id=s["session_id"],
                                title=s.get("title", "Untitled"),
                                created_at=int(s.get("created_at", 0) * 1000),
                                updated_at=int(s.get("updated_at", 0) * 1000),
                                message_count=s.get("message_count", 0),
                                workspace=s.get("workspace"),
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
                response = await client.post(
                    f"{self.base_url}/api/session/delete",
                    json={"session_id": session_id},
                    headers=self.headers,
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("ok", False)
        except Exception:
            logger.exception("Failed to delete session %s", session_id)
        return False

    async def start_chat(self, request: AgentChatRequest) -> AgentChatStartResponse:
        """Initiate a chat turn. Returns stream_id for SSE consumption."""
        async with httpx.AsyncClient() as client:
            payload = {
                "session_id": request.session_id,
                "message": request.message,
                "profile": "wright",
            }
            response = await client.post(
                f"{self.base_url}/api/chat/start",
                json=payload,
                headers=self.headers,
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            return AgentChatStartResponse(
                stream_id=data["stream_id"],
                session_id=data["session_id"],
            )

    async def stream_response(self, stream_id: str) -> AsyncIterator[AgentStreamEvent]:
        """Yield SSE events from the agent's response stream."""
        async with httpx.AsyncClient() as client:
            async with aconnect_sse(
                client,
                "GET",
                f"{self.base_url}/api/chat/stream?stream_id={stream_id}",
                headers=self.headers,
                timeout=60.0,
            ) as event_source:
                async for sse in event_source.aiter_sse():
                    event_type = sse.event
                    if not event_type or event_type == "heartbeat":
                        continue

                    try:
                        event_data = json.loads(sse.data)
                    except Exception:
                        event_data = {"text": sse.data}

                    # Map WebUI SSE events to Wright base AgentStreamEvents
                    if event_type == "token":
                        yield AgentStreamEvent(type="token", data=event_data)
                    elif event_type in ("tool", "tool_complete"):
                        yield AgentStreamEvent(type="tool", data=event_data)
                    elif event_type == "progress":
                        yield AgentStreamEvent(type="progress", data=event_data)
                    elif event_type in ("done", "stream_end"):
                        yield AgentStreamEvent(type="stream_end", data=event_data)
                    elif event_type in ("error", "apperror"):
                        yield AgentStreamEvent(
                            type="error",
                            data={
                                "message": event_data.get("message", "Unknown error")
                            },
                        )
                    elif event_type == "cancel":
                        yield AgentStreamEvent(
                            type="error", data={"message": "Cancelled by user"}
                        )

    async def get_session_workspace(self, session_id: str) -> str | None:
        """Retrieve the workspace path for a given session ID by querying Hermes API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/sessions?all_profiles=0",
                    headers=self.headers,
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()
                for s in data.get("sessions", []):
                    if s.get("session_id") == session_id:
                        return s.get("workspace")
        except Exception as e:
            logger.error("Failed to query workspace for session %s: %s", session_id, e)
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
        """Retrieve chat history from Hermes WebUI.

        Hermes stores all messages server-side. We query the session endpoint
        with messages=1 and map to AgentChatMessage dataclass.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/session?session_id={session_id}&messages=1",
                    headers=self.headers,
                    timeout=10.0,
                )
                if response.status_code == 404:
                    logger.debug("No session/history found for session %s", session_id)
                    return []
                response.raise_for_status()
                data = response.json()
                session_data = data.get("session", {})
                messages = session_data.get("messages", [])
                result = []
                for idx, msg in enumerate(messages):
                    role = msg.get("role", "assistant")
                    # Skip system messages from the UI display
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
                            elif isinstance(item, dict) and isinstance(
                                item.get("text"), str
                            ):
                                parts.append(item["text"])
                        content = "".join(parts)
                    elif not isinstance(content, str):
                        content = str(content) if content is not None else ""

                    timestamp_val = msg.get("timestamp", msg.get("created_at", 0))
                    # Convert to epoch ms
                    if isinstance(timestamp_val, (int, float)):
                        if timestamp_val < 10000000000:  # Seconds to milliseconds
                            timestamp = int(timestamp_val * 1000)
                        else:
                            timestamp = int(timestamp_val)
                    else:
                        timestamp = 0

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
            logger.error(
                "Failed to fetch chat history for session %s: %s", session_id, e
            )
            return []

    async def get_commands(self) -> list[AgentCommand]:
        """Retrieve the available slash commands from Hermes WebUI."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/commands",
                    headers=self.headers,
                    timeout=5.0,
                )
                response.raise_for_status()
                data = response.json()
                cmds = data.get("commands", [])
                return [
                    AgentCommand(name=c["name"], description=c.get("description", ""))
                    for c in cmds
                ]
        except Exception as e:
            logger.error("Failed to fetch commands from Hermes: %s", e)
            return []

    async def cancel_chat(self, session_id: str, stream_id: str) -> bool:
        """Cancel an active response stream by calling Hermes WebUI cancel endpoint."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/chat/cancel?stream_id={stream_id}",
                    headers=self.headers,
                    timeout=5.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("ok", False)
        except Exception as e:
            logger.error("Failed to cancel chat stream %s: %s", stream_id, e)
        return False
