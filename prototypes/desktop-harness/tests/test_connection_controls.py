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
    repository.create(
        "alpha",
        "chat-alpha",
        str(directory),
        workspace_name="Alpha",
        agent_id="openai-desktop-harness",
    )
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
    sync = Mock()
    repository.set_active_gateway_session("chat-alpha")
    owner = McpApiService(
        engine,
        SimpleNamespace(
            gateway_service=gateway,
            agent_sync_manager=SimpleNamespace(sync_workspace_tools=sync),
        ),
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


@pytest.mark.asyncio
async def test_shared_uninstall_uses_existing_owner_and_preserves_configuration_and_grants(
    controls, monkeypatch
):
    app, owner, repository, engine, gateway, sync, directory = controls
    from api.services.mcp_services import registry_services

    delete_secrets = Mock()
    monkeypatch.setattr(registry_services, "delete_secrets", delete_secrets)
    manager = Mock()
    owner.app_state.agent_sync_manager = manager
    before = get_server(owner.db_path, "playwright-mcp")
    repository.set_enabled_tools("alpha", ["playwright-mcp"])
    repository.create(
        "beta", "chat-beta", str(directory.parent / "beta"), workspace_name="Beta"
    )
    repository.set_enabled_tools("beta", ["playwright-mcp"])
    grants = {key: repository.enabled_tools(key) for key in ("alpha", "beta")}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        state = (
            await client.get("/api/desktop/connection-controls", params=scope)
        ).json()["state"]
        request = {
            **scope,
            "shared_scope": "wright-host",
            "control_digest": state["control_digest"],
            "operation": "uninstall",
        }
        result = await client.post("/api/desktop/connection-controls", json=request)
        assert result.status_code == 200 and "PRIVATE" not in result.text
        after = result.json()["state"]
        assert not after["active"] and not after["installed"]
        registered = get_server(owner.db_path, "playwright-mcp")
        assert (
            registered.command == before.command
            and registered.launch_env == before.launch_env
        )
        assert registered.installed_version == before.installed_version
        assert {key: repository.enabled_tools(key) for key in grants} == grants
        engine.stop_server.assert_awaited_once_with("playwright-mcp")
        manager.sync_workspace_tools.assert_not_called()
        sync.assert_not_called()
        delete_secrets.assert_not_called()
        gateway.publish_list_changes.assert_called_once_with(workspace_id=None)
        # Repeating either a stale request or a new uninstall cannot stop again.
        assert (
            await client.post("/api/desktop/connection-controls", json=request)
        ).status_code == 409
        assert (
            await client.post(
                "/api/desktop/connection-controls",
                json={**request, "control_digest": after["control_digest"]},
            )
        ).status_code == 409
        engine.stop_server.assert_awaited_once()


@pytest.mark.asyncio
async def test_uninstall_denied_and_uncertain_outcomes_never_repeat_owner(controls):
    from api.security import require_admin

    app, owner, _, engine, _, _, _ = controls
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        state = (
            await client.get("/api/desktop/connection-controls", params=scope)
        ).json()["state"]
        request = {
            **scope,
            "shared_scope": "wright-host",
            "control_digest": state["control_digest"],
            "operation": "uninstall",
        }
        app.dependency_overrides.pop(require_admin)
        assert (
            await client.post("/api/desktop/connection-controls", json=request)
        ).status_code == 403
        app.dependency_overrides[require_admin] = lambda: None
        for patch, status in [
            ({"session_id": "foreign"}, 403),
            ({"control_digest": "f" * 64}, 409),
            ({"tool_id": "inspect"}, 422),
        ]:
            assert (
                await client.post(
                    "/api/desktop/connection-controls", json={**request, **patch}
                )
            ).status_code == status
        engine.stop_server.assert_not_awaited()
        owner.uninstall_server = AsyncMock(side_effect=OSError("PRIVATE diagnostic"))
        failed = await client.post("/api/desktop/connection-controls", json=request)
        assert failed.status_code == 503 and "PRIVATE" not in failed.text
        owner.uninstall_server.assert_awaited_once_with("playwright-mcp")


@pytest.mark.asyncio
async def test_saved_provider_status_is_scoped_read_only_and_redacted(
    controls, monkeypatch
):
    app, owner, repository, engine, gateway, sync, directory = controls
    plan = SimpleNamespace(
        workspace_id="alpha",
        requested_scope="workspace",
        state="completed",
        capability_id="playwright-mcp",
        plan_digest="a" * 64,
    )
    monkeypatch.setattr(owner, "get_install_plan", Mock(return_value=plan))
    get_view = Mock(
        return_value=SimpleNamespace(
            local_validation={
                "evidence_id": "saved",
                "state": "passed",
                "observed_at": "2026-10-17",
                "private": "PRIVATE_VALIDATION",
            },
            user_state=SimpleNamespace(
                installed=True,
                active=False,
                enabled_workspaces=[
                    {"workspace_id": "alpha"},
                    {"workspace_id": "OTHER_PRIVATE", "label": "PRIVATE_LABEL"},
                ],
            ),
        )
    )
    monkeypatch.setattr(owner, "get_capability", get_view)
    validate = AsyncMock()
    enable = Mock()
    monkeypatch.setattr(owner, "run_capability_validation", validate)
    monkeypatch.setattr(owner, "enable_capability_for_workspace", enable)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        params = {"workspace_id": "alpha", "session_id": "chat-alpha"}
        result = await client.get(
            "/api/desktop/connection-plans/saved/signin", params=params
        )
        assert result.status_code == 200
        data = result.json()
        assert data["plan_digest"] == "a" * 64
        assert data["provider_status"] == {
            "installed": True,
            "active": False,
            "enabled_here": True,
            "recorded_validation": {
                "evidence_id": "saved",
                "state": "passed",
                "observed_at": "2026-10-17",
            },
        }
        assert (
            "PRIVATE" not in result.text
            and result.headers["cache-control"] == "no-store"
        )
        get_view.assert_called_once_with("playwright-mcp")
        for patch in [{"session_id": "foreign"}, {"workspace_id": "foreign"}]:
            denied = await client.get(
                "/api/desktop/connection-plans/saved/signin", params={**params, **patch}
            )
            assert denied.status_code in {403, 404}
        assert get_view.call_count == 1
        app.dependency_overrides.pop(
            __import__("api.security", fromlist=["require_admin"]).require_admin
        )
        denied = await client.get(
            "/api/desktop/connection-plans/saved/signin", params=params
        )
        assert denied.status_code == 403 and get_view.call_count == 1
    validate.assert_not_called()
    enable.assert_not_called()
    engine.start_server.assert_not_called()
    engine.stop_server.assert_not_called()


@pytest.mark.asyncio
async def test_explicit_replacement_read_requires_admin_exact_scope_and_current_source(
    controls,
):
    app, owner, repository, engine, gateway, sync, directory = controls
    from api.security import require_admin

    before = get_server(owner.db_path, "playwright-mcp")
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        state = (
            await client.get("/api/desktop/connection-controls", params=scope)
        ).json()["state"]
        request = {**scope, "control_digest": state["control_digest"]}
        # Legacy private configuration has no public projection, even on intent.
        denied = await client.post("/api/desktop/connection-replacement", json=request)
        assert denied.status_code == 409 and "PRIVATE" not in denied.text
        update_server(
            owner.db_path,
            "playwright-mcp",
            {
                "deployment_mode": "user-reviewed-import",
                "command": ["uvx", "example-mcp==1.0.0"],
                "launch_env": {"RUN_MODE": "read-only"},
            },
        )
        stale = await client.post("/api/desktop/connection-replacement", json=request)
        assert stale.status_code == 409
        state = (
            await client.get("/api/desktop/connection-controls", params=scope)
        ).json()["state"]
        assert "replacement" not in state and "command" not in state
        request["control_digest"] = state["control_digest"]
        current = get_server(owner.db_path, "playwright-mcp").model_dump_json()
        draft = await client.post("/api/desktop/connection-replacement", json=request)
        assert draft.status_code == 200
        assert draft.json()["configuration"]["arguments"] == ["example-mcp==1.0.0"]
        assert draft.json()["configuration"]["name"] == ""
        assert get_server(owner.db_path, "playwright-mcp").model_dump_json() == current
        cross_scope = await client.post(
            "/api/desktop/connection-replacement",
            json={**request, "session_id": "wrong"},
        )
        assert cross_scope.status_code == 403
        app.dependency_overrides.pop(require_admin)
        forbidden = await client.post(
            "/api/desktop/connection-replacement", json=request
        )
        assert forbidden.status_code == 403
    engine.start_server.assert_not_awaited()
    engine.stop_server.assert_not_awaited()
    gateway.assert_not_called()
    assert before.command == ["fixture-command", "PRIVATE_CONFIGURATION"]
