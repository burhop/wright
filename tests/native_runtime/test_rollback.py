from __future__ import annotations

from pathlib import Path

from wright_engineering.runtime.models import LifecycleState

from .support import FakeProcessManager, lifecycle, seed_runtime


class SchemaFive:
    def current_schema(self, data_root: Path) -> int:
        return 5

    def prepare_activation(self, **kwargs):
        raise AssertionError("rollback must not migrate or restore a backup")


def test_compatible_rollback_activates_retained_predecessor(tmp_path: Path) -> None:
    runtime = lifecycle(tmp_path, migration_manager=SchemaFive())
    seed_runtime(runtime, version="0.1.5", runtime_id="current", running=True)
    seed_runtime(runtime, version="0.1.4", runtime_id="previous", active=False)
    result = runtime.rollback()
    manifest = runtime.store.load()
    assert result.ok and result.state is LifecycleState.HEALTHY
    assert manifest.active_runtime_id == "previous"
    assert manifest.predecessor_runtime_id == "current"


def test_rollback_refuses_runtime_that_cannot_open_current_schema(
    tmp_path: Path,
) -> None:
    processes = FakeProcessManager()
    runtime = lifecycle(
        tmp_path, migration_manager=SchemaFive(), process_manager=processes
    )
    seed_runtime(runtime, version="0.1.5", runtime_id="current", running=True)
    seed_runtime(
        runtime,
        version="0.1.4",
        runtime_id="previous",
        active=False,
        data_schema_max=4,
    )
    result = runtime.rollback()
    assert not result.ok
    assert result.code == "rollback_schema_incompatible"
    assert processes.stops == []
    assert runtime.store.load().active_runtime_id == "current"
    assert result.details["newer_state"] == {
        "schema_version": "1.0",
        "state": "quarantined-from-older-runtime",
        "reason": "DATA_SCHEMA_NEWER_THAN_CANDIDATE",
        "data_schema": 5,
        "candidate_runtime_id": "previous",
        "supported_max": 4,
        "recovery": "USE_COMPATIBLE_RUNTIME_OR_EXPLICIT_BACKUP_RECOVERY",
    }
    assert runtime.store.load_newer_state_quarantine() == result.details["newer_state"]


def test_rollback_without_predecessor_is_actionable(tmp_path: Path) -> None:
    runtime = lifecycle(tmp_path, migration_manager=SchemaFive())
    seed_runtime(runtime, version="0.1.5", runtime_id="current")
    result = runtime.rollback()
    assert not result.ok
    assert result.code == "rollback_unavailable"
    assert result.remediation
