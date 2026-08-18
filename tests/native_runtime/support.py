from __future__ import annotations

import hashlib
from dataclasses import replace
from importlib.resources import files
from pathlib import Path

from wright_engineering.runtime.artifacts import RuntimeArtifact
from wright_engineering.runtime.compatibility import CompatibilityPolicy
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


class FakeInstaller:
    def __init__(
        self, layout: NativeLayout, *, fail_versions: set[str] | None = None
    ) -> None:
        self.layout = layout
        self.fail_versions = fail_versions or set()
        self.installed: list[str] = []

    def install(self, artifact: RuntimeArtifact, runtime_id: str) -> Path:
        if artifact.version in self.fail_versions:
            raise RuntimeError("injected installer failure")
        self.installed.append(artifact.version)
        environment = self.layout.runtime_path(runtime_id)
        executable = environment / "Scripts" / "python.exe"
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b"")
        return environment


class FakeProcessManager:
    def __init__(self) -> None:
        self.launches: list[str] = []
        self.stops: list[str] = []

    def launch(self, command, **kwargs):
        runtime_id = kwargs["runtime_id"]
        self.launches.append(runtime_id)
        identity = ProcessIdentity(
            pid=100 + len(self.launches),
            started_at=utc_now(),
            runtime_id=runtime_id,
            executable_path=str(Path(command[0]).resolve()),
            host=kwargs["host"],
            port=kwargs["port"],
            instance_id=f"instance-{len(self.launches)}",
            challenge_hash=hashlib.sha256(b"challenge").hexdigest(),
            operation_id=kwargs["operation_id"],
        )
        return object(), identity, "challenge"

    def require_identity(
        self, identity, runtime_path, *, expected_runtime_id, **kwargs
    ):
        if identity.runtime_id != expected_runtime_id:
            raise RuntimeError("identity mismatch")
        return object()

    def stop(self, identity, runtime_path, *, expected_runtime_id, **kwargs):
        self.require_identity(
            identity, runtime_path, expected_runtime_id=expected_runtime_id
        )
        self.stops.append(expected_runtime_id)


def artifact(tmp_path: Path, version: str) -> RuntimeArtifact:
    wheel = tmp_path / f"wright_engineering-{version}-py3-none-any.whl"
    wheel.write_bytes(f"wheel-{version}".encode())
    return RuntimeArtifact.from_local(wheel, version, SourceChannel.LOCAL_CANDIDATE)


def lifecycle(
    tmp_path: Path,
    *,
    installer: FakeInstaller | None = None,
    process_manager: FakeProcessManager | None = None,
    health_probe=None,
    migration_manager=None,
) -> NativeLifecycle:
    layout = NativeLayout.from_wright_home(tmp_path / "wright-home")
    compatibility = replace(
        CompatibilityPolicy.load(
            Path(str(files("wright_engineering").joinpath("compatibility.json")))
        ),
        runtime_specifier=">=0.1.4,<=0.1.8",
    )
    return NativeLifecycle(
        layout,
        installer=installer or FakeInstaller(layout),  # type: ignore[arg-type]
        process_manager=process_manager or FakeProcessManager(),  # type: ignore[arg-type]
        health_probe=health_probe or (lambda _: True),
        migration_manager=migration_manager,
        compatibility=compatibility,
        manager_id="cli",
        adapter_protocol="wright-lifecycle-v1",
    )


def seed_runtime(
    runtime: NativeLifecycle,
    *,
    version: str,
    runtime_id: str,
    active: bool = True,
    running: bool = False,
    data_schema_min: int = 0,
    data_schema_max: int = 9,
    artifact_sha256: str = "a" * 64,
) -> RuntimeInstallation:
    environment = runtime.layout.runtime_path(runtime_id)
    executable = environment / "Scripts" / "python.exe"
    executable.parent.mkdir(parents=True, exist_ok=True)
    executable.write_bytes(b"")
    installation = RuntimeInstallation(
        runtime_id=runtime_id,
        version=version,
        distribution="wright-engineering",
        artifact_filename=f"wright_engineering-{version}-py3-none-any.whl",
        artifact_sha256=artifact_sha256,
        source_channel=SourceChannel.STABLE,
        environment_path=str(environment),
        python_version="3.12.11",
        platform_tag="windows-x86_64",
        runtime_specifier=f"=={version}",
        manager_protocols={"cli": "wright-lifecycle-v1"},
        data_schema_min=data_schema_min,
        data_schema_max=data_schema_max,
        installed_at=utc_now(),
        verified_at=utc_now(),
        status=RuntimeStatus.ACTIVE if active else RuntimeStatus.PREDECESSOR,
    )
    manifest = runtime.store.load()
    manifest.runtimes[runtime_id] = installation
    if active:
        manifest.active_runtime_id = runtime_id
        manifest.lifecycle_state = (
            LifecycleState.HEALTHY if running else LifecycleState.STOPPED
        )
    else:
        manifest.predecessor_runtime_id = runtime_id
    if running:
        manifest.process = ProcessIdentity(
            pid=42,
            started_at=utc_now(),
            runtime_id=runtime_id,
            executable_path=str(executable.resolve()),
            host="127.0.0.1",
            port=8000,
            instance_id="old-instance",
            challenge_hash="a" * 64,
            operation_id="old-start",
        )
    runtime.store.save(manifest)
    return installation
