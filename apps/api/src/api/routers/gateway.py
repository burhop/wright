from __future__ import annotations

import json
import os
import uuid
from collections import Counter

from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from api.config import DATABASE_PATH
from data_vault import GatewayRepository
from tool_registry.gateway_models import GatewayError, SessionState

router = APIRouter()


class GatewayCallRequest(BaseModel):
    name: str
    arguments: dict = Field(default_factory=dict)


@router.get("/diagnostics")
async def gateway_diagnostics(
    session_id: str,
    limit: int = Query(100, ge=1, le=1000),
):
    """Return redacted, persisted MCP timings for one bound session."""
    rows = GatewayRepository(DATABASE_PATH).list_audit(session_id)[-limit:]
    events = []
    terminal_by_request: set[str] = set()
    started_by_request: dict[str, dict] = {}
    terminal_outcomes = {"succeeded", "failed", "timed_out", "cancelled", "denied"}
    for row in rows:
        event = dict(row)
        try:
            event["metadata"] = json.loads(event.pop("metadata_json", "{}"))
        except (TypeError, json.JSONDecodeError):
            event["metadata"] = {}
        request_id = str(event.get("request_id") or "")
        if request_id and event.get("outcome") == "started":
            started_by_request[request_id] = event
        if request_id and event.get("outcome") in terminal_outcomes:
            terminal_by_request.add(request_id)
        events.append(event)

    completed = [
        event
        for event in events
        if event.get("operation") == "tool.call"
        and event.get("outcome") in terminal_outcomes
    ]
    durations = [int(event.get("duration_ms") or 0) for event in completed]
    slowest = sorted(
        completed,
        key=lambda event: int(event.get("duration_ms") or 0),
        reverse=True,
    )[:10]
    active = [
        event
        for request_id, event in started_by_request.items()
        if request_id not in terminal_by_request
    ]
    return {
        "session_id": session_id,
        "summary": {
            "completed_calls": len(completed),
            "active_calls": len(active),
            "total_duration_ms": sum(durations),
            "average_duration_ms": (
                round(sum(durations) / len(durations), 2) if durations else 0
            ),
            "maximum_duration_ms": max(durations, default=0),
            "outcomes": dict(Counter(event["outcome"] for event in completed)),
        },
        "active": active,
        "slowest": slowest,
        "events": events,
    }


def _bound_service(
    request: Request,
    session_id: str | None,
    workspace_id: str | None,
):
    if os.getenv("WRIGHT_LEGACY_GATEWAY") != "1":
        raise HTTPException(status_code=404, detail="Legacy gateway is disabled")
    if not session_id or not workspace_id:
        raise HTTPException(
            status_code=400,
            detail="X-Wright-Session-Id and X-Wright-Workspace-Id are required",
        )
    service = request.app.state.gateway_service
    try:
        context = service.open_session(
            session_id=session_id,
            principal_id="local-admin",
            workspace_id=workspace_id,
            transport="legacy",
        )
        if context.state is SessionState.CREATED:
            service.initialize_session(
                session_id,
                protocol_version="2025-11-25",
                client_name="wright-legacy-gateway",
                client_version="one-release-compatibility",
                client_capabilities={},
            )
    except GatewayError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid gateway binding") from exc
    return service


@router.get("/tools")
async def list_gateway_tools(
    request: Request,
    session_id: str | None = Header(None, alias="X-Wright-Session-Id"),
    workspace_id: str | None = Header(None, alias="X-Wright-Workspace-Id"),
):
    service = _bound_service(request, session_id, workspace_id)
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": dict(tool.input_schema),
                "outputSchema": (
                    dict(tool.output_schema) if tool.output_schema is not None else None
                ),
                "annotations": dict(tool.annotations),
            }
            for tool in service.list_tools(session_id)
        ]
    }


@router.post("/call")
async def call_gateway_tool(
    body: GatewayCallRequest,
    request: Request,
    session_id: str | None = Header(None, alias="X-Wright-Session-Id"),
    workspace_id: str | None = Header(None, alias="X-Wright-Workspace-Id"),
):
    service = _bound_service(request, session_id, workspace_id)
    try:
        result = await service.call_tool(
            session_id, str(uuid.uuid4()), body.name, body.arguments
        )
    except GatewayError as exc:
        return {
            "isError": True,
            "content": [{"type": "text", "text": str(exc)}],
            "structuredContent": {"error": exc.code.value},
        }
    return {
        "isError": result.is_error,
        "content": list(result.content),
        "structuredContent": result.structured_content,
    }


@router.get("/events")
async def stream_gateway_events(
    request: Request,
    session_id: str | None = Header(None, alias="X-Wright-Session-Id"),
    workspace_id: str | None = Header(None, alias="X-Wright-Workspace-Id"),
):
    service = _bound_service(request, session_id, workspace_id)
    context = service._session(session_id)

    async def events():
        yield "data: connected\n\n"
        async for event in service.notifier.subscribe(context):
            yield f"data: {json.dumps({'event': event})}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
