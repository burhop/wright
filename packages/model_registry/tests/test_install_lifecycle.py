from __future__ import annotations

from datetime import UTC, datetime
from concurrent.futures import ThreadPoolExecutor

from data_vault import ModelArtifactStore, ModelRepository, upgrade_database
from fixture_factory import generate_affine_fixture
from fakes import FakeDiskReservation
from model_registry.lifecycle import (
    CancellationSignal,
    MappingArtifactSource,
    ModelInstallLifecycle,
)
from model_registry.planning import confirm_effect_plan, create_effect_plan
from model_registry.policy import HostObservation


NOW = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)


def lifecycle(tmp_path):
    db = tmp_path / "state.db"
    upgrade_database(db)
    repository = ModelRepository(str(db))
    store = ModelArtifactStore(tmp_path / "data")
    return (
        repository,
        store,
        ModelInstallLifecycle(
            repository=repository,
            store=store,
            disk=FakeDiskReservation(10_000_000),
            clock=lambda: NOW,
        ),
    )


def confirmed_plan(fixture):
    plan = create_effect_plan(
        fixture.package,
        variant_id="json-cpu-f64",
        snapshot_id="snapshot-1",
        principal_id="engineer-1",
        host=HostObservation.reference(),
        now=NOW,
    )
    return confirm_effect_plan(
        plan,
        principal_id="engineer-1",
        plan_digest=plan.plan_digest,
        now=NOW,
        current_plan=plan,
    )


def test_confirmed_install_verifies_promotes_and_activates_atomically(tmp_path) -> None:
    fixture = generate_affine_fixture(tmp_path / "fixture")
    repository, store, service = lifecycle(tmp_path)
    operation = service.install(
        confirmed_plan(fixture),
        fixture.package,
        MappingArtifactSource(fixture.artifacts),
        trace_id="trace-install-1",
    )

    assert operation["state"] == "succeeded"
    assert operation["cleanup_state"] == "clean"
    installation_id = operation["result"]["installation_id"]
    activation = store.read_activation(installation_id)
    assert activation is not None
    assert activation["manifest_digest"] == fixture.manifest_digest
    assert all(store.has_verified(value) for value in activation["artifacts"].values())
    assert repository.get_operation(operation["operation_id"])["state"] == "succeeded"


def test_install_is_idempotent_and_reuses_verified_content(tmp_path) -> None:
    fixture = generate_affine_fixture(tmp_path / "fixture")
    _, _, service = lifecycle(tmp_path)
    source = MappingArtifactSource(fixture.artifacts)
    plan = confirmed_plan(fixture)
    first = service.install(plan, fixture.package, source)
    calls = source.calls
    second = service.install(plan, fixture.package, source)
    assert second == first
    assert source.calls == calls


def test_successor_install_stays_inactive_until_separate_activation(tmp_path) -> None:
    current = generate_affine_fixture(tmp_path / "current")
    successor = generate_affine_fixture(tmp_path / "successor", revision=2, scale=3.0)
    repository, _, service = lifecycle(tmp_path)

    first = service.install(
        confirmed_plan(current),
        current.package,
        MappingArtifactSource(current.artifacts),
    )
    second = service.install(
        confirmed_plan(successor),
        successor.package,
        MappingArtifactSource(successor.artifacts),
    )

    assert first["state"] == "succeeded"
    assert second["state"] == "succeeded"
    assert (
        repository.get_installation(first["result"]["installation_id"])[
            "active_revision"
        ]
        == 1
    )
    assert (
        repository.get_installation(second["result"]["installation_id"])[
            "active_revision"
        ]
        == 0
    )


def test_concurrent_installers_converge_on_one_operation_and_activation(
    tmp_path,
) -> None:
    fixture = generate_affine_fixture(tmp_path / "fixture")
    _, store, service = lifecycle(tmp_path)
    source = MappingArtifactSource(fixture.artifacts)
    plan = confirmed_plan(fixture)
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(
            executor.map(
                lambda _index: service.install(plan, fixture.package, source),
                range(2),
            )
        )
    assert results[0] == results[1]
    assert results[0]["state"] == "succeeded"
    assert source.calls == len(fixture.artifacts)
    assert len(list(store.installations_root.glob("*.json"))) == 1


def test_cancel_and_failure_cleanup_never_appear_active(tmp_path) -> None:
    fixture = generate_affine_fixture(tmp_path / "fixture")
    _, store, service = lifecycle(tmp_path)
    cancellation = CancellationSignal()
    cancellation.request()
    cancelled = service.install(
        confirmed_plan(fixture),
        fixture.package,
        MappingArtifactSource(fixture.artifacts),
        cancellation=cancellation,
    )
    assert cancelled["state"] == "cancelled"
    assert cancelled["cleanup_state"] == "clean"
    assert list(store.installations_root.glob("*.json")) == []

    broken = dict(fixture.artifacts)
    broken["model/coefficients.json"] = b"wrong"
    failed = service.install(
        confirmed_plan(fixture).model_copy(
            update={"plan_id": "plan-broken", "plan_digest": "f" * 64}
        ),
        fixture.package,
        MappingArtifactSource(broken),
    )
    assert failed["state"] == "failed"
    assert failed["failure"]["category"] == "digest_mismatch"


def test_disk_exhaustion_and_concurrent_identity_fail_closed(tmp_path) -> None:
    fixture = generate_affine_fixture(tmp_path / "fixture")
    db = tmp_path / "state.db"
    upgrade_database(db)
    service = ModelInstallLifecycle(
        repository=ModelRepository(str(db)),
        store=ModelArtifactStore(tmp_path / "data"),
        disk=FakeDiskReservation(1),
        clock=lambda: NOW,
    )
    failed = service.install(
        confirmed_plan(fixture),
        fixture.package,
        MappingArtifactSource(fixture.artifacts),
    )
    assert failed["state"] == "failed"
    assert failed["failure"]["category"] == "insufficient_disk"


def test_offline_import_uses_the_same_policy_and_activation_path(tmp_path) -> None:
    fixture = generate_affine_fixture(tmp_path / "fixture")
    _, store, service = lifecycle(tmp_path)
    operation = service.import_archive(
        confirmed_plan(fixture), fixture.archive_path, trace_id="trace-import-1"
    )
    assert operation["state"] == "succeeded"
    assert store.read_activation(operation["result"]["installation_id"]) is not None
