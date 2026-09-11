from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from core.workflow_definitions import (
    WorkflowDefinition,
    accept_workflow_candidate,
    promote_recovery_workflow_definition,
    promote_workflow_draft,
)
from core.workflow_drafts import WorkflowDraft, canonical_json_bytes
from data_vault.workflow_definition_repository import (
    WorkflowDefinitionRepository,
    WorkflowDefinitionRevisionConflict,
    WorkflowDefinitionSchemaError,
    rollback_workflow_definition_schema,
    upgrade_workflow_definition_schema,
)


CORE_FIXTURE = (
    Path(__file__).parents[2]
    / "core"
    / "tests"
    / "fixtures"
    / "workflow_drafts"
    / "representative-workflow.json"
)
RECOVERY_FIXTURE = (
    Path(__file__).parents[3]
    / "specs"
    / "080-canonical-workflow-recovery"
    / "fixtures"
    / "mounting-bracket.workflow.json"
)


def load_legacy() -> WorkflowDraft:
    return WorkflowDraft.model_validate_json(CORE_FIXTURE.read_bytes())


def next_definition(current: WorkflowDefinition) -> WorkflowDefinition:
    payload = current.model_dump(mode="json")
    payload["metadata"]["title"] = "Promoted product definition revision 2"
    payload["semantic_sha256"] = None
    candidate = WorkflowDefinition.model_validate(payload)
    return accept_workflow_candidate(current, candidate)


def test_promotion_uses_independent_sidecar_and_exact_legacy_rollback(tmp_path) -> None:
    primary = tmp_path / "wright.sqlite3"
    repository = WorkflowDefinitionRepository(primary)
    legacy = load_legacy()
    promotion = promote_workflow_draft(legacy)

    repository.create_from_promotion(promotion)

    assert repository.db_path == tmp_path / "workflow-definitions.sqlite3"
    assert not primary.exists()
    assert not (tmp_path / "workflow-drafts.sqlite3").exists()
    assert repository.read(legacy.draft_id) == promotion.definition
    assert canonical_json_bytes(
        repository.read_legacy_rollback(legacy.draft_id, 1)
    ) == (canonical_json_bytes(legacy))


def test_recovery_promotion_persists_stable_definition_and_exact_source(
    tmp_path,
) -> None:
    repository = WorkflowDefinitionRepository(tmp_path / "wright.sqlite3")
    source = RECOVERY_FIXTURE.read_bytes()
    promotion = promote_recovery_workflow_definition(source)

    repository.create_from_recovery_promotion(promotion)

    stored = repository.read(promotion.definition.workflow_id)
    assert stored == promotion.definition
    assert stored is not None
    assert stored.schema_version == "2.0.0"
    assert stored.revision == 2
    assert (
        repository.read_recovery_rollback(stored.workflow_id, stored.revision) == source
    )
    assert repository.read_recovery_rollback(stored.workflow_id, 1) is None
    assert repository.read_legacy_rollback(stored.workflow_id, 1) is None


def test_append_only_compare_and_set_reopen_and_corruption_containment(
    tmp_path,
) -> None:
    primary = tmp_path / "wright.sqlite3"
    repository = WorkflowDefinitionRepository(primary)
    promotion = promote_workflow_draft(load_legacy())
    first = promotion.definition
    second = next_definition(first)
    repository.create_from_promotion(promotion)
    repository.save(second, expected_revision=1)

    reopened = WorkflowDefinitionRepository(primary)
    assert reopened.read(first.workflow_id) == second
    assert reopened.read_revision(first.workflow_id, 1) == first
    assert reopened.read_revision(first.workflow_id, 2) == second
    with pytest.raises(WorkflowDefinitionRevisionConflict):
        reopened.save(second, expected_revision=1)

    with sqlite3.connect(repository.db_path) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute(
                "UPDATE workflow_definition_revisions SET semantic_sha256 = ?",
                ("f" * 64,),
            )


def test_schema_upgrade_is_transactional_and_empty_schema_can_roll_back(
    tmp_path,
) -> None:
    path = tmp_path / "workflow-definitions.sqlite3"
    with sqlite3.connect(path) as connection:
        assert upgrade_workflow_definition_schema(connection) == 1
        assert upgrade_workflow_definition_schema(connection) == 1
        ledger = connection.execute(
            "SELECT version, name, checksum FROM workflow_definition_schema_migrations"
        ).fetchall()
        assert len(ledger) == 1
        assert ledger[0][0:2] == (1, "canonical_workflow_definitions")
        assert len(ledger[0][2]) == 64

        assert rollback_workflow_definition_schema(connection, target_version=0) == 0
        assert (
            connection.execute(
                "SELECT 1 FROM sqlite_master WHERE name = 'workflow_definition_revisions'"
            ).fetchone()
            is None
        )


def test_populated_schema_refuses_destructive_schema_rollback(tmp_path) -> None:
    repository = WorkflowDefinitionRepository(tmp_path / "wright.sqlite3")
    repository.create_from_promotion(promote_workflow_draft(load_legacy()))

    with sqlite3.connect(repository.db_path) as connection:
        with pytest.raises(WorkflowDefinitionSchemaError, match="contains definitions"):
            rollback_workflow_definition_schema(connection, target_version=0)
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM workflow_definition_revisions"
            ).fetchone()[0]
            == 1
        )


def test_persisted_envelope_digest_mismatch_fails_closed(tmp_path) -> None:
    repository = WorkflowDefinitionRepository(tmp_path / "wright.sqlite3")
    repository.create_from_promotion(promote_workflow_draft(load_legacy()))
    with sqlite3.connect(repository.db_path) as connection:
        connection.execute("DROP TRIGGER workflow_definition_revisions_no_update")
        row = connection.execute(
            "SELECT envelope_json FROM workflow_definition_revisions"
        ).fetchone()
        payload = json.loads(bytes(row[0]))
        payload["metadata"]["title"] = "corrupted"
        connection.execute(
            "UPDATE workflow_definition_revisions SET envelope_json = ?",
            (json.dumps(payload).encode(),),
        )

    with pytest.raises(WorkflowDefinitionSchemaError):
        repository.read(load_legacy().draft_id)


def test_corrupted_recovery_rollback_envelope_fails_closed(tmp_path) -> None:
    repository = WorkflowDefinitionRepository(tmp_path / "wright.sqlite3")
    promotion = promote_recovery_workflow_definition(RECOVERY_FIXTURE.read_bytes())
    recovery_revision = promotion.definition.revision
    assert recovery_revision == 2
    repository.create_from_recovery_promotion(promotion)
    with sqlite3.connect(repository.db_path) as connection:
        connection.execute("DROP TRIGGER workflow_definition_revisions_no_update")
        connection.execute(
            "UPDATE workflow_definition_revisions SET source_envelope_json = ?",
            (b"{}",),
        )

    with pytest.raises(WorkflowDefinitionSchemaError):
        repository.read_recovery_rollback(
            promotion.definition.workflow_id, recovery_revision
        )
