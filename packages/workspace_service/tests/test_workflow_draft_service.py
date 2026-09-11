from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.workflow_drafts import WorkflowDraft, canonical_sha256
from data_vault import WorkflowDraftRepository
from workspace_service.workflow_draft_service import (
    WorkflowDraftConflictError,
    WorkflowDraftInvalidError,
    WorkflowDraftNotFoundError,
    WorkflowDraftService,
)


FIXTURE = (
    Path(__file__).parents[2]
    / "core"
    / "tests"
    / "fixtures"
    / "workflow_drafts"
    / "representative-workflow.json"
)


def load_draft() -> WorkflowDraft:
    return WorkflowDraft.model_validate_json(FIXTURE.read_bytes())


def candidate_with_layout_offset(draft: WorkflowDraft, offset: int) -> WorkflowDraft:
    payload = draft.model_dump(mode="json")
    payload["layout"]["positions"][0]["x"] += offset
    payload["layout_sha256"] = canonical_sha256(payload["layout"])
    return WorkflowDraft.model_validate(payload)


def test_create_returns_a_valid_empty_revision_and_read_reopens_it(tmp_path) -> None:
    service = WorkflowDraftService(
        tmp_path / "wright.sqlite3", id_factory=lambda: "draft.new-workflow"
    )

    created = service.create(title="New workflow", purpose="Compose a safe draft.")

    assert created.draft_id == "draft.new-workflow"
    assert created.revision == 1
    assert created.semantic.blocks == ()
    assert created.layout.positions == ()
    assert service.validate(created).valid
    assert service.read(created.draft_id) == created
    with pytest.raises(WorkflowDraftNotFoundError):
        service.read("draft.missing")


def test_invalid_candidate_preserves_last_valid_saved_revision(tmp_path) -> None:
    repository = WorkflowDraftRepository(tmp_path / "wright.sqlite3")
    first = load_draft()
    repository.create(first)
    service = WorkflowDraftService(repository=repository)
    payload = json.loads(first.model_dump_json())
    payload["layout"]["positions"].pop()
    payload["layout_sha256"] = canonical_sha256(payload["layout"])
    invalid = WorkflowDraft.model_validate(payload)

    validation = service.validate(invalid)
    assert not validation.valid
    assert [item.code for item in validation.diagnostics] == [
        "LAYOUT_BLOCK_POSITION_MISSING"
    ]

    with pytest.raises(WorkflowDraftInvalidError) as captured:
        service.save(first.draft_id, invalid, expected_revision=1)

    assert captured.value.diagnostics == validation.diagnostics
    assert repository.read(first.draft_id) == first


def test_save_revalidates_and_assigns_the_next_revision(tmp_path) -> None:
    repository = WorkflowDraftRepository(tmp_path / "wright.sqlite3")
    first = load_draft()
    repository.create(first)
    service = WorkflowDraftService(repository=repository)
    candidate = candidate_with_layout_offset(first, 24)

    saved = service.save(first.draft_id, candidate, expected_revision=1)

    assert candidate.revision == 1
    assert saved.revision == 2
    assert saved.layout.positions[0].x == first.layout.positions[0].x + 24
    assert saved.layout_sha256 == canonical_sha256(saved.layout)
    assert repository.read(first.draft_id) == saved


def test_stale_save_reports_conflict_and_preserves_current_revision(tmp_path) -> None:
    repository = WorkflowDraftRepository(tmp_path / "wright.sqlite3")
    first = load_draft()
    repository.create(first)
    service = WorkflowDraftService(repository=repository)
    current = service.save(
        first.draft_id,
        candidate_with_layout_offset(first, 24),
        expected_revision=1,
    )

    with pytest.raises(WorkflowDraftConflictError) as captured:
        service.save(
            first.draft_id,
            candidate_with_layout_offset(first, 48),
            expected_revision=1,
        )

    assert captured.value.expected_revision == 1
    assert captured.value.current_revision == 2
    assert repository.read(first.draft_id) == current
