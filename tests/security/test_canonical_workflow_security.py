from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from core.canonical_workflow_runs import WorkflowArtifactRecord, WorkflowRunActivity
from core.canonical_workflow_runs import capture_recovery_workflow_run
from core.workflow_definitions import (
    WorkflowCommandBatch,
    WorkflowDefinition,
    canonical_definition_sha256,
    promote_recovery_workflow_definition,
)
from core.workflow_runs import WorkflowRun, WorkflowRunState
from data_vault import upgrade_database
from data_vault.workflow_definition_repository import WorkflowDefinitionRepository
from workspace_service.workflow_operations import (
    WorkspaceWorkflowOperations,
    WorkflowOperationsError,
    WorkflowOperationsSettings,
)
from workspace_service.surfaces.grants import (
    CapabilityGrantError,
    CapabilityGrantService,
    CapabilityRequest,
)
from workspace_service.surfaces.service import ActorRole, SurfaceActor


ROOT = Path(__file__).parents[2]
DEFINITION_FIXTURE = (
    ROOT
    / "specs"
    / "080-canonical-workflow-recovery"
    / "fixtures"
    / "mounting-bracket.workflow.json"
)
RAW_SECRET = "wright-workflow-secret-sentinel-7419"
NOW = datetime(2026, 9, 1, 5, 0, tzinfo=UTC)


def _actor(
    *,
    workspace_id: str = "workspace-a",
    user_id: str = "engineer-a",
    role: ActorRole = ActorRole.ENGINEER,
) -> SurfaceActor:
    return SurfaceActor(
        user_id=user_id,
        workspace_id=workspace_id,
        session_id="session-a",
        role=role,
    )


def _grant_service(tmp_path: Path) -> CapabilityGrantService:
    database = tmp_path / "state.db"
    upgrade_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace-a', 'session-a', '/workspace/a', 1, 1)"""
        )
        connection.commit()
    return CapabilityGrantService(
        database,
        clock=lambda: NOW,
        id_factory=lambda: "grant-canonical-workflow-1",
    )


def _mutating_request(**overrides) -> CapabilityRequest:
    values = {
        "source_id": "canonical-workflow-composer",
        "source_version": "2.0.0",
        "instance_id": "workflow.mounting-bracket",
        "capability": "workflow.definition.mutate",
        "operation": "apply-command-batch",
        "constraints": {
            "workflow_id": "workflow.mounting-bracket",
            "base_revision": 1,
        },
        "risk_tier": "mutating",
        "persistence": "operation",
        "duration_seconds": 300,
        "declared": True,
        "decision": "allow",
        "reason": "Apply the reviewed atomic command batch",
    }
    values.update(overrides)
    return CapabilityRequest(**values)


def test_mutating_authority_is_exact_workspace_user_revision_and_single_use(
    tmp_path: Path,
) -> None:
    service = _grant_service(tmp_path)
    request = _mutating_request()
    service.decide(actor=_actor(), request=request)

    with pytest.raises(CapabilityGrantError, match="grant scope"):
        service.authorize(actor=_actor(workspace_id="workspace-b"), request=request)
    with pytest.raises(CapabilityGrantError, match="grant scope"):
        service.authorize(actor=_actor(user_id="engineer-b"), request=request)
    with pytest.raises(CapabilityGrantError, match="grant scope"):
        service.authorize(
            actor=_actor(),
            request=_mutating_request(
                constraints={
                    "workflow_id": "workflow.mounting-bracket",
                    "base_revision": 2,
                }
            ),
        )

    assert service.authorize(actor=_actor(), request=request).used_at == NOW
    with pytest.raises(CapabilityGrantError, match="consumed"):
        service.authorize(actor=_actor(), request=request)


def test_administrator_only_authority_cannot_be_self_granted_by_engineer(
    tmp_path: Path,
) -> None:
    service = _grant_service(tmp_path)
    request = _mutating_request(
        capability="target.attach",
        operation="attach-external-runtime",
    )

    with pytest.raises(CapabilityGrantError, match="administrator"):
        service.decide(actor=_actor(), request=request)
    assert service.decide(
        actor=_actor(role=ActorRole.ADMIN), request=request
    ).decision == "allow"


def test_runtime_history_is_hidden_outside_exact_workspace_and_session() -> None:
    run = WorkflowRun(
        run_id="run.scope-001",
        workspace_id="workspace-a",
        session_id="session-a",
        workflow_id="workflow.mounting-bracket",
        revision=1,
        generation=1,
        state=WorkflowRunState.SUCCEEDED,
    )

    class Runner:
        @staticmethod
        def get(run_id: str) -> WorkflowRun:
            assert run_id == run.run_id
            return run

    operations = WorkspaceWorkflowOperations(
        None,  # type: ignore[arg-type]
        Runner(),  # type: ignore[arg-type]
        settings=WorkflowOperationsSettings(enabled=True),
    )

    assert operations.run(
        workspace_id="workspace-a", session_id="session-a", run_id=run.run_id
    ) == run
    for workspace_id, session_id in (
        ("workspace-b", "session-a"),
        ("workspace-a", "session-b"),
    ):
        with pytest.raises(WorkflowOperationsError, match="not found"):
            operations.run(
                workspace_id=workspace_id,
                session_id=session_id,
                run_id=run.run_id,
            )


def test_definition_rejects_secret_shaped_configuration_before_digest_or_storage() -> None:
    payload = json.loads(DEFINITION_FIXTURE.read_text(encoding="utf-8"))
    payload["schema_version"] = "2.0.0"
    payload["blocks"][0]["configuration"]["api_token"] = RAW_SECRET
    payload["semantic_sha256"] = None
    payload["semantic_sha256"] = canonical_definition_sha256(payload)

    with pytest.raises(ValidationError, match="secret-like field"):
        WorkflowDefinition.model_validate(payload)


def test_recovery_promotion_rejects_secret_material_in_exact_source() -> None:
    payload = json.loads(DEFINITION_FIXTURE.read_text(encoding="utf-8"))
    payload["blocks"][0]["configuration"]["authorization"] = RAW_SECRET
    payload["semantic_sha256"] = canonical_definition_sha256(payload)
    original = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    with pytest.raises(ValueError, match="secret-like field"):
        promote_recovery_workflow_definition(original)


def test_recovery_run_archive_rejects_secret_material_in_opaque_fields() -> None:
    original = json.dumps(
        {
            "document_kind": "workflow-run",
            "schema_version": "1.0.0-recovery.1",
            "run_id": "run.recovery-security-001",
            "workflow_id": "workflow.mounting-bracket",
            "workflow_revision": 1,
            "semantic_sha256": "a" * 64,
            "diagnostic": {"api_token": RAW_SECRET},
        },
        separators=(",", ":"),
    ).encode("utf-8")

    with pytest.raises(ValueError, match="unsupported or invalid") as rejected:
        capture_recovery_workflow_run(original)
    assert "secret-like field" in str(rejected.value.__cause__)


def test_immutable_activity_and_artifact_records_reject_secret_bearing_text() -> None:
    with pytest.raises(ValidationError, match="secret material"):
        WorkflowRunActivity(
            run_id="run.security-001",
            sequence=1,
            occurred_at=1,
            kind="progress",
            summary=f"authorization={RAW_SECRET}",
            evidence_reference=None,
        )

    with pytest.raises(ValidationError, match="secret"):
        WorkflowArtifactRecord(
            artifact_id="artifact.security-001",
            run_id="run.security-001",
            step_id="step.security-001",
            contract_id="artifact.step",
            type_id="type.file.step",
            media_type="model/step",
            digest_sha256="a" * 64,
            size_bytes=1,
            producer_block_id="block.export-step",
            upstream_artifact_ids=(),
            storage_reference="https://engineer:password@example.invalid/artifact.step",
            preview_state="unavailable",
            allowed_actions=("inspect",),
            lifetime="retained",
            expires_at=None,
            cleanup_state="retained",
        )


def test_atomic_command_batch_resource_limit_fails_closed() -> None:
    command = {
        "kind": "set_block_title",
        "block_id": "block.design-intent",
        "title": "Bounded title",
    }
    with pytest.raises(ValidationError, match="at most 1000 items"):
        WorkflowCommandBatch.model_validate(
            {
                "document_kind": "workflow-command-batch",
                "schema_version": "1.0.0",
                "base_revision": 2,
                "origin": "text",
                "commands": [command] * 1001,
            }
        )


def test_definition_repository_rejects_oversized_envelope_before_sidecar_write(
    tmp_path: Path,
) -> None:
    definition = promote_recovery_workflow_definition(
        DEFINITION_FIXTURE.read_bytes()
    ).definition
    blocks = list(definition.blocks)
    blocks[0] = blocks[0].model_copy(update={"instructions": "x" * (4 * 1024 * 1024)})
    oversized = definition.model_copy(
        update={
            "revision": 1,
            "parent_revision": None,
            "blocks": tuple(blocks),
            "semantic_sha256": None,
        }
    )
    oversized = oversized.model_copy(
        update={"semantic_sha256": canonical_definition_sha256(oversized)}
    )
    repository = WorkflowDefinitionRepository(tmp_path / "wright.sqlite3")

    with pytest.raises(ValueError, match="4 MiB limit"):
        repository.create(oversized)

    assert not repository.db_path.exists()
