"""Thin authenticated presentation and preference control-plane routes."""

from __future__ import annotations

from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field

from api.composition import surface_application
from api.routers.surfaces import get_surface_actor
from core.surfaces.models import SurfaceId
from workspace_service.surfaces.presentation_service import (
    IsolatedPresentationAcknowledgementRequired,
    PresentationLaunch,
    PresentationService,
    PresentationUnavailable,
)
from workspace_service.surfaces.service import SurfaceActor


router = APIRouter(prefix="/surfaces")


class PresentationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    kind: Literal["panel", "browser"]
    remember_preference: bool = Field(default=False, alias="rememberPreference")
    isolated_acknowledged: bool = Field(
        default=False, alias="isolatedAcknowledged"
    )


class PreferenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["panel", "browser"]


class PresentationLaunchResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    presentation_id: str = Field(alias="presentationId")
    instance_id: str = Field(alias="instanceId")
    generation: int = Field(ge=1)
    kind: Literal["panel", "browser"]
    absolute_bootstrap_url: str = Field(alias="absoluteBootstrapUrl")
    expires_at: str = Field(alias="expiresAt")


class PresentationPreferenceResponse(BaseModel):
    kind: Literal["panel", "browser"]
    remembered: bool
    reason: str


def get_presentation_service() -> PresentationService:
    return surface_application().presentation_service


def _launch_payload(launch: PresentationLaunch) -> PresentationLaunchResponse:
    return PresentationLaunchResponse(
        presentation_id=launch.presentation_id,
        instance_id=launch.instance_id,
        generation=launch.generation,
        kind=cast(Literal["panel", "browser"], launch.kind),
        absolute_bootstrap_url=launch.absolute_bootstrap_url,
        expires_at=launch.expires_at.isoformat().replace("+00:00", "Z"),
    )


@router.post(
    "/{surface_id}/presentations",
    response_model=PresentationLaunchResponse,
    status_code=201,
)
def create_presentation(
    surface_id: str,
    body: PresentationRequest,
    response: Response,
    actor: Annotated[SurfaceActor, Depends(get_surface_actor)],
    service: Annotated[PresentationService, Depends(get_presentation_service)],
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=16, max_length=128)
    ],
) -> PresentationLaunchResponse:
    try:
        result = service.open(
            actor=actor,
            surface_id=SurfaceId(surface_id),
            kind=body.kind,
            idempotency_key=idempotency_key,
            remember_preference=body.remember_preference,
            isolated_acknowledged=body.isolated_acknowledged,
        )
    except IsolatedPresentationAcknowledgementRequired as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except (PresentationUnavailable, ValueError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    response.status_code = 201 if result.created else 200
    return _launch_payload(result.launch)


@router.delete("/{surface_id}/presentations/{presentation_id}", status_code=204)
def close_presentation(
    surface_id: str,
    presentation_id: str,
    actor: Annotated[SurfaceActor, Depends(get_surface_actor)],
    service: Annotated[PresentationService, Depends(get_presentation_service)],
) -> Response:
    try:
        service.close(
            actor=actor,
            surface_id=SurfaceId(surface_id),
            presentation_id=presentation_id,
        )
    except (PresentationUnavailable, ValueError) as error:
        raise HTTPException(status_code=404, detail="Presentation not found") from error
    return Response(status_code=204)


@router.get(
    "/{surface_id}/presentation-preference",
    response_model=PresentationPreferenceResponse,
)
def get_presentation_preference(
    surface_id: str,
    actor: Annotated[SurfaceActor, Depends(get_surface_actor)],
    service: Annotated[PresentationService, Depends(get_presentation_service)],
) -> PresentationPreferenceResponse:
    try:
        decision = service.resolve_preference(
            actor=actor, surface_id=SurfaceId(surface_id)
        )
    except (PresentationUnavailable, ValueError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return PresentationPreferenceResponse(
        kind=cast(Literal["panel", "browser"], decision.kind),
        remembered=decision.remembered,
        reason=decision.reason,
    )


@router.put(
    "/{surface_id}/presentation-preference",
    response_model=PresentationPreferenceResponse,
)
def set_presentation_preference(
    surface_id: str,
    body: PreferenceRequest,
    actor: Annotated[SurfaceActor, Depends(get_surface_actor)],
    service: Annotated[PresentationService, Depends(get_presentation_service)],
) -> PresentationPreferenceResponse:
    try:
        decision = service.set_preference(
            actor=actor, surface_id=SurfaceId(surface_id), kind=body.kind
        )
    except (PresentationUnavailable, ValueError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return PresentationPreferenceResponse(
        kind=cast(Literal["panel", "browser"], decision.kind),
        remembered=decision.remembered,
        reason=decision.reason,
    )
