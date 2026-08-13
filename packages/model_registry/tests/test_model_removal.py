from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

import pytest
from data_vault import ModelArtifactStore, ModelRepository, upgrade_database
from model_registry.lifecycle import (
    CancellationSignal,
    LifecycleFailure,
    ModelMaintenanceLifecycle,
)


NOW = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)


def _maintenance(tmp_path):
    database = tmp_path / "state.db"
    upgrade_database(database)
    repository = ModelRepository(str(database))
    store = ModelArtifactStore(tmp_path / "data")
    content = b"reviewed deterministic model bytes"
    digest = hashlib.sha256(content).hexdigest()
    staged = store.stage_bytes(
        operation_id="operation-seed",
        expected_digest=digest,
        content=content,
        maximum_bytes=len(content),
    )
    store.promote(staged)
    repository.record_content_object(
        content_digest=digest,
        size=len(content),
        state="verified",
        storage_key=f"sha256/{digest[:2]}/{digest}",
        verification={"algorithm": "sha256", "size": len(content)},
        observed_at=NOW,
    )
    repository.save_installation(
        installation_id="installation-one",
        model_id="wright-affine-test",
        package_revision=1,
        variant_id="json-cpu-f64",
        manifest_digest="a" * 64,
        installation_digest="b" * 64,
        runtime_adapter_id="wright-deterministic",
        runtime_adapter_version="1.0.0",
        state="ready",
        active=True,
        installed_at=NOW,
    )
    repository.record_installation_artifacts(
        "installation-one", {"model/data.json": digest}, created_at=NOW
    )
    return (
        repository,
        store,
        digest,
        ModelMaintenanceLifecycle(
            repository=repository, store=store, clock=lambda: NOW
        ),
    )


def test_reference_and_lease_block_purge_until_detached_or_released(tmp_path) -> None:
    repository, store, digest, lifecycle = _maintenance(tmp_path)
    repository.add_reference(
        reference_id="reference-workflow",
        content_digest=digest,
        installation_id="installation-one",
        kind="workflow",
        owner_id="workflow-one",
        created_at=NOW,
    )
    repository.acquire_lease(
        lease_id="lease-run",
        content_digest=digest,
        owner_id="run-one",
        expires_at=NOW + timedelta(minutes=5),
        observed_at=NOW,
    )

    lifecycle.disable("installation-one")
    lifecycle.uninstall("installation-one")
    preview = lifecycle.preview_purge("installation-one")
    assert preview["reclaimable_bytes"] == 0
    assert {item["kind"] for item in preview["blockers"]} == {
        "workflow",
        "lease",
    }
    with pytest.raises(LifecycleFailure, match="referenced"):
        lifecycle.purge("installation-one")

    assert (
        lifecycle.set_reference_state("reference-workflow", "archived")["state"]
        == "archived"
    )
    repository.release_lease("lease-run")
    preview = lifecycle.preview_purge("installation-one")
    assert preview["reclaimable_bytes"] == len(b"reviewed deterministic model bytes")
    result = lifecycle.purge("installation-one")
    assert result["state"] == "succeeded"
    assert result["reclaimed_bytes"] == preview["reclaimable_bytes"]
    assert not store.has_verified(digest)


def test_cancellable_cleanup_and_restart_recovery_leave_no_partial_residue(
    tmp_path,
) -> None:
    _, store, digest, lifecycle = _maintenance(tmp_path)
    lifecycle.disable("installation-one")
    lifecycle.uninstall("installation-one")
    signal = CancellationSignal()
    signal.request()
    with pytest.raises(LifecycleFailure) as cancelled:
        lifecycle.purge("installation-one", cancellation=signal)
    assert cancelled.value.code == "cancelled"
    assert store.has_verified(digest)

    content = b"partial"
    partial_digest = hashlib.sha256(content).hexdigest()
    store.stage_bytes(
        operation_id="operation-interrupted",
        expected_digest=partial_digest,
        content=content,
        maximum_bytes=len(content),
    )
    recovered = lifecycle.recover_cleanup("operation-interrupted")
    assert recovered["cleanup_state"] == "clean"
    assert not (store.staging_root / "operation-interrupted").exists()
