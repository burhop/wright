"""Application use cases for the offline engineering-model catalog."""

from __future__ import annotations

import platform as platform_module
import os
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

import psutil
from data_vault import ModelArtifactStore, ModelRepository
from model_registry.catalog import ModelCatalog, ModelCatalogError, ModelCatalogFilters
from model_registry.generated import affine_artifacts
from model_registry.lifecycle import (
    DiskReservationManager,
    MappingArtifactSource,
    ModelInstallLifecycle,
)
from model_registry.planning import (
    ModelEffectPlan,
    ModelPlanError,
    confirm_effect_plan,
    create_effect_plan,
)
from model_registry.offline_source import OfflinePackageError, inspect_offline_package
from model_registry.policy import HostObservation
from tool_registry.model_library_port import EngineeringModelPortError


def observe_local_model_host(data_root: str | Path | None = None) -> HostObservation:
    platform_names = {
        "darwin": "macos",
        "linux": "linux",
        "windows": "windows",
    }
    architectures = {
        "amd64": "x86_64",
        "x86_64": "x86_64",
        "aarch64": "aarch64",
        "arm64": "aarch64",
    }
    system = platform_names.get(platform_module.system().lower(), "unknown")
    architecture = architectures.get(platform_module.machine().lower(), "unknown")
    target = Path(data_root) if data_root is not None else Path.cwd()
    try:
        available_disk = shutil.disk_usage(target).free
    except OSError:
        available_disk = 0
    return HostObservation(
        platform=system,
        architecture=architecture,
        available_disk_bytes=available_disk,
        available_ram_bytes=int(psutil.virtual_memory().available),
        accelerators=frozenset({"cpu"}),
        runtime_adapters={"wright-deterministic": "1.0.0"},
    )


class EngineeringModelService:
    """Read-only first slice; constructing it performs no source or runtime calls."""

    def __init__(
        self,
        *,
        catalog: ModelCatalog | None = None,
        host_observer: Callable[[], HostObservation] | None = None,
        repository: ModelRepository | None = None,
        artifact_store: ModelArtifactStore | None = None,
        lifecycle: ModelInstallLifecycle | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.catalog = catalog or ModelCatalog.load_bundled()
        self.host_observer = host_observer or observe_local_model_host
        self.repository = repository
        self.artifact_store = artifact_store
        self.clock = clock or (lambda: datetime.now(UTC))
        if lifecycle is not None:
            self.lifecycle = lifecycle
        elif repository is not None and artifact_store is not None:
            self.lifecycle = ModelInstallLifecycle(
                repository=repository,
                store=artifact_store,
                disk=DiskReservationManager(artifact_store.root),
                clock=self.clock,
            )
        else:
            self.lifecycle = None

    def list_catalog(
        self,
        *,
        search: str | None = None,
        task: str | None = None,
        source_kind: str | None = None,
        readiness: tuple[str, ...] = (),
        platform: str | None = None,
        architecture: str | None = None,
        accelerator: str | None = None,
        evidence_state: str | None = None,
        maximum_bytes: int | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> dict:
        try:
            page = self.catalog.list(
                ModelCatalogFilters(
                    search=search,
                    task=task,
                    source_kind=source_kind,
                    readiness=readiness,
                    platform=platform,
                    architecture=architecture,
                    accelerator=accelerator,
                    evidence_state=evidence_state,
                    maximum_bytes=maximum_bytes,
                ),
                host=self.host_observer(),
                cursor=cursor,
                limit=limit,
            )
        except ModelCatalogError as error:
            raise EngineeringModelPortError(
                error.code,
                str(error),
                "Adjust the bounded filters or reload the current offline snapshot.",
            ) from error
        return {
            "snapshot": self.catalog.snapshot.projection(),
            "models": list(page.items),
            "next_cursor": page.next_cursor,
            "total": page.total,
        }

    def get_catalog_model(self, model_id: str) -> dict:
        try:
            return self.catalog.get_view(model_id, host=self.host_observer())
        except ModelCatalogError as error:
            raise EngineeringModelPortError(
                error.code,
                str(error),
                "Choose a model from the active offline catalog snapshot.",
            ) from error

    def _require_lifecycle(self) -> tuple[ModelRepository, ModelInstallLifecycle]:
        if self.repository is None or self.lifecycle is None:
            raise EngineeringModelPortError(
                "model_lifecycle_unavailable",
                "The local engineering-model lifecycle is not configured.",
                "Restart Wright with its owned data root available.",
            )
        return self.repository, self.lifecycle

    def _entry_package(self, model_id: str):
        try:
            entry = self.catalog.get(model_id)
        except ModelCatalogError as error:
            raise EngineeringModelPortError(
                error.code,
                str(error),
                "Choose a model from the active offline catalog snapshot.",
            ) from error
        if entry.package is None:
            raise EngineeringModelPortError(
                "model_not_installable",
                "This catalog entry has no approved installable package.",
                "Review its blockers and wait for complete package evidence.",
            )
        return entry.package

    def create_plan(
        self,
        *,
        operation_kind: str,
        model_id: str,
        variant_id: str,
        principal_id: str,
    ) -> dict[str, Any]:
        repository, _ = self._require_lifecycle()
        if operation_kind not in {"install", "import"}:
            raise EngineeringModelPortError(
                "operation_unsupported",
                "This lifecycle operation is not available in the install slice.",
                "Choose install or offline import.",
            )
        package = self._entry_package(model_id)
        cached = {
            artifact.sha256
            for artifact in package.variant(variant_id).artifacts
            if self.artifact_store is not None
            and self.artifact_store.has_verified(artifact.sha256)
        }
        try:
            plan = create_effect_plan(
                package,
                variant_id=variant_id,
                snapshot_id=self.catalog.snapshot.snapshot_id,
                principal_id=principal_id,
                host=self.host_observer(),
                now=self.clock(),
                operation_kind=operation_kind,
                cached_digests=cached,
            )
        except (KeyError, ModelPlanError, ValueError) as error:
            raise EngineeringModelPortError(
                getattr(error, "code", "plan_invalid"),
                str(error),
                "Choose an approved compatible variant and create a fresh plan.",
            ) from error
        repository.save_plan(
            plan_id=plan.plan_id,
            principal_id=plan.principal_id,
            plan_digest=plan.plan_digest,
            state=plan.state,
            plan=plan.model_dump(mode="json", exclude_none=True),
            created_at=plan.created_at,
            expires_at=plan.expires_at,
        )
        return plan.model_dump(mode="json", exclude_none=True)

    def _import_path(self, plan_id: str) -> Path:
        if self.artifact_store is None:
            raise EngineeringModelPortError(
                "model_lifecycle_unavailable",
                "The local engineering-model artifact store is unavailable.",
                "Restart Wright with its owned data root available.",
            )
        if not plan_id.startswith("plan-") or len(plan_id) > 128:
            raise EngineeringModelPortError(
                "plan_invalid", "The import plan identity is invalid.", "Upload again."
            )
        root = self.artifact_store.root / "imports"
        root.mkdir(parents=True, exist_ok=True)
        return root / f"{plan_id}.wright-model.zip"

    def create_import_plan(
        self, *, archive: bytes, principal_id: str
    ) -> dict[str, Any]:
        repository, _ = self._require_lifecycle()
        if not archive or len(archive) > 256 * 1024 * 1024:
            raise EngineeringModelPortError(
                "size_exceeded",
                "The offline package exceeds the 256 MiB upload ceiling.",
                "Choose a smaller reviewed package.",
            )
        assert self.artifact_store is not None
        import_root = self.artifact_store.root / "imports"
        import_root.mkdir(parents=True, exist_ok=True)
        temporary = import_root / f".upload-{uuid.uuid4().hex}.tmp"
        try:
            with temporary.open("xb") as stream:
                stream.write(archive)
                stream.flush()
                os.fsync(stream.fileno())
            inspected = inspect_offline_package(
                temporary,
                maximum_archive_bytes=256 * 1024 * 1024,
                maximum_expanded_bytes=512 * 1024 * 1024,
            )
            plan = create_effect_plan(
                inspected.package,
                variant_id=inspected.package.variants[0].variant_id,
                snapshot_id=self.catalog.snapshot.snapshot_id,
                principal_id=principal_id,
                host=self.host_observer(),
                now=self.clock(),
                operation_kind="import",
                cached_digests={
                    artifact.sha256
                    for variant in inspected.package.variants
                    for artifact in variant.artifacts
                    if self.artifact_store.has_verified(artifact.sha256)
                },
            )
            repository.save_plan(
                plan_id=plan.plan_id,
                principal_id=plan.principal_id,
                plan_digest=plan.plan_digest,
                state=plan.state,
                plan=plan.model_dump(mode="json", exclude_none=True),
                created_at=plan.created_at,
                expires_at=plan.expires_at,
            )
            target = self._import_path(plan.plan_id)
            if target.exists():
                if target.read_bytes() != archive:
                    raise EngineeringModelPortError(
                        "plan_invalidated",
                        "The offline package identity collided with different bytes.",
                        "Upload again to create a fresh plan.",
                    )
                temporary.unlink(missing_ok=True)
            else:
                os.replace(temporary, target)
            return plan.model_dump(mode="json", exclude_none=True)
        except EngineeringModelPortError:
            raise
        except OfflinePackageError as error:
            raise EngineeringModelPortError(
                error.code,
                str(error),
                "Repair or regenerate the offline package, then upload it again.",
            ) from error
        finally:
            temporary.unlink(missing_ok=True)

    def _load_plan(self, plan_id: str, principal_id: str) -> ModelEffectPlan:
        repository, _ = self._require_lifecycle()
        row = repository.get_plan(plan_id)
        if row is None or row["principal_id"] != principal_id:
            raise EngineeringModelPortError(
                "plan_not_found",
                "The engineering-model plan was not found.",
                "Create and review a fresh plan.",
            )
        try:
            return ModelEffectPlan.model_validate(row["plan"]).model_copy(
                update={"state": row["state"]}
            )
        except ValueError as error:
            raise EngineeringModelPortError(
                "plan_invalid",
                "The durable engineering-model plan is invalid.",
                "Create and review a fresh plan.",
            ) from error

    def get_plan(self, plan_id: str, *, principal_id: str) -> dict[str, Any]:
        return self._load_plan(plan_id, principal_id).model_dump(
            mode="json", exclude_none=True
        )

    def confirm_plan(
        self,
        plan_id: str,
        *,
        principal_id: str,
        plan_digest: str,
        trace_id: str,
    ) -> dict[str, Any]:
        repository, lifecycle = self._require_lifecycle()
        plan = self._load_plan(plan_id, principal_id)
        import_path: Path | None = None
        if plan.operation_kind == "import":
            import_path = self._import_path(plan.plan_id)
            if not import_path.is_file():
                raise EngineeringModelPortError(
                    "plan_invalidated",
                    "The staged offline package is no longer available.",
                    "Upload it again and review a fresh plan.",
                )
            try:
                package = inspect_offline_package(import_path).package
            except OfflinePackageError as error:
                raise EngineeringModelPortError(
                    error.code,
                    str(error),
                    "Upload the reviewed offline package again.",
                ) from error
        else:
            package = self._entry_package(plan.model_id)
        cached = {
            artifact.sha256
            for artifact in package.variant(plan.variant_id).artifacts
            if self.artifact_store is not None
            and self.artifact_store.has_verified(artifact.sha256)
        }
        current = create_effect_plan(
            package,
            variant_id=plan.variant_id,
            snapshot_id=self.catalog.snapshot.snapshot_id,
            principal_id=principal_id,
            host=self.host_observer(),
            now=plan.created_at,
            ttl=plan.expires_at - plan.created_at,
            operation_kind=plan.operation_kind,
            cached_digests=cached,
        )
        try:
            confirmed = confirm_effect_plan(
                plan,
                principal_id=principal_id,
                plan_digest=plan_digest,
                now=self.clock(),
                current_plan=current,
            )
        except ModelPlanError as error:
            raise EngineeringModelPortError(
                error.code,
                str(error),
                "Create and review a fresh plan.",
            ) from error
        if not repository.transition_plan(
            plan_id, expected_state="confirmable", state="confirmed", trace_id=trace_id
        ):
            raise EngineeringModelPortError(
                "plan_invalidated",
                "The plan was already used or changed.",
                "Create and review a fresh plan.",
            )
        if plan.operation_kind != "import" and package.source.kind != "wright":
            raise EngineeringModelPortError(
                "source_unavailable",
                "No reviewed source adapter is enabled for this package.",
                "Use an approved offline package or keep the entry evaluation-only.",
            )
        try:
            if import_path is not None:
                operation = lifecycle.import_archive(
                    confirmed, import_path, trace_id=trace_id
                )
            else:
                source = MappingArtifactSource(affine_artifacts(package))
                operation = lifecycle.install(
                    confirmed, package, source, trace_id=trace_id
                )
        except ValueError as error:
            raise EngineeringModelPortError(
                getattr(error, "code", "model_install_failed"),
                str(error),
                "Inspect the durable operation and retry from a fresh plan.",
            ) from error
        finally:
            if import_path is not None:
                import_path.unlink(missing_ok=True)
        return self._operation_projection(operation)

    @staticmethod
    def _time_projection(value: Any) -> str:
        if isinstance(value, (int, float)):
            return (
                datetime.fromtimestamp(value / 1000, UTC)
                .isoformat()
                .replace("+00:00", "Z")
            )
        return str(value)

    def _operation_projection(self, row: dict[str, Any]) -> dict[str, Any]:
        result = {
            "schema_version": "1.0",
            "operation_id": row["operation_id"],
            "plan_id": row["plan_id"],
            "plan_digest": row["plan_digest"],
            "kind": row["kind"],
            "state": row["state"],
            "phase": row["phase"],
            "progress": row["progress"],
            "result": row.get("result"),
            "failure": row.get("failure"),
            "trace_id": row["trace_id"],
            "cancellation_requested_at": (
                self._time_projection(row["cancellation_requested_at"])
                if row.get("cancellation_requested_at")
                else None
            ),
            "cleanup_state": row["cleanup_state"],
            "created_at": self._time_projection(row["created_at"]),
            "updated_at": self._time_projection(row["updated_at"]),
        }
        return {key: value for key, value in result.items() if value is not None}

    def _authorized_operation(
        self, operation_id: str, principal_id: str
    ) -> dict[str, Any]:
        repository, _ = self._require_lifecycle()
        row = repository.get_operation(operation_id)
        plan = repository.get_plan(row["plan_id"]) if row is not None else None
        if row is None or plan is None or plan["principal_id"] != principal_id:
            raise EngineeringModelPortError(
                "operation_not_found",
                "The engineering-model operation was not found.",
                "Open an operation started by the current principal.",
            )
        return row

    def get_operation(self, operation_id: str, *, principal_id: str) -> dict[str, Any]:
        return self._operation_projection(
            self._authorized_operation(operation_id, principal_id)
        )

    def cancel_operation(
        self, operation_id: str, *, principal_id: str
    ) -> dict[str, Any]:
        repository, _ = self._require_lifecycle()
        row = self._authorized_operation(operation_id, principal_id)
        if row["state"] in {"blocked", "succeeded", "failed", "cancelled"}:
            return self._operation_projection(row)
        repository.transition_operation(
            operation_id,
            expected_state=row["state"],
            state="cancelling",
            phase="cancelling",
            progress=row["progress"],
            cleanup_state="pending",
            cancellation_requested_at=self.clock(),
            updated_at=self.clock(),
            trace_id=row["trace_id"],
        )
        return self.get_operation(operation_id, principal_id=principal_id)

    def operation_events(
        self, operation_id: str, *, principal_id: str, after: int
    ) -> tuple[dict[str, Any], ...]:
        if after >= 1:
            self._authorized_operation(operation_id, principal_id)
            return ()
        return (
            {
                "sequence": 1,
                "operation": self.get_operation(
                    operation_id, principal_id=principal_id
                ),
            },
        )


__all__ = ["EngineeringModelService", "observe_local_model_host"]
