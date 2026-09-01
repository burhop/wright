from __future__ import annotations

import socket
from pathlib import Path

from core.canonical_workflow_runs import (
    CanonicalWorkflowRun,
    WorkflowArtifactRecord,
    WorkflowRunActivity,
    WorkflowRunStepRecord,
)
from core.workflow_definitions import promote_recovery_workflow_definition
from core.workflow_layouts import promote_recovery_workflow_layout
from data_vault.workflow_definition_repository import WorkflowDefinitionRepository
from data_vault.workflow_execution_repository import CanonicalWorkflowRunRepository
from data_vault.workflow_layout_repository import WorkflowLayoutRepository


ROOT = Path(__file__).parents[2]
FIXTURES = ROOT / "specs" / "080-canonical-workflow-recovery" / "fixtures"


def _run(definition, run_id: str) -> CanonicalWorkflowRun:
    return CanonicalWorkflowRun(
        document_kind="workflow-run",
        schema_version="1.0.0",
        run_id=run_id,
        workflow_id=definition.workflow_id,
        workflow_revision=definition.revision,
        semantic_sha256=definition.semantic_sha256,
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


def _exercise_workspace(root: Path, run_id: str):
    primary = root / "wright.sqlite3"
    definition_promotion = promote_recovery_workflow_definition(
        (FIXTURES / "mounting-bracket.workflow.json").read_bytes()
    )
    definition = definition_promotion.definition
    layout_promotion = promote_recovery_workflow_layout(
        (FIXTURES / "mounting-bracket.layout.json").read_bytes(), definition
    )

    definitions = WorkflowDefinitionRepository(primary)
    layouts = WorkflowLayoutRepository(primary)
    runs = CanonicalWorkflowRunRepository(primary)
    definitions.create_from_recovery_promotion(definition_promotion)
    layouts.create_from_recovery_promotion(layout_promotion)
    current = _run(definition, run_id)
    runs.create(current, definition)
    runs.append_activity(
        WorkflowRunActivity(
            run_id=run_id,
            sequence=1,
            occurred_at=100,
            kind="registered",
            summary="Run registered",
            evidence_reference=f"trace://{run_id}/1",
        )
    )
    step = WorkflowRunStepRecord(
        run_id=run_id,
        step_id="step.export-001",
        block_id="block.export-step",
        attempt=1,
        state="succeeded",
        started_at=101,
        completed_at=102,
        input_artifact_ids=(),
        output_artifact_ids=("artifact.step-output-001",),
        diagnosis_codes=(),
        component_scope=None,
    )
    artifact = WorkflowArtifactRecord(
        artifact_id="artifact.step-output-001",
        run_id=run_id,
        step_id=step.step_id,
        contract_id="artifact.step",
        type_id="type.file.step",
        media_type="model/step",
        digest_sha256="a" * 64,
        size_bytes=1024,
        producer_block_id="block.export-step",
        upstream_artifact_ids=(),
        storage_reference=f"vault://runs/{run_id}/bracket.step",
        preview_state="ready",
        allowed_actions=("inspect", "preview", "open", "download"),
        lifetime="retained",
        expires_at=None,
        cleanup_state="retained",
    )
    runs.record_step(step, definition)
    runs.record_artifact(artifact, definition)
    runs.transition(run_id, "running", expected_state="queued", at=103)
    runs.transition(run_id, "succeeded", expected_state="running", at=104)
    return primary, definition, layout_promotion.layout, artifact


def test_canonical_definition_layout_and_run_reopen_offline_and_remain_isolated(
    tmp_path: Path, monkeypatch
) -> None:
    network_calls: list[object] = []

    def refuse_network(*args, **kwargs):
        network_calls.append((args, kwargs))
        raise AssertionError("canonical workflow path attempted network access")

    monkeypatch.setattr(socket, "create_connection", refuse_network)
    monkeypatch.setattr(socket, "getaddrinfo", refuse_network)

    primary_a, definition, layout, artifact = _exercise_workspace(
        tmp_path / "workspace-a", "run.offline-a"
    )
    primary_b, _, _, _ = _exercise_workspace(
        tmp_path / "workspace-b", "run.offline-b"
    )

    reopened_definitions = WorkflowDefinitionRepository(primary_a)
    reopened_layouts = WorkflowLayoutRepository(primary_a)
    reopened_runs = CanonicalWorkflowRunRepository(primary_a)
    snapshot = reopened_runs.reconnect("run.offline-a")

    assert network_calls == []
    assert reopened_definitions.read(definition.workflow_id) == definition
    assert reopened_layouts.read(definition.workflow_id) == layout
    assert snapshot.run.state == "succeeded"
    assert snapshot.artifacts == (artifact,)
    assert snapshot.cursor == 3
    assert not primary_a.exists()
    assert not primary_b.exists()
    assert reopened_runs.get("run.offline-b") is None
    assert CanonicalWorkflowRunRepository(primary_b).get("run.offline-a") is None
    filenames = {path.name for path in primary_a.parent.iterdir()}
    assert {
        "workflow-definitions.sqlite3",
        "workflow-layouts.sqlite3",
        "workflow-runs.sqlite3",
    }.issubset(filenames)
    assert all(
        name.removesuffix("-wal").removesuffix("-shm")
        in {
            "workflow-definitions.sqlite3",
            "workflow-layouts.sqlite3",
            "workflow-runs.sqlite3",
        }
        for name in filenames
    )
