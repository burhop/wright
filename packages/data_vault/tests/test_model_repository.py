from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from data_vault import MIGRATIONS, ModelRepository, upgrade_database


DIGEST = "a" * 64
OTHER_DIGEST = "b" * 64


def repository(tmp_path) -> ModelRepository:
    path = tmp_path / "state.db"
    upgrade_database(path)
    return ModelRepository(str(path))


def test_plan_identity_is_idempotent_immutable_and_optimistic(tmp_path) -> None:
    repo = repository(tmp_path)
    now = datetime.now(UTC)
    plan = {"model_id": "wright-affine-test", "effects": []}
    repo.save_plan(
        plan_id="plan-1",
        principal_id="engineer-1",
        plan_digest=DIGEST,
        state="confirmable",
        plan=plan,
        created_at=now,
        expires_at=now + timedelta(minutes=10),
    )
    repo.save_plan(
        plan_id="plan-1",
        principal_id="engineer-1",
        plan_digest=DIGEST,
        state="confirmable",
        plan=plan,
        created_at=now,
        expires_at=now + timedelta(minutes=10),
    )
    with pytest.raises(ValueError, match="immutable"):
        repo.save_plan(
            plan_id="plan-1",
            principal_id="engineer-1",
            plan_digest=OTHER_DIGEST,
            state="confirmable",
            plan=plan,
            created_at=now,
            expires_at=now + timedelta(minutes=10),
        )
    assert repo.transition_plan(
        "plan-1", expected_state="confirmable", state="confirmed"
    )
    assert not repo.transition_plan(
        "plan-1", expected_state="confirmable", state="expired"
    )
    assert repo.get_plan("plan-1")["state"] == "confirmed"


def test_operation_terminal_state_is_immutable_and_retry_is_idempotent(
    tmp_path,
) -> None:
    repo = repository(tmp_path)
    now = datetime.now(UTC)
    repo.save_plan(
        plan_id="plan-1",
        principal_id="engineer-1",
        plan_digest=DIGEST,
        state="confirmed",
        plan={"model_id": "wright-affine-test", "effects": []},
        created_at=now,
        expires_at=now + timedelta(minutes=10),
    )
    repo.create_operation(
        operation_id="operation-1",
        plan_id="plan-1",
        plan_digest=DIGEST,
        kind="install",
        trace_id="trace-1",
        created_at=now,
    )
    assert repo.transition_operation(
        "operation-1",
        expected_state="prepared",
        state="running",
        phase="acquiring",
        progress={"completed_bytes": 0, "maximum_bytes": 24},
        updated_at=now,
    )
    assert repo.transition_operation(
        "operation-1",
        expected_state="running",
        state="succeeded",
        phase="complete",
        progress={"completed_bytes": 24, "maximum_bytes": 24},
        result={"installation_id": "installation-1"},
        cleanup_state="clean",
        updated_at=now,
    )
    assert not repo.transition_operation(
        "operation-1",
        expected_state="running",
        state="failed",
        phase="failed",
        progress={},
        updated_at=now,
    )
    with pytest.raises(ValueError, match="immutable"):
        repo.create_operation(
            operation_id="operation-1",
            plan_id="different",
            plan_digest=DIGEST,
            kind="install",
            trace_id="trace-1",
            created_at=now,
        )
    assert repo.get_operation("operation-1")["result"] == {
        "installation_id": "installation-1"
    }


def test_installations_bindings_references_leases_and_evidence_are_scoped(
    tmp_path,
) -> None:
    repo = repository(tmp_path)
    now = datetime.now(UTC)
    with sqlite3.connect(repo.db_path) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)""",
            ("workspace-a", "session-a", "workspace-a", 1, 1),
        )
    repo.save_installation(
        installation_id="installation-1",
        model_id="wright-affine-test",
        package_revision=1,
        variant_id="json-cpu-f64",
        manifest_digest=DIGEST,
        installation_digest=OTHER_DIGEST,
        runtime_adapter_id="wright-deterministic",
        runtime_adapter_version="1.0.0",
        state="ready",
        active=True,
        installed_at=now,
    )
    repo.bind_workspace(
        binding_id="binding-1",
        workspace_id="workspace-a",
        installation_id="installation-1",
        task_id="predict",
        tool_name="wright_model__wright-affine-test__predict",
        binding_digest=DIGEST,
        policy_snapshot_digest=OTHER_DIGEST,
        state="enabled",
        created_at=now,
    )
    assert repo.list_bindings("workspace-a")[0]["installation_id"] == ("installation-1")
    assert repo.list_bindings("workspace-b") == ()

    repo.record_content_object(
        content_digest=DIGEST,
        size=7,
        state="verified",
        storage_key=f"sha256/{DIGEST[:2]}/{DIGEST}",
        verification={"algorithm": "sha256", "size": 7},
        observed_at=now,
    )
    repo.add_reference(
        reference_id="reference-1",
        content_digest=DIGEST,
        installation_id="installation-1",
        kind="workspace",
        owner_id="workspace-a",
        created_at=now,
    )
    repo.acquire_lease(
        lease_id="lease-1",
        content_digest=DIGEST,
        owner_id="operation-1",
        expires_at=now + timedelta(minutes=1),
        observed_at=now,
    )
    assert repo.content_hold_count(DIGEST, at=now) == 2
    repo.release_lease("lease-1")
    repo.detach_reference("reference-1", detached_at=now)
    assert repo.content_hold_count(DIGEST, at=now) == 0

    repo.record_test_evidence(
        evidence_id="evidence-1",
        installation_id="installation-1",
        vector_id="predict-two",
        material_digest=DIGEST,
        observation_digest=OTHER_DIGEST,
        state="passed",
        evidence={"outcome": "passed"},
        created_at=now,
    )
    assert repo.list_test_evidence("installation-1")[0]["material_digest"] == DIGEST


def test_repository_rejects_secret_and_oversized_json(tmp_path) -> None:
    repo = repository(tmp_path)
    now = datetime.now(UTC)
    with pytest.raises(ValueError):
        repo.save_plan(
            plan_id="plan-secret",
            principal_id="engineer",
            plan_digest=DIGEST,
            state="blocked",
            plan={"api_key": "synthetic-secret"},
            created_at=now,
            expires_at=now + timedelta(minutes=1),
        )
    with pytest.raises(ValueError, match="64 KiB"):
        repo.save_plan(
            plan_id="plan-large",
            principal_id="engineer",
            plan_digest=DIGEST,
            state="blocked",
            plan={"message": "x" * 70_000},
            created_at=now,
            expires_at=now + timedelta(minutes=1),
        )


def test_schema_version_matches_migration_count() -> None:
    assert len(MIGRATIONS) == 16
