from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from core.canonical_workflow_runs import (
    CanonicalWorkflowRun,
    WorkflowArtifactRecord,
    WorkflowRunActivity,
    WorkflowRunStepRecord,
)
from core.workflow_definitions import promote_recovery_workflow_definition
from data_vault.workflow_execution_repository import (
    CanonicalWorkflowRunRepository,
    WorkflowExecutionSchemaError,
    WorkflowRunStateConflict,
    rollback_workflow_execution_schema,
    upgrade_workflow_execution_schema,
)


ROOT = Path(__file__).parents[3]
DEFINITION_FIXTURE = (
    ROOT
    / "specs"
    / "080-canonical-workflow-recovery"
    / "fixtures"
    / "mounting-bracket.workflow.json"
)


def definition():
    return promote_recovery_workflow_definition(
        DEFINITION_FIXTURE.read_bytes()
    ).definition


def run() -> CanonicalWorkflowRun:
    subject = definition()
    return CanonicalWorkflowRun(
        document_kind="workflow-run",
        schema_version="1.0.0",
        run_id="run.production-001",
        workflow_id=subject.workflow_id,
        workflow_revision=subject.revision,
        semantic_sha256=subject.semantic_sha256,
        created_at=100,
        completed_at=None,
        mode="simulated",
        state="queued",
        active_block_id=None,
        active_relationship_id=None,
        material_supplied=False,
        outputs_ready=False,
        cleanup_state="retained",
    )


def repository(tmp_path) -> CanonicalWorkflowRunRepository:
    return CanonicalWorkflowRunRepository(tmp_path / "wright.sqlite3")


def activity(sequence: int, kind: str, at: int) -> WorkflowRunActivity:
    return WorkflowRunActivity(
        run_id=run().run_id,
        sequence=sequence,
        occurred_at=at,
        kind=kind,
        summary=kind.replace("_", " ").title(),
        evidence_reference=f"trace://run.production-001/{sequence}",
    )


def artifact(*, lifetime: str = "retained") -> WorkflowArtifactRecord:
    return WorkflowArtifactRecord(
        artifact_id="artifact.step-output-001",
        run_id=run().run_id,
        step_id="step.export-001",
        contract_id="artifact.step",
        type_id="type.file.step",
        media_type="model/step",
        digest_sha256="a" * 64,
        size_bytes=1024,
        producer_block_id="block.export-step",
        upstream_artifact_ids=(),
        storage_reference="vault://runs/run.production-001/bracket.step",
        preview_state="ready",
        allowed_actions=("inspect", "preview", "open", "download"),
        lifetime=lifetime,
        expires_at=125 if lifetime == "ephemeral" else None,
        cleanup_state="retained",
    )


def step() -> WorkflowRunStepRecord:
    return WorkflowRunStepRecord(
        run_id=run().run_id,
        step_id="step.export-001",
        block_id="block.export-step",
        attempt=1,
        state="succeeded",
        started_at=110,
        completed_at=120,
        input_artifact_ids=(),
        output_artifact_ids=(artifact().artifact_id,),
        diagnosis_codes=(),
        component_scope=None,
    )


def test_independent_create_and_immutable_definition_subject(tmp_path) -> None:
    repo = repository(tmp_path)
    repo.create(run(), definition())

    assert repo.db_path == tmp_path / "workflow-runs.sqlite3"
    assert not (tmp_path / "wright.sqlite3").exists()
    assert not (tmp_path / "workflow-definitions.sqlite3").exists()
    assert not (tmp_path / "workflow-layouts.sqlite3").exists()
    assert repo.get(run().run_id) == run()

    with sqlite3.connect(repo.db_path) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="identity is immutable"):
            connection.execute(
                "UPDATE canonical_workflow_runs SET semantic_sha256 = ?",
                ("f" * 64,),
            )


def test_steps_artifacts_activity_and_cursor_reconnect(tmp_path) -> None:
    repo = repository(tmp_path)
    repo.create(run(), definition())
    repo.append_activity(activity(1, "registered", 100))
    repo.append_activity(activity(2, "connected", 101))
    step_record = step()
    repo.record_step(step_record, definition())
    repo.record_artifact(artifact(), definition())

    snapshot = repo.reconnect(run().run_id, after_sequence=1)

    assert snapshot.run == run()
    assert snapshot.steps == (step_record,)
    assert snapshot.artifacts == (artifact(),)
    assert [event.sequence for event in snapshot.activities] == [2]
    assert snapshot.cursor == 2
    with pytest.raises(ValueError, match="contiguous"):
        repo.append_activity(activity(4, "progress", 102))


def test_cancellation_is_atomic_and_terminal(tmp_path) -> None:
    repo = repository(tmp_path)
    repo.create(run(), definition())
    repo.append_activity(activity(1, "registered", 100))
    repo.transition(run().run_id, "running", expected_state="queued", at=105)

    cancelling = repo.request_cancel(run().run_id, at=110)
    cancelled = repo.complete_cancel(run().run_id, at=111)

    assert cancelling.state == "cancelling"
    assert cancelled.state == "cancelled"
    assert cancelled.completed_at == 111
    assert [event.kind for event in repo.reconnect(run().run_id).activities] == [
        "registered",
        "progress",
        "cancel_requested",
        "terminal",
    ]
    with pytest.raises(WorkflowRunStateConflict):
        repo.transition(run().run_id, "running", expected_state="queued", at=112)


def test_cleanup_preserves_artifact_lineage_and_is_idempotent(tmp_path) -> None:
    repo = repository(tmp_path)
    repo.create(run(), definition())
    repo.append_activity(activity(1, "registered", 100))
    repo.record_step(step(), definition())
    repo.record_artifact(artifact(lifetime="ephemeral"), definition())
    repo.transition(run().run_id, "running", expected_state="queued", at=105)
    repo.transition(run().run_id, "succeeded", expected_state="running", at=120)

    cleaned = repo.cleanup(run().run_id, at=130)
    repeated = repo.cleanup(run().run_id, at=131)

    assert cleaned.run.cleanup_state == "cleaned"
    assert cleaned.artifacts[0].cleanup_state == "cleaned"
    assert cleaned.artifacts[0].digest_sha256 == "a" * 64
    assert repeated.cursor == cleaned.cursor
    assert repeated.activities[-1].kind == "cleanup"


def test_needs_input_resume_and_direct_queued_cancel_have_complete_activity(
    tmp_path,
) -> None:
    repo = repository(tmp_path)
    repo.create(run(), definition())
    repo.transition(run().run_id, "running", expected_state="queued", at=101)
    repo.transition(run().run_id, "needs_input", expected_state="running", at=102)
    repo.transition(run().run_id, "running", expected_state="needs_input", at=103)

    assert [event.kind for event in repo.reconnect(run().run_id).activities] == [
        "progress",
        "needs_input",
        "resumed",
    ]

    second = run().model_copy(update={"run_id": "run.production-002"})
    repo.create(second, definition())
    repo.request_cancel(second.run_id, at=104)
    assert [event.kind for event in repo.reconnect(second.run_id).activities] == [
        "cancel_requested",
        "terminal",
    ]


def test_complete_projection_transition_records_active_identity_and_output_facts(
    tmp_path,
) -> None:
    repo = repository(tmp_path)
    repo.create(run(), definition())
    candidate = run().model_copy(
        update={
            "state": "running",
            "active_block_id": "block.design-intent",
            "material_supplied": True,
            "outputs_ready": True,
        }
    )

    updated = repo.transition_projection(
        candidate, definition(), expected_state="queued", at=105
    )

    assert updated.active_block_id == "block.design-intent"
    assert updated.material_supplied is True
    assert updated.outputs_ready is True
    assert repo.get(run().run_id) == updated


def test_cleanup_rejects_nonterminal_run(tmp_path) -> None:
    repo = repository(tmp_path)
    repo.create(run(), definition())

    with pytest.raises(WorkflowRunStateConflict, match="terminal"):
        repo.cleanup(run().run_id, at=110)


def test_schema_rollback_is_empty_only(tmp_path) -> None:
    path = tmp_path / "workflow-runs.sqlite3"
    with sqlite3.connect(path) as connection:
        assert upgrade_workflow_execution_schema(connection) == 1
        assert rollback_workflow_execution_schema(connection, target_version=0) == 0

    repo = repository(tmp_path)
    repo.create(run(), definition())
    with sqlite3.connect(repo.db_path) as connection:
        with pytest.raises(WorkflowExecutionSchemaError, match="contains runs"):
            rollback_workflow_execution_schema(connection, target_version=0)


def test_corrupted_run_subject_fails_closed_on_reopen(tmp_path) -> None:
    repo = repository(tmp_path)
    repo.create(run(), definition())
    with sqlite3.connect(repo.db_path) as connection:
        connection.execute("DROP TRIGGER canonical_workflow_runs_identity_no_update")
        connection.execute(
            "UPDATE canonical_workflow_runs SET semantic_sha256 = ?",
            ("f" * 64,),
        )

    with pytest.raises(WorkflowExecutionSchemaError):
        repo.get(run().run_id)


def test_historical_recovery_run_keeps_original_definition_digest_and_bytes(
    tmp_path,
) -> None:
    repo = repository(tmp_path)
    original = (
        b'{"document_kind":"workflow-run","schema_version":"1.0.0-recovery.1",'
        b'"run_id":"run.recovery-001","workflow_id":"workflow.mounting-bracket",'
        b'"workflow_revision":1,"semantic_sha256":"'
        + b"57ed2b7caacc9b3a779d9e960a681a9b8fe6dc1cfc9c3d48fa6ddd5e184be889"
        + b'","state":"succeeded"}'
    )

    captured = repo.archive_recovery_run(original)
    repo.create(run(), definition())

    assert captured.semantic_sha256 != run().semantic_sha256
    assert repo.read_recovery_run(captured.run_id) == original
    with sqlite3.connect(repo.db_path) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute(
                "UPDATE recovery_workflow_run_envelopes SET semantic_sha256 = ?",
                (run().semantic_sha256,),
            )
