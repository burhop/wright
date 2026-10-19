import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def controls(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from mcp_bridge import server

    client = SimpleNamespace(
        scope=AsyncMock(), call=AsyncMock(return_value={"state": "owner"})
    )
    return server(client), client


def request(**extra):
    return {
        "workspace_id": "a",
        "session_id": "chat-a",
        "capability_id": "provider",
        "server_id": "registered",
        "shared_scope": "wright-host",
        "control_digest": "a" * 64,
        "operation": "stop",
        **extra,
    }


def test_connection_control_ports_are_app_only_and_preserve_exact_subject(controls):
    server, client = controls
    tools = {tool.name: tool for tool in asyncio.run(server.list_tools())}
    for name in ("wright_connection_controls", "wright_connection_control"):
        assert tools[name].meta["ui"]["visibility"] == ["app"]
    assert tools["wright_connection_controls"].annotations.readOnlyHint is True
    assert tools["wright_connection_control"].annotations.readOnlyHint is False
    assert tools["wright_connection_control"].annotations.destructiveHint is True
    result = asyncio.run(
        server.call_tool("wright_connection_control", {"request": request()})
    )[1]
    assert result["ok"]
    client.scope.assert_awaited_once_with("a", "chat-a")
    client.call.assert_awaited_once_with(
        "POST", "/api/desktop/connection-controls", json=request()
    )


@pytest.mark.parametrize(
    "extra",
    [
        {"workspace_dir": "/other"},
        {"operation": "dispatch"},
        {"operation": "tool-enable"},
        {"tool_id": "unexpected-for-stop"},
        {"operation": "uninstall", "tool_id": "unexpected-for-uninstall"},
        {"approval_mode": "auto"},
        {"shared_scope": "workspace"},
    ],
)
def test_control_cannot_expand_authority_before_owner(controls, extra):
    server, client = controls
    with pytest.raises(Exception):
        asyncio.run(
            server.call_tool("wright_connection_control", {"request": request(**extra)})
        )
    client.scope.assert_not_awaited()
    client.call.assert_not_awaited()


@pytest.mark.parametrize("status,known", [(403, True), (409, True), (503, False)])
def test_control_rejection_and_uncertainty_never_retry(controls, status, known):
    from native_source_tools import WrightRequestRejected

    server, client = controls
    client.call.side_effect = WrightRequestRejected(status, "PRIVATE diagnostics")
    result = asyncio.run(
        server.call_tool("wright_connection_control", {"request": request()})
    )[1]
    assert result["error"]["outcome_known"] is known
    assert "PRIVATE" not in str(result)
    client.call.assert_awaited_once()


def test_uninstall_port_preserves_exact_scope_without_session_sync_override(controls):
    server, client = controls
    result = asyncio.run(
        server.call_tool(
            "wright_connection_control", {"request": request(operation="uninstall")}
        )
    )[1]
    assert result["ok"]
    client.call.assert_awaited_once_with(
        "POST", "/api/desktop/connection-controls", json=request(operation="uninstall")
    )
