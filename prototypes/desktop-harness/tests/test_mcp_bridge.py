import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest


@pytest.fixture
def bridge(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    import mcp_bridge

    return mcp_bridge


def test_pinned_sdk_preserves_unattended_json_as_text(bridge):
    client = SimpleNamespace(
        scope=AsyncMock(), call=AsyncMock(return_value={"accepted": True})
    )
    server = bridge.server(client)
    step_json = json.dumps(
        {
            "version": "wright.unattended-step/1",
            "status": "completed",
            "response": "Result",
            "reason": None,
        }
    )
    asyncio.run(
        server.call_tool(
            "wright_reasoning_answer",
            {
                "workspace_id": "workspace",
                "session_id": "session",
                "request_id": "request",
                "request_digest": "a" * 64,
                "binding_digest": "b" * 64,
                "response_id": "response",
                "reply": step_json,
            },
        )
    )
    payload = client.call.call_args.kwargs["json"]
    assert payload["response"]["reply"] == step_json
    assert isinstance(payload["response"]["reply"], str)


def test_html_success_cannot_be_accepted_as_api_evidence(bridge):
    client = bridge.WrightDesktopClient.__new__(bridge.WrightDesktopClient)
    client.http = SimpleNamespace(
        request=AsyncMock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "text/html"},
                text="<html>Frontend fallback</html>",
            )
        )
    )
    with pytest.raises(RuntimeError, match="non-JSON"):
        asyncio.run(client.call("POST", "/api/workspace/workflow-sources", json={}))
    assert client.http.request.await_count == 1


def test_pinned_sdk_preserves_typed_action_and_original_arguments(bridge):
    client = SimpleNamespace(
        scope=AsyncMock(), call=AsyncMock(return_value={"accepted": True})
    )
    decision = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "inspection-proposal",
                "type": "function",
                "function": {
                    "name": "tool_0",
                    "arguments": '{"relativePath":"inputs/requirements.md"}',
                },
            }
        ],
    }
    asyncio.run(
        bridge.server(client).call_tool(
            "wright_reasoning_action",
            {
                "workspace_id": "workspace",
                "session_id": "session",
                "request_id": "request",
                "request_digest": "a" * 64,
                "binding_digest": "b" * 64,
                "response_id": "response",
                "decision": decision,
            },
        )
    )
    client.scope.assert_awaited_once_with("workspace", "session")
    assert client.call.await_count == 1
    assert client.call.call_args.kwargs["json"]["response"]["reply"] == decision


@pytest.mark.parametrize(
    "decision",
    [
        {"role": "assistant", "content": None, "tool_calls": []},
        {"role": "assistant", "content": "result", "extra_authority": True},
        {"role": "assistant", "tool_calls": [{"id": "one"}, {"id": "two"}]},
    ],
)
def test_invalid_action_never_reaches_wright_api(bridge, decision):
    from mcp.server.fastmcp.exceptions import ToolError

    client = SimpleNamespace(scope=AsyncMock(), call=AsyncMock())
    with pytest.raises(ToolError):
        asyncio.run(
            bridge.server(client).call_tool(
                "wright_reasoning_action",
                {
                    "workspace_id": "workspace",
                    "session_id": "session",
                    "request_id": "request",
                    "request_digest": "a" * 64,
                    "binding_digest": "b" * 64,
                    "response_id": "response",
                    "decision": decision,
                },
            )
        )
    client.scope.assert_not_awaited()
    client.call.assert_not_awaited()


def test_workspace_panel_has_scoped_read_only_metadata_and_versioned_resource(bridge):
    client = SimpleNamespace(scope=AsyncMock(), call=AsyncMock())

    async def inspect():
        server = bridge.server(client)
        tool = next(
            t for t in await server.list_tools() if t.name == "wright_workspace_panel"
        )
        assert tool.annotations.readOnlyHint is True
        assert tool.outputSchema["type"] == "object"
        assert tool.meta["ui"]["resourceUri"] == bridge.WORKSPACE_PANEL_URI
        assert tool.meta["openai/ui"]["entrypoints"] == [{"type": "thread"}]
        resource = (await server.read_resource(bridge.WORKSPACE_PANEL_URI))[0]
        assert resource.mime_type == "text/html;profile=mcp-app"
        assert resource.meta["ui"]["csp"] == {
            "connectDomains": [],
            "resourceDomains": [],
        }
        assert resource.content == bridge.WORKSPACE_PANEL_HTML
        assert "fetch(" not in resource.content

    asyncio.run(inspect())
    client.scope.assert_not_awaited()
    client.call.assert_not_awaited()


def test_workspace_panel_reads_only_exact_workspace_and_connection(bridge):
    workspace = {"workspace_id": "workspace", "workspace_name": "Lab"}
    client = SimpleNamespace(
        scope=AsyncMock(return_value=workspace),
        call=AsyncMock(return_value={"connected": True}),
    )
    result = asyncio.run(
        bridge.server(client).call_tool(
            "wright_workspace_panel",
            {"workspace_id": "workspace", "session_id": "session"},
        )
    )
    client.scope.assert_awaited_once_with("workspace", "session")
    client.call.assert_awaited_once_with("GET", "/api/desktop/connection")
    assert result[1] == {"connection": {"connected": True}, "workspace": workspace}


@pytest.mark.parametrize(
    "arguments", [{"workspace_id": "workspace"}, {"session_id": "session"}]
)
def test_incomplete_panel_scope_never_reads_api(bridge, arguments):
    from mcp.server.fastmcp.exceptions import ToolError

    client = SimpleNamespace(scope=AsyncMock(), call=AsyncMock())
    with pytest.raises(ToolError, match="together"):
        asyncio.run(
            bridge.server(client).call_tool("wright_workspace_panel", arguments)
        )
    client.scope.assert_not_awaited()
    client.call.assert_not_awaited()


def test_denied_workspace_panel_does_not_read_connection_or_another_workspace(bridge):
    from mcp.server.fastmcp.exceptions import ToolError

    client = SimpleNamespace(
        scope=AsyncMock(side_effect=ValueError("Scope denied")), call=AsyncMock()
    )
    with pytest.raises(ToolError, match="Scope denied"):
        asyncio.run(
            bridge.server(client).call_tool(
                "wright_workspace_panel",
                {"workspace_id": "other", "session_id": "session"},
            )
        )
    client.call.assert_not_awaited()
