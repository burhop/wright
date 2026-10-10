import json
import sqlite3

from data_vault import upgrade_database
from tool_registry.catalog_reconcile import reconcile_wright_managed_servers
from workspace_service.adapters.runtime import _with_builtin_workspace_tools
from workspace_service.use_cases.tools import _with_builtin_tools


def test_workspace_tools_do_not_inject_retired_engine():
    assert _with_builtin_tools(None) == []
    tools = ["rivet-workflows", "Solid Edge MCP", "Rivet Workflows", "BREP"]
    assert _with_builtin_tools(tools) == ["Solid Edge MCP", "BREP"]
    assert _with_builtin_workspace_tools(tools) == ["Solid Edge MCP", "BREP"]


def test_reconcile_retires_managed_rivet_without_losing_history_or_user_tools(tmp_path):
    database = tmp_path / "state.db"
    upgrade_database(database)
    with sqlite3.connect(database) as db:
        db.execute("""INSERT INTO mcp_servers
            (server_id, name, type, command, deployment_mode, is_active, is_installed,
             status, created_at, updated_at)
            VALUES ('rivet-workflows', 'Rivet Workflows', 'stdio', '[]',
                    'wright-managed', 1, 1, 'active', 1, 1)""")
        db.execute(
            """INSERT INTO mcp_tools
            (tool_id, server_id, name, input_schema, is_enabled, created_at)
            VALUES ('rivet-workflows:old', 'rivet-workflows', 'old', ?, 1, 1)""",
            (json.dumps({}),),
        )
        db.execute("""INSERT INTO mcp_servers
            (server_id, name, type, command, is_active, is_installed, status, created_at, updated_at)
            VALUES ('independent', 'Independent MCP', 'stdio', '[]', 1, 1, 'active', 1, 1)""")
    assert reconcile_wright_managed_servers(str(database)) == 0
    assert reconcile_wright_managed_servers(str(database)) == 0
    with sqlite3.connect(database) as db:
        assert db.execute(
            "SELECT is_active,is_installed,status FROM mcp_servers WHERE server_id='rivet-workflows'"
        ).fetchone() == (0, 0, "inactive")
        assert db.execute(
            "SELECT is_enabled FROM mcp_tools WHERE tool_id='rivet-workflows:old'"
        ).fetchone() == (0,)
        assert db.execute(
            "SELECT is_active,is_installed FROM mcp_servers WHERE server_id='independent'"
        ).fetchone() == (1, 1)
