from __future__ import annotations

import uuid
import sqlite3

import pytest
from fastapi.testclient import TestClient

from api.config import DATABASE_PATH
from api.main import app
from data_vault.secret_provider import FileSecretProvider
from data_vault.workspace_repository import WorkspaceRepository
from tool_registry import McpServer, McpTool
from tool_registry.db import insert_server, insert_tools


@pytest.fixture
def legacy_client(monkeypatch):
    monkeypatch.setenv("WRIGHT_LEGACY_GATEWAY", "1")
    with TestClient(app, base_url="http://localhost") as client:
        yield client


@pytest.fixture(autouse=True)
def cleanup_gateway_test_rows():
    yield
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            "DELETE FROM gateway_audit_events WHERE workspace_id LIKE 'workspace-%'"
        )
        connection.execute("DELETE FROM mcp_tools WHERE server_id LIKE 'calc-%'")
        connection.execute("DELETE FROM mcp_servers WHERE server_id LIKE 'calc-%'")
        connection.execute(
            "DELETE FROM workspace_agent_sessions WHERE workspace_id LIKE 'workspace-%'"
        )
        connection.execute(
            "DELETE FROM engineering_workspaces WHERE workspace_id LIKE 'workspace-%'"
        )


def _seed(tmp_path):
    suffix = uuid.uuid4().hex
    server_id = f"calc-{suffix}"
    workspace_id = f"workspace-{suffix}"
    session_id = f"session-{suffix}"
    workspace = tmp_path / workspace_id
    workspace.mkdir()
    insert_server(
        DATABASE_PATH,
        McpServer(
            server_id=server_id,
            name=f"Calculation {suffix}",
            type="stdio",
            command=["uv", "run", "calc"],
            is_active=False,
            is_installed=True,
            status="inactive",
            created_at=1000,
            updated_at=1000,
        ),
    )
    insert_tools(
        DATABASE_PATH,
        [
            McpTool(
                tool_id=f"{server_id}:mesh_calc",
                server_id=server_id,
                name="mesh_calc",
                description="Calculate mesh",
                input_schema={"type": "object"},
                is_enabled=True,
                created_at=1000,
            )
        ],
    )
    WorkspaceRepository(
        DATABASE_PATH, secrets=FileSecretProvider(tmp_path / "secrets.json")
    ).create(
        workspace_id,
        session_id,
        str(workspace),
        workspace_name="Gateway",
    )
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            "UPDATE engineering_workspaces SET enabled_tools = ? WHERE workspace_id = ?",
            (f'["{server_id}"]', workspace_id),
        )
    return server_id, session_id, workspace_id, str(workspace)


def _headers(session_id, workspace_id):
    return {
        "X-Wright-Session-Id": session_id,
        "X-Wright-Workspace-Id": workspace_id,
    }


def test_legacy_gateway_is_disabled_by_default(sync_client) -> None:
    response = sync_client.get("/api/gateway/tools")
    assert response.status_code == 404


def test_legacy_gateway_requires_and_uses_explicit_binding(
    legacy_client, tmp_path
) -> None:
    server_id, session_id, workspace_id, _ = _seed(tmp_path)
    assert legacy_client.get("/api/gateway/tools").status_code == 400

    response = legacy_client.get(
        "/api/gateway/tools", headers=_headers(session_id, workspace_id)
    )
    assert response.status_code == 200
    names = [item["name"] for item in response.json()["tools"]]
    assert f"{server_id}__mesh_calc" in names

    foreign = legacy_client.get(
        "/api/gateway/tools", headers=_headers(session_id, "foreign")
    )
    assert foreign.status_code in {400, 409}


def test_legacy_call_delegates_to_gateway_service(
    legacy_client, tmp_path, monkeypatch
) -> None:
    server_id, session_id, workspace_id, workspace_path = _seed(tmp_path)
    captured = {}

    async def start(server, workspace_dir=None, *, approval_context=None):
        captured["start"] = (server, workspace_dir, approval_context)

    async def call(server, tool, arguments, *, approval_context=None):
        captured["call"] = (server, tool, arguments, approval_context)
        return {"ok": True}

    monkeypatch.setattr(app.state.mcp_engine, "start_server", start)
    monkeypatch.setattr(app.state.mcp_engine, "call_tool", call)
    response = legacy_client.post(
        "/api/gateway/call",
        headers=_headers(session_id, workspace_id),
        json={"name": f"{server_id}__mesh_calc", "arguments": {}},
    )
    assert response.status_code == 200
    assert response.json()["structuredContent"] == {"ok": True}
    assert captured["start"][1] == workspace_path
    assert captured["call"][3].workspace_id == workspace_id


def test_mcp_router_uses_generic_wright_gateway_sync():
    from api.services import mcp_services

    assert (
        mcp_services.sync_mcp_server_to_wright_gateway.__module__
        == "api.services.wright_gateway_sync"
    )
