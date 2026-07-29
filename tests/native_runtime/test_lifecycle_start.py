from __future__ import annotations

import hashlib
from pathlib import Path

from wright_engineering.runtime.artifacts import RuntimeArtifact
from wright_engineering.runtime.layout import NativeLayout
from wright_engineering.runtime.lifecycle import NativeLifecycle
from wright_engineering.runtime.models import (
    LifecycleState,
    ProcessIdentity,
    SourceChannel,
    utc_now,
)


class FakeInstaller:
    def __init__(self, layout: NativeLayout, *, fail: bool = False) -> None:
        self.layout = layout
        self.fail = fail
        self.calls = 0

    def install(self, artifact: RuntimeArtifact, runtime_id: str) -> Path:
        self.calls += 1
        if self.fail:
            raise RuntimeError("injected install failure with secret=do-not-leak")
        environment = self.layout.runtime_path(runtime_id)
        executable = environment / "Scripts" / "python.exe"
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b"")
        return environment


class FakeProcessManager:
    def __init__(self) -> None:
        self.launches = 0
        self.identity: ProcessIdentity | None = None

    def launch(self, command, **kwargs):
        self.launches += 1
        self.identity = ProcessIdentity(
            pid=123,
            started_at=utc_now(),
            runtime_id=kwargs["runtime_id"],
            executable_path=str(Path(command[0]).resolve()),
            host=kwargs["host"],
            port=kwargs["port"],
            instance_id="00000000-0000-4000-8000-000000000123",
            challenge_hash=hashlib.sha256(b"challenge").hexdigest(),
            operation_id=kwargs["operation_id"],
        )
        return object(), self.identity, "challenge"

    def require_identity(
        self, identity, runtime_path, *, expected_runtime_id, **kwargs
    ):
        assert identity.runtime_id == expected_runtime_id
        assert Path(identity.executable_path).is_relative_to(runtime_path)
        return object()

    def stop(self, *args, **kwargs):
        return None


def _artifact(tmp_path: Path) -> RuntimeArtifact:
    wheel = tmp_path / "wright_engineering-0.1.6-py3-none-any.whl"
    wheel.write_bytes(b"wheel")
    return RuntimeArtifact.from_local(wheel, "0.1.6", SourceChannel.LOCAL_CANDIDATE)


def test_start_automatically_installs_then_reuses_healthy_runtime(
    tmp_path: Path,
) -> None:
    layout = NativeLayout.from_wright_home(tmp_path / "wright-home")
    installer = FakeInstaller(layout)
    processes = FakeProcessManager()
    lifecycle = NativeLifecycle(
        layout,
        installer=installer,  # type: ignore[arg-type]
        process_manager=processes,  # type: ignore[arg-type]
        health_probe=lambda _: True,
        manager_id="cli",
        adapter_protocol="wright-lifecycle-v1",
    )

    first = lifecycle.start(artifact=_artifact(tmp_path))
    second = lifecycle.start()

    assert first.ok and first.state is LifecycleState.HEALTHY
    assert second.ok and second.code == "already_running"
    assert installer.calls == 1
    assert processes.launches == 1


def test_failed_install_is_actionable_and_never_healthy(tmp_path: Path) -> None:
    layout = NativeLayout.from_wright_home(tmp_path / "wright-home")
    lifecycle = NativeLifecycle(
        layout,
        installer=FakeInstaller(layout, fail=True),  # type: ignore[arg-type]
        process_manager=FakeProcessManager(),  # type: ignore[arg-type]
        health_probe=lambda _: True,
        manager_id="cli",
        adapter_protocol="wright-lifecycle-v1",
    )
    result = lifecycle.start(artifact=_artifact(tmp_path))
    assert not result.ok
    assert result.state in {LifecycleState.FAILED, LifecycleState.RECOVERY_REQUIRED}
    assert "do-not-leak" not in repr(result.to_dict())
    assert result.remediation


def test_failed_health_never_reports_candidate_active(tmp_path: Path) -> None:
    layout = NativeLayout.from_wright_home(tmp_path / "wright-home")
    lifecycle = NativeLifecycle(
        layout,
        installer=FakeInstaller(layout),  # type: ignore[arg-type]
        process_manager=FakeProcessManager(),  # type: ignore[arg-type]
        health_probe=lambda _: False,
        manager_id="cli",
        adapter_protocol="wright-lifecycle-v1",
    )
    result = lifecycle.start(artifact=_artifact(tmp_path))
    assert not result.ok
    assert result.code == "health_failed"
    assert lifecycle.store.load().lifecycle_state is LifecycleState.FAILED


def test_start_fails_closed_for_unsupported_manager_protocol(tmp_path: Path) -> None:
    layout = NativeLayout.from_wright_home(tmp_path / "wright-home")
    lifecycle = NativeLifecycle(
        layout,
        installer=FakeInstaller(layout),  # type: ignore[arg-type]
        process_manager=FakeProcessManager(),  # type: ignore[arg-type]
        health_probe=lambda _: True,
        manager_id="hermes",
        manager_version="0.19.0",
        adapter_protocol="invented-package-plugin-v1",
    )
    result = lifecycle.start(artifact=_artifact(tmp_path))
    assert not result.ok
    assert result.code == "compatibility_failed"
    assert result.details["compatibility_code"] == "manager_protocol_incompatible"


def test_runtime_environment_roots_secret_storage_in_wright_home(tmp_path: Path) -> None:
    layout = NativeLayout.from_wright_home(tmp_path / "wright-home")
    lifecycle = NativeLifecycle(
        layout,
        installer=FakeInstaller(layout),  # type: ignore[arg-type]
        process_manager=FakeProcessManager(),  # type: ignore[arg-type]
        manager_id="codex",
        adapter_protocol="mcp-v1",
    )

    environment = lifecycle._runtime_environment()

    assert environment["WRIGHT_SECRETS_PATH"] == str(
        layout.data / "credentials.json"
    )
    assert environment["WRIGHT_SECRETS_DIR"] == str(layout.data / "secrets.d")
    assert environment["WRIGHT_AUTH_MODE"] == "enforced"
    assert len(environment["WRIGHT_API_TOKEN"]) == 64
    assert layout.control_plane_token.read_text(encoding="utf-8") == environment[
        "WRIGHT_API_TOKEN"
    ]
