from __future__ import annotations

import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from data_vault import WorkspaceRepository, upgrade_database
from data_vault.secret_provider import create_default_secret_provider
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from tool_registry import McpEngine
from tool_registry.capability_services import CapabilityServiceDependencies

from api.main import app
from api.services.mcp_services import McpApiService, get_mcp_api_service

ROOT = Path(__file__).resolve().parents[2]
CHILD = ROOT / "packages/tool_registry/tests/mock_server.py"
NOW = datetime(2026, 8, 13, 2, 0, tzinfo=UTC)


class ChildMcpProbe:
    def __init__(self, *, close_after_list: bool = False) -> None:
        self.close_after_list = close_after_list
        self._transport = None
        self._session_context = None
        self._session = None
        self._initialized = False

    async def _start(self) -> ClientSession:
        if self._session is not None:
            return self._session
        parameters = StdioServerParameters(
            command=sys.executable,
            args=[str(CHILD)],
        )
        self._transport = stdio_client(parameters)
        streams = await self._transport.__aenter__()
        self._session_context = ClientSession(*streams)
        self._session = await self._session_context.__aenter__()
        return self._session

    async def _close(self) -> None:
        if self._session_context is not None:
            await self._session_context.__aexit__(None, None, None)
        if self._transport is not None:
            await self._transport.__aexit__(None, None, None)
        self._session = None
        self._session_context = None
        self._transport = None
        self._initialized = False

    async def initialize(self):
        session = await self._start()
        result = await session.initialize()
        self._initialized = True
        return result.model_dump(mode="json", by_alias=True)

    async def initialized(self):
        # ClientSession.initialize sends the required initialized notification.
        return None

    async def list_tools(self):
        session = await self._start()
        if not self._initialized:
            await self.initialize()
        result = await session.list_tools()
        tools = [tool.model_dump(mode="json", by_alias=True) for tool in result.tools]
        if self.close_after_list:
            await self._close()
        return tools

    async def call_tool(self, name: str, arguments: dict):
        session = await self._start()
        if not self._initialized:
            await self.initialize()
        result = await session.call_tool(name, arguments)
        payload = result.model_dump(mode="json", by_alias=True)
        await self._close()
        return payload


class WorkspaceFixture:
    def __init__(self, database) -> None:
        self.repository = WorkspaceRepository(
            str(database), secrets=create_default_secret_provider()
        )

    def set_workspace_tool_enabled_by_workspace(
        self, workspace_id: str, server_id: str, enabled: bool
    ):
        selected = list(self.repository.enabled_tools(workspace_id) or [])
        selected = [item for item in selected if item != server_id]
        if enabled:
            selected.append(server_id)
        self.repository.set_enabled_tools(workspace_id, selected)
        return SimpleNamespace(enabled_tools=selected)


@pytest.mark.asyncio
@pytest.mark.mcp_protocol
async def test_local_api_child_mcp_add_validate_and_single_workspace_enablement(
    tmp_path,
) -> None:
    database = tmp_path / "capability-system-smoke.db"
    upgrade_database(database)
    with sqlite3.connect(database) as connection:
        connection.executemany(
            """INSERT INTO engineering_workspaces (
                workspace_id, session_id, local_path, enabled_tools,
                created_at, updated_at, workspace_name
            ) VALUES (?, ?, ?, '[]', 1, 1, ?)""",
            (
                ("workspace-a", "session-a", str(tmp_path / "a"), "Bracket A"),
                ("workspace-b", "session-b", str(tmp_path / "b"), "Bracket B"),
            ),
        )

    clients: dict[str, ChildMcpProbe] = {}
    gateway_clients: dict[str, ChildMcpProbe] = {}
    probes: dict[str, dict] = {}
    service = McpApiService(
        McpEngine(str(database)),
        SimpleNamespace(workspace_service=WorkspaceFixture(database)),
        CapabilityServiceDependencies(
            database_path=database,
            clock=lambda: NOW,
            validation_clients=clients,
            validation_gateway_clients=gateway_clients,
            validation_read_only_probes=probes,
        ),
    )
    app.dependency_overrides[get_mcp_api_service] = lambda: service
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://wright.local"
        ) as client:
            added = await client.post(
                "/api/mcp/servers",
                json={
                    "name": "Deterministic Child MCP",
                    "type": "stdio",
                    "command": [sys.executable, str(CHILD)],
                    "category": "cad",
                    "description": "Local system-smoke fixture",
                    "installed_version": "1.0.0",
                },
            )
            assert added.status_code == 201
            server_id = added.json()["server_id"]
            with sqlite3.connect(database) as connection:
                connection.execute(
                    "UPDATE mcp_servers SET is_installed = 1 WHERE server_id = ?",
                    (server_id,),
                )
            clients[server_id] = ChildMcpProbe(close_after_list=True)
            gateway_clients[server_id] = ChildMcpProbe(close_after_list=True)

            validated = await client.post(
                f"/api/mcp/servers/{server_id}/validation-runs"
            )
            assert validated.status_code == 200, validated.text
            evidence = validated.json()
            assert evidence["state"] == "passed", evidence
            assert evidence["tool_count"] == 1
            assert "gateway_proxy_validated" in evidence["reason_codes"]
            assert evidence["read_only_probe"] is None

            enabled = await client.post(
                f"/api/mcp/workspaces/workspace-a/capabilities/{server_id}/enable"
            )
            assert enabled.status_code == 200, enabled.text
            assert enabled.json()["workspace_id"] == "workspace-a"
            assert enabled.json()["invocation_approved"] is False

    finally:
        app.dependency_overrides.pop(get_mcp_api_service, None)

    repository = WorkspaceRepository(
        str(database), secrets=create_default_secret_provider()
    )
    assert repository.enabled_tools("workspace-a") == [server_id]
    assert repository.enabled_tools("workspace-b") == []
