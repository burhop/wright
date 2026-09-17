from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import closing

import pytest

from data_vault.cli import run
from data_vault.lifecycle_lock import lifecycle_lock
from data_vault.models import DatabaseBusyError


def test_cli_status_upgrade_backup_restore_json_contract(tmp_path, capsys):
    database = tmp_path / "state.db"

    assert run(["--json", "status", "--database", str(database)]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["ready"] is False
    assert status["pending"]
    assert database.exists() is False

    assert run(["--json", "upgrade", "--database", str(database)]) == 0
    upgraded = json.loads(capsys.readouterr().out)
    assert upgraded["ready"] is True

    assert run(["--json", "backup", "--database", str(database)]) == 0
    backup = json.loads(capsys.readouterr().out)
    assert backup["manifest_path"].endswith(".manifest.json")

    with closing(sqlite3.connect(database)) as connection:
        connection.execute(
            "INSERT INTO system_settings (key, value) VALUES ('changed', 'yes')"
        )
        connection.commit()
    assert (
        run(
            [
                "--json",
                "restore",
                "--database",
                str(database),
                "--manifest",
                backup["manifest_path"],
            ]
        )
        == 0
    )
    restored = json.loads(capsys.readouterr().out)
    assert restored["ready"] is True


def test_cli_errors_use_stable_exit_code_and_no_row_values(tmp_path, capsys):
    database = tmp_path / "corrupt.db"
    seeded_value = "test-secret-value"
    database.write_bytes(f"not sqlite {seeded_value}".encode())

    assert run(["--json", "status", "--database", str(database)]) == 4
    output = capsys.readouterr().err
    assert seeded_value not in output
    assert json.loads(output)["success"] is False


def test_lifecycle_lock_times_out_for_concurrent_operation(tmp_path):
    database = tmp_path / "state.db"
    entered = threading.Event()
    release = threading.Event()

    def hold_lock():
        with lifecycle_lock(database):
            entered.set()
            release.wait(timeout=5)

    thread = threading.Thread(target=hold_lock)
    thread.start()
    assert entered.wait(timeout=2)
    try:
        with pytest.raises(DatabaseBusyError):
            with lifecycle_lock(database, timeout=0.05):
                pass
    finally:
        release.set()
        thread.join(timeout=2)


def test_cli_filesystem_failure_uses_stable_exit_code(tmp_path, capsys):
    database = tmp_path / "state.db"
    assert run(["upgrade", "--database", str(database)]) == 0
    capsys.readouterr()
    invalid_directory = tmp_path / "not-a-directory"
    invalid_directory.write_text("occupied", encoding="utf-8")

    assert (
        run(
            [
                "--json",
                "backup",
                "--database",
                str(database),
                "--output-dir",
                str(invalid_directory),
            ]
        )
        == 6
    )
    assert json.loads(capsys.readouterr().err)["success"] is False
