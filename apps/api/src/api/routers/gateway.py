from __future__ import annotations

import json
import os
import uuid

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from tool_registry.gateway_models import GatewayError, SessionState

router = APIRouter()


class GatewayCallRequest(BaseModel):
    name: str
    arguments: dict = Field(default_factory=dict)


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
