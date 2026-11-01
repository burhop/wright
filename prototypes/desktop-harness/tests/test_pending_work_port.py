"""Attention navigation stays scoped and cannot dispatch or expose run payloads."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def pending(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from mcp_bridge import server

    document = {
        "workspace_id": "workspace",
        "checkpoints": {
            "items": [
                {
                    "checkpoint_id": "c1",
                    "workflow_path": "workflows/handle.wflow",
                    "run_id": "run-1",
                    "path": "runs/run-1.json",
                    "source_digest": "a" * 64,
                    "state": "pending",
                    "action_kind": "local_review",
                    "execution_context": {"private": "must not leave owner"},
                }
            ],
            "next_cursor": None,
        },
        "reviews": {"items": [], "next_cursor": None},
        "private": "unrequested top-level data",
    }
    client = SimpleNamespace(scope=AsyncMock(), call=AsyncMock(return_value=document))
    return server(client), client, document


@pytest.mark.asyncio
async def test_attention_is_app_only_scoped_navigation_projection(pending):
    server, client, _ = pending
    tools = {tool.name: tool for tool in await server.list_tools()}
    tool = tools["wright_workspace_pending"]
    assert tool.annotations.readOnlyHint is True
    assert tool.meta["ui"]["visibility"] == ["app"]
    _, result = await server.call_tool(
        "wright_workspace_pending",
        {
            "workspace_id": "workspace",
            "session_id": "session",
            "checkpoint_after": "c0",
        },
    )
    assert result["checkpoints"]["items"][0]["run_id"] == "run-1"
    assert "execution_context" not in result["checkpoints"]["items"][0]
    assert "private" not in result
    client.scope.assert_awaited_once_with("workspace", "session")
    client.call.assert_awaited_once_with(
        "GET",
        "/api/workspace/workflow-sources/pending",
        params={"session_id": "session", "checkpoint_after": "c0", "review_after": ""},
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "patch",
    [
        {"workspace_id": "other"},
        {"checkpoints": None},
        {"reviews": {"items": [{}] * 21, "next_cursor": None}},
        {"reviews": {"items": ["invalid"], "next_cursor": None}},
    ],
)
async def test_attention_rejects_wrong_scope_or_invalid_page(pending, patch):
    server, _, document = pending
    document.update(patch)
    with pytest.raises(Exception):
        await server.call_tool(
            "wright_workspace_pending",
            {"workspace_id": "workspace", "session_id": "session"},
        )


@pytest.mark.asyncio
async def test_attention_denied_scope_never_reads(pending):
    server, client, _ = pending
    client.scope.side_effect = ValueError("Unavailable")
    with pytest.raises(Exception):
        await server.call_tool(
            "wright_workspace_pending",
            {"workspace_id": "workspace", "session_id": "other"},
        )
    client.call.assert_not_awaited()
