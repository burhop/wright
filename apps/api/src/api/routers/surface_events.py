"""Workspace-scoped Server-Sent Events for descriptor updates."""

from __future__ import annotations

import asyncio
import json
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse

from api.composition import surface_application
from api.routers.surfaces import get_surface_actor
from api.schemas.surfaces import SurfaceDescriptorResponse
from workspace_service.surfaces.events import SurfaceEventHistory
from workspace_service.surfaces.service import SurfaceActor


router = APIRouter(prefix="/surfaces")


def get_surface_events() -> SurfaceEventHistory:
    return surface_application().events


@router.get("/events")
async def stream_surface_events(
    request: Request,
    actor: Annotated[SurfaceActor, Depends(get_surface_actor)],
    events: Annotated[SurfaceEventHistory, Depends(get_surface_events)],
    last_event_id: Annotated[
        str | None, Header(alias="Last-Event-ID", max_length=128)
    ] = None,
) -> StreamingResponse:
    if last_event_id is not None and not last_event_id.strip():
        raise HTTPException(status_code=400, detail="Last-Event-ID must not be empty")

    async def generate():
        cursor = last_event_id
        while not await request.is_disconnected():
            available = events.after(
                workspace_id=actor.workspace_id,
                user_id=actor.user_id,
                session_id=actor.session_id,
                last_event_id=cursor,
            )
            if available:
                for event in available:
                    cursor = event.event_id
                    payload = SurfaceDescriptorResponse.from_domain(
                        event.descriptor
                    ).model_dump(mode="json", by_alias=True, exclude_none=True)
                    yield (
                        f"id: {event.event_id}\n"
                        f"event: {event.event_type}\n"
                        f"data: {json.dumps(payload, separators=(',', ':'))}\n\n"
                    )
            else:
                yield ": keepalive\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )
