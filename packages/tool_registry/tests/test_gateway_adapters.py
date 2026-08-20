from __future__ import annotations

import time

import pytest

from data_vault import upgrade_database

from tool_registry.db import insert_server, insert_tools, update_server
from tool_registry.gateway_adapters import (
    DatabaseGatewayCatalog,
    EngineGatewayLifecycle,
)
from tool_registry.models import McpServer, McpTool


def _server(server_id: str, *, risk_level: str) -> McpServer:
    now = int(time.time())
    return McpServer(
        server_id=server_id,
        name=server_id,
        type="stdio",
        command=["server"],
        is_active=True,
        is_installed=True,
        status="active",
        risk_level=risk_level,
        approval_gates=["wright-mcp-appliance-bundle"],
        created_at=now,
        updated_at=now,
    )


def _tool(server_id: str) -> McpTool:
    return McpTool(
        tool_id=f"{server_id}:ping",
        server_id=server_id,
        name="ping",
        description="Ping",
        input_schema={"type": "object"},
        is_enabled=True,
        created_at=int(time.time()),
    )


def test_database_gateway_catalog_projects_only_policy_required_approvals(
    tmp_path,
) -> None:
    db_path = str(tmp_path / "gateway-adapter.db")
    upgrade_database(db_path)
    insert_server(db_path, _server("bundled-low-risk", risk_level="low"))
    insert_tools(db_path, [_tool("bundled-low-risk")])
    insert_server(db_path, _server("machine-high-risk", risk_level="high"))
    insert_tools(db_path, [_tool("machine-high-risk")])

    catalog = DatabaseGatewayCatalog(db_path)

    low_risk_tool = catalog.tools("bundled-low-risk")[0]
    high_risk_tool = catalog.tools("machine-high-risk")[0]

    assert low_risk_tool.required_approvals == frozenset()
    assert high_risk_tool.required_approvals == frozenset(
        {"wright-mcp-appliance-bundle"}
    )


def test_database_gateway_server_revision_ignores_health_but_tracks_authority(
    tmp_path,
) -> None:
    db_path = str(tmp_path / "gateway-revision.db")
    upgrade_database(db_path)
    server = _server("remote-server", risk_level="low")
    insert_server(db_path, server)
    insert_tools(db_path, [_tool("remote-server")])
    catalog = DatabaseGatewayCatalog(db_path)

    initial = catalog.tools("remote-server")[0].provenance["server_revision"]
    update_server(
        db_path,
        "remote-server",
        {
            "is_active": False,
            "status": "inactive",
            "updated_at": server.updated_at + 1,
        },
    )
    after_health_change = catalog.tools("remote-server")[0].provenance[
        "server_revision"
    ]
    update_server(
        db_path,
        "remote-server",
        {"command": ["replacement-server"], "updated_at": server.updated_at + 2},
    )
    after_authority_change = catalog.tools("remote-server")[0].provenance[
        "server_revision"
    ]

    assert after_health_change == initial
    assert after_authority_change != initial


class _Lifecycle:
    def __init__(self) -> None:
        self.runner = None

    def runner_for(self, server_id: str):
        return self.runner


class _Engine:
    def __init__(self, *, starts_successfully: bool = True) -> None:
        self.lifecycle = _Lifecycle()
        self.starts: list[tuple[str, str, object]] = []
        self.starts_successfully = starts_successfully

    async def start_server(
        self,
        server_id: str,
        workspace_path: str,
        *,
        approval_context,
    ) -> None:
        self.starts.append((server_id, workspace_path, approval_context))
        if self.starts_successfully:
            self.lifecycle.runner = object()


@pytest.mark.asyncio
async def test_engine_gateway_notifies_after_lazy_tool_discovery() -> None:
    engine = _Engine()
    changed: list[str] = []
    lifecycle = EngineGatewayLifecycle(
        engine,  # type: ignore[arg-type]
        tools_changed=changed.append,
    )

    await lifecycle.ensure_started(
        "remote-server",
        workspace_path="D:\\workspace",
        approval_context={"workspace_approvals": ["network_access_approval"]},
    )
    await lifecycle.ensure_started(
        "remote-server",
        workspace_path="D:\\workspace",
        approval_context={"workspace_approvals": ["network_access_approval"]},
    )

    assert len(engine.starts) == 1
    assert changed == ["remote-server"]


@pytest.mark.asyncio
async def test_engine_gateway_does_not_notify_after_failed_discovery() -> None:
    engine = _Engine(starts_successfully=False)
    changed: list[str] = []
    lifecycle = EngineGatewayLifecycle(
        engine,  # type: ignore[arg-type]
        tools_changed=changed.append,
    )

    await lifecycle.ensure_started(
        "remote-server",
        workspace_path="D:\\workspace",
        approval_context={},
    )

    assert changed == []
