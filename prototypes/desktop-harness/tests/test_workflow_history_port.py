"""The native history port delegates to the canonical recorded-source owner."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def history(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from mcp_bridge import server

    document = {
        "workspace_id": "workspace",
        "workflow_path": "workflows/part.wflow",
        "runs": [
            {
                "run_id": "run",
                "status": "waiting_human",
                "path": "runs/part/run.json",
                "source_digest": "a" * 64,
                "started_at": "2026-10-14T00:00:00Z",
                "completed_at": None,
                "results": [{"private_payload": "not-needed-in-home"}],
            }
        ],
    }
    client = SimpleNamespace(scope=AsyncMock(), call=AsyncMock(return_value=document))
    return server(client), client, document


@pytest.mark.asyncio
async def test_history_retains_recorded_identities_without_result_payloads(history):
    server, client, document = history
    _, result = await server.call_tool(
        "wright_workflow_history",
        {
            "workspace_id": "workspace",
            "session_id": "session",
            "path": document["workflow_path"],
        },
    )
    assert result["runs"][0]["source_digest"] == "a" * 64
    assert result["runs"][0]["status"] == "waiting_human"
    assert "results" not in result["runs"][0]
    client.scope.assert_awaited_once_with("workspace", "session")
    client.call.assert_awaited_once_with(
        "GET",
        "/api/workspace/workflow-sources/runs",
        params={"session_id": "session", "path": document["workflow_path"]},
    )
    assert "results" in document["runs"][0]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "patch",
    [
        {"workspace_id": "other"},
        {"workflow_path": "workflows/other.wflow"},
        {"runs": None},
        {"runs": [{}] * 21},
        {"runs": ["invalid"]},
    ],
)
async def test_wrong_history_scope_or_shape_is_denied(history, patch):
    server, _, document = history
    document.update(patch)
    with pytest.raises(Exception):
        await server.call_tool(
            "wright_workflow_history",
            {
                "workspace_id": "workspace",
                "session_id": "session",
                "path": "workflows/part.wflow",
            },
        )


@pytest.mark.asyncio
async def test_denied_session_never_reads_history(history):
    server, client, _ = history
    client.scope.side_effect = ValueError("Workspace unavailable")
    with pytest.raises(Exception):
        await server.call_tool(
            "wright_workflow_history",
            {
                "workspace_id": "workspace",
                "session_id": "other",
                "path": "workflows/part.wflow",
            },
        )
    client.call.assert_not_awaited()
