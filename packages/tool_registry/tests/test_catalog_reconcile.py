from __future__ import annotations

import sqlite3
import json

from data_vault import upgrade_database
from tool_registry.catalog_reconcile import reconcile_engineering_catalog
from tool_registry import catalog_reconcile


def test_schema_upgrade_does_not_seed_or_mutate_catalog_rows(tmp_path):
    database = tmp_path / "state.db"

    upgrade_database(database)

    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM mcp_servers").fetchone() == (0,)


def test_reconcile_seeds_catalog_and_preserves_unknown_server(tmp_path):
    database = tmp_path / "state.db"
    upgrade_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO mcp_servers (
                server_id, name, type, command, created_at, updated_at
            ) VALUES ('user-owned', 'User Owned', 'stdio', 'custom', 1, 1)"""
        )
        connection.commit()

    count = reconcile_engineering_catalog(str(database))

    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT name FROM mcp_servers WHERE server_id='user-owned'"
        ).fetchone() == ("User Owned",)
        assert connection.execute("SELECT COUNT(*) FROM mcp_servers").fetchone()[0] == (
            count + 1
        )


def test_reconcile_resets_only_failed_wright_catalog_install(tmp_path):
    database = tmp_path / "state.db"
    upgrade_database(database)
    reconcile_engineering_catalog(str(database))
    with sqlite3.connect(database) as connection:
        connection.execute(
            """UPDATE mcp_servers SET is_installed=1, is_active=1, status='error',
                error_message='missing' WHERE server_id='openscad-mcp-server'"""
        )
        connection.commit()

    reconcile_engineering_catalog(str(database))

    with sqlite3.connect(database) as connection:
        assert connection.execute(
            """SELECT is_installed, is_active, status, error_message
            FROM mcp_servers WHERE server_id='openscad-mcp-server'"""
        ).fetchone() == (0, 0, "inactive", None)


def test_reconcile_persists_trusted_launch_environment(tmp_path, monkeypatch):
    database = tmp_path / "state.db"
    upgrade_database(database)
    entry = {
        "server_id": "workspace-aware",
        "name": "Workspace Aware",
        "type": "stdio",
        "command": json.dumps(["server"]),
        "category": "cad",
        "description": "Synthetic server",
        "launch_env": json.dumps({"SERVER_WORKSPACE": "{workspace.path}"}),
        "verification_state": "verified_mcp",
        "installability_tier": "tested",
        "risk_level": "low",
        "deployment_mode": "local-only",
        "platform_support": {},
        "host_software_required": [],
        "credentials_required": [],
        "default_enabled": True,
        "approval_gates": [],
        "validation_result": {},
    }
    monkeypatch.setattr(catalog_reconcile, "ENGINEERING_CATALOG", [entry])

    reconcile_engineering_catalog(str(database))

    with sqlite3.connect(database) as connection:
        launch_env = connection.execute(
            "SELECT launch_env FROM mcp_servers WHERE server_id='workspace-aware'"
        ).fetchone()[0]
    assert json.loads(launch_env) == {"SERVER_WORKSPACE": "{workspace.path}"}
