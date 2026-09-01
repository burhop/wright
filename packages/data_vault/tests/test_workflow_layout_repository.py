from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from core.workflow_definitions import promote_recovery_workflow_definition
from core.workflow_layouts import (
    WorkflowLayout,
    canonical_layout_sha256,
    layout_envelope_bytes,
    promote_recovery_workflow_layout,
)
from data_vault.workflow_layout_repository import (
    WorkflowLayoutRepository,
    WorkflowLayoutRevisionConflict,
    WorkflowLayoutSchemaError,
    rollback_workflow_layout_schema,
    upgrade_workflow_layout_schema,
)


ROOT = Path(__file__).parents[3]
DEFINITION_FIXTURE = (
    ROOT
    / "specs"
    / "080-canonical-workflow-recovery"
    / "fixtures"
    / "mounting-bracket.workflow.json"
)
LAYOUT_FIXTURE = (
    ROOT
    / "specs"
    / "080-canonical-workflow-recovery"
    / "fixtures"
    / "mounting-bracket.layout.json"
)


def load_definition():
    return promote_recovery_workflow_definition(
        DEFINITION_FIXTURE.read_bytes()
    ).definition


def load_promotion():
    return promote_recovery_workflow_layout(
        LAYOUT_FIXTURE.read_bytes(), load_definition()
    )


def next_layout(current: WorkflowLayout) -> WorkflowLayout:
    payload = current.model_dump(mode="json")
    payload["layout_revision"] += 1
    payload["positions"]["block.capture-brief"] = {"x": 700, "y": 240}
    return WorkflowLayout.model_validate(payload)


def test_create_reopen_save_and_exact_recovery_source(tmp_path) -> None:
    primary = tmp_path / "wright.sqlite3"
    repository = WorkflowLayoutRepository(primary)
    promotion = load_promotion()

    repository.create_from_recovery_promotion(promotion)

    assert repository.db_path == tmp_path / "workflow-layouts.sqlite3"
    assert not primary.exists()
    assert not (tmp_path / "workflow-drafts.sqlite3").exists()
    assert not (tmp_path / "workflow-definitions.sqlite3").exists()
    assert repository.read(promotion.layout.workflow_id) == promotion.layout
    reopened = repository.reopen(promotion.layout.workflow_id)
    assert reopened.layout == promotion.layout
    assert reopened.original == layout_envelope_bytes(promotion.layout)
    assert repository.read_recovery_rollback(promotion.layout.workflow_id, 1) == (
        LAYOUT_FIXTURE.read_bytes()
    )

    second = next_layout(promotion.layout)
    repository.save(second, load_definition(), expected_layout_revision=1)
    assert repository.read(second.workflow_id) == second
    assert repository.read_revision(second.workflow_id, 1) == promotion.layout
    assert repository.read_revision(second.workflow_id, 2) == second
    with pytest.raises(WorkflowLayoutRevisionConflict):
        repository.save(second, load_definition(), expected_layout_revision=1)


def test_unknown_stored_version_reopens_with_original_bytes(tmp_path) -> None:
    repository = WorkflowLayoutRepository(tmp_path / "wright.sqlite3")
    payload = json.loads(LAYOUT_FIXTURE.read_text(encoding="utf-8"))
    payload["schema_version"] = "99.0.0"
    original = json.dumps(payload, separators=(",", ":")).encode()
    digest = hashlib.sha256(original).hexdigest()
    with sqlite3.connect(repository.db_path) as connection:
        upgrade_workflow_layout_schema(connection)
        connection.execute(
            """INSERT INTO workflow_layout_revisions
            (workflow_id, layout_revision, parent_layout_revision, semantic_revision,
             layout_sha256, envelope_json, source_document_kind, source_schema_version,
             source_envelope_json, source_envelope_sha256)
            VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL)""",
            ("workflow.mounting-bracket", 1, None, 1, digest, original),
        )
        connection.execute(
            """INSERT INTO workflow_layout_heads
            (workflow_id, current_layout_revision, layout_sha256)
            VALUES (?, ?, ?)""",
            ("workflow.mounting-bracket", 1, digest),
        )

    result = repository.reopen("workflow.mounting-bracket")

    assert result.layout is None
    assert result.original == original
    assert result.diagnostics[0].code == "WFR-LAYOUT-VERSION-UNSUPPORTED"


def test_schema_rollback_is_empty_only_and_transactional(tmp_path) -> None:
    path = tmp_path / "workflow-layouts.sqlite3"
    with sqlite3.connect(path) as connection:
        assert upgrade_workflow_layout_schema(connection) == 1
        assert upgrade_workflow_layout_schema(connection) == 1
        assert rollback_workflow_layout_schema(connection, target_version=0) == 0

    repository = WorkflowLayoutRepository(tmp_path / "wright.sqlite3")
    repository.create_from_recovery_promotion(load_promotion())
    with sqlite3.connect(repository.db_path) as connection:
        with pytest.raises(WorkflowLayoutSchemaError, match="contains layouts"):
            rollback_workflow_layout_schema(connection, target_version=0)


def test_corrupted_stable_and_recovery_envelopes_fail_closed(tmp_path) -> None:
    repository = WorkflowLayoutRepository(tmp_path / "wright.sqlite3")
    promotion = load_promotion()
    repository.create_from_recovery_promotion(promotion)
    with sqlite3.connect(repository.db_path) as connection:
        connection.execute("DROP TRIGGER workflow_layout_revisions_no_update")
        connection.execute(
            "UPDATE workflow_layout_revisions SET envelope_json = ?",
            (b"{}",),
        )
    with pytest.raises(WorkflowLayoutSchemaError):
        repository.read(promotion.layout.workflow_id)

    clean = WorkflowLayoutRepository(tmp_path / "other" / "wright.sqlite3")
    clean.create_from_recovery_promotion(promotion)
    with sqlite3.connect(clean.db_path) as connection:
        connection.execute("DROP TRIGGER workflow_layout_revisions_no_update")
        connection.execute(
            "UPDATE workflow_layout_revisions SET source_envelope_json = ?",
            (b"{}",),
        )
    with pytest.raises(WorkflowLayoutSchemaError):
        clean.read_recovery_rollback(promotion.layout.workflow_id, 1)


def test_persisted_layout_digest_matches_canonical_envelope(tmp_path) -> None:
    repository = WorkflowLayoutRepository(tmp_path / "wright.sqlite3")
    promotion = load_promotion()
    repository.create_from_recovery_promotion(promotion)

    with sqlite3.connect(repository.db_path) as connection:
        row = connection.execute(
            "SELECT layout_sha256, envelope_json FROM workflow_layout_revisions"
        ).fetchone()

    assert row[0] == canonical_layout_sha256(promotion.layout)
    assert hashlib.sha256(bytes(row[1])).hexdigest() == row[0]


def test_forged_promotion_digest_is_rejected_before_storage(tmp_path) -> None:
    repository = WorkflowLayoutRepository(tmp_path / "wright.sqlite3")
    forged = replace(load_promotion(), source_envelope_sha256="f" * 64)

    with pytest.raises(ValueError, match="source digest mismatch"):
        repository.create_from_recovery_promotion(forged)

    assert not repository.db_path.exists()
