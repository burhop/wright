from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from data_vault.backup import create_backup, load_manifest, restore_backup
from data_vault.migrations import database_status, upgrade_database
from data_vault.models import DatabaseCompatibilityError


def _setting(path, value: str) -> None:
    with closing(sqlite3.connect(path)) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO system_settings (key, value) VALUES ('sample', ?)",
            (value,),
        )
        connection.commit()


def _read_setting(path) -> str:
    with closing(sqlite3.connect(path)) as connection:
        return connection.execute(
            "SELECT value FROM system_settings WHERE key='sample'"
        ).fetchone()[0]


def test_backup_publishes_verified_snapshot_and_manifest(tmp_path):
    database = tmp_path / "state.db"
    upgrade_database(database)
    _setting(database, "stored")

    result = create_backup(database, output_dir=tmp_path / "safe")
    manifest, snapshot = load_manifest(result.manifest_path)

    assert snapshot.read_bytes()
    assert manifest.database_sha256 == result.sha256
    assert manifest.schema_version == database_status(database).current_version
    assert _read_setting(snapshot) == "stored"
    if os.name != "nt":
        assert snapshot.stat().st_mode & 0o777 == 0o600
        assert os.stat(result.manifest_path).st_mode & 0o777 == 0o600


def test_tampered_snapshot_is_rejected_without_touching_active_database(tmp_path):
    database = tmp_path / "state.db"
    upgrade_database(database)
    _setting(database, "active")
    result = create_backup(database)
    snapshot = (
        tmp_path
        / "backups"
        / json.loads(open(result.manifest_path, encoding="utf-8").read())[
            "database_file"
        ]
    )
    snapshot.write_bytes(snapshot.read_bytes() + b"tampered")

    with pytest.raises(DatabaseCompatibilityError, match="size does not match"):
        restore_backup(database, result.manifest_path)

    assert _read_setting(database) == "active"


def test_restore_activates_snapshot_and_preserves_displaced_state(tmp_path):
    database = tmp_path / "state.db"
    upgrade_database(database)
    _setting(database, "before")
    backup = create_backup(database)
    _setting(database, "after")

    result = restore_backup(database, backup.manifest_path)

    assert result.ready is True
    assert _read_setting(database) == "before"
    assert result.rollback_snapshot_path is not None
    assert _read_setting(result.rollback_snapshot_path) == "after"


def test_post_activation_interruption_restores_displaced_database(tmp_path):
    database = tmp_path / "state.db"
    upgrade_database(database)
    _setting(database, "snapshot")
    backup = create_backup(database)
    _setting(database, "active")

    def interrupt(stage: str) -> None:
        if stage == "after_activation":
            raise RuntimeError("injected restore interruption")

    with pytest.raises(RuntimeError, match="injected restore interruption"):
        restore_backup(database, backup.manifest_path, failure_hook=interrupt)

    assert _read_setting(database) == "active"


def test_manifest_path_escape_is_rejected(tmp_path):
    database = tmp_path / "state.db"
    upgrade_database(database)
    backup = create_backup(database)
    manifest_path = tmp_path / "backups" / "unsafe.manifest.json"
    payload = json.loads(open(backup.manifest_path, encoding="utf-8").read())
    payload["database_file"] = "../state.db"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(DatabaseCompatibilityError, match="path is unsafe"):
        restore_backup(database, manifest_path)


def test_verified_backup_can_replace_corrupt_active_database(tmp_path):
    database = tmp_path / "state.db"
    upgrade_database(database)
    _setting(database, "healthy")
    backup = create_backup(database)
    database.write_bytes(b"corrupt active database")

    result = restore_backup(database, backup.manifest_path)

    assert result.ready is True
    assert _read_setting(database) == "healthy"
    assert result.rollback_snapshot_path is not None
    assert (
        Path(result.rollback_snapshot_path).read_bytes() == b"corrupt active database"
    )


def test_upgrade_of_existing_legacy_state_creates_preupgrade_backup(tmp_path):
    database = tmp_path / "legacy.db"
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("CREATE TABLE legacy_user_data (value TEXT)")
        connection.execute("INSERT INTO legacy_user_data VALUES ('preserve')")
        connection.commit()

    result = upgrade_database(database)

    assert result.backup_manifest is not None
    manifest, snapshot = load_manifest(result.backup_manifest)
    assert manifest.schema_version == 0
    with closing(sqlite3.connect(snapshot)) as connection:
        assert connection.execute("SELECT value FROM legacy_user_data").fetchone() == (
            "preserve",
        )
