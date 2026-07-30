"""Manager-neutral orchestration of Wright's isolated native runtime."""

from __future__ import annotations

import json
import os
import shutil
import sys
import time
import urllib.error
import urllib.request
from hashlib import sha256
from importlib.metadata import version as distribution_version
from importlib.resources import files
from pathlib import Path
from typing import Callable, Mapping
from uuid import uuid4

from wright_engineering.runtime.compatibility import (
    CompatibilityError,
    CompatibilityPolicy,
    current_platform_tag,
)

from .artifacts import ArtifactResolver, RuntimeArtifact
from .auth import ensure_control_plane_token
from .diagnostics import bounded_details, core_checks_ok, run_named_probes, safe_probe
from .installer import RuntimeInstaller
from .layout import NativeLayout
from .logging import LifecycleLogger
from .migrations import NativeMigrationManager
from .models import (
    LifecycleResult,
    LifecycleState,
    Manifest,
    OperationKind,
    OperationRecord,
    ProcessIdentity,
    ResultCode,
    RuntimeInstallation,
    RuntimeStatus,
    utc_now,
)
from .process import ProcessError, ProcessManager
from .purge import PurgeManager
from .state import LifecycleBusy, ManifestStore, StateError


HealthProbe = Callable[[ProcessIdentity], bool]


def _runtime_id(artifact: RuntimeArtifact) -> str:
    identity = "|".join(
        (
            "wright-engineering",
            artifact.version,
            f"{sys.version_info.major}.{sys.version_info.minor}",
            sys.platform,
            artifact.sha256,
        )
    )
    return sha256(identity.encode("utf-8")).hexdigest()[:24]


class NativeLifecycle:
    def __init__(
        self,
        layout: NativeLayout,
        *,
        store: ManifestStore | None = None,
        installer: RuntimeInstaller | None = None,
        process_manager: ProcessManager | None = None,
        health_probe: HealthProbe | None = None,
        compatibility: CompatibilityPolicy | None = None,
        manager_id: str | None = None,
        manager_version: str | None = None,
        adapter_protocol: str | None = None,
        status_probes: Mapping[str, Callable[[], object]] | None = None,
        doctor_probes: Mapping[str, Callable[[], object]] | None = None,
        lock_timeout: float = 5.0,
        lifecycle_logger: LifecycleLogger | None = None,
        migration_manager: NativeMigrationManager | None = None,
        host: str = "127.0.0.1",
        port: int = 8000,
    ) -> None:
        self.layout = layout
        self.store = store or ManifestStore(layout)
        self.installer = installer or RuntimeInstaller(layout)
        self.process_manager = process_manager or ProcessManager()
        self.health_probe = health_probe or self._probe_health
        self.compatibility = compatibility or CompatibilityPolicy.load(
            Path(str(files("wright_engineering").joinpath("compatibility.json")))
        )
        self.manager_id = manager_id or os.environ.get("WRIGHT_MANAGER_ID", "cli")
        self.manager_version = manager_version or os.environ.get(
            "WRIGHT_MANAGER_VERSION"
        )
        self.adapter_protocol = adapter_protocol or os.environ.get(
            "WRIGHT_MANAGER_PROTOCOL", "wright-lifecycle-v1"
        )
        self.status_probes = dict(status_probes or {})
        self.doctor_probes = dict(doctor_probes or {})
        self.lock_timeout = lock_timeout
        self.logger = lifecycle_logger or LifecycleLogger(
            self.layout.logs / "lifecycle.jsonl"
        )
        self.migration_manager = migration_manager or NativeMigrationManager()
        self.host = host
        self.port = port

    @classmethod
    def default(cls) -> NativeLifecycle:
        return cls(
            NativeLayout.discover(),
            port=int(os.environ.get("WRIGHT_NATIVE_PORT", "8000")),
        )

    def start(
        self,
        *,
        requested_by: str | None = None,
        artifact: RuntimeArtifact | None = None,
    ) -> LifecycleResult:
        operation_id = str(uuid4())
        started_at = utc_now()
        try:
            artifact = artifact or ArtifactResolver().resolve_environment()
            with self.store.lock(operation_id=operation_id, timeout=self.lock_timeout):
                manifest = self.store.load()
                if manifest.current_operation is not None:
                    return self._result(
                        manifest,
                        operation_id,
                        "start",
                        False,
                        ResultCode.RECOVERY_REQUIRED,
                        "A prior lifecycle operation requires recovery.",
                        started_at,
                        remediation=["Run /wright doctor before retrying."],
                    )
                runtime_version = (
                    artifact.version
                    if artifact is not None
                    else (
                        manifest.runtimes[manifest.active_runtime_id].version
                        if manifest.active_runtime_id
                        else self.compatibility.runtime_version
                    )
                )
                self.compatibility.require_compatible(
                    runtime_version=runtime_version,
                    python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                    platform_tag=current_platform_tag(),
                    data_schema=1,
                    manager_id=self.manager_id,
                    manager_version=self.manager_version,
                    adapter_protocol=self.adapter_protocol,
                )
                if (
                    manifest.lifecycle_state is LifecycleState.HEALTHY
                    and manifest.process is not None
                    and manifest.active_runtime_id is not None
                ):
                    runtime = manifest.runtimes[manifest.active_runtime_id]
                    self.process_manager.require_identity(
                        manifest.process,
                        Path(runtime.environment_path),
                        expected_runtime_id=runtime.runtime_id,
                    )
                    if self.health_probe(manifest.process):
                        return self._result(
                            manifest,
                            operation_id,
                            "start",
                            True,
                            ResultCode.ALREADY_RUNNING,
                            "Wright is already healthy.",
                            started_at,
                            details=self._healthy_details(manifest),
                            persist=False,
                        )

                if manifest.active_runtime_id is None:
                    if artifact is None:
                        return self._result(
                            manifest,
                            operation_id,
                            "start",
                            False,
                            "runtime_artifact_required",
                            "No compatible managed Wright runtime is installed.",
                            started_at,
                            remediation=[
                                "Install or update Wright through the supported adapter for this manager."
                            ],
                        )
                    manifest = self._install_locked(
                        manifest,
                        artifact,
                        operation_id,
                        requested_by or self.manager_id,
                    )

                active_runtime_id = manifest.active_runtime_id
                if active_runtime_id is None:
                    raise RuntimeError("runtime_activation_missing")
                runtime = manifest.runtimes[active_runtime_id]
                manifest.transition(LifecycleState.STARTING)
                manifest.current_operation = OperationRecord(
                    operation_id=operation_id,
                    kind=OperationKind.START,
                    requested_by=requested_by or self.manager_id,
                    started_at=started_at,
                    from_state=LifecycleState.STOPPED,
                    target_state=LifecycleState.HEALTHY,
                    candidate_runtime_id=runtime.runtime_id,
                )
                self.store.save(manifest)

                environment = Path(runtime.environment_path)
                python = RuntimeInstaller.environment_python(environment)
                log_path = self.layout.logs / f"runtime-{operation_id}.log"
                self.layout.logs.mkdir(parents=True, exist_ok=True)
                with log_path.open("ab") as log_handle:
                    _, identity, _ = self.process_manager.launch(
                        [
                            str(python),
                            "-m",
                            "wright_engineering.cli",
                            "runtime",
                            "serve",
                            "--host",
                            self.host,
                            "--port",
                            str(self.port),
                            "--data-root",
                            str(self.layout.data),
                        ],
                        runtime_id=runtime.runtime_id,
                        runtime_path=environment,
                        operation_id=operation_id,
                        host=self.host,
                        port=self.port,
                        environment=self._runtime_environment(),
                        log_handle=log_handle,
                    )
                manifest.process = identity
                manifest.current_operation.checkpoint = "process_launched"
                self.store.save(manifest)

                if not self.health_probe(identity):
                    try:
                        self.process_manager.stop(
                            identity,
                            environment,
                            expected_runtime_id=runtime.runtime_id,
                        )
                    except Exception:
                        pass
                    manifest.process = None
                    runtime.status = RuntimeStatus.FAILED
                    runtime.failure_code = "health_failed"
                    manifest.active_runtime_id = None
                    manifest.transition(LifecycleState.FAILED)
                    manifest.current_operation = None
                    return self._result(
                        manifest,
                        operation_id,
                        "start",
                        False,
                        ResultCode.HEALTH_FAILED,
                        "Wright started but did not prove its runtime identity and health.",
                        started_at,
                        remediation=[
                            "Run /wright doctor and inspect the redacted runtime log."
                        ],
                    )

                identity.health_verified_at = utc_now()
                runtime.status = RuntimeStatus.ACTIVE
                runtime.verified_at = runtime.verified_at or utc_now()
                manifest.process = identity
                manifest.transition(LifecycleState.HEALTHY)
                manifest.current_operation = None
                return self._result(
                    manifest,
                    operation_id,
                    "start",
                    True,
                    ResultCode.OK,
                    "Wright is healthy.",
                    started_at,
                    details=self._healthy_details(manifest),
                )
        except CompatibilityError as exc:
            manifest = self.store.load()
            return self._result(
                manifest,
                operation_id,
                "start",
                False,
                ResultCode.COMPATIBILITY_FAILED,
                "This manager adapter, runtime, Python, or platform combination is not supported.",
                started_at,
                details={"compatibility_code": exc.code},
                remediation=[
                    "Use a supported manager adapter protocol and Wright runtime version."
                ],
            )
        except LifecycleBusy as exc:
            manifest = self.store.load()
            return self._result(
                manifest,
                operation_id,
                "start",
                False,
                ResultCode.LIFECYCLE_BUSY,
                "Another Wright lifecycle operation is in progress.",
                started_at,
                details={"active_operation_id": exc.operation_id},
                persist=False,
            )
        except Exception as exc:
            manifest = self.store.load()
            if manifest.lifecycle_state not in {
                LifecycleState.FAILED,
                LifecycleState.RECOVERY_REQUIRED,
            }:
                try:
                    manifest.transition(LifecycleState.FAILED)
                except ValueError:
                    manifest.lifecycle_state = LifecycleState.RECOVERY_REQUIRED
            manifest.current_operation = None
            return self._result(
                manifest,
                operation_id,
                "start",
                False,
                "start_failed",
                "Wright could not be installed or started.",
                started_at,
                details={"error_type": type(exc).__name__},
                remediation=["Run /wright doctor for safe recovery guidance."],
            )

    def status(self) -> LifecycleResult:
        started_at = utc_now()
        operation_id = str(uuid4())
        try:
            manifest = self.store.load()
        except StateError as exc:
            return LifecycleResult(
                operation_id=operation_id,
                command="status",
                ok=False,
                state=LifecycleState.RECOVERY_REQUIRED,
                code=exc.code,
                summary="Wright lifecycle state could not be read safely.",
                details={},
                remediation=["Run /wright doctor before changing the installation."],
                started_at=started_at,
                finished_at=utc_now(),
            )
        details: dict[str, object] = {
            "runtime_distribution_version": self._distribution_version(),
            "manager_id": self.manager_id,
            "adapter_protocol": self.adapter_protocol,
            "state": manifest.lifecycle_state.value,
            "data_root": manifest.data_root,
            "active_runtime": manifest.active_runtime_id,
            "predecessor_runtime": manifest.predecessor_runtime_id,
            "operation_id": manifest.current_operation.operation_id
            if manifest.current_operation
            else None,
            "ui_url": f"http://{self.host}:{self.port}/",
            "api_healthy": False,
            "ui_healthy": False,
        }
        compatibility: dict[str, object]
        try:
            runtime_version = (
                manifest.runtimes[manifest.active_runtime_id].version
                if manifest.active_runtime_id
                else self.compatibility.runtime_version
            )
            self.compatibility.require_compatible(
                runtime_version=runtime_version,
                python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                platform_tag=current_platform_tag(),
                data_schema=1,
                manager_id=self.manager_id,
                manager_version=self.manager_version,
                adapter_protocol=self.adapter_protocol,
            )
            compatibility = {"ok": True, "code": "compatible"}
        except CompatibilityError as exc:
            compatibility = {"ok": False, "code": exc.code}
        details["compatibility"] = compatibility
        if manifest.process:
            process_owned = False
            if manifest.active_runtime_id:
                runtime = manifest.runtimes[manifest.active_runtime_id]
                try:
                    self.process_manager.require_identity(
                        manifest.process,
                        Path(runtime.environment_path),
                        expected_runtime_id=runtime.runtime_id,
                    )
                    process_owned = True
                except ProcessError as exc:
                    details["process_identity_code"] = str(exc)
                    process_owned = False
                except Exception:
                    details["process_identity_code"] = "process_identity_unavailable"
                    process_owned = False
            healthy = process_owned and self.health_probe(manifest.process)
            details.update(
                {
                    "pid": manifest.process.pid,
                    "instance_id": manifest.process.instance_id,
                    "process_owned": process_owned,
                    "api_healthy": healthy,
                    "ui_healthy": healthy,
                }
            )
        details.update(
            run_named_probes(
                ("manager", "mcp", "catalog", "configuration", "workspaces"),
                self.status_probes,
            )
        )
        return LifecycleResult(
            operation_id=operation_id,
            command="status",
            ok=True,
            state=manifest.lifecycle_state,
            code=ResultCode.OK.value,
            summary=f"Wright is {manifest.lifecycle_state.value}.",
            details=bounded_details(
                details,
                allowed=set(details),
            ),
            started_at=started_at,
            finished_at=utc_now(),
        )

    def doctor(self) -> LifecycleResult:
        started_at = utc_now()
        operation_id = str(uuid4())
        status = self.status()
        checks: dict[str, object] = {
            "manifest": {"ok": status.code != "manifest_corrupt"},
            "compatibility": status.details.get("compatibility", {"ok": False}),
            "runtime_containment": {"ok": self._runtime_paths_contained()},
            "process_ownership": {
                "ok": status.details.get(
                    "process_owned", status.state is not LifecycleState.HEALTHY
                )
            },
            "api": {"ok": bool(status.details.get("api_healthy"))},
            "ui": {"ok": bool(status.details.get("ui_healthy"))},
            "data_permissions": {"ok": self._data_permissions_ready()},
            "backup": safe_probe("backup", self.doctor_probes.get("backup")),
            "manager": status.details.get("manager", {"ok": False}),
            "mcp": status.details.get("mcp", {"ok": False}),
            "catalog": status.details.get("catalog", {"ok": False}),
            "configuration": status.details.get("configuration", {"ok": False}),
            "workspaces": status.details.get("workspaces", {"ok": False}),
        }
        optional = {
            name: safe_probe(name, probe)
            for name, probe in self.doctor_probes.items()
            if name != "backup"
        }
        core_ok = core_checks_ok(
            checks,
            require_running_health=status.state
            in {LifecycleState.HEALTHY, LifecycleState.DEGRADED},
        )
        return LifecycleResult(
            operation_id=operation_id,
            command="doctor",
            ok=core_ok,
            state=status.state,
            code=ResultCode.OK.value if core_ok else "doctor_findings",
            summary=(
                "Wright's core native installation checks passed."
                if core_ok
                else "Wright has core installation findings that need attention."
            ),
            details=bounded_details(
                {"checks": checks, "optional": optional},
                allowed={"checks", "optional"},
            ),
            remediation=[]
            if core_ok
            else ["Review the failed checks before changing lifecycle state."],
            started_at=started_at,
            finished_at=utc_now(),
        )

    def stop(self, *, requested_by: str | None = None) -> LifecycleResult:
        operation_id = str(uuid4())
        started_at = utc_now()
        try:
            with self.store.lock(operation_id=operation_id, timeout=self.lock_timeout):
                manifest = self.store.load()
                if manifest.process is None:
                    if manifest.lifecycle_state in {
                        LifecycleState.HEALTHY,
                        LifecycleState.DEGRADED,
                        LifecycleState.STARTING,
                    }:
                        manifest.lifecycle_state = LifecycleState.RECOVERY_REQUIRED
                        return self._result(
                            manifest,
                            operation_id,
                            "stop",
                            False,
                            ResultCode.RECOVERY_REQUIRED,
                            "Lifecycle state claims a running runtime but no process identity is recorded.",
                            started_at,
                            remediation=["Run /wright doctor before retrying."],
                        )
                    return self._result(
                        manifest,
                        operation_id,
                        "stop",
                        True,
                        ResultCode.ALREADY_STOPPED,
                        "Wright is already stopped.",
                        started_at,
                    )
                runtime_id = manifest.process.runtime_id
                runtime = manifest.runtimes.get(runtime_id)
                if runtime is None or manifest.active_runtime_id != runtime_id:
                    manifest.lifecycle_state = LifecycleState.RECOVERY_REQUIRED
                    return self._result(
                        manifest,
                        operation_id,
                        "stop",
                        False,
                        ResultCode.PROCESS_IDENTITY_FAILED,
                        "The recorded process does not match the active runtime.",
                        started_at,
                        remediation=["Run /wright doctor; no process was signaled."],
                    )
                from_state = manifest.lifecycle_state
                if from_state is not LifecycleState.STOPPING:
                    manifest.transition(LifecycleState.STOPPING)
                manifest.current_operation = OperationRecord(
                    operation_id=operation_id,
                    kind=OperationKind.STOP,
                    requested_by=requested_by or self.manager_id,
                    started_at=started_at,
                    from_state=from_state,
                    target_state=LifecycleState.STOPPED,
                    candidate_runtime_id=runtime_id,
                )
                self.store.save(manifest)
                try:
                    self.process_manager.stop(
                        manifest.process,
                        Path(runtime.environment_path),
                        expected_runtime_id=runtime_id,
                    )
                except Exception as exc:
                    manifest.lifecycle_state = LifecycleState.RECOVERY_REQUIRED
                    manifest.current_operation = None
                    return self._result(
                        manifest,
                        operation_id,
                        "stop",
                        False,
                        ResultCode.PROCESS_IDENTITY_FAILED,
                        "Wright refused to signal a process whose identity could not be proven.",
                        started_at,
                        details={"error_type": type(exc).__name__},
                        remediation=[
                            "Run /wright doctor; unrelated processes were left untouched."
                        ],
                    )
                manifest.process = None
                runtime.status = RuntimeStatus.VERIFIED
                manifest.transition(LifecycleState.STOPPED)
                manifest.current_operation = None
                return self._result(
                    manifest,
                    operation_id,
                    "stop",
                    True,
                    ResultCode.OK,
                    "Wright stopped safely.",
                    started_at,
                )
        except LifecycleBusy as exc:
            manifest = self.store.load()
            return self._result(
                manifest,
                operation_id,
                "stop",
                False,
                ResultCode.LIFECYCLE_BUSY,
                "Another Wright lifecycle operation is in progress.",
                started_at,
                details={"active_operation_id": exc.operation_id},
                persist=False,
            )

    def update(
        self,
        version: str | None = None,
        *,
        artifact: RuntimeArtifact | None = None,
        requested_by: str | None = None,
    ) -> LifecycleResult:
        operation_id = str(uuid4())
        started_at = utc_now()
        try:
            artifact = artifact or ArtifactResolver().resolve_environment()
            with self.store.lock(operation_id=operation_id, timeout=self.lock_timeout):
                manifest = self.store.load()
                if artifact is None:
                    return self._result(
                        manifest,
                        operation_id,
                        "update",
                        False,
                        "update_artifact_required",
                        "An exact approved Wright update artifact is required.",
                        started_at,
                        remediation=[
                            "Retry through the supported Wright manager adapter."
                        ],
                    )
                if version and version != artifact.version:
                    return self._result(
                        manifest,
                        operation_id,
                        "update",
                        False,
                        "update_version_mismatch",
                        "The requested version does not match the supplied artifact.",
                        started_at,
                    )
                current_id = manifest.active_runtime_id
                if current_id is None or current_id not in manifest.runtimes:
                    return self._result(
                        manifest,
                        operation_id,
                        "update",
                        False,
                        "update_not_installed",
                        "Wright must be installed before it can be updated.",
                        started_at,
                        remediation=[
                            "Run /wright start with an approved install artifact."
                        ],
                    )
                current = manifest.runtimes[current_id]
                if current.version == artifact.version:
                    return self._result(
                        manifest,
                        operation_id,
                        "update",
                        True,
                        "already_current",
                        f"Wright {artifact.version} is already active.",
                        started_at,
                        persist=False,
                    )
                self.compatibility.require_compatible(
                    runtime_version=artifact.version,
                    python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                    platform_tag=current_platform_tag(),
                    data_schema=self.migration_manager.current_schema(self.layout.data),
                    manager_id=self.manager_id,
                    manager_version=self.manager_version,
                    adapter_protocol=self.adapter_protocol,
                )
                origin_state = manifest.lifecycle_state
                was_running = (
                    origin_state in {LifecycleState.HEALTHY, LifecycleState.DEGRADED}
                    and manifest.process is not None
                )
                manifest.transition(LifecycleState.UPDATING)
                candidate_id = _runtime_id(artifact)
                manifest.desired_runtime_version = artifact.version
                manifest.current_operation = OperationRecord(
                    operation_id=operation_id,
                    kind=OperationKind.UPDATE,
                    requested_by=requested_by or self.manager_id,
                    started_at=started_at,
                    from_state=origin_state,
                    target_state=LifecycleState.HEALTHY
                    if was_running
                    else LifecycleState.STOPPED,
                    candidate_runtime_id=candidate_id,
                )
                self.store.save(manifest)
                try:
                    candidate = manifest.runtimes.get(candidate_id)
                    if candidate is None:
                        environment = self.installer.install(artifact, candidate_id)
                        candidate = self._installation_from_artifact(
                            artifact, candidate_id, environment
                        )
                        manifest.runtimes[candidate_id] = candidate
                    manifest.current_operation.checkpoint = "candidate_verified"
                    self.store.save(manifest)
                    backup = self.migration_manager.prepare_activation(
                        data_root=self.layout.data,
                        data_schema_min=candidate.data_schema_min,
                        data_schema_max=candidate.data_schema_max,
                        operation_id=operation_id,
                    )
                    manifest.current_operation.backup_manifest = backup
                    manifest.current_operation.checkpoint = "migration_ready"
                    self.store.save(manifest)
                except Exception as exc:
                    if candidate_id in manifest.runtimes:
                        manifest.runtimes[candidate_id].status = RuntimeStatus.FAILED
                        manifest.runtimes[
                            candidate_id
                        ].failure_code = "update_staging_failed"
                    manifest.lifecycle_state = origin_state
                    manifest.current_operation = None
                    return self._result(
                        manifest,
                        operation_id,
                        "update",
                        False,
                        "update_staging_failed",
                        "The update failed before activation; the current runtime was preserved.",
                        started_at,
                        details={"error_type": type(exc).__name__},
                        remediation=[
                            "Check artifact and migration diagnostics, then retry."
                        ],
                    )

                if was_running and manifest.process is not None:
                    self.process_manager.stop(
                        manifest.process,
                        Path(current.environment_path),
                        expected_runtime_id=current.runtime_id,
                    )
                    manifest.process = None
                current.status = RuntimeStatus.PREDECESSOR
                candidate.status = RuntimeStatus.ACTIVE
                manifest.predecessor_runtime_id = current_id
                manifest.active_runtime_id = candidate_id
                manifest.current_operation.checkpoint = "candidate_activated"
                self.store.save(manifest)

                if was_running:
                    identity = self._launch_runtime(candidate, operation_id)
                    if identity is None:
                        candidate.status = RuntimeStatus.FAILED
                        candidate.failure_code = "health_failed"
                        current.status = RuntimeStatus.ACTIVE
                        manifest.active_runtime_id = current_id
                        manifest.predecessor_runtime_id = None
                        recovered = self._launch_runtime(current, operation_id)
                        manifest.current_operation = None
                        if recovered is not None:
                            manifest.process = recovered
                            manifest.lifecycle_state = LifecycleState.HEALTHY
                            return self._result(
                                manifest,
                                operation_id,
                                "update",
                                False,
                                "update_recovered",
                                "The candidate failed health verification; the predecessor was restored.",
                                started_at,
                            )
                        manifest.process = None
                        manifest.lifecycle_state = LifecycleState.RECOVERY_REQUIRED
                        return self._result(
                            manifest,
                            operation_id,
                            "update",
                            False,
                            ResultCode.RECOVERY_REQUIRED,
                            "The candidate and predecessor could not be verified after update.",
                            started_at,
                            remediation=[
                                "Use the recorded backup and runtime evidence for manual recovery."
                            ],
                        )
                    manifest.process = identity
                    manifest.lifecycle_state = LifecycleState.HEALTHY
                else:
                    manifest.process = None
                    manifest.lifecycle_state = LifecycleState.STOPPED
                manifest.current_operation = None
                return self._result(
                    manifest,
                    operation_id,
                    "update",
                    True,
                    ResultCode.OK,
                    f"Wright updated to {candidate.version}; the predecessor is retained.",
                    started_at,
                    details={
                        "active_runtime": candidate.runtime_id,
                        "predecessor_runtime": current.runtime_id,
                    },
                )
        except LifecycleBusy as exc:
            manifest = self.store.load()
            return self._result(
                manifest,
                operation_id,
                "update",
                False,
                ResultCode.LIFECYCLE_BUSY,
                "Another Wright lifecycle operation is in progress.",
                started_at,
                details={"active_operation_id": exc.operation_id},
                persist=False,
            )
        except Exception as exc:
            manifest = self.store.load()
            manifest.lifecycle_state = LifecycleState.RECOVERY_REQUIRED
            manifest.current_operation = None
            return self._result(
                manifest,
                operation_id,
                "update",
                False,
                ResultCode.RECOVERY_REQUIRED,
                "The update could not complete safely.",
                started_at,
                details={"error_type": type(exc).__name__},
                remediation=["Run /wright doctor before retrying."],
            )

    def rollback(
        self,
        version: str | None = None,
        *,
        requested_by: str | None = None,
    ) -> LifecycleResult:
        operation_id = str(uuid4())
        started_at = utc_now()
        try:
            with self.store.lock(operation_id=operation_id, timeout=self.lock_timeout):
                manifest = self.store.load()
                current_id = manifest.active_runtime_id
                target_id = manifest.predecessor_runtime_id
                if version:
                    target_id = next(
                        (
                            item.runtime_id
                            for item in manifest.runtimes.values()
                            if item.version == version
                            and item.status
                            in {RuntimeStatus.PREDECESSOR, RuntimeStatus.VERIFIED}
                        ),
                        None,
                    )
                if (
                    current_id is None
                    or target_id is None
                    or current_id not in manifest.runtimes
                    or target_id not in manifest.runtimes
                    or not Path(manifest.runtimes[target_id].environment_path).is_dir()
                ):
                    return self._result(
                        manifest,
                        operation_id,
                        "rollback",
                        False,
                        "rollback_unavailable",
                        "No retained compatible rollback runtime is available.",
                        started_at,
                        remediation=[
                            "Install an exact approved version through the Wright lifecycle."
                        ],
                    )
                current = manifest.runtimes[current_id]
                target = manifest.runtimes[target_id]
                schema = self.migration_manager.current_schema(self.layout.data)
                if not target.data_schema_min <= schema <= target.data_schema_max:
                    return self._result(
                        manifest,
                        operation_id,
                        "rollback",
                        False,
                        "rollback_schema_incompatible",
                        "The retained runtime cannot open the current data schema.",
                        started_at,
                        details={
                            "current_schema": schema,
                            "supported_min": target.data_schema_min,
                            "supported_max": target.data_schema_max,
                        },
                        remediation=[
                            "Use the documented explicit backup recovery procedure."
                        ],
                    )
                origin_state = manifest.lifecycle_state
                was_running = (
                    origin_state in {LifecycleState.HEALTHY, LifecycleState.DEGRADED}
                    and manifest.process is not None
                )
                manifest.transition(LifecycleState.ROLLING_BACK)
                manifest.current_operation = OperationRecord(
                    operation_id=operation_id,
                    kind=OperationKind.ROLLBACK,
                    requested_by=requested_by or self.manager_id,
                    started_at=started_at,
                    from_state=origin_state,
                    target_state=LifecycleState.HEALTHY
                    if was_running
                    else LifecycleState.STOPPED,
                    candidate_runtime_id=target_id,
                    recovery_action="Reactivate current runtime; never restore data implicitly.",
                )
                self.store.save(manifest)
                if was_running and manifest.process is not None:
                    self.process_manager.stop(
                        manifest.process,
                        Path(current.environment_path),
                        expected_runtime_id=current_id,
                    )
                    manifest.process = None
                current.status = RuntimeStatus.PREDECESSOR
                target.status = RuntimeStatus.ACTIVE
                manifest.active_runtime_id = target_id
                manifest.predecessor_runtime_id = current_id
                if was_running:
                    identity = self._launch_runtime(target, operation_id)
                    if identity is None:
                        target.status = RuntimeStatus.PREDECESSOR
                        current.status = RuntimeStatus.ACTIVE
                        manifest.active_runtime_id = current_id
                        manifest.predecessor_runtime_id = target_id
                        restored = self._launch_runtime(current, operation_id)
                        manifest.current_operation = None
                        if restored is not None:
                            manifest.process = restored
                            manifest.lifecycle_state = LifecycleState.HEALTHY
                            return self._result(
                                manifest,
                                operation_id,
                                "rollback",
                                False,
                                "rollback_recovered",
                                "Rollback health failed; the current runtime was restored.",
                                started_at,
                            )
                        manifest.lifecycle_state = LifecycleState.RECOVERY_REQUIRED
                        return self._result(
                            manifest,
                            operation_id,
                            "rollback",
                            False,
                            ResultCode.RECOVERY_REQUIRED,
                            "Neither rollback target nor current runtime could be verified.",
                            started_at,
                        )
                    manifest.process = identity
                    manifest.lifecycle_state = LifecycleState.HEALTHY
                else:
                    manifest.lifecycle_state = LifecycleState.STOPPED
                    manifest.process = None
                manifest.current_operation = None
                return self._result(
                    manifest,
                    operation_id,
                    "rollback",
                    True,
                    ResultCode.OK,
                    f"Wright rolled back to {target.version} without changing user data.",
                    started_at,
                )
        except LifecycleBusy as exc:
            manifest = self.store.load()
            return self._result(
                manifest,
                operation_id,
                "rollback",
                False,
                ResultCode.LIFECYCLE_BUSY,
                "Another Wright lifecycle operation is in progress.",
                started_at,
                details={"active_operation_id": exc.operation_id},
                persist=False,
            )

    def uninstall(self, *, requested_by: str | None = None) -> LifecycleResult:
        operation_id = str(uuid4())
        started_at = utc_now()
        try:
            with self.store.lock(operation_id=operation_id, timeout=self.lock_timeout):
                manifest = self.store.load()
                managed_exists = (
                    self.layout.runtimes.exists() or self.layout.cache.exists()
                )
                if (
                    manifest.lifecycle_state is LifecycleState.NOT_INSTALLED
                    and not manifest.runtimes
                    and not managed_exists
                ):
                    return self._result(
                        manifest,
                        operation_id,
                        "uninstall",
                        True,
                        "already_uninstalled",
                        "Wright runtime code is already uninstalled; user data is preserved.",
                        started_at,
                        details={"preserved_data": str(self.layout.data)},
                        persist=False,
                    )
                origin_state = manifest.lifecycle_state
                if manifest.process is not None:
                    runtime = manifest.runtimes.get(manifest.process.runtime_id)
                    if runtime is None:
                        manifest.lifecycle_state = LifecycleState.RECOVERY_REQUIRED
                        return self._result(
                            manifest,
                            operation_id,
                            "uninstall",
                            False,
                            ResultCode.PROCESS_IDENTITY_FAILED,
                            "Uninstall refused because process ownership is ambiguous.",
                            started_at,
                            remediation=[
                                "Run /wright doctor; no process or data was deleted."
                            ],
                        )
                    self.process_manager.stop(
                        manifest.process,
                        Path(runtime.environment_path),
                        expected_runtime_id=runtime.runtime_id,
                    )
                    manifest.process = None
                    manifest.lifecycle_state = LifecycleState.STOPPED
                if manifest.lifecycle_state is LifecycleState.NOT_INSTALLED:
                    manifest.lifecycle_state = LifecycleState.UNINSTALLING
                else:
                    manifest.transition(LifecycleState.UNINSTALLING)
                manifest.current_operation = OperationRecord(
                    operation_id=operation_id,
                    kind=OperationKind.UNINSTALL,
                    requested_by=requested_by or self.manager_id,
                    started_at=started_at,
                    from_state=origin_state,
                    target_state=LifecycleState.NOT_INSTALLED,
                    checkpoint="process_stopped",
                )
                self.store.save(manifest)
                for directory in (self.layout.runtimes, self.layout.cache):
                    if directory.is_symlink():
                        raise ValueError("managed_directory_symlink_refused")
                    if directory.exists():
                        self.layout.require_owned(directory)
                        shutil.rmtree(directory)
                manifest.runtimes.clear()
                manifest.active_runtime_id = None
                manifest.predecessor_runtime_id = None
                manifest.desired_runtime_version = None
                manifest.process = None
                manifest.current_operation = None
                manifest.lifecycle_state = LifecycleState.NOT_INSTALLED
                return self._result(
                    manifest,
                    operation_id,
                    "uninstall",
                    True,
                    ResultCode.OK,
                    "Wright runtime code was removed and user data was preserved.",
                    started_at,
                    details={"preserved_data": str(self.layout.data)},
                    remediation=[
                        "Reinstall through a supported manager adapter to reopen preserved data."
                    ],
                )
        except LifecycleBusy as exc:
            manifest = self.store.load()
            return self._result(
                manifest,
                operation_id,
                "uninstall",
                False,
                ResultCode.LIFECYCLE_BUSY,
                "Another Wright lifecycle operation is in progress.",
                started_at,
                details={"active_operation_id": exc.operation_id},
                persist=False,
            )
        except Exception as exc:
            manifest = self.store.load()
            manifest.lifecycle_state = LifecycleState.RECOVERY_REQUIRED
            manifest.current_operation = None
            return self._result(
                manifest,
                operation_id,
                "uninstall",
                False,
                ResultCode.RECOVERY_REQUIRED,
                "Wright could not finish uninstall safely; user data was not purged.",
                started_at,
                details={"error_type": type(exc).__name__},
                remediation=["Run /wright doctor and retry uninstall."],
            )

    def purge(
        self,
        confirmation: str | None = None,
        *,
        requested_by: str | None = None,
    ) -> LifecycleResult:
        operation_id = str(uuid4())
        started_at = utc_now()
        manifest = self.store.load()
        if not self.store.manifest_path.exists():
            # Persist the installation identity so the disclosed purge scope and
            # confirmation code remain stable across the two deliberate calls.
            self.store.save(manifest)
        manager = PurgeManager(self.layout)
        try:
            plan = manager.plan(manifest.installation_id)
        except Exception as exc:
            return self._result(
                manifest,
                operation_id,
                "purge",
                False,
                ResultCode.UNSAFE_PATH,
                "Wright refused an unsafe purge scope.",
                started_at,
                details={"error_type": type(exc).__name__},
                remediation=[
                    "Remove symlinks or ambiguous paths and run /wright doctor."
                ],
                persist=False,
            )
        if confirmation is None:
            return self._result(
                manifest,
                operation_id,
                "purge",
                False,
                "purge_confirmation_required",
                "Purge will permanently delete the disclosed Wright-owned data path.",
                started_at,
                details={
                    "confirmation_code": plan.confirmation_code,
                    "targets": [str(path) for path in plan.targets],
                },
                remediation=[
                    f"Run /wright purge {plan.confirmation_code} to confirm this exact scope."
                ],
                persist=False,
            )
        if confirmation != plan.confirmation_code:
            return self._result(
                manifest,
                operation_id,
                "purge",
                False,
                ResultCode.INVALID_CONFIRMATION,
                "The purge confirmation does not match the current path scope.",
                started_at,
                persist=False,
            )
        try:
            with self.store.lock(operation_id=operation_id, timeout=self.lock_timeout):
                manifest = self.store.load()
                if manifest.process is not None:
                    runtime = manifest.runtimes.get(manifest.process.runtime_id)
                    if runtime is None:
                        raise RuntimeError("purge_process_identity_missing")
                    self.process_manager.stop(
                        manifest.process,
                        Path(runtime.environment_path),
                        expected_runtime_id=runtime.runtime_id,
                    )
                    manifest.process = None
                    manifest.lifecycle_state = LifecycleState.STOPPED
                for directory in (self.layout.runtimes, self.layout.cache):
                    if directory.is_symlink():
                        raise RuntimeError("managed_directory_symlink_refused")
                    if directory.exists():
                        self.layout.require_owned(directory)
                        shutil.rmtree(directory)
                if manifest.lifecycle_state is LifecycleState.NOT_INSTALLED:
                    manifest.lifecycle_state = LifecycleState.PURGING
                else:
                    manifest.transition(LifecycleState.PURGING)
                manifest.current_operation = OperationRecord(
                    operation_id=operation_id,
                    kind=OperationKind.PURGE,
                    requested_by=requested_by or self.manager_id,
                    started_at=started_at,
                    from_state=LifecycleState.STOPPED,
                    target_state=LifecycleState.NOT_INSTALLED,
                    checkpoint="scope_confirmed",
                )
                self.store.save(manifest)
                removed = manager.execute(plan, confirmation)
                manifest.runtimes.clear()
                manifest.active_runtime_id = None
                manifest.predecessor_runtime_id = None
                manifest.process = None
                manifest.current_operation = None
                manifest.lifecycle_state = LifecycleState.NOT_INSTALLED
                return self._result(
                    manifest,
                    operation_id,
                    "purge",
                    True,
                    ResultCode.OK,
                    "Confirmed Wright-owned data was purged.",
                    started_at,
                    details={"removed_categories": list(removed)},
                )
        except Exception as exc:
            manifest = self.store.load()
            manifest.lifecycle_state = LifecycleState.RECOVERY_REQUIRED
            manifest.current_operation = None
            return self._result(
                manifest,
                operation_id,
                "purge",
                False,
                ResultCode.RECOVERY_REQUIRED,
                "Purge did not complete; unrelated files were not targeted.",
                started_at,
                details={"error_type": type(exc).__name__},
                remediation=[
                    "Review the deletion evidence and retry only after resolving the failure."
                ],
            )
        except Exception as exc:
            manifest = self.store.load()
            manifest.lifecycle_state = LifecycleState.RECOVERY_REQUIRED
            manifest.current_operation = None
            return self._result(
                manifest,
                operation_id,
                "rollback",
                False,
                ResultCode.RECOVERY_REQUIRED,
                "Rollback could not complete safely.",
                started_at,
                details={"error_type": type(exc).__name__},
                remediation=[
                    "Run /wright doctor; no data backup was restored implicitly."
                ],
            )

    def _runtime_paths_contained(self) -> bool:
        try:
            manifest = self.store.load()
            return all(
                Path(runtime.environment_path)
                .resolve(strict=False)
                .is_relative_to(self.layout.runtimes.resolve(strict=False))
                for runtime in manifest.runtimes.values()
            )
        except Exception:
            return False

    def _data_permissions_ready(self) -> bool:
        try:
            self.layout.data.mkdir(parents=True, exist_ok=True)
            return os.access(self.layout.data, os.R_OK | os.W_OK)
        except OSError:
            return False

    def _install_locked(
        self,
        manifest: Manifest,
        artifact: RuntimeArtifact,
        operation_id: str,
        requested_by: str,
    ) -> Manifest:
        from_state = manifest.lifecycle_state
        if from_state not in {
            LifecycleState.NOT_INSTALLED,
            LifecycleState.FAILED,
            LifecycleState.RECOVERY_REQUIRED,
        }:
            raise RuntimeError("install_state_invalid")
        manifest.transition(LifecycleState.INSTALLING)
        runtime_id = _runtime_id(artifact)
        manifest.desired_runtime_version = artifact.version
        manifest.current_operation = OperationRecord(
            operation_id=operation_id,
            kind=OperationKind.INSTALL,
            requested_by=requested_by,
            started_at=utc_now(),
            from_state=from_state,
            target_state=LifecycleState.STOPPED,
            candidate_runtime_id=runtime_id,
        )
        self.store.save(manifest)
        environment = self.installer.install(artifact, runtime_id)
        manifest.runtimes[runtime_id] = self._installation_from_artifact(
            artifact, runtime_id, environment
        )
        manifest.active_runtime_id = runtime_id
        manifest.transition(LifecycleState.STOPPED)
        manifest.current_operation = None
        self.store.save(manifest)
        return manifest

    def _installation_from_artifact(
        self, artifact: RuntimeArtifact, runtime_id: str, environment: Path
    ) -> RuntimeInstallation:
        return RuntimeInstallation(
            runtime_id=runtime_id,
            version=artifact.version,
            distribution="wright-engineering",
            artifact_filename=artifact.filename,
            artifact_sha256=artifact.sha256,
            source_channel=artifact.channel,
            environment_path=str(environment.resolve()),
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            platform_tag=current_platform_tag(),
            runtime_specifier=self.compatibility.runtime_specifier,
            manager_protocols={
                manager_id: protocol.adapter_protocol
                for manager_id, protocol in self.compatibility.manager_protocols.items()
            },
            data_schema_min=self.compatibility.data_schema_min,
            data_schema_max=self.compatibility.data_schema_max,
            installed_at=utc_now(),
            verified_at=utc_now(),
            status=RuntimeStatus.VERIFIED,
        )

    def _launch_runtime(
        self, runtime: RuntimeInstallation, operation_id: str
    ) -> ProcessIdentity | None:
        environment = Path(runtime.environment_path)
        python = RuntimeInstaller.environment_python(environment)
        log_path = self.layout.logs / f"runtime-{operation_id}.log"
        self.layout.logs.mkdir(parents=True, exist_ok=True)
        with log_path.open("ab") as log_handle:
            _, identity, _ = self.process_manager.launch(
                [
                    str(python),
                    "-m",
                    "wright_engineering.cli",
                    "runtime",
                    "serve",
                    "--host",
                    self.host,
                    "--port",
                    str(self.port),
                    "--data-root",
                    str(self.layout.data),
                ],
                runtime_id=runtime.runtime_id,
                runtime_path=environment,
                operation_id=operation_id,
                host=self.host,
                port=self.port,
                environment=self._runtime_environment(),
                log_handle=log_handle,
            )
        if not self.health_probe(identity):
            try:
                self.process_manager.stop(
                    identity,
                    environment,
                    expected_runtime_id=runtime.runtime_id,
                )
            except Exception:
                pass
            return None
        identity.health_verified_at = utc_now()
        return identity

    def _result(
        self,
        manifest: Manifest,
        operation_id: str,
        command: str,
        ok: bool,
        code: str | ResultCode,
        summary: str,
        started_at: str,
        *,
        details: dict[str, object] | None = None,
        remediation: list[str] | None = None,
        persist: bool = True,
    ) -> LifecycleResult:
        result = LifecycleResult(
            operation_id=operation_id,
            command=command,
            ok=ok,
            state=manifest.lifecycle_state,
            code=code.value if isinstance(code, ResultCode) else code,
            summary=summary,
            details=bounded_details(details or {}, allowed=set(details or {})),
            remediation=remediation or [],
            started_at=started_at,
            finished_at=utc_now(),
        )
        if persist:
            manifest.last_result = result
            self.store.save(manifest)
        self.logger.emit(
            "lifecycle_result",
            operation_id=operation_id,
            command=command,
            ok=ok,
            state=manifest.lifecycle_state.value,
            code=result.code,
        )
        return result

    def _healthy_details(self, manifest: Manifest) -> dict[str, object]:
        runtime = manifest.runtimes[manifest.active_runtime_id]  # type: ignore[index]
        return {
            "runtime_version": runtime.version,
            "runtime_id": runtime.runtime_id,
            "ui_url": f"http://{self.host}:{self.port}/",
            "data_root": manifest.data_root,
            "pid": manifest.process.pid if manifest.process else None,
        }

    @staticmethod
    def _distribution_version() -> str:
        try:
            return distribution_version("wright-engineering")
        except Exception:
            return "unknown"

    def _runtime_environment(self) -> dict[str, str]:
        api_token = ensure_control_plane_token(self.layout)
        values = {
            "WRIGHT_HOME": str(self.layout.wright_home),
            "WRIGHT_SECRETS_PATH": str(self.layout.data / "credentials.json"),
            "WRIGHT_SECRETS_DIR": str(self.layout.data / "secrets.d"),
            "WRIGHT_AUTH_MODE": "enforced",
            "WRIGHT_API_TOKEN": api_token,
            "WRIGHT_MANAGER_ID": self.manager_id,
            "WRIGHT_MANAGER_PROTOCOL": self.adapter_protocol,
        }
        if self.manager_version:
            values["WRIGHT_MANAGER_VERSION"] = self.manager_version
        return values

    @staticmethod
    def _probe_health(identity: ProcessIdentity) -> bool:
        url = f"http://{identity.host}:{identity.port}/api/runtime/identity"
        deadline = time.monotonic() + 30.0
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(url, timeout=2.0) as response:
                    payload = json.load(response)
                return bool(
                    payload.get("product") == "wright"
                    and payload.get("runtime_id") == identity.runtime_id
                    and payload.get("instance_id") == identity.instance_id
                    and payload.get("challenge_hash") == identity.challenge_hash
                )
            except (OSError, urllib.error.URLError, ValueError, json.JSONDecodeError):
                time.sleep(0.25)
        return False
