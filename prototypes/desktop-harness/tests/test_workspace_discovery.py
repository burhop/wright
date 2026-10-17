from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from fastapi import FastAPI
import httpx
import pytest

from data_vault import WorkspaceRepository, upgrade_database
from workspace_service.use_cases.lifecycle import WorkspaceLifecycleUseCases


@pytest.mark.asyncio
async def test_upload_requires_operator_exact_scope_and_closed_body(discovery):
    import base64
    import hashlib
    from api.security import SecuritySettings, require_admin

    app, _, _, create, _ = discovery
    root = create("Upload")
    app.state.security_settings = SecuritySettings(
        "enforced", "synthetic-operator-token", (), "127.0.0.1"
    )
    content = b"native STEP\x00\xff"
    digest = hashlib.sha256(content).hexdigest()
    owner = app.state.desktop_service.files
    owner.stage_upload = AsyncMock(return_value=f"uploads/{digest}/input.step")
    body = {
        "workspace_id": "Upload",
        "session_id": "desktop-Upload",
        "filename": "input.step",
        "sha256": digest,
        "content_base64": base64.b64encode(content).decode(),
    }
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        response = await client.post("/api/desktop/files/upload", json=body)
        assert response.status_code == 403
        owner.stage_upload.assert_not_awaited()
        app.dependency_overrides[require_admin] = lambda: None
        response = await client.post(
            "/api/desktop/files/upload", json={**body, "session_id": "other"}
        )
        assert response.status_code == 403
        owner.stage_upload.assert_not_awaited()
        response = await client.post(
            "/api/desktop/files/upload", json={**body, "path": "outputs/overwrite.step"}
        )
        assert response.status_code == 422
        owner.stage_upload.assert_not_awaited()
        response = await client.post(
            "/api/desktop/files/upload", json={**body, "content_base64": "!!!!"}
        )
        assert response.status_code == 422
        owner.stage_upload.assert_not_awaited()
        response = await client.post("/api/desktop/files/upload", json=body)
        assert response.status_code == 200
        assert response.json() == {
            "workspace_id": "Upload",
            "session_id": "desktop-Upload",
            "filename": "input.step",
            "path": f"uploads/{digest}/input.step",
            "sha256": digest,
            "bytes": len(content),
        }
        owner.stage_upload.assert_awaited_once_with(
            str(root), "input.step", content, digest
        )
        for error, status in [
            (FileExistsError("PRIVATE"), 409),
            (OSError("PRIVATE"), 503),
        ]:
            owner.stage_upload.side_effect = error
            response = await client.post("/api/desktop/files/upload", json=body)
            assert response.status_code == status and "PRIVATE" not in response.text


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
    owner.get_capability.return_value = SimpleNamespace(
        local_validation=None,
        user_state=SimpleNamespace(installed=True, active=False, enabled_workspaces=[]),
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


@pytest.mark.asyncio
async def test_preview_reuses_bounded_owner_and_checks_scope_first(discovery):
    app, _, _, create, _ = discovery
    directory = create("Preview")
    files = app.state.desktop_service.files
    files.read = AsyncMock(
        return_value=SimpleNamespace(
            binary=False, content=b"<script>not executed</script>"
        )
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        denied = await client.get(
            "/api/desktop/workspaces/Preview/file-preview",
            params={"session_id": "other", "path": "notes.md"},
        )
        assert denied.status_code == 403
        files.read.assert_not_awaited()
        response = await client.get(
            "/api/desktop/workspaces/Preview/file-preview",
            params={"session_id": "desktop-Preview", "path": "notes.md"},
        )
        assert response.json()["content"] == "<script>not executed</script>"
        files.read.assert_awaited_once_with(str(directory), "notes.md", max_bytes=65536)
        files.read.side_effect = ValueError("File exceeds the preview byte limit")
        unsupported = await client.get(
            "/api/desktop/workspaces/Preview/file-preview",
            params={"session_id": "desktop-Preview", "path": "large.txt"},
        )
        assert unsupported.json()["supported"] is False
        assert "content" not in unsupported.json()


def test_bounded_file_owner_preserves_limits_and_confinement(tmp_path):
    from workspace_service.adapters.filesystem import LocalWorkspaceFiles

    root = tmp_path / "workspace"
    root.mkdir()
    files = LocalWorkspaceFiles(str(root))
    (root / "note.txt").write_bytes(b"hello")
    assert files.read("note.txt", max_bytes=5)[1] == b"hello"
    with pytest.raises(ValueError, match="preview byte limit"):
        files.read("note.txt", max_bytes=4)
    outside = tmp_path / "outside.txt"
    outside.write_text("private")
    (root / "linked.txt").symlink_to(outside)
    for path in ("../outside.txt", str(outside), "linked.txt"):
        with pytest.raises(ValueError):
            files.read(path, max_bytes=64)
    assert outside.read_text() == "private"


@pytest.mark.asyncio
async def test_preview_bridge_is_ui_only_and_read_only(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from mcp_bridge import server

    client = SimpleNamespace(
        call=AsyncMock(return_value={"supported": False}), scope=AsyncMock()
    )
    bridge = server(client)
    tool = next(
        tool
        for tool in await bridge.list_tools()
        if tool.name == "wright_workspace_file_preview"
    )
    assert tool.annotations.readOnlyHint
    assert tool.meta["ui"]["visibility"] == ["app"]
    await bridge.call_tool(
        tool.name, {"workspace_id": "a", "session_id": "chat-a", "path": "notes.md"}
    )
    client.scope.assert_awaited_once_with("a", "chat-a")
    client.call.assert_awaited_once_with(
        "GET",
        "/api/desktop/workspaces/a/file-preview",
        params={"session_id": "chat-a", "path": "notes.md"},
    )


@pytest.mark.asyncio
async def test_saved_plan_discovery_requires_session_scope_and_filters_owner_output(
    discovery,
):
    from api.services.mcp_services import get_mcp_api_service

    app, _, _, create, _ = discovery
    create("Alpha")
    create("Beta")

    def plan(workspace, scope, capability):
        fields = dict(
            plan_id=f"plan-{workspace}-{scope}",
            workspace_id=workspace,
            requested_scope=scope,
            capability_id=capability,
            state="blocked",
            created_at="2026-10-15T00:00:00Z",
        )
        return SimpleNamespace(**fields, model_dump=lambda **kwargs: fields)

    owner = SimpleNamespace(
        list_workspace_install_plans=Mock(
            return_value=[
                plan("Alpha", "workspace", "import:custom"),
                plan("Beta", "workspace", "import:private"),
                plan("Alpha", "global_registered", "import:global"),
            ]
        )
    )
    app.dependency_overrides[get_mcp_api_service] = lambda: owner
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/desktop/connection-plans",
            params={"workspace_id": "Alpha", "session_id": "desktop-Alpha"},
        )
        assert response.status_code == 200
        assert [item["capability_id"] for item in response.json()["plans"]] == [
            "import:custom"
        ]
        owner.list_workspace_install_plans.assert_called_once_with("Alpha", None)
        owner.list_workspace_install_plans.reset_mock()
        denied = await client.get(
            "/api/desktop/connection-plans",
            params={"workspace_id": "Alpha", "session_id": "desktop-Beta"},
        )
        assert denied.status_code in (403, 404)
        owner.list_workspace_install_plans.assert_not_called()


@pytest.mark.asyncio
async def test_custom_preview_plan_is_workspace_bound_and_explicitly_expires(discovery):
    from api.services.mcp_services import get_mcp_api_service

    app, _, _, create, _ = discovery
    create("Alpha")
    create("Beta")
    owner = Mock()
    owner.preview_import.return_value = {"preview_id": "preview", "drafts": []}
    owner.create_install_plan.return_value = {"plan_id": "saved"}
    app.dependency_overrides[get_mcp_api_service] = lambda: owner
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/desktop/connection-imports/preview",
            json={
                "workspace_id": "Alpha",
                "session_id": "desktop-Alpha",
                "name": "Custom CAD",
                "url": "https://example.invalid/mcp",
            },
        )
        assert response.status_code == 200
        owner.create_install_plan.assert_not_called()
        body = {
            "workspace_id": "Beta",
            "session_id": "desktop-Beta",
            "preview_token": response.json()["preview_token"],
            "draft_id": "draft",
            "draft_digest": "a" * 64,
        }
        assert (
            await client.post("/api/desktop/connection-imports/plan", json=body)
        ).status_code == 409
        owner.create_install_plan.assert_not_called()
        body.update(workspace_id="Alpha", session_id="desktop-Alpha")
        assert (
            await client.post("/api/desktop/connection-imports/plan", json=body)
        ).status_code == 200
        values = owner.create_install_plan.call_args.kwargs
        assert values["requested_scope"] == "workspace"
        assert values["workspace_id"] == "Alpha"
        assert values["independently_completed_license"] is False
        assert values["import_preview_id"] == "preview"
        assert values["draft_digest"] == "a" * 64
        owner.apply_install_plan.assert_not_called()
        owner.approve_install_plan.assert_not_called()
        owner.create_install_plan.reset_mock()
        backend = app.state.desktop_backend
        previous_clock = backend._now
        backend._now = lambda: previous_clock() + 901
        assert (
            await client.post("/api/desktop/connection-imports/plan", json=body)
        ).status_code == 409
        backend.import_scopes.clear()  # Restart loses transient preview, never durable plans.
        assert (
            await client.post("/api/desktop/connection-imports/plan", json=body)
        ).status_code == 409
        owner.create_install_plan.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "http://example.invalid/mcp",
        "https://user:password@example.invalid/mcp",
        "https://example.invalid/mcp?token=secret",
        "https://example.invalid/mcp#secret",
    ],
)
async def test_custom_preview_rejects_credential_or_unsupported_endpoint_before_owner(
    discovery, url
):
    from api.services.mcp_services import get_mcp_api_service

    app, _, _, create, _ = discovery
    create("Alpha")
    owner = Mock()
    app.dependency_overrides[get_mcp_api_service] = lambda: owner
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/desktop/connection-imports/preview",
            json={
                "workspace_id": "Alpha",
                "session_id": "desktop-Alpha",
                "name": "Custom",
                "url": url,
            },
        )
        assert response.status_code == 422
        owner.preview_import.assert_not_called()


@pytest.mark.asyncio
async def test_workspace_creation_conflict_is_actionable_without_path_disclosure(
    discovery,
):
    from workspace_service.service import WorkspaceService

    app, repository, _, create, _ = discovery
    directory = create("Existing")
    service = app.state.desktop_service
    backend = app.state.desktop_backend
    backend.clients["private-test-client"] = backend._now() + 30
    before = repository.list_all()
    sessions = repository.list_sessions("Existing")

    async def create_owned(name, parent, agent, **kwargs):
        WorkspaceService._ensure_workspace_available(service, name, str(directory))
        raise AssertionError("The real owner must reject an existing directory")

    service.create_workspace = AsyncMock(side_effect=create_owned)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/desktop/workspaces", json={"name": "Existing"}
        )
    assert response.status_code == 409
    assert "Open the existing workspace" in response.json()["detail"]
    assert str(directory) not in response.text
    service.create_workspace.assert_awaited_once()
    assert repository.list_all() == before
    assert repository.list_sessions("Existing") == sessions


@pytest.mark.asyncio
async def test_download_exact_bytes_and_scope(discovery):
    import base64
    import hashlib

    app, _, _, create, _ = discovery
    directory = create("Download")
    content = b"ISO-10303-21;\x00\xff\r\nEND-ISO-10303-21;"
    (directory / "part.step").write_bytes(content)
    owner = app.state.desktop_service.files
    owner.read_bytes = AsyncMock(return_value=content)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        route = "/api/desktop/workspaces/Download/file-download"
        denied = await client.get(
            route, params={"session_id": "other", "path": "part.step"}
        )
        assert denied.status_code == 403
        owner.read_bytes.assert_not_awaited()
        result = (
            await client.get(
                route, params={"session_id": "desktop-Download", "path": "part.step"}
            )
        ).json()
        assert result["supported"]
        assert base64.b64decode(result["content_base64"], validate=True) == content
        assert result["sha256"] == hashlib.sha256(content).hexdigest()
        assert result["bytes"] == len(content)
        assert result["filename"] == "part.step"
        owner.read_bytes.assert_awaited_once_with(
            str(directory), "part.step", maximum_bytes=16 * 1024 * 1024
        )
        owner.read_bytes.side_effect = ValueError("private exception detail")
        rejected = (
            await client.get(
                route, params={"session_id": "desktop-Download", "path": "part.step"}
            )
        ).json()
        assert rejected["supported"] is False
        assert "content_base64" not in rejected
        assert "private exception detail" not in str(rejected)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        "../outside",
        "/etc/passwd",
        "C:\\secret",
        "a:stream",
        ".env",
        ".wright/state.json",
        "outputs/.secret",
        "freecad_mcp_work/file",
        "bad\nname",
        "linked.step",
        "missing.step",
    ],
)
async def test_download_rejects_nonvisible_or_unconfined_paths_before_read(
    discovery, path
):
    app, _, _, create, root = discovery
    directory = create("Download")
    outside = root / "outside"
    outside.write_bytes(b"private")
    (directory / "linked.step").symlink_to(outside)
    owner = app.state.desktop_service.files
    owner.read_bytes = AsyncMock(return_value=b"must not read")
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        result = (
            await client.get(
                "/api/desktop/workspaces/Download/file-download",
                params={"session_id": "desktop-Download", "path": path},
            )
        ).json()
    assert result["supported"] is False
    assert "content_base64" not in result
    owner.read_bytes.assert_not_awaited()


@pytest.mark.asyncio
async def test_download_bridge_is_ui_only_and_scoped(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from mcp_bridge import server

    client = SimpleNamespace(
        call=AsyncMock(return_value={"supported": False}), scope=AsyncMock()
    )
    bridge = server(client)
    tool = next(
        tool
        for tool in await bridge.list_tools()
        if tool.name == "wright_workspace_file_download"
    )
    assert tool.annotations.readOnlyHint
    assert tool.meta["ui"]["visibility"] == ["app"]
    await bridge.call_tool(
        tool.name, {"workspace_id": "a", "session_id": "chat-a", "path": "part.step"}
    )
    client.scope.assert_awaited_once_with("a", "chat-a")
    client.call.assert_awaited_once_with(
        "GET",
        "/api/desktop/workspaces/a/file-download",
        params={"session_id": "chat-a", "path": "part.step"},
    )


@pytest.mark.asyncio
async def test_disable_requires_operator_and_owned_session_before_mutation(discovery):
    from api.security import SecuritySettings, require_admin
    from api.services.mcp_services import get_mcp_api_service

    app, _, _, create, _ = discovery
    app.state.security_settings = SecuritySettings(
        "enforced", "synthetic-operator-token", (), "127.0.0.1"
    )
    create("Alpha")
    owner = SimpleNamespace(
        disable_capability_for_workspace=Mock(
            return_value={
                "workspace_id": "Alpha",
                "capability_id": "cad",
                "server_id": "registered-cad",
                "enabled": False,
            }
        )
    )
    app.dependency_overrides[get_mcp_api_service] = lambda: owner
    body = {
        "workspace_id": "Alpha",
        "session_id": "desktop-Alpha",
        "capability_id": "cad",
        "server_id": "registered-cad",
    }
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        denied = await client.post("/api/desktop/connections/disable", json=body)
        assert denied.status_code in (401, 403)
        owner.disable_capability_for_workspace.assert_not_called()
        app.dependency_overrides[require_admin] = lambda: None
        wrong = await client.post(
            "/api/desktop/connections/disable", json={**body, "session_id": "unrelated"}
        )
        assert wrong.status_code == 403
        owner.disable_capability_for_workspace.assert_not_called()
        result = await client.post("/api/desktop/connections/disable", json=body)
        assert result.status_code == 200
        assert result.json()["availability"]["enabled"] is False
        owner.disable_capability_for_workspace.assert_called_once_with(
            "cad", "Alpha", expected_server_id="registered-cad"
        )
        extra = await client.post(
            "/api/desktop/connections/disable", json={**body, "approval_mode": "auto"}
        )
        assert extra.status_code == 422
        assert owner.disable_capability_for_workspace.call_count == 1


@pytest.mark.asyncio
async def test_local_command_preview_uses_existing_normalizer_without_execution(discovery):
    import json
    from api.services.mcp_services import get_mcp_api_service
    from tool_registry.config_import import preview_configuration

    app, _, _, create, _ = discovery
    create("Alpha")
    owner = Mock()
    owner.preview_import.side_effect = preview_configuration
    app.dependency_overrides[get_mcp_api_service] = lambda: owner
    body = {
        "workspace_id": "Alpha", "session_id": "desktop-Alpha",
        "name": "Local provider", "command": "/usr/bin/python3",
        "arguments": ["-m", "existing_mcp", "a path with spaces"],
    }
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        response = await client.post("/api/desktop/connection-imports/preview", json=body)
        assert response.status_code == 200, response.text
        result = response.json()
        draft = result["preview"]["drafts"][0]
        assert draft["transport"] == "stdio" and draft["errors"] == []
        assert draft["command"] == body["command"]
        assert draft["arguments"] == body["arguments"]
        assert result["preview"]["source_discarded"] is True
        assert json.loads(owner.preview_import.call_args.args[0]) == {
            "name": body["name"], "type": "stdio",
            "command": body["command"], "args": body["arguments"],
        }
        owner.create_install_plan.assert_not_called()
        owner.apply_install_plan.assert_not_called()
        owner.approve_install_plan.assert_not_called()
        owner.preview_import.reset_mock()
        for patch, status in [
            ({"session_id": "wrong"}, 403),
            ({"env": {"TOKEN": "not-allowed"}}, 422),
            ({"url": "https://example.invalid/mcp"}, 422),
            ({"arguments": [1]}, 422),
            ({"arguments": ["a" * 4097]}, 422),
            ({"arguments": ["a"] * 513}, 422),
        ]:
            denied = await client.post(
                "/api/desktop/connection-imports/preview", json={**body, **patch}
            )
            assert denied.status_code == status, denied.text
        owner.preview_import.assert_not_called()
        unsafe = await client.post(
            "/api/desktop/connection-imports/preview",
            json={**body, "command": "python;id", "arguments": ["$(id)"]},
        )
        assert unsafe.status_code == 200
        codes = {item["code"] for item in unsafe.json()["preview"]["drafts"][0]["errors"]}
        assert codes == {"command_unsafe", "argument_shell_expression"}
        owner.apply_install_plan.assert_not_called()
