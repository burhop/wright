import uuid
import time
import structlog
import os
import shlex
import subprocess
import yaml
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, HTTPException, status, Response
from pydantic import BaseModel
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

def sync_mcp_server_to_hermes(server: McpServer):
    """Sync an MCP server's active/inactive state to Hermes config.yaml files."""
    import sys
    if "pytest" in sys.modules:
        return
        
    key_name = "".join(c.lower() for c in server.name if c.isalnum())
    if not key_name:
        key_name = server.server_id
        
    paths = [
        os.path.expanduser("~/.hermes/profiles/wright/config.yaml"),
        os.path.expanduser("~/.hermes/config.yaml")
    ]
    
    for path in paths:
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r") as f:
                config = yaml.safe_load(f) or {}
                
            if "mcp_servers" not in config:
                config["mcp_servers"] = {}
                
            if server.is_active:
                if server.type == "stdio":
                    if not server.command:
                        continue
                    args = []
                    if isinstance(server.command, list):
                        cmd = server.command[0]
                        if len(server.command) > 1:
                            args = server.command[1:]
                    else:
                        parsed = shlex.split(server.command)
                        cmd = parsed[0] if parsed else "echo"
                        args = parsed[1:] if len(parsed) > 1 else []
                        
                    srv_config = {
                        "command": cmd,
                        "args": args
                    }
                    
                    if key_name == "openscadgeometry" or "openscad" in key_name:
                        srv_config["env"] = {
                            "OPENSCAD_PATH": "/home/burhop/repos/wright/scripts/openscad-headless.sh"
                        }
                    config["mcp_servers"][key_name] = srv_config
                    
                elif server.type == "sse":
                    if not server.command or not isinstance(server.command, str):
                        continue
                    config["mcp_servers"][key_name] = {
                        "url": server.command,
                        "transport": "sse"
                    }
            else:
                for k in list(config["mcp_servers"].keys()):
                    if k == key_name or (key_name == "openscadgeometry" and k == "openscad"):
                        del config["mcp_servers"][k]
                        
            with open(path, "w") as f:
                yaml.safe_dump(config, f, default_flow_style=False)
                
        except Exception as e:
            print(f"Failed to sync MCP server {server.name} to Hermes config {path}: {e}")

# Imports moved to top

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

class ServerInstallResponse(BaseModel):
    server_id: str
    is_installed: bool
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
            
        # Sync with Hermes config
        sync_mcp_server_to_hermes(updated)
        
        # Restart Hermes WebUI in background to reload config
        subprocess.Popen(
            "export HERMES_HOME=\"$HOME/.hermes/profiles/wright\" && /home/burhop/hermes-webui/ctl.sh stop && /home/burhop/hermes-webui/ctl.sh start 8788",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
            
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

@router.post("/servers/{server_id}/install", response_model=ServerInstallResponse)
async def install_server_endpoint(
    server_id: str,
    request: Request,
    session_id: Optional[str] = None,
    engine: McpEngine = Depends(get_mcp_engine)
):
    logger.info("installing_server", server_id=server_id, session_id=session_id)
    
    server = get_server(engine.db_path, server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP Server '{server_id}' not found."
        )

    try:
        # Mark as installed in database
        from tool_registry.db import update_server
        update_server(engine.db_path, server_id, {"is_installed": True, "updated_at": int(time.time())})
        
        # Start server once to discover tools
        updated = await engine.start_server(server_id)
        
        # If a session_id is provided, check if enabled in that workspace.
        # If not, stop the runner.
        should_stop = True
        if session_id:
            from core.workspace import get_workspace_enabled_tools
            enabled_tools = get_workspace_enabled_tools(engine.db_path, session_id)
            if enabled_tools is not None:
                if (updated.name in enabled_tools) or (updated.server_id in enabled_tools):
                    should_stop = False
        else:
            should_stop = True

        if should_stop:
            updated = await engine.stop_server(server_id)
            # Retain is_installed state
            update_server(engine.db_path, server_id, {"is_installed": True})
            updated.is_installed = True
            
        # Sync with the active agent if session is active
        if session_id:
            sync_manager = getattr(request.app.state, "agent_sync_manager", None)
            if sync_manager:
                sync_manager.sync_workspace_tools(session_id)
            
        return ServerInstallResponse(
            server_id=updated.server_id,
            is_installed=updated.is_installed,
            status=updated.status,
            error_message=updated.error_message
        )
    except Exception as e:
        logger.exception("install_server_failed", server_id=server_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to install MCP server: {e}"
        )

@router.post("/servers/{server_id}/uninstall", response_model=ServerInstallResponse)
async def uninstall_server_endpoint(
    server_id: str,
    request: Request,
    session_id: Optional[str] = None,
    engine: McpEngine = Depends(get_mcp_engine)
):
    logger.info("uninstalling_server", server_id=server_id, session_id=session_id)
    
    server = get_server(engine.db_path, server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP Server '{server_id}' not found."
        )

    try:
        # Stop the server runner
        updated = await engine.stop_server(server_id)
        
        # Mark as not installed in database
        from tool_registry.db import update_server
        updated = update_server(engine.db_path, server_id, {
            "is_installed": False, 
            "is_active": False,
            "status": "inactive",
            "updated_at": int(time.time())
        })
        
        # Sync tools removal to the agent if session is active
        if session_id:
            sync_manager = getattr(request.app.state, "agent_sync_manager", None)
            if sync_manager:
                sync_manager.sync_workspace_tools(session_id)
                
        return ServerInstallResponse(
            server_id=updated.server_id,
            is_installed=updated.is_installed,
            status=updated.status,
            error_message=updated.error_message
        )
    except Exception as e:
        logger.exception("uninstall_server_failed", server_id=server_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to uninstall MCP server: {e}"
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
        
        # Sync removal with Hermes config
        server.is_active = False
        sync_mcp_server_to_hermes(server)
        
        # Restart Hermes WebUI in background to reload config
        subprocess.Popen(
            "export HERMES_HOME=\"$HOME/.hermes/profiles/wright\" && /home/burhop/hermes-webui/ctl.sh stop && /home/burhop/hermes-webui/ctl.sh start 8788",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
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
