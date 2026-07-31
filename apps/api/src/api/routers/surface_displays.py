"""Execution-authenticated display ingestion and durable-output deletion."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from api.composition import surface_application
from api.schemas.surfaces import SurfaceDescriptorResponse
from workspace_service.surfaces.display_service import (
    DisplayContractError,
    DisplayDeletionNotConfirmed,
    DisplayExecutionContext,
    DisplayRevisionConflict,
    DisplayService,
)
from workspace_service.surfaces.display_tokens import (
    DisplayExecutionClaims,
    DisplayExecutionTokenService,
    DisplayTokenRejected,
)


router = APIRouter(prefix="/surfaces")
DISPLAY_AUDIENCE = "wright-display-ingest-v1"


def get_display_service() -> DisplayService:
    return surface_application().display_service


def get_display_token_service() -> DisplayExecutionTokenService:
    return surface_application().display_tokens


def _claims(
    authorization: str | None,
    workspace_id: str,
    tokens: DisplayExecutionTokenService,
) -> DisplayExecutionClaims:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Display bearer token required")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Display bearer token required")
    try:
        return tokens.validate(
            token, audience=DISPLAY_AUDIENCE, workspace_id=workspace_id
        )
    except DisplayTokenRejected as error:
        raise HTTPException(status_code=401, detail=str(error)) from error


def _context(claims: DisplayExecutionClaims) -> DisplayExecutionContext:
    return DisplayExecutionContext(
        user_id=claims.user_id,
        workspace_id=claims.workspace_id,
        session_id=claims.session_id,
        task_id=claims.task_id,
        execution_id=claims.execution_id,
        prompt=claims.prompt,
        no_prompt=claims.prompt is None,
        effective_constraints=dict(claims.effective_constraints),
        script=claims.script,
        script_revision=claims.script_revision,
        trace_id=claims.trace_id,
    )


def _control_context(
    *,
    request: Request,
    workspace_id: str,
    session_id: str | None,
    authorization: str | None,
    tokens: DisplayExecutionTokenService,
) -> DisplayExecutionContext:
    if authorization and authorization.startswith("Bearer "):
        return _context(_claims(authorization, workspace_id, tokens))
    user_id = getattr(request.state, "principal_id", None)
    role = getattr(request.state, "principal_role", None)
    if not user_id or role not in {None, "engineer", "admin"} or not session_id:
        raise HTTPException(status_code=401, detail="Authenticated surface user required")
    return DisplayExecutionContext(
        user_id=str(user_id),
        workspace_id=workspace_id,
        session_id=session_id,
        task_id="control-plane",
        execution_id="control-plane",
        prompt=None,
        no_prompt=True,
        effective_constraints={},
        script="control-plane",
        script_revision=1,
        trace_id=getattr(request.state, "trace_id", "no-active-trace"),
    )


@router.post("/displays")
def ingest_display(
    body: Annotated[
        dict[str, Any],
        Body(media_type="application/vnd.wright.display+json"),
    ],
    service: Annotated[DisplayService, Depends(get_display_service)],
    tokens: Annotated[
        DisplayExecutionTokenService, Depends(get_display_token_service)
    ],
    workspace_id: Annotated[
        str, Header(alias="X-Wright-Workspace-ID", min_length=1, max_length=128)
    ],
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=16, max_length=128)
    ],
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> JSONResponse:
    claims = _claims(authorization, workspace_id, tokens)
    if body.get("idempotencyKey") != idempotency_key:
        raise HTTPException(
            status_code=422,
            detail="Idempotency-Key must match the display envelope",
        )
    try:
        result = service.ingest(body, context=_context(claims))
    except DisplayContractError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except DisplayRevisionConflict as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    payload = SurfaceDescriptorResponse.from_domain(result.descriptor).model_dump(
        mode="json", by_alias=True, exclude_none=True
    )
    return JSONResponse(status_code=201 if result.created else 200, content=payload)


@router.delete("/{surface_id}/display")
def delete_display(
    surface_id: str,
    request: Request,
    service: Annotated[DisplayService, Depends(get_display_service)],
    tokens: Annotated[
        DisplayExecutionTokenService, Depends(get_display_token_service)
    ],
    workspace_id: Annotated[
        str, Header(alias="X-Wright-Workspace-ID", min_length=1, max_length=128)
    ],
    retention_disclosure_confirmed: Annotated[
        bool, Query(alias="retentionDisclosureConfirmed")
    ],
    session_id: Annotated[
        str | None, Header(alias="X-Wright-Session-ID", max_length=128)
    ] = None,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> dict[str, Any]:
    context = _control_context(
        request=request,
        workspace_id=workspace_id,
        session_id=session_id,
        authorization=authorization,
        tokens=tokens,
    )
    try:
        result = service.delete(
            surface_id=surface_id,
            context=context,
            retention_disclosure_confirmed=retention_disclosure_confirmed,
        )
    except DisplayDeletionNotConfirmed as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Display surface not found") from error
    return {
        "deleted": result.deleted,
        "recoverable": result.recoverable,
        "retentionStatus": result.retention_status,
    }


@router.get("/{surface_id}/display")
def get_display(
    surface_id: str,
    request: Request,
    service: Annotated[DisplayService, Depends(get_display_service)],
    tokens: Annotated[
        DisplayExecutionTokenService, Depends(get_display_token_service)
    ],
    workspace_id: Annotated[str, Header(alias="X-Wright-Workspace-ID")],
    session_id: Annotated[
        str | None, Header(alias="X-Wright-Session-ID", max_length=128)
    ] = None,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> dict[str, Any]:
    context = _control_context(
        request=request,
        workspace_id=workspace_id,
        session_id=session_id,
        authorization=authorization,
        tokens=tokens,
    )
    try:
        return service.display_projection(surface_id=surface_id, context=context)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Display surface not found") from error


@router.get("/{surface_id}/history")
def get_display_history(
    surface_id: str,
    request: Request,
    service: Annotated[DisplayService, Depends(get_display_service)],
    tokens: Annotated[
        DisplayExecutionTokenService, Depends(get_display_token_service)
    ],
    workspace_id: Annotated[str, Header(alias="X-Wright-Workspace-ID")],
    session_id: Annotated[
        str | None, Header(alias="X-Wright-Session-ID", max_length=128)
    ] = None,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> dict[str, Any]:
    context = _control_context(
        request=request,
        workspace_id=workspace_id,
        session_id=session_id,
        authorization=authorization,
        tokens=tokens,
    )
    try:
        return {"items": service.surface_history(surface_id=surface_id, context=context)}
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Display surface not found") from error


@router.get("/{surface_id}/verification")
def get_display_verification(
    surface_id: str,
    request: Request,
    service: Annotated[DisplayService, Depends(get_display_service)],
    tokens: Annotated[
        DisplayExecutionTokenService, Depends(get_display_token_service)
    ],
    workspace_id: Annotated[str, Header(alias="X-Wright-Workspace-ID")],
    session_id: Annotated[
        str | None, Header(alias="X-Wright-Session-ID", max_length=128)
    ] = None,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> dict[str, Any]:
    context = _control_context(
        request=request,
        workspace_id=workspace_id,
        session_id=session_id,
        authorization=authorization,
        tokens=tokens,
    )
    try:
        return service.verify_artifact(surface_id=surface_id, context=context)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Display surface not found") from error
