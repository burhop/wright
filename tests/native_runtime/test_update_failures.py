from __future__ import annotations

from pathlib import Path

from wright_engineering.runtime.models import LifecycleState

from .support import (
    FakeInstaller,
    FakeProcessManager,
    artifact,
    lifecycle,
    seed_runtime,
)


class FailingMigrations:
    def prepare_activation(self, **kwargs):
        raise RuntimeError("migration failed")

    def current_schema(self, data_root: Path) -> int:
        return 5


def test_installer_failure_leaves_predecessor_active(tmp_path: Path) -> None:
    layout = lifecycle(tmp_path)
    failing = FakeInstaller(layout.layout, fail_versions={"0.1.5"})
    layout.installer = failing  # type: ignore[assignment]
    seed_runtime(layout, version="0.1.4", runtime_id="old", running=False)
    result = layout.update(artifact=artifact(tmp_path, "0.1.5"))
    manifest = layout.store.load()
    assert not result.ok
    assert manifest.active_runtime_id == "old"
    assert manifest.lifecycle_state is LifecycleState.STOPPED


def test_migration_failure_is_honest_and_keeps_old_runtime(tmp_path: Path) -> None:
    runtime = lifecycle(tmp_path, migration_manager=FailingMigrations())
    seed_runtime(runtime, version="0.1.4", runtime_id="old", running=False)
    result = runtime.update(artifact=artifact(tmp_path, "0.1.5"))
    assert not result.ok
    assert runtime.store.load().active_runtime_id == "old"
    assert result.state in {LifecycleState.STOPPED, LifecycleState.RECOVERY_REQUIRED}


def test_failed_candidate_health_restores_running_predecessor(tmp_path: Path) -> None:
    probes = iter([False, True])
    processes = FakeProcessManager()
    runtime = lifecycle(
        tmp_path,
        process_manager=processes,
        health_probe=lambda _: next(probes),
    )
    seed_runtime(runtime, version="0.1.4", runtime_id="old", running=True)
    result = runtime.update(artifact=artifact(tmp_path, "0.1.5"))
    manifest = runtime.store.load()
    assert not result.ok
    assert result.code == "update_recovered"
    assert manifest.active_runtime_id == "old"
    assert manifest.lifecycle_state is LifecycleState.HEALTHY
