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
        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health", timeout=5.0)
                latency = (time.perf_counter() - start_time) * 1000.0
                if response.status_code == 200:
                    return {"state": "connected", "latencyMs": latency}
        except Exception as e:
            logger.debug("Hermes health check failed: %s", e)
        return {"state": "disconnected", "latencyMs": 0.0}

    async def create_session(self, workspace: str | None = None) -> AgentSessionInfo:
        """Create a new agent session."""
        async with httpx.AsyncClient() as client:
            payload = {}
            if workspace:
                payload["workspace"] = workspace
            response = await client.post(
                f"{self.base_url}/api/session/new",
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
            )

    async def list_sessions(self) -> list[AgentSessionInfo]:
        """List all sessions for this adapter's profile."""
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
                    )
                )
            return result

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
                        yield AgentStreamEvent(type="error", data={"message": event_data.get("message", "Unknown error")})
                    elif event_type == "cancel":
                        yield AgentStreamEvent(type="error", data={"message": "Cancelled by user"})

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
