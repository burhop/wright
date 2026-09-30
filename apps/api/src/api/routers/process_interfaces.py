"""Authenticated native transport over the owning process interface service."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from api.routers.workspace import (
    _require_process_validation_role,
    _workflow_source_scope,
    get_workspace_service,
)
from api.schemas.process_interfaces import (
    SetProcessInputsRequest,
    ProcessReadinessRequest,
)
from core.process_interactions import (
    InputSnapshot,
    InteractionSnapshot,
    ProcessRef,
    Readiness,
    Locator,
)
from core.process_validation import Digest, Identifier
from core.tracing import traced
from workspace_service import WorkspaceService
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.process_interfaces.service import ProcessScope

router = APIRouter(dependencies=[Depends(_require_process_validation_role)])


def _native_context(request, service, session_id, path, digest):
    bound = _workflow_source_scope(session_id, service)
    # Local control-plane authentication currently has one administrator token.
    # A supplied actor is never accepted; richer auth may provide its own ID.
    principal = getattr(request.state, "principal_id", None) or "local-control-plane"
    scope = ProcessScope(
        principal,
        bound.workspace_id,
        frozenset(
            {
                "process.read",
                "process.inputs",
                "process.results",
                "process.navigate",
            }
        ),
    )
    process = ProcessRef(
        workspace_id=bound.workspace_id, source_path=path, source_digest=digest
    )
    return service.process_interfaces, scope, process


def _transport_error(error: ProcessInterfaceError):
    code = error.reason.code
    status = (
        403
        if code in {"SCOPE_DENIED", "ACTION_NOT_PERMITTED", "PRESENTATION_EXPIRED"}
        else 409
        if code
        in {
            "SOURCE_CHANGED",
            "SUBJECT_STALE",
            "OPTION_STALE",
            "REQUEST_CONFLICT",
            "UI_INCOMPATIBLE",
        }
        else 503
        if code in {"CAPABILITY_UNAVAILABLE", "OUTCOME_UNKNOWN"}
        else 422
    )
    return HTTPException(
        status_code=status,
        detail={
            "code": code,
            "message": error.reason.message,
            "correction": error.reason.correction,
            "reason": error.reason.model_dump(mode="json"),
            "diagnostic": error.diagnostic,
        },
    )


@router.get("/interaction", response_model=InteractionSnapshot)
@traced("api.process.interface.snapshot")
async def interaction_snapshot(
    request: Request,
    response: Response,
    session_id: Identifier,
    path: Locator,
    expected_storage_digest: Digest,
    run_id: Identifier | None = None,
    input_snapshot_id: Identifier | None = None,
    page: str | None = Query(default=None, max_length=256),
    service: WorkspaceService = Depends(get_workspace_service),
):
    response.headers["Cache-Control"] = "no-store"
    application, scope, process = _native_context(
        request, service, session_id, path, expected_storage_digest
    )
    try:
        return await application.get_snapshot(
            scope,
            process,
            run_id=run_id,
            input_snapshot_id=input_snapshot_id,
            page=page,
            gateway=getattr(request.app.state, "gateway_service", None),
            session_id=session_id,
        )
    except ProcessInterfaceError as error:
        raise _transport_error(error) from error


@router.post("/inputs", response_model=InputSnapshot)
@traced("api.process.interface.inputs")
async def set_process_inputs(
    body: SetProcessInputsRequest,
    request: Request,
    response: Response,
    service: WorkspaceService = Depends(get_workspace_service),
):
    response.headers["Cache-Control"] = "no-store"
    application, scope, process = _native_context(
        request, service, body.session_id, body.path, body.expected_storage_digest
    )
    try:
        prepared = await application.set_inputs(
            scope,
            process,
            bindings=body.bindings,
            gateway=getattr(request.app.state, "gateway_service", None),
            session_id=body.session_id,
        )
        return prepared.snapshot
    except ProcessInterfaceError as error:
        raise _transport_error(error) from error


@router.post("/readiness", response_model=Readiness)
@traced("api.process.interface.readiness")
async def process_readiness(
    body: ProcessReadinessRequest,
    request: Request,
    response: Response,
    service: WorkspaceService = Depends(get_workspace_service),
):
    response.headers["Cache-Control"] = "no-store"
    application, scope, process = _native_context(
        request, service, body.session_id, body.path, body.expected_storage_digest
    )
    try:
        return await application.check_readiness(
            scope,
            process,
            body.input_snapshot_id,
            gateway=getattr(request.app.state, "gateway_service", None),
            session_id=body.session_id,
        )
    except ProcessInterfaceError as error:
        raise _transport_error(error) from error
