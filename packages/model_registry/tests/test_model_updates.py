from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from data_vault import ModelArtifactStore, ModelRepository, upgrade_database
from fixture_factory import generate_affine_fixture
from model_registry.generated import affine_artifacts
from model_registry.lifecycle import (
    ModelMaintenanceLifecycle,
    compare_model_revisions,
)


NOW = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)


def _changed_package(tmp_path):
    current = generate_affine_fixture(tmp_path / "current").package
    candidate = generate_affine_fixture(
        tmp_path / "candidate", revision=2, scale=3.0
    ).package
    document = candidate.model_dump(mode="json")
    document["license"]["attribution"] = "Updated Wright attribution."
    document["license"]["redistribution"] = "review_required"
    document["tasks"][0]["input_schema"]["properties"]["x"]["minimum"] = 0
    document["tasks"][0]["units"] = {"x": "mm", "y": "mm"}
    document["tasks"][0]["coordinate_convention"] = "right-handed XYZ"
    document["variants"][0]["runtime"]["version_specifier"] = "==1.1.0"
    document["variants"][0]["resources"]["ram_bytes"] = 2_097_152
    document["limitations"][0]["description"] = "Updated test-only limitation."
    from model_registry import ModelPackage

    return current, ModelPackage.model_validate(document)


def _save_installation(repository, package, *, state: str, active: bool) -> str:
    installation_id = f"installation-{package.package_revision}"
    repository.save_installation(
        installation_id=installation_id,
        model_id=package.model_id,
        package_revision=package.package_revision,
        variant_id=package.variants[0].variant_id,
        manifest_digest=package.digest,
        installation_digest=("a" if package.package_revision == 1 else "b") * 64,
        runtime_adapter_id="wright-deterministic",
        runtime_adapter_version="1.0.0",
        state=state,
        active=active,
        installed_at=NOW,
    )
    return installation_id


def test_semantic_revision_diff_covers_every_engineering_review_facet(tmp_path) -> None:
    current, candidate = _changed_package(tmp_path)
    difference = compare_model_revisions(current, candidate)

    assert set(difference.changed_facets) == {
        "license",
        "redistribution",
        "artifacts",
        "adapter",
        "schemas",
        "units",
        "coordinates",
        "resources",
        "vectors",
        "limitations",
    }
    assert difference.requires_retest is True
    assert difference.requires_license_review is True
    assert len(difference.diff_digest) == 64


def test_failed_update_preserves_current_and_successor_activation_is_atomic(
    tmp_path,
) -> None:
    current, candidate = _changed_package(tmp_path)
    database = tmp_path / "state.db"
    upgrade_database(database)
    repository = ModelRepository(str(database))
    lifecycle = ModelMaintenanceLifecycle(
        repository=repository,
        store=ModelArtifactStore(tmp_path / "data"),
        clock=lambda: NOW,
    )
    current_id = _save_installation(repository, current, state="ready", active=True)
    successor_id = _save_installation(
        repository, candidate, state="installed", active=False
    )

    failed = lifecycle.activate_successor(current_id, successor_id)
    assert failed["state"] == "blocked"
    assert repository.get_installation(current_id)["active_revision"] == 1

    repository.mark_installation_tested(
        successor_id,
        expected_state="installed",
        state="ready",
        adapter_version="1.0.0",
        evidence_id="evidence-successor",
        observed_at=NOW,
    )
    activated = lifecycle.activate_successor(current_id, successor_id)
    assert activated["state"] == "succeeded"
    assert repository.get_installation(current_id)["active_revision"] == 0
    assert repository.get_installation(successor_id)["active_revision"] == 1
    assert repository.get_installation(successor_id)["predecessor_id"] == current_id


def test_rollback_requires_retest_and_reuses_cached_predecessor(tmp_path) -> None:
    current, candidate = _changed_package(tmp_path)
    database = tmp_path / "state.db"
    upgrade_database(database)
    repository = ModelRepository(str(database))
    store = ModelArtifactStore(tmp_path / "data")
    lifecycle = ModelMaintenanceLifecycle(
        repository=repository, store=store, clock=lambda: NOW
    )
    predecessor_id = _save_installation(
        repository, current, state="ready", active=False
    )
    current_id = _save_installation(repository, candidate, state="ready", active=True)
    cached_artifacts = affine_artifacts(current)
    artifact_digests = {}
    for index, (path, value) in enumerate(sorted(cached_artifacts.items())):
        digest = hashlib.sha256(value).hexdigest()
        staged = store.stage_bytes(
            operation_id=f"operation-cache-{index}",
            expected_digest=digest,
            content=value,
            maximum_bytes=len(value),
        )
        store.promote(staged)
        repository.record_content_object(
            content_digest=digest,
            size=len(value),
            state="verified",
            storage_key=f"sha256/{digest[:2]}/{digest}",
            verification={"algorithm": "sha256", "size": len(value)},
            observed_at=NOW,
        )
        artifact_digests[path] = digest
    repository.record_installation_artifacts(
        predecessor_id, artifact_digests, created_at=NOW
    )

    prepared = lifecycle.prepare_rollback(current_id, predecessor_id)
    assert prepared["state"] == "testing_required"
    assert prepared["cached_content_reused"] is True
    assert repository.get_installation(current_id)["active_revision"] == 1
    repository.mark_installation_tested(
        predecessor_id,
        expected_state="installed",
        state="ready",
        adapter_version="1.0.0",
        evidence_id="evidence-rollback",
        observed_at=NOW,
    )
    rolled_back = lifecycle.activate_successor(current_id, predecessor_id)
    assert rolled_back["state"] == "succeeded"
    assert repository.get_installation(predecessor_id)["active_revision"] == 1
