from abc import ABC, abstractmethod
from typing import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
import hashlib
from typing import Any, Literal


@dataclass(frozen=True)
class AgentInvocationContext:
    """Prepared presentation role; never an implicit grant of agent tools.

    Callers retain this immutable context with every turn, including corrections.
    The first role returns source as text and has no executable tools.
    """

    role: Literal["process-ui-author"]
    version: Literal["1"]
    instructions_version: str
    instructions: str
    instructions_digest: str
    model_policy: Literal["inherit_default"] = "inherit_default"
    allowed_tools: tuple[str, ...] = ()
    expected_model_reference: str | None = None
    expected_configuration_digest: str | None = None

    def __post_init__(self):
        if (self.role, self.version, self.model_policy) != (
            "process-ui-author",
            "1",
            "inherit_default",
        ):
            raise ValueError("Unsupported invocation role or model policy")
        if (
            not isinstance(self.instructions_version, str)
            or not self.instructions_version.strip()
            or len(self.instructions_version) > 128
        ):
            raise ValueError("A bounded instructions version is required")
        if (
            not isinstance(self.instructions, str)
            or not self.instructions.strip()
            or len(self.instructions.encode("utf-8")) > 131072
        ):
            raise ValueError("Prepared instructions must contain 1–131072 bytes")
        if (
            hashlib.sha256(self.instructions.encode("utf-8")).hexdigest()
            != self.instructions_digest
        ):
            raise ValueError("Prepared instructions digest does not match")
        if self.allowed_tools != ():
            raise ValueError("The first process UI role has no executable tools")
        if (self.expected_model_reference is None) != (
            self.expected_configuration_digest is None
        ):
            raise ValueError(
                "Expected model and configuration identities must be paired"
            )
        if self.expected_model_reference is not None:
            if (
                not isinstance(self.expected_model_reference, str)
                or not self.expected_model_reference.strip()
                or len(self.expected_model_reference) > 160
            ):
                raise ValueError("Expected model identity is invalid")
            digest = self.expected_configuration_digest
            if (
                not isinstance(digest, str)
                or len(digest) != 64
                or any(char not in "0123456789abcdef" for char in digest)
            ):
                raise ValueError("Expected model configuration digest is invalid")


@dataclass(frozen=True)
class AgentInvocationCapabilities:
    """Actual adapter qualification, distinct from general chat health."""

    adapter: str
    available: bool = False
    effective_instructions_every_turn: bool = False
    no_tools: bool = False
    inherited_default_model: bool = False
    reason: str | None = None
    model_reference: str | None = None
    configuration_digest: str | None = None
    provider_reference: str | None = None
    transport: str | None = None

    def __post_init__(self):
        if not isinstance(self.adapter, str) or not self.adapter.strip():
            raise ValueError("An adapter identity is required")
        if any(
            type(value) is not bool
            for value in (
                self.available,
                self.effective_instructions_every_turn,
                self.no_tools,
                self.inherited_default_model,
            )
        ):
            raise ValueError("Invocation capability flags must be booleans")
        if self.available and not (
            self.effective_instructions_every_turn
            and self.no_tools
            and self.inherited_default_model
        ):
            raise ValueError("Authoring requires all scoped invocation capabilities")
        if not self.available and not self.reason:
            raise ValueError("Unavailable authoring requires an actionable reason")
        for value in (self.model_reference, self.provider_reference, self.transport):
            if value is not None and (
                not isinstance(value, str) or not value.strip() or len(value) > 160
            ):
                raise ValueError(
                    "Invocation metadata must use bounded public identifiers"
                )
        if self.configuration_digest is not None and (
            not isinstance(self.configuration_digest, str)
            or len(self.configuration_digest) != 64
            or any(char not in "0123456789abcdef" for char in self.configuration_digest)
        ):
            raise ValueError(
                "Invocation configuration identity must be a SHA-256 digest"
            )


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
    active_rivet_slug: str | None = None
    invocation_context: AgentInvocationContext | None = None
    instruction_set: dict | None = None
    # Internal evidence callback; never user-authored invocation/action authority.
    invocation_observer: Callable[[dict], Awaitable[None]] | None = None
    gateway_handler: Callable[[dict], Awaitable[dict]] | None = None
    gateway_cleanup: Callable[[], Awaitable[None]] | None = None


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
class AgentToolCallEvidence:
    """Read-only projection of matched persisted agent messages, not run authority."""

    session_id: str
    call_id: str
    tool_name: str
    arguments: dict[str, Any] | str | None
    request_message_id: str | None
    response_message_id: str | None = None
    response: str | None = None
    display_response: str | None = None
    timestamp: int = 0
    source: str = "agent.session-messages"
    record_note: str | None = None


@dataclass
class AgentChatMessage:
    """A single chat message from an agent session's history."""

    id: str
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: int  # epoch ms
    trace_id: str | None = None
    tool_evidence: tuple[AgentToolCallEvidence, ...] = ()


class BaseAgentEngine(ABC):
    """Abstract base for all agent adapters (Constitution 2)."""

    async def get_invocation_capabilities(self) -> AgentInvocationCapabilities:
        """Existing adapters remain valid and fail closed for restricted roles."""
        return AgentInvocationCapabilities(
            adapter=type(self).__name__,
            reason="This adapter has not qualified restricted process interface authoring.",
        )

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
