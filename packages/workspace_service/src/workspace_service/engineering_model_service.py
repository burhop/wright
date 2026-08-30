"""Application use cases for the offline engineering-model catalog."""

from __future__ import annotations

import platform as platform_module
import os
import shutil
import uuid
import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

import psutil
from data_vault import ModelArtifactStore, ModelRepository
from model_registry.catalog import ModelCatalog, ModelCatalogError, ModelCatalogFilters
from model_registry.generated import affine_artifacts, chatter_fixture_artifacts
from model_registry.http_source import HttpPackageArtifactSource
from model_registry.lifecycle import (
    DiskReservationManager,
    LifecycleFailure,
    MappingArtifactSource,
    ModelInstallLifecycle,
    ModelMaintenanceLifecycle,
    compare_model_revisions,
)
from model_registry.planning import (
    ModelEffectPlan,
    ModelPlanError,
    confirm_effect_plan,
    create_effect_plan,
    create_maintenance_effect_plan,
)
from model_registry.offline_source import (
    OfflinePackageError,
    export_offline_package,
    inspect_offline_package,
)
from model_registry.policy import HostObservation
from model_registry.gateway_provider import engineering_model_tool_name
from model_registry.models import ModelPackage, canonical_digest
from model_registry.runtime import (
    RuntimeFailure,
    RuntimeProgress,
    RuntimeSession,
    RuntimeSupervisor,
    built_in_runtime_registry,
    current_runtime_platform,
)
from model_registry.testing import EvidenceFailure, evaluate_test_vector
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
        runtime_adapters=built_in_runtime_registry().versions(),
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
        runtime_supervisor: RuntimeSupervisor | None = None,
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
        if runtime_supervisor is not None:
            self.runtime_supervisor = runtime_supervisor
        elif artifact_store is not None:
            self.runtime_supervisor = RuntimeSupervisor(
                built_in_runtime_registry(),
                scratch_root=artifact_store.root / "runtime-scratch",
                observer=artifact_store.observer,
            )
        else:
            self.runtime_supervisor = None
        self._runtime_requests: dict[tuple[str, str], RuntimeSession] = {}
        self._runtime_lock = asyncio.Lock()
        self.maintenance: ModelMaintenanceLifecycle | None = None
        if repository is not None and artifact_store is not None:
            self.maintenance = ModelMaintenanceLifecycle(
                repository=repository, store=artifact_store, clock=self.clock
            )
        self._authorized_exports: dict[str, tuple[str, datetime]] = {}

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

    def list_installations(
        self, *, model_id: str | None = None, principal_id: str
    ) -> dict[str, Any]:
        repository, _ = self._require_lifecycle()
        rows = tuple(
            row
            for row in repository.list_installations()
            if model_id is None or row["model_id"] == model_id
        )
        installations: list[dict[str, Any]] = []
        for row in rows:
            projection = {
                "installation_id": row["installation_id"],
                "model_id": row["model_id"],
                "package_revision": row["package_revision"],
                "variant_id": row["variant_id"],
                "manifest_digest": row["manifest_digest"],
                "state": row["state"],
                "active_revision": bool(row["active_revision"]),
                "runtime_adapter_id": row["runtime_adapter_id"],
                "runtime_adapter_version": row["runtime_adapter_version"],
                "standard_test_evidence_id": row.get("standard_test_evidence_id"),
                "installed_at": self._time_projection(row["installed_at"]),
                "last_verified_at": (
                    self._time_projection(row["last_verified_at"])
                    if row.get("last_verified_at")
                    else None
                ),
            }
            installations.append(
                {key: value for key, value in projection.items() if value is not None}
            )
        return {"installations": installations}

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

    def _create_maintenance_plan(
        self,
        *,
        operation_kind: str,
        installation_id: str,
        target_installation_id: str | None,
        principal_id: str,
        now: datetime | None = None,
        ttl: timedelta = timedelta(minutes=10),
    ) -> ModelEffectPlan:
        repository, store, maintenance = self._require_maintenance()
        installation = repository.get_installation(installation_id)
        if installation is None:
            raise EngineeringModelPortError(
                "installation_not_found",
                "The model installation was not found.",
                "Choose a current exact installation.",
            )
        observed = now or self.clock()
        snapshot = repository.removal_snapshot(installation_id, at=observed)
        assert snapshot is not None
        artifacts = tuple(snapshot["artifacts"])
        target = (
            repository.get_installation(target_installation_id)
            if target_installation_id
            else None
        )
        target_snapshot = (
            repository.removal_snapshot(target_installation_id, at=observed)
            if target_installation_id and target is not None
            else None
        )
        blockers: list[dict[str, str]] = []

        def block(category: str, message: str, recovery: str) -> None:
            blockers.append(
                {"category": category, "message": message, "recovery": recovery}
            )

        state = str(installation["state"])
        if operation_kind == "disable" and state in {"uninstalled", "missing"}:
            block(
                "installation_not_found",
                "An uninstalled or missing revision cannot be disabled.",
                "Choose a currently installed revision.",
            )
        elif operation_kind == "uninstall" and state not in {
            "disabled",
            "uninstalled",
        }:
            block(
                "installation_enabled",
                "The installation must be disabled before uninstall.",
                "Preview and confirm disable first.",
            )
        elif operation_kind == "purge":
            preview = maintenance.preview_purge(installation_id)
            for item in preview["blockers"]:
                block(
                    "reference_blocked",
                    str(
                        item.get("message")
                        or "Verified content is still referenced or leased."
                    ),
                    "Detach or archive the exact reference, or release the lease, then create a fresh purge plan.",
                )
        elif operation_kind == "export":
            if state in {"uninstalled", "missing"}:
                block(
                    "installation_not_found",
                    "The installed model is unavailable for export.",
                    "Choose a verified installed revision.",
                )
            try:
                package, variant = self._installation_package(installation)
            except EngineeringModelPortError as error:
                block(error.category, str(error), error.recovery)
            else:
                if (
                    package.source.access in {"gated", "private"}
                    or package.license.redistribution != "allowed"
                    or any(not item.redistributable for item in variant.artifacts)
                ):
                    block(
                        "export_forbidden",
                        "The exact package is not approved for redistribution.",
                        "Keep it local or obtain an independently reviewed redistribution decision.",
                    )
                if any(
                    item.get("state") != "verified"
                    or not store.has_verified(str(item["content_digest"]))
                    for item in artifacts
                ):
                    block(
                        "artifact_missing",
                        "One or more exact export artifacts are unavailable.",
                        "Repair the installation before exporting it.",
                    )
        elif operation_kind in {"update", "rollback"}:
            if target is None or target_installation_id is None:
                block(
                    "installation_not_found",
                    "The exact target installation was not found.",
                    "Choose an installed tested target revision.",
                )
            elif (
                target["model_id"] != installation["model_id"]
                or not installation["active_revision"]
                or target["active_revision"]
            ):
                block(
                    "stale_binding",
                    "The current and target revision relationship is stale.",
                    "Reload the active revision and choose its exact inactive target.",
                )
            elif operation_kind == "update" and target["state"] != "ready":
                block(
                    "test_failed",
                    "The successor must pass its exact standard test before update activation.",
                    "Run the mandatory standard test against the successor first.",
                )
            elif operation_kind == "rollback" and (
                target_snapshot is None
                or not target_snapshot["artifacts"]
                or any(
                    item.get("state") != "verified"
                    or not store.has_verified(str(item["content_digest"]))
                    for item in target_snapshot["artifacts"]
                )
            ):
                block(
                    "source_unavailable",
                    "The exact rollback content is not available in verified cache.",
                    "Restore or reacquire the exact predecessor before rollback.",
                )

        references: list[dict[str, str]] = [
            {
                "kind": "current_installation",
                "owner_id": installation_id,
                "effect": "retain",
            },
            {
                "kind": "installation_state",
                "owner_id": canonical_digest(
                    {
                        "installation_id": installation_id,
                        "state": state,
                        "active": bool(installation["active_revision"]),
                    }
                ),
                "effect": "retain",
            },
        ]
        if target is not None:
            references.append(
                {
                    "kind": "target_state",
                    "owner_id": canonical_digest(
                        {
                            "installation_id": target_installation_id,
                            "state": target["state"],
                            "active": bool(target["active_revision"]),
                        }
                    ),
                    "effect": "retain",
                }
            )
        for item in snapshot["references"]:
            references.append(
                {
                    "kind": f"reference_{item['kind']}",
                    "owner_id": str(item["reference_id"]),
                    "effect": "block" if item["state"] == "active" else "retain",
                }
            )
        plan_artifacts = (
            tuple(target_snapshot["artifacts"])
            if operation_kind == "rollback" and target_snapshot is not None
            else artifacts
        )
        return create_maintenance_effect_plan(
            operation_kind=operation_kind,
            installation=installation,
            target_installation=target,
            artifacts=plan_artifacts,
            snapshot_id=self.catalog.snapshot.snapshot_id,
            principal_id=principal_id,
            now=observed,
            ttl=ttl,
            blockers=tuple(blockers),
            references=tuple(references),
            reclaimable_bytes=int(snapshot["reclaimable_bytes"]),
        )

    def create_plan(
        self,
        *,
        operation_kind: str,
        model_id: str | None = None,
        variant_id: str | None = None,
        installation_id: str | None = None,
        target_installation_id: str | None = None,
        principal_id: str,
    ) -> dict[str, Any]:
        repository, _ = self._require_lifecycle()
        maintenance_kinds = {
            "update",
            "rollback",
            "export",
            "disable",
            "uninstall",
            "purge",
        }
        if operation_kind in maintenance_kinds:
            if not installation_id:
                raise EngineeringModelPortError(
                    "installation_not_found",
                    "This maintenance plan requires an exact installation.",
                    "Choose the installation to change.",
                )
            try:
                plan = self._create_maintenance_plan(
                    operation_kind=operation_kind,
                    installation_id=installation_id,
                    target_installation_id=target_installation_id,
                    principal_id=principal_id,
                )
            except (LifecycleFailure, ModelPlanError, ValueError) as error:
                raise EngineeringModelPortError(
                    getattr(error, "code", "plan_invalid"),
                    str(error),
                    "Reload the exact installation state and create a fresh plan.",
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
        if operation_kind not in {"install", "import"}:
            raise EngineeringModelPortError(
                "operation_unsupported",
                "This lifecycle operation is not supported.",
                "Choose a published engineering-model operation.",
            )
        if not model_id or not variant_id:
            raise EngineeringModelPortError(
                "plan_invalid",
                "Install plans require an exact model and variant.",
                "Choose an approved model variant.",
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
        if plan.operation_kind in {
            "update",
            "rollback",
            "export",
            "disable",
            "uninstall",
            "purge",
        }:
            return self._confirm_maintenance_plan(
                plan,
                principal_id=principal_id,
                plan_digest=plan_digest,
                trace_id=trace_id,
            )
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
        source = None
        if import_path is None:
            if package.model_id == "wright-affine-test":
                source = MappingArtifactSource(affine_artifacts(package))
            elif package.model_id == "wright-chatter-generated-test":
                source = MappingArtifactSource(chatter_fixture_artifacts(package))
            elif package.source.kind == "https" and package.source.access == "public":
                source = HttpPackageArtifactSource()
            else:
                raise EngineeringModelPortError(
                    "source_unavailable",
                    "No reviewed source adapter is enabled for this package.",
                    "Use an approved public HTTPS or offline package source.",
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
        try:
            if import_path is not None:
                operation = lifecycle.import_archive(
                    confirmed, import_path, trace_id=trace_id
                )
            else:
                assert source is not None
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
    def _plan_reference_owner(plan: ModelEffectPlan, kind: str) -> str | None:
        return next(
            (item.owner_id for item in plan.references if item.kind == kind), None
        )

    def _confirm_maintenance_plan(
        self,
        plan: ModelEffectPlan,
        *,
        principal_id: str,
        plan_digest: str,
        trace_id: str,
    ) -> dict[str, Any]:
        repository, _ = self._require_lifecycle()
        installation_id = self._plan_reference_owner(plan, "current_installation")
        target_installation_id = self._plan_reference_owner(plan, "target_installation")
        if installation_id is None:
            raise EngineeringModelPortError(
                "plan_invalid",
                "The maintenance plan does not identify its exact installation.",
                "Create and review a fresh plan.",
            )
        try:
            current = self._create_maintenance_plan(
                operation_kind=plan.operation_kind,
                installation_id=installation_id,
                target_installation_id=target_installation_id,
                principal_id=principal_id,
                now=plan.created_at,
                ttl=plan.expires_at - plan.created_at,
            )
            confirmed = confirm_effect_plan(
                plan,
                principal_id=principal_id,
                plan_digest=plan_digest,
                now=self.clock(),
                current_plan=current,
            )
        except (LifecycleFailure, ModelPlanError, ValueError) as error:
            raise EngineeringModelPortError(
                getattr(error, "code", "plan_invalidated"),
                str(error),
                "Reload current state and create a fresh maintenance plan.",
            ) from error
        if not repository.transition_plan(
            plan.plan_id,
            expected_state="confirmable",
            state="confirmed",
            trace_id=trace_id,
        ):
            raise EngineeringModelPortError(
                "plan_invalidated",
                "The plan was already used or changed.",
                "Create and review a fresh plan.",
            )
        return self._execute_maintenance_plan(
            confirmed,
            installation_id=installation_id,
            target_installation_id=target_installation_id,
            principal_id=principal_id,
            trace_id=trace_id,
        )

    def _execute_maintenance_plan(
        self,
        plan: ModelEffectPlan,
        *,
        installation_id: str,
        target_installation_id: str | None,
        principal_id: str,
        trace_id: str,
    ) -> dict[str, Any]:
        repository, _, maintenance = self._require_maintenance()
        operation_id = f"operation-{plan.plan_digest[:24]}"
        existing = repository.get_operation(operation_id)
        if existing is not None:
            return self._operation_projection(existing)
        repository.create_operation(
            operation_id=operation_id,
            plan_id=plan.plan_id,
            plan_digest=plan.plan_digest,
            kind=plan.operation_kind,
            trace_id=trace_id,
            created_at=self.clock(),
        )
        repository.transition_operation(
            operation_id,
            expected_state="prepared",
            state="running",
            phase="applying",
            progress={
                "completed_items": 0,
                "total_items": 1,
                "completed_bytes": 0,
                "maximum_bytes": sum(item.maximum_bytes for item in plan.effects),
                "message": f"Applying confirmed {plan.operation_kind} effects.",
            },
            updated_at=self.clock(),
            trace_id=trace_id,
        )
        try:
            if plan.operation_kind == "disable":
                result = maintenance.disable(installation_id)
            elif plan.operation_kind == "uninstall":
                result = maintenance.uninstall(installation_id)
            elif plan.operation_kind == "purge":
                result = maintenance.purge(installation_id)
            elif plan.operation_kind == "update":
                if target_installation_id is None:
                    raise LifecycleFailure(
                        "plan_invalidated", "The update target is unavailable"
                    )
                result = maintenance.activate_successor(
                    installation_id, target_installation_id
                )
                if result.get("state") == "blocked":
                    raise LifecycleFailure(
                        str(result.get("category") or "update_blocked"),
                        str(result.get("message") or "Update activation was blocked"),
                    )
            elif plan.operation_kind == "rollback":
                if target_installation_id is None:
                    raise LifecycleFailure(
                        "plan_invalidated", "The rollback target is unavailable"
                    )
                result = maintenance.prepare_rollback(
                    installation_id, target_installation_id
                )
            elif plan.operation_kind == "export":
                result = self._create_offline_export_unchecked(
                    installation_id,
                    principal_id=principal_id,
                    trace_id=trace_id,
                )
            else:  # pragma: no cover - guarded by the validated plan model
                raise LifecycleFailure(
                    "operation_unsupported", "Maintenance operation is unsupported"
                )
            cleanup_state = str(result.get("cleanup_state") or "not_needed")
            repository.transition_operation(
                operation_id,
                expected_state="running",
                state="succeeded",
                phase="complete",
                progress={
                    "completed_items": 1,
                    "total_items": 1,
                    "completed_bytes": sum(
                        item.exact_bytes or 0 for item in plan.effects
                    ),
                    "maximum_bytes": sum(item.maximum_bytes for item in plan.effects),
                    "message": f"Confirmed {plan.operation_kind} effects completed.",
                },
                result=result,
                cleanup_state=cleanup_state,
                updated_at=self.clock(),
                trace_id=trace_id,
            )
        except (EngineeringModelPortError, LifecycleFailure, ValueError) as error:
            code = getattr(
                error, "category", getattr(error, "code", "maintenance_failed")
            )
            terminal = (
                "blocked"
                if code
                in {
                    "installation_enabled",
                    "reference_blocked",
                    "source_unavailable",
                    "stale_binding",
                    "test_failed",
                }
                else "failed"
            )
            repository.transition_operation(
                operation_id,
                expected_state="running",
                state=terminal,
                phase=terminal,
                progress={
                    "completed_items": 0,
                    "total_items": 1,
                    "completed_bytes": 0,
                    "maximum_bytes": sum(item.maximum_bytes for item in plan.effects),
                    "message": f"Confirmed {plan.operation_kind} effects did not complete.",
                },
                failure={
                    "category": code,
                    "message": str(error),
                    "recovery": "Reload exact state, inspect cleanup, and create a fresh plan.",
                },
                cleanup_state=(
                    "residue" if plan.operation_kind == "purge" else "not_needed"
                ),
                updated_at=self.clock(),
                trace_id=trace_id,
            )
        row = repository.get_operation(operation_id)
        if row is None:  # pragma: no cover - durable repository invariant
            raise RuntimeError("Model maintenance operation persistence failed")
        return self._operation_projection(row)

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

    def _require_runtime(
        self,
    ) -> tuple[ModelRepository, ModelArtifactStore, RuntimeSupervisor]:
        repository, _ = self._require_lifecycle()
        if self.artifact_store is None or self.runtime_supervisor is None:
            raise EngineeringModelPortError(
                "runtime_missing",
                "The reviewed engineering-model runtime is unavailable.",
                "Restart Wright with its owned model data root available.",
            )
        return repository, self.artifact_store, self.runtime_supervisor

    def _require_maintenance(
        self,
    ) -> tuple[ModelRepository, ModelArtifactStore, ModelMaintenanceLifecycle]:
        repository, _, _ = self._require_runtime()
        if self.artifact_store is None or self.maintenance is None:
            raise EngineeringModelPortError(
                "model_lifecycle_unavailable",
                "Engineering-model maintenance is unavailable.",
                "Restart Wright with its owned model data root available.",
            )
        return repository, self.artifact_store, self.maintenance

    def get_installation_maintenance(
        self, installation_id: str, *, principal_id: str
    ) -> dict[str, Any]:
        _, _, maintenance = self._require_maintenance()
        try:
            return maintenance.preview_purge(installation_id)
        except ValueError as error:
            raise EngineeringModelPortError(
                getattr(error, "code", "maintenance_failed"),
                str(error),
                "Reload the exact installation and its current references.",
            ) from error

    def compare_installation_update(
        self,
        installation_id: str,
        *,
        model_id: str,
        variant_id: str,
        principal_id: str,
    ) -> dict[str, Any]:
        repository, _, _ = self._require_maintenance()
        installation = repository.get_installation(installation_id)
        if installation is None:
            raise EngineeringModelPortError(
                "installation_not_found",
                "The model installation was not found.",
                "Choose a current installation.",
            )
        current, _ = self._installation_package(installation)
        candidate = self._entry_package(model_id)
        try:
            difference = compare_model_revisions(
                current,
                candidate,
                current_variant_id=str(installation["variant_id"]),
                candidate_variant_id=variant_id,
            )
        except (KeyError, ValueError) as error:
            raise EngineeringModelPortError(
                getattr(error, "code", "update_invalid"),
                str(error),
                "Choose a reviewed revision and compatible variant of the same model.",
            ) from error
        return difference.projection()

    def maintain_installation(
        self,
        installation_id: str,
        *,
        action: str,
        target_installation_id: str | None,
        principal_id: str,
        trace_id: str,
    ) -> dict[str, Any]:
        raise EngineeringModelPortError(
            "effect_plan_required",
            f"The {action} action requires an exact reviewed effect plan.",
            "Create the maintenance plan, review every effect, then confirm it once.",
        )

    def set_model_reference_state(
        self, reference_id: str, *, state: str, principal_id: str
    ) -> dict[str, Any]:
        _, _, maintenance = self._require_maintenance()
        try:
            return maintenance.set_reference_state(reference_id, state)
        except ValueError as error:
            raise EngineeringModelPortError(
                getattr(error, "code", "reference_not_found"),
                str(error),
                "Reload the current reference list.",
            ) from error

    def create_offline_export(
        self, installation_id: str, *, principal_id: str, trace_id: str
    ) -> dict[str, Any]:
        raise EngineeringModelPortError(
            "effect_plan_required",
            "Offline export requires an exact reviewed effect plan.",
            "Create an export plan, review redistribution and bytes, then confirm it once.",
        )

    def _create_offline_export_unchecked(
        self, installation_id: str, *, principal_id: str, trace_id: str
    ) -> dict[str, Any]:
        repository, store, _ = self._require_maintenance()
        installation = repository.get_installation(installation_id)
        if installation is None or installation["state"] in {"uninstalled", "missing"}:
            raise EngineeringModelPortError(
                "installation_not_found",
                "The installed model is unavailable for export.",
                "Choose an installed, tested, or disabled revision.",
            )
        package, variant = self._installation_package(installation)
        declarations = {item.path: item for item in variant.artifacts}
        rows = repository.installation_artifacts(installation_id)
        if {str(row["artifact_path"]) for row in rows} != set(declarations):
            raise EngineeringModelPortError(
                "artifact_missing",
                "The installed artifact set is incomplete.",
                "Repair the exact installation before exporting it.",
            )
        try:
            artifacts = {
                str(row["artifact_path"]): store.read_verified(
                    str(row["content_digest"]),
                    maximum_bytes=declarations[str(row["artifact_path"])].size,
                )
                for row in rows
            }
            artifact_id = (
                "export-"
                + canonical_digest(
                    {
                        "installation_digest": installation["installation_digest"],
                        "manifest_digest": package.digest,
                        "artifact_digests": sorted(
                            str(row["content_digest"]) for row in rows
                        ),
                    }
                )[:24]
            )
            export_root = store.root / "exports"
            export_root.mkdir(parents=True, exist_ok=True)
            target = export_root / f"{artifact_id}.wright-model.zip"
            result = export_offline_package(package, artifacts, target)
        except (KeyError, ValueError, OfflinePackageError) as error:
            raise EngineeringModelPortError(
                getattr(error, "code", "export_failed"),
                str(error),
                "Review redistribution and installation integrity before retrying.",
            ) from error
        repository.add_reference(
            reference_id=f"reference-{artifact_id}",
            content_digest=None,
            installation_id=installation_id,
            kind="export",
            owner_id=artifact_id,
            created_at=self.clock(),
        )
        self._authorized_exports[artifact_id] = (
            principal_id,
            self.clock() + timedelta(minutes=10),
        )
        return {
            "artifact_id": artifact_id,
            "sha256": result.archive_sha256,
            "size": result.size,
            "filename": f"{package.model_id}-r{package.package_revision}.wright-model.zip",
        }

    def read_offline_export(self, artifact_id: str, *, principal_id: str) -> bytes:
        repository, store, _ = self._require_maintenance()
        authorization = self._authorized_exports.get(artifact_id)
        if authorization is None and artifact_id.startswith("export-"):
            durable = repository.find_export_authorization(artifact_id)
            if durable is not None:
                authorization = (
                    str(durable["principal_id"]),
                    datetime.fromtimestamp(durable["updated_at"] / 1000, UTC)
                    + timedelta(minutes=10),
                )
        if (
            authorization is None
            or authorization[0] != principal_id
            or self.clock() >= authorization[1]
            or not artifact_id.startswith("export-")
            or len(artifact_id) > 128
        ):
            raise EngineeringModelPortError(
                "export_not_found",
                "The offline export is unavailable.",
                "Create a fresh authorized export.",
            )
        target = store.root / "exports" / f"{artifact_id}.wright-model.zip"
        if not target.is_file() or target.stat().st_size > 512 * 1024 * 1024:
            raise EngineeringModelPortError(
                "export_not_found",
                "The offline export is unavailable.",
                "Create a fresh authorized export.",
            )
        return target.read_bytes()

    def _installation_package(self, installation: dict[str, Any]):
        try:
            package = self._entry_package(str(installation["model_id"]))
        except EngineeringModelPortError:
            package = None
        if package is None or (
            package.package_revision != int(installation["package_revision"])
            or package.digest != installation["manifest_digest"]
        ):
            try:
                package = ModelPackage.model_validate(installation.get("package"))
            except ValueError as error:
                raise EngineeringModelPortError(
                    "stale_binding",
                    "The exact installed package declaration is unavailable.",
                    "Restore the installation database backup or reinstall the exact revision.",
                ) from error
        if (
            package.package_revision != int(installation["package_revision"])
            or package.digest != installation["manifest_digest"]
        ):
            raise EngineeringModelPortError(
                "stale_binding",
                "The installation package identity is no longer current.",
                "Reinstall and rerun the standard test.",
            )
        try:
            variant = package.variant(str(installation["variant_id"]))
        except KeyError as error:
            raise EngineeringModelPortError(
                "stale_binding",
                "The installed variant is no longer available.",
                "Reinstall and rerun the standard test.",
            ) from error
        return package, variant

    def _artifact_paths(self, installation_id: str) -> dict[str, Path]:
        repository, store, _ = self._require_runtime()
        rows = repository.installation_artifacts(installation_id)
        if not rows:
            activation = store.read_activation(installation_id)
            raw = activation.get("artifacts") if activation else None
            if isinstance(raw, dict):
                rows = tuple(
                    {"artifact_path": key, "content_digest": value}
                    for key, value in raw.items()
                )
        try:
            return {
                str(row["artifact_path"]): store.verified_path(
                    str(row["content_digest"])
                )
                for row in rows
            }
        except KeyError as error:
            raise EngineeringModelPortError(
                "artifact_missing",
                "One or more installed artifacts are unavailable.",
                "Reinstall the exact package before testing it.",
            ) from error

    async def _runtime_session(
        self,
        installation: dict[str, Any],
        task_id: str,
        *,
        trace_id: str,
    ) -> RuntimeSession:
        _, _, supervisor = self._require_runtime()
        package, variant = self._installation_package(installation)
        platform_name, architecture = current_runtime_platform()
        return await supervisor.start_session(
            adapter_id=variant.runtime.adapter_id,
            installation_id=str(installation["installation_id"]),
            artifacts=self._artifact_paths(str(installation["installation_id"])),
            model_format=variant.format,
            task_id=task_id,
            platform=platform_name,
            architecture=architecture,
            execution_provider="cpu",
            startup_timeout=min(
                30.0,
                max(2.0, variant.resources.load_timeout_ms / 1000),
            ),
            maximum_artifact_bytes=max(
                variant.resources.installed_bytes,
                sum(item.size for item in variant.artifacts),
            ),
            required_ram_bytes=variant.resources.ram_bytes,
            required_disk_bytes=variant.resources.installed_bytes,
            trace_id=trace_id,
        )

    async def run_standard_test(
        self, installation_id: str, *, principal_id: str, trace_id: str
    ) -> dict[str, Any]:
        repository, _, _ = self._require_runtime()
        installation = repository.get_installation(installation_id)
        if installation is None or installation["state"] not in {
            "installed",
            "testing",
            "ready",
            "unhealthy",
        }:
            raise EngineeringModelPortError(
                "installation_not_found",
                "The installation is unavailable for testing.",
                "Install the exact package before running its standard test.",
            )
        package, variant = self._installation_package(installation)
        if installation["state"] == "ready":
            return self.get_standard_test_evidence(
                installation_id, principal_id=principal_id
            )
        session: RuntimeSession | None = None
        evidence_rows: list[dict[str, Any]] = []
        try:
            session = await self._runtime_session(
                installation,
                variant.test_vectors[0].task_id,
                trace_id=trace_id,
            )
            await session.verify(timeout=variant.resources.load_timeout_ms / 1000)
            handle = await session.load(
                timeout=variant.resources.load_timeout_ms / 1000
            )
            for vector in variant.test_vectors:
                if not vector.mandatory:
                    continue
                task = next(
                    item for item in package.tasks if item.task_id == vector.task_id
                )
                result = await session.infer(
                    handle,
                    vector.input,
                    schema_digest=canonical_digest(task.input_schema),
                    timeout=vector.limits.inference_timeout_ms / 1000,
                    maximum_output_bytes=vector.limits.max_output_bytes,
                )
                evidence = evaluate_test_vector(
                    package=package,
                    variant=variant,
                    vector=vector,
                    output=result["output"],
                    installation_id=installation_id,
                    installation_digest=str(installation["installation_digest"]),
                    artifact_set_digest=session.artifact_set_digest,
                    adapter_id=session.descriptor.adapter_id,
                    adapter_version=session.descriptor.adapter_version,
                    adapter_contract_version=session.descriptor.contract_version,
                    environment_policy_digest=canonical_digest(
                        {
                            "platform": current_runtime_platform()[0],
                            "architecture": current_runtime_platform()[1],
                            "provider": "cpu",
                        }
                    ),
                    timing_ms=int(result.get("timing_ms") or 0),
                    resources={"provider": "cpu"},
                    trace_id=trace_id,
                )
                evidence_id = (
                    "evidence-"
                    + canonical_digest(
                        {
                            "material_digest": evidence.material_digest,
                            "observation_digest": evidence.observation_digest,
                        }
                    )[:24]
                )
                repository.record_test_evidence(
                    evidence_id=evidence_id,
                    installation_id=installation_id,
                    vector_id=vector.vector_id,
                    material_digest=evidence.material_digest,
                    observation_digest=evidence.observation_digest,
                    state=evidence.state,
                    evidence=evidence.projection(),
                    created_at=self.clock(),
                    trace_id=trace_id,
                )
                evidence_rows.append(
                    {
                        "evidence_id": evidence_id,
                        **evidence.projection(),
                    }
                )
            evidence_id = str(evidence_rows[-1]["evidence_id"])
            if not repository.mark_installation_tested(
                installation_id,
                expected_state=str(installation["state"]),
                state="ready",
                adapter_version=session.descriptor.adapter_version,
                evidence_id=evidence_id,
                observed_at=self.clock(),
            ):
                raise EngineeringModelPortError(
                    "stale_binding",
                    "The installation changed while its evidence was being recorded.",
                    "Reload the installation before retrying its standard test.",
                )
            return {
                "installation_id": installation_id,
                "installation_state": "ready",
                "adapter_id": session.descriptor.adapter_id,
                "adapter_version": session.descriptor.adapter_version,
                "evidence": evidence_rows,
            }
        except (RuntimeFailure, EvidenceFailure) as error:
            repository.mark_installation_tested(
                installation_id,
                expected_state=str(installation["state"]),
                state="unhealthy",
                adapter_version=str(installation["runtime_adapter_version"]),
                evidence_id=None,
                observed_at=self.clock(),
            )
            raise EngineeringModelPortError(
                getattr(error, "category", "test_failed"),
                str(error),
                "Repair the exact installation/runtime and run the standard test again.",
            ) from error
        finally:
            if session is not None:
                cleanup = await session.shutdown()
                if cleanup != "clean":
                    raise EngineeringModelPortError(
                        "cleanup_residue",
                        "The runtime left cleanup residue.",
                        "Inspect Wright runtime diagnostics before retrying.",
                    )

    def get_standard_test_evidence(
        self, installation_id: str, *, principal_id: str
    ) -> dict[str, Any]:
        repository, _, _ = self._require_runtime()
        installation = repository.get_installation(installation_id)
        if installation is None:
            raise EngineeringModelPortError(
                "installation_not_found",
                "The model installation was not found.",
                "Choose an installed model.",
            )
        return {
            "installation_id": installation_id,
            "installation_state": installation["state"],
            "adapter_id": installation["runtime_adapter_id"],
            "adapter_version": installation["runtime_adapter_version"],
            "evidence": list(repository.list_test_evidence(installation_id)),
        }

    def create_workspace_binding(
        self,
        installation_id: str,
        *,
        task_id: str,
        workspace_id: str,
        principal_id: str,
    ) -> dict[str, Any]:
        repository, _, _ = self._require_runtime()
        installation = repository.get_installation(installation_id)
        if installation is None or installation["state"] != "ready":
            raise EngineeringModelPortError(
                "runtime_unhealthy",
                "The exact installation is not ready.",
                "Run the mandatory standard test first.",
            )
        package, _ = self._installation_package(installation)
        if task_id not in {item.task_id for item in package.tasks}:
            raise EngineeringModelPortError(
                "unsupported_task",
                "The installation does not provide this engineering task.",
                "Choose a declared task.",
            )
        tool_name = engineering_model_tool_name(package.model_id, task_id)
        policy_digest = canonical_digest(
            {"workspace_id": workspace_id, "policy": "gateway-model-v1"}
        )
        binding_material = {
            "workspace_id": workspace_id,
            "installation_id": installation_id,
            "installation_digest": installation["installation_digest"],
            "task_id": task_id,
            "tool_name": tool_name,
            "policy_snapshot_digest": policy_digest,
        }
        binding_digest = canonical_digest(binding_material)
        binding_id = "binding-" + binding_digest[:24]
        try:
            repository.bind_workspace(
                binding_id=binding_id,
                workspace_id=workspace_id,
                installation_id=installation_id,
                task_id=task_id,
                tool_name=tool_name,
                binding_digest=binding_digest,
                policy_snapshot_digest=policy_digest,
                state="enabled",
                created_at=self.clock(),
            )
        except Exception as error:
            existing = repository.get_binding(binding_id)
            if existing is None:
                raise EngineeringModelPortError(
                    "stale_binding",
                    "A conflicting workspace binding already exists.",
                    "Disable the conflicting binding and review a fresh one.",
                ) from error
            if existing["state"] == "disabled":
                if not repository.set_binding_state(
                    binding_id,
                    expected_state="disabled",
                    state="enabled",
                    observed_at=self.clock(),
                ):
                    raise EngineeringModelPortError(
                        "stale_binding",
                        "The existing workspace binding changed concurrently.",
                        "Reload and review the current binding.",
                    ) from error
            elif existing["state"] != "enabled":
                raise EngineeringModelPortError(
                    "stale_binding",
                    "The existing workspace binding is stale or blocked.",
                    "Review a fresh binding before enabling the capability.",
                ) from error
        return {
            "binding_id": binding_id,
            "binding_digest": binding_digest,
            "workspace_id": workspace_id,
            "installation_id": installation_id,
            "task_id": task_id,
            "tool_name": tool_name,
            "policy_snapshot_digest": policy_digest,
            "state": "enabled",
        }

    def set_workspace_binding_state(
        self,
        binding_id: str,
        *,
        state: str,
        workspace_id: str,
        principal_id: str,
    ) -> dict[str, Any]:
        repository, _, _ = self._require_runtime()
        if state not in {"enabled", "disabled"}:
            raise EngineeringModelPortError(
                "binding_state_invalid",
                "Binding state is invalid.",
                "Choose enabled or disabled.",
            )
        binding = repository.get_binding(binding_id)
        if binding is None or binding["workspace_id"] != workspace_id:
            raise EngineeringModelPortError(
                "binding_not_found",
                "The workspace binding was not found.",
                "Choose a current workspace binding.",
            )
        if state == "enabled":
            return self.create_workspace_binding(
                str(binding["installation_id"]),
                task_id=str(binding["task_id"]),
                workspace_id=workspace_id,
                principal_id=principal_id,
            )
        if binding["state"] != state:
            if not repository.set_binding_state(
                binding_id,
                expected_state=str(binding["state"]),
                state=state,
                observed_at=self.clock(),
            ):
                raise EngineeringModelPortError(
                    "stale_binding",
                    "The binding changed concurrently.",
                    "Reload and try again.",
                )
        return {**binding, "state": state}

    def declared_model_tool_names(self) -> frozenset[str]:
        names = set()
        for entry in self.catalog.entries:
            if entry.package is None:
                continue
            for task in entry.package.tasks:
                names.add(
                    engineering_model_tool_name(entry.package.model_id, task.task_id)
                )
        return frozenset(names)

    def discover_model_capabilities(
        self, *, principal_id: str, workspace_id: str, session_id: str
    ) -> tuple[dict[str, Any], ...]:
        repository, _, _ = self._require_runtime()
        results = []
        for binding in repository.list_bindings(workspace_id):
            installation = repository.get_installation(str(binding["installation_id"]))
            if installation is None:
                continue
            try:
                package, _ = self._installation_package(installation)
                task = next(
                    item for item in package.tasks if item.task_id == binding["task_id"]
                )
            except (EngineeringModelPortError, StopIteration):
                continue
            evidence = repository.list_test_evidence(
                str(installation["installation_id"])
            )
            current = next(
                (
                    item
                    for item in reversed(evidence)
                    if item["evidence_id"] == installation["standard_test_evidence_id"]
                ),
                None,
            )
            if current is None:
                continue
            expected_policy = canonical_digest(
                {"workspace_id": workspace_id, "policy": "gateway-model-v1"}
            )
            results.append(
                {
                    "model_id": package.model_id,
                    "task_id": task.task_id,
                    "description": f"{task.description} Limitation: {package.limitations[0].description}",
                    "input_schema": task.input_schema,
                    "output_schema": task.output_schema,
                    "workspace_id": workspace_id,
                    "binding_id": binding["binding_id"],
                    "binding_digest": binding["binding_digest"],
                    "binding_state": binding["state"],
                    "installation_id": installation["installation_id"],
                    "installation_digest": installation["installation_digest"],
                    "installation_state": installation["state"],
                    "adapter_id": installation["runtime_adapter_id"],
                    "adapter_version": installation["runtime_adapter_version"],
                    "evidence_id": current["evidence_id"],
                    "evidence_state": current["state"],
                    "material_digest": current["material_digest"],
                    "policy_snapshot_digest": binding["policy_snapshot_digest"],
                    "policy_current": binding["policy_snapshot_digest"]
                    == expected_policy,
                    "package_revision": package.package_revision,
                    "manifest_digest": package.digest,
                    "variant_id": installation["variant_id"],
                    "artifact_set_digest": canonical_digest(
                        {
                            str(item["artifact_path"]): str(item["content_digest"])
                            for item in repository.installation_artifacts(
                                str(installation["installation_id"])
                            )
                        }
                    ),
                    "runtime_version": (
                        "numpy-compatible-1"
                        if package.model_id.startswith("wright-chatter")
                        else str(installation["runtime_adapter_version"])
                    ),
                    "test_material_digest": current["material_digest"],
                    "input_schema_digest": canonical_digest(task.input_schema),
                    "output_schema_digest": canonical_digest(task.output_schema),
                    "threshold": (
                        0.5 if package.model_id.startswith("wright-chatter") else None
                    ),
                    "resource_digest": canonical_digest(
                        package.variant(
                            str(installation["variant_id"])
                        ).resources.model_dump(mode="json")
                    ),
                }
            )
        return tuple(results)

    async def invoke_model_capability(
        self,
        *,
        principal_id: str,
        workspace_id: str,
        session_id: str,
        request_id: str,
        trace_id: str,
        tool_name: str,
        binding_digest: str,
        arguments: dict[str, Any],
        approval_context: Any,
        progress_callback,
    ) -> dict[str, Any]:
        repository, _, _ = self._require_runtime()
        binding = repository.get_binding_by_digest(binding_digest)
        if (
            binding is None
            or binding["workspace_id"] != workspace_id
            or binding["tool_name"] != tool_name
            or binding["state"] != "enabled"
        ):
            raise EngineeringModelPortError(
                "stale_binding",
                "The reviewed model binding changed.",
                "Review the workflow binding again.",
            )
        installation = repository.get_installation(str(binding["installation_id"]))
        if installation is None or installation["state"] != "ready":
            raise EngineeringModelPortError(
                "runtime_unhealthy",
                "The bound installation is no longer ready.",
                "Run its standard test again.",
            )
        package, variant = self._installation_package(installation)
        task = next(
            item for item in package.tasks if item.task_id == binding["task_id"]
        )
        session = await self._runtime_session(
            installation, task.task_id, trace_id=trace_id
        )
        key = (session_id, request_id)
        async with self._runtime_lock:
            if key in self._runtime_requests:
                await session.shutdown()
                raise EngineeringModelPortError(
                    "runtime_unhealthy",
                    "The model request identity is already active.",
                    "Use a unique request identity.",
                )
            self._runtime_requests[key] = session

        async def forward(event: RuntimeProgress) -> None:
            if progress_callback is None:
                return
            result = progress_callback(
                {
                    "sequence": event.sequence,
                    "phase": event.phase,
                    "completed": event.completed_items,
                    "total": event.total_items,
                    "message": event.message,
                }
            )
            if result is not None:
                await result

        handle = None
        try:
            await session.verify(
                timeout=variant.resources.load_timeout_ms / 1000,
                progress_callback=forward,
            )
            handle = await session.load(
                timeout=variant.resources.load_timeout_ms / 1000,
                progress_callback=forward,
            )
            result = await session.infer(
                handle,
                arguments,
                schema_digest=canonical_digest(task.input_schema),
                timeout=variant.resources.inference_timeout_ms / 1000,
                maximum_output_bytes=variant.resources.max_output_bytes,
                progress_callback=forward,
                model_evidence=(
                    {
                        "model_id": package.model_id,
                        "package_revision": package.package_revision,
                        "variant_id": variant.variant_id,
                        "artifact_set_digest": session.artifact_set_digest,
                        "installation_digest": installation["installation_digest"],
                        "adapter_id": session.descriptor.adapter_id,
                        "adapter_version": session.descriptor.adapter_version,
                        "runtime_version": "numpy-compatible-1",
                        "test_evidence_id": installation["standard_test_evidence_id"],
                        "task_id": task.task_id,
                        "input_schema_digest": canonical_digest(task.input_schema),
                        "output_schema_digest": canonical_digest(task.output_schema),
                        "threshold": 0.5,
                    }
                    if package.model_id.startswith("wright-chatter")
                    else None
                ),
            )
            assert self.artifact_store is not None
            self.artifact_store.observer.record(
                "model.gateway.call",
                trace_id=trace_id,
                attributes={
                    "request_id": request_id,
                    "workspace_id": workspace_id,
                    "binding_digest": binding_digest,
                    "installation_digest": installation["installation_digest"],
                    "adapter_id": session.descriptor.adapter_id,
                    "task_id": task.task_id,
                    "result_digest": canonical_digest(result["output"]),
                },
            )
            return {
                "content": [
                    {"type": "text", "text": "Engineering model inference completed."}
                ],
                "structuredContent": dict(result["output"]),
                "_meta": {
                    "binding_digest": binding_digest,
                    "installation_digest": installation["installation_digest"],
                    "adapter_id": session.descriptor.adapter_id,
                    "adapter_version": session.descriptor.adapter_version,
                    "input_digest": canonical_digest(arguments),
                    "output_digest": canonical_digest(result["output"]),
                    "trace_id": trace_id,
                },
            }
        except asyncio.CancelledError:
            assert self.artifact_store is not None
            self.artifact_store.observer.record(
                "model.gateway.call",
                trace_id=trace_id,
                state="cancelled",
                attributes={
                    "request_id": request_id,
                    "workspace_id": workspace_id,
                    "binding_digest": binding_digest,
                    "task_id": task.task_id,
                },
            )
            raise
        except RuntimeFailure as error:
            assert self.artifact_store is not None
            self.artifact_store.observer.record(
                "model.gateway.call",
                trace_id=trace_id,
                state="failed",
                attributes={
                    "request_id": request_id,
                    "workspace_id": workspace_id,
                    "binding_digest": binding_digest,
                    "task_id": task.task_id,
                    "failure_category": error.category,
                },
            )
            raise EngineeringModelPortError(
                error.category,
                str(error),
                "Rerun the mandatory test or inspect runtime diagnostics.",
            ) from error
        finally:
            if handle is not None:
                try:
                    await session.unload(handle)
                except RuntimeFailure:
                    pass
            await session.shutdown()
            async with self._runtime_lock:
                self._runtime_requests.pop(key, None)

    async def cancel_model_request(self, *, session_id: str, request_id: str) -> None:
        session = self._runtime_requests.get((session_id, request_id))
        if session is not None:
            await session.cancel_current()

    async def close_model_session(self, *, session_id: str) -> None:
        owned = [
            (key, runtime)
            for key, runtime in self._runtime_requests.items()
            if key[0] == session_id
        ]
        await asyncio.gather(
            *(runtime.shutdown() for _, runtime in owned), return_exceptions=True
        )
        async with self._runtime_lock:
            for key, _ in owned:
                self._runtime_requests.pop(key, None)

    async def shutdown_model_runtime(self) -> None:
        if self.runtime_supervisor is not None:
            await self.runtime_supervisor.shutdown()
        async with self._runtime_lock:
            self._runtime_requests.clear()


__all__ = ["EngineeringModelService", "observe_local_model_host"]
