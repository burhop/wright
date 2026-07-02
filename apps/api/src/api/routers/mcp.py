import structlog
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel
from tool_registry import (
    McpServer,
    McpServerCreate,
    McpTool,
)
from core.tracing import traced
from api.services.mcp_services import (
    McpApiService,
    get_mcp_api_service,
    mcp_service_http_exception,
)
from tool_registry.services import McpServiceError

logger = structlog.get_logger(__name__)
router = APIRouter()

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
async def list_servers(service: McpApiService = Depends(get_mcp_api_service)):
    try:
        return ServersListResponse(servers=service.list_servers())
    except McpServiceError as e:
        raise mcp_service_http_exception(e)
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
    body: McpServerCreate,
    service: McpApiService = Depends(get_mcp_api_service),
):
    logger.info("registering_server", name=body.name, type=body.type)
    try:
        new_server = service.register_server(body)
        return RegisterServerResponse(
            server_id=new_server.server_id,
            name=new_server.name,
            status=new_server.status,
        )
    except McpServiceError as e:
        raise mcp_service_http_exception(e)
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
    service: McpApiService = Depends(get_mcp_api_service),
):
    logger.info(
        "toggling_server_activation",
        server_id=server_id,
        target_is_active=body.is_active,
    )

    try:
        updated = await service.toggle_server_activation(server_id, body.is_active)
        return ServerToggleResponse(
            server_id=updated.server_id,
            is_active=updated.is_active,
            status=updated.status,
            error_message=updated.error_message,
            type=updated.type,
        )
    except McpServiceError as e:
        raise mcp_service_http_exception(e)
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
    session_id: Optional[str] = None,
    service: McpApiService = Depends(get_mcp_api_service),
):
    logger.info("installing_server", server_id=server_id, session_id=session_id)

    try:
        updated = await service.install_server(server_id, session_id)
        return ServerInstallResponse(
            server_id=updated.server_id,
            is_installed=updated.is_installed,
            status=updated.status,
            error_message=updated.error_message,
            type=updated.type,
        )
    except McpServiceError as e:
        raise mcp_service_http_exception(e)
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
    service: McpApiService = Depends(get_mcp_api_service),
):
    try:
        result = service.validate_server(server_id)
        return ValidateServerResponse(**result.model_dump())
    except McpServiceError as e:
        raise mcp_service_http_exception(e)


@router.post(
    "/servers/report-missing",
    response_model=RegisterServerResponse,
    status_code=status.HTTP_201_CREATED,
)
@traced("mcp.server.report_missing")
async def report_missing_mcp(
    body: MissingMcpReportRequest,
    service: McpApiService = Depends(get_mcp_api_service),
):
    try:
        server = service.report_missing_server(body)
    except McpServiceError as e:
        raise mcp_service_http_exception(e)
    return RegisterServerResponse(
        server_id=server.server_id,
        name=server.name,
        status=server.status,
    )


@router.post("/servers/{server_id}/uninstall", response_model=ServerInstallResponse)
@traced("mcp.server.uninstall")
async def uninstall_server_endpoint(
    server_id: str,
    session_id: Optional[str] = None,
    service: McpApiService = Depends(get_mcp_api_service),
):
    logger.info("uninstalling_server", server_id=server_id, session_id=session_id)

    try:
        updated = await service.uninstall_server(server_id, session_id)
        return ServerInstallResponse(
            server_id=updated.server_id,
            is_installed=updated.is_installed,
            status=updated.status,
            error_message=updated.error_message,
            type=updated.type,
        )
    except McpServiceError as e:
        raise mcp_service_http_exception(e)
    except Exception as e:
        logger.exception("uninstall_server_failed", server_id=server_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to uninstall MCP server: {e}",
        )


@router.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
@traced("mcp.server.delete")
async def delete_server_endpoint(
    server_id: str, service: McpApiService = Depends(get_mcp_api_service)
):
    logger.info("deleting_server", server_id=server_id)

    try:
        await service.delete_server(server_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except McpServiceError as e:
        raise mcp_service_http_exception(e)
    except Exception as e:
        logger.exception("delete_server_failed", server_id=server_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete MCP server: {e}",
        )


@router.get("/tools", response_model=ToolsListResponse)
@traced("mcp.tool.list")
async def list_tools_endpoint(service: McpApiService = Depends(get_mcp_api_service)):
    try:
        return ToolsListResponse(tools=service.list_tools())
    except McpServiceError as e:
        raise mcp_service_http_exception(e)
    except Exception as e:
        logger.exception("list_tools_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list MCP tools: {e}",
        )


@router.patch("/tools/{tool_id}", response_model=ToolToggleResponse)
@traced("mcp.tool.toggle")
async def toggle_tool_enabled(
    tool_id: str,
    body: ToolToggleRequest,
    service: McpApiService = Depends(get_mcp_api_service),
):
    logger.info("toggling_tool_enabled", tool_id=tool_id, is_enabled=body.is_enabled)

    try:
        service.set_tool_enabled(tool_id, body.is_enabled)
        return ToolToggleResponse(tool_id=tool_id, is_enabled=body.is_enabled)
    except McpServiceError as e:
        raise mcp_service_http_exception(e)
    except Exception as e:
        logger.exception("toggle_tool_failed", tool_id=tool_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle tool enabled state: {e}",
        )


@router.get("/servers/{server_id}/version-check")
@traced("mcp.server.version_check")
async def version_check_endpoint(
    server_id: str, service: McpApiService = Depends(get_mcp_api_service)
):
    try:
        return await service.check_server_version(server_id)
    except McpServiceError as e:
        raise mcp_service_http_exception(e)


@router.post("/servers/{server_id}/update")
@traced("mcp.server.update")
async def update_server_endpoint(
    server_id: str, service: McpApiService = Depends(get_mcp_api_service)
):
    try:
        return await service.update_server_version(server_id)
    except McpServiceError as e:
        raise mcp_service_http_exception(e)


# ── Credential Management Endpoints ──────────────────────────────────────────


@router.get("/servers/{server_id}/credentials", response_model=CredentialStatusResponse)
@traced("mcp.server.credentials.get")
async def get_credential_status(
    server_id: str, service: McpApiService = Depends(get_mcp_api_service)
):
    """Get credential definitions and configured status for a server.
    Never returns actual credential values."""
    try:
        return CredentialStatusResponse(**service.get_credential_status(server_id))
    except McpServiceError as e:
        raise mcp_service_http_exception(e)


@router.put("/servers/{server_id}/credentials", response_model=CredentialStatusResponse)
@traced("mcp.server.credentials.save")
async def save_credentials(
    server_id: str,
    body: SaveCredentialsRequest,
    service: McpApiService = Depends(get_mcp_api_service),
):
    """Save credential values for a server. Values are stored in the local
    secrets file, never in the database or API responses."""
    try:
        status_data = service.save_credentials(server_id, body.credentials)
        return CredentialStatusResponse(**status_data)
    except McpServiceError as e:
        raise mcp_service_http_exception(e)


@router.delete(
    "/servers/{server_id}/credentials", status_code=status.HTTP_204_NO_CONTENT
)
@traced("mcp.server.credentials.delete")
async def delete_credentials_endpoint(
    server_id: str, service: McpApiService = Depends(get_mcp_api_service)
):
    """Delete all saved credentials for a server."""
    logger.info("deleting_credentials", server_id=server_id)
    try:
        service.delete_credentials(server_id)
    except McpServiceError as e:
        raise mcp_service_http_exception(e)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
