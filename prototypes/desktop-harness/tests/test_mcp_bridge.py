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
