import json
import sqlite3

import pytest

from api.database.secret_migration import (
    SecretMigrationError,
    migrate_plaintext_secrets,
    restore_plaintext_backup,
)
from core.secrets import CredentialReference, FileSecretProvider


@pytest.fixture
def legacy_database(tmp_path):
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE system_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO system_settings VALUES ('api_keys', ?)",
            (json.dumps({"OPENAI_API_KEY": "legacy-api-secret"}),),
        )
        connection.execute(
            "CREATE TABLE engineering_workspaces "
            "(workspace_id TEXT PRIMARY KEY, git_token TEXT)"
        )
        connection.execute(
            "INSERT INTO engineering_workspaces VALUES ('workspace-1', 'legacy-git-secret')"
        )
        connection.commit()
    return path


def test_migration_backs_up_verifies_and_removes_plaintext(
    legacy_database, tmp_path, monkeypatch
):
    backup = tmp_path / "migration-backup.json"
    monkeypatch.setenv("WRIGHT_SECRET_MIGRATION_BACKUP", str(backup))
    provider = FileSecretProvider(tmp_path / "protected.json")

    result = migrate_plaintext_secrets(str(legacy_database), provider)

    assert result == backup
    assert backup.exists()
    assert (
        provider.get(CredentialReference("global", "", "OPENAI_API_KEY"))
        == "legacy-api-secret"
    )
    assert (
        provider.get(CredentialReference("workspace", "workspace-1", "GIT_TOKEN"))
        == "legacy-git-secret"
    )
    with sqlite3.connect(legacy_database) as connection:
        assert (
            connection.execute(
                "SELECT value FROM system_settings WHERE key = 'api_keys'"
            ).fetchone()
            is None
        )
        assert (
            connection.execute(
                "SELECT git_token FROM engineering_workspaces"
            ).fetchone()[0]
            is None
        )

    assert migrate_plaintext_secrets(str(legacy_database), provider) is None


def test_failed_provider_keeps_plaintext_and_backup(
    legacy_database, tmp_path, monkeypatch
):
    backup = tmp_path / "migration-backup.json"
    monkeypatch.setenv("WRIGHT_SECRET_MIGRATION_BACKUP", str(backup))

    class FailingProvider:
        def set(self, reference, value):
            raise OSError("unavailable")

        def get(self, reference):
            return None

    with pytest.raises(SecretMigrationError, match="restore from"):
        migrate_plaintext_secrets(str(legacy_database), FailingProvider())

    assert backup.exists()
    with sqlite3.connect(legacy_database) as connection:
        assert (
            "legacy-api-secret"
            in connection.execute(
                "SELECT value FROM system_settings WHERE key = 'api_keys'"
            ).fetchone()[0]
        )


def test_backup_restores_previous_plaintext_state(
    legacy_database, tmp_path, monkeypatch
):
    backup = tmp_path / "migration-backup.json"
    monkeypatch.setenv("WRIGHT_SECRET_MIGRATION_BACKUP", str(backup))
    provider = FileSecretProvider(tmp_path / "protected.json")
    migrate_plaintext_secrets(str(legacy_database), provider)

    restore_plaintext_backup(str(legacy_database), backup)

    with sqlite3.connect(legacy_database) as connection:
        assert (
            "legacy-api-secret"
            in connection.execute(
                "SELECT value FROM system_settings WHERE key = 'api_keys'"
            ).fetchone()[0]
        )
        assert (
            connection.execute(
                "SELECT git_token FROM engineering_workspaces"
            ).fetchone()[0]
            == "legacy-git-secret"
        )
