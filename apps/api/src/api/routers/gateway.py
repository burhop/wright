import asyncio
from typing import Set
import structlog
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from tool_registry import (
    McpEngine,
    get_servers,
    get_tools,
)
from api.services.mcp_services import get_mcp_engine
from core.workspace import get_gateway_workspace, get_workspace_enabled_tools

logger = structlog.get_logger(__name__)
router = APIRouter()

# Active SSE listener queues
gateway_event_queues: Set[asyncio.Queue] = set()


def notify_gateway_tool_change():
    """Notify all connected gateway clients that the tool list has changed."""
    logger.info(
        "notifying_gateways_of_tool_change", active_queues=len(gateway_event_queues)
    )
    for queue in list(gateway_event_queues):
        try:
            queue.put_nowait("list_changed")
        except Exception as e:
            logger.warning("failed_to_queue_gateway_event", error=str(e))


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

    # Start the server runner if not active
    try:
        runner = engine._active_runners.get(target_server.server_id)
        if not runner or not runner.is_running():
            workspace_dir = None
            try:
                workspace = get_gateway_workspace(db_path)
                if workspace:
                    workspace_dir = workspace["local_path"]
            except Exception:
                pass
            await engine.start_server(
                target_server.server_id, workspace_dir=workspace_dir
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
            target_server.server_id, tool_name, body.arguments
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
