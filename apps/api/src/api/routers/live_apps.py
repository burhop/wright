"""Thin authenticated controls for managed Workspace Surface applications."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from api.composition import surface_application
from api.routers.surfaces import get_surface_actor
from core.surfaces.errors import SurfaceError
from core.surfaces.models import SurfaceId
from workspace_service.surfaces.live_app_manager import LiveAppInstance
from workspace_service.surfaces.live_app_service import (
    LiveAppControlError,
    LiveAppControlService,
)
from workspace_service.surfaces.service import SurfaceActor


router = APIRouter(prefix="/surfaces")


class LiveAppFailureResponse(BaseModel):
    code: str
    message: str
    retryable: bool


class LiveAppActionResponse(BaseModel):
    operation: str
    label: str


class LiveAppResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    surface_id: str = Field(alias="surfaceId")
    instance_id: str = Field(alias="instanceId")
    generation: int = Field(ge=1)
    state: str
    sharing: str
    ownership: str
    platform: str | None
    lifetime_policy: str = Field(alias="lifetimePolicy")
    lease_expires_at: datetime | None = Field(alias="leaseExpiresAt")
    idle_seconds: int | None = Field(alias="idleSeconds")
    last_activity_at: datetime = Field(alias="lastActivityAt")
    started_at: datetime | None = Field(alias="startedAt")
    ready_at: datetime | None = Field(alias="readyAt")
    ended_at: datetime | None = Field(alias="endedAt")
    failure: LiveAppFailureResponse | None
    actions: list[LiveAppActionResponse]


class LiveAppHealthResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    instance_id: str = Field(alias="instanceId")
    generation: int
    state: str
    ok: bool | None
    diagnostic_code: str | None = Field(alias="diagnosticCode")
    message: str
    observed_status: int | None = Field(alias="observedStatus")
    attempts: int


class LiveAppLogEntryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    sequence: int
    stream: str
    message: str
    captured_at: datetime = Field(alias="capturedAt")
    byte_count: int = Field(alias="byteCount")


class LiveAppLogsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    entries: list[LiveAppLogEntryResponse]
    rotated: bool
    dropped_bytes: int = Field(alias="droppedBytes")
    next_sequence: int = Field(alias="nextSequence")


def get_live_app_service() -> LiveAppControlService:
    return surface_application().live_apps


def _actions(state: str) -> list[LiveAppActionResponse]:
    operations = {
        "declared": (("start", "Start application"),),
        "ready": (("restart", "Restart application"), ("stop", "Stop application")),
        "unhealthy": (
            ("restart", "Restart application"),
            ("stop", "Stop application"),
        ),
        "failed": (("retry", "Retry application"),),
        "stopped": (("restart", "Start application again"),),
    }.get(state, ())
    return [LiveAppActionResponse(operation=item[0], label=item[1]) for item in operations]


def _runtime(surface_id: str, instance: LiveAppInstance) -> LiveAppResponse:
    return LiveAppResponse(
        surface_id=surface_id,
        instance_id=instance.instance_id,
        generation=instance.generation,
        state=instance.state,
        sharing=instance.sharing,
        ownership=instance.ownership,
        platform=instance.platform,
        lifetime_policy=instance.lifetime_policy,
        lease_expires_at=instance.lease_expires_at,
        idle_seconds=instance.idle_seconds,
        last_activity_at=instance.last_activity_at,
        started_at=instance.started_at,
        ready_at=instance.ready_at,
        ended_at=instance.ended_at,
        failure=(
            LiveAppFailureResponse(
                code=instance.failure.code,
                message=instance.failure.message,
                retryable=instance.failure.retryable,
            )
            if instance.failure is not None
            else None
        ),
        actions=_actions(instance.state),
    )


def _translate(error: LiveAppControlError | SurfaceError | ValueError) -> HTTPException:
    if isinstance(error, LiveAppControlError):
        status_code = 404 if error.code.endswith("NOT_FOUND") else 409
        if error.code.startswith("SURFACE_LIMIT_"):
            status_code = 429
        return HTTPException(
            status_code=status_code,
            detail={
                "code": error.code,
                "message": str(error),
                "retryable": error.retryable,
            },
        )
    if isinstance(error, SurfaceError):
        return HTTPException(status_code=404, detail=error.as_dict())
    return HTTPException(status_code=400, detail=str(error))


async def _operate(
    operation: str,
    *,
    surface_id: str,
    actor: SurfaceActor,
    service: LiveAppControlService,
    idempotency_key: str,
) -> LiveAppResponse:
    try:
        method = getattr(service, operation)
        instance = await method(
            actor=actor,
            surface_id=SurfaceId(surface_id),
            idempotency_key=idempotency_key,
        )
    except (LiveAppControlError, SurfaceError, ValueError) as error:
        raise _translate(error) from error
    return _runtime(surface_id, instance)


@router.post("/{surface_id}/start", response_model=LiveAppResponse, status_code=202)
async def start_live_app(
    surface_id: str,
    actor: Annotated[SurfaceActor, Depends(get_surface_actor)],
    service: Annotated[LiveAppControlService, Depends(get_live_app_service)],
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=16, max_length=128)
    ],
) -> LiveAppResponse:
    return await _operate(
        "start",
        surface_id=surface_id,
        actor=actor,
        service=service,
        idempotency_key=idempotency_key,
    )


@router.post("/{surface_id}/retry", response_model=LiveAppResponse, status_code=202)
async def retry_live_app(
    surface_id: str,
    actor: Annotated[SurfaceActor, Depends(get_surface_actor)],
    service: Annotated[LiveAppControlService, Depends(get_live_app_service)],
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=16, max_length=128)
    ],
) -> LiveAppResponse:
    return await _operate(
        "retry",
        surface_id=surface_id,
        actor=actor,
        service=service,
        idempotency_key=idempotency_key,
    )


@router.post("/{surface_id}/restart", response_model=LiveAppResponse, status_code=202)
async def restart_live_app(
    surface_id: str,
    actor: Annotated[SurfaceActor, Depends(get_surface_actor)],
    service: Annotated[LiveAppControlService, Depends(get_live_app_service)],
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=16, max_length=128)
    ],
) -> LiveAppResponse:
    return await _operate(
        "restart",
        surface_id=surface_id,
        actor=actor,
        service=service,
        idempotency_key=idempotency_key,
    )


@router.post("/{surface_id}/stop", response_model=LiveAppResponse, status_code=202)
async def stop_live_app(
    surface_id: str,
    actor: Annotated[SurfaceActor, Depends(get_surface_actor)],
    service: Annotated[LiveAppControlService, Depends(get_live_app_service)],
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=16, max_length=128)
    ],
) -> LiveAppResponse:
    return await _operate(
        "stop",
        surface_id=surface_id,
        actor=actor,
        service=service,
        idempotency_key=idempotency_key,
    )


@router.get("/{surface_id}/live-app", response_model=LiveAppResponse)
async def inspect_live_app(
    surface_id: str,
    actor: Annotated[SurfaceActor, Depends(get_surface_actor)],
    service: Annotated[LiveAppControlService, Depends(get_live_app_service)],
) -> LiveAppResponse:
    try:
        instance = await service.inspect(
            actor=actor, surface_id=SurfaceId(surface_id)
        )
    except (LiveAppControlError, SurfaceError, ValueError) as error:
        raise _translate(error) from error
    return _runtime(surface_id, instance)


@router.get("/{surface_id}/live-app/health", response_model=LiveAppHealthResponse)
async def live_app_health(
    surface_id: str,
    actor: Annotated[SurfaceActor, Depends(get_surface_actor)],
    service: Annotated[LiveAppControlService, Depends(get_live_app_service)],
) -> LiveAppHealthResponse:
    try:
        instance = await service.health(
            actor=actor, surface_id=SurfaceId(surface_id)
        )
    except (LiveAppControlError, SurfaceError, ValueError) as error:
        raise _translate(error) from error
    probe = instance.last_health
    return LiveAppHealthResponse(
        instance_id=instance.instance_id,
        generation=instance.generation,
        state=instance.state,
        ok=probe.ok if probe else None,
        diagnostic_code=probe.diagnostic_code if probe else None,
        message=probe.message if probe else "No health probe is declared.",
        observed_status=probe.observed_status if probe else None,
        attempts=probe.attempts if probe else 0,
    )


@router.get("/{surface_id}/live-app/logs", response_model=LiveAppLogsResponse)
async def live_app_logs(
    surface_id: str,
    actor: Annotated[SurfaceActor, Depends(get_surface_actor)],
    service: Annotated[LiveAppControlService, Depends(get_live_app_service)],
    after_sequence: Annotated[
        int, Query(alias="afterSequence", ge=0)
    ] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 200,
) -> LiveAppLogsResponse:
    try:
        tail = await service.logs(
            actor=actor,
            surface_id=SurfaceId(surface_id),
            after_sequence=after_sequence,
            limit=limit,
        )
    except (LiveAppControlError, SurfaceError, ValueError) as error:
        raise _translate(error) from error
    return LiveAppLogsResponse(
        entries=[
            LiveAppLogEntryResponse(
                sequence=item.sequence,
                stream=item.stream,
                message=item.message,
                captured_at=item.captured_at,
                byte_count=item.byte_count,
            )
            for item in tail.entries
        ],
        rotated=tail.rotated,
        dropped_bytes=tail.dropped_bytes,
        next_sequence=tail.next_sequence,
    )


__all__ = ["get_live_app_service", "router"]
