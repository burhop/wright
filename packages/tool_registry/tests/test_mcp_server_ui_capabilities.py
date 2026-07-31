from __future__ import annotations

import anyio
import pytest
from mcp import ClientSession
import mcp.types as types

from tool_registry.gateway_models import GatewayTool
from tool_registry.mcp_server import (
    _mcp_tool,
    create_mcp_server,
    initialization_options,
)
from tool_registry.models import McpUiToolMetadata
from tool_registry.runners.protocol import MCP_APPS_EXTENSION, MCP_APP_MIME_TYPE
from test_gateway_service import service


def test_ui_extension_is_advertised_only_when_full_host_is_enabled() -> None:
    gateway, _, _ = service()
    disabled = initialization_options(create_mcp_server(gateway, "s1"))
    enabled = initialization_options(
        create_mcp_server(gateway, "s1", ui_enabled=True)
    )

    assert disabled.capabilities.experimental in (None, {})
    assert enabled.capabilities.experimental == {
        MCP_APPS_EXTENSION: {"mimeTypes": [MCP_APP_MIME_TYPE]}
    }


def test_tool_projection_merges_canonical_ui_and_opaque_upstream_metadata() -> None:
    upstream = {
        "ui": {
            "resourceUri": "ui://reference/app",
            "visibility": ["model", "app"],
        },
        "vendor/opaque": {"preserve": True},
    }
    projected = _mcp_tool(
        GatewayTool(
            name="reference__render",
            server_id="reference",
            tool_name="render",
            description="Render",
            input_schema={"type": "object"},
            upstream_meta=upstream,
            ui=McpUiToolMetadata.from_upstream(upstream),
            provenance={"source": "child"},
        )
    )

    assert projected.meta["ui"] == upstream["ui"]
    assert projected.meta["vendor/opaque"] == {"preserve": True}
    assert projected.meta["wright/serverId"] == "reference"
    assert projected.meta["wright/provenance"] == {"source": "child"}


def test_upstream_cannot_overwrite_wright_authority_or_provenance() -> None:
    projected = _mcp_tool(
        GatewayTool(
            name="reference__render",
            server_id="reference",
            tool_name="render",
            description="Render",
            input_schema={},
            upstream_meta={
                "wright/serverId": "foreign",
                "wright/provenance": {"source": "forged"},
                "wright/safetyReviewed": False,
            },
            provenance={"source": "verified"},
        )
    )

    assert projected.meta["wright/serverId"] == "reference"
    assert projected.meta["wright/provenance"] == {"source": "verified"}
    assert projected.meta["wright/safetyReviewed"] is True


@pytest.mark.asyncio
async def test_server_round_trip_preserves_all_result_blocks_structured_and_meta() -> None:
    gateway, lifecycle, _ = service()
    lifecycle.result = {
        "content": [
            {"type": "text", "text": "fallback"},
            {"type": "image", "data": "aW1hZ2U=", "mimeType": "image/png"},
            {"type": "audio", "data": "YXVkaW8=", "mimeType": "audio/wav"},
            {
                "type": "resource_link",
                "uri": "ui://reference/details",
                "name": "Details",
            },
            {
                "type": "resource",
                "resource": {
                    "uri": "wright://artifact/w1/result.txt",
                    "mimeType": "text/plain",
                    "text": "embedded",
                },
            },
        ],
        "structuredContent": {"server": "cad", "workspace": "w1"},
        "_meta": {"ui": {"resourceUri": "ui://reference/app"}, "opaque": 9},
        "isError": False,
    }
    server = create_mcp_server(gateway, "s1", ui_enabled=True)
    client_write, server_read = anyio.create_memory_object_stream(10)
    server_write, client_read = anyio.create_memory_object_stream(10)

    async with anyio.create_task_group() as group:
        group.start_soon(
            server.run,
            server_read,
            server_write,
            initialization_options(server),
        )
        async with ClientSession(client_read, client_write) as client:
            await client.initialize()
            result = await client.call_tool("cad__run", {})
            assert [type(item) for item in result.content] == [
                types.TextContent,
                types.ImageContent,
                types.AudioContent,
                types.ResourceLink,
                types.EmbeddedResource,
            ]
            assert result.structuredContent == {"server": "cad", "workspace": "w1"}
            assert result.meta == {
                "ui": {"resourceUri": "ui://reference/app"},
                "opaque": 9,
            }
        group.cancel_scope.cancel()
