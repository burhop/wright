"""Public frozen agent identity and transport outcomes, independent of workflows."""

from typing import Literal, Protocol

import hashlib
import json

from pydantic import Field, StrictStr, model_validator

from .process_validation import Contract, Digest, Identifier, canonical_digest


class AgentConfiguration(Contract):
    """Resolved public identity. Digests reference evidence, never credentials."""

    schema_version: Literal["wright.agent-configuration/1"] = (
        "wright.agent-configuration/1"
    )
    platform: Identifier
    model_reference: Identifier
    runtime_version: Identifier
    client_version: Identifier
    transport: Identifier
    auth_method: Identifier
    instructions_digest: Digest
    tools_digest: Digest
    effective_configuration_digest: Digest

    @property
    def digest(self) -> str:
        return canonical_digest(self)


class AgentPlatformSession(Contract):
    session_id: Identifier
    workspace_id: Identifier
    backend_thread_id: Identifier
    configuration: AgentConfiguration
    created_at_ms: int = Field(ge=0, strict=True)
    archived: bool = False
    gateway_binding_digest: Digest | None = None


class AgentChatGatewayBinding(Contract):
    session_id: Identifier
    workspace_id: Identifier
    principal_id: Identifier
    tool_name: Literal["wright__workspace_status"] = "wright__workspace_status"

    @property
    def digest(self):
        return canonical_digest(self)


class AgentPlatformConflict(ValueError):
    """Frozen routing or a durable agent receipt changed unexpectedly."""


class AgentWorkspaceBinding(Contract):
    workspace_id: Identifier
    workspace_path: StrictStr = Field(min_length=1, max_length=4096)
    platform: Identifier


class AgentChatSessionRecord(Contract):
    """Frozen chat identity before Wright associates its workspace identifier."""

    session_id: Identifier
    backend_thread_id: Identifier
    workspace_path: StrictStr = Field(min_length=1, max_length=4096)
    configuration: AgentConfiguration
    instructions: StrictStr = Field(min_length=1, max_length=131072)
    resolved_configuration_json: StrictStr = Field(min_length=2, max_length=2097152)
    tool_configuration_json: StrictStr = Field(min_length=2, max_length=131072)
    reasoning_effort: Literal["none", "minimal", "low", "medium", "high", "xhigh"]
    account_digest: Digest
    created_at_ms: int = Field(ge=0, strict=True)

    @model_validator(mode="after")
    def instruction_identity(self):
        if hashlib.sha256(self.instructions.encode()).hexdigest() != (
            self.configuration.instructions_digest
        ):
            raise ValueError("Chat instructions differ from their frozen digest")
        for snapshot, expected in (
            (
                self.resolved_configuration_json,
                self.configuration.effective_configuration_digest,
            ),
            (self.tool_configuration_json, self.configuration.tools_digest),
        ):
            if canonical_digest(json.loads(snapshot)) != expected:
                raise ValueError(
                    "Chat configuration snapshot differs from its frozen digest"
                )
        return self


AgentTurnStatus = Literal[
    "prepared",
    "dispatching",
    "submitted",
    "running",
    "completed",
    "failed",
    "interrupted",
    "unknown",
]
AGENT_TURN_TERMINAL = frozenset({"completed", "failed", "interrupted"})


class AgentPlatformTurn(Contract):
    """A receipt is evidence of its boundary, not proof of an external effect."""

    session_id: Identifier
    attempt_id: Identifier
    message_digest: Digest
    configuration_digest: Digest
    status: AgentTurnStatus = "prepared"
    backend_turn_id: Identifier | None = None
    error_code: Identifier | None = None
    created_at_ms: int = Field(ge=0, strict=True)
    updated_at_ms: int = Field(ge=0, strict=True)

    @model_validator(mode="after")
    def receipt_identity(self):
        if self.updated_at_ms < self.created_at_ms:
            raise ValueError("Turn receipt time cannot precede creation")
        if self.status in {"submitted", "running", "completed", "interrupted"} and (
            self.backend_turn_id is None
        ):
            raise ValueError("Acknowledged turn state requires a backend turn identity")
        return self


class AgentChatRepository(Protocol):
    """Storage port supplied by the Wright application composition owner."""

    def create_chat_session(
        self, session: AgentChatSessionRecord
    ) -> AgentChatSessionRecord: ...
    def get_chat_session(self, session_id: str) -> AgentChatSessionRecord: ...
    def list_chat_sessions(
        self, platform: str
    ) -> tuple[AgentChatSessionRecord, ...]: ...
    def archive_chat_session(self, session_id: str) -> None: ...
    def get_chat_gateway(self, session_id: str) -> AgentChatGatewayBinding | None: ...
    def bind_chat_gateway(
        self, binding: AgentChatGatewayBinding
    ) -> AgentChatGatewayBinding: ...
    def resolve_workspace_binding(self, session_id: str) -> AgentWorkspaceBinding: ...
    def create_session(self, session: AgentPlatformSession) -> AgentPlatformSession: ...
    def get_session(self, session_id: str) -> AgentPlatformSession: ...
    def prepare_turn(self, turn: AgentPlatformTurn) -> AgentPlatformTurn: ...
    def transition(
        self, expected: AgentPlatformTurn, updated: AgentPlatformTurn
    ) -> AgentPlatformTurn: ...
    def unresolved_turns(self, session_id: str) -> tuple[AgentPlatformTurn, ...]: ...
