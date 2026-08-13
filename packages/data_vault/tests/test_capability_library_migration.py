from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from data_vault.backup import load_manifest
from data_vault.migrations import LEDGER_TABLE, upgrade_database
from capability_library_v12 import (
    CUSTOM_SERVER_ID,
    ERROR_SERVER_ID,
    LEGACY_CATALOG_SERVER_ID,
    LEGACY_TOOL_ID,
    WORKSPACE_ID,
    create_capability_library_v12_database,
)


def _sentinel_state(path: Path) -> dict[str, object]:
    with sqlite3.connect(path) as connection:
        servers = connection.execute(
            """SELECT server_id, name, type, command, is_active, is_installed,
                      status, error_message, installed_version, env_vars,
                      credentials_required, default_enabled
               FROM mcp_servers
               WHERE server_id IN (?, ?, ?) ORDER BY server_id""",
            (LEGACY_CATALOG_SERVER_ID, CUSTOM_SERVER_ID, ERROR_SERVER_ID),
        ).fetchall()
        tool = connection.execute(
            """SELECT tool_id, server_id, name, is_enabled, output_schema,
                      annotations, meta FROM mcp_tools WHERE tool_id=?""",
            (LEGACY_TOOL_ID,),
        ).fetchone()
        workspace = connection.execute(
            """SELECT workspace_id, session_id, local_path, enabled_tools,
                      workspace_name FROM engineering_workspaces WHERE workspace_id=?""",
            (WORKSPACE_ID,),
        ).fetchone()
    return {"servers": servers, "tool": tool, "workspace": workspace}


def test_v12_upgrade_is_additive_backed_up_idempotent_and_old_reader_safe(
    tmp_path,
) -> None:
    database = create_capability_library_v12_database(tmp_path / "legacy-v12.db")
    before = _sentinel_state(database)

    result = upgrade_database(database, backup_dir=tmp_path / "backups")

    assert result.starting_version == 12
    assert result.ending_version == 16
    assert result.applied == (
        {"version": 13, "name": "capability_library_onboarding"},
        {"version": 14, "name": "rivet_workspace_mcp_gateway"},
        {"version": 15, "name": "rivet_engineering_scenario_reports"},
        {"version": 16, "name": "local_engineering_model_library"},
    )
    assert result.backup_manifest is not None
    assert result.diagnostics == (
        {
            "code": "pre_upgrade_backup_created",
            "from_version": 12,
            "to_version": 16,
        },
        {
            "code": "capability_library_migration_applied",
            "version": 13,
            "preserved_existing_rows": True,
        },
    )
    manifest, snapshot = load_manifest(result.backup_manifest)
    assert manifest.schema_version == 12
    assert snapshot.is_file()
    assert _sentinel_state(database) == before

    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT transport_variant FROM mcp_servers WHERE server_id=?",
            (LEGACY_CATALOG_SERVER_ID,),
        ).fetchone() == (None,)
        # A schema-12 reader/writer that names only old columns remains valid.
        connection.execute(
            """INSERT INTO mcp_servers
               (server_id, name, type, command, created_at, updated_at)
               VALUES ('old-reader-row', 'Old reader row', 'stdio', '["old"]', 1, 1)"""
        )
        assert connection.execute(
            "SELECT name, command FROM mcp_servers WHERE server_id='old-reader-row'"
        ).fetchone() == ("Old reader row", '["old"]')
        connection.rollback()

    second = upgrade_database(database, backup_dir=tmp_path / "backups")
    assert second.applied == ()
    assert second.backup_manifest is None
    assert _sentinel_state(database) == before


def test_v12_upgrade_failure_rolls_back_schema_and_preserves_verified_backup(
    tmp_path,
) -> None:
    database = create_capability_library_v12_database(tmp_path / "failed-v12.db")
    before = _sentinel_state(database)
    backup_dir = tmp_path / "backups"

    def fail_after_operations(migration, _connection) -> None:
        if migration.version == 13:
            raise RuntimeError("simulated capability migration interruption")

    with pytest.raises(RuntimeError, match="simulated capability migration"):
        upgrade_database(
            database,
            backup_dir=backup_dir,
            failure_hook=fail_after_operations,
        )

    with sqlite3.connect(database) as connection:
        assert connection.execute(
            f"SELECT MAX(version) FROM {LEDGER_TABLE}"
        ).fetchone() == (12,)
        assert (
            connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='catalog_snapshots'"
            ).fetchone()
            is None
        )
        assert "transport_variant" not in {
            row[1] for row in connection.execute("PRAGMA table_info(mcp_servers)")
        }
    assert _sentinel_state(database) == before
    manifests = sorted(backup_dir.glob("*.manifest.json"))
    assert len(manifests) == 1
    manifest, snapshot = load_manifest(manifests[0])
    assert manifest.schema_version == 12
    assert snapshot.is_file()
