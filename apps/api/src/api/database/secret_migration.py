"""Backup-first extraction of legacy plaintext credentials."""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

from core.secrets import CredentialReference, SecretProvider, default_secret_provider

MIGRATION_ID = "043-plaintext-credentials-v1"


class SecretMigrationError(RuntimeError):
    pass


def _table_exists(connection: sqlite3.Connection, table: str) -> bool:
    return (
        connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
        ).fetchone()
        is not None
    )


def _collect(connection: sqlite3.Connection) -> dict[str, Any]:
    api_keys: dict[str, str] = {}
    workspace_tokens: dict[str, str] = {}
    if _table_exists(connection, "system_settings"):
        row = connection.execute(
            "SELECT value FROM system_settings WHERE key = 'api_keys'"
        ).fetchone()
        if row and row[0]:
            try:
                payload = json.loads(row[0])
            except json.JSONDecodeError as exc:
                raise SecretMigrationError(
                    "Legacy API key settings are corrupt"
                ) from exc
            if isinstance(payload, dict):
                api_keys = {
                    str(key): str(value)
                    for key, value in payload.items()
                    if isinstance(value, str) and value
                }
    if _table_exists(connection, "engineering_workspaces"):
        for workspace_id, token in connection.execute(
            "SELECT workspace_id, git_token FROM engineering_workspaces "
            "WHERE git_token IS NOT NULL AND git_token != ''"
        ):
            workspace_tokens[str(workspace_id)] = str(token)
    return {"api_keys": api_keys, "workspace_git_tokens": workspace_tokens}


def _backup_path(database_path: str) -> Path:
    configured = os.environ.get("WRIGHT_SECRET_MIGRATION_BACKUP")
    return Path(configured or f"{database_path}.secrets-backup.json")


def _write_backup(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            if os.name != "nt":
                raise
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump({"migration_id": MIGRATION_ID, **payload}, handle)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        try:
            os.chmod(path, 0o600)
        except OSError:
            if os.name != "nt":
                raise
    finally:
        temporary.unlink(missing_ok=True)


def migrate_plaintext_secrets(
    database_path: str, provider: SecretProvider | None = None
) -> Path | None:
    provider = provider or default_secret_provider()
    with sqlite3.connect(database_path) as connection:
        legacy = _collect(connection)
        if not legacy["api_keys"] and not legacy["workspace_git_tokens"]:
            return None

        backup = _backup_path(database_path)
        if not backup.exists():
            _write_backup(backup, legacy)

        try:
            for name, value in legacy["api_keys"].items():
                reference = CredentialReference("global", "", name)
                provider.set(reference, value)
                if provider.get(reference) != value:
                    raise SecretMigrationError("API credential verification failed")
            for workspace_id, value in legacy["workspace_git_tokens"].items():
                reference = CredentialReference("workspace", workspace_id, "GIT_TOKEN")
                provider.set(reference, value)
                if provider.get(reference) != value:
                    raise SecretMigrationError("Git credential verification failed")
        except Exception as exc:
            raise SecretMigrationError(
                f"Credential migration failed; restore from {backup}"
            ) from exc

        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DELETE FROM system_settings WHERE key = 'api_keys'")
            if _table_exists(connection, "engineering_workspaces"):
                connection.execute(
                    "UPDATE engineering_workspaces SET git_token = NULL "
                    "WHERE git_token IS NOT NULL"
                )
            connection.commit()
        except Exception as exc:
            connection.rollback()
            raise SecretMigrationError(
                f"Plaintext cleanup failed; restore from {backup}"
            ) from exc
        return backup


def restore_plaintext_backup(database_path: str, backup_path: str | Path) -> None:
    payload = json.loads(Path(backup_path).read_text(encoding="utf-8"))
    if payload.get("migration_id") != MIGRATION_ID:
        raise SecretMigrationError("Unsupported credential backup")
    with sqlite3.connect(database_path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "INSERT OR REPLACE INTO system_settings (key, value) VALUES ('api_keys', ?)",
            (json.dumps(payload.get("api_keys", {})),),
        )
        for workspace_id, token in payload.get("workspace_git_tokens", {}).items():
            connection.execute(
                "UPDATE engineering_workspaces SET git_token = ? WHERE workspace_id = ?",
                (token, workspace_id),
            )
        connection.commit()
