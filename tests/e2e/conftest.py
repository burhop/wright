import json
import sqlite3
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from tool_registry import McpServer, McpTool
from tool_registry.db import insert_server, insert_tools


@pytest.fixture
def offline_api_client(tmp_path, monkeypatch):
    db_path = str(tmp_path / "wright-smoke.db")
    monkeypatch.setenv("WRIGHT_TESTING", "1")
    monkeypatch.setenv("DATABASE_PATH", db_path)
    monkeypatch.setenv("WRIGHT_SECRETS_PATH", str(tmp_path / "secrets.json"))
    monkeypatch.setenv("WRIGHT_LEGACY_GATEWAY", "1")

    from api import main
    from api.database import migrate

    monkeypatch.setattr(main, "DATABASE_PATH", db_path)
    monkeypatch.setattr(migrate, "DATABASE_PATH", db_path)

    with TestClient(main.app) as client:
        client.app.state.agent_sync_manager = SimpleNamespace(
            active_agent="hermes",
            sync_workspace_tools=lambda session_id: None,
        )
        yield client


@pytest.fixture
def gateway_smoke_seed(offline_api_client, tmp_path):
    db_path = offline_api_client.app.state.mcp_engine.db_path
    workspace_path = tmp_path / "gateway-workspace"
    workspace_path.mkdir()

    server = McpServer(
        server_id="smoke-gateway-server",
        name="Smoke Gateway",
        type="stdio",
        command=["python", "-m", "smoke_gateway"],
        is_active=True,
        is_installed=True,
        status="active",
        created_at=1000,
        updated_at=1000,
    )
    insert_server(db_path, server)
    insert_tools(
        db_path,
        [
            McpTool(
                tool_id="smoke-gateway-server:ping",
                server_id="smoke-gateway-server",
                name="ping",
                description="Ping smoke tool",
                input_schema={"type": "object"},
                is_enabled=True,
                created_at=1000,
            )
        ],
    )

    from data_vault.secret_provider import FileSecretProvider
    from data_vault.workspace_repository import WorkspaceRepository

    WorkspaceRepository(
        db_path, secrets=FileSecretProvider(tmp_path / "gateway-secrets.json")
    ).create(
        "smoke-workspace",
        "smoke-session",
        str(workspace_path),
        workspace_name="Smoke Workspace",
    )
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE engineering_workspaces SET enabled_tools = ? WHERE workspace_id = ?",
            (json.dumps([server.server_id]), "smoke-workspace"),
        )

    return {
        "db_path": db_path,
        "server_id": server.server_id,
        "tool_name": "smoke-gateway-server__ping",
        "headers": {
            "X-Wright-Session-Id": "smoke-session",
            "X-Wright-Workspace-Id": "smoke-workspace",
        },
    }
