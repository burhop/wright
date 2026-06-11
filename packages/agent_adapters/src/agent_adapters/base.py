from abc import ABC, abstractmethod
from typing import AsyncIterator
from dataclasses import dataclass


@dataclass
class AgentStreamEvent:
    """A single event from an agent response stream."""

    type: str  # "token" | "tool" | "stream_end" | "error"
    data: dict  # Event-specific payload


@dataclass
class AgentChatRequest:
    """Request to send a message to an agent."""

    session_id: str
    message: str
    trace_id: str | None = None
    attachments: list[str] | None = None


@dataclass
class AgentCommand:
    """A command provided by the agent engine."""

    name: str
    description: str




@dataclass
class AgentSessionInfo:
    """Summary of an agent session."""

    session_id: str
    title: str
    created_at: int
    updated_at: int
    message_count: int
    workspace: str | None = None


@dataclass
class AgentChatMessage:
    """A single chat message from an agent session's history."""

    id: str
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: int  # epoch ms
    trace_id: str | None = None


class BaseAgentEngine(ABC):
    """Abstract base for all agent adapters (Constitution §2)."""

    @abstractmethod
    async def check_health(self) -> dict:
        """Return {"state": "connected"|"disconnected", "latencyMs": float}."""
        pass

    @abstractmethod
    async def create_session(
        self, workspace: str | None = None, instructions: str | None = None
    ) -> AgentSessionInfo:
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
    async def stream_chat(
        self, request: AgentChatRequest
    ) -> AsyncIterator[AgentStreamEvent]:
        """Send a message and stream back the agent's response.

        This is a unified operation: it sends the user message to the
        agent backend and yields SSE events as they arrive. There is
        no separate start/stream handoff.

        Adapters map their backend's streaming format to AgentStreamEvent:
        - "token": text content delta
        - "tool": tool invocation (name, args, call_id)
        - "progress": tool execution progress (tool name, status, label)
        - "stream_end": response complete
        - "error": error occurred
        """
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

    @abstractmethod
    async def get_chat_history(self, session_id: str) -> list["AgentChatMessage"]:
        """Retrieve the full chat message history for a session.

        Each agent backend is responsible for persisting its own chat history.
        Returns a list of AgentChatMessage ordered by timestamp.
        """
        pass

    @abstractmethod
    async def get_commands(self) -> list[AgentCommand]:
        """Retrieve the available slash commands from the agent engine."""
        pass

    async def cancel_chat(self, session_id: str) -> bool:
        """Cancel an active response stream. Returns True if successfully accepted."""
        return False
