from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping


class GatewayErrorCode(StrEnum):
    INVALID_BINDING = "invalid_binding"
    INVALID_LIFECYCLE = "invalid_lifecycle"
    UNSUPPORTED_PROTOCOL = "unsupported_protocol"
    NOT_FOUND = "not_found"
    POLICY_DENIED = "policy_denied"
    INVALID_INPUT = "invalid_input"
    INVALID_OUTPUT = "invalid_output"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    CHILD_UNAVAILABLE = "child_unavailable"
    INTERNAL = "internal"


class GatewayError(RuntimeError):
    def __init__(self, code: GatewayErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class SessionState(StrEnum):
    CREATED = "created"
    INITIALIZED = "initialized"
    ACTIVE = "active"
    CLOSING = "closing"
    CLOSED = "closed"


class RequestState(StrEnum):
    ACCEPTED = "accepted"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"

    @property
    def terminal(self) -> bool:
        return self in {
            RequestState.SUCCEEDED,
            RequestState.FAILED,
            RequestState.CANCELLED,
            RequestState.TIMED_OUT,
        }


@dataclass(frozen=True, slots=True)
class GatewaySessionContext:
    session_id: str
    principal_id: str
    workspace_id: str
    workspace_path: str
    transport: str
    protocol_version: str | None = None
    client_name: str | None = None
    client_version: str | None = None
    client_capabilities: Mapping[str, Any] = field(default_factory=dict)
    state: SessionState = SessionState.CREATED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        required = {
            "session_id": self.session_id,
            "principal_id": self.principal_id,
            "workspace_id": self.workspace_id,
            "workspace_path": self.workspace_path,
        }
        missing = [name for name, value in required.items() if not value.strip()]
        if missing:
            raise GatewayError(
                GatewayErrorCode.INVALID_BINDING,
                f"Gateway binding requires {', '.join(missing)}",
            )
        if self.transport not in {"stdio", "streamable_http", "legacy"}:
            raise GatewayError(
                GatewayErrorCode.INVALID_BINDING,
                f"Unsupported gateway transport: {self.transport}",
            )
        object.__setattr__(
            self,
            "client_capabilities",
            MappingProxyType(dict(self.client_capabilities)),
        )

    def initialized(
        self,
        *,
        protocol_version: str,
        client_name: str,
        client_version: str,
        client_capabilities: Mapping[str, Any],
    ) -> GatewaySessionContext:
        if self.state is not SessionState.CREATED:
            raise GatewayError(
                GatewayErrorCode.INVALID_LIFECYCLE,
                "Gateway session may be initialized exactly once",
            )
        return GatewaySessionContext(
            session_id=self.session_id,
            principal_id=self.principal_id,
            workspace_id=self.workspace_id,
            workspace_path=self.workspace_path,
            transport=self.transport,
            protocol_version=protocol_version,
            client_name=client_name,
            client_version=client_version,
            client_capabilities=client_capabilities,
            state=SessionState.INITIALIZED,
            created_at=self.created_at,
        )

    def activate(self) -> GatewaySessionContext:
        if self.state is not SessionState.INITIALIZED:
            raise GatewayError(
                GatewayErrorCode.INVALID_LIFECYCLE,
                "Gateway session must initialize before activation",
            )
        return self._with_state(SessionState.ACTIVE)

    def close(self) -> GatewaySessionContext:
        if self.state is SessionState.CLOSED:
            return self
        return self._with_state(SessionState.CLOSED)

    def _with_state(self, state: SessionState) -> GatewaySessionContext:
        return GatewaySessionContext(
            session_id=self.session_id,
            principal_id=self.principal_id,
            workspace_id=self.workspace_id,
            workspace_path=self.workspace_path,
            transport=self.transport,
            protocol_version=self.protocol_version,
            client_name=self.client_name,
            client_version=self.client_version,
            client_capabilities=self.client_capabilities,
            state=state,
            created_at=self.created_at,
        )


@dataclass(slots=True)
class GatewayRequest:
    session_id: str
    request_id: str
    method: str
    correlation_id: str
    deadline: float
    maximum_deadline: float
    state: RequestState = RequestState.ACCEPTED
    cancellation_reason: str | None = None

    def transition(self, target: RequestState) -> None:
        if self.state.terminal:
            raise GatewayError(
                GatewayErrorCode.INVALID_LIFECYCLE,
                f"Request {self.request_id} is already terminal",
            )
        allowed = {
            RequestState.ACCEPTED: {RequestState.RUNNING, RequestState.CANCELLED},
            RequestState.RUNNING: {
                RequestState.SUCCEEDED,
                RequestState.FAILED,
                RequestState.CANCELLED,
                RequestState.TIMED_OUT,
            },
        }
        if target not in allowed.get(self.state, set()):
            raise GatewayError(
                GatewayErrorCode.INVALID_LIFECYCLE,
                f"Invalid request transition: {self.state} -> {target}",
            )
        self.state = target

    def cancel(self, reason: str | None = None) -> None:
        self.cancellation_reason = reason
        self.transition(RequestState.CANCELLED)


@dataclass(frozen=True, slots=True)
class GatewayTool:
    name: str
    server_id: str
    tool_name: str
    description: str
    input_schema: Mapping[str, Any]
    output_schema: Mapping[str, Any] | None = None
    annotations: Mapping[str, Any] = field(default_factory=dict)
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class GatewayResource:
    uri: str
    name: str
    description: str
    mime_type: str
    provenance: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class GatewayToolResult:
    content: tuple[Mapping[str, Any], ...]
    structured_content: Mapping[str, Any] | None = None
    is_error: bool = False
    error_code: GatewayErrorCode | None = None
