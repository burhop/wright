from __future__ import annotations

from pathlib import Path

from wright_engineering.runtime.models import LifecycleState

from .support import FakeProcessManager, lifecycle, seed_runtime


def test_running_uninstall_stops_runtime_removes_code_and_preserves_data(
    tmp_path: Path,
) -> None:
    processes = FakeProcessManager()
    runtime = lifecycle(tmp_path, process_manager=processes)
    seed_runtime(runtime, version="0.1.5", runtime_id="current", running=True)
    user_file = runtime.layout.data / "workspaces" / "project" / "design.step"
    user_file.parent.mkdir(parents=True)
    user_file.write_text("keep", encoding="utf-8")
    (runtime.layout.cache / "wheel.whl").parent.mkdir(parents=True)
    (runtime.layout.cache / "wheel.whl").write_bytes(b"cache")

    result = runtime.uninstall()
    manifest = runtime.store.load()

    assert result.ok and result.state is LifecycleState.NOT_INSTALLED
    assert processes.stops == ["current"]
    assert not runtime.layout.runtimes.exists()
    assert not runtime.layout.cache.exists()
    assert user_file.read_text(encoding="utf-8") == "keep"
    assert manifest.runtimes == {}


def test_uninstall_is_idempotent(tmp_path: Path) -> None:
    runtime = lifecycle(tmp_path)
    assert runtime.uninstall().ok
    second = runtime.uninstall()
    assert second.ok
    assert second.code == "already_uninstalled"
