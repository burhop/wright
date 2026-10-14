from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


def catalog():
    return {
        "snapshot": {
            "snapshot_id": "snapshot",
            "channel": "bundled",
            "sequence": 1,
            "offline": True,
            "updated_at": "2026-10-14T00:00:00Z",
        },
        "total": 1,
        "capabilities": [
            {
                "capability_id": "cad",
                "canonical_id": "cad",
                "name": "CAD",
                "vendor": "Example",
                "description": "Design tools",
                "lifecycle_stage": "design",
                "maturity": "preview",
                "evidence_class": "official_preview",
                "transport": "streamable_http",
                "locality": "remote",
                "risk_level": "medium",
                "installability_tier": "remote",
                "compatibility": {
                    "status": "compatible",
                    "platform_key": "linux-arm64",
                },
                "user_state": {
                    "installed": True,
                    "active": True,
                    "credentials_configured": {"secret-field-name": False},
                    "enabled_workspaces": [
                        {"workspace_id": "other", "label": "private other workspace"}
                    ],
                },
                "requirements": {"private_field": "not a panel field"},
            }
        ],
    }


@pytest.mark.asyncio
async def test_connection_summary_scopes_membership_and_does_not_disclose_other_workspaces(
    monkeypatch,
):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from mcp_bridge import server

    client = SimpleNamespace(scope=AsyncMock(), call=AsyncMock(return_value=catalog()))
    bridge = server(client)
    _, result = await bridge.call_tool(
        "wright_connections_list",
        {
            "workspace_id": "workspace",
            "session_id": "session",
            "search": "CAD",
            "cursor": "page",
        },
    )
    client.scope.assert_awaited_once_with("workspace", "session")
    client.call.assert_awaited_once_with(
        "GET",
        "/api/mcp/capabilities",
        params={"search": "CAD", "limit": 50, "cursor": "page"},
    )
    row = result["connections"][0]
    assert row["enabled_here"] is False
    assert row["credentials_missing"] is True
    assert "private other" not in str(result)
    assert "secret-field-name" not in str(result)
    assert "private_field" not in str(result)
    client.call.return_value["capabilities"][0]["user_state"][
        "enabled_workspaces"
    ].append({"workspace_id": "workspace", "label": "Here"})
    _, result = await bridge.call_tool(
        "wright_connections_list",
        {"workspace_id": "workspace", "session_id": "session"},
    )
    assert result["connections"][0]["enabled_here"] is True


@pytest.mark.asyncio
async def test_denied_scope_never_reads_catalog_and_invalid_catalog_is_not_empty_success(
    monkeypatch,
):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from mcp_bridge import server

    client = SimpleNamespace(
        scope=AsyncMock(side_effect=RuntimeError("scope denied")),
        call=AsyncMock(return_value={}),
    )
    bridge = server(client)
    args = {"workspace_id": "workspace", "session_id": "wrong"}
    with pytest.raises(Exception, match="scope denied"):
        await bridge.call_tool("wright_connections_list", args)
    client.call.assert_not_awaited()
    client.scope.side_effect = None
    with pytest.raises(Exception, match="validation"):
        await bridge.call_tool("wright_connections_list", args)
