from __future__ import annotations

import time
import uuid
from typing import AsyncIterator

from .base import (
    AgentChatMessage,
    AgentChatRequest,
    AgentCommand,
    AgentSessionInfo,
    AgentStreamEvent,
    BaseAgentEngine,
)
from .context import NoOpAgentContextMaterializer
from .gateway import WrightGatewayProfile, build_wright_gateway_args


class OpenClawStubEngine(BaseAgentEngine):
    """Offline-safe placeholder engine for the future OpenClaw provider."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path
        self._sessions: dict[str, AgentSessionInfo] = {}

    async def check_health(self) -> dict:
        return {
            "state": "disconnected",
            "latencyMs": 0.0,
            "error": "OpenClaw provider is a stub in this build.",
        }

    async def create_session(
        self, workspace: str | None = None, instructions: str | None = None
    ) -> AgentSessionInfo:
        now = int(time.time())
        session = AgentSessionInfo(
            session_id=f"openclaw-stub-{uuid.uuid4()}",
            title="OpenClaw Stub Session",
            created_at=now,
            updated_at=now,
            message_count=0,
            workspace=workspace,
        )
        self._sessions[session.session_id] = session
        return session

    async def list_sessions(self) -> list[AgentSessionInfo]:
        return list(self._sessions.values())

    async def delete_session(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None

    async def stream_chat(
        self, request: AgentChatRequest
    ) -> AsyncIterator[AgentStreamEvent]:
        yield AgentStreamEvent(
            type="error",
            data={"message": "OpenClaw provider is a stub in this build."},
        )

    async def get_session_workspace(self, session_id: str) -> str | None:
        session = self._sessions.get(session_id)
        return session.workspace if session else None

    async def save_context(self, session_id: str, workspace_id: str) -> bool:
        return True

    async def load_context(self, session_id: str, workspace_id: str) -> dict | None:
        return None

    async def get_chat_history(self, session_id: str) -> list[AgentChatMessage]:
        return []

    async def get_commands(self) -> list[AgentCommand]:
        return []


def openclaw_wright_gateway_profile(repo_dir: str) -> WrightGatewayProfile:
    return WrightGatewayProfile(
        provider_name="openclaw",
        server_name="wright-gateway",
        command="uv",
        args=build_wright_gateway_args(repo_dir),
        terminal_cwd=repo_dir,
    )


def openclaw_context_materializer() -> NoOpAgentContextMaterializer:
    return NoOpAgentContextMaterializer(provider_id="openclaw", support_level="stub")
