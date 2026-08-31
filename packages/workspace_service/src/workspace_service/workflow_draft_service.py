"""Application orchestration for provisional visual workflow drafts."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from core.workflow_draft_validation import (
    WorkflowDraftDiagnostic,
    validate_workflow_draft,
)
from core.workflow_drafts import (
    Phase,
    WorkflowDraft,
    WorkflowLayout,
    WorkflowSemantic,
    canonical_sha256,
)
from data_vault import (
    WorkflowDraftAlreadyExists,
    WorkflowDraftRepository,
    WorkflowDraftRevisionConflict,
)


class WorkflowDraftNotFoundError(LookupError):
    """The requested draft does not exist in the local draft store."""


class WorkflowDraftIdentityMismatchError(ValueError):
    """Path, envelope, or revision identity does not match the current draft."""


class WorkflowDraftConflictError(RuntimeError):
    """A save expected a draft revision that is no longer current."""

    def __init__(self, *, expected_revision: int, current_revision: int) -> None:
        super().__init__("The workflow draft changed; reopen it before saving again")
        self.expected_revision = expected_revision
        self.current_revision = current_revision


class WorkflowDraftInvalidError(ValueError):
    """A candidate failed deterministic semantic or layout validation."""

    def __init__(
        self, diagnostics: tuple[WorkflowDraftDiagnostic, ...]
    ) -> None:
        super().__init__("The workflow draft candidate is invalid")
        self.diagnostics = diagnostics


@dataclass(frozen=True, slots=True)
class WorkflowDraftValidationResult:
    valid: bool
    semantic_sha256: str
    layout_sha256: str
    diagnostics: tuple[WorkflowDraftDiagnostic, ...]


def _new_draft_id() -> str:
    return f"draft.{uuid.uuid4().hex}"


class WorkflowDraftService:
    """Create, validate, reopen, and atomically save valid draft revisions."""

    def __init__(
        self,
        primary_database_path: str | Path | None = None,
        *,
        repository: WorkflowDraftRepository | None = None,
        id_factory: Callable[[], str] = _new_draft_id,
    ) -> None:
        if repository is None:
            if primary_database_path is None:
                raise ValueError(
                    "A primary database path or workflow draft repository is required"
                )
            repository = WorkflowDraftRepository(primary_database_path)
        self.repository = repository
        self.id_factory = id_factory

    def create(
        self,
        *,
        title: str = "Untitled workflow",
        purpose: str = "Compose a provisional engineering workflow.",
    ) -> WorkflowDraft:
        semantic = WorkflowSemantic(
            title=title,
            purpose=purpose,
            phases=(
                Phase(
                    id="phase.draft",
                    name="Draft",
                    purpose="Organize provisional workflow blocks.",
                    order=0,
                    block_ids=(),
                ),
            ),
            blocks=(),
            ports=(),
            connections=(),
            gates=(),
            feedback_paths=(),
            intended_artifacts=(),
        )
        layout = WorkflowLayout(schema_version="1.0.0", positions=())
        draft = WorkflowDraft(
            document_kind="workflow-draft",
            schema_version="1.0.0-draft.1",
            draft_id=self.id_factory(),
            revision=1,
            semantic_sha256=canonical_sha256(semantic),
            layout_sha256=canonical_sha256(layout),
            semantic=semantic,
            layout=layout,
        )
        validation = self.validate(draft)
        if not validation.valid:
            raise WorkflowDraftInvalidError(validation.diagnostics)
        try:
            self.repository.create(draft)
        except WorkflowDraftAlreadyExists as error:
            raise WorkflowDraftConflictError(
                expected_revision=0, current_revision=1
            ) from error
        return draft

    def read(self, draft_id: str) -> WorkflowDraft:
        draft = self.repository.read(draft_id)
        if draft is None:
            raise WorkflowDraftNotFoundError("Workflow draft not found")
        return draft

    @staticmethod
    def validate(candidate: WorkflowDraft) -> WorkflowDraftValidationResult:
        diagnostics = validate_workflow_draft(candidate)
        return WorkflowDraftValidationResult(
            valid=not diagnostics,
            semantic_sha256=candidate.semantic_sha256,
            layout_sha256=candidate.layout_sha256,
            diagnostics=diagnostics,
        )

    def save(
        self,
        draft_id: str,
        candidate: WorkflowDraft,
        *,
        expected_revision: int,
    ) -> WorkflowDraft:
        current = self.read(draft_id)
        if current.revision != expected_revision:
            raise WorkflowDraftConflictError(
                expected_revision=expected_revision,
                current_revision=current.revision,
            )
        if candidate.draft_id != draft_id or candidate.revision != expected_revision:
            raise WorkflowDraftIdentityMismatchError(
                "Workflow draft identity does not match the requested current revision"
            )

        validation = self.validate(candidate)
        if not validation.valid:
            raise WorkflowDraftInvalidError(validation.diagnostics)

        saved = WorkflowDraft(
            document_kind=candidate.document_kind,
            schema_version=candidate.schema_version,
            draft_id=candidate.draft_id,
            revision=expected_revision + 1,
            semantic_sha256=canonical_sha256(candidate.semantic),
            layout_sha256=canonical_sha256(candidate.layout),
            semantic=candidate.semantic,
            layout=candidate.layout,
        )
        try:
            self.repository.save(saved, expected_revision=expected_revision)
        except WorkflowDraftRevisionConflict as error:
            latest = self.repository.read(draft_id)
            current_revision = latest.revision if latest is not None else expected_revision
            raise WorkflowDraftConflictError(
                expected_revision=expected_revision,
                current_revision=current_revision,
            ) from error
        return saved


__all__ = [
    "WorkflowDraftConflictError",
    "WorkflowDraftIdentityMismatchError",
    "WorkflowDraftInvalidError",
    "WorkflowDraftNotFoundError",
    "WorkflowDraftService",
    "WorkflowDraftValidationResult",
]
