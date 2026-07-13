from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any

import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.lowlevel.helper_types import ReadResourceContents
from pydantic import AnyUrl

from .gateway_models import GatewayError, SessionState
from .gateway_service import GatewayService, SUPPORTED_PROTOCOL_VERSION


def create_mcp_server(
    service: GatewayService,
    gateway_session_id: str,
) -> Server:
    pump_task: asyncio.Task[None] | None = None

    @asynccontextmanager
    async def lifespan(_: Server):
        nonlocal pump_task
        try:
            yield {}
        finally:
            if pump_task is not None:
                pump_task.cancel()
                await asyncio.gather(pump_task, return_exceptions=True)

    server = Server(
        "wright-gateway",
        version="0.1.0",
        instructions=(
            "Wright exposes only tools and resources authorized for the explicitly "
            "bound engineering workspace. Tool annotations are descriptive hints; "
            "Wright policy remains authoritative."
        ),
        lifespan=lifespan,
    )

    async def ensure_initialized() -> None:
        nonlocal pump_task
        context = service._session(gateway_session_id, allow_created=True)
        if context.state is SessionState.CREATED:
            parameters = server.request_context.session.client_params
            client_info = parameters.clientInfo if parameters is not None else None
            capabilities = parameters.capabilities if parameters is not None else None
            context = service.initialize_session(
                gateway_session_id,
                protocol_version=(
                    str(parameters.protocolVersion)
                    if parameters is not None
                    else SUPPORTED_PROTOCOL_VERSION
                ),
                client_name=client_info.name if client_info is not None else "unknown",
                client_version=(
                    client_info.version if client_info is not None else "unknown"
                ),
                client_capabilities=(
                    capabilities.model_dump(mode="json")
                    if capabilities is not None
                    else {}
                ),
            )
        if pump_task is None:
            sdk_session = server.request_context.session

            async def pump_notifications() -> None:
                async for event in service.notifier.subscribe(context):
                    if event == "tools/list_changed":
                        await sdk_session.send_tool_list_changed()
                    elif event == "resources/list_changed":
                        await sdk_session.send_resource_list_changed()

            pump_task = asyncio.create_task(pump_notifications())

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        await ensure_initialized()
        return [_mcp_tool(tool) for tool in service.list_tools(gateway_session_id)]

    @server.call_tool(validate_input=True)
    async def call_tool(name: str, arguments: dict[str, Any]) -> types.CallToolResult:
        await ensure_initialized()
        request_id = str(server.request_context.request_id)
        try:
            result = await service.call_tool(
                gateway_session_id,
                request_id,
                name,
                arguments,
            )
        except GatewayError as error:
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=str(error))],
                structuredContent={"error": error.code.value},
                isError=True,
            )
        return types.CallToolResult(
            content=[
                types.TextContent(type="text", text=str(item.get("text", "")))
                for item in result.content
                if item.get("type") == "text"
            ],
            structuredContent=(
                dict(result.structured_content)
                if result.structured_content is not None
                else None
            ),
            isError=result.is_error,
        )

    @server.list_resources()
    async def list_resources() -> list[types.Resource]:
        await ensure_initialized()
        return [
            types.Resource(
                uri=AnyUrl(resource.uri),
                name=resource.name,
                description=resource.description,
                mimeType=resource.mime_type,
                _meta={"wright/provenance": dict(resource.provenance)},
            )
            for resource in service.list_resources(gateway_session_id)
        ]

    @server.read_resource()
    async def read_resource(uri) -> list[ReadResourceContents]:
        await ensure_initialized()
        result = service.read_resource(gateway_session_id, str(uri))
        return [ReadResourceContents(result.content, result.mime_type)]

    return server


def initialization_options(server: Server):
    return server.create_initialization_options(
        notification_options=NotificationOptions(
            tools_changed=True,
            resources_changed=True,
        ),
        experimental_capabilities={},
    )


def _mcp_tool(tool) -> types.Tool:
    annotations = dict(tool.annotations)
    sdk_annotations = types.ToolAnnotations(
        title=annotations.get("title"),
        readOnlyHint=annotations.get("readOnlyHint"),
        destructiveHint=annotations.get("destructiveHint"),
        idempotentHint=annotations.get("idempotentHint"),
        openWorldHint=annotations.get("openWorldHint"),
    )
    return types.Tool(
        name=tool.name,
        description=tool.description,
        inputSchema=dict(tool.input_schema),
        outputSchema=(
            dict(tool.output_schema) if tool.output_schema is not None else None
        ),
        annotations=sdk_annotations,
        _meta={
            "wright/serverId": tool.server_id,
            "wright/toolName": tool.tool_name,
            "wright/approvalGates": annotations.get("approval_gates", []),
            "wright/provenance": dict(tool.provenance),
            "wright/safetyReviewed": True,
        },
    )
