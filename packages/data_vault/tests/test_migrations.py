from __future__ import annotations

import sqlite3

import pytest

from data_vault.migrations import (
    LEDGER_TABLE,
    MIGRATIONS,
    database_status,
    upgrade_database,
)
from data_vault.models import DatabaseCompatibilityError, DatabaseIntegrityError

from fixtures import corrupt_database, create_partial_legacy_database


def test_fresh_database_applies_numbered_migrations_in_order(tmp_path):
    path = tmp_path / "fresh.db"

    result = upgrade_database(path)
    status = database_status(path)

    assert result.starting_version == 0
    assert result.ending_version == len(MIGRATIONS)
    assert [item["version"] for item in result.applied] == list(
        range(1, len(MIGRATIONS) + 1)
    )
    assert status.ready is True
    assert status.pending == ()
    with sqlite3.connect(path) as connection:
        entries = connection.execute(
            f"SELECT version, name, checksum FROM {LEDGER_TABLE} ORDER BY version"
        ).fetchall()
    assert entries == [
        (migration.version, migration.name, migration.checksum)
        for migration in MIGRATIONS
    ]


def test_partial_legacy_database_is_adopted_without_losing_records(tmp_path):
    path = create_partial_legacy_database(tmp_path / "legacy.db")

    upgrade_database(path)

    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT name FROM mcp_servers WHERE server_id='custom-user-server'"
        ).fetchone() == ("Custom User Server",)
        assert connection.execute(
            "SELECT local_path FROM engineering_workspaces WHERE workspace_id='workspace-one'"
        ).fetchone() == ("/workspace/one",)
        assert connection.execute(
            "SELECT session_id FROM workspace_agent_sessions WHERE workspace_id='workspace-one'"
        ).fetchone() == ("session-one",)


def test_upgrade_is_idempotent(tmp_path):
    path = tmp_path / "state.db"
    upgrade_database(path)

    second = upgrade_database(path)

    assert second.applied == ()
    assert second.starting_version == second.ending_version == len(MIGRATIONS)


def test_complete_unversioned_feature_043_shape_is_adopted(tmp_path):
    path = tmp_path / "feature-043.db"
    upgrade_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute("DROP TABLE wright_schema_migrations")
        connection.execute(
            "INSERT INTO system_settings VALUES ('legacy-marker', 'preserve')"
        )
        connection.commit()

    result = upgrade_database(path)

    assert result.starting_version == 0
    assert result.ending_version == len(MIGRATIONS)
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT value FROM system_settings WHERE key='legacy-marker'"
        ).fetchone() == ("preserve",)


def test_checksum_drift_fails_without_mutation(tmp_path):
    path = tmp_path / "state.db"
    upgrade_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            f"UPDATE {LEDGER_TABLE} SET checksum='tampered' WHERE version=1"
        )
        connection.commit()

    with pytest.raises(DatabaseCompatibilityError, match="checksum mismatch"):
        upgrade_database(path)

    with sqlite3.connect(path) as connection:
        assert connection.execute(
            f"SELECT checksum FROM {LEDGER_TABLE} WHERE version=1"
        ).fetchone() == ("tampered",)
        assert connection.execute(
            f"SELECT COUNT(*) FROM {LEDGER_TABLE}"
        ).fetchone() == (len(MIGRATIONS),)


def test_future_version_is_rejected(tmp_path):
    path = tmp_path / "future.db"
    upgrade_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            f"INSERT INTO {LEDGER_TABLE} VALUES (?, ?, ?, ?, ?, ?)",
            (99, "future", "future", "now", 0, "99.0.0"),
        )
        connection.commit()

    with pytest.raises(DatabaseCompatibilityError, match="newer"):
        database_status(path)


def test_corrupt_database_is_rejected(tmp_path):
    path = corrupt_database(tmp_path / "corrupt.db")

    with pytest.raises(DatabaseIntegrityError):
        database_status(path)


def test_foreign_key_corruption_is_rejected(tmp_path):
    path = tmp_path / "foreign-key.db"
    upgrade_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(
            """INSERT INTO workspace_agent_sessions
            (workspace_id, session_id, created_at, updated_at)
            VALUES ('missing-workspace', 'orphan-session', 1, 1)"""
        )
        connection.commit()

    with pytest.raises(DatabaseIntegrityError, match="workspace_agent_sessions"):
        database_status(path)
