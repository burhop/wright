from __future__ import annotations

import sqlite3

from data_vault import upgrade_database
from tool_registry.catalog_reconcile import reconcile_wright_managed_servers
from tool_registry.engineering_catalog import ENGINEERING_CATALOG


def _row(database):
    with sqlite3.connect(database) as connection:
        return connection.execute(
            """SELECT server_id, command, is_installed, is_active, status,
                      default_enabled, deployment_mode, risk_level
               FROM mcp_servers WHERE server_id='rivet-workflows'"""
        ).fetchone()


def test_fresh_start_does_not_install_retired_rivet_server(tmp_path):
    database = tmp_path / "state.db"
    upgrade_database(database)

    assert reconcile_wright_managed_servers(str(database)) == 0
    assert _row(database) is None
    with sqlite3.connect(database) as connection:
        tools = connection.execute(
            "SELECT name, is_enabled FROM mcp_tools WHERE server_id='rivet-workflows' ORDER BY name"
        ).fetchall()
    assert tools == []


def test_wright_managed_reconcile_preserves_independent_user_disablement(tmp_path):
    database = tmp_path / "state.db"
    upgrade_database(database)
    reconcile_wright_managed_servers(str(database))
    with sqlite3.connect(database) as connection:
        connection.execute("""INSERT INTO mcp_servers
            (server_id,name,type,command,is_active,is_installed,status,created_at,updated_at)
            VALUES ('independent','Independent MCP','stdio','[]',0,1,'inactive',1,1)""")
        connection.commit()

    reconcile_wright_managed_servers(str(database))

    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT is_installed,is_active,status FROM mcp_servers WHERE server_id='independent'"
        ).fetchone() == (1, 0, "inactive")


def test_internal_rivet_server_is_not_in_public_engineering_catalog():
    assert "rivet-workflows" not in {
        entry["server_id"] for entry in ENGINEERING_CATALOG
    }
