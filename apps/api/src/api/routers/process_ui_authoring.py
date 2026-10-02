"""Native authoring and fixed managed presentation over existing owners."""

import asyncio

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import StreamingResponse

from agent_adapters.base import AgentInvocationCapabilities
from api.composition import surface_application
from api.routers.workspace import get_workspace_service
from api.schemas.process_interfaces import (
    ProcessUIAuthoringRequest,
    ProcessUISaveRequest,
    ProcessUIActivateRequest,
    ProcessUIPresentRequest,
    ProcessUIPreviewRequest,
    ProcessUICloseRequest,
    ProcessUIStartReceiptRequest,
    ProcessSourceRequest,
)
from api.schemas.surfaces import SurfaceDescriptorResponse
from core.process_validation import Digest, Identifier
from core.process_interactions import Locator
from core.surfaces.models import LiveAppSurfaceSource, LiveAppOwnership, SurfaceId
from core.surfaces.errors import SurfaceError
from workspace_service.surfaces.live_app_service import LiveAppControlError
from workspace_service.process_interfaces.authoring import (
    NativeAuthoringScope,
    ProcessInterfaceAuthoring,
)
from workspace_service.process_interfaces.compatibility import (
    check_interface_compatibility,
)
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.process_interfaces.presentation import (
    ProcessInterfacePresentations,
)
from workspace_service.process_interfaces.toolchain import discover_build_toolchain
from workspace_service.surfaces.service import SurfaceActor, ActorRole

router = APIRouter()
AUTHORING_OBSERVER_SECONDS = 300


class _UnavailableRole:
    async def get_invocation_capabilities(self):
        return AgentInvocationCapabilities(
            adapter="unavailable",
            available=False,
            reason="The configured agent does not expose the qualified interface-authoring role.",
        )


def get_process_ui_authoring(request: Request, service=Depends(get_workspace_service)):
    application = service.process_interfaces
    existing = application.__dict__.get("_authoring")
    if existing is not None:
        return existing
    engine = getattr(request.app.state, "agent_engine", None)
    toolchain = discover_build_toolchain()
    if engine is None or not callable(
        getattr(engine, "get_invocation_capabilities", None)
    ):
        # Durable status/cancellation still reconcile without a model. Do not
        # activate broad agent chat or cache an unavailable engine forever.
        return ProcessInterfaceAuthoring(application, _UnavailableRole(), toolchain)
    return application.configure_authoring(engine, toolchain)


def get_process_ui_surfaces():
    return surface_application()


def _context(request, service, source):
    from api.routers.process_interfaces import _native_context

    application, scope, process = _native_context(
        request, service, source.session_id, source.path, source.expected_storage_digest
    )
    return application, NativeAuthoringScope(scope, True), process


def _error(error):
    from api.routers.process_interfaces import _transport_error

    if isinstance(error, (KeyError, ValueError)):
        error = ProcessInterfaceError(
            "UI_INCOMPATIBLE",
            "The requested interface record is unavailable or changed.",
            "Reload its saved revision or use the common working view.",
        )
    return _transport_error(error)


def _actor(request, scope, session_id):
    # Same principal as native process commands; legacy surfaces' compatibility
    # fallback is intentionally not substituted into durable process identity.
    role = getattr(request.state, "principal_role", None) or ActorRole.ADMIN
    return SurfaceActor(
        user_id=scope.principal_id,
        workspace_id=scope.workspace_id,
        session_id=session_id,
        role=role,
    )


def _ui(application, scope, process, ui_id):
    scope.require(process, "process.read")
    ui = application.interfaces.get_ui(process.workspace_id, ui_id)
    if ui.archived or ui.process.source_path != process.source_path:
        raise ProcessInterfaceError(
            "SCOPE_DENIED",
            "This interface belongs to another process.",
            "Choose an interface from this process's registered workspace.",
        )
    return ui


@router.get("/authoring-capabilities")
async def authoring_capabilities(
    request: Request,
    response: Response,
    session_id: Identifier,
    path: Locator,
    expected_storage_digest: Digest,
    service=Depends(get_workspace_service),
    authoring=Depends(get_process_ui_authoring),
):
    response.headers["Cache-Control"] = "no-store"
    application, scope, process = _context(
        request,
        service,
        ProcessSourceRequest(
            session_id=session_id,
            path=path,
            expected_storage_digest=expected_storage_digest,
        ),
    )
    try:
        await application.resolve_process(scope.process_scope, process)
        result = await authoring.capabilities()
        return result | {
            "process": process,
            "available_process_capabilities": sorted(scope.process_scope.capabilities),
        }
    except ProcessInterfaceError as error:
        raise _error(error) from error


@router.post("/authoring-jobs", status_code=202)
async def create_authoring_job(
    body: ProcessUIAuthoringRequest,
    request: Request,
    response: Response,
    service=Depends(get_workspace_service),
    authoring=Depends(get_process_ui_authoring),
):
    response.headers["Cache-Control"] = "no-store"
    _, scope, process = _context(request, service, body)
    try:
        return await authoring.submit(
            scope,
            process,
            body.request_id,
            body.instruction,
            title=body.title,
            ui_id=body.ui_id,
            base_revision=body.base_revision,
        )
    except (ProcessInterfaceError, KeyError, ValueError) as error:
        raise _error(error) from error


@router.get("/authoring-jobs/{job_id}")
async def authoring_job(
    job_id: Identifier,
    request: Request,
    response: Response,
    session_id: Identifier,
    path: Locator,
    expected_storage_digest: Digest,
    service=Depends(get_workspace_service),
    authoring=Depends(get_process_ui_authoring),
):
    response.headers["Cache-Control"] = "no-store"
    application, scope, process = _context(
        request,
        service,
        ProcessSourceRequest(
            session_id=session_id,
            path=path,
            expected_storage_digest=expected_storage_digest,
        ),
    )
    try:
        job = await authoring.status(scope, process, job_id)
        built = None
        if job.state in {"preview_ready", "saved"}:
            _, manifest, report, _, _ = application.ui_revisions.preview_bundle(
                scope.process_scope, process, job_id
            )
            ui = application.interfaces.get_ui(process.workspace_id, manifest.ui_id)
            try:
                observation = application.interfaces.get_authoring_record(
                    process.workspace_id, job_id, "preview"
                )
            except KeyError:
                observation = None
            built = {
                "manifest": manifest,
                "build": report,
                "active_revision": ui.active_revision,
                "previewed_at": observation["previewed_at"] if observation else None,
            }
        return {"job": job, "preview": built}
    except (ProcessInterfaceError, KeyError, ValueError) as error:
        raise _error(error) from error


@router.get("/authoring-jobs/{job_id}/events")
async def authoring_events(
    job_id: Identifier,
    request: Request,
    session_id: Identifier,
    path: Locator,
    expected_storage_digest: Digest,
    service=Depends(get_workspace_service),
    authoring=Depends(get_process_ui_authoring),
):
    _, scope, process = _context(
        request,
        service,
        ProcessSourceRequest(
            session_id=session_id,
            path=path,
            expected_storage_digest=expected_storage_digest,
        ),
    )
    try:
        first = await authoring.status(scope, process, job_id)
    except (ProcessInterfaceError, KeyError, ValueError) as error:
        raise _error(error) from error

    async def observed():
        job, prior = first, None
        # This stream is an observer. Disconnect does not cancel generation.
        deadline = asyncio.get_running_loop().time() + AUTHORING_OBSERVER_SECONDS
        while asyncio.get_running_loop().time() < deadline:
            if await request.is_disconnected():
                return
            data = job.model_dump_json()
            if data != prior:
                yield "event: authoring\ndata: " + data + "\n\n"
                prior = data
            if job.state in {"preview_ready", "saved", "failed", "cancelled"}:
                return
            await asyncio.sleep(0.25)
            try:
                job = await authoring.status(scope, process, job_id)
            except (ProcessInterfaceError, KeyError, ValueError):
                yield 'event: reconciliation\ndata: {"reason":"authoring_status_unavailable"}\n\n'
                return
        yield 'event: reconciliation\ndata: {"reason":"observer_expired"}\n\n'

    return StreamingResponse(
        observed(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


@router.post("/authoring-jobs/{job_id}/cancel")
async def cancel_authoring_job(
    job_id: Identifier,
    body: ProcessSourceRequest,
    request: Request,
    response: Response,
    service=Depends(get_workspace_service),
    authoring=Depends(get_process_ui_authoring),
):
    response.headers["Cache-Control"] = "no-store"
    _, scope, process = _context(request, service, body)
    try:
        return await authoring.cancel(scope, process, job_id)
    except (ProcessInterfaceError, KeyError, ValueError) as error:
        raise _error(error) from error


@router.post("/uis/{ui_id}/revisions/{revision_id}/save")
async def save_interface(
    ui_id: Identifier,
    revision_id: Identifier,
    body: ProcessUISaveRequest,
    request: Request,
    response: Response,
    service=Depends(get_workspace_service),
):
    response.headers["Cache-Control"] = "no-store"
    application, scope, process = _context(request, service, body)
    try:
        job = application.interfaces.job_for_revision(
            process.workspace_id, ui_id, revision_id
        )
        if job.job_id != body.job_id:
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "This save identifies a different built job.",
                "Open the exact preview and its revision.",
            )
        return await application.ui_revisions.save(
            scope,
            process,
            body.job_id,
            expected_source_digest=body.source_digest,
            expected_manifest_digest=body.manifest_digest,
            expected_bundle_digest=body.bundle_digest,
            expected_active_revision=body.expected_active_revision,
        )
    except (ProcessInterfaceError, KeyError, ValueError) as error:
        raise _error(error) from error


@router.post("/uis/{ui_id}/activate")
async def activate_interface(
    ui_id: Identifier,
    body: ProcessUIActivateRequest,
    request: Request,
    response: Response,
    service=Depends(get_workspace_service),
):
    response.headers["Cache-Control"] = "no-store"
    application, scope, process = _context(request, service, body)
    try:
        return await application.ui_revisions.activate(
            scope,
            process,
            ui_id,
            body.revision_id,
            expected_active_revision=body.expected_active_revision,
        )
    except (ProcessInterfaceError, KeyError, ValueError) as error:
        raise _error(error) from error


@router.get("/uis/{ui_id}/compatibility")
async def interface_compatibility(
    ui_id: Identifier,
    request: Request,
    response: Response,
    session_id: Identifier,
    path: Locator,
    expected_storage_digest: Digest,
    revision_id: Identifier | None = None,
    service=Depends(get_workspace_service),
):
    response.headers["Cache-Control"] = "no-store"
    application, author, process = _context(
        request,
        service,
        ProcessSourceRequest(
            session_id=session_id,
            path=path,
            expected_storage_digest=expected_storage_digest,
        ),
    )
    try:
        ui = _ui(application, author.process_scope, process, ui_id)
        revision = application.interfaces.get_revision(
            process.workspace_id, ui_id, revision_id or ui.active_revision
        )
        application.ui_revisions.saved_source(
            author.process_scope, revision.manifest.process, revision
        )
        return await check_interface_compatibility(
            application, author.process_scope, process, revision
        )
    except (ProcessInterfaceError, KeyError, ValueError) as error:
        raise _error(error) from error


@router.get("/uis")
async def list_interfaces(
    request: Request,
    response: Response,
    session_id: Identifier,
    path: Locator,
    expected_storage_digest: Digest,
    service=Depends(get_workspace_service),
):
    response.headers["Cache-Control"] = "no-store"
    application, author, process = _context(
        request,
        service,
        ProcessSourceRequest(
            session_id=session_id,
            path=path,
            expected_storage_digest=expected_storage_digest,
        ),
    )
    try:
        await application.resolve_process(author.process_scope, process)
        return {
            "interfaces": [
                ui
                for ui in application.interfaces.list_uis(
                    process.workspace_id, process.source_path
                )
                if not ui.archived
            ]
        }
    except (ProcessInterfaceError, KeyError, ValueError) as error:
        raise _error(error) from error


@router.get("/uis/{ui_id}/revisions")
async def list_interface_revisions(
    ui_id: Identifier,
    request: Request,
    response: Response,
    session_id: Identifier,
    path: Locator,
    expected_storage_digest: Digest,
    service=Depends(get_workspace_service),
):
    response.headers["Cache-Control"] = "no-store"
    application, author, process = _context(
        request,
        service,
        ProcessSourceRequest(
            session_id=session_id,
            path=path,
            expected_storage_digest=expected_storage_digest,
        ),
    )
    try:
        await application.resolve_process(author.process_scope, process)
        _ui(application, author.process_scope, process, ui_id)
        return {
            "revisions": application.interfaces.list_revisions(
                process.workspace_id, ui_id
            )
        }
    except (ProcessInterfaceError, KeyError, ValueError) as error:
        raise _error(error) from error


def _presentation_payload(value):
    from api.routers.surface_presentations import _launch_payload

    return {
        "descriptor": SurfaceDescriptorResponse.from_domain(value["descriptor"]),
        "launch": _launch_payload(value["launch"]),
        "binding": value["binding"],
        "job_id": value["job_id"],
        "build": value["build"],
    }


@router.post("/authoring-jobs/{job_id}/preview")
async def preview_interface(
    job_id: Identifier,
    body: ProcessUIPreviewRequest,
    request: Request,
    response: Response,
    service=Depends(get_workspace_service),
    surfaces=Depends(get_process_ui_surfaces),
):
    response.headers["Cache-Control"] = "no-store"
    application, author, process = _context(request, service, body)
    try:
        value = await ProcessInterfacePresentations(application, surfaces).open(
            author.process_scope,
            process,
            _actor(request, author.process_scope, body.session_id),
            job_id,
            body.request_id,
            read_only=True,
            run_id=body.run_id,
        )
        return _presentation_payload(value)
    except (ProcessInterfaceError, KeyError, ValueError) as error:
        raise _error(error) from error


@router.post("/uis/{ui_id}/present")
async def present_interface(
    ui_id: Identifier,
    body: ProcessUIPresentRequest,
    request: Request,
    response: Response,
    service=Depends(get_workspace_service),
    surfaces=Depends(get_process_ui_surfaces),
):
    response.headers["Cache-Control"] = "no-store"
    application, author, process = _context(request, service, body)
    try:
        ui = _ui(application, author.process_scope, process, ui_id)
        revision_id = body.revision_id or ui.active_revision
        if revision_id is None:
            raise ProcessInterfaceError(
                "UI_INCOMPATIBLE",
                "This interface has no saved revision.",
                "Open and save its built preview first.",
            )
        job = application.interfaces.job_for_revision(
            process.workspace_id, ui_id, revision_id
        )
        value = await ProcessInterfacePresentations(application, surfaces).open(
            author.process_scope,
            process,
            _actor(request, author.process_scope, body.session_id),
            job.job_id,
            body.request_id,
            read_only=False,
            run_id=body.run_id,
        )
        return _presentation_payload(value)
    except (ProcessInterfaceError, KeyError, ValueError) as error:
        raise _error(error) from error


@router.get("/uis/{ui_id}/runtime-diagnostics")
async def interface_runtime_diagnostics(
    ui_id: Identifier,
    request: Request,
    response: Response,
    session_id: Identifier,
    path: Locator,
    expected_storage_digest: Digest,
    revision_id: Identifier,
    surface_id: Identifier,
    after_sequence: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    service=Depends(get_workspace_service),
    surfaces=Depends(get_process_ui_surfaces),
):
    """Read the existing runtime/log owners under exact native process/UI scope."""
    response.headers["Cache-Control"] = "no-store"
    application, author, process = _context(
        request,
        service,
        ProcessSourceRequest(
            session_id=session_id,
            path=path,
            expected_storage_digest=expected_storage_digest,
        ),
    )
    try:
        _ui(application, author.process_scope, process, ui_id)
        job = application.interfaces.job_for_revision(
            process.workspace_id, ui_id, revision_id
        )
        # Verify immutable provenance even for a built preview that never saved.
        application.ui_revisions.preview_bundle(
            author.process_scope, process, job.job_id
        )
        actor = _actor(request, author.process_scope, session_id)
        descriptor = await surfaces.service.get(
            actor=actor, surface_id=SurfaceId(surface_id)
        )
        if (
            not isinstance(descriptor.source, LiveAppSurfaceSource)
            or descriptor.source.ownership != LiveAppOwnership.WRIGHT_OWNED
            or descriptor.source.manifest_id != f"process.{ui_id}.{revision_id}"
        ):
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "This runtime does not belong to the requested interface revision.",
                "Inspect the exact interface in its owning process and workspace.",
            )
        try:
            runtime = await surfaces.live_apps.inspect(
                actor=actor, surface_id=descriptor.surface_id
            )
        except LiveAppControlError as error:
            if error.code != "SURFACE_INSTANCE_NOT_FOUND":
                raise
            # Startup reconciliation revokes old runtime authority. Its scoped
            # descriptor is evidence of that reconciliation, not a live probe
            # or a reconstruction of the original startup failure.
            return {
                "process": process,
                "ui_id": ui_id,
                "revision_id": revision_id,
                "surface_id": surface_id,
                "state": descriptor.lifecycle,
                "state_source": "surface-reconciliation",
                "generation": None,
                "failure": descriptor.diagnostic_summary,
                "last_health": None,
                "logs": None,
                "logs_unavailable": "SURFACE_INSTANCE_NOT_FOUND",
            }
        logs_unavailable = None
        try:
            logs = await surfaces.live_apps.logs(
                actor=actor,
                surface_id=descriptor.surface_id,
                after_sequence=after_sequence,
                limit=limit,
            )
        except LiveAppControlError as error:
            if error.code != "SURFACE_LOGS_UNAVAILABLE":
                raise
            # Runtime state remains useful after restart, when the owner's
            # bounded in-memory log buffer is no longer available.
            logs = None
            logs_unavailable = "SURFACE_LOGS_UNAVAILABLE"
        return {
            "process": process,
            "ui_id": ui_id,
            "revision_id": revision_id,
            "surface_id": surface_id,
            "state": runtime.state,
            "state_source": "runtime-owner",
            "generation": runtime.generation,
            "failure": runtime.failure,
            "last_health": runtime.last_health,
            "logs": logs,
            "logs_unavailable": logs_unavailable,
        }
    except SurfaceError:
        raise _error(
            ProcessInterfaceError(
                "SCOPE_DENIED",
                "This runtime is unavailable in the authorized interface scope.",
                "Choose its exact saved interface in the owning workspace.",
            )
        ) from None
    except LiveAppControlError as error:
        raise _error(
            ProcessInterfaceError(
                "CAPABILITY_UNAVAILABLE",
                "Wright could not read this managed interface's diagnostics.",
                "Use the common working view and reconcile its managed runtime.",
                details={"runtime_code": error.code},
            )
        ) from None
    except (ProcessInterfaceError, KeyError, ValueError) as error:
        raise _error(error) from error


@router.post("/presentations/close", status_code=204)
async def close_interface(
    body: ProcessUICloseRequest,
    request: Request,
    service=Depends(get_workspace_service),
    surfaces=Depends(get_process_ui_surfaces),
):
    application, author, _ = _context(request, service, body)
    try:
        await ProcessInterfacePresentations(application, surfaces).close(
            author.process_scope,
            _actor(request, author.process_scope, body.session_id),
            body.surface_id,
            body.presentation_id,
        )
        return Response(status_code=204, headers={"Cache-Control": "no-store"})
    except (ProcessInterfaceError, KeyError, ValueError) as error:
        raise _error(error) from error


@router.post("/presentations/start-receipt")
async def presentation_start_receipt(
    body: ProcessUIStartReceiptRequest,
    request: Request,
    response: Response,
    service=Depends(get_workspace_service),
    surfaces=Depends(get_process_ui_surfaces),
):
    response.headers["Cache-Control"] = "no-store"
    application, author, process = _context(request, service, body)
    try:
        receipt = await ProcessInterfacePresentations(
            application, surfaces
        ).start_receipt(
            author.process_scope,
            process,
            _actor(request, author.process_scope, body.session_id),
            body.surface_id,
            body.presentation_id,
            request_id=body.request_id,
        )
        return {"receipt": receipt}
    except (ProcessInterfaceError, KeyError, ValueError) as error:
        raise _error(error) from error
