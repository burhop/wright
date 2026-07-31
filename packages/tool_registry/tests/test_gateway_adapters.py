from __future__ import annotations

import time

from data_vault import upgrade_database

from tool_registry.db import insert_server, insert_tools
from tool_registry.gateway_adapters import DatabaseGatewayCatalog
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
