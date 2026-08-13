"""Durable verified engineering-model acquisition and activation state machine."""

from __future__ import annotations

import threading
from dataclasses import dataclass
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
                runtime_adapter_version = (
                    variant.runtime.version_specifier.removeprefix("==")
                )
                installation_digest = canonical_digest(
                    {
                        "activation": activation,
                        "runtime_adapter_id": variant.runtime.adapter_id,
                        "runtime_adapter_version": runtime_adapter_version,
                    }
                )
                self.repository.save_installation(
                    installation_id=installation_id,
                    model_id=package.model_id,
                    package_revision=package.package_revision,
                    variant_id=variant.variant_id,
                    manifest_digest=package.digest,
                    installation_digest=installation_digest,
                    runtime_adapter_id=variant.runtime.adapter_id,
                    runtime_adapter_version=runtime_adapter_version,
                    state="installed",
                    active=True,
                    installed_at=self.clock(),
                )
                record_artifacts = getattr(
                    self.repository, "record_installation_artifacts", None
                )
                if callable(record_artifacts):
                    record_artifacts(
                        installation_id,
                        artifacts,
                        created_at=self.clock(),
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


_UPDATE_FACETS = (
    "license",
    "redistribution",
    "artifacts",
    "adapter",
    "schemas",
    "units",
    "coordinates",
    "resources",
    "vectors",
    "limitations",
)


@dataclass(frozen=True, slots=True)
class ModelRevisionDifference:
    current_manifest_digest: str
    candidate_manifest_digest: str
    changed_facets: tuple[str, ...]
    diff_digest: str
    requires_retest: bool
    requires_license_review: bool

    def projection(self) -> dict[str, Any]:
        return {
            "current_manifest_digest": self.current_manifest_digest,
            "candidate_manifest_digest": self.candidate_manifest_digest,
            "changed_facets": list(self.changed_facets),
            "diff_digest": self.diff_digest,
            "requires_retest": self.requires_retest,
            "requires_license_review": self.requires_license_review,
        }


def compare_model_revisions(
    current: ModelPackage,
    candidate: ModelPackage,
    *,
    current_variant_id: str | None = None,
    candidate_variant_id: str | None = None,
) -> ModelRevisionDifference:
    """Compare every semantic facet that can change engineering behavior or trust."""

    if current.model_id != candidate.model_id:
        raise LifecycleFailure("model_identity_changed", "Model identity changed")
    current_variant = current.variant(
        current_variant_id or current.variants[0].variant_id
    )
    candidate_variant = candidate.variant(
        candidate_variant_id or candidate.variants[0].variant_id
    )
    current_tasks = [item.model_dump(mode="json") for item in current.tasks]
    candidate_tasks = [item.model_dump(mode="json") for item in candidate.tasks]
    materials: dict[str, tuple[Any, Any]] = {
        "license": (
            current.license.model_dump(mode="json", exclude={"redistribution"}),
            candidate.license.model_dump(mode="json", exclude={"redistribution"}),
        ),
        "redistribution": (
            current.license.redistribution,
            candidate.license.redistribution,
        ),
        "artifacts": (
            [item.model_dump(mode="json") for item in current_variant.artifacts],
            [item.model_dump(mode="json") for item in candidate_variant.artifacts],
        ),
        "adapter": (
            current_variant.runtime.model_dump(mode="json"),
            candidate_variant.runtime.model_dump(mode="json"),
        ),
        "schemas": (
            [
                (item["task_id"], item["input_schema"], item["output_schema"])
                for item in current_tasks
            ],
            [
                (item["task_id"], item["input_schema"], item["output_schema"])
                for item in candidate_tasks
            ],
        ),
        "units": (
            [(item["task_id"], item.get("units", {})) for item in current_tasks],
            [(item["task_id"], item.get("units", {})) for item in candidate_tasks],
        ),
        "coordinates": (
            [
                (item["task_id"], item.get("coordinate_convention"))
                for item in current_tasks
            ],
            [
                (item["task_id"], item.get("coordinate_convention"))
                for item in candidate_tasks
            ],
        ),
        "resources": (
            current_variant.resources.model_dump(mode="json"),
            candidate_variant.resources.model_dump(mode="json"),
        ),
        "vectors": (
            [item.model_dump(mode="json") for item in current_variant.test_vectors],
            [item.model_dump(mode="json") for item in candidate_variant.test_vectors],
        ),
        "limitations": (
            [item.model_dump(mode="json") for item in current.limitations],
            [item.model_dump(mode="json") for item in candidate.limitations],
        ),
    }
    changed = tuple(
        name for name in _UPDATE_FACETS if materials[name][0] != materials[name][1]
    )
    material = {
        "current_manifest_digest": current.digest,
        "candidate_manifest_digest": candidate.digest,
        "changes": {
            name: {"before": materials[name][0], "after": materials[name][1]}
            for name in changed
        },
    }
    return ModelRevisionDifference(
        current.digest,
        candidate.digest,
        changed,
        canonical_digest(material),
        bool(changed),
        bool({"license", "redistribution"}.intersection(changed)),
    )


class ModelMaintenanceLifecycle:
    """Reference-safe update, rollback, removal, and recovery orchestration."""

    def __init__(self, *, repository, store, clock: Callable[[], datetime]) -> None:
        self.repository = repository
        self.store = store
        self.clock = clock
        self._guard = threading.Lock()

    def activate_successor(
        self, current_installation_id: str, successor_installation_id: str
    ) -> dict[str, Any]:
        with self._guard:
            current = self.repository.get_installation(current_installation_id)
            successor = self.repository.get_installation(successor_installation_id)
            if current is None or successor is None:
                raise LifecycleFailure(
                    "installation_not_found", "Installation was not found"
                )
            if successor["state"] != "ready":
                return {
                    "state": "blocked",
                    "category": "test_failed",
                    "message": "The successor must pass its exact standard test before activation.",
                }
            changed = self.repository.activate_installation(
                successor_installation_id,
                predecessor_id=current_installation_id,
                observed_at=self.clock(),
            )
            if not changed:
                raise LifecycleFailure(
                    "stale_binding", "Active revision changed concurrently"
                )
            return {
                "state": "succeeded",
                "active_installation_id": successor_installation_id,
                "predecessor_id": current_installation_id,
            }

    def prepare_rollback(
        self, current_installation_id: str, target_installation_id: str
    ) -> dict[str, Any]:
        current = self.repository.get_installation(current_installation_id)
        target = self.repository.get_installation(target_installation_id)
        if (
            current is None
            or target is None
            or current["model_id"] != target["model_id"]
            or not current["active_revision"]
        ):
            raise LifecycleFailure(
                "installation_not_found", "Rollback target is unavailable"
            )
        artifacts = self.repository.installation_artifacts(target_installation_id)
        cached = bool(artifacts) and all(
            self.store.has_verified(str(item["content_digest"])) for item in artifacts
        )
        if not cached:
            raise LifecycleFailure(
                "source_unavailable", "Rollback content is not cached"
            )
        if not self.repository.prepare_installation_retest(
            target_installation_id, observed_at=self.clock()
        ):
            raise LifecycleFailure(
                "stale_binding", "Rollback target changed concurrently"
            )
        return {
            "state": "testing_required",
            "current_installation_id": current_installation_id,
            "target_installation_id": target_installation_id,
            "cached_content_reused": True,
        }

    def disable(self, installation_id: str) -> dict[str, Any]:
        changed = self.repository.set_installation_lifecycle_state(
            installation_id,
            expected_states=("installed", "testing", "ready", "unhealthy"),
            state="disabled",
            active=False,
            observed_at=self.clock(),
        )
        current = self.repository.get_installation(installation_id)
        if current is None:
            raise LifecycleFailure(
                "installation_not_found", "Installation was not found"
            )
        if not changed and current["state"] != "disabled":
            raise LifecycleFailure("stale_binding", "Installation changed concurrently")
        return {"installation_id": installation_id, "state": "disabled"}

    def uninstall(self, installation_id: str) -> dict[str, Any]:
        changed = self.repository.set_installation_lifecycle_state(
            installation_id,
            expected_states=("disabled",),
            state="uninstalled",
            active=False,
            observed_at=self.clock(),
        )
        current = self.repository.get_installation(installation_id)
        if current is None:
            raise LifecycleFailure(
                "installation_not_found", "Installation was not found"
            )
        if not changed and current["state"] != "uninstalled":
            raise LifecycleFailure(
                "installation_enabled",
                "Disable the installation before uninstalling it",
            )
        return {"installation_id": installation_id, "state": "uninstalled"}

    def preview_purge(self, installation_id: str) -> dict[str, Any]:
        snapshot = self.repository.removal_snapshot(installation_id, at=self.clock())
        if snapshot is None:
            raise LifecycleFailure(
                "installation_not_found", "Installation was not found"
            )
        installation = snapshot["installation"]
        blockers = list(snapshot["blockers"])
        if installation["state"] != "uninstalled":
            blockers.insert(
                0,
                {
                    "kind": "package",
                    "owner_id": installation_id,
                    "message": "Disable and uninstall before purging verified bytes.",
                },
            )
        return {
            "installation_id": installation_id,
            "state": installation["state"],
            "active": bool(installation["active_revision"]),
            "reclaimable_bytes": 0 if blockers else snapshot["reclaimable_bytes"],
            "blockers": blockers,
            "references": snapshot["references"],
        }

    def set_reference_state(self, reference_id: str, state: str) -> dict[str, Any]:
        row = self.repository.set_reference_state(
            reference_id, state=state, observed_at=self.clock()
        )
        if row is None:
            raise LifecycleFailure("reference_not_found", "Reference was not found")
        return row

    def purge(
        self,
        installation_id: str,
        *,
        cancellation: CancellationSignal | None = None,
    ) -> dict[str, Any]:
        signal = cancellation or CancellationSignal()
        with self._guard:
            preview = self.preview_purge(installation_id)
            if signal.requested():
                raise LifecycleFailure("cancelled", "Purge was cancelled safely")
            if preview["blockers"]:
                raise LifecycleFailure(
                    "reference_blocked", "Verified content is still referenced"
                )
            snapshot = self.repository.removal_snapshot(
                installation_id, at=self.clock()
            )
            assert snapshot is not None
            reclaimed = 0
            for digest in sorted(
                {str(item["content_digest"]) for item in snapshot["artifacts"]}
            ):
                reclaimed += self.store.remove_verified(digest)
                self.repository.mark_content_missing(digest, observed_at=self.clock())
            self.store.remove_activation(installation_id)
            return {
                "installation_id": installation_id,
                "state": "succeeded",
                "reclaimed_bytes": reclaimed,
                "cleanup_state": "clean",
            }

    def recover_cleanup(self, operation_id: str) -> dict[str, Any]:
        result = self.store.cleanup_staging(operation_id)
        return {
            "operation_id": operation_id,
            "cleanup_state": result.state,
            "removed_items": result.removed_items,
            "residue": list(result.residue),
        }


__all__ = [
    "CancellationSignal",
    "DiskReservationManager",
    "LifecycleFailure",
    "MappingArtifactSource",
    "ModelMaintenanceLifecycle",
    "ModelInstallLifecycle",
    "ModelRevisionDifference",
    "compare_model_revisions",
]
