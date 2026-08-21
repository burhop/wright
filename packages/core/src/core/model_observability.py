"""Bounded structured logging and tracing for engineering-model boundaries."""

from __future__ import annotations

import math
import re
from typing import Any, Mapping, Sequence

import structlog
from opentelemetry import trace

from .redaction import redact_text

MODEL_BOUNDARY_EVENTS = frozenset(
    {
        "model.adapter.infer",
        "model.adapter.verify",
        "model.cleanup",
        "model.database.operation",
        "model.database.plan",
        "model.evidence.record",
        "model.export",
        "model.gateway.call",
        "model.operation.cancel",
        "model.source.acquire",
        "model.storage.activate",
        "model.storage.promote",
        "model.storage.reconcile",
        "model.storage.stage",
    }
)

_IDENTITY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_ATTRIBUTE = re.compile(r"^[a-z][a-z0-9._-]{0,127}$")
_PRIVATE_FIELD = re.compile(
    r"(?i)(?:path|command|endpoint|environment|authority|api[_-]?key|secret|token|password|authorization|credential|payload|arguments|content(?![_-]digest)|input(?![_-]digest)|output(?![_-]digest))"
)
_STATES = frozenset({"started", "succeeded", "failed", "blocked", "cancelled"})


def _safe_scalar(value: Any) -> str | bool | int | float | None:
    if value is None or isinstance(value, (str, bool, int)):
        if isinstance(value, str):
            return redact_text(value)[:512]
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return None


def _safe_attributes(
    attributes: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], int]:
    safe: dict[str, Any] = {}
    redacted = 0
    for key, value in list((attributes or {}).items())[:64]:
        name = str(key)
        if not _ATTRIBUTE.fullmatch(name) or _PRIVATE_FIELD.search(name):
            redacted += 1
            continue
        scalar = _safe_scalar(value)
        if scalar is not None:
            safe[name] = scalar
            continue
        if isinstance(value, Sequence) and not isinstance(
            value, (str, bytes, bytearray)
        ):
            items = [_safe_scalar(item) for item in list(value)[:32]]
            if all(item is not None for item in items):
                safe[name] = items
                continue
        redacted += 1
    if attributes and len(attributes) > 64:
        redacted += len(attributes) - 64
    return safe, redacted


class ModelBoundaryObserver:
    """Emit allowlisted zero-payload model events and spans."""

    def __init__(self, *, logger=None, tracer=None) -> None:
        self.logger = logger or structlog.get_logger("wright.model")
        self.tracer = tracer or trace.get_tracer("wright.model")

    def record(
        self,
        event: str,
        *,
        trace_id: str,
        state: str = "succeeded",
        attributes: Mapping[str, Any] | None = None,
    ) -> None:
        if event not in MODEL_BOUNDARY_EVENTS:
            raise ValueError("Model observability event is not allowlisted")
        if not _IDENTITY.fullmatch(trace_id):
            raise ValueError("Model observability trace identity is invalid")
        if state not in _STATES:
            raise ValueError("Model observability state is invalid")
        safe, redacted_fields = _safe_attributes(attributes)
        log_attributes = {
            "trace_id": trace_id,
            "state": state,
            "redacted_fields": redacted_fields,
            **safe,
        }
        span_attributes = {
            "wright.trace_id": trace_id,
            "wright.model.state": state,
            "wright.model.redacted_fields": redacted_fields,
            **{f"wright.model.{key}": value for key, value in safe.items()},
        }
        with self.tracer.start_as_current_span(event, attributes=span_attributes):
            self.logger.info(event, **log_attributes)


__all__ = ["MODEL_BOUNDARY_EVENTS", "ModelBoundaryObserver"]
