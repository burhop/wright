"""Structured, redacted telemetry values for Workspace Surfaces."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from core.redaction import REDACTED, redact_mapping, redact_text


_CODE = re.compile(r"^SURFACE_[A-Z0-9]+(?:_[A-Z0-9]+)+$")
_CONTENT_KEY = re.compile(
    r"(?i)(prompt|effective_constraints|script(?:_content)?$|target_url|display_url|"
    r"request_url|query|body|authorization|cookie|token|secret|password|credential)"
)
_SAFE_CONTENT_SUFFIX = ("_hash", "_digest", "_id", "_revision")


class SurfaceSeverity(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class TraceCorrelation:
    correlation_id: str
    trace_id: str
    span_id: str

    def __post_init__(self) -> None:
        for label, value, maximum in (
            ("correlation_id", self.correlation_id, 128),
            ("trace_id", self.trace_id, 64),
            ("span_id", self.span_id, 32),
        ):
            if not value or len(value) > maximum:
                raise ValueError(f"{label} is required and bounded")


def redact_surface_attributes(
    attributes: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Redact credentials and artifact content while preserving safe IDs/hashes."""

    if not attributes:
        return {}
    safe: dict[str, Any] = {}
    for raw_key, value in attributes.items():
        key = str(raw_key)
        lowered = key.lower()
        if _CONTENT_KEY.search(key) and not lowered.endswith(_SAFE_CONTENT_SUFFIX):
            safe[key] = REDACTED
        elif isinstance(value, Mapping):
            safe[key] = redact_surface_attributes(value)
        elif isinstance(value, list):
            safe[key] = [
                redact_surface_attributes(item)
                if isinstance(item, Mapping)
                else redact_text(item)
                if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            safe[key] = value
    return redact_mapping(safe)


@dataclass(frozen=True, slots=True)
class SurfaceDiagnosticEvent:
    timestamp: datetime
    severity: SurfaceSeverity
    code: str
    message: str
    correlation: TraceCorrelation
    retryable: bool
    workspace_id: str
    surface_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    instance_id: str | None = None
    presentation_id: str | None = None
    runtime_id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None:
            raise ValueError("diagnostic timestamp must be timezone-aware")
        object.__setattr__(self, "severity", SurfaceSeverity(self.severity))
        if not _CODE.fullmatch(self.code):
            raise ValueError("diagnostic code must use the stable SURFACE_* vocabulary")
        object.__setattr__(self, "message", redact_text(self.message))
        if not self.workspace_id.strip():
            raise ValueError("workspace_id is required")
        object.__setattr__(
            self, "attributes", redact_surface_attributes(self.attributes)
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "correlation_id": self.correlation.correlation_id,
            "trace_id": self.correlation.trace_id,
            "span_id": self.correlation.span_id,
            "retryable": self.retryable,
            "workspace_id": self.workspace_id,
            "surface_id": self.surface_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "instance_id": self.instance_id,
            "presentation_id": self.presentation_id,
            "runtime_id": self.runtime_id,
            "attributes": dict(self.attributes),
        }
