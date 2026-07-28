from __future__ import annotations

from pathlib import Path

from wright_engineering.runtime.layout import NativeLayout
from wright_engineering.runtime.lifecycle import NativeLifecycle


def test_competing_session_receives_lifecycle_busy_with_operation_id(
    tmp_path: Path,
) -> None:
    layout = NativeLayout.from_hermes_home(tmp_path / "hermes")
    lifecycle = NativeLifecycle(
        layout,
        lock_timeout=0.02,
        hermes_version="0.19.0",
        plugin_capability="python-distribution-v1",
    )
    with lifecycle.store.lock(operation_id="session-one", timeout=0.1):
        result = lifecycle.start(requested_by="session-two")
    assert not result.ok
    assert result.code == "lifecycle_busy"
    assert result.details["active_operation_id"] == "session-one"


def test_status_remains_available_while_mutation_lock_is_held(tmp_path: Path) -> None:
    layout = NativeLayout.from_hermes_home(tmp_path / "hermes")
    lifecycle = NativeLifecycle(
        layout,
        hermes_version="0.19.0",
        plugin_capability="python-distribution-v1",
    )
    with lifecycle.store.lock(operation_id="session-one", timeout=0.1):
        result = lifecycle.status()
    assert result.ok
