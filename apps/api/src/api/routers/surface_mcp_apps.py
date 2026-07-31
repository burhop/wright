"""Authenticated, surface-scoped transport for packaged MCP Apps."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Any, Literal
from urllib.parse import urlunsplit

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

from api.config import get_workspace_surface_settings
from api.routers.surfaces import get_surface_actor, get_surface_service
from core.surfaces.errors import SurfaceError
from core.surfaces.models import McpAppSurfaceSource, SurfaceDescriptor, SurfaceId
from tool_registry.gateway_models import (
    GatewayError,
    GatewayErrorCode,
    GatewayToolResult,
)
from tool_registry.gateway_service import GatewayService
from workspace_service.surfaces.service import SurfaceActor, SurfaceService


router = APIRouter(prefix="/surfaces/{surface_id}/mcp-app")


class _ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class McpAppResourceResponse(_ContractModel):
    html: str
    media_type: str = Field(alias="mediaType")
    csp: dict[str, Any] | None = None
    granted_permissions: dict[str, Any] = Field(
        default_factory=dict, alias="grantedPermissions"
    )


class McpAppProjectionResponse(_ContractModel):
    capability: Literal["supported", "absent", "unsupported"]
    protocol_version: str | None = Field(default=None, alias="protocolVersion")
    reason: str | None = None
    content_hash: str | None = Field(default=None, alias="contentHash")
    sandbox_origin: str | None = Field(default=None, alias="sandboxOrigin")
    resource: McpAppResourceResponse | None = None
    fallback_result: dict[str, Any] | None = Field(default=None, alias="fallbackResult")
    initial_tool_input: dict[str, Any] | None = Field(
        default=None, alias="initialToolInput"
    )
    initial_tool_result: dict[str, Any] | None = Field(
        default=None, alias="initialToolResult"
    )
    host_capabilities: list[str] = Field(default_factory=list, alias="hostCapabilities")


class OperationRequest(_ContractModel):
    request_id: str = Field(alias="requestId", min_length=1, max_length=128)


class ToolCallRequest(OperationRequest):
    name: str = Field(min_length=1, max_length=512)
    arguments: dict[str, Any] = Field(default_factory=dict)


class ResourceReadRequest(OperationRequest):
    uri: str = Field(min_length=1, max_length=2048)


def get_gateway_service(request: Request) -> GatewayService:
    gateway = getattr(request.app.state, "gateway_service", None)
    if gateway is None:
        raise HTTPException(status_code=503, detail="MCP_APP_GATEWAY_UNAVAILABLE")
    return gateway


async def _mcp_surface(
    *,
    actor: SurfaceActor,
    surface_id: str,
    service: SurfaceService,
) -> tuple[SurfaceDescriptor, McpAppSurfaceSource]:
    try:
        descriptor = await service.get(actor=actor, surface_id=SurfaceId(surface_id))
    except (SurfaceError, ValueError) as error:
        raise HTTPException(
            status_code=404, detail="MCP_APP_SURFACE_NOT_FOUND"
        ) from error
    if not isinstance(descriptor.source, McpAppSurfaceSource):
        raise HTTPException(status_code=409, detail="SURFACE_SOURCE_NOT_MCP_APP")
    return descriptor, descriptor.source


def _sandbox_origin() -> str:
    preview = get_workspace_surface_settings().preview
    port = (
        ""
        if (preview.scheme, preview.public_port)
        in {
            ("https", 443),
            ("http", 80),
        }
        else f":{preview.public_port}"
    )
    return urlunsplit(
        (preview.scheme, f"mcp-sandbox.{preview.domain}{port}", "", "", "")
    )


def _tool_result(result: GatewayToolResult) -> dict[str, Any]:
    payload: dict[str, Any] = {"content": [dict(item) for item in result.content]}
    if result.structured_content is not None:
        payload["structuredContent"] = dict(result.structured_content)
    if result.meta:
        payload["_meta"] = dict(result.meta)
    if result.is_error:
        payload["isError"] = True
    return payload


def _gateway_error(error: GatewayError) -> HTTPException:
    status_code = {
        GatewayErrorCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
        GatewayErrorCode.POLICY_DENIED: status.HTTP_403_FORBIDDEN,
        GatewayErrorCode.INVALID_INPUT: status.HTTP_400_BAD_REQUEST,
        GatewayErrorCode.TIMEOUT: status.HTTP_504_GATEWAY_TIMEOUT,
        GatewayErrorCode.CHILD_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
    }.get(error.code, status.HTTP_409_CONFLICT)
    return HTTPException(status_code=status_code, detail=error.code.value)


@router.get("/presentation", response_model=McpAppProjectionResponse)
async def get_mcp_app_presentation(
    surface_id: str,
    actor: Annotated[SurfaceActor, Depends(get_surface_actor)],
    service: Annotated[SurfaceService, Depends(get_surface_service)],
    gateway: Annotated[GatewayService, Depends(get_gateway_service)],
) -> McpAppProjectionResponse:
    _descriptor, source = await _mcp_surface(
        actor=actor, surface_id=surface_id, service=service
    )
    fallback = dict(source.fallback_result) if source.fallback_result else None
    settings = get_workspace_surface_settings()
    if not settings.flags.mcp_apps:
        return McpAppProjectionResponse(
            capability="absent",
            reason="MCP Apps are disabled for this Wright deployment.",
            fallbackResult=fallback,
        )
    try:
        binding = await gateway.read_app_resource(
            source.gateway_session_id,
            f"projection:{surface_id}",
            source.server_id,
            source.server_id,
            source.resource_uri,
        )
    except GatewayError as error:
        raise _gateway_error(error) from error
    if (
        binding.server_connection_id != source.server_connection_id
        or binding.content_hash != source.content_hash
    ):
        return McpAppProjectionResponse(
            capability="supported",
            protocolVersion=source.protocol_version,
            reason=(
                "The MCP App resource changed after this surface was created. "
                "Run the tool again to open the current version."
            ),
            fallbackResult=fallback,
        )
    if not isinstance(binding.content, str):
        return McpAppProjectionResponse(
            capability="supported",
            protocolVersion=source.protocol_version,
            reason="The MCP App resource is not a text HTML document.",
            fallbackResult=fallback,
        )
    raw_csp = binding.metadata.ui.get("csp")
    csp = dict(raw_csp) if isinstance(raw_csp, Mapping) else None
    return McpAppProjectionResponse(
        capability="supported",
        protocolVersion=source.protocol_version,
        contentHash=binding.content_hash,
        sandboxOrigin=_sandbox_origin(),
        resource=McpAppResourceResponse(
            html=binding.content,
            mediaType=binding.media_type,
            csp=csp,
            # Requested device permissions remain denied until an exact grant exists.
            grantedPermissions={},
        ),
        fallbackResult=fallback,
        initialToolInput=(
            dict(source.initial_tool_input) if source.initial_tool_input else None
        ),
        initialToolResult=fallback,
        hostCapabilities=[],
    )


@router.post("/tools/call")
async def call_mcp_app_tool(
    surface_id: str,
    body: ToolCallRequest,
    actor: Annotated[SurfaceActor, Depends(get_surface_actor)],
    service: Annotated[SurfaceService, Depends(get_surface_service)],
    gateway: Annotated[GatewayService, Depends(get_gateway_service)],
) -> dict[str, Any]:
    _descriptor, source = await _mcp_surface(
        actor=actor, surface_id=surface_id, service=service
    )
    try:
        return _tool_result(
            await gateway.call_app_tool(
                source.gateway_session_id,
                body.request_id,
                source.server_id,
                body.name,
                body.arguments,
            )
        )
    except GatewayError as error:
        raise _gateway_error(error) from error


@router.post("/resources/list")
async def list_mcp_app_resources(
    surface_id: str,
    body: OperationRequest,
    actor: Annotated[SurfaceActor, Depends(get_surface_actor)],
    service: Annotated[SurfaceService, Depends(get_surface_service)],
    gateway: Annotated[GatewayService, Depends(get_gateway_service)],
) -> Mapping[str, Any]:
    _descriptor, source = await _mcp_surface(
        actor=actor, surface_id=surface_id, service=service
    )
    try:
        return await gateway.list_app_resources(
            source.gateway_session_id, body.request_id, source.server_id
        )
    except GatewayError as error:
        raise _gateway_error(error) from error


@router.post("/resource-templates/list")
async def list_mcp_app_resource_templates(
    surface_id: str,
    body: OperationRequest,
    actor: Annotated[SurfaceActor, Depends(get_surface_actor)],
    service: Annotated[SurfaceService, Depends(get_surface_service)],
    gateway: Annotated[GatewayService, Depends(get_gateway_service)],
) -> Mapping[str, Any]:
    _descriptor, source = await _mcp_surface(
        actor=actor, surface_id=surface_id, service=service
    )
    try:
        return await gateway.list_app_resource_templates(
            source.gateway_session_id, body.request_id, source.server_id
        )
    except GatewayError as error:
        raise _gateway_error(error) from error


@router.post("/resources/read")
async def read_mcp_app_resource(
    surface_id: str,
    body: ResourceReadRequest,
    actor: Annotated[SurfaceActor, Depends(get_surface_actor)],
    service: Annotated[SurfaceService, Depends(get_surface_service)],
    gateway: Annotated[GatewayService, Depends(get_gateway_service)],
) -> dict[str, Any]:
    _descriptor, source = await _mcp_surface(
        actor=actor, surface_id=surface_id, service=service
    )
    try:
        binding = await gateway.read_app_resource(
            source.gateway_session_id,
            body.request_id,
            source.server_id,
            source.server_id,
            body.uri,
        )
    except GatewayError as error:
        raise _gateway_error(error) from error
    content: dict[str, Any] = {
        "uri": binding.upstream_resource_uri,
        "mimeType": binding.media_type,
    }
    if isinstance(binding.content, str):
        content["text"] = binding.content
    else:
        import base64

        content["blob"] = base64.b64encode(binding.content).decode("ascii")
    return {"contents": [content]}


@router.delete("/operations/{request_id}", status_code=204)
async def cancel_mcp_app_operation(
    surface_id: str,
    request_id: str,
    actor: Annotated[SurfaceActor, Depends(get_surface_actor)],
    service: Annotated[SurfaceService, Depends(get_surface_service)],
    gateway: Annotated[GatewayService, Depends(get_gateway_service)],
) -> None:
    _descriptor, source = await _mcp_surface(
        actor=actor, surface_id=surface_id, service=service
    )
    gateway.cancel(source.gateway_session_id, request_id, "MCP App request aborted")


__all__ = ["get_gateway_service", "router"]
