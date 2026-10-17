from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI, HTTPException
from data_vault import WorkspaceRepository, upgrade_database
from workspace_service.executor import BoundedExecutor
from workspace_service.use_cases.context import WorkspaceContextUseCases


@pytest_asyncio.fixture
async def settings_api(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from desktop_backend import DesktopBackend
    from api.security import require_admin

    database = str(tmp_path / "state.db")
    upgrade_database(database)
    secrets = Mock()
    secrets.get.side_effect = AssertionError("No credential reads")
    secrets.set.side_effect = AssertionError("No credential writes")
    repository = WorkspaceRepository(database, secrets=secrets)
    root = tmp_path / "workspaces" / "alpha"
    root.mkdir(parents=True)
    repository.create("alpha", "desktop-alpha", str(root), workspace_name="Alpha")
    repository.associate_session(
        "alpha", "desktop-alpha", agent_id="openai-desktop-harness"
    )
    repository.update_remote(
        "alpha",
        "https://user:PRIVATE@host/repo",
        "public-user",
        None,
        "old context",
        10485760,
    )
    executor = BoundedExecutor()
    owner = SimpleNamespace(
        db_path=database,
        repository=repository,
        executor=executor,
        context=WorkspaceContextUseCases(repository),
    )
    app = FastAPI()

    async def operator():
        return None

    app.dependency_overrides[require_admin] = operator
    app.include_router(DesktopBackend(owner, tmp_path, 5210).router())
    yield app, repository, secrets, owner, root
    await executor.close()


@pytest.mark.asyncio
async def test_scoped_partial_save_redacts_legacy_remote_and_preserves_other_owners(
    settings_api,
):
    app, repository, secrets, _, _ = settings_api
    from api.security import require_admin

    scope = {"workspace_id": "alpha", "session_id": "desktop-alpha"}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        observed = await client.post("/api/desktop/workspace-settings/read", json=scope)
        assert observed.status_code == 200 and "PRIVATE" not in observed.text
        state = observed.json()["settings"]
        assert state["remote_hidden"] and state["git_remote_url"] is None
        body = {
            **scope,
            "expected_revision": state["revision"],
            "changes": {"workspace_prompt": "new context"},
        }
        saved = await client.post("/api/desktop/workspace-settings/save", json=body)
        assert saved.status_code == 200 and "PRIVATE" not in saved.text
        assert saved.json()["settings"]["workspace_prompt"] == "new context"
        raw = repository.get_by_id("alpha")
        assert raw["git_remote_url"] == "https://user:PRIVATE@host/repo"
        assert (
            raw["git_username"] == "public-user"
            and raw["git_large_file_threshold"] == 10485760
        )
        assert (
            await client.post("/api/desktop/workspace-settings/save", json=body)
        ).status_code == 409
        body["expected_revision"] = saved.json()["settings"]["revision"]
        for patch, status in [
            ({"session_id": "foreign"}, 403),
            ({"workspace_id": "foreign"}, 403),
            ({"changes": {"git_token": "new"}}, 422),
            ({"changes": {"agent_id": "hermes"}}, 422),
            ({"changes": {"git_large_file_threshold": True}}, 422),
            ({"changes": {}}, 422),
            ({"changes": {"git_remote_url": "https://user:password@host/repo"}}, 422),
        ]:
            value = await client.post(
                "/api/desktop/workspace-settings/save", json={**body, **patch}
            )
            assert value.status_code == status, value.text

        async def deny():
            raise HTTPException(403, "operator required")

        app.dependency_overrides[require_admin] = deny
        assert (
            await client.post("/api/desktop/workspace-settings/save", json=body)
        ).status_code == 403
        assert repository.get_by_id("alpha") == raw
        secrets.get.assert_not_called()
        secrets.set.assert_not_called()
        assert (
            repository.list_sessions("alpha")[0]["agent_id"] == "openai-desktop-harness"
        )


@pytest.mark.asyncio
async def test_workspace_context_is_embedded_only_into_new_sources(settings_api):
    from workspace_service.workflow_instruction_settings import (
        WorkflowInstructionSettings,
    )
    from workspace_service.workflow_sources import WorkspaceWorkflowSourceUseCases
    from workspace_service.service import WorkspaceService

    app, repository, _, owner, root = settings_api
    owner.workflow_instruction_settings = WorkflowInstructionSettings(owner.db_path)
    sources = WorkspaceWorkflowSourceUseCases(
        owner.executor,
        instruction_defaults=lambda path: (
            WorkspaceService.workflow_instruction_defaults(owner, path)
        ),
    )
    source = 'workflow context_proof\n  name: "Context proof"\n  purpose: "Preserve explicit instructions"\n  discipline: "mechanical.design"\n  reviewed_ai_suggestions: true\nend\n'
    accepted = await sources.create(
        str(root), "workflows/before.workflow.wflow", source
    )
    assert "old context" in accepted.source
    scope = {"workspace_id": "alpha", "session_id": "desktop-alpha"}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        before = (
            await client.post("/api/desktop/workspace-settings/read", json=scope)
        ).json()["settings"]
        result = await client.post(
            "/api/desktop/workspace-settings/save",
            json={
                **scope,
                "expected_revision": before["revision"],
                "changes": {"workspace_prompt": "new context"},
            },
        )
        assert result.status_code == 200
    newer = await sources.create(str(root), "workflows/after.workflow.wflow", source)
    assert "new context" in newer.source and "old context" not in newer.source
    assert await sources.read(str(root), accepted.path) == accepted
    assert not (root / "runs").exists()


@pytest.mark.asyncio
async def test_settings_tools_are_closed_app_only_and_scope_denials_are_known(
    monkeypatch,
):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from mcp_bridge import server
    from native_source_tools import WrightRequestRejected

    client = SimpleNamespace(
        scope=AsyncMock(), call=AsyncMock(return_value={"settings": {}})
    )
    bridge = server(client)
    tools = {tool.name: tool for tool in await bridge.list_tools()}
    assert tools["wright_workspace_settings_read"].annotations.readOnlyHint
    assert tools["wright_workspace_settings_save"].annotations.destructiveHint
    for name in ("wright_workspace_settings_read", "wright_workspace_settings_save"):
        assert tools[name].meta["ui"]["visibility"] == ["app"]
    body = {
        "workspace_id": "alpha",
        "session_id": "desktop-alpha",
        "expected_revision": "a" * 64,
        "changes": {"workspace_prompt": "new"},
    }
    await bridge.call_tool("wright_workspace_settings_save", {"request": body})
    client.call.assert_awaited_once_with(
        "POST", "/api/desktop/workspace-settings/save", json=body
    )
    client.call.reset_mock()
    with pytest.raises(Exception):
        await bridge.call_tool(
            "wright_workspace_settings_save",
            {"request": {**body, "changes": {"git_token": "no"}}},
        )
    client.call.assert_not_awaited()
    client.scope.side_effect = WrightRequestRejected(403, "PRIVATE")
    denied = (
        await bridge.call_tool("wright_workspace_settings_save", {"request": body})
    )[1]
    assert denied["error"]["outcome_known"] is True and "PRIVATE" not in str(denied)
    client.call.assert_not_awaited()
