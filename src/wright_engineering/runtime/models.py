"""Dependency-free lifecycle state and result models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, ClassVar
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class LifecycleState(StrEnum):
    NOT_INSTALLED = "not_installed"
    INSTALLING = "installing"
    STOPPED = "stopped"
    STARTING = "starting"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    STOPPING = "stopping"
    UPDATING = "updating"
    ROLLING_BACK = "rolling_back"
    UNINSTALLING = "uninstalling"
    PURGING = "purging"
    FAILED = "failed"
    RECOVERY_REQUIRED = "recovery_required"


class OperationKind(StrEnum):
    INSTALL = "install"
    START = "start"
    STOP = "stop"
    UPDATE = "update"
    ROLLBACK = "rollback"
    UNINSTALL = "uninstall"
    PURGE = "purge"


class RuntimeStatus(StrEnum):
    STAGED = "staged"
    VERIFIED = "verified"
    ACTIVE = "active"
    PREDECESSOR = "predecessor"
    FAILED = "failed"
    REMOVABLE = "removable"


class SourceChannel(StrEnum):
    LOCAL_CANDIDATE = "local_candidate"
    TEST = "test"
    STABLE = "stable"


class ResultCode(StrEnum):
    OK = "ok"
    ALREADY_RUNNING = "already_running"
    ALREADY_STOPPED = "already_stopped"
    LIFECYCLE_BUSY = "lifecycle_busy"
    COMPATIBILITY_FAILED = "compatibility_failed"
    ARTIFACT_FAILED = "artifact_failed"
    PROCESS_IDENTITY_FAILED = "process_identity_failed"
    HEALTH_FAILED = "health_failed"
    RECOVERY_REQUIRED = "recovery_required"
    INVALID_CONFIRMATION = "invalid_confirmation"
    UNSAFE_PATH = "unsafe_path"


@dataclass(slots=True)
class RuntimeInstallation:
    runtime_id: str
    version: str
    distribution: str
    artifact_filename: str
    artifact_sha256: str
    source_channel: SourceChannel
    environment_path: str
    python_version: str
    platform_tag: str
    plugin_compatibility: str
    hermes_compatibility: str
    data_schema_min: int
    data_schema_max: int
    installed_at: str
    verified_at: str | None = None
    status: RuntimeStatus = RuntimeStatus.STAGED
    failure_code: str | None = None

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> RuntimeInstallation:
        copy = dict(value)
        copy["source_channel"] = SourceChannel(copy["source_channel"])
        copy["status"] = RuntimeStatus(copy["status"])
        return cls(**copy)

    def validate(self) -> None:
        if not self.runtime_id or "/" in self.runtime_id or "\\" in self.runtime_id:
            raise ValueError("runtime_id_invalid")
        if self.distribution != "wright-engineering":
            raise ValueError("runtime_distribution_invalid")
        if len(self.artifact_sha256) != 64 or any(
            char not in "0123456789abcdef" for char in self.artifact_sha256.lower()
        ):
            raise ValueError("runtime_artifact_hash_invalid")
        if not Path(self.environment_path).is_absolute():
            raise ValueError("runtime_environment_not_absolute")
        if self.data_schema_min < 0 or self.data_schema_max < self.data_schema_min:
            raise ValueError("runtime_schema_range_invalid")


@dataclass(slots=True)
class OperationRecord:
    operation_id: str
    kind: OperationKind
    requested_by: str
    started_at: str
    from_state: LifecycleState
    target_state: LifecycleState
    candidate_runtime_id: str | None = None
    checkpoint: str = "intent_recorded"
    backup_manifest: str | None = None
    recovery_action: str | None = None

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> OperationRecord:
        copy = dict(value)
        copy["kind"] = OperationKind(copy["kind"])
        copy["from_state"] = LifecycleState(copy["from_state"])
        copy["target_state"] = LifecycleState(copy["target_state"])
        return cls(**copy)


@dataclass(slots=True)
class ProcessIdentity:
    pid: int
    started_at: str
    runtime_id: str
    executable_path: str
    host: str
    port: int
    instance_id: str
    challenge_hash: str
    operation_id: str
    health_verified_at: str | None = None

    def validate(self) -> None:
        if self.pid <= 0:
            raise ValueError("process_pid_invalid")
        if not Path(self.executable_path).is_absolute():
            raise ValueError("process_executable_not_absolute")
        if self.host not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("process_host_not_loopback")
        if not 1 <= self.port <= 65535:
            raise ValueError("process_port_invalid")
        if len(self.challenge_hash) != 64:
            raise ValueError("process_challenge_hash_invalid")


@dataclass(slots=True)
class LifecycleResult:
    operation_id: str
    command: str
    ok: bool
    state: LifecycleState
    code: str
    summary: str
    details: dict[str, Any] = field(default_factory=dict)
    remediation: list[str] = field(default_factory=list)
    started_at: str = field(default_factory=utc_now)
    finished_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return _to_primitive(asdict(self))


@dataclass(slots=True)
class Manifest:
    SCHEMA_VERSION: ClassVar[int] = 1

    schema_version: int
    installation_id: str
    hermes_home: str
    data_root: str
    active_runtime_id: str | None
    predecessor_runtime_id: str | None
    desired_runtime_version: str | None
    lifecycle_state: LifecycleState
    current_operation: OperationRecord | None
    process: ProcessIdentity | None
    runtimes: dict[str, RuntimeInstallation]
    last_result: LifecycleResult | None
    created_at: str
    updated_at: str

    _TRANSITIONS: ClassVar[dict[LifecycleState, set[LifecycleState]]] = {
        LifecycleState.NOT_INSTALLED: {
            LifecycleState.INSTALLING,
            LifecycleState.PURGING,
            LifecycleState.RECOVERY_REQUIRED,
        },
        LifecycleState.INSTALLING: {
            LifecycleState.STOPPED,
            LifecycleState.FAILED,
            LifecycleState.RECOVERY_REQUIRED,
        },
        LifecycleState.STOPPED: {
            LifecycleState.STARTING,
            LifecycleState.UPDATING,
            LifecycleState.ROLLING_BACK,
            LifecycleState.UNINSTALLING,
            LifecycleState.PURGING,
            LifecycleState.FAILED,
        },
        LifecycleState.STARTING: {
            LifecycleState.HEALTHY,
            LifecycleState.DEGRADED,
            LifecycleState.FAILED,
            LifecycleState.RECOVERY_REQUIRED,
        },
        LifecycleState.HEALTHY: {
            LifecycleState.STOPPING,
            LifecycleState.UPDATING,
            LifecycleState.ROLLING_BACK,
            LifecycleState.UNINSTALLING,
            LifecycleState.DEGRADED,
            LifecycleState.FAILED,
            LifecycleState.RECOVERY_REQUIRED,
        },
        LifecycleState.DEGRADED: {
            LifecycleState.STOPPING,
            LifecycleState.UPDATING,
            LifecycleState.ROLLING_BACK,
            LifecycleState.UNINSTALLING,
            LifecycleState.HEALTHY,
            LifecycleState.FAILED,
            LifecycleState.RECOVERY_REQUIRED,
        },
        LifecycleState.STOPPING: {
            LifecycleState.STOPPED,
            LifecycleState.RECOVERY_REQUIRED,
        },
        LifecycleState.UPDATING: {
            LifecycleState.STOPPED,
            LifecycleState.HEALTHY,
            LifecycleState.FAILED,
            LifecycleState.RECOVERY_REQUIRED,
        },
        LifecycleState.ROLLING_BACK: {
            LifecycleState.STOPPED,
            LifecycleState.HEALTHY,
            LifecycleState.FAILED,
            LifecycleState.RECOVERY_REQUIRED,
        },
        LifecycleState.UNINSTALLING: {
            LifecycleState.NOT_INSTALLED,
            LifecycleState.RECOVERY_REQUIRED,
        },
        LifecycleState.PURGING: {
            LifecycleState.NOT_INSTALLED,
            LifecycleState.RECOVERY_REQUIRED,
        },
        LifecycleState.FAILED: {
            LifecycleState.INSTALLING,
            LifecycleState.ROLLING_BACK,
            LifecycleState.STOPPING,
            LifecycleState.UNINSTALLING,
            LifecycleState.PURGING,
            LifecycleState.RECOVERY_REQUIRED,
        },
        LifecycleState.RECOVERY_REQUIRED: {
            LifecycleState.INSTALLING,
            LifecycleState.ROLLING_BACK,
            LifecycleState.STOPPING,
            LifecycleState.UNINSTALLING,
            LifecycleState.PURGING,
            LifecycleState.FAILED,
        },
    }

    @classmethod
    def create(cls, hermes_home: Path, data_root: Path) -> Manifest:
        now = utc_now()
        return cls(
            schema_version=cls.SCHEMA_VERSION,
            installation_id=str(uuid4()),
            hermes_home=str(hermes_home.resolve()),
            data_root=str(data_root.resolve()),
            active_runtime_id=None,
            predecessor_runtime_id=None,
            desired_runtime_version=None,
            lifecycle_state=LifecycleState.NOT_INSTALLED,
            current_operation=None,
            process=None,
            runtimes={},
            last_result=None,
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Manifest:
        try:
            copy = dict(value)
            copy["lifecycle_state"] = LifecycleState(copy["lifecycle_state"])
            operation = copy.get("current_operation")
            copy["current_operation"] = (
                OperationRecord.from_dict(operation) if operation else None
            )
            process = copy.get("process")
            copy["process"] = ProcessIdentity(**process) if process else None
            copy["runtimes"] = {
                key: RuntimeInstallation.from_dict(runtime)
                for key, runtime in copy.get("runtimes", {}).items()
            }
            result = copy.get("last_result")
            if result:
                result = dict(result)
                result["state"] = LifecycleState(result["state"])
                copy["last_result"] = LifecycleResult(**result)
            return cls(**copy)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("manifest_schema_invalid") from exc

    def to_dict(self) -> dict[str, Any]:
        return _to_primitive(asdict(self))

    def transition(self, target: LifecycleState) -> None:
        if target == self.lifecycle_state:
            return
        if target not in self._TRANSITIONS[self.lifecycle_state]:
            raise ValueError(
                f"invalid_transition:{self.lifecycle_state.value}->{target.value}"
            )
        self.lifecycle_state = target
        self.updated_at = utc_now()

    def validate(self) -> None:
        if self.schema_version != self.SCHEMA_VERSION:
            raise ValueError("manifest_schema_version_unsupported")
        if (
            not Path(self.hermes_home).is_absolute()
            or not Path(self.data_root).is_absolute()
        ):
            raise ValueError("manifest_path_not_absolute")
        for key, runtime in self.runtimes.items():
            runtime.validate()
            if key != runtime.runtime_id:
                raise ValueError("runtime_key_mismatch")
        if self.active_runtime_id:
            active = self.runtimes.get(self.active_runtime_id)
            if active is None:
                raise ValueError("active_runtime_missing")
            if active.status not in {RuntimeStatus.VERIFIED, RuntimeStatus.ACTIVE}:
                raise ValueError("active_runtime_unverified")
        if (
            self.predecessor_runtime_id
            and self.predecessor_runtime_id not in self.runtimes
        ):
            raise ValueError("predecessor_runtime_missing")
        if (
            sum(
                runtime.status is RuntimeStatus.ACTIVE
                for runtime in self.runtimes.values()
            )
            > 1
        ):
            raise ValueError("multiple_active_runtimes")
        if (
            sum(
                runtime.status is RuntimeStatus.PREDECESSOR
                for runtime in self.runtimes.values()
            )
            > 1
        ):
            raise ValueError("multiple_predecessor_runtimes")
        if self.process:
            self.process.validate()
            if self.process.runtime_id != self.active_runtime_id:
                raise ValueError("process_runtime_not_active")


def _to_primitive(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _to_primitive(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_primitive(item) for item in value]
    return value
