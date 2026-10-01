"""Authenticated native transport over the owning process interface service."""

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
from agent_adapters.report_generation import (
    generate_workflow_response,
    decide_workflow_tool_action,
)

from api.routers.workspace import (
    _require_process_validation_role,
    _workflow_source_scope,
    get_workspace_service,
)
from api.schemas.process_interfaces import (
    SetProcessInputsRequest,
    ProcessReadinessRequest,
    ProcessRunRequest,
    ProcessCancelRequest,
)
from core.process_interactions import (
    InputSnapshot,
    InteractionSnapshot,
    ProcessRef,
    Readiness,
    Locator,
    StartReceipt,
    ProcessCancellationReceipt,
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
                "process.start",
                "process.cancel",
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


@router.post("/runs", response_model=StartReceipt, status_code=202)
@traced("api.process.interface.start")
async def start_process_run(
    body: ProcessRunRequest,
    request: Request,
    response: Response,
    service: WorkspaceService = Depends(get_workspace_service),
):
    response.headers["Cache-Control"] = "no-store"
    application, scope, process = _native_context(
        request, service, body.session_id, body.path, body.expected_storage_digest
    )
    try:
        return await application.runs.start(
            scope,
            process,
            body.input_snapshot_id,
            body.request_id,
            expected_input_digest=body.expected_input_digest,
            response_generator=generate_workflow_response,
            action_generator=decide_workflow_tool_action,
            gateway=getattr(request.app.state, "gateway_service", None),
            session_id=body.session_id,
            integration_policy_digest=body.integration_policy_digest,
        )
    except ProcessInterfaceError as error:
        raise _transport_error(error) from error


@router.get("/runs/{run_id}", response_model=InteractionSnapshot)
@traced("api.process.interface.attach")
async def attach_process_run(
    run_id: Identifier,
    request: Request,
    response: Response,
    session_id: Identifier,
    path: Locator,
    expected_storage_digest: Digest,
    page: str | None = Query(default=None, max_length=256),
    service: WorkspaceService = Depends(get_workspace_service),
):
    response.headers["Cache-Control"] = "no-store"
    application, scope, process = _native_context(
        request, service, session_id, path, expected_storage_digest
    )
    try:
        application.runs._receipt(scope, process, run_id)
        return await application.get_snapshot(
            scope,
            process,
            run_id=run_id,
            page=page,
            gateway=getattr(request.app.state, "gateway_service", None),
            session_id=session_id,
        )
    except ProcessInterfaceError as error:
        raise _transport_error(error) from error


@router.get("/runs/{run_id}/events")
@traced("api.process.interface.follow")
async def follow_process_run(
    run_id: Identifier,
    request: Request,
    session_id: Identifier,
    path: Locator,
    expected_storage_digest: Digest,
    cursor: str | None = Query(default=None, max_length=256),
    service: WorkspaceService = Depends(get_workspace_service),
):
    application, scope, process = _native_context(
        request, service, session_id, path, expected_storage_digest
    )
    cursor = cursor or request.headers.get("last-event-id")
    if cursor is not None and len(cursor) > 256:
        raise _transport_error(
            ProcessInterfaceError(
                "SUBJECT_STALE",
                "The progress cursor exceeds its supported size.",
                "Attach to the current run without that cursor.",
            )
        )
    try:
        first = await application.runs.events(scope, process, run_id, cursor=cursor)
    except ProcessInterfaceError as error:
        raise _transport_error(error) from error

    async def observed_events():
        page = first
        while True:
            yield f"id: {page['cursor']}\nevent: progress\ndata: {json.dumps(page, ensure_ascii=False)}\n\n"
            if not page["following"] and not page["has_more"]:
                return
            await asyncio.sleep(0 if page["has_more"] else 0.25)
            try:
                page = await application.runs.events(
                    scope, process, run_id, cursor=page["cursor"]
                )
            except ProcessInterfaceError as error:
                yield (
                    "event: reconciliation\ndata: "
                    + json.dumps(error.reason.model_dump(mode="json"))
                    + "\n\n"
                )
                return

    # The streaming request owns this observer only. The supervisor retains the
    # executor task and durable start identity after ASGI disconnect cancellation.
    return StreamingResponse(
        observed_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-store",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/runs/{run_id}/cancel", response_model=ProcessCancellationReceipt)
@traced("api.process.interface.cancel")
async def cancel_process_run(
    run_id: Identifier,
    body: ProcessCancelRequest,
    request: Request,
    response: Response,
    service: WorkspaceService = Depends(get_workspace_service),
):
    response.headers["Cache-Control"] = "no-store"
    application, scope, process = _native_context(
        request, service, body.session_id, body.path, body.expected_storage_digest
    )
    try:
        return await application.runs.cancel(scope, process, run_id, body.request_id)
    except ProcessInterfaceError as error:
        raise _transport_error(error) from error
