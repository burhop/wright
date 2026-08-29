"""Closed response and error skeletons for the read-only program-status API."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ClosedProgramStatusModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProgramStatusErrorCode(StrEnum):
    UNAVAILABLE = "PROGRAM_STATUS_UNAVAILABLE"
    IDENTITY_MISMATCH = "PROGRAM_STATUS_IDENTITY_MISMATCH"
    INVALID = "PROGRAM_STATUS_INVALID"
    READ_FAILED = "PROGRAM_STATUS_READ_FAILED"
    PUBLISHER_UNAVAILABLE = "PROGRAM_STATUS_PUBLISHER_UNAVAILABLE"
    PUBLISHER_INVALID = "PROGRAM_STATUS_PUBLISHER_INVALID"
    PUBLISHER_READ_FAILED = "PROGRAM_STATUS_PUBLISHER_READ_FAILED"


class ProgramStatusErrorResponse(ClosedProgramStatusModel):
    error_code: ProgramStatusErrorCode
    message: str = Field(min_length=1, max_length=500)
    recovery_class: str = Field(min_length=1, max_length=100)
    trace_id: str = Field(min_length=1, max_length=200)


class ProgramStatusEvidenceReferenceResponse(ClosedProgramStatusModel):
    id: str = Field(min_length=1, max_length=160)
    path: str = Field(min_length=1, max_length=500)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ProgramStatusSourceResponse(ClosedProgramStatusModel):
    commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    tree: str = Field(pattern=r"^[0-9a-f]{40}$")
    program_tree: str = Field(pattern=r"^[0-9a-f]{40}$")
    snapshot_path: str = Field(min_length=1, max_length=500)
    snapshot_raw_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    raw_identity_verification: Literal["publisher_git_blob_attested"]
    raw_identity_evidence: ProgramStatusEvidenceReferenceResponse
    dashboard_canonical_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_catalog_path: Literal[
        "specs/077-browser-program-status/contracts/program-status-source-catalog.json"
    ]
    source_catalog_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    validation_transition: str = Field(pattern=r"^TR-[0-9]{4}$")
    validation_verdict: Literal["passed"]


class ProgramStatusBundleResponse(ClosedProgramStatusModel):
    """Closed transport shell; tool_registry owns nested semantic validation."""

    schema_version: Literal["1.0.0"]
    bundle_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    generated_at: str = Field(min_length=1, max_length=100)
    source: ProgramStatusSourceResponse
    dashboard: dict[str, Any]
    supplement: dict[str, Any]


class ProgramStatusPublisherResponse(ClosedProgramStatusModel):
    """Bounded operational publisher state; never readiness or authority."""

    state: Literal["active", "inactive", "failed", "unavailable"]
    mode: str = Field(min_length=1, max_length=100)
    observed_commit: str | None = Field(default=None, pattern=r"^[0-9a-f]{40}$")
    last_attempt_at: str | None = Field(default=None, max_length=100)
    last_success_at: str | None = Field(default=None, max_length=100)
    failure_code: str | None = Field(default=None, max_length=100)
    recovery: str | None = Field(default=None, max_length=500)
