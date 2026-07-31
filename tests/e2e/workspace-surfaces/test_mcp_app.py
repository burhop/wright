from __future__ import annotations

import sys
from pathlib import Path

import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from pydantic import AnyUrl

from tool_registry.gateway_models import GatewaySessionContext, GatewayTool
from tool_registry.models import McpUiToolMetadata
from tool_registry.ui.policy import McpUiPolicy

ROOT = Path(__file__).parents[3]
EXAMPLE = ROOT / "examples" / "workspace-surfaces" / "mcp_app_server"
APP_URI = "ui://wright.reference/design"


@pytest.mark.asyncio
async def test_reference_mcp_app_exact_read_fallback_and_teardown() -> None:
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(EXAMPLE / "server.py")],
        cwd=EXAMPLE,
    )
    async with stdio_client(parameters) as streams:
        async with ClientSession(*streams) as session:
            initialized = await session.initialize()
            assert "io.modelcontextprotocol/ui" in (
                initialized.capabilities.experimental or {}
            )

            resources = await session.list_resources()
            assert resources.resources == []  # exact read must not depend on listing

            tools = {tool.name: tool for tool in (await session.list_tools()).tools}
            assert tools["show_design"].meta["ui"] == {
                "resourceUri": APP_URI,
                "visibility": ["model", "app"],
            }

            resource = await session.read_resource(AnyUrl(APP_URI))
            assert resource.contents[0].mimeType == "text/html;profile=mcp-app"
            assert "Wright reference design" in resource.contents[0].text
            assert "requestTeardown" in resource.contents[0].text

            fallback = await session.call_tool("show_design", {})
            assert not fallback.isError
            assert "Design: bracket" in fallback.content[0].text
            assert fallback.structuredContent["shape"] == "bracket"
    # Leaving both official SDK contexts closes stdio and revokes the server connection.


def test_reference_mcp_app_policy_authorizes_same_server_and_denies_other_scope() -> None:
    session = GatewaySessionContext(
        session_id="session",
        principal_id="engineer",
        workspace_id="workspace",
        workspace_path=str(EXAMPLE),
        transport="stdio",
    )
    policy = McpUiPolicy()

    def tool(name: str, server_id: str, visibility: list[str]) -> GatewayTool:
        return GatewayTool(
            name=f"{server_id}__{name}",
            server_id=server_id,
            tool_name=name,
            description=name,
            input_schema={"type": "object"},
            ui=McpUiToolMetadata.from_upstream(
                {"ui": {"visibility": visibility}}
            ),
        )

    allowed = policy.can_call_tool(
        session,
        tool("resize_design", "reference", ["app"]),
        {"width": 90, "height": 60},
        app_server_id="reference",
    )
    model_only = policy.can_call_tool(
        session,
        tool("model_only_status", "reference", ["model"]),
        {},
        app_server_id="reference",
    )
    cross_server = policy.can_call_tool(
        session,
        tool("resize_design", "other", ["app"]),
        {},
        app_server_id="reference",
    )

    assert (allowed.allowed, allowed.reason_code) == (True, "same_server_policy_allowed")
    assert (model_only.allowed, model_only.reason_code) == (False, "model_only")
    assert (cross_server.allowed, cross_server.reason_code) == (False, "cross_server_denied")
