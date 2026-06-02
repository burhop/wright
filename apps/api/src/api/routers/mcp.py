import uuid
import time
import structlog
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Request, HTTPException, status, Response
from pydantic import BaseModel, Field

from tool_registry import (
    McpServer,
    McpServerCreate,
    McpTool,
    get_servers,
    get_server,
    insert_server,
    delete_server,
    get_tools,
    get_tool,
    update_tool_enabled,
    McpEngine,
)

logger = structlog.get_logger(__name__)
router = APIRouter()

# ── Dependency injection helper ──────────────────────────────────────────────
def get_mcp_engine(request: Request) -> McpEngine:
    """Extract McpEngine from app state."""
    engine = getattr(request.app.state, "mcp_engine", None)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MCP engine not initialized in app state"
        )
    return engine

# ── REST Models ──────────────────────────────────────────────────────────────
class ServersListResponse(BaseModel):
    servers: List[McpServer]

class RegisterServerResponse(BaseModel):
    server_id: str
    name: str
    status: str

class ServerToggleRequest(BaseModel):
    is_active: bool

class ServerToggleResponse(BaseModel):
    server_id: str
    is_active: bool
    status: str
    error_message: Optional[str] = None

class ToolsListResponse(BaseModel):
    tools: List[McpTool]

class ToolToggleRequest(BaseModel):
    is_enabled: bool

class ToolToggleResponse(BaseModel):
    tool_id: str
    is_enabled: bool

# ── Route Handlers ───────────────────────────────────────────────────────────

@router.get("/servers", response_model=ServersListResponse)
async def list_servers(engine: McpEngine = Depends(get_mcp_engine)):
    try:
        servers = get_servers(engine.db_path)
        return ServersListResponse(servers=servers)
    except Exception as e:
        logger.exception("list_servers_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list MCP servers: {e}"
        )

@router.post("/servers", response_model=RegisterServerResponse, status_code=status.HTTP_201_CREATED)
async def register_server(body: McpServerCreate, engine: McpEngine = Depends(get_mcp_engine)):
    server_id = str(uuid.uuid4())
    logger.info("registering_server", name=body.name, type=body.type)
    
    # Check if a server with this name already exists to avoid unique constraint error
    from tool_registry.db import get_server_by_name
    existing = get_server_by_name(engine.db_path, body.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An MCP server with the name '{body.name}' is already registered."
        )

    now = int(time.time())
    new_server = McpServer(
        server_id=server_id,
        name=body.name,
        type=body.type,
        command=body.command,
        is_active=False,
        status="inactive",
        error_message=None,
        category=body.category,
        created_at=now,
        updated_at=now
    )
    try:
        insert_server(engine.db_path, new_server)
        return RegisterServerResponse(
            server_id=server_id,
            name=body.name,
            status="inactive"
        )
    except Exception as e:
        logger.exception("register_server_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register MCP server: {e}"
        )

@router.patch("/servers/{server_id}", response_model=ServerToggleResponse)
async def toggle_server_activation(
    server_id: str,
    body: ServerToggleRequest,
    engine: McpEngine = Depends(get_mcp_engine)
):
    logger.info("toggling_server_activation", server_id=server_id, target_is_active=body.is_active)
    
    server = get_server(engine.db_path, server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP Server '{server_id}' not found."
        )

    try:
        if body.is_active:
            updated = await engine.start_server(server_id)
        else:
            updated = await engine.stop_server(server_id)
            
        return ServerToggleResponse(
            server_id=updated.server_id,
            is_active=updated.is_active,
            status=updated.status,
            error_message=updated.error_message
        )
    except Exception as e:
        logger.exception("toggle_server_failed", server_id=server_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle MCP server activation: {e}"
        )

@router.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server_endpoint(server_id: str, engine: McpEngine = Depends(get_mcp_engine)):
    logger.info("deleting_server", server_id=server_id)
    
    server = get_server(engine.db_path, server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP Server '{server_id}' not found."
        )

    try:
        # First ensure runner is stopped and tools are cleared
        await engine.stop_server(server_id)
        # Delete server from database
        delete_server(engine.db_path, server_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.exception("delete_server_failed", server_id=server_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete MCP server: {e}"
        )

@router.get("/tools", response_model=ToolsListResponse)
async def list_tools_endpoint(engine: McpEngine = Depends(get_mcp_engine)):
    try:
        tools = get_tools(engine.db_path)
        return ToolsListResponse(tools=tools)
    except Exception as e:
        logger.exception("list_tools_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list MCP tools: {e}"
        )

@router.patch("/tools/{tool_id}", response_model=ToolToggleResponse)
async def toggle_tool_enabled(
    tool_id: str,
    body: ToolToggleRequest,
    engine: McpEngine = Depends(get_mcp_engine)
):
    logger.info("toggling_tool_enabled", tool_id=tool_id, is_enabled=body.is_enabled)
    
    tool = get_tool(engine.db_path, tool_id)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP Tool '{tool_id}' not found."
        )

    try:
        success = update_tool_enabled(engine.db_path, tool_id, body.is_enabled)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update tool state in database."
            )
        return ToolToggleResponse(
            tool_id=tool_id,
            is_enabled=body.is_enabled
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("toggle_tool_failed", tool_id=tool_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle tool enabled state: {e}"
        )
