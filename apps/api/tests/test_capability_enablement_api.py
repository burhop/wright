from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from data_vault import WorkspaceRepository, upgrade_database
from data_vault.secret_provider import create_default_secret_provider
from fastapi import HTTPException
from fastapi.testclient import TestClient
from tool_registry import McpEngine, McpServer
from tool_registry.capability_services import CapabilityServiceDependencies
from tool_registry.db import insert_server, update_server

from api.main import app
from api.routers.mcp import require_engineer_or_admin
from api.services.mcp_services import McpApiService, get_mcp_api_service

NOW = datetime(2026, 8, 12, 12, 0, tzinfo=UTC)
SERVER_ID = "fixture-workspace-capability"


class ProbeClient:
    async def initialize(self):
        return {"serverInfo": {"name": "fixture", "version": "1.0.0"}}

    async def initialized(self):
        return None

    async def list_tools(self):
        return [{"name": "inspect", "inputSchema": {"type": "object"}}]

    async def call_tool(self, name, arguments):
        return {"ok": name == "inspect", "argument_count": len(arguments)}


class WorkspaceServiceFixture:
    def __init__(self, database):
        self.repository = WorkspaceRepository(
            str(database), secrets=create_default_secret_provider()
        )

    def set_workspace_tool_enabled_by_workspace(
        self, workspace_id: str, server_id: str, enabled: bool
    ):
        current = self.repository.enabled_tools(workspace_id) or []
        selected = [item for item in current if item != server_id]
        if enabled:
            selected.append(server_id)
        self.repository.set_enabled_tools(workspace_id, selected)
        return SimpleNamespace(enabled_tools=selected)


@pytest.fixture
def enablement_client(tmp_path):
    database = tmp_path / "enablement.db"
    upgrade_database(database)
    insert_server(
        str(database),
        McpServer(
            server_id=SERVER_ID,
            name="Fixture Workspace Capability",
            type="stdio",
            command=["fixture-mcp"],
            is_active=False,
            is_installed=True,
            status="inactive",
            category="cad",
            created_at=1,
            updated_at=1,
            installed_version="1.0.0",
        ),
    )
    with sqlite3.connect(database) as connection:
        connection.executemany(
            """INSERT INTO engineering_workspaces (
                workspace_id, session_id, local_path, enabled_tools,
                created_at, updated_at, workspace_name
            ) VALUES (?, ?, ?, ?, 1, 1, ?)""",
            (
                ("workspace-a", "session-a", "D:/workspace/a", "[]", "Workspace A"),
                ("workspace-b", "session-b", "D:/workspace/b", "[]", "Workspace B"),
            ),
        )
        connection.commit()
    workspace_service = WorkspaceServiceFixture(database)
    service = McpApiService(
        McpEngine(str(database)),
        SimpleNamespace(workspace_service=workspace_service),
        CapabilityServiceDependencies(
            database_path=database,
            clock=lambda: NOW,
            validation_clients={SERVER_ID: ProbeClient()},
            validation_gateway_clients={SERVER_ID: ProbeClient()},
            validation_read_only_probes={
                SERVER_ID: {
                    "name": "inspect",
                    "arguments": {},
                    "limitation": "Reads fixture status only",
                }
            },
        ),
    )
    app.dependency_overrides[get_mcp_api_service] = lambda: service
    try:
        with TestClient(app) as client:
            yield client, database
    finally:
        app.dependency_overrides.pop(get_mcp_api_service, None)
        app.dependency_overrides.pop(require_engineer_or_admin, None)


def test_validation_and_enablement_are_scoped_without_invocation_authority(
    enablement_client,
) -> None:
    client, database = enablement_client
    validation = client.post(f"/api/mcp/servers/{SERVER_ID}/validation-runs")

    assert validation.status_code == 200
    evidence = validation.json()
    assert evidence["state"] == "passed"
    assert evidence["protocol_steps"] == {
        "initialize": "passed",
        "notifications/initialized": "passed",
        "tools/list": "passed",
    }
    assert evidence["read_only_probe"]["limitation"] == "Reads fixture status only"

    enabled = client.post(
        f"/api/mcp/workspaces/workspace-a/capabilities/{SERVER_ID}/enable"
    )
    assert enabled.status_code == 200
    assert enabled.json()["enabled"] is True
    assert enabled.json()["invocation_approved"] is False
    assert "separate" in enabled.json()["message"]

    with sqlite3.connect(database) as connection:
        workspace_rows = dict(
            connection.execute(
                "SELECT workspace_id, enabled_tools FROM engineering_workspaces"
            ).fetchall()
        )
    assert json.loads(workspace_rows["workspace-a"]) == [SERVER_ID]
    assert json.loads(workspace_rows["workspace-b"]) == []


def test_missing_failed_or_stale_validation_blocks_enablement(
    enablement_client,
) -> None:
    client, database = enablement_client
    missing = client.post(
        f"/api/mcp/workspaces/workspace-a/capabilities/{SERVER_ID}/enable"
    )
    assert missing.status_code == 409
    assert missing.json()["error_code"] == "validation_required"

    assert (
        client.post(f"/api/mcp/servers/{SERVER_ID}/validation-runs").status_code == 200
    )
    update_server(str(database), SERVER_ID, {"installed_version": "2.0.0"})
    stale = client.post(
        f"/api/mcp/workspaces/workspace-a/capabilities/{SERVER_ID}/enable"
    )
    assert stale.status_code == 409
    assert stale.json()["error_code"] == "validation_stale"


def test_validation_and_workspace_enablement_enforce_role(enablement_client) -> None:
    client, _ = enablement_client

    def deny_role():
        raise HTTPException(status_code=403, detail="Engineer role required")

    app.dependency_overrides[require_engineer_or_admin] = deny_role
    assert (
        client.post(f"/api/mcp/servers/{SERVER_ID}/validation-runs").status_code == 403
    )
    assert (
        client.post(
            f"/api/mcp/workspaces/workspace-a/capabilities/{SERVER_ID}/enable"
        ).status_code
        == 403
    )
