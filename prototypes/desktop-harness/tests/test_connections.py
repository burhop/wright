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


@pytest.mark.asyncio
async def test_signin_urls_are_only_in_private_metadata(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from mcp_bridge import server

    private_url = "https://issuer.example/authorize?state=synthetic-private"
    client = SimpleNamespace(
        scope=AsyncMock(),
        call=AsyncMock(
            return_value={
                "workspace_id": "w",
                "session_id": "s",
                "plan_id": "p",
                "presentation": "awaiting_user",
                "authorization_url": private_url,
                "callback_uri": "http://127.0.0.1:9505/oauth/callback",
            }
        ),
    )
    bridge = server(client)
    tool = next(
        t for t in await bridge.list_tools() if t.name == "wright_connection_signin"
    )
    assert tool.meta["ui"]["visibility"] == ["app"]
    result = await bridge.call_tool(
        "wright_connection_signin",
        {"workspace_id": "w", "session_id": "s", "plan_id": "p"},
    )
    assert result.meta["wright/signin"]["authorization_url"] == private_url
    assert private_url not in str(result.content)
    assert private_url not in str(result.structuredContent)
    assert "9505" not in str(result.structuredContent)


@pytest.mark.asyncio
async def test_connection_readback_exposes_saved_validation_without_repeating_it(
    monkeypatch,
):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from mcp_bridge import server

    data = catalog()
    evidence = {
        "evidence_id": "v1",
        "state": "stale",
        "observed_at": "2026-10-14T00:00:00Z",
        "reason_codes": ["validation_evidence_expired"],
    }
    data["capabilities"][0]["local_validation"] = {
        **evidence,
        "unrelated_private_field": "do not disclose",
    }
    client = SimpleNamespace(scope=AsyncMock(), call=AsyncMock(return_value=data))
    _, result = await server(client).call_tool(
        "wright_connections_list", {"workspace_id": "w", "session_id": "s"}
    )
    assert result["connections"][0]["local_validation"] == evidence
    assert "do not disclose" not in str(result)
    client.call.assert_awaited_once_with(
        "GET", "/api/mcp/capabilities", params={"search": "", "limit": 50}
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("capability", [None, "import:custom"])
async def test_saved_plan_discovery_can_omit_provider_but_always_scopes_workspace(
    monkeypatch, capability
):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from mcp_bridge import server

    client = SimpleNamespace(
        scope=AsyncMock(), call=AsyncMock(return_value={"plans": []})
    )
    args = {"workspace_id": "workspace", "session_id": "session"}
    if capability is not None:
        args["capability_id"] = capability
    await server(client).call_tool("wright_connection_plans", args)
    client.scope.assert_awaited_once_with("workspace", "session")
    client.call.assert_awaited_once_with(
        "GET", "/api/desktop/connection-plans", params=args
    )
