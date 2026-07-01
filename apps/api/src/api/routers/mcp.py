import uuid
import time
import structlog
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, HTTPException, status, Response
from pydantic import BaseModel
from tool_registry import (
    McpServer,
    McpServerCreate,
    McpTool,
    EnvVarDefinition,
    get_servers,
    get_server,
    insert_server,
    delete_server,
    get_tools,
    get_tool,
    update_tool_enabled,
    McpEngine,
    read_secrets,
    write_secrets,
    delete_secrets,
    has_credentials,
)
from core.tracing import traced
from api.services.wright_gateway_sync import (
    sync_mcp_server_to_wright_gateway,
)
from tool_registry.mcp_catalog import is_install_blocked, tier_sort_key
from tool_registry.mcp_followups import write_followup_record
from tool_registry.mcp_validation import classify_server

logger = structlog.get_logger(__name__)
router = APIRouter()


# ── Dependency injection helper ──────────────────────────────────────────────
def get_mcp_engine(request: Request) -> McpEngine:
    """Extract McpEngine from app state."""
    engine = getattr(request.app.state, "mcp_engine", None)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MCP engine not initialized in app state",
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
    type: Optional[str] = None


class ServerInstallResponse(BaseModel):
    server_id: str
    is_installed: bool
    status: str
    error_message: Optional[str] = None
    type: Optional[str] = None


class ToolsListResponse(BaseModel):
    tools: List[McpTool]


class ToolToggleRequest(BaseModel):
    is_enabled: bool


class ToolToggleResponse(BaseModel):
    tool_id: str
    is_enabled: bool


class CredentialStatusResponse(BaseModel):
    server_id: str
    env_vars: list = []
    configured: dict = {}


class SaveCredentialsRequest(BaseModel):
    credentials: dict


class ValidateServerResponse(BaseModel):
    server_id: str
    environment: str
    status: str
    installability_tier: str
    message: str
    missing_dependencies: list[str] = []
    diagnostics: str = ""
    follow_up_url: Optional[str] = None


class MissingMcpReportRequest(BaseModel):
    name: str
    source_url: Optional[str] = None
    notes: Optional[str] = None
    category: str = "utilities"


# ── Route Handlers ───────────────────────────────────────────────────────────


@router.get("/servers", response_model=ServersListResponse)
@traced("mcp.server.list")
async def list_servers(engine: McpEngine = Depends(get_mcp_engine)):
    try:
        servers = sorted(get_servers(engine.db_path), key=tier_sort_key)
        # Add credentials_configured status for servers with env_var definitions
        for server in servers:
            if server.env_vars and isinstance(server.env_vars, list):
                var_names = [
                    v.name for v in server.env_vars if isinstance(v, EnvVarDefinition)
                ]
                if var_names:
                    server.credentials_configured = has_credentials(
                        server.server_id, var_names
                    )
        return ServersListResponse(servers=servers)
    except Exception as e:
        logger.exception("list_servers_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list MCP servers: {e}",
        )


@router.post(
    "/servers",
    response_model=RegisterServerResponse,
    status_code=status.HTTP_201_CREATED,
)
@traced("mcp.server.register")
async def register_server(
    body: McpServerCreate, engine: McpEngine = Depends(get_mcp_engine)
):
    server_id = str(uuid.uuid4())
    logger.info("registering_server", name=body.name, type=body.type)

    # Check if a server with this name already exists to avoid unique constraint error
    from tool_registry.db import get_server_by_name

    existing = get_server_by_name(engine.db_path, body.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An MCP server with the name '{body.name}' is already registered.",
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
        updated_at=now,
        image_url=body.image_url,
        description=body.description,
        source_url=body.source_url,
        installed_version=body.installed_version,
        env_vars=body.env_vars,
        instructions=body.instructions,
        verification_state=body.verification_state,
        installability_tier=body.installability_tier,
        risk_level=body.risk_level,
        deployment_mode=body.deployment_mode,
        platform_support=body.platform_support,
        host_software_required=body.host_software_required,
        credentials_required=body.credentials_required,
        default_enabled=body.default_enabled,
        approval_gates=body.approval_gates,
        validation_result=body.validation_result,
        follow_up_url=body.follow_up_url,
        install_blocked_reason=body.install_blocked_reason,
    )
    try:
        insert_server(engine.db_path, new_server)
        return RegisterServerResponse(
            server_id=server_id, name=body.name, status="inactive"
        )
    except Exception as e:
        logger.exception("register_server_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register MCP server: {e}",
        )


@router.patch("/servers/{server_id}", response_model=ServerToggleResponse)
@traced("mcp.server.toggle")
async def toggle_server_activation(
    server_id: str,
    body: ServerToggleRequest,
    engine: McpEngine = Depends(get_mcp_engine),
):
    logger.info(
        "toggling_server_activation",
        server_id=server_id,
        target_is_active=body.is_active,
    )

    server = get_server(engine.db_path, server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP Server '{server_id}' not found.",
        )

    try:
        if body.is_active:
            updated = await engine.start_server(server_id)
        else:
            updated = await engine.stop_server(server_id)

        # Sync with the active Wright gateway profile.
        sync_mcp_server_to_wright_gateway(updated)

        return ServerToggleResponse(
            server_id=updated.server_id,
            is_active=updated.is_active,
            status=updated.status,
            error_message=updated.error_message,
            type=updated.type,
        )
    except Exception as e:
        logger.exception("toggle_server_failed", server_id=server_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle MCP server activation: {e}",
        )


@router.post("/servers/{server_id}/install", response_model=ServerInstallResponse)
@traced("mcp.server.install")
async def install_server_endpoint(
    server_id: str,
    request: Request,
    session_id: Optional[str] = None,
    engine: McpEngine = Depends(get_mcp_engine),
):
    logger.info("installing_server", server_id=server_id, session_id=session_id)

    server = get_server(engine.db_path, server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP Server '{server_id}' not found.",
        )
    if is_install_blocked(server):
        reason = server.install_blocked_reason or (
            f"Server '{server.name}' is marked {server.installability_tier}."
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)

    try:
        # Mark as installed in database
        from tool_registry.db import update_server

        update_server(
            engine.db_path,
            server_id,
            {"is_installed": True, "updated_at": int(time.time())},
        )

        # Start server once to discover tools
        updated = await engine.start_server(server_id)

        # If a session_id is provided, check if enabled in that workspace.
        # If not, stop the runner.
        should_stop = True
        if session_id:
            from core.workspace import get_workspace_enabled_tools

            enabled_tools = get_workspace_enabled_tools(engine.db_path, session_id)
            if enabled_tools is not None:
                if (updated.name in enabled_tools) or (
                    updated.server_id in enabled_tools
                ):
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
            error_message=updated.error_message,
            type=updated.type,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("install_server_failed", server_id=server_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to install MCP server: {e}",
        )


@router.post("/servers/{server_id}/validate", response_model=ValidateServerResponse)
@traced("mcp.server.validate")
async def validate_server_endpoint(
    server_id: str,
    engine: McpEngine = Depends(get_mcp_engine),
):
    server = get_server(engine.db_path, server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP Server '{server_id}' not found.",
        )

    result = classify_server(server)
    follow_up_url = result.follow_up_url
    if result.status == "failed" or result.installability_tier == "non_working":
        follow_up_url = write_followup_record(
            Path("docs/mcp-catalog/followups"),
            result,
            source_url=server.source_url,
            verification_state=server.verification_state,
        )
        result.follow_up_url = follow_up_url

    from tool_registry.db import update_server as db_update_server

    db_update_server(
        engine.db_path,
        server_id,
        {
            "validation_result": result.as_summary(),
            "installability_tier": result.installability_tier,
            "follow_up_url": follow_up_url,
        },
    )
    return ValidateServerResponse(**result.model_dump())


@router.post(
    "/servers/report-missing",
    response_model=RegisterServerResponse,
    status_code=status.HTTP_201_CREATED,
)
@traced("mcp.server.report_missing")
async def report_missing_mcp(
    body: MissingMcpReportRequest,
    engine: McpEngine = Depends(get_mcp_engine),
):
    normalized = "".join(
        char.lower() if char.isalnum() else "-" for char in body.name.strip()
    ).strip("-")
    normalized = "-".join(part for part in normalized.split("-") if part)
    server_id = f"reported-{normalized or uuid.uuid4().hex[:8]}"
    now = int(time.time())

    existing = get_server(engine.db_path, server_id)
    if existing:
        return RegisterServerResponse(
            server_id=existing.server_id,
            name=existing.name,
            status=existing.status,
        )

    server = McpServer(
        server_id=server_id,
        name=body.name,
        type="stdio",
        command=None,
        is_active=False,
        is_installed=False,
        status="inactive",
        category=body.category,
        created_at=now,
        updated_at=now,
        description=body.notes or "User-reported MCP candidate pending verification.",
        source_url=body.source_url,
        verification_state="user_reported_url_needed",
        installability_tier="blocked",
        risk_level="low",
        deployment_mode="unknown",
        default_enabled=False,
        install_blocked_reason="User-reported MCP candidate pending source and install verification.",
    )
    insert_server(engine.db_path, server)
    return RegisterServerResponse(
        server_id=server.server_id,
        name=server.name,
        status=server.status,
    )


@router.post("/servers/{server_id}/uninstall", response_model=ServerInstallResponse)
@traced("mcp.server.uninstall")
async def uninstall_server_endpoint(
    server_id: str,
    request: Request,
    session_id: Optional[str] = None,
    engine: McpEngine = Depends(get_mcp_engine),
):
    logger.info("uninstalling_server", server_id=server_id, session_id=session_id)

    server = get_server(engine.db_path, server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP Server '{server_id}' not found.",
        )

    try:
        # Stop the server runner
        updated = await engine.stop_server(server_id)

        # Mark as not installed in database
        from tool_registry.db import update_server

        updated = update_server(
            engine.db_path,
            server_id,
            {
                "is_installed": False,
                "is_active": False,
                "status": "inactive",
                "updated_at": int(time.time()),
            },
        )

        # Sync tools removal to the agent if session is active
        if session_id:
            sync_manager = getattr(request.app.state, "agent_sync_manager", None)
            if sync_manager:
                sync_manager.sync_workspace_tools(session_id)

        return ServerInstallResponse(
            server_id=updated.server_id,
            is_installed=updated.is_installed,
            status=updated.status,
            error_message=updated.error_message,
            type=updated.type,
        )
    except Exception as e:
        logger.exception("uninstall_server_failed", server_id=server_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to uninstall MCP server: {e}",
        )


@router.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
@traced("mcp.server.delete")
async def delete_server_endpoint(
    server_id: str, engine: McpEngine = Depends(get_mcp_engine)
):
    logger.info("deleting_server", server_id=server_id)

    server = get_server(engine.db_path, server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP Server '{server_id}' not found.",
        )

    try:
        # First ensure runner is stopped and tools are cleared
        await engine.stop_server(server_id)
        # Delete server from database
        delete_server(engine.db_path, server_id)
        # Clean up any saved credentials
        delete_secrets(server_id)

        # Sync removal with the active Wright gateway profile.
        server.is_active = False
        sync_mcp_server_to_wright_gateway(server)

        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.exception("delete_server_failed", server_id=server_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete MCP server: {e}",
        )


@router.get("/tools", response_model=ToolsListResponse)
@traced("mcp.tool.list")
async def list_tools_endpoint(engine: McpEngine = Depends(get_mcp_engine)):
    try:
        tools = get_tools(engine.db_path)
        return ToolsListResponse(tools=tools)
    except Exception as e:
        logger.exception("list_tools_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list MCP tools: {e}",
        )


@router.patch("/tools/{tool_id}", response_model=ToolToggleResponse)
@traced("mcp.tool.toggle")
async def toggle_tool_enabled(
    tool_id: str, body: ToolToggleRequest, engine: McpEngine = Depends(get_mcp_engine)
):
    logger.info("toggling_tool_enabled", tool_id=tool_id, is_enabled=body.is_enabled)

    tool = get_tool(engine.db_path, tool_id)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP Tool '{tool_id}' not found.",
        )

    try:
        success = update_tool_enabled(engine.db_path, tool_id, body.is_enabled)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update tool state in database.",
            )
        return ToolToggleResponse(tool_id=tool_id, is_enabled=body.is_enabled)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("toggle_tool_failed", tool_id=tool_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle tool enabled state: {e}",
        )


@router.get("/servers/{server_id}/version-check")
@traced("mcp.server.version_check")
async def version_check_endpoint(
    server_id: str, engine: McpEngine = Depends(get_mcp_engine)
):
    server = get_server(engine.db_path, server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP Server '{server_id}' not found.",
        )
    if server.type in ("sse", "webmcp"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Version check not applicable for network-type servers.",
        )

    from tool_registry.version_check import check_server_version

    result = await check_server_version(server)
    if "error" in result and result["error"] is not None:
        if result["error"] == "unsupported_package_manager":
            return {
                "server_id": server_id,
                "installed": None,
                "latest": None,
                "update_available": False,
                "error": result["error"],
            }
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Version check failed: {result['error']}",
        )
    return result


@router.post("/servers/{server_id}/update")
@traced("mcp.server.update")
async def update_server_endpoint(
    server_id: str, engine: McpEngine = Depends(get_mcp_engine)
):
    server = get_server(engine.db_path, server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP Server '{server_id}' not found.",
        )
    if server.type != "stdio":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Update not applicable for network-type servers.",
        )

    from tool_registry.version_check import update_server

    result = await update_server(server)
    if result.get("error"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {result['error']}",
        )

    from tool_registry.db import update_server as db_update_server

    db_update_server(
        engine.db_path,
        server_id,
        {
            "installed_version": result["installed_version"],
            "updated_at": int(time.time()),
        },
    )

    return {
        "server_id": server_id,
        "installed_version": result["installed_version"],
        "success": True,
        "error": None,
    }


# ── Credential Management Endpoints ──────────────────────────────────────────


@router.get("/servers/{server_id}/credentials", response_model=CredentialStatusResponse)
@traced("mcp.server.credentials.get")
async def get_credential_status(
    server_id: str, engine: McpEngine = Depends(get_mcp_engine)
):
    """Get credential definitions and configured status for a server.
    Never returns actual credential values."""
    server = get_server(engine.db_path, server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP Server '{server_id}' not found.",
        )

    env_var_defs = []
    configured = {}
    if server.env_vars and isinstance(server.env_vars, list):
        env_var_defs = [
            v.model_dump() if isinstance(v, EnvVarDefinition) else v
            for v in server.env_vars
        ]
        var_names = [v.name for v in server.env_vars if isinstance(v, EnvVarDefinition)]
        configured = has_credentials(server_id, var_names)

    return CredentialStatusResponse(
        server_id=server_id,
        env_vars=env_var_defs,
        configured=configured,
    )


@router.put("/servers/{server_id}/credentials", response_model=CredentialStatusResponse)
@traced("mcp.server.credentials.save")
async def save_credentials(
    server_id: str,
    body: SaveCredentialsRequest,
    engine: McpEngine = Depends(get_mcp_engine),
):
    """Save credential values for a server. Values are stored in the local
    secrets file, never in the database or API responses."""
    server = get_server(engine.db_path, server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP Server '{server_id}' not found.",
        )

    # Validate credentials are strings — never log values
    sanitized: dict = {}
    for key, value in body.credentials.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credential keys and values must be strings.",
            )
        if value.strip():
            sanitized[key] = value

    logger.info("saving_credentials", server_id=server_id, var_count=len(sanitized))
    if sanitized:
        existing = read_secrets(server_id)
        write_secrets(server_id, {**existing, **sanitized})

    # Return updated configured status
    env_var_defs = []
    configured = {}
    if server.env_vars and isinstance(server.env_vars, list):
        env_var_defs = [
            v.model_dump() if isinstance(v, EnvVarDefinition) else v
            for v in server.env_vars
        ]
        var_names = [v.name for v in server.env_vars if isinstance(v, EnvVarDefinition)]
        configured = has_credentials(server_id, var_names)

    return CredentialStatusResponse(
        server_id=server_id,
        env_vars=env_var_defs,
        configured=configured,
    )


@router.delete(
    "/servers/{server_id}/credentials", status_code=status.HTTP_204_NO_CONTENT
)
@traced("mcp.server.credentials.delete")
async def delete_credentials_endpoint(
    server_id: str, engine: McpEngine = Depends(get_mcp_engine)
):
    """Delete all saved credentials for a server."""
    server = get_server(engine.db_path, server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP Server '{server_id}' not found.",
        )

    logger.info("deleting_credentials", server_id=server_id)
    delete_secrets(server_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
