import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def bridge(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from mcp_bridge import server

    client = SimpleNamespace(
        scope=AsyncMock(), call=AsyncMock(return_value={"path": "saved"})
    )
    return server(client), client


def request(**extra):
    return {
        "workspace_id": "a",
        "session_id": "session-a",
        "filename": "data.csv",
        "content_base64": "YQ==",
        "sha256": "a" * 64,
        **extra,
    }


def test_upload_is_app_only_and_forwards_exact_typed_scope(bridge):
    server, client = bridge
    tools = {tool.name: tool for tool in asyncio.run(server.list_tools())}
    tool = tools["wright_workspace_file_upload"]
    assert tool.meta["ui"]["visibility"] == ["app"]
    assert tool.annotations.readOnlyHint is False
    result = asyncio.run(server.call_tool(tool.name, {"request": request()}))[1]
    assert result["ok"] is True
    client.scope.assert_awaited_once_with("a", "session-a")
    client.call.assert_awaited_once_with(
        "POST", "/api/desktop/files/upload", json=request()
    )


@pytest.mark.parametrize(
    "extra",
    [
        {"path": "overwrite"},
        {"run": True},
        {"approval_mode": "auto"},
        {"sha256": "bad"},
        {"content_base64": ""},
    ],
)
def test_invalid_upload_authority_does_not_call_owner(bridge, extra):
    server, client = bridge
    with pytest.raises(Exception):
        asyncio.run(
            server.call_tool(
                "wright_workspace_file_upload", {"request": request(**extra)}
            )
        )
    client.scope.assert_not_awaited()
    client.call.assert_not_awaited()


@pytest.mark.parametrize(
    "status,known", [(403, True), (409, True), (422, True), (503, False)]
)
def test_rejected_and_uncertain_upload_outcomes_never_retry(bridge, status, known):
    from native_source_tools import WrightRequestRejected

    server, client = bridge
    client.call.side_effect = WrightRequestRejected(status, "PRIVATE raw diagnostics")
    result = asyncio.run(
        server.call_tool("wright_workspace_file_upload", {"request": request()})
    )[1]
    assert result["error"]["outcome_known"] is known
    assert "PRIVATE" not in str(result)
    client.call.assert_awaited_once()
