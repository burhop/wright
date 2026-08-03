"""Neutral values for an isolated workspace-bound workflow editor."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class EditorAvailability(StrEnum):
    DISABLED = "disabled"
    AVAILABLE = "available"
    MISSING = "missing"
    INCOMPATIBLE = "incompatible"


class WorkflowEditorError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class EditorAssetManifest:
    rivet_version: str
    entrypoint: str | None
    sha256: str | None
    license: str


@dataclass(frozen=True, slots=True)
class EditorBootstrap:
    availability: EditorAvailability
    grant_id: str | None
    workflow_id: str | None
    revision: int | None
    etag: str | None
    expires_at: datetime | None
    detail: str | None = None
