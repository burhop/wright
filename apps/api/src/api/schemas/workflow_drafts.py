"""Closed transport contracts for provisional workflow draft authoring."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from core.workflow_draft_validation import WorkflowDraftDiagnostic
from core.workflow_drafts import WorkflowDraft
from workspace_service import WorkflowDraftValidationResult


Digest = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
DiagnosticCode = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=96,
        pattern=r"^[A-Z][A-Z0-9_]*$",
    ),
]
RecoveryClass = Literal[
    "enable_feature",
    "reopen_draft",
    "correct_candidate",
    "install_compatible_wright",
    "refresh_and_retry",
    "retry_or_inspect_local_store",
]


class _ClosedTransport(BaseModel):
    model_config = ConfigDict(extra="forbid")


class WorkflowDraftCreateRequest(_ClosedTransport):
    title: str = Field(default="Untitled workflow", min_length=1, max_length=500)
    purpose: str = Field(
        default="Compose a provisional engineering workflow.",
        min_length=1,
        max_length=500,
    )


class WorkflowDraftEnvelope(WorkflowDraft):
    """The direct versioned draft body used by create, read, validate, and save."""


class WorkflowDraftDiagnosticResponse(_ClosedTransport):
    code: DiagnosticCode
    path: str = Field(min_length=1, max_length=300)
    affected_semantic_ids: tuple[str, ...] = Field(max_length=64)
    explanation: str = Field(min_length=1, max_length=500)
    correction: str = Field(min_length=1, max_length=500)

    @classmethod
    def from_domain(
        cls, diagnostic: WorkflowDraftDiagnostic
    ) -> "WorkflowDraftDiagnosticResponse":
        return cls(
            code=diagnostic.code,
            path=diagnostic.path,
            affected_semantic_ids=diagnostic.affected_semantic_ids,
            explanation=diagnostic.explanation,
            correction=diagnostic.correction,
        )


class WorkflowDraftValidationResponse(_ClosedTransport):
    valid: bool
    semantic_sha256: Digest
    layout_sha256: Digest
    diagnostics: tuple[WorkflowDraftDiagnosticResponse, ...] = Field(max_length=256)

    @classmethod
    def from_domain(
        cls, result: WorkflowDraftValidationResult
    ) -> "WorkflowDraftValidationResponse":
        return cls(
            valid=result.valid,
            semantic_sha256=result.semantic_sha256,
            layout_sha256=result.layout_sha256,
            diagnostics=tuple(
                WorkflowDraftDiagnosticResponse.from_domain(item)
                for item in result.diagnostics
            ),
        )


class WorkflowDraftErrorCode(StrEnum):
    UNAVAILABLE = "WORKFLOW_COMPOSER_UNAVAILABLE"
    NOT_FOUND = "WORKFLOW_DRAFT_NOT_FOUND"
    INVALID = "WORKFLOW_DRAFT_INVALID"
    INCOMPATIBLE_SCHEMA = "WORKFLOW_DRAFT_INCOMPATIBLE_SCHEMA"
    IDENTITY_MISMATCH = "WORKFLOW_DRAFT_IDENTITY_MISMATCH"
    STALE_REVISION = "WORKFLOW_DRAFT_STALE_REVISION"
    STORAGE_FAILED = "WORKFLOW_DRAFT_STORAGE_FAILED"


class WorkflowDraftErrorResponse(_ClosedTransport):
    error_code: WorkflowDraftErrorCode
    message: str = Field(min_length=1, max_length=500)
    recovery_class: RecoveryClass
    trace_id: str = Field(min_length=1, max_length=200)
    diagnostics: tuple[WorkflowDraftDiagnosticResponse, ...] | None = Field(
        default=None, max_length=256
    )


__all__ = [
    "WorkflowDraftCreateRequest",
    "WorkflowDraftDiagnosticResponse",
    "WorkflowDraftEnvelope",
    "WorkflowDraftErrorCode",
    "WorkflowDraftErrorResponse",
    "WorkflowDraftValidationResponse",
]
