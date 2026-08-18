from __future__ import annotations

from pathlib import Path

from wright_engineering.runtime.models import LifecycleState, RuntimeStatus

from .support import artifact, lifecycle, seed_runtime


class FakeMigrations:
    def __init__(self) -> None:
        self.calls = 0

    def prepare_activation(self, **kwargs):
        self.calls += 1
        return str(Path(kwargs["data_root"]) / "backups" / "backup.manifest.json")

    def current_schema(self, data_root: Path) -> int:
        return 5


def test_update_stages_backs_up_activates_and_retains_predecessor(
    tmp_path: Path,
) -> None:
    layout_runtime = lifecycle(tmp_path, migration_manager=FakeMigrations())
    seed_runtime(layout_runtime, version="0.1.4", runtime_id="old", running=True)
    result = layout_runtime.update(artifact=artifact(tmp_path, "0.1.5"))
    manifest = layout_runtime.store.load()

    assert result.ok and result.state is LifecycleState.HEALTHY
    assert manifest.active_runtime_id != "old"
    assert manifest.predecessor_runtime_id == "old"
    assert manifest.runtimes["old"].status is RuntimeStatus.PREDECESSOR
    assert manifest.runtimes[manifest.active_runtime_id].status is RuntimeStatus.ACTIVE
    assert (layout_runtime.layout.workspaces).is_relative_to(layout_runtime.layout.data)


def test_update_to_current_version_is_idempotent(tmp_path: Path) -> None:
    runtime = lifecycle(tmp_path, migration_manager=FakeMigrations())
    candidate = artifact(tmp_path, "0.1.5")
    seed_runtime(
        runtime,
        version="0.1.5",
        runtime_id="current",
        artifact_sha256=candidate.sha256,
    )
    result = runtime.update(artifact=candidate)
    assert result.ok
    assert result.code == "already_current"


def test_update_activates_repaired_candidate_with_same_version_new_hash(
    tmp_path: Path,
) -> None:
    runtime = lifecycle(tmp_path, migration_manager=FakeMigrations())
    seed_runtime(runtime, version="0.1.5", runtime_id="current", running=True)
    candidate = artifact(tmp_path, "0.1.5")

    result = runtime.update(artifact=candidate)
    manifest = runtime.store.load()

    assert result.ok and result.code == "ok"
    assert manifest.active_runtime_id != "current"
    assert manifest.predecessor_runtime_id == "current"
    assert manifest.runtimes[manifest.active_runtime_id].artifact_sha256 == (
        candidate.sha256
    )


def test_second_update_replaces_predecessor_without_losing_retained_runtime(
    tmp_path: Path,
) -> None:
    runtime = lifecycle(tmp_path, migration_manager=FakeMigrations())
    seed_runtime(runtime, version="0.1.4", runtime_id="oldest", active=False)
    seed_runtime(runtime, version="0.1.5", runtime_id="current", running=True)

    result = runtime.update(artifact=artifact(tmp_path, "0.1.5"))
    manifest = runtime.store.load()

    assert result.ok and result.state is LifecycleState.HEALTHY
    assert manifest.predecessor_runtime_id == "current"
    assert manifest.runtimes["current"].status is RuntimeStatus.PREDECESSOR
    assert manifest.runtimes["oldest"].status is RuntimeStatus.VERIFIED
