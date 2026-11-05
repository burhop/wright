"""Scoped engineering option reads retain existing API/gateway ownership."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from mcp.server.fastmcp import FastMCP
from api.desktop.native_source_tools import register_native_source_tools


def fixture():
    client = SimpleNamespace(
        scope=AsyncMock(), call=AsyncMock(return_value={"supported": False})
    )
    server = FastMCP("options-test")
    register_native_source_tools(server, client)
    return server, client


@pytest.mark.parametrize(
    "kind,flag", [("cad", "documents"), ("application", "resources")]
)
@pytest.mark.parametrize("include", [False, True])
def test_exact_owner_read(kind, flag, include):
    server, client = fixture()
    _, result = asyncio.run(
        server.call_tool(
            "wright_workflow_editor_options",
            {
                "request": {
                    "workspace_id": "workspace",
                    "session_id": "session",
                    "kind": kind,
                    "server_id": "engineering-tool",
                    "include_resources": include,
                }
            },
        )
    )
    client.scope.assert_awaited_once_with("workspace", "session")
    client.call.assert_awaited_once_with(
        "GET",
        f"/api/workspace/workflow-sources/{kind}",
        params={
            "session_id": "session",
            "server_id": "engineering-tool",
            flag: "true" if include else "false",
        },
    )
    assert result == {
        "workspace_id": "workspace",
        "session_id": "session",
        "kind": kind,
        "options": {"supported": False},
    }


@pytest.mark.parametrize(
    "extra",
    [
        {"kind": "../run", "server_id": "tool"},
        {"kind": "cad"},
        {"kind": "input-files", "server_id": "tool"},
        {"kind": "input-files", "include_resources": True},
        {"kind": "cad", "server_id": "tool", "include_resources": "true"},
        {"kind": "cad", "server_id": "tool", "url": "https://outside.example"},
    ],
)
def test_rejects_ambiguous_or_arbitrary_requests(extra):
    server, client = fixture()
    with pytest.raises(Exception):
        asyncio.run(
            server.call_tool(
                "wright_workflow_editor_options",
                {
                    "request": {
                        "workspace_id": "workspace",
                        "session_id": "session",
                        **extra,
                    }
                },
            )
        )
    client.call.assert_not_awaited()


def test_scope_denial_precedes_owner_read():
    server, client = fixture()
    client.scope.side_effect = PermissionError("denied")
    with pytest.raises(Exception, match="denied"):
        asyncio.run(
            server.call_tool(
                "wright_workflow_editor_options",
                {
                    "request": {
                        "workspace_id": "foreign",
                        "session_id": "session",
                        "kind": "cad",
                        "server_id": "tool",
                    }
                },
            )
        )
    client.call.assert_not_awaited()
