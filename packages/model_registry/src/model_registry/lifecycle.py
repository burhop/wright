"""Durable verified engineering-model acquisition and activation state machine."""

from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path
import shutil
from typing import Any, Callable, Mapping, Protocol

from .models import ArtifactDeclaration, ModelPackage, canonical_digest
from .http_source import HttpSourceError
from .offline_source import OfflinePackageError, inspect_offline_package
from .planning import ModelEffectPlan


class RepositoryPort(Protocol):
    def save_plan(self, **values) -> None: ...
    def create_operation(self, **values) -> None: ...
    def get_operation(self, operation_id: str) -> dict[str, Any] | None: ...
    def transition_operation(self, operation_id: str, **values) -> bool: ...
    def record_content_object(self, **values) -> None: ...
    def save_installation(self, **values) -> None: ...


class StorePort(Protocol):
    def has_verified(self, content_digest: str) -> bool: ...
    def stage_bytes(self, **values): ...
    def promote(self, staged, **values): ...
    def activate(self, **values) -> dict[str, object]: ...
    def cleanup_staging(self, operation_id: str, **values): ...


class DiskPort(Protocol):
    def reserve(self, operation_id: str, bytes: int): ...


class _DiskReservation:
    def __init__(self, owner: "DiskReservationManager", operation_id: str) -> None:
        self.owner = owner
        self.operation_id = operation_id
        self.released = False

    def release(self) -> None:
        if not self.released:
            self.owner.release(self.operation_id)
            self.released = True


class DiskReservationManager:
    """Process-local reservation backed by a fresh filesystem-free-space check."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self._reservations: dict[str, int] = {}
        self._lock = threading.Lock()

    def reserve(self, operation_id: str, bytes: int) -> _DiskReservation:
        if bytes < 0:
            raise ValueError("Disk reservation is invalid")
        with self._lock:
            existing = self._reservations.get(operation_id)
            if existing is not None:
                if existing != bytes:
                    raise ValueError("Disk reservation identity changed")
                return _DiskReservation(self, operation_id)
            available = shutil.disk_usage(self.root).free - sum(
                self._reservations.values()
            )
            if bytes > available:
                raise ValueError("Insufficient disk capacity")
            self._reservations[operation_id] = bytes
        return _DiskReservation(self, operation_id)

    def release(self, operation_id: str) -> None:
        with self._lock:
            self._reservations.pop(operation_id, None)


class CancellationSignal:
    def __init__(self) -> None:
        self._requested = threading.Event()

    def request(self) -> None:
        self._requested.set()

    def requested(self) -> bool:
        return self._requested.is_set()


class MappingArtifactSource:
    """Deterministic injected source used by generated and inspected packages."""

    def __init__(self, artifacts: Mapping[str, bytes]) -> None:
        self._artifacts = dict(artifacts)
        self.calls = 0

    def fetch_artifact(
        self,
        package: ModelPackage,
        artifact: ArtifactDeclaration,
        *,
        maximum_bytes: int,
        is_cancelled: Callable[[], bool],
    ) -> bytes:
        self.calls += 1
        if is_cancelled():
            raise LifecycleFailure("cancelled", "Installation was cancelled")
        try:
            value = self._artifacts[artifact.path]
        except KeyError as error:
            raise LifecycleFailure(
                "source_unavailable", "Declared artifact is unavailable"
            ) from error
        if len(value) > maximum_bytes:
            raise LifecycleFailure(
                "size_exceeded", "Artifact exceeds its confirmed ceiling"
            )
        return value


class LifecycleFailure(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


_FAILURE_RECOVERY = {
    "cancelled": "Retry from a fresh confirmed plan when installation is wanted.",
    "digest_mismatch": "Discard operation staging and retry from a fresh plan.",
    "insufficient_disk": "Free space, then create and review a fresh plan.",
    "size_exceeded": "Review the declared package bounds and create a fresh plan.",
    "source_unavailable": "Restore the exact source or use a verified offline package.",
    "internal_error": "Inspect the bounded operation evidence and retry safely.",
}


class ModelInstallLifecycle:
    def __init__(
        self,
        *,
        repository: RepositoryPort,
        store: StorePort,
        disk: DiskPort,
        clock: Callable[[], datetime],
    ) -> None:
        self.repository = repository
        self.store = store
        self.disk = disk
        self.clock = clock
        self._locks: dict[str, threading.Lock] = {}
        self._guard = threading.Lock()

    def _lock(self, identity: str) -> threading.Lock:
        with self._guard:
            return self._locks.setdefault(identity, threading.Lock())

    @staticmethod
    def _progress(
        *,
        completed_items: int,
        total_items: int,
        completed_bytes: int,
        maximum_bytes: int,
        message: str,
    ) -> dict[str, Any]:
        return {
            "completed_items": completed_items,
            "total_items": total_items,
            "completed_bytes": completed_bytes,
            "maximum_bytes": maximum_bytes,
            "message": message,
        }

    def install(
        self,
        plan: ModelEffectPlan,
        package: ModelPackage,
        source,
        *,
        cancellation: CancellationSignal | None = None,
        trace_id: str = "no-active-span",
    ) -> dict[str, Any]:
        if plan.state != "confirmed" or plan.manifest_digest != package.digest:
            raise LifecycleFailure(
                "plan_invalidated", "A confirmed matching plan is required"
            )
        variant = package.variant(plan.variant_id)
        operation_id = f"operation-{plan.plan_digest[:24]}"
        installation_id = f"installation-{package.model_id}-r{package.package_revision}-{variant.variant_id}"
        with self._lock(installation_id):
            existing = self.repository.get_operation(operation_id)
            if existing is not None:
                return existing
            now = self.clock()
            stored_plan = getattr(self.repository, "get_plan", lambda _plan_id: None)(
                plan.plan_id
            )
            if stored_plan is None:
                self.repository.save_plan(
                    plan_id=plan.plan_id,
                    principal_id=plan.principal_id,
                    plan_digest=plan.plan_digest,
                    state="confirmed",
                    plan=plan.model_dump(mode="json", exclude_none=True),
                    created_at=plan.created_at,
                    expires_at=plan.expires_at,
                    trace_id=trace_id,
                )
            elif stored_plan["state"] != "confirmed":
                raise LifecycleFailure(
                    "plan_invalidated", "The durable plan is not confirmed"
                )
            self.repository.create_operation(
                operation_id=operation_id,
                plan_id=plan.plan_id,
                plan_digest=plan.plan_digest,
                kind="install" if plan.operation_kind == "install" else "import",
                trace_id=trace_id,
                created_at=now,
            )
            total_bytes = sum(item.size for item in variant.artifacts)
            total_items = len(variant.artifacts)
            signal = cancellation or CancellationSignal()
            reservation = None
            completed_bytes = 0
            completed_items = 0
            try:
                if signal.requested():
                    raise LifecycleFailure("cancelled", "Installation was cancelled")
                try:
                    reservation = self.disk.reserve(operation_id, total_bytes)
                except ValueError as error:
                    raise LifecycleFailure(
                        "insufficient_disk", "Disk reservation failed"
                    ) from error
                self.repository.transition_operation(
                    operation_id,
                    expected_state="prepared",
                    state="running",
                    phase="acquiring",
                    progress=self._progress(
                        completed_items=0,
                        total_items=total_items,
                        completed_bytes=0,
                        maximum_bytes=total_bytes,
                        message="Acquiring exact declared artifacts.",
                    ),
                    updated_at=self.clock(),
                    trace_id=trace_id,
                )
                artifacts: dict[str, str] = {}
                for declaration in variant.artifacts:
                    if signal.requested():
                        raise LifecycleFailure(
                            "cancelled", "Installation was cancelled"
                        )
                    if not self.store.has_verified(declaration.sha256):
                        content = source.fetch_artifact(
                            package,
                            declaration,
                            maximum_bytes=declaration.size,
                            is_cancelled=signal.requested,
                        )
                        try:
                            staged = self.store.stage_bytes(
                                operation_id=operation_id,
                                expected_digest=declaration.sha256,
                                content=content,
                                maximum_bytes=declaration.size,
                                trace_id=trace_id,
                            )
                            verified = self.store.promote(staged, trace_id=trace_id)
                        except ValueError as error:
                            message = str(error).lower()
                            code = (
                                "digest_mismatch"
                                if "digest" in message
                                else "size_exceeded"
                            )
                            raise LifecycleFailure(
                                code, "Artifact verification failed"
                            ) from error
                        self.repository.record_content_object(
                            content_digest=verified.content_digest,
                            size=verified.size,
                            state="verified",
                            storage_key=(
                                f"sha256/{verified.content_digest[:2]}/"
                                f"{verified.content_digest}"
                            ),
                            verification={
                                "algorithm": "sha256",
                                "size": verified.size,
                            },
                            observed_at=self.clock(),
                        )
                    artifacts[declaration.path] = declaration.sha256
                    completed_items += 1
                    completed_bytes += declaration.size
                    self.repository.transition_operation(
                        operation_id,
                        expected_state="running",
                        state="running",
                        phase="verifying",
                        progress=self._progress(
                            completed_items=completed_items,
                            total_items=total_items,
                            completed_bytes=completed_bytes,
                            maximum_bytes=total_bytes,
                            message=(
                                f"Verified {completed_items} of {total_items} artifacts."
                            ),
                        ),
                        updated_at=self.clock(),
                        trace_id=trace_id,
                    )
                self.repository.transition_operation(
                    operation_id,
                    expected_state="running",
                    state="activating",
                    phase="activating",
                    progress=self._progress(
                        completed_items=completed_items,
                        total_items=total_items,
                        completed_bytes=completed_bytes,
                        maximum_bytes=total_bytes,
                        message="Atomically activating verified content.",
                    ),
                    updated_at=self.clock(),
                    trace_id=trace_id,
                )
                activation = self.store.activate(
                    installation_id=installation_id,
                    manifest_digest=package.digest,
                    artifacts=artifacts,
                    trace_id=trace_id,
                )
                installation_digest = canonical_digest(activation)
                self.repository.save_installation(
                    installation_id=installation_id,
                    model_id=package.model_id,
                    package_revision=package.package_revision,
                    variant_id=variant.variant_id,
                    manifest_digest=package.digest,
                    installation_digest=installation_digest,
                    runtime_adapter_id=variant.runtime.adapter_id,
                    runtime_adapter_version=variant.runtime.version_specifier,
                    state="installed",
                    active=True,
                    installed_at=self.clock(),
                )
                cleanup = self.store.cleanup_staging(operation_id, trace_id=trace_id)
                self.repository.transition_operation(
                    operation_id,
                    expected_state="activating",
                    state="succeeded",
                    phase="complete",
                    progress=self._progress(
                        completed_items=total_items,
                        total_items=total_items,
                        completed_bytes=total_bytes,
                        maximum_bytes=total_bytes,
                        message=(
                            "Verified model package installed; standard tests remain required."
                        ),
                    ),
                    result={
                        "installation_id": installation_id,
                        "installation_digest": installation_digest,
                        "readiness": "installed_unverified",
                    },
                    cleanup_state=cleanup.state,
                    updated_at=self.clock(),
                    trace_id=trace_id,
                )
            except (LifecycleFailure, OfflinePackageError, HttpSourceError) as error:
                code = getattr(error, "code", "internal_error")
                cleanup = self.store.cleanup_staging(operation_id, trace_id=trace_id)
                current = self.repository.get_operation(operation_id) or {
                    "state": "prepared"
                }
                terminal = "cancelled" if code == "cancelled" else "failed"
                self.repository.transition_operation(
                    operation_id,
                    expected_state=current["state"],
                    state=terminal,
                    phase="cancelled" if terminal == "cancelled" else "failed",
                    progress=self._progress(
                        completed_items=completed_items,
                        total_items=total_items,
                        completed_bytes=completed_bytes,
                        maximum_bytes=total_bytes,
                        message=(
                            "Installation cancelled safely."
                            if terminal == "cancelled"
                            else "Installation failed safely."
                        ),
                    ),
                    failure={
                        "category": code,
                        "message": str(error),
                        "recovery": _FAILURE_RECOVERY.get(
                            code, _FAILURE_RECOVERY["internal_error"]
                        ),
                    },
                    cleanup_state=cleanup.state,
                    cancellation_requested_at=(
                        self.clock() if terminal == "cancelled" else None
                    ),
                    updated_at=self.clock(),
                    trace_id=trace_id,
                )
            finally:
                if reservation is not None:
                    reservation.release()
            result = self.repository.get_operation(operation_id)
            if result is None:
                raise RuntimeError("Model operation persistence failed")
            return result

    def import_archive(
        self,
        plan: ModelEffectPlan,
        archive_path: str | Path,
        *,
        cancellation: CancellationSignal | None = None,
        trace_id: str = "no-active-span",
    ) -> dict[str, Any]:
        inspected = inspect_offline_package(archive_path)
        return self.install(
            plan,
            inspected.package,
            MappingArtifactSource(inspected.artifacts),
            cancellation=cancellation,
            trace_id=trace_id,
        )


__all__ = [
    "CancellationSignal",
    "DiskReservationManager",
    "LifecycleFailure",
    "MappingArtifactSource",
    "ModelInstallLifecycle",
]
