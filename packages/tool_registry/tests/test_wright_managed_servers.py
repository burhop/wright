from __future__ import annotations

import json
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


def test_wright_managed_rivet_server_is_installed_and_active_on_first_seed(tmp_path):
    database = tmp_path / "state.db"
    upgrade_database(database)

    assert reconcile_wright_managed_servers(str(database)) == 1

    row = _row(database)
    assert row is not None
    assert row[0] == "rivet-workflows"
    assert json.loads(row[1]) == ["wright-rivet-mcp"]
    assert row[2:5] == (1, 1, "active")
    assert row[5:] == (1, "wright-managed", "medium")
    with sqlite3.connect(database) as connection:
        tools = connection.execute(
            "SELECT name, is_enabled FROM mcp_tools WHERE server_id='rivet-workflows' ORDER BY name"
        ).fetchall()
    assert [name for name, _enabled in tools] == [
        "create_workflow",
        "inspect_workflow",
        "list_templates",
        "list_workflows",
        "run_workflow",
        "validate_workflow",
    ]
    assert all(enabled == 1 for _name, enabled in tools)


def test_wright_managed_reconcile_preserves_user_disablement(tmp_path):
    database = tmp_path / "state.db"
    upgrade_database(database)
    reconcile_wright_managed_servers(str(database))
    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE mcp_servers SET is_active=0, status='inactive' WHERE server_id='rivet-workflows'"
        )
        connection.execute(
            "UPDATE mcp_tools SET is_enabled=0 WHERE tool_id='rivet-workflows:run_workflow'"
        )
        connection.commit()

    reconcile_wright_managed_servers(str(database))

    assert _row(database)[2:5] == (1, 0, "inactive")
    with sqlite3.connect(database) as connection:
        enabled = connection.execute(
            "SELECT is_enabled FROM mcp_tools WHERE tool_id='rivet-workflows:run_workflow'"
        ).fetchone()[0]
    assert enabled == 0


def test_internal_rivet_server_is_not_in_public_engineering_catalog():
    assert "rivet-workflows" not in {
        entry["server_id"] for entry in ENGINEERING_CATALOG
    }
