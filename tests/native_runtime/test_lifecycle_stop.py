from __future__ import annotations

from pathlib import Path

from wright_engineering.runtime.layout import NativeLayout
from wright_engineering.runtime.lifecycle import NativeLifecycle
from wright_engineering.runtime.models import (
    LifecycleState,
    ProcessIdentity,
    RuntimeInstallation,
    RuntimeStatus,
    SourceChannel,
    utc_now,
)
from wright_engineering.runtime.process import ProcessError


class StopProcessManager:
    def __init__(self, *, mismatch: bool = False) -> None:
        self.mismatch = mismatch
        self.stops = 0

    def stop(self, *args, **kwargs) -> None:
        if self.mismatch:
            raise ProcessError("process_start_mismatch")
        self.stops += 1


def _running_lifecycle(tmp_path: Path, manager: StopProcessManager) -> NativeLifecycle:
    layout = NativeLayout.from_wright_home(tmp_path / "wright-home")
    lifecycle = NativeLifecycle(
        layout,
        process_manager=manager,  # type: ignore[arg-type]
        health_probe=lambda _: True,
        manager_id="cli",
        adapter_protocol="wright-lifecycle-v1",
    )
    runtime_path = layout.runtime_path("runtime-1")
    executable = runtime_path / "Scripts" / "python.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"")
    manifest = lifecycle.store.load()
    manifest.runtimes["runtime-1"] = RuntimeInstallation(
        runtime_id="runtime-1",
        version="0.1.5",
        distribution="wright-engineering",
        artifact_filename="wright_engineering-0.1.5-py3-none-any.whl",
        artifact_sha256="a" * 64,
        source_channel=SourceChannel.LOCAL_CANDIDATE,
        environment_path=str(runtime_path),
        python_version="3.12.11",
        platform_tag="windows-x86_64",
        runtime_specifier="==0.1.5",
        manager_protocols={"cli": "wright-lifecycle-v1"},
        data_schema_min=1,
        data_schema_max=1,
        installed_at=utc_now(),
        verified_at=utc_now(),
        status=RuntimeStatus.ACTIVE,
    )
    manifest.active_runtime_id = "runtime-1"
    manifest.lifecycle_state = LifecycleState.HEALTHY
    manifest.process = ProcessIdentity(
        pid=42,
        started_at=utc_now(),
        runtime_id="runtime-1",
        executable_path=str(executable.resolve()),
        host="127.0.0.1",
        port=8000,
        instance_id="instance",
        challenge_hash="a" * 64,
        operation_id="start-op",
    )
    lifecycle.store.save(manifest)
    return lifecycle


def test_stop_is_idempotent_and_clears_verified_process(tmp_path: Path) -> None:
    manager = StopProcessManager()
    lifecycle = _running_lifecycle(tmp_path, manager)
    first = lifecycle.stop()
    second = lifecycle.stop()
    assert first.ok and first.state is LifecycleState.STOPPED
    assert second.ok and second.code == "already_stopped"
    assert manager.stops == 1
    assert lifecycle.store.load().process is None


def test_identity_mismatch_never_signals_and_requires_recovery(tmp_path: Path) -> None:
    manager = StopProcessManager(mismatch=True)
    lifecycle = _running_lifecycle(tmp_path, manager)
    result = lifecycle.stop()
    assert not result.ok
    assert result.state is LifecycleState.RECOVERY_REQUIRED
    assert manager.stops == 0
    assert lifecycle.store.load().process is not None
