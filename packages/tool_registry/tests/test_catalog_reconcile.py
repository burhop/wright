from __future__ import annotations

import sqlite3

from data_vault import upgrade_database
from tool_registry.catalog_reconcile import reconcile_engineering_catalog


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
