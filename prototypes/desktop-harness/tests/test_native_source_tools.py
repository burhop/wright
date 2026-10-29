import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from mcp.server.fastmcp import FastMCP


@pytest.fixture
def native_save(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from native_source_tools import register_native_source_tools

    client = SimpleNamespace(
        scope=AsyncMock(), call=AsyncMock(return_value={"source": "accepted"})
    )
    server = FastMCP("native-source-test")
    register_native_source_tools(server, client)
    return server, client


def args():
    return {
        "workspace_id": "workspace",
        "session_id": "session",
        "path": "workflows/test.workflow.wflow",
        "source": "proposed",
        "expected_storage_revision": 7,
        "expected_storage_digest": "a" * 64,
        "semantic_change_validated": True,
        "layout": {"version": 1},
        "expected_layout_revision": 2,
    }


def test_save_forwards_exact_cas_and_layout_identity(native_save):
    server, client = native_save
    _, result = asyncio.run(server.call_tool("wright_workflow_save", args()))
    assert result == {"ok": True, "document": {"source": "accepted"}}
    client.scope.assert_awaited_once_with("workspace", "session")
    payload = client.call.call_args.kwargs["json"]
    assert payload["expected_storage_revision"] == 7
    assert payload["expected_storage_digest"] == "a" * 64
    assert payload["expected_layout_revision"] == 2
    assert payload["source"] == "proposed"
    assert client.call.call_args.args == ("PUT", "/api/workspace/workflow-sources")
    assert client.call.await_count == 1


def test_wrong_scope_never_reaches_source_write(native_save):
    server, client = native_save
    client.scope.side_effect = PermissionError("scope differs")
    with pytest.raises(Exception, match="scope differs"):
        asyncio.run(server.call_tool("wright_workflow_save", args()))
    client.call.assert_not_awaited()


def test_layout_needs_explicit_revision(native_save):
    server, client = native_save
    with pytest.raises(Exception, match="expected revision"):
        asyncio.run(
            server.call_tool(
                "wright_workflow_save", {**args(), "expected_layout_revision": None}
            )
        )
    client.call.assert_not_awaited()


@pytest.mark.parametrize(
    "status,known,code",
    [
        (403, True, "PERMISSION_DENIED"),
        (409, True, "WORKFLOW_SOURCE_CONFLICT"),
        (500, False, "SOURCE_UNAVAILABLE"),
    ],
)
def test_failure_is_explicit_without_retry(native_save, status, known, code):
    server, client = native_save
    request = httpx.Request("PUT", "http://private/api/workspace/workflow-sources")
    response = httpx.Response(status, request=request)
    client.call.side_effect = httpx.HTTPStatusError(
        "private diagnostics omitted", request=request, response=response
    )
    _, result = asyncio.run(server.call_tool("wright_workflow_save", args()))
    assert result["ok"] is False
    assert result["error"]["code"] == code
    assert result["error"]["outcome_known"] is known
    assert "private" not in result["error"]["message"]
    assert client.call.await_count == 1


@pytest.mark.parametrize("status", [403, 409, 500])
def test_real_transport_retains_http_status(native_save, status, monkeypatch):
    from mcp_bridge import WrightDesktopClient

    server, client = native_save
    transport = WrightDesktopClient.__new__(WrightDesktopClient)
    transport.http = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                status, json={"detail": "private diagnostics"}, request=request
            )
        ),
        base_url="http://private",
    )
    client.call = transport.call
    _, result = asyncio.run(server.call_tool("wright_workflow_save", args()))
    assert result["error"]["outcome_known"] is (status != 500)
    assert "private" not in result["error"]["message"]


def test_real_scope_denial_is_known_and_never_writes(native_save):
    from native_source_tools import WrightRequestRejected

    server, client = native_save
    client.scope.side_effect = WrightRequestRejected(403, "private scope diagnostics")
    _, result = asyncio.run(server.call_tool("wright_workflow_save", args()))
    assert result["error"]["code"] == "PERMISSION_DENIED"
    assert result["error"]["outcome_known"] is True
    client.call.assert_not_awaited()


def test_editor_tool_discovery_is_app_only_scoped_and_read_only(native_save):
    server, client = native_save
    tool = {
        "name": "cad.inspect",
        "server_id": "cad",
        "tool_name": "inspect",
        "title": "Inspect CAD",
        "description": "Inspect the selected document",
        "input_schema": {"type": "object"},
        "output_schema": None,
        "schema_digest": "b" * 64,
    }
    client.call.side_effect = [
        {"tools": [tool]},
        {
            "servers": [
                {"server_id": "cad", "name": "Study CAD", "private_config": "omitted"}
            ]
        },
    ]
    _, result = asyncio.run(
        server.call_tool(
            "wright_workflow_editor_tools",
            {
                "request": {"workspace_id": "workspace", "session_id": "session"},
            },
        )
    )
    assert result == {
        "workspace_id": "workspace",
        "session_id": "session",
        "tools": [{**tool, "server_name": "Study CAD", "workspace_server": True}],
    }
    client.scope.assert_awaited_once_with("workspace", "session")
    assert client.call.await_count == 2
    assert client.call.call_args_list[0].args == (
        "GET",
        "/api/workspace/workflow-sources/tools",
    )
    assert client.call.call_args_list[0].kwargs == {"params": {"session_id": "session"}}
    assert client.call.call_args_list[1].args == ("GET", "/api/mcp/servers")
    registered = next(
        t
        for t in asyncio.run(server.list_tools())
        if t.name == "wright_workflow_editor_tools"
    )
    assert registered.meta["ui"]["visibility"] == ["app"]
    assert registered.annotations.readOnlyHint is True


def test_editor_tool_discovery_scope_denial_makes_no_request(native_save):
    server, client = native_save
    client.scope.side_effect = PermissionError("scope differs")
    with pytest.raises(Exception, match="scope differs"):
        asyncio.run(
            server.call_tool(
                "wright_workflow_editor_tools",
                {
                    "request": {"workspace_id": "other", "session_id": "session"},
                },
            )
        )
    client.call.assert_not_awaited()


@pytest.mark.parametrize(
    "tools", [None, {}, [None], [{"token": "must not leave owner"}]]
)
def test_editor_tool_discovery_rejects_invalid_metadata(native_save, tools):
    server, client = native_save
    client.call.return_value = {"tools": tools}
    with pytest.raises(Exception, match="invalid workflow tool"):
        asyncio.run(
            server.call_tool(
                "wright_workflow_editor_tools",
                {
                    "request": {"workspace_id": "workspace", "session_id": "session"},
                },
            )
        )
    assert client.call.await_count == 1
