from __future__ import annotations

from pathlib import Path

import pytest

from core.canonical_workflow_runs import (
    CanonicalWorkflowRun,
    WorkflowArtifactRecord,
    WorkflowComponentScope,
    WorkflowRunActivity,
    WorkflowRunStepRecord,
    capture_recovery_workflow_run,
    validate_artifact_subject,
    validate_run_subject,
    validate_step_subject,
)
from core.workflow_definitions import (
    canonical_definition_bytes,
    promote_recovery_workflow_definition,
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


def test_run_subject_is_exact_and_state_does_not_change_definition() -> None:
    subject = definition()
    before = canonical_definition_bytes(subject)
    current = run()

    validate_run_subject(subject, current)
    running = current.model_copy(
        update={"state": "running", "active_block_id": "block.design-intent"}
    )
    validate_run_subject(subject, running)

    assert canonical_definition_bytes(subject) == before
    assert running.semantic_sha256 == subject.semantic_sha256


def test_run_subject_mismatch_fails_closed() -> None:
    current = run().model_copy(update={"semantic_sha256": "f" * 64})

    with pytest.raises(ValueError, match="WFR-RUN-SUBJECT-MISMATCH"):
        validate_run_subject(definition(), current)


def test_step_component_scope_resolves_to_definition_addresses() -> None:
    step = WorkflowRunStepRecord(
        run_id=run().run_id,
        step_id="step.review-001",
        block_id="block.review-design",
        attempt=1,
        state="succeeded",
        started_at=110,
        completed_at=120,
        input_artifact_ids=("artifact.geometry",),
        output_artifact_ids=("artifact.approved",),
        diagnosis_codes=(),
        component_scope=WorkflowComponentScope(
            component_instance_id="block.review-design",
            component_id="component.review-cell",
            component_version="1.0.0",
            internal_semantic_id="component.review-cell.relationship.accept",
        ),
    )

    validate_step_subject(definition(), step)

    invalid = step.model_copy(
        update={
            "component_scope": step.component_scope.model_copy(
                update={"internal_semantic_id": "component.review-cell.missing"}
            )
        }
    )
    with pytest.raises(ValueError, match="WFR-RUN-COMPONENT-ADDRESS"):
        validate_step_subject(definition(), invalid)


def test_artifact_contract_lineage_is_definition_bound() -> None:
    artifact = WorkflowArtifactRecord(
        artifact_id="artifact.step-output-001",
        run_id=run().run_id,
        step_id="step.export-001",
        contract_id="artifact.step",
        type_id="type.file.step",
        media_type="model/step",
        digest_sha256="a" * 64,
        size_bytes=1024,
        producer_block_id="block.export-step",
        upstream_artifact_ids=("artifact.approved-geometry-001",),
        storage_reference="vault://runs/run.production-001/bracket.step",
        preview_state="ready",
        allowed_actions=("inspect", "preview", "open", "download"),
        lifetime="retained",
        expires_at=None,
        cleanup_state="retained",
    )

    validate_artifact_subject(definition(), artifact)

    invalid = artifact.model_copy(update={"producer_block_id": "block.design-intent"})
    with pytest.raises(ValueError, match="WFR-RUN-ARTIFACT-PRODUCER"):
        validate_artifact_subject(definition(), invalid)


def test_activity_is_closed_and_bounded() -> None:
    activity = WorkflowRunActivity(
        run_id=run().run_id,
        sequence=1,
        occurred_at=100,
        kind="registered",
        summary="Run registered",
        evidence_reference="trace://run.production-001/1",
    )

    assert activity.sequence == 1
    with pytest.raises(ValueError):
        WorkflowRunActivity(
            run_id=run().run_id,
            sequence=0,
            occurred_at=100,
            kind="registered",
            summary="Run registered",
            evidence_reference=None,
        )


def test_recovery_run_capture_preserves_original_historical_subject() -> None:
    original = (
        b'{"document_kind":"workflow-run","schema_version":"1.0.0-recovery.1",'
        b'"run_id":"run.recovery-001","workflow_id":"workflow.mounting-bracket",'
        b'"workflow_revision":1,"semantic_sha256":"'
        + b"57ed2b7caacc9b3a779d9e960a681a9b8fe6dc1cfc9c3d48fa6ddd5e184be889"
        + b'","state":"succeeded"}'
    )

    captured = capture_recovery_workflow_run(original)

    assert captured.original == original
    assert captured.semantic_sha256 != definition().semantic_sha256
    assert captured.workflow_revision == 1
