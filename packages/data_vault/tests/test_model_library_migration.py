from __future__ import annotations

import sqlite3

import pytest

from data_vault.migrations import LEDGER_TABLE, MIGRATIONS, upgrade_database


MODEL_TABLES = {
    "model_catalog_snapshots",
    "model_install_plans",
    "model_operations",
    "model_content_objects",
    "model_installations",
    "model_installation_artifacts",
    "model_test_evidence",
    "model_capability_bindings",
    "model_references",
    "model_leases",
}


def test_migration_16_is_additive_contiguous_and_preserves_legacy_state(
    tmp_path,
) -> None:
    path = tmp_path / "models.db"
    result = upgrade_database(path, migrations=MIGRATIONS[:15])
    assert result.ending_version == 15
    with sqlite3.connect(path) as connection:
        connection.execute(
            """INSERT INTO mcp_servers
            (server_id, name, type, command, created_at, updated_at)
            VALUES ('legacy-server', 'Legacy Server', 'stdio', '[\"legacy\"]', 1, 1)"""
        )
        connection.commit()

    result = upgrade_database(path, migrations=MIGRATIONS[:16])

    assert result.applied == (
        {"version": 16, "name": "local_engineering_model_library"},
    )
    with sqlite3.connect(path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert MODEL_TABLES <= tables
        assert connection.execute(
            "SELECT name FROM mcp_servers WHERE server_id='legacy-server'"
        ).fetchone() == ("Legacy Server",)
    assert [item.version for item in MIGRATIONS] == list(range(1, len(MIGRATIONS) + 1))


def test_migration_16_is_idempotent(tmp_path) -> None:
    path = tmp_path / "models.db"
    upgrade_database(path, migrations=MIGRATIONS[:16])
    second = upgrade_database(path, migrations=MIGRATIONS[:16])
    assert second.applied == ()
    assert second.starting_version == second.ending_version == 16


def test_migration_16_failure_rolls_back_ledger_entry(tmp_path) -> None:
    path = tmp_path / "models.db"
    upgrade_database(path, migrations=MIGRATIONS[:15])
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE model_installations (wrong TEXT)")
        connection.commit()

    with pytest.raises(Exception):
        upgrade_database(path)

    with sqlite3.connect(path) as connection:
        assert connection.execute(
            f"SELECT COUNT(*) FROM {LEDGER_TABLE} WHERE version=16"
        ).fetchone() == (0,)
        assert (
            connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='model_operations'"
            ).fetchone()
            is None
        )
