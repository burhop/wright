"""Readable platform errors with bounded, redacted technical details."""

from __future__ import annotations

from typing import Literal, get_args
import math

from core.errors import ErrorCode
from core.process_interactions import NavigationTarget, Reason
from core.process_validation import canonical_json
from core.redaction import redact_mapping, redact_text

from ..errors import WorkspaceServiceError

ProcessErrorCode = Literal[
    "INPUT_REQUIRED",
    "READINESS_UNSUPPORTED",
    "SOURCE_CHANGED",
    "SUBJECT_STALE",
    "OPTION_STALE",
    "INTERACTION_NOT_DECLARED",
    "RESPONSE_INVALID",
    "REQUEST_CONFLICT",
    "CAPABILITY_UNAVAILABLE",
    "UI_MODEL_TIMEOUT",
    "UI_MODEL_AUTH_REQUIRED",
    "UI_MODEL_RATE_LIMITED",
    "ACTION_NOT_PERMITTED",
    "OUTCOME_UNKNOWN",
    "UI_INCOMPATIBLE",
    "SCOPE_DENIED",
    "PRESENTATION_EXPIRED",
]

_DOMAIN_CODES = {
    "SOURCE_CHANGED": ErrorCode.CONFLICT,
    "SUBJECT_STALE": ErrorCode.CONFLICT,
    "OPTION_STALE": ErrorCode.CONFLICT,
    "REQUEST_CONFLICT": ErrorCode.CONFLICT,
    "UI_INCOMPATIBLE": ErrorCode.CONFLICT,
    "SCOPE_DENIED": ErrorCode.FORBIDDEN_PATH,
    "PRESENTATION_EXPIRED": ErrorCode.FORBIDDEN_PATH,
    "ACTION_NOT_PERMITTED": ErrorCode.FORBIDDEN_PATH,
    "CAPABILITY_UNAVAILABLE": ErrorCode.DEPENDENCY_UNAVAILABLE,
    "OUTCOME_UNKNOWN": ErrorCode.DEPENDENCY_UNAVAILABLE,
    "UI_MODEL_TIMEOUT": ErrorCode.DEPENDENCY_UNAVAILABLE,
    "UI_MODEL_AUTH_REQUIRED": ErrorCode.DEPENDENCY_UNAVAILABLE,
    "UI_MODEL_RATE_LIMITED": ErrorCode.DEPENDENCY_UNAVAILABLE,
}


def safe_diagnostic(details: dict | None) -> dict:
    """Redact before retention; bound depth/count/string size of each diagnostic."""
    visits = 0

    def bounded(value, depth=0):
        nonlocal visits
        visits += 1
        if depth >= 6 or visits > 128:
            return "[Details truncated]"
        if isinstance(value, dict):
            return {
                str(key)[:160]: bounded(item, depth + 1)
                for key, item in list(value.items())[:32]
            }
        if isinstance(value, (list, tuple)):
            return [bounded(item, depth + 1) for item in value[:32]]
        if isinstance(value, str):
            return redact_text(value)[:4096]
        if type(value) is float and not math.isfinite(value):
            return "[Non-finite detail]"
        if value is None or type(value) in (bool, int, float):
            return value
        return "[Unsupported detail]"

    redacted = redact_mapping(bounded(details or {}))
    if len(canonical_json(redacted).encode("utf-8")) > 65_536:
        return {
            "message": "Technical details exceed the display bound.",
            "truncated": True,
        }
    return redacted


class ProcessInterfaceError(WorkspaceServiceError):
    def __init__(
        self,
        code: ProcessErrorCode,
        message: str,
        correction: str,
        *,
        navigation: NavigationTarget | None = None,
        details: dict | None = None,
    ):
        if code not in get_args(ProcessErrorCode):
            raise ValueError("Unknown process interface error category")
        self.reason = Reason(
            code=code,
            message=redact_text(message),
            correction=redact_text(correction),
            navigation=navigation,
        )
        self.diagnostic = safe_diagnostic(details)
        super().__init__(
            self.reason.message,
            error_code=_DOMAIN_CODES.get(code, ErrorCode.INVALID_INPUT),
            operation="process.interface",
            context={
                "reason": self.reason.model_dump(mode="json"),
                "diagnostic": self.diagnostic,
            },
        )
