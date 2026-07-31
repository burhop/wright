"""Authenticated, composite-bound Workspace Surface message routing."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Callable, Mapping


_OPERATION = re.compile(r"^[a-z][a-z0-9_.:/-]{1,127}$")
_KINDS = frozenset({"request", "result", "error", "event", "cancel"})
_TOP_LEVEL = frozenset(
    {
        "protocolVersion",
        "kind",
        "messageId",
        "correlationId",
        "traceId",
        "replyTo",
        "binding",
        "operation",
        "toolName",
        "sequence",
        "createdAt",
        "deadlineAt",
        "idempotencyKey",
        "payload",
        "error",
    }
)
_BINDING_KEYS = frozenset(
    {
        "workspaceId",
        "sessionId",
        "surfaceId",
        "instanceId",
        "generation",
        "documentOrigin",
        "serverId",
        "presentationId",
    }
)


@dataclass(frozen=True, slots=True)
class AuthorizedSurfaceBinding:
    workspace_id: str
    session_id: str
    surface_id: str
    instance_id: str
    generation: int
    document_origin: str
    presentation_id: str
    active: bool
    server_id: str | None = None


@dataclass(frozen=True, slots=True)
class SurfaceMessageOutcome:
    ok: bool
    code: str
    payload: Any = None
    retryable: bool = False


@dataclass(frozen=True, slots=True)
class _ValidatedMessage:
    message_id: str
    kind: str
    operation: str
    sequence: int
    deadline_at: datetime
    reply_to: str | None
    payload: Any
    canonical_hash: str
    binding: Mapping[str, Any]


class _MessageRejected(RuntimeError):
    def __init__(self, code: str, *, retryable: bool = False) -> None:
        super().__init__(code)
        self.code = code
        self.retryable = retryable


class SurfaceMessageRouter:
    def __init__(
        self,
        *,
        clock=lambda: datetime.now(UTC),
        handlers: Mapping[str, Callable[[Any], Any]] | None = None,
        cancel: Callable[[str], None] | None = None,
        maximum_message_bytes: int = 4 * 1024 * 1024,
        maximum_json_depth: int = 32,
        maximum_messages_per_minute: int = 60,
        replay_window_seconds: int = 300,
    ) -> None:
        if (
            min(
                maximum_message_bytes,
                maximum_json_depth,
                maximum_messages_per_minute,
                replay_window_seconds,
            )
            < 1
        ):
            raise ValueError("surface message limits must be positive")
        self.clock = clock
        self.handlers = dict(handlers or {})
        self.cancel = cancel or (lambda _reply_to: None)
        self.maximum_message_bytes = maximum_message_bytes
        self.maximum_json_depth = maximum_json_depth
        self.maximum_messages_per_minute = maximum_messages_per_minute
        self.replay_window = timedelta(seconds=replay_window_seconds)
        self._replays: dict[
            tuple[str, str], tuple[datetime, str, SurfaceMessageOutcome]
        ] = {}
        self._sequences: dict[tuple[str, str, str], int] = {}
        self._rates: dict[tuple[str, str], deque[datetime]] = defaultdict(deque)

    @staticmethod
    def _depth(value: Any, current: int = 0) -> int:
        if isinstance(value, dict):
            return max(
                (
                    SurfaceMessageRouter._depth(item, current + 1)
                    for item in value.values()
                ),
                default=current + 1,
            )
        if isinstance(value, list):
            return max(
                (SurfaceMessageRouter._depth(item, current + 1) for item in value),
                default=current + 1,
            )
        return current

    @staticmethod
    def _date(value: Any) -> datetime:
        if not isinstance(value, str):
            raise _MessageRejected("SURFACE_MESSAGE_INVALID")
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise _MessageRejected("SURFACE_MESSAGE_INVALID") from error
        if parsed.tzinfo is None:
            raise _MessageRejected("SURFACE_MESSAGE_INVALID")
        return parsed

    def _validate(self, message: Any) -> _ValidatedMessage:
        if not isinstance(message, dict) or not set(message) <= _TOP_LEVEL:
            raise _MessageRejected("SURFACE_MESSAGE_INVALID")
        try:
            encoded = json.dumps(
                message, sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode("utf-8")
        except (TypeError, ValueError) as error:
            raise _MessageRejected("SURFACE_MESSAGE_INVALID") from error
        if len(encoded) > self.maximum_message_bytes:
            raise _MessageRejected("SURFACE_MESSAGE_TOO_LARGE")
        if self._depth(message.get("payload")) > self.maximum_json_depth:
            raise _MessageRejected("SURFACE_MESSAGE_TOO_DEEP")
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
        if not required <= set(message) or message["protocolVersion"] != "1.0":
            raise _MessageRejected("SURFACE_MESSAGE_INVALID")
        kind = message["kind"]
        operation = message["operation"]
        if (
            kind not in _KINDS
            or not isinstance(operation, str)
            or not _OPERATION.fullmatch(operation)
        ):
            raise _MessageRejected("SURFACE_MESSAGE_INVALID")
        for name in ("messageId", "correlationId"):
            try:
                uuid.UUID(str(message[name]))
            except (ValueError, AttributeError) as error:
                raise _MessageRejected("SURFACE_MESSAGE_INVALID") from error
        reply_to = message.get("replyTo")
        if kind in {"result", "error", "cancel"} and not reply_to:
            raise _MessageRejected("SURFACE_MESSAGE_INVALID")
        if reply_to is not None:
            try:
                uuid.UUID(str(reply_to))
            except (ValueError, AttributeError) as error:
                raise _MessageRejected("SURFACE_MESSAGE_INVALID") from error
        sequence = message["sequence"]
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
            raise _MessageRejected("SURFACE_MESSAGE_INVALID")
        self._date(message["createdAt"])
        deadline_at = self._date(message["deadlineAt"])
        raw_binding = message["binding"]
        binding_required = {
            "workspaceId",
            "sessionId",
            "surfaceId",
            "instanceId",
            "generation",
            "documentOrigin",
        }
        if (
            not isinstance(raw_binding, dict)
            or not binding_required <= set(raw_binding)
            or not set(raw_binding) <= _BINDING_KEYS
        ):
            raise _MessageRejected("SURFACE_MESSAGE_INVALID")
        return _ValidatedMessage(
            message_id=str(message["messageId"]),
            kind=str(kind),
            operation=operation,
            sequence=sequence,
            deadline_at=deadline_at,
            reply_to=str(reply_to) if reply_to is not None else None,
            payload=message.get("payload"),
            canonical_hash=hashlib.sha256(encoded).hexdigest(),
            binding=raw_binding,
        )

    @staticmethod
    def _binding_key(binding: AuthorizedSurfaceBinding) -> tuple[str, str, str]:
        return (
            binding.workspace_id,
            binding.presentation_id,
            binding.document_origin,
        )

    @staticmethod
    def _check_binding(
        binding: AuthorizedSurfaceBinding, message: _ValidatedMessage
    ) -> None:
        if not binding.active:
            raise _MessageRejected("SURFACE_MESSAGE_PRESENTATION_GONE")
        raw = message.binding
        if raw.get("generation") != binding.generation:
            raise _MessageRejected("SURFACE_MESSAGE_STALE_GENERATION")
        expected = {
            "workspaceId": binding.workspace_id,
            "sessionId": binding.session_id,
            "surfaceId": binding.surface_id,
            "instanceId": binding.instance_id,
            "documentOrigin": binding.document_origin,
            "presentationId": binding.presentation_id,
        }
        if binding.server_id is not None:
            expected["serverId"] = binding.server_id
        if any(raw.get(key) != value for key, value in expected.items()):
            raise _MessageRejected("SURFACE_MESSAGE_BINDING_MISMATCH")

    def _rate(self, binding: AuthorizedSurfaceBinding, now: datetime) -> None:
        key = (binding.workspace_id, binding.presentation_id)
        window = self._rates[key]
        cutoff = now - timedelta(minutes=1)
        while window and window[0] <= cutoff:
            window.popleft()
        if len(window) >= self.maximum_messages_per_minute:
            raise _MessageRejected("SURFACE_MESSAGE_RATE_LIMIT", retryable=True)
        window.append(now)

    def route(
        self, *, binding: AuthorizedSurfaceBinding, message: Any
    ) -> SurfaceMessageOutcome:
        try:
            validated = self._validate(message)
            self._check_binding(binding, validated)
            now = self.clock()
            if validated.deadline_at < now:
                raise _MessageRejected("SURFACE_MESSAGE_DEADLINE")
            replay_key = (binding.presentation_id, validated.message_id)
            replay = self._replays.get(replay_key)
            if replay is not None:
                _stored_at, stored_hash, outcome = replay
                if hmac_compare(stored_hash, validated.canonical_hash):
                    return outcome
                raise _MessageRejected("SURFACE_MESSAGE_REPLAY")
            self._rate(binding, now)
            sequence_key = self._binding_key(binding)
            previous = self._sequences.get(sequence_key)
            if previous is not None and validated.sequence <= previous:
                self._rates[(binding.workspace_id, binding.presentation_id)].pop()
                raise _MessageRejected("SURFACE_MESSAGE_SEQUENCE")
            if validated.kind == "cancel":
                assert validated.reply_to is not None
                self.cancel(validated.reply_to)
                outcome = SurfaceMessageOutcome(ok=True, code="CANCELLED")
            else:
                handler = self.handlers.get(validated.operation)
                payload = (
                    handler(validated.payload)
                    if handler is not None
                    else validated.payload
                )
                outcome = SurfaceMessageOutcome(ok=True, code="OK", payload=payload)
            self._sequences[sequence_key] = validated.sequence
            self._replays[replay_key] = (now, validated.canonical_hash, outcome)
            cutoff = now - self.replay_window
            self._replays = {
                key: value for key, value in self._replays.items() if value[0] >= cutoff
            }
            return outcome
        except _MessageRejected as error:
            return SurfaceMessageOutcome(
                ok=False, code=error.code, retryable=error.retryable
            )


def hmac_compare(left: str, right: str) -> bool:
    """Keep digest comparison constant-time without retaining raw messages."""
    import hmac

    return hmac.compare_digest(left, right)


__all__ = [
    "AuthorizedSurfaceBinding",
    "SurfaceMessageOutcome",
    "SurfaceMessageRouter",
]
