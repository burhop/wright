from __future__ import annotations

import sqlite3

import pytest

from data_vault.migrations import (
    LEDGER_TABLE,
    MIGRATIONS,
    database_status,
    upgrade_database,
)


@pytest.mark.parametrize(
    "failed_version", [migration.version for migration in MIGRATIONS]
)
def test_each_migration_rolls_back_operations_and_ledger(tmp_path, failed_version):
    path = tmp_path / f"failure-{failed_version}.db"

    def fail(migration, connection):
        if migration.version == failed_version:
            connection.execute("CREATE TABLE should_rollback (value TEXT NOT NULL)")
            raise RuntimeError("injected interruption")

    with pytest.raises(RuntimeError, match="injected interruption"):
        upgrade_database(path, failure_hook=fail)

    with sqlite3.connect(path) as connection:
        applied = connection.execute(
            f"SELECT version FROM {LEDGER_TABLE} ORDER BY version"
        ).fetchall()
        rollback_table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE name='should_rollback'"
        ).fetchone()
    assert [row[0] for row in applied] == list(range(1, failed_version))
    assert rollback_table is None
    assert database_status(path).current_version == failed_version - 1
