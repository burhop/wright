"""Stable domain error vocabulary without transport or infrastructure types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    NOT_FOUND = "not_found"
    INVALID_INPUT = "invalid_input"
    CONFLICT = "conflict"
    FORBIDDEN_PATH = "forbidden_path"
    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    INTERNAL = "internal"


@dataclass(frozen=True, slots=True)
class ErrorDetail:
    code: ErrorCode
    message: str
    operation: str | None = None
    context: dict[str, Any] = field(default_factory=dict)


class WrightError(Exception):
    """Base exception carrying a safe, serializable error detail."""

    def __init__(self, detail: ErrorDetail) -> None:
        super().__init__(detail.message)
        self.detail = detail
