"""Thin authenticated HTTP routes for the Engineering Models library."""

from __future__ import annotations

import json

from fastapi import (
    APIRouter,
    Depends,
    File,
    Header,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from tool_registry.model_library_port import (
    EngineeringModelApplicationPort,
    EngineeringModelPortError,
)

from api.schemas.engineering_models import (
    EngineeringModelListResponse,
    EngineeringModelResponse,
    ModelOperationEventResponse,
    ModelOperationResponse,
    ModelPlanConfirmationRequest,
    ModelPlanRequest,
    ModelPlanResponse,
    ModelRuntimeTestResponse,
    ModelWorkspaceBindingRequest,
    ModelWorkspaceBindingResponse,
    ModelWorkspaceBindingStateRequest,
)

router = APIRouter()


def require_engineer_or_admin(request: Request) -> None:
    settings = request.app.state.security_settings
    if not settings.enforced:
        return
    if getattr(request.state, "principal_role", None) not in {"engineer", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Engineer or administrator role required",
        )


def get_engineering_model_application(
    request: Request,
) -> EngineeringModelApplicationPort:
    application = getattr(request.app.state, "engineering_model_application", None)
    if application is not None:
        return application
    from api.composition import engineering_model_application

    return engineering_model_application()


def _port_error(error: EngineeringModelPortError) -> HTTPException:
    if error.category in {"model_not_found", "plan_not_found", "operation_not_found"}:
        status_code = 404
    elif error.category in {
        "plan_invalidated",
        "plan_blocked",
        "model_not_installable",
    }:
        status_code = 409
    elif error.category in {"insufficient_disk", "size_exceeded"}:
        status_code = 413
    elif error.category in {"source_unavailable", "model_lifecycle_unavailable"}:
        status_code = 503
    else:
        status_code = 400
    return HTTPException(
        status_code=status_code,
        detail={
            "category": error.category,
            "message": str(error),
            "recovery": error.recovery,
        },
    )


def _request_actor(request: Request) -> str:
    return str(getattr(request.state, "principal_id", "local-admin"))


def _request_trace(request: Request) -> str:
    return str(getattr(request.state, "trace_id", "no-active-span"))


@router.get(
    "/catalog",
    response_model=EngineeringModelListResponse,
    dependencies=[Depends(require_engineer_or_admin)],
)
def list_engineering_models(
    search: str | None = Query(default=None, max_length=200),
    task: str | None = Query(default=None, max_length=96),
    source_kind: str | None = Query(default=None, max_length=32),
    readiness: list[str] = Query(default=[]),
    platform: str | None = Query(default=None, max_length=32),
    architecture: str | None = Query(default=None, max_length=32),
    accelerator: str | None = Query(default=None, max_length=32),
    evidence_state: str | None = Query(default=None, max_length=32),
    maximum_bytes: int | None = Query(default=None, ge=0),
    cursor: str | None = Query(default=None, max_length=4096),
    limit: int = Query(default=50, ge=1, le=100),
    application: EngineeringModelApplicationPort = Depends(
        get_engineering_model_application
    ),
):
    try:
        return application.list_catalog(
            search=search,
            task=task,
            source_kind=source_kind,
            readiness=tuple(readiness),
            platform=platform,
            architecture=architecture,
            accelerator=accelerator,
            evidence_state=evidence_state,
            maximum_bytes=maximum_bytes,
            cursor=cursor,
            limit=limit,
        )
    except EngineeringModelPortError as error:
        raise _port_error(error) from error


@router.get(
    "/catalog/{model_id}",
    response_model=EngineeringModelResponse,
    dependencies=[Depends(require_engineer_or_admin)],
)
def get_engineering_model(
    model_id: str,
    application: EngineeringModelApplicationPort = Depends(
        get_engineering_model_application
    ),
):
    try:
        return application.get_catalog_model(model_id)
    except EngineeringModelPortError as error:
        raise _port_error(error) from error
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail={
                "category": "model_not_found",
                "message": "Engineering model is not present in this snapshot.",
                "recovery": "Choose a model from the active offline catalog snapshot.",
            },
        ) from error


@router.post(
    "/plans",
    response_model=ModelPlanResponse,
    dependencies=[Depends(require_engineer_or_admin)],
)
def create_engineering_model_plan(
    body: ModelPlanRequest,
    request: Request,
    application: EngineeringModelApplicationPort = Depends(
        get_engineering_model_application
    ),
):
    try:
        return application.create_plan(
            **body.model_dump(), principal_id=_request_actor(request)
        )
    except EngineeringModelPortError as error:
        raise _port_error(error) from error


@router.post(
    "/imports",
    response_model=ModelPlanResponse,
    dependencies=[Depends(require_engineer_or_admin)],
)
async def create_engineering_model_import_plan(
    request: Request,
    package: UploadFile = File(...),
    application: EngineeringModelApplicationPort = Depends(
        get_engineering_model_application
    ),
):
    maximum = 256 * 1024 * 1024
    content = bytearray()
    while chunk := await package.read(1024 * 1024):
        content.extend(chunk)
        if len(content) > maximum:
            raise HTTPException(
                status_code=413,
                detail={
                    "category": "size_exceeded",
                    "message": "The offline package exceeds the 256 MiB upload ceiling.",
                    "recovery": "Choose a smaller reviewed package.",
                },
            )
    try:
        return application.create_import_plan(
            archive=bytes(content), principal_id=_request_actor(request)
        )
    except EngineeringModelPortError as error:
        raise _port_error(error) from error


@router.get(
    "/plans/{plan_id}",
    response_model=ModelPlanResponse,
    dependencies=[Depends(require_engineer_or_admin)],
)
def get_engineering_model_plan(
    plan_id: str,
    request: Request,
    application: EngineeringModelApplicationPort = Depends(
        get_engineering_model_application
    ),
):
    try:
        return application.get_plan(plan_id, principal_id=_request_actor(request))
    except EngineeringModelPortError as error:
        raise _port_error(error) from error


@router.post(
    "/plans/{plan_id}/confirm",
    response_model=ModelOperationResponse,
    dependencies=[Depends(require_engineer_or_admin)],
)
def confirm_engineering_model_plan(
    plan_id: str,
    body: ModelPlanConfirmationRequest,
    request: Request,
    application: EngineeringModelApplicationPort = Depends(
        get_engineering_model_application
    ),
):
    try:
        return application.confirm_plan(
            plan_id,
            principal_id=_request_actor(request),
            plan_digest=body.plan_digest,
            trace_id=_request_trace(request),
        )
    except EngineeringModelPortError as error:
        raise _port_error(error) from error


@router.get(
    "/operations/{operation_id}",
    response_model=ModelOperationResponse,
    dependencies=[Depends(require_engineer_or_admin)],
)
def get_engineering_model_operation(
    operation_id: str,
    request: Request,
    application: EngineeringModelApplicationPort = Depends(
        get_engineering_model_application
    ),
):
    try:
        return application.get_operation(
            operation_id, principal_id=_request_actor(request)
        )
    except EngineeringModelPortError as error:
        raise _port_error(error) from error


@router.post(
    "/operations/{operation_id}/cancel",
    response_model=ModelOperationResponse,
    dependencies=[Depends(require_engineer_or_admin)],
)
def cancel_engineering_model_operation(
    operation_id: str,
    request: Request,
    application: EngineeringModelApplicationPort = Depends(
        get_engineering_model_application
    ),
):
    try:
        return application.cancel_operation(
            operation_id, principal_id=_request_actor(request)
        )
    except EngineeringModelPortError as error:
        raise _port_error(error) from error


@router.get(
    "/operations/{operation_id}/events",
    dependencies=[Depends(require_engineer_or_admin)],
)
def engineering_model_operation_events(
    operation_id: str,
    request: Request,
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    application: EngineeringModelApplicationPort = Depends(
        get_engineering_model_application
    ),
):
    try:
        after = int(last_event_id or 0)
        if not 0 <= after <= 1000:
            raise ValueError
    except ValueError as error:
        raise HTTPException(status_code=400, detail="Invalid event cursor") from error
    try:
        events = application.operation_events(
            operation_id, principal_id=_request_actor(request), after=after
        )
        bounded = tuple(
            ModelOperationEventResponse.model_validate(item).model_dump(
                mode="json", exclude_none=True
            )
            for item in events[:1000]
        )
    except EngineeringModelPortError as error:
        raise _port_error(error) from error

    def stream():
        for event in bounded:
            yield (
                f"id: {event['sequence']}\n"
                "event: operation\n"
                f"data: {json.dumps(event, separators=(',', ':'))}\n\n"
            )

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


@router.post(
    "/installations/{installation_id}/standard-test",
    response_model=ModelRuntimeTestResponse,
    dependencies=[Depends(require_engineer_or_admin)],
)
async def run_engineering_model_standard_test(
    installation_id: str,
    request: Request,
    application: EngineeringModelApplicationPort = Depends(
        get_engineering_model_application
    ),
):
    try:
        return await application.run_standard_test(
            installation_id,
            principal_id=_request_actor(request),
            trace_id=_request_trace(request),
        )
    except EngineeringModelPortError as error:
        raise _port_error(error) from error


@router.get(
    "/installations/{installation_id}/evidence",
    response_model=ModelRuntimeTestResponse,
    dependencies=[Depends(require_engineer_or_admin)],
)
def get_engineering_model_test_evidence(
    installation_id: str,
    request: Request,
    application: EngineeringModelApplicationPort = Depends(
        get_engineering_model_application
    ),
):
    try:
        return application.get_standard_test_evidence(
            installation_id, principal_id=_request_actor(request)
        )
    except EngineeringModelPortError as error:
        raise _port_error(error) from error


@router.post(
    "/workspaces/{workspace_id}/bindings",
    response_model=ModelWorkspaceBindingResponse,
    dependencies=[Depends(require_engineer_or_admin)],
)
def create_engineering_model_workspace_binding(
    workspace_id: str,
    body: ModelWorkspaceBindingRequest,
    request: Request,
    bound_workspace_id: str = Header(
        alias="X-Wright-Workspace-ID", min_length=1, max_length=128
    ),
    application: EngineeringModelApplicationPort = Depends(
        get_engineering_model_application
    ),
):
    if bound_workspace_id != workspace_id:
        raise HTTPException(
            status_code=409,
            detail={
                "category": "invalid_binding",
                "message": "The requested and authenticated workspace identities differ.",
                "recovery": "Reload the target workspace before enabling this capability.",
            },
        )
    try:
        return application.create_workspace_binding(
            body.installation_id,
            task_id=body.task_id,
            workspace_id=workspace_id,
            principal_id=_request_actor(request),
        )
    except EngineeringModelPortError as error:
        raise _port_error(error) from error


@router.patch(
    "/workspaces/{workspace_id}/bindings/{binding_id}",
    response_model=ModelWorkspaceBindingResponse,
    dependencies=[Depends(require_engineer_or_admin)],
)
def set_engineering_model_workspace_binding_state(
    workspace_id: str,
    binding_id: str,
    body: ModelWorkspaceBindingStateRequest,
    request: Request,
    bound_workspace_id: str = Header(
        alias="X-Wright-Workspace-ID", min_length=1, max_length=128
    ),
    application: EngineeringModelApplicationPort = Depends(
        get_engineering_model_application
    ),
):
    if bound_workspace_id != workspace_id:
        raise HTTPException(
            status_code=409,
            detail={
                "category": "invalid_binding",
                "message": "The requested and authenticated workspace identities differ.",
                "recovery": "Reload the target workspace before changing this capability.",
            },
        )
    try:
        return application.set_workspace_binding_state(
            binding_id,
            state=body.state,
            workspace_id=workspace_id,
            principal_id=_request_actor(request),
        )
    except EngineeringModelPortError as error:
        raise _port_error(error) from error


__all__ = ["get_engineering_model_application", "router"]
