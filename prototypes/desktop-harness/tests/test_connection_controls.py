"""Operator controls reuse actual registry owners and never grant workspace access."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from fastapi import FastAPI
import httpx
import pytest

from data_vault import WorkspaceRepository, upgrade_database
from tool_registry import McpServer, McpTool
from tool_registry.db import (
    get_server,
    get_tools,
    insert_server,
    insert_tools,
    update_server,
)


@pytest.fixture
def controls(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from desktop_backend import DesktopBackend
    from api.security import SecuritySettings, require_admin
    from api.services.mcp_services import McpApiService, get_mcp_api_service

    database = str(tmp_path / "state.db")
    upgrade_database(database)
    repository = WorkspaceRepository(database, secrets=Mock())
    directory = tmp_path / "workspaces" / "alpha"
    directory.mkdir(parents=True)
    repository.create("alpha", "chat-alpha", str(directory), workspace_name="Alpha")
    repository.associate_session(
        "alpha", "chat-alpha", agent_id="openai-desktop-harness"
    )
    identity = "playwright-mcp"
    insert_server(
        database,
        McpServer(
            server_id=identity,
            name="Playwright",
            type="stdio",
            command=["fixture-command", "PRIVATE_CONFIGURATION"],
            launch_env={"CONFIG": "PRIVATE_VALUE"},
            is_active=False,
            is_installed=True,
            status="inactive",
            created_at=1,
            updated_at=1,
        ),
    )
    insert_tools(
        database,
        [
            McpTool(
                tool_id="inspect",
                server_id=identity,
                name="inspect",
                input_schema={"type": "object"},
                is_enabled=True,
                created_at=1,
            )
        ],
    )
    runner = SimpleNamespace(cwd=None)
    engine = SimpleNamespace(
        db_path=database, lifecycle=SimpleNamespace(runner_for=lambda _: runner)
    )

    async def start(server_id, *, workspace_dir=None, approval_context=None):
        runner.cwd = workspace_dir
        return update_server(
            database, server_id, {"is_active": True, "status": "active"}
        )

    async def stop(server_id):
        runner.cwd = None
        return update_server(
            database, server_id, {"is_active": False, "status": "inactive"}
        )

    engine.start_server = AsyncMock(side_effect=start)
    engine.stop_server = AsyncMock(side_effect=stop)
    gateway = Mock()
    owner = McpApiService(engine, SimpleNamespace(gateway_service=gateway))
    sync = Mock()
    monkeypatch.setattr(
        "api.services.mcp_services.sync_mcp_server_to_wright_gateway", sync
    )
    backend = DesktopBackend(
        SimpleNamespace(db_path=database, repository=repository), tmp_path, 5207
    )
    app = FastAPI()
    app.state.security_settings = SecuritySettings(
        "enforced", "synthetic-operator-token", (), "127.0.0.1"
    )
    app.include_router(backend.router())
    app.dependency_overrides[get_mcp_api_service] = lambda: owner
    app.dependency_overrides[require_admin] = lambda: None
    return app, owner, repository, engine, gateway, sync, directory


scope = {
    "workspace_id": "alpha",
    "session_id": "chat-alpha",
    "capability_id": "playwright-mcp",
    "server_id": "playwright-mcp",
}


@pytest.mark.asyncio
async def test_actual_owner_switches_preserve_workspace_grants_and_harness_config(
    controls,
):
    app, owner, repository, engine, gateway, sync, directory = controls
    memberships = repository.enabled_tools("alpha")
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        read = await client.get("/api/desktop/connection-controls", params=scope)
        assert read.status_code == 200 and "PRIVATE" not in read.text
        before = read.json()["state"]
        request = {
            **scope,
            "shared_scope": "wright-host",
            "control_digest": before["control_digest"],
            "operation": "tool-disable",
            "tool_id": "inspect",
        }
        disabled = await client.post("/api/desktop/connection-controls", json=request)
        assert disabled.status_code == 200
        state = disabled.json()["state"]
        assert state["tools"][0]["enabled"] is False
        assert get_tools(owner.db_path, "playwright-mcp")[0].is_enabled is False
        stale = await client.post("/api/desktop/connection-controls", json=request)
        assert stale.status_code == 409
        started = await client.post(
            "/api/desktop/connection-controls",
            json={
                **scope,
                "shared_scope": "wright-host",
                "control_digest": state["control_digest"],
                "operation": "start",
            },
        )
        assert started.status_code == 200
        state = started.json()["state"]
        assert state["active"] and state["bound_workspace_id"] == "alpha"
        assert engine.start_server.call_args.kwargs["workspace_dir"] == str(directory)
        stopped = await client.post(
            "/api/desktop/connection-controls",
            json={
                **scope,
                "shared_scope": "wright-host",
                "control_digest": state["control_digest"],
                "operation": "stop",
            },
        )
        assert stopped.status_code == 200 and not stopped.json()["state"]["active"]
        assert repository.enabled_tools("alpha") == memberships
        assert get_server(owner.db_path, "playwright-mcp").is_installed
        sync.assert_not_called()
        assert gateway.publish_list_changes.call_count == 3


@pytest.mark.asyncio
async def test_authority_and_subject_denials_prevent_owner_calls(controls):
    from api.security import require_admin

    app, owner, _, engine, _, sync, _ = controls
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        state = (
            await client.get("/api/desktop/connection-controls", params=scope)
        ).json()["state"]
        body = {
            **scope,
            "shared_scope": "wright-host",
            "control_digest": state["control_digest"],
            "operation": "start",
        }
        app.dependency_overrides.pop(require_admin)
        assert (
            await client.post("/api/desktop/connection-controls", json=body)
        ).status_code == 403
        app.dependency_overrides[require_admin] = lambda: None
        for extra, status in [
            ({"session_id": "other"}, 403),
            ({"server_id": "other"}, 409),
            ({"operation": "tool-enable", "tool_id": "other-provider:tool"}, 403),
            ({"operation": "tool-enable"}, 422),
            ({"tool_id": "inspect"}, 422),
            ({"shared_scope": "workspace"}, 422),
            ({"approval_mode": "auto"}, 422),
        ]:
            response = await client.post(
                "/api/desktop/connection-controls", json={**body, **extra}
            )
            assert response.status_code == status, response.text
        update_server(owner.db_path, "playwright-mcp", {"installed_version": "changed"})
        assert (
            await client.post("/api/desktop/connection-controls", json=body)
        ).status_code == 409
        engine.start_server.assert_not_awaited()
        engine.stop_server.assert_not_awaited()
        sync.assert_not_called()


@pytest.mark.asyncio
async def test_existing_agent_profile_sync_remains_default_for_legacy_caller(controls):
    _, owner, _, engine, gateway, sync, _ = controls
    await owner.toggle_server_activation("playwright-mcp", True)
    sync.assert_called_once()
    gateway.publish_list_changes.assert_called_once()
    assert "workspace_dir" not in engine.start_server.call_args.kwargs


@pytest.mark.asyncio
@pytest.mark.parametrize("failure,status", [(OSError("PRIVATE"), 503)])
async def test_owner_failure_requires_readback_without_repeat(
    controls, failure, status
):
    app, owner, _, _, _, _, _ = controls
    owner.toggle_server_activation = AsyncMock(side_effect=failure)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        state = (
            await client.get("/api/desktop/connection-controls", params=scope)
        ).json()["state"]
        response = await client.post(
            "/api/desktop/connection-controls",
            json={
                **scope,
                "shared_scope": "wright-host",
                "control_digest": state["control_digest"],
                "operation": "start",
            },
        )
        assert response.status_code == status and "PRIVATE" not in response.text
        owner.toggle_server_activation.assert_awaited_once()
