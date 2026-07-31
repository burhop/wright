"""Stable, redacted Workspace Surfaces error vocabulary."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from core.redaction import redact_mapping, redact_text


class SurfaceErrorCode(StrEnum):
    NOT_FOUND = "SURFACE_STATE_NOT_FOUND"
    INVALID_TRANSITION = "SURFACE_STATE_INVALID_TRANSITION"
    STALE_REVISION = "SURFACE_STATE_STALE_REVISION"
    FORBIDDEN = "SURFACE_POLICY_FORBIDDEN"
    INVALID_LIMIT = "SURFACE_POLICY_INVALID_LIMIT"
    PROTOCOL_INVALID = "SURFACE_PROTOCOL_INVALID"
    INTERNAL = "SURFACE_RUNTIME_INTERNAL"


class SurfaceOptimisticLockError(RuntimeError):
    """Infrastructure-neutral signal that compare-and-set lost a race."""


class SurfaceError(Exception):
    """Safe application error with transport-neutral stable metadata."""

    def __init__(
        self,
        *,
        code: SurfaceErrorCode | str,
        message: str,
        retryable: bool = False,
        correlation_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        self.code = SurfaceErrorCode(code)
        self.message = redact_text(message)
        self.retryable = retryable
        self.correlation_id = correlation_id
        self.context = redact_mapping(context)
        super().__init__(self.message)

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code.value,
            "message": self.message,
            "retryable": self.retryable,
            "correlation_id": self.correlation_id,
            "context": self.context,
        }

    def __repr__(self) -> str:
        return f"SurfaceError(code={self.code.value!r}, message={self.message!r})"
