"""Native draft ports preserve storage ownership, scope, and admin authorization."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI, HTTPException
from data_vault import WorkspaceRepository, upgrade_database
from workspace_service.workflow_sources import (
    WorkspaceWorkflowSourceStore,
    WorkspaceWorkflowSourceUseCases,
)
from workspace_service.executor import BoundedExecutor


@pytest_asyncio.fixture
async def draft_api(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from desktop_backend import DesktopBackend

    root = tmp_path / "workspaces" / "alpha"
    root.mkdir(parents=True)
    store = WorkspaceWorkflowSourceStore(str(root))
    accepted = store.create("workflows/example.workflow.wflow", "accepted")
    database = str(tmp_path / "state.db")
    upgrade_database(database)
    repository = WorkspaceRepository(database, secrets=Mock())
    repository.create("alpha", "desktop-alpha", str(root), workspace_name="Alpha")
    repository.associate_session(
        "alpha", "desktop-alpha", agent_id="openai-desktop-harness"
    )
    executor = BoundedExecutor()
    owner = SimpleNamespace(
        db_path=database,
        repository=repository,
        workflow_sources=WorkspaceWorkflowSourceUseCases(executor),
    )
    backend = DesktopBackend(owner, tmp_path, 5209)
    app = FastAPI()
    from api.security import require_admin

    async def permitted_test_admin():
        return None

    app.dependency_overrides[require_admin] = permitted_test_admin
    app.include_router(backend.router())
    body = {
        "workspace_id": "alpha",
        "session_id": "desktop-alpha",
        "path": accepted.path,
        "draft_id": "editor-one",
        "request_id": "save-one",
        "expected_draft_digest": None,
        "snapshot": {
            "base_storage_revision": 1,
            "base_storage_digest": accepted.storage_digest,
            "source": "invalid raw",
            "applied_source": "valid diagram",
            "layout": None,
            "view": "code",
        },
    }
    yield app, body, store, accepted
    await executor.close()


@pytest.mark.asyncio
async def test_real_owner_scope_closed_request_and_admin_denial(draft_api):
    from api.security import require_admin

    app, body, store, accepted = draft_api
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        saved = await client.post("/api/desktop/editor-drafts/save", json=body)
        assert saved.status_code == 200, saved.text
        assert saved.json()["draft"]["source"] == "invalid raw"
        read = {
            key: body[key] for key in ("workspace_id", "session_id", "path", "draft_id")
        }
        observed = await client.post("/api/desktop/editor-drafts/read", json=read)
        assert observed.status_code == 200 and observed.json() == saved.json()
        for patch, status in [
            ({"session_id": "foreign"}, 403),
            ({"workspace_id": "foreign"}, 403),
            ({"run": True}, 422),
            ({"expected_draft_digest": "invalid"}, 422),
            ({"snapshot": {**body["snapshot"], "approval": True}}, 422),
        ]:
            response = await client.post(
                "/api/desktop/editor-drafts/save", json={**body, **patch}
            )
            assert response.status_code == status, response.text

        async def deny():
            raise HTTPException(403, "admin required")

        app.dependency_overrides[require_admin] = deny
        assert (
            await client.post(
                "/api/desktop/editor-drafts/save",
                json={**body, "request_id": "save-two"},
            )
        ).status_code == 403
        assert (
            await client.post("/api/desktop/editor-drafts/read", json=read)
        ).status_code == 200
        assert store.read(accepted.path) == accepted
        assert (
            store.editor_drafts_read(accepted.path, "editor-one")["draft"][
                "draft_revision"
            ]
            == 1
        )


@pytest.mark.asyncio
async def test_mcp_ports_are_app_only_closed_and_never_retry(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from mcp_bridge import server
    from native_source_tools import WrightRequestRejected

    client = SimpleNamespace(
        scope=AsyncMock(), call=AsyncMock(return_value={"drafts": []})
    )
    bridge = server(client)
    tools = {tool.name: tool for tool in await bridge.list_tools()}
    assert tools["wright_editor_drafts_read"].annotations.readOnlyHint
    assert not tools["wright_editor_draft_save"].annotations.readOnlyHint
    assert tools["wright_editor_draft_save"].annotations.destructiveHint
    for name in ("wright_editor_drafts_read", "wright_editor_draft_save"):
        assert tools[name].meta["ui"]["visibility"] == ["app"]
    read = {
        "workspace_id": "alpha",
        "session_id": "desktop-alpha",
        "path": "workflows/example.workflow.wflow",
        "draft_id": None,
    }
    await bridge.call_tool("wright_editor_drafts_read", {"request": read})
    client.call.assert_awaited_once_with(
        "POST", "/api/desktop/editor-drafts/read", json=read
    )
    client.call.reset_mock()
    with pytest.raises(Exception):
        await bridge.call_tool(
            "wright_editor_drafts_read", {"request": {**read, "approve": True}}
        )
    client.call.assert_not_awaited()
    request = {
        **read,
        "draft_id": "editor-one",
        "request_id": "save-one",
        "expected_draft_digest": None,
        "snapshot": {
            "source": "",
            "applied_source": "diagram",
            "layout": None,
            "view": "code",
            "base_storage_revision": 1,
            "base_storage_digest": "a" * 64,
        },
    }
    for status, known in [(409, True), (503, False)]:
        client.call.side_effect = WrightRequestRejected(status, "PRIVATE")
        value = (
            await bridge.call_tool("wright_editor_draft_save", {"request": request})
        )[1]
        assert value["error"]["outcome_known"] is known and "PRIVATE" not in str(value)
        client.call.assert_awaited_once()
        client.call.reset_mock()
    client.scope.side_effect = WrightRequestRejected(403, "PRIVATE scope diagnostic")
    value = (await bridge.call_tool("wright_editor_draft_save", {"request": request}))[1]
    assert value["error"]["outcome_known"] is True and "PRIVATE" not in str(value)
    client.call.assert_not_awaited()
