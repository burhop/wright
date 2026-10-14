from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from fastapi import FastAPI
import httpx
import pytest

from data_vault import WorkspaceRepository, upgrade_database
from workspace_service.use_cases.lifecycle import WorkspaceLifecycleUseCases


@pytest.fixture
def discovery(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from desktop_backend import DesktopBackend

    database = str(tmp_path / "state.db")
    upgrade_database(database)
    secrets = Mock()
    repository = WorkspaceRepository(database, secrets=secrets)
    service = SimpleNamespace(
        db_path=database,
        repository=repository,
        lifecycle=WorkspaceLifecycleUseCases(repository),
        files=SimpleNamespace(
            tree=AsyncMock(return_value={"type": "directory", "children": []})
        ),
    )
    backend = DesktopBackend(service, tmp_path, 5207)
    app = FastAPI()
    app.state.desktop_service = service
    app.state.desktop_backend = backend
    app.include_router(backend.router())

    def create(name, *, agent="openai-desktop-harness", outside=False, missing=False):
        directory = tmp_path / ("outside" if outside else "workspaces") / name
        if not missing:
            directory.mkdir(parents=True)
        session = "desktop-" + name
        repository.create(name, session, str(directory), workspace_name=name)
        repository.associate_session(name, session, agent_id=agent)
        return directory

    return app, repository, secrets, create, tmp_path


async def read(app):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        return await client.get("/api/desktop/workspaces")


@pytest.mark.asyncio
async def test_lists_only_owned_desktop_scopes_without_rebinding(discovery):
    app, repository, secrets, create, _ = discovery
    create("Zulu")
    create("Alpha")
    create("Hermes", agent="hermes")
    create("Outside", outside=True)
    repository.associate_session(
        "Alpha", "new-hermes-default", agent_id="hermes", updated_at=9999999999
    )
    before = repository.list_all()
    sessions = repository.list_sessions("Alpha")
    response = await read(app)
    assert response.status_code == 200
    items = response.json()["workspaces"]
    assert [item["workspace_name"] for item in items] == ["Alpha", "Zulu"]
    assert items[0]["session_id"] == "desktop-Alpha"
    assert all(item["available"] for item in items)
    assert all("local_path" not in item and "git_token" not in item for item in items)
    assert repository.list_all() == before
    assert repository.list_sessions("Alpha") == sessions
    assert not secrets.mock_calls


@pytest.mark.asyncio
async def test_missing_owned_workspace_is_visible_but_unavailable(discovery):
    app, _, _, create, _ = discovery
    create("Missing", missing=True)
    response = await read(app)
    assert response.json()["workspaces"] == [
        {
            "workspace_id": "Missing",
            "session_id": "desktop-Missing",
            "workspace_name": "Missing",
            "available": False,
            "reason": "Workspace directory is unavailable",
        }
    ]


@pytest.mark.asyncio
async def test_symlink_outside_connection_does_not_disclose_workspace(discovery):
    app, _, _, create, root = discovery
    directory = create("Escape")
    directory.rmdir()
    target = root / "unrelated"
    target.mkdir()
    directory.symlink_to(target, target_is_directory=True)
    assert (await read(app)).json() == {"workspaces": []}


@pytest.mark.asyncio
async def test_catalog_failure_is_not_reported_as_empty_success(discovery, monkeypatch):
    app, repository, _, _, _ = discovery
    monkeypatch.setattr(
        repository, "list_all", Mock(side_effect=RuntimeError("database unavailable"))
    )
    with pytest.raises(RuntimeError, match="database unavailable"):
        await read(app)


@pytest.mark.asyncio
async def test_bridge_discovery_is_read_only_and_preserves_failure(monkeypatch):

    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from mcp_bridge import server

    client = SimpleNamespace(
        call=AsyncMock(return_value={"workspaces": []}), scope=AsyncMock()
    )
    bridge = server(client)
    tool = next(
        tool
        for tool in await bridge.list_tools()
        if tool.name == "wright_workspace_list"
    )
    assert tool.annotations.readOnlyHint
    assert tool.outputSchema["type"] == "object"
    assert tool.meta["ui"]["visibility"] == ["model", "app"]
    _, result = await bridge.call_tool("wright_workspace_list", {})
    assert result == {"workspaces": []}
    client.call.assert_awaited_once_with("GET", "/api/desktop/workspaces")
    client.scope.assert_not_awaited()
    client.call.side_effect = RuntimeError("connection unavailable")
    with pytest.raises(Exception, match="connection unavailable"):
        await bridge.call_tool("wright_workspace_list", {})


@pytest.mark.asyncio
async def test_file_tree_reuses_owner_and_denies_wrong_session_before_read(discovery):
    app, _, _, create, _ = discovery
    directory = create("Alpha")
    files = app.state.desktop_service.files
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        denied = await client.get(
            "/api/desktop/workspaces/Alpha/files", params={"session_id": "wrong"}
        )
        assert denied.status_code == 403
        files.tree.assert_not_awaited()
        response = await client.get(
            "/api/desktop/workspaces/Alpha/files",
            params={"session_id": "desktop-Alpha"},
        )
        assert response.status_code == 200
        assert response.json()["session_id"] == "desktop-Alpha"
        files.tree.assert_awaited_once_with(str(directory))


@pytest.mark.asyncio
async def test_connection_plan_reuses_owner_with_exact_scope_and_no_apply(discovery):
    from api.services.mcp_services import get_mcp_api_service

    app, _, _, create, _ = discovery
    create("Alpha")
    owner = Mock()
    owner.create_install_plan.return_value = {"plan_id": "reviewable"}
    app.dependency_overrides[get_mcp_api_service] = lambda: owner
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        body = {"workspace_id": "Alpha", "session_id": "wrong", "capability_id": "cad"}
        assert (
            await client.post("/api/desktop/connection-plans", json=body)
        ).status_code == 403
        owner.create_install_plan.assert_not_called()
        body["session_id"] = "desktop-Alpha"
        response = await client.post("/api/desktop/connection-plans", json=body)
        assert response.status_code == 200
        assert response.json()["workspace_id"] == "Alpha"
        kwargs = owner.create_install_plan.call_args.kwargs
        assert kwargs["requested_scope"] == "workspace"
        assert kwargs["workspace_id"] == "Alpha"
        assert kwargs["independently_completed_license"] is False
        owner.approve_install_plan.assert_not_called()
        owner.apply_install_plan.assert_not_called()
        body["independently_completed_license"] = True
        assert (
            await client.post("/api/desktop/connection-plans", json=body)
        ).status_code == 200
        assert (
            owner.create_install_plan.call_args.kwargs[
                "independently_completed_license"
            ]
            is True
        )
        body["requested_scope"] = "global_registered"
        assert (
            await client.post("/api/desktop/connection-plans", json=body)
        ).status_code == 422


@pytest.mark.asyncio
async def test_setup_actions_require_admin_exact_scope_and_owner_digest(discovery):
    from api.services.mcp_services import get_mcp_api_service
    from tool_registry.install_plans import InstallPlanError

    app, _, _, create, _ = discovery
    create("Alpha")
    app.state.security_settings = SimpleNamespace(enforced=True)

    @app.middleware("http")
    async def test_principal(request, call_next):
        request.state.principal_role = request.headers.get("test-role", "viewer")
        return await call_next(request)

    owner = Mock()
    owner.get_install_plan.return_value = SimpleNamespace(
        workspace_id="Alpha", requested_scope="workspace"
    )
    app.dependency_overrides[get_mcp_api_service] = lambda: owner
    body = {
        "workspace_id": "Alpha",
        "session_id": "desktop-Alpha",
        "plan_digest": "a" * 64,
    }
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        for operation in ("approve", "apply"):
            path = "/api/desktop/connection-plans/plan/" + operation
            assert (await client.post(path, json=body)).status_code == 403
            owner.get_install_plan.assert_not_called()
            owner.get_install_plan.return_value.workspace_id = "Other"
            assert (
                await client.post(path, json=body, headers={"test-role": "admin"})
            ).status_code == 403
            owner.approve_install_plan.assert_not_called()
            owner.apply_install_plan.assert_not_called()
            owner.get_install_plan.reset_mock()
        owner.get_install_plan.return_value.workspace_id = "Alpha"
        owner.approve_install_plan.side_effect = InstallPlanError(
            "plan_digest_mismatch", "Stale plan"
        )
        response = await client.post(
            "/api/desktop/connection-plans/plan/approve",
            json=body,
            headers={"test-role": "admin"},
        )
        assert response.status_code >= 400
        owner.approve_install_plan.assert_called_once()
        assert owner.approve_install_plan.call_args.args == ("plan", "a" * 64)
        owner.apply_install_plan.assert_not_called()
        read = await client.get(
            "/api/desktop/connection-plans/plan",
            params={"workspace_id": "Alpha", "session_id": "desktop-Alpha"},
        )
        assert read.status_code == 200
        assert read.json()["plan"]["workspace_id"] == "Alpha"
        owner.apply_install_plan.assert_not_called()


@pytest.mark.asyncio
async def test_operator_signin_is_scoped_and_cleared_without_workspace_grant(discovery):
    import asyncio
    from api.services.mcp_services import get_mcp_api_service

    app, _, _, create, _ = discovery
    create("Alpha")
    backend = app.state.desktop_backend
    app.state.security_settings = SimpleNamespace(enforced=True)

    @app.middleware("http")
    async def test_principal(request, call_next):
        request.state.principal_role = request.headers.get("test-role", "viewer")
        return await call_next(request)

    owner = Mock()
    owner.get_install_plan.return_value = SimpleNamespace(
        workspace_id="Alpha",
        requested_scope="workspace",
        capability_id="cad",
        state="completed",
        plan_digest="a" * 64,
    )
    ready, finish = asyncio.Event(), asyncio.Event()

    async def validate(server_id, **kwargs):
        assert server_id == "cad"
        await backend.oauth.present(
            "cad",
            "https://issuer.example/auth?state=synthetic",
            "http://127.0.0.1:9505/oauth/callback",
        )
        ready.set()
        await finish.wait()
        return {"state": "passed", "boundary": "synthetic validator"}

    owner.run_capability_validation = AsyncMock(side_effect=validate)
    app.dependency_overrides[get_mcp_api_service] = lambda: owner
    scope = {"workspace_id": "Alpha", "session_id": "desktop-Alpha"}
    path = "/api/desktop/connection-plans/p"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        assert (await client.get(path + "/signin", params=scope)).status_code == 403
        task = asyncio.create_task(
            client.post(
                path + "/validate",
                json={**scope, "plan_digest": "a" * 64},
                headers={"test-role": "admin"},
            )
        )
        try:
            await asyncio.wait_for(ready.wait(), 5)
            response = await client.get(
                path + "/signin", params=scope, headers={"test-role": "admin"}
            )
            assert response.headers["cache-control"] == "no-store"
            assert response.json()["presentation"] == "awaiting_user"
            assert (
                await client.get(
                    "/api/desktop/connection-plans/other/signin",
                    params=scope,
                    headers={"test-role": "admin"},
                )
            ).status_code == 403
            duplicate = await client.post(
                path + "/validate",
                json={**scope, "plan_digest": "a" * 64},
                headers={"test-role": "admin"},
            )
            assert duplicate.status_code == 409
            owner.run_capability_validation.assert_awaited_once()
        finally:
            finish.set()
            result = await asyncio.wait_for(task, 5)
        assert result.status_code == 200
        assert (
            await client.get(
                path + "/signin", params=scope, headers={"test-role": "admin"}
            )
        ).json()["authorization_url"] is None
        owner.enable_capability_for_workspace.assert_not_called()


@pytest.mark.asyncio
async def test_workspace_enablement_retains_operator_scope_and_existing_owner(
    discovery,
):
    from api.services.mcp_services import get_mcp_api_service
    from tool_registry.validation_evidence import ValidationEvidenceError

    app, _, _, create, _ = discovery
    create("Alpha")
    app.state.security_settings = SimpleNamespace(enforced=True)

    @app.middleware("http")
    async def principal(request, call_next):
        request.state.principal_role = request.headers.get("test-role", "viewer")
        return await call_next(request)

    owner = Mock()
    plan = SimpleNamespace(
        workspace_id="Alpha",
        requested_scope="workspace",
        capability_id="cad",
        state="completed",
        plan_digest="a" * 64,
    )
    owner.get_install_plan.return_value = plan
    app.dependency_overrides[get_mcp_api_service] = lambda: owner
    path = "/api/desktop/connection-plans/p/enable"
    body = {
        "workspace_id": "Alpha",
        "session_id": "desktop-Alpha",
        "plan_digest": "a" * 64,
    }
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        assert (await client.post(path, json=body)).status_code == 403
        headers = {"test-role": "admin"}
        assert (
            await client.post(
                path, json={**body, "plan_digest": "b" * 64}, headers=headers
            )
        ).status_code == 409
        plan.workspace_id = "Other"
        assert (await client.post(path, json=body, headers=headers)).status_code == 403
        owner.enable_capability_for_workspace.assert_not_called()
        plan.workspace_id = "Alpha"
        owner.enable_capability_for_workspace.side_effect = ValidationEvidenceError(
            "validation_required", "Current validation required"
        )
        denied = await client.post(path, json=body, headers=headers)
        assert denied.status_code == 409
        assert denied.json()["detail"]["code"] == "validation_required"
        owner.enable_capability_for_workspace.side_effect = None
        owner.enable_capability_for_workspace.return_value = {
            "enabled": True,
            "invocation_approved": False,
        }
        response = await client.post(path, json=body, headers=headers)
        assert response.status_code == 200
        assert response.json()["enablement"]["invocation_approved"] is False
        owner.enable_capability_for_workspace.assert_called_with("cad", "Alpha")
        owner.run_capability_validation.assert_not_called()
        owner.apply_install_plan.assert_not_called()


@pytest.mark.asyncio
async def test_saved_setup_list_uses_exact_workspace_and_excludes_other_scopes(
    discovery,
):
    from api.services.mcp_services import get_mcp_api_service

    app, _, _, create, _ = discovery
    create("Alpha")
    owner = Mock()

    def plan(workspace, capability, scope):
        data = dict(
            plan_id="saved",
            capability_id=capability,
            workspace_id=workspace,
            state="completed",
            created_at="2026-10-14",
        )
        return SimpleNamespace(
            **data, requested_scope=scope, model_dump=lambda **_: data
        )

    owner.list_workspace_install_plans.return_value = [
        plan("Alpha", "cad", "workspace"),
        plan("Other", "cad", "workspace"),
        plan("Alpha", "other", "workspace"),
        plan("Alpha", "cad", "global_registered"),
    ]
    app.dependency_overrides[get_mcp_api_service] = lambda: owner
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/desktop/connection-plans",
            params={
                "workspace_id": "Alpha",
                "session_id": "desktop-Alpha",
                "capability_id": "cad",
            },
        )
    assert response.status_code == 200
    assert len(response.json()["plans"]) == 1
    assert response.json()["plans"][0]["workspace_id"] == "Alpha"
    owner.list_workspace_install_plans.assert_called_once_with("Alpha", "cad")
    owner.create_install_plan.assert_not_called()
    owner.apply_install_plan.assert_not_called()
