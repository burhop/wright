from abc import ABC, abstractmethod
from typing import AsyncIterator
from dataclasses import dataclass

@dataclass
class AgentStreamEvent:
    """A single event from an agent response stream."""
    type: str          # "token" | "tool" | "stream_end" | "error"
    data: dict         # Event-specific payload

@dataclass
class AgentChatRequest:
    """Request to send a message to an agent."""
    session_id: str
    message: str
    trace_id: str | None = None

@dataclass
class AgentChatStartResponse:
    """Response from starting a chat turn."""
    stream_id: str
    session_id: str

@dataclass
class AgentSessionInfo:
    """Summary of an agent session."""
    session_id: str
    title: str
    created_at: int
    updated_at: int
    message_count: int

class BaseAgentEngine(ABC):
    """Abstract base for all agent adapters (Constitution §2)."""

    @abstractmethod
    async def check_health(self) -> dict:
        """Return {"state": "connected"|"disconnected", "latencyMs": float}."""
        pass

    @abstractmethod
    async def create_session(self, workspace: str | None = None) -> AgentSessionInfo:
        """Create a new agent session."""
        pass

    @abstractmethod
    async def list_sessions(self) -> list[AgentSessionInfo]:
        """List all sessions for this adapter's profile."""
        pass

    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session. Returns True if deleted."""
        pass

    @abstractmethod
    async def start_chat(self, request: AgentChatRequest) -> AgentChatStartResponse:
        """Initiate a chat turn. Returns stream_id for SSE consumption."""
        pass

    @abstractmethod
    async def stream_response(self, stream_id: str) -> AsyncIterator[AgentStreamEvent]:
        """Yield SSE events from the agent's response stream."""
        pass

    @abstractmethod
    async def get_session_workspace(self, session_id: str) -> str | None:
        """Retrieve the workspace path for a given session ID."""
        pass

    @abstractmethod
    async def save_context(self, session_id: str, workspace_id: str) -> bool:
        """Save agent context for a workspace. Returns True on success."""
        pass

    @abstractmethod
    async def load_context(self, session_id: str, workspace_id: str) -> dict | None:
        """Load agent context for a workspace. Returns context dict or None."""
        pass
