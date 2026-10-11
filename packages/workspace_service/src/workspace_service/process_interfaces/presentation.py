"""Native owner of fixed static UI presentation over the existing surface graph.

Opening or closing a view never executes, cancels or approves its process. Model
source supplies no launch command, endpoint, principal or grant authority.
"""

import json
import os
from pathlib import PurePosixPath, PureWindowsPath
import tempfile

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

    async def start_receipt(
        self, scope, process, actor, surface_id, presentation_id, *, request_id=None
    ):
        """Resolve a view's retained start through the existing receipt owner.

        The browser supplies no run identity or input authority. Reading this
        association never resubmits, resumes or cancels an execution.
        """
        from .surface_bridge import presentation_start_key

        self._actor(scope, actor)
        scope.require(process, "process.read")
        try:
            record = self.surfaces.presentation_service.get_record(
                actor=actor, presentation_id=presentation_id
            )
        except PresentationUnavailable:
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "This start belongs to another view.",
                "Reopen the process in its owning workspace.",
            ) from None
        descriptor = await self.surfaces.service.get(actor=actor, surface_id=surface_id)
        if (
            record.surface_id != str(surface_id)
            or record.session_id != actor.session_id
            or record.state not in {"issued", "active"}
            or record.expires_at <= self.surfaces.presentation_service.clock()
            or descriptor.lifecycle is not SurfaceLifecycle.READY
            or descriptor.instance is None
            or descriptor.instance.get("instanceId") != record.instance_id
            or descriptor.instance.get("generation") != record.generation
            or descriptor.source.source_id != record.source_id
            or descriptor.source.source_version != record.source_version
        ):
            raise ProcessInterfaceError(
                "PRESENTATION_EXPIRED",
                "This interface view is no longer current.",
                "Use the common view to reconcile the recorded run.",
            )
        grants = self.surfaces.grant_service.repository.list(
            user_id=actor.user_id,
            workspace_id=actor.workspace_id,
            source_id=record.source_id,
            source_version=record.source_version,
        )
        bindings = {}
        for grant in grants:
            if (
                grant.capability == "process.read"
                and grant.instance_id == record.instance_id
            ):
                binding = ProcessPresentationBinding.model_validate(grant.constraints)
                if (
                    binding.presentation_id == presentation_id
                    and binding.generation == record.generation
                ):
                    bindings[canonical_digest(binding)] = binding
        if len(bindings) != 1:
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "This view has no exact process binding.",
                "Reopen its saved interface.",
            )
        binding = next(iter(bindings.values()))
        if (
            binding.process != process
            or binding.read_only
            or binding.run_id is not None
            or record.source_id != f"process.{binding.ui_id}.{binding.revision_id}"
        ):
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "This view cannot attach a preparation request.",
                "Use its exact process and run view.",
            )
        try:
            self.surfaces.grant_service.authorize(
                actor=actor,
                request=CapabilityRequest(
                    source_id=record.source_id,
                    source_version=record.source_version,
                    instance_id=record.instance_id,
                    capability="process.read",
                    operation="process.read",
                    constraints=binding.model_dump(mode="json"),
                    risk_tier="low",
                    persistence="instance",
                    duration_seconds=600,
                    declared=True,
                    decision="allow",
                    reason="Reconcile the exact view's recorded start.",
                ),
            )
        except CapabilityGrantError:
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "This view's process grant is unavailable.",
                "Reopen its saved interface.",
            ) from None
        job = self.application.interfaces.job_for_revision(
            process.workspace_id, binding.ui_id, binding.revision_id
        )
        try:
            retained = self.application.interfaces.get_authoring_record(
                process.workspace_id,
                job.job_id,
                presentation_start_key(presentation_id),
            )
        except KeyError:
            if request_id is None:
                return None
            raise ProcessInterfaceError(
                "OUTCOME_UNKNOWN",
                "This view has no retained start request.",
                "Reconcile its request in the common view; do not submit another start.",
            ) from None
        if (
            retained.get("binding") != binding.model_dump(mode="json")
            or retained.get("principal_id") != scope.principal_id
            or retained.get("session_id") != actor.session_id
            or retained.get("instance_id") != record.instance_id
            or retained.get("source_version") != record.source_version
            or (request_id is not None and retained.get("request_id") != request_id)
        ):
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "This request does not belong to this view.",
                "Reconcile its exact recorded start.",
            )
        try:
            receipt = self.application.inputs.start_receipt(
                scope.principal_id, process, retained["request_id"]
            )
        except KeyError:
            raise ProcessInterfaceError(
                "OUTCOME_UNKNOWN",
                "The retained request has no confirmed start receipt.",
                "Reconcile that same request; do not submit a new start.",
            ) from None
        expected = canonical_digest(
            {
                "process": process,
                "input_snapshot_id": retained["input_snapshot_id"],
                "input_digest": retained["input_digest"],
                "integration_policy_digest": retained["integration_policy_digest"],
            }
        )
        if receipt.process != process or receipt.payload_digest != expected:
            raise ProcessInterfaceError(
                "SUBJECT_STALE",
                "The start receipt and view association disagree.",
                "Inspect their exact identities before continuing.",
            )
        return receipt

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
            previous = path.read_bytes()
            stored = json.loads(previous)
            current = parse_live_app_manifest(stored)
            if current.canonical_hash != declaration.canonical_hash:
                # These declarations are host-local derived data, not saved UI
                # source. Relocation can change only the interpreter and vault
                # paths. Never execute either stored path, or accept changes to
                # commands, inventory, capabilities, isolation or other policy.
                argv = stored["launch"].get("argv", [])
                expected = value["launch"]["argv"]
                if len(argv) != len(expected):
                    raise ValueError("The fixed managed manifest changed")
                suffix = tuple(PurePosixPath(expected[4].replace("\\", "/")).parts[-5:])
                for index in (0, 4):
                    old = argv[index]
                    if not (
                        PurePosixPath(old).is_absolute()
                        or PureWindowsPath(old).is_absolute()
                    ):
                        raise ValueError("The managed runtime path is not absolute")
                if (
                    tuple(PurePosixPath(argv[4].replace("\\", "/")).parts[-5:])
                    != suffix
                ):
                    raise ValueError("The managed vault identity changed")
                argv[0], argv[4] = expected[0], expected[4]
                if (
                    parse_live_app_manifest(stored).canonical_hash
                    != declaration.canonical_hash
                ):
                    raise ValueError("The fixed managed manifest changed")
                temporary = None
                try:
                    with tempfile.NamedTemporaryFile(
                        mode="w", encoding="utf-8", dir=path.parent, delete=False
                    ) as stream:
                        temporary = stream.name
                        json.dump(value, stream, sort_keys=True)
                    if path.read_bytes() != previous:
                        raise ValueError(
                            "The fixed managed manifest changed during relocation"
                        )
                    os.replace(temporary, path)
                finally:
                    if temporary and os.path.exists(temporary):
                        os.unlink(temporary)
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
        except LiveAppControlError as error:
            capacity = error.code == "SURFACE_LIMIT_OWNED_APPS"
            raise ProcessInterfaceError(
                "CAPABILITY_UNAVAILABLE",
                (
                    "The workspace has reached its open interface limit."
                    if capacity
                    else "Wright could not open the managed process interface."
                ),
                (
                    "Close an unused interface tab, then reopen this saved interface."
                    if capacity
                    else "Use the common view and inspect its managed runtime diagnostics before reopening."
                ),
                details={"runtime_code": error.code, "retryable": error.retryable},
            ) from None
        except (PresentationUnavailable, SurfaceError):
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
            self.application.ui_revisions.presentation_bundle(scope, process, job_id)
        )
        validate_manifest_bindings(
            manifest,
            process,
            accepted_binding_catalog(resolved.document),
            allow_process_revision=True,
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
            self.application.ui_revisions.saved_source(
                scope, manifest.process, revision
            )
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
        await self._reconcile_expired(scope, actor)
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

    async def _reconcile_expired(self, scope, actor):
        """Release expired static views through their existing lifecycle owners.

        A browser can disappear without sending close. Its expired presentation
        must not retain capacity indefinitely. This is scoped to this native
        actor's process views; a live presentation, CAD host or process run is
        never an idle-time inference or a cleanup target.
        """
        now = self.surfaces.presentation_service.clock()
        for descriptor in await self.surfaces.service.list(actor=actor):
            source = descriptor.source
            if (
                not isinstance(source, LiveAppSurfaceSource)
                or source.ownership is not LiveAppOwnership.WRIGHT_OWNED
                or not source.source_id.startswith("process.ui-")
                or descriptor.lifecycle
                not in {SurfaceLifecycle.READY, SurfaceLifecycle.UNHEALTHY}
            ):
                continue
            for record in self.surfaces.presentation_service.list_records(
                actor=actor, surface_id=descriptor.surface_id
            ):
                instance = descriptor.instance or {}
                if (
                    record.expires_at <= now
                    and record.instance_id == instance.get("instanceId")
                    and record.generation == instance.get("generation")
                    and record.source_id == source.source_id
                    and record.source_version == source.source_version
                ):
                    # Include already-closed records so a prior interrupted
                    # runtime stop can reconcile through its idempotent owner.
                    await self._close(
                        scope, actor, descriptor.surface_id, record.presentation_id
                    )

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
            instance = descriptor.instance or {}
            if (
                descriptor.lifecycle
                in {
                    SurfaceLifecycle.READY,
                    SurfaceLifecycle.UNHEALTHY,
                }
                and instance.get("instanceId") == record.instance_id
                and instance.get("generation") == record.generation
                and descriptor.source.source_id == record.source_id
                and descriptor.source.source_version == record.source_version
            ):
                await self.surfaces.live_apps.stop(
                    actor=actor,
                    surface_id=surface_id,
                    idempotency_key="process-ui-close:"
                    + canonical_digest({"presentation_id": presentation_id}),
                )
