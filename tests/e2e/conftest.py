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

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO engineering_workspaces (
                workspace_id, workspace_name, local_path, session_id, enabled_tools,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "smoke-workspace",
                "Smoke Workspace",
                str(workspace_path),
                "smoke-session",
                json.dumps(["Smoke Gateway"]),
                1000,
                1000,
            ),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO system_settings (key, value)
            VALUES ('active_gateway_session_id', 'smoke-session')
            """
        )
        conn.commit()

    return {
        "db_path": db_path,
        "server_id": server.server_id,
        "tool_name": "smokegateway__ping",
    }
