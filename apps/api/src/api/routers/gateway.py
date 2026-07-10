import asyncio
import structlog
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from tool_registry import (
    ApprovalContext,
    McpEngine,
    get_servers,
    get_tools,
)
from api.services.mcp_services import get_mcp_engine
from workspace_service.adapters.runtime import (
    get_gateway_workspace,
    get_workspace_enabled_tools,
)
from api.notifications import gateway_event_queues

logger = structlog.get_logger(__name__)
router = APIRouter()


class GatewayCallRequest(BaseModel):
    name: str
    arguments: dict = {}


@router.get("/tools")
async def list_gateway_tools(engine: McpEngine = Depends(get_mcp_engine)):
    """Return consolidated list of enabled tools for the active workspace session."""
    db_path = engine.db_path
    workspace = get_gateway_workspace(db_path)

    if not workspace:
        return {"tools": []}

    session_id = workspace["session_id"]
    enabled_tools = get_workspace_enabled_tools(db_path, session_id)

    all_servers = get_servers(db_path)
    tools_response = []

    for server in all_servers:
        if not server.is_installed:
            continue

        # Check if server is enabled
        is_enabled = True
        if enabled_tools is not None:
            is_enabled = (server.name in enabled_tools) or (
                server.server_id in enabled_tools
            )

        if not is_enabled:
            continue

        key_name = "".join(c.lower() for c in server.name if c.isalnum())
        if not key_name:
            key_name = server.server_id

        server_tools = get_tools(db_path, server.server_id)
        for tool in server_tools:
            if not tool.is_enabled:
                continue

            prefixed_name = f"{key_name}__{tool.name}"
            tools_response.append(
                {
                    "name": prefixed_name,
                    "description": tool.description,
                    "inputSchema": tool.input_schema,
                }
            )

    return {"tools": tools_response}


@router.post("/call")
async def call_gateway_tool(
    body: GatewayCallRequest, engine: McpEngine = Depends(get_mcp_engine)
):
    """Execute a prefixed tool call on the corresponding child MCP server runner."""
    if "__" not in body.name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid prefixed tool name: {body.name}",
        )

    server_key, tool_name = body.name.split("__", 1)
    db_path = engine.db_path
    workspace = None
    approval_context = ApprovalContext()
    try:
        workspace = get_gateway_workspace(db_path)
        if workspace:
            approval_context = ApprovalContext(workspace_id=workspace["workspace_id"])
    except Exception:
        pass

    all_servers = get_servers(db_path)
    target_server = None
    for server in all_servers:
        key_name = "".join(c.lower() for c in server.name if c.isalnum())
        if not key_name:
            key_name = server.server_id
        if key_name == server_key:
            target_server = server
            break

    if not target_server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP Server with key prefix '{server_key}' not found.",
        )

    if workspace:
        enabled_tools = get_workspace_enabled_tools(db_path, workspace["session_id"])
        is_workspace_enabled = enabled_tools is None or (
            target_server.name in enabled_tools
            or target_server.server_id in enabled_tools
        )
        if is_workspace_enabled:
            approval_context = ApprovalContext(
                workspace_id=workspace["workspace_id"],
                workspace_approvals=set(target_server.approval_gates or []),
            )

    # Start the server runner if not active
    try:
        runner = engine._active_runners.get(target_server.server_id)
        if not runner or not runner.is_running():
            workspace_dir = workspace["local_path"] if workspace else None
            await engine.start_server(
                target_server.server_id,
                workspace_dir=workspace_dir,
                approval_context=approval_context,
            )
    except Exception as e:
        logger.exception(
            "gateway_start_server_failed", server=target_server.name, error=str(e)
        )
        return {
            "isError": True,
            "content": [
                {
                    "type": "text",
                    "text": f"Failed to start MCP Server '{target_server.name}': {e}",
                }
            ],
        }

    # Execute tool call
    try:
        result = await engine.call_tool(
            target_server.server_id,
            tool_name,
            body.arguments,
            approval_context=approval_context,
        )
        return result
    except Exception as e:
        logger.exception("gateway_call_tool_failed", tool=tool_name, error=str(e))
        return {
            "isError": True,
            "content": [
                {
                    "type": "text",
                    "text": f"Error calling tool '{tool_name}' on '{target_server.name}': {e}",
                }
            ],
        }


async def event_generator(queue: asyncio.Queue):
    try:
        yield "data: connected\n\n"
        while True:
            event = await queue.get()
            yield f"data: {event}\n\n"
            queue.task_done()
    except asyncio.CancelledError:
        pass
    finally:
        gateway_event_queues.discard(queue)


@router.get("/events")
async def stream_gateway_events(request: Request):
    """SSE endpoint for forwarding tool configuration/workspace changes to the gateway client."""
    queue = asyncio.Queue()
    gateway_event_queues.add(queue)
    return StreamingResponse(
        event_generator(queue),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
