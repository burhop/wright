from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from core.workflow_drafts import WorkflowDraft, canonical_json_bytes, canonical_sha256
from data_vault.workflow_draft_repository import (
    WorkflowDraftRepository,
    WorkflowDraftRevisionConflict,
    WorkflowDraftStorageError,
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


def next_revision(draft: WorkflowDraft, *, x_offset: int = 0) -> WorkflowDraft:
    payload = draft.model_dump(mode="json")
    payload["revision"] += 1
    payload["layout"]["positions"][0]["x"] += x_offset
    payload["layout_sha256"] = canonical_sha256(payload["layout"])
    return WorkflowDraft.model_validate(payload)


def test_sidecar_is_lazy_canonical_and_independent_of_primary_database(tmp_path) -> None:
    primary = tmp_path / "wright.sqlite3"
    repository = WorkflowDraftRepository(primary)

    assert repository.db_path == tmp_path / "workflow-drafts.sqlite3"
    assert repository.read("draft.missing") is None
    assert not repository.db_path.exists()

    draft = load_draft()
    repository.create(draft)

    assert not primary.exists()
    assert repository.read(draft.draft_id) == draft
    with sqlite3.connect(repository.db_path) as connection:
        journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
        stored = connection.execute(
            "SELECT envelope_json FROM workflow_draft_revisions"
        ).fetchone()[0]
    assert journal_mode == "wal"
    assert bytes(stored) == canonical_json_bytes(draft)


def test_save_appends_revision_and_stale_compare_and_set_preserves_head(
    tmp_path,
) -> None:
    repository = WorkflowDraftRepository(tmp_path / "wright.sqlite3")
    first = load_draft()
    second = next_revision(first, x_offset=16)
    stale_second = next_revision(first, x_offset=32)

    repository.create(first)
    repository.save(second, expected_revision=1)

    with pytest.raises(WorkflowDraftRevisionConflict):
        repository.save(stale_second, expected_revision=1)

    assert repository.read(first.draft_id) == second
    assert repository.read_revision(first.draft_id, 1) == first
    assert repository.read_revision(first.draft_id, 2) == second
    with sqlite3.connect(repository.db_path) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM workflow_draft_revisions WHERE draft_id = ?",
            (first.draft_id,),
        ).fetchone()[0]
    assert count == 2


def test_failed_revision_insert_rolls_back_head_update(tmp_path) -> None:
    repository = WorkflowDraftRepository(tmp_path / "wright.sqlite3")
    first = load_draft()
    second = next_revision(first, x_offset=16)
    repository.create(first)

    with sqlite3.connect(repository.db_path) as connection:
        connection.execute(
            """INSERT INTO workflow_draft_revisions
            (draft_id, revision, semantic_sha256, layout_sha256, envelope_json)
            VALUES (?, ?, ?, ?, ?)""",
            (
                second.draft_id,
                second.revision,
                second.semantic_sha256,
                second.layout_sha256,
                canonical_json_bytes(second),
            ),
        )

    with pytest.raises(WorkflowDraftStorageError):
        repository.save(second, expected_revision=1)

    assert repository.read(first.draft_id) == first


def test_save_rejects_nonconsecutive_revision_without_writing(tmp_path) -> None:
    repository = WorkflowDraftRepository(tmp_path / "wright.sqlite3")
    first = load_draft()
    payload = json.loads(canonical_json_bytes(first))
    payload["revision"] = 3
    third = WorkflowDraft.model_validate(payload)
    repository.create(first)

    with pytest.raises(ValueError, match="next consecutive revision"):
        repository.save(third, expected_revision=1)

    assert repository.read(first.draft_id) == first
    assert repository.read_revision(first.draft_id, 3) is None
