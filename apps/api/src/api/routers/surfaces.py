"""Thin authenticated Workspace Surface control-plane routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from api.composition import surface_application
from api.config import rivet_editor_enabled
from api.schemas.surfaces import (
    DeclareSurfaceRequest,
    SurfaceDescriptorResponse,
    SurfaceListResponse,
    LiveAppDeclareRequest,
    declare_request_to_domain,
)
from core.surfaces.errors import SurfaceError
from core.surfaces.models import SurfaceId
from workspace_service.surfaces.service import ActorRole, SurfaceActor, SurfaceService


router = APIRouter(prefix="/surfaces")


def get_surface_service() -> SurfaceService:
    return surface_application().service


def get_surface_actor(
    request: Request,
    workspace_id: Annotated[str, Header(alias="X-Wright-Workspace-ID")],
    session_id: Annotated[str, Header(alias="X-Wright-Session-ID")],
) -> SurfaceActor:
    role = getattr(request.state, "principal_role", None)
    settings = getattr(request.app.state, "security_settings", None)
    if role is None and settings is not None and not settings.enforced:
        role = ActorRole.ADMIN.value
    if role not in {ActorRole.ENGINEER.value, ActorRole.ADMIN.value}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Engineer or administrator role required",
        )
    return SurfaceActor(
        user_id=getattr(request.state, "principal_id", "local-user"),
        workspace_id=workspace_id,
        session_id=session_id,
        role=role,
    )


def _translate_error(error: SurfaceError) -> HTTPException:
    status_code = {
        "SURFACE_STATE_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "SURFACE_STATE_STALE_REVISION": status.HTTP_409_CONFLICT,
        "SURFACE_STATE_INVALID_TRANSITION": status.HTTP_409_CONFLICT,
        "SURFACE_POLICY_FORBIDDEN": status.HTTP_403_FORBIDDEN,
    }.get(error.code.value, status.HTTP_400_BAD_REQUEST)
    return HTTPException(status_code=status_code, detail=error.as_dict())


@router.get("", response_model=SurfaceListResponse)
async def list_surfaces(
    actor: Annotated[SurfaceActor, Depends(get_surface_actor)],
    service: Annotated[SurfaceService, Depends(get_surface_service)],
) -> SurfaceListResponse:
    try:
        descriptors = await service.list(actor=actor)
    except SurfaceError as error:
        raise _translate_error(error) from error
    return SurfaceListResponse(
        items=[SurfaceDescriptorResponse.from_domain(item) for item in descriptors]
    )


@router.get("/{surface_id}", response_model=SurfaceDescriptorResponse)
async def get_surface(
    surface_id: str,
    actor: Annotated[SurfaceActor, Depends(get_surface_actor)],
    service: Annotated[SurfaceService, Depends(get_surface_service)],
) -> SurfaceDescriptorResponse:
    try:
        descriptor = await service.get(actor=actor, surface_id=SurfaceId(surface_id))
    except (SurfaceError, ValueError) as error:
        if isinstance(error, SurfaceError):
            raise _translate_error(error) from error
        raise HTTPException(status_code=400, detail=str(error)) from error
    return SurfaceDescriptorResponse.from_domain(descriptor)


@router.post("", response_model=SurfaceDescriptorResponse, status_code=201)
async def declare_surface(
    body: DeclareSurfaceRequest,
    actor: Annotated[SurfaceActor, Depends(get_surface_actor)],
    service: Annotated[SurfaceService, Depends(get_surface_service)],
    idempotency_key: Annotated[
        str,
        Header(alias="Idempotency-Key", min_length=16, max_length=128),
    ],
) -> SurfaceDescriptorResponse:
    if (
        isinstance(body, LiveAppDeclareRequest)
        and body.manifest.get("id") == "wright.rivet-editor"
        and not rivet_editor_enabled()
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Rivet editor is disabled"
        )
    source, title = declare_request_to_domain(
        body, actor=actor, idempotency_key=idempotency_key
    )
    try:
        descriptor = await service.declare(
            actor=actor,
            source=source,
            title=title,
            idempotency_key=idempotency_key,
        )
    except SurfaceError as error:
        raise _translate_error(error) from error
    return SurfaceDescriptorResponse.from_domain(descriptor)
