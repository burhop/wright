"""Exact-scope, abortable routing for Wright's experimental WebMCP bridge."""

from __future__ import annotations

import asyncio
import json
import re
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit
from datetime import UTC, datetime, timedelta

from jsonschema import ValidationError, validate  # type: ignore[import-untyped]


_TOOL_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")


class WebMcpRoutingError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class WebMcpBinding:
    principal_id: str
    workspace_id: str
    session_id: str
    surface_id: str
    instance_id: str
    generation: int
    document_origin: str
    server_id: str
    tool_name: str

    def __post_init__(self) -> None:
        for name in (
            "principal_id",
            "workspace_id",
            "session_id",
            "surface_id",
            "instance_id",
            "server_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip() or len(value) > 256:
                raise ValueError(f"{name} is invalid")
        if not isinstance(self.generation, int) or self.generation < 1:
            raise ValueError("generation must be a positive integer")
        if not _TOOL_NAME.fullmatch(self.tool_name):
            raise ValueError("tool_name is invalid")
        parsed = urlsplit(self.document_origin)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("document_origin must be an exact HTTP(S) origin")
        normalized = f"{parsed.scheme}://{parsed.netloc}"
        if self.document_origin != normalized:
            raise ValueError("document_origin must be normalized")

    def envelope(self) -> dict[str, Any]:
        return {
            "workspaceId": self.workspace_id,
            "sessionId": self.session_id,
            "surfaceId": self.surface_id,
            "instanceId": self.instance_id,
            "generation": self.generation,
            "documentOrigin": self.document_origin,
            "serverId": self.server_id,
        }


@dataclass(frozen=True, slots=True)
class WebMcpRegistration:
    binding: WebMcpBinding
    description: str
    input_schema: Mapping[str, Any]


@dataclass(slots=True)
class _Registered:
    registration: WebMcpRegistration
    websocket: Any
    calls: deque[float]


@dataclass(slots=True)
class _Pending:
    binding: WebMcpBinding
    websocket: Any
    future: asyncio.Future[Mapping[str, Any]]


AuditSink = Callable[[str, Mapping[str, Any]], None]


class WebMcpRouter:
    def __init__(
        self,
        *,
        maximum_message_bytes: int = 1_048_576,
        maximum_calls_per_minute: int = 60,
        operation_timeout: float = 30.0,
        audit: AuditSink | None = None,
    ) -> None:
        if min(maximum_message_bytes, maximum_calls_per_minute) <= 0:
            raise ValueError("WebMCP limits must be positive")
        if operation_timeout <= 0:
            raise ValueError("WebMCP operation timeout must be positive")
        self.maximum_message_bytes = maximum_message_bytes
        self.maximum_calls_per_minute = maximum_calls_per_minute
        self.operation_timeout = operation_timeout
        self.audit = audit or (lambda _event, _fields: None)
        self._registrations: dict[WebMcpBinding, _Registered] = {}
        self._by_socket: dict[Any, set[WebMcpBinding]] = defaultdict(set)
        self._pending: dict[str, _Pending] = {}

    def register(
        self,
        websocket: Any,
        registration: WebMcpRegistration,
    ) -> None:
        self._validate_registration(registration)
        current = self._registrations.get(registration.binding)
        if current is not None and current.websocket is not websocket:
            raise WebMcpRoutingError(
                "SURFACE_PROTOCOL_WEBMCP_DUPLICATE",
                "A different document already owns this WebMCP registration",
            )
        self._registrations[registration.binding] = _Registered(
            registration=registration,
            websocket=websocket,
            calls=current.calls if current is not None else deque(),
        )
        self._by_socket[websocket].add(registration.binding)
        self.audit("webmcp.registered", self._audit_fields(registration.binding))

    def unregister(
        self,
        websocket: Any,
        binding: WebMcpBinding,
        *,
        reason: str = "disposed",
    ) -> bool:
        current = self._registrations.get(binding)
        if current is None or current.websocket is not websocket:
            return False
        self._registrations.pop(binding, None)
        self._by_socket[websocket].discard(binding)
        self._cancel_binding(binding, reason)
        self.audit(
            "webmcp.unregistered",
            {**self._audit_fields(binding), "reason": reason},
        )
        return True

    def disconnect(self, websocket: Any, *, reason: str = "disconnect") -> int:
        bindings = tuple(self._by_socket.pop(websocket, ()))
        for binding in bindings:
            current = self._registrations.get(binding)
            if current is not None and current.websocket is websocket:
                self._registrations.pop(binding, None)
                self._cancel_binding(binding, reason)
        if bindings:
            self.audit("webmcp.disconnected", {"count": len(bindings), "reason": reason})
        return len(bindings)

    def matching(
        self,
        *,
        workspace_id: str,
        server_id: str,
        tool_name: str,
    ) -> tuple[WebMcpBinding, ...]:
        return tuple(
            binding
            for binding in self._registrations
            if binding.workspace_id == workspace_id
            and binding.server_id == server_id
            and binding.tool_name == tool_name
        )

    async def invoke(
        self,
        binding: WebMcpBinding,
        arguments: Mapping[str, Any],
        *,
        timeout: float | None = None,
    ) -> Mapping[str, Any]:
        registered = self._registrations.get(binding)
        if registered is None:
            raise WebMcpRoutingError(
                "SURFACE_STATE_WEBMCP_NOT_REGISTERED",
                "The exact WebMCP surface tool is no longer registered",
            )
        self._bounded_json(arguments, "arguments")
        try:
            validate(instance=dict(arguments), schema=dict(registered.registration.input_schema))
        except ValidationError as error:
            raise WebMcpRoutingError(
                "SURFACE_PROTOCOL_WEBMCP_ARGUMENTS_INVALID",
                "WebMCP arguments do not match the registered schema",
            ) from error
        self._consume_rate(registered)
        call_id = f"webmcp-{uuid.uuid4()}"
        correlation_id = str(uuid.uuid4())
        future: asyncio.Future[Mapping[str, Any]] = (
            asyncio.get_running_loop().create_future()
        )
        self._pending[call_id] = _Pending(binding, registered.websocket, future)
        now = datetime.now(UTC)
        payload = {
            "protocolVersion": "1.0",
            "kind": "request",
            "messageId": call_id.removeprefix("webmcp-"),
            "correlationId": correlation_id,
            "binding": binding.envelope(),
            "operation": "webmcp.tool.call",
            "toolName": binding.tool_name,
            "sequence": 0,
            "createdAt": now.isoformat(),
            "deadlineAt": (now + timedelta(seconds=self.operation_timeout)).isoformat(),
            "payload": dict(arguments),
        }
        try:
            await registered.websocket.send_text(self._bounded_json(payload, "request"))
            response = await asyncio.wait_for(
                future,
                min(timeout or self.operation_timeout, self.operation_timeout),
            )
            if response.get("kind") == "error":
                raise WebMcpRoutingError(
                    "SURFACE_PROTOCOL_WEBMCP_TOOL_ERROR",
                    "The WebMCP tool returned an error",
                )
            result = response.get("payload", {})
            if not isinstance(result, Mapping):
                raise WebMcpRoutingError(
                    "SURFACE_PROTOCOL_WEBMCP_RESULT_INVALID",
                    "The WebMCP tool result must be an object",
                )
            self._bounded_json(result, "result")
            self.audit("webmcp.call.succeeded", self._audit_fields(binding))
            return dict(result)
        except (asyncio.CancelledError, TimeoutError):
            await self._send_cancel(registered.websocket, call_id, binding)
            self.audit("webmcp.call.cancelled", self._audit_fields(binding))
            raise
        finally:
            self._pending.pop(call_id, None)

    def handle_message(self, websocket: Any, message: str) -> bool:
        if len(message.encode("utf-8")) > self.maximum_message_bytes:
            raise WebMcpRoutingError(
                "SURFACE_LIMIT_WEBMCP_MESSAGE_BYTES",
                "WebMCP message exceeds the configured limit",
            )
        try:
            payload = json.loads(message)
        except json.JSONDecodeError as error:
            raise WebMcpRoutingError(
                "SURFACE_PROTOCOL_WEBMCP_JSON_INVALID",
                "WebMCP message is not valid JSON",
            ) from error
        if not isinstance(payload, Mapping):
            raise WebMcpRoutingError(
                "SURFACE_PROTOCOL_WEBMCP_MESSAGE_INVALID",
                "WebMCP message is not an object",
            )
        self.validate_surface_message(payload)
        reply_to = payload.get("replyTo")
        if not isinstance(reply_to, str):
            return False
        call_id = f"webmcp-{reply_to}"
        pending = self._pending.get(call_id)
        if pending is None:
            self.audit("webmcp.response.late", {"call_id": call_id[:64]})
            return False
        if pending.websocket is not websocket:
            self.audit("webmcp.response.wrong_socket", self._audit_fields(pending.binding))
            return False
        if payload.get("binding") != pending.binding.envelope():
            self.audit("webmcp.response.stale_scope", self._audit_fields(pending.binding))
            return False
        if not pending.future.done():
            pending.future.set_result(dict(payload))
            return True
        return False

    def validate_surface_message(self, payload: Mapping[str, Any]) -> None:
        required = {
            "protocolVersion",
            "kind",
            "messageId",
            "correlationId",
            "binding",
            "operation",
            "sequence",
            "createdAt",
            "deadlineAt",
        }
        allowed = required | {"traceId", "replyTo", "toolName", "idempotencyKey", "payload", "error"}
        if (
            payload.get("protocolVersion") != "1.0"
            or not required.issubset(payload)
            or not set(payload).issubset(allowed)
            or payload.get("kind") not in {"request", "result", "error", "event", "cancel"}
            or not isinstance(payload.get("binding"), Mapping)
            or not isinstance(payload.get("operation"), str)
            or not isinstance(payload.get("sequence"), int)
        ):
            raise WebMcpRoutingError(
                "SURFACE_PROTOCOL_WEBMCP_MESSAGE_INVALID",
                "WebMCP surface message does not match contract version 1.0",
            )
        for key in ("messageId", "correlationId"):
            try:
                uuid.UUID(str(payload.get(key)))
            except ValueError as error:
                raise WebMcpRoutingError(
                    "SURFACE_PROTOCOL_WEBMCP_MESSAGE_INVALID",
                    f"WebMCP {key} is not a UUID",
                ) from error
        self._bounded_json(payload, "message")

    async def close(self) -> None:
        for pending in tuple(self._pending.values()):
            if not pending.future.done():
                pending.future.cancel()
        self._pending.clear()
        self._registrations.clear()
        self._by_socket.clear()

    def _validate_registration(self, registration: WebMcpRegistration) -> None:
        if len(registration.description) > 2048:
            raise WebMcpRoutingError(
                "SURFACE_LIMIT_WEBMCP_DESCRIPTION",
                "WebMCP description exceeds the configured limit",
            )
        schema = dict(registration.input_schema)
        if schema.get("type") not in {None, "object"}:
            raise WebMcpRoutingError(
                "SURFACE_PROTOCOL_WEBMCP_SCHEMA_INVALID",
                "WebMCP input schema must describe an object",
            )
        self._bounded_json(schema, "schema")

    def _bounded_json(self, value: Any, label: str) -> str:
        try:
            encoded = json.dumps(value, allow_nan=False, separators=(",", ":"))
        except (TypeError, ValueError) as error:
            raise WebMcpRoutingError(
                "SURFACE_PROTOCOL_WEBMCP_JSON_INVALID",
                f"WebMCP {label} is not JSON serializable",
            ) from error
        if len(encoded.encode("utf-8")) > self.maximum_message_bytes:
            raise WebMcpRoutingError(
                "SURFACE_LIMIT_WEBMCP_MESSAGE_BYTES",
                f"WebMCP {label} exceeds the configured limit",
            )
        return encoded

    def _consume_rate(self, registered: _Registered) -> None:
        now = time.monotonic()
        while registered.calls and registered.calls[0] <= now - 60:
            registered.calls.popleft()
        if len(registered.calls) >= self.maximum_calls_per_minute:
            raise WebMcpRoutingError(
                "SURFACE_LIMIT_WEBMCP_RATE",
                "WebMCP tool call rate exceeded",
            )
        registered.calls.append(now)

    def _cancel_binding(self, binding: WebMcpBinding, reason: str) -> None:
        for pending in tuple(self._pending.values()):
            if pending.binding == binding and not pending.future.done():
                pending.future.set_exception(
                    WebMcpRoutingError(
                        "SURFACE_STATE_WEBMCP_DISPOSED",
                        f"WebMCP registration ended: {reason}",
                    )
                )

    async def _send_cancel(
        self, websocket: Any, call_id: str, binding: WebMcpBinding
    ) -> None:
        payload = {
            "protocolVersion": "1.0",
            "kind": "cancel",
            "messageId": str(uuid.uuid4()),
            "correlationId": str(uuid.uuid4()),
            "replyTo": call_id.removeprefix("webmcp-"),
            "binding": binding.envelope(),
            "operation": "webmcp.tool.cancel",
            "toolName": binding.tool_name,
            "sequence": 0,
            "createdAt": datetime.now(UTC).isoformat(),
            "deadlineAt": datetime.now(UTC).isoformat(),
        }
        try:
            await websocket.send_text(self._bounded_json(payload, "cancellation"))
        except Exception:
            return

    @staticmethod
    def _audit_fields(binding: WebMcpBinding) -> dict[str, Any]:
        return {
            "workspace_id": binding.workspace_id,
            "session_id": binding.session_id,
            "surface_id": binding.surface_id,
            "generation": binding.generation,
            "document_origin": binding.document_origin,
            "server_id": binding.server_id,
            "tool_name": binding.tool_name,
        }


__all__ = [
    "WebMcpBinding",
    "WebMcpRegistration",
    "WebMcpRouter",
    "WebMcpRoutingError",
]
