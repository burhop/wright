"""Native owner of fixed static UI presentation over the existing surface graph.

Opening or closing a view never executes, cancels or approves its process. Model
source supplies no launch command, endpoint, principal or grant authority.
"""

import json

from core.process_validation import Identifier, canonical_digest
from core.surfaces.live_app_manifest import parse_live_app_manifest
from core.surfaces.models import (
    LiveAppOwnership,
    LiveAppSurfaceSource,
    SurfaceLifecycle,
)
from core.surfaces.errors import SurfaceError
from pydantic import TypeAdapter

from ..surfaces.grants import (
    CapabilityGrantError,
    CapabilityRequest,
    ProcessPresentationBinding,
)
from ..surfaces.process_ui_manifest import process_ui_manifest
from ..surfaces.service import SurfaceActor
from ..surfaces.live_app_service import LiveAppControlError
from ..surfaces.presentation_service import PresentationUnavailable
from ..workspace_path import WorkspacePath
from .authoring import accepted_binding_catalog
from .build import validate_manifest_bindings
from .errors import ProcessInterfaceError
from .service import ProcessScope


class ProcessInterfacePresentations:
    def __init__(self, application, surfaces):
        self.application, self.surfaces = application, surfaces

    @staticmethod
    def _actor(scope, actor):
        if not isinstance(actor, SurfaceActor) or (
            actor.user_id,
            actor.workspace_id,
        ) != (scope.principal_id, scope.workspace_id):
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "The view does not belong to this native workspace context.",
                "Reopen the process in its registered Wright workspace.",
            )

    @staticmethod
    def _install_manifest(root, value, declaration):
        path = WorkspacePath(root).resolve(
            f".wright/apps/{declaration.manifest_id}.surface.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        for parent in (path.parent, *path.parent.parents):
            if (
                parent.is_symlink()
                or getattr(parent.stat(), "st_file_attributes", 0) & 0x400
            ):
                raise ValueError("The managed manifest cannot follow links")
        if path.exists():
            if (
                path.is_symlink()
                or getattr(path.stat(), "st_file_attributes", 0) & 0x400
                or path.stat().st_size > 262144
            ):
                raise ValueError("The fixed manifest is not a regular bounded file")
            current = parse_live_app_manifest(json.loads(path.read_bytes()))
            if current.canonical_hash != declaration.canonical_hash:
                raise ValueError("The fixed managed manifest changed")
            return
        with path.open("x", encoding="utf-8") as stream:
            json.dump(value, stream, sort_keys=True)

    async def open(
        self, scope, process, actor, job_id, request_id, *, read_only, run_id=None
    ):
        try:
            return await self._open(
                scope,
                process,
                actor,
                job_id,
                request_id,
                read_only=read_only,
                run_id=run_id,
            )
        except (LiveAppControlError, PresentationUnavailable, SurfaceError):
            raise ProcessInterfaceError(
                "CAPABILITY_UNAVAILABLE",
                "Wright could not open the managed process interface.",
                "Use the common view and inspect its managed runtime diagnostics before reopening.",
            ) from None

    async def _open(
        self, scope, process, actor, job_id, request_id, *, read_only, run_id=None
    ):
        self._actor(scope, actor)
        scope.require(process, "process.read")
        request_id = TypeAdapter(Identifier).validate_python(request_id)
        if type(read_only) is not bool:
            raise ValueError("Presentation mode must be explicit")
        if not self.surfaces.accepting_commands:
            raise ProcessInterfaceError(
                "CAPABILITY_UNAVAILABLE",
                "Wright's managed interface host is not ready.",
                "Use the common view while the surface service starts.",
            )
        resolved = await self.application.resolve_process(scope, process)
        job, manifest, report, _source, _bundle = (
            self.application.ui_revisions.preview_bundle(scope, process, job_id)
        )
        validate_manifest_bindings(
            manifest, process, accepted_binding_catalog(resolved.document)
        )
        if not set(manifest.capabilities) <= scope.capabilities:
            raise ProcessInterfaceError(
                "UI_INCOMPATIBLE",
                "The interface requests unavailable process capabilities.",
                "Update its capabilities or use the common working view.",
            )
        if not read_only:
            revision = self.application.interfaces.get_revision(
                process.workspace_id, manifest.ui_id, manifest.revision_id
            )
            self.application.ui_revisions.saved_source(scope, process, revision)
        if run_id is not None:
            bound = ProcessScope(
                scope.principal_id,
                scope.workspace_id,
                scope.capabilities,
                run_bound=True,
                run_id=run_id,
            )
            self.application.runs._receipt(bound, process, run_id)
        built = self.application.interfaces.get_authoring_record(
            process.workspace_id, job_id, "built"
        )
        value, declaration = process_ui_manifest(
            resolved.workspace_dir, manifest, built["inventory_digest"]
        )
        try:
            self._install_manifest(resolved.workspace_dir, value, declaration)
        except (OSError, ValueError):
            raise ProcessInterfaceError(
                "UI_INCOMPATIBLE",
                "The fixed interface runtime declaration is unavailable or changed.",
                "Restore its managed declaration or use the common working view.",
            ) from None
        source = LiveAppSurfaceSource(
            manifest_id=declaration.manifest_id,
            manifest_version=declaration.version,
            manifest_hash=declaration.canonical_hash,
            ownership=LiveAppOwnership.WRIGHT_OWNED,
            administrator_approved=True,
            sharing_mode="isolated",
        )
        key = "process-ui:" + canonical_digest({"request_id": request_id})
        descriptor = await self.surfaces.service.declare(
            actor=actor, source=source, title=manifest.title[:256], idempotency_key=key
        )
        if descriptor.source != source:
            raise ProcessInterfaceError(
                "REQUEST_CONFLICT",
                "This view request already identifies a different interface revision.",
                "Reconcile its existing presentation or choose a new view request.",
            )
        if descriptor.lifecycle is SurfaceLifecycle.DECLARED:
            await self.surfaces.live_apps.start(
                actor=actor, surface_id=descriptor.surface_id, idempotency_key=key
            )
            descriptor = await self.surfaces.service.get(
                actor=actor, surface_id=descriptor.surface_id
            )
        if descriptor.lifecycle is not SurfaceLifecycle.READY:
            raise ProcessInterfaceError(
                "CAPABILITY_UNAVAILABLE",
                "The managed interface is not ready for a presentation.",
                "Wait for its current launch or inspect its managed runtime diagnostics.",
            )
        opened = self.surfaces.presentation_service.open(
            actor=actor,
            surface_id=descriptor.surface_id,
            kind="panel",
            idempotency_key=key,
            remember_preference=False,
            isolated_acknowledged=True,
        )
        launch = opened.launch
        binding = ProcessPresentationBinding(
            process=process,
            ui_id=manifest.ui_id,
            revision_id=manifest.revision_id,
            run_id=run_id,
            read_only=read_only,
            presentation_id=launch.presentation_id,
            generation=launch.generation,
        )
        record = self.surfaces.presentation_service.get_record(
            actor=actor, presentation_id=launch.presentation_id
        )
        if record.surface_id != str(descriptor.surface_id):
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "The view belongs to another managed surface.",
                "Reopen the exact interface from its owning workspace.",
            )
        duration = min(
            self.surfaces.grant_service.policy.maximum_duration_seconds,
            max(
                1,
                int(
                    (
                        record.expires_at - self.surfaces.presentation_service.clock()
                    ).total_seconds()
                ),
            ),
        )
        existing = self.surfaces.grant_service.repository.list(
            user_id=actor.user_id,
            workspace_id=actor.workspace_id,
            source_id=source.source_id,
            source_version=source.source_version,
        )
        prior = [
            grant
            for grant in existing
            if grant.instance_id == launch.instance_id
            and grant.constraints.get("presentation_id") == launch.presentation_id
        ]
        if any(grant.constraints != binding.model_dump(mode="json") for grant in prior):
            raise ProcessInterfaceError(
                "REQUEST_CONFLICT",
                "This view request already has a different process/run binding.",
                "Reconcile its existing view or open the requested run with a new view identity.",
            )
        try:
            for capability in manifest.capabilities:
                read = capability in {
                    "process.read",
                    "process.results",
                    "process.navigate",
                }
                if read_only and not read:
                    continue
                request = CapabilityRequest(
                    source_id=source.source_id,
                    source_version=source.source_version,
                    instance_id=launch.instance_id,
                    capability=capability,
                    operation=capability,
                    constraints=binding.model_dump(mode="json"),
                    risk_tier="low" if read else "mutating",
                    persistence="instance",
                    duration_seconds=duration,
                    declared=True,
                    decision="allow",
                    reason="Use this native-authorized exact process interface; engineering decisions remain separate.",
                )
                if prior:
                    self.surfaces.grant_service.authorize(actor=actor, request=request)
                else:
                    self.surfaces.grant_service.decide(actor=actor, request=request)
        except CapabilityGrantError:
            await self.close(
                scope, actor, descriptor.surface_id, launch.presentation_id
            )
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "The process presentation exceeds current surface capability policy.",
                "Use the common view or reopen with a fresh permitted presentation.",
            ) from None
        return {
            "descriptor": descriptor,
            "launch": launch,
            "binding": binding,
            "job_id": job.job_id,
            "build": report,
        }

    async def close(self, scope, actor, surface_id, presentation_id):
        try:
            return await self._close(scope, actor, surface_id, presentation_id)
        except (LiveAppControlError, SurfaceError):
            raise ProcessInterfaceError(
                "CAPABILITY_UNAVAILABLE",
                "The interface could not finish its managed-view cleanup.",
                "Reconcile the view's runtime diagnostics. Closing a view does not cancel its process.",
            ) from None

    async def _close(self, scope, actor, surface_id, presentation_id):
        self._actor(scope, actor)
        try:
            record = self.surfaces.presentation_service.get_record(
                actor=actor, presentation_id=presentation_id
            )
        except PresentationUnavailable:
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "This view is unavailable in the native workspace context.",
                "Close the presentation from its owning workspace tab.",
            ) from None
        if record.surface_id != str(surface_id) or not record.source_id.startswith(
            "process.ui-"
        ):
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "This presentation is not a process interface.",
                "Close its owning view in Wright.",
            )
        self.surfaces.presentation_service.close(
            actor=actor, surface_id=surface_id, presentation_id=presentation_id
        )
        grants = self.surfaces.grant_service.repository.list(
            user_id=actor.user_id,
            workspace_id=actor.workspace_id,
            source_id=record.source_id,
            source_version=record.source_version,
        )
        for grant in grants:
            if (
                grant.revoked_at is None
                and grant.constraints.get("presentation_id") == presentation_id
            ):
                self.surfaces.grant_service.revoke(actor=actor, grant_id=grant.grant_id)
        remaining = self.surfaces.presentation_service.list_records(
            actor=actor, surface_id=surface_id
        )
        now = self.surfaces.presentation_service.clock()
        if not any(
            item.state in {"issued", "active"} and item.expires_at > now
            for item in remaining
        ):
            descriptor = await self.surfaces.service.get(
                actor=actor, surface_id=surface_id
            )
            if descriptor.lifecycle in {
                SurfaceLifecycle.READY,
                SurfaceLifecycle.UNHEALTHY,
            }:
                await self.surfaces.live_apps.stop(
                    actor=actor,
                    surface_id=surface_id,
                    idempotency_key="process-ui-close:"
                    + canonical_digest({"presentation_id": presentation_id}),
                )
