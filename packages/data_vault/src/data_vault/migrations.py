from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Sequence

from .lifecycle_lock import lifecycle_lock
from .models import (
    DatabaseBusyError,
    DatabaseCompatibilityError,
    DatabaseFilesystemError,
    DatabaseIntegrityError,
    DatabaseLifecycleError,
    DatabaseStatus,
    UpgradeResult,
)
from .state_store import connect_state_db

PRODUCT_VERSION = "0.1.0"
LEDGER_TABLE = "wright_schema_migrations"


@dataclass(frozen=True)
class Operation:
    kind: str
    sql: str
    table: str | None = None
    column: str | None = None

    def canonical(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "sql": " ".join(self.sql.split()),
            "table": self.table,
            "column": self.column,
        }

    def apply(self, connection: sqlite3.Connection) -> None:
        if self.kind == "add_column":
            assert self.table and self.column
            columns = {
                str(row[1])
                for row in connection.execute(f'PRAGMA table_info("{self.table}")')
            }
            if self.column in columns:
                return
        connection.execute(self.sql)


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    operations: tuple[Operation, ...]

    @property
    def checksum(self) -> str:
        payload = {
            "version": self.version,
            "name": self.name,
            "operations": [operation.canonical() for operation in self.operations],
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()


def sql(statement: str) -> Operation:
    return Operation("sql", statement)


def add_column(table: str, column: str, definition: str) -> Operation:
    return Operation(
        "add_column",
        f'ALTER TABLE "{table}" ADD COLUMN "{column}" {definition}',
        table,
        column,
    )


MCP_COLUMNS = (
    ("is_installed", "INTEGER NOT NULL DEFAULT 0 CHECK(is_installed IN (0, 1))"),
    ("image_url", "TEXT"),
    ("description", "TEXT"),
    ("source_url", "TEXT"),
    ("installed_version", "TEXT"),
    ("env_vars", "TEXT"),
    ("instructions", "TEXT"),
    ("verification_state", "TEXT DEFAULT 'user_reported_url_needed'"),
    ("installability_tier", "TEXT DEFAULT 'might_work'"),
    ("risk_level", "TEXT DEFAULT 'low'"),
    ("deployment_mode", "TEXT DEFAULT 'unknown'"),
    ("platform_support", "TEXT"),
    ("host_software_required", "TEXT"),
    ("credentials_required", "TEXT"),
    ("default_enabled", "INTEGER DEFAULT 1"),
    ("approval_gates", "TEXT"),
    ("validation_result", "TEXT"),
    ("follow_up_url", "TEXT"),
    ("install_blocked_reason", "TEXT"),
)

MIGRATIONS: tuple[Migration, ...] = (
    Migration(
        1,
        "mcp_registry",
        (
            sql("""CREATE TABLE IF NOT EXISTS mcp_servers (
                server_id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE,
                type TEXT NOT NULL CHECK(type IN ('stdio', 'sse', 'webmcp')),
                command TEXT, is_active INTEGER NOT NULL DEFAULT 0 CHECK(is_active IN (0, 1)),
                is_installed INTEGER NOT NULL DEFAULT 0 CHECK(is_installed IN (0, 1)),
                status TEXT NOT NULL DEFAULT 'inactive' CHECK(status IN ('active', 'inactive', 'error')),
                error_message TEXT, category TEXT NOT NULL DEFAULT 'utilities',
                created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL,
                image_url TEXT, description TEXT, source_url TEXT, installed_version TEXT,
                env_vars TEXT, instructions TEXT,
                verification_state TEXT DEFAULT 'user_reported_url_needed',
                installability_tier TEXT DEFAULT 'might_work', risk_level TEXT DEFAULT 'low',
                deployment_mode TEXT DEFAULT 'unknown', platform_support TEXT,
                host_software_required TEXT, credentials_required TEXT,
                default_enabled INTEGER DEFAULT 1, approval_gates TEXT,
                validation_result TEXT, follow_up_url TEXT, install_blocked_reason TEXT
            )"""),
            *(
                add_column("mcp_servers", name, definition)
                for name, definition in MCP_COLUMNS
            ),
            sql("""CREATE TABLE IF NOT EXISTS mcp_tools (
                tool_id TEXT PRIMARY KEY, server_id TEXT NOT NULL, name TEXT NOT NULL,
                description TEXT, input_schema TEXT NOT NULL,
                is_enabled INTEGER NOT NULL DEFAULT 1 CHECK(is_enabled IN (0, 1)),
                created_at INTEGER NOT NULL,
                FOREIGN KEY (server_id) REFERENCES mcp_servers(server_id) ON DELETE CASCADE
            )"""),
        ),
    ),
    Migration(
        2,
        "workspace_sessions",
        (
            sql("""CREATE TABLE IF NOT EXISTS engineering_workspaces (
                workspace_id TEXT PRIMARY KEY, session_id TEXT NOT NULL UNIQUE,
                local_path TEXT NOT NULL, git_remote_url TEXT, git_username TEXT,
                git_token TEXT, enabled_tools TEXT, created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL, workspace_name TEXT, workspace_prompt TEXT,
                git_large_file_threshold INTEGER DEFAULT 10485760
            )"""),
            add_column("engineering_workspaces", "enabled_tools", "TEXT"),
            add_column("engineering_workspaces", "workspace_name", "TEXT"),
            add_column("engineering_workspaces", "workspace_prompt", "TEXT"),
            add_column(
                "engineering_workspaces",
                "git_large_file_threshold",
                "INTEGER DEFAULT 10485760",
            ),
            sql("""CREATE TABLE IF NOT EXISTS workspace_agent_sessions (
                workspace_id TEXT NOT NULL, session_id TEXT NOT NULL UNIQUE,
                agent_id TEXT NOT NULL DEFAULT 'hermes', title TEXT,
                created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL,
                is_archived INTEGER NOT NULL DEFAULT 0 CHECK(is_archived IN (0, 1)),
                PRIMARY KEY (workspace_id, session_id),
                FOREIGN KEY (workspace_id) REFERENCES engineering_workspaces(workspace_id) ON DELETE CASCADE
            )"""),
            sql("""INSERT OR IGNORE INTO workspace_agent_sessions
                (workspace_id, session_id, agent_id, title, created_at, updated_at, is_archived)
                SELECT workspace_id, session_id, 'hermes', workspace_name, created_at, updated_at, 0
                FROM engineering_workspaces WHERE session_id IS NOT NULL AND session_id != ''"""),
        ),
    ),
    Migration(
        3,
        "conversation_settings",
        (
            sql("""CREATE TABLE IF NOT EXISTS agent_contexts (
                workspace_id TEXT PRIMARY KEY, context_data TEXT, updated_at INTEGER NOT NULL,
                FOREIGN KEY (workspace_id) REFERENCES engineering_workspaces(workspace_id) ON DELETE CASCADE
            )"""),
            sql("""CREATE TABLE IF NOT EXISTS chat_messages (
                id TEXT PRIMARY KEY, session_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL, timestamp INTEGER NOT NULL,
                trace_id TEXT, created_at INTEGER NOT NULL
            )"""),
            sql(
                "CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id, timestamp)"
            ),
            sql("""CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY, value TEXT NOT NULL
            )"""),
        ),
    ),
)


def validate_definitions(migrations: Sequence[Migration] = MIGRATIONS) -> None:
    versions = [migration.version for migration in migrations]
    names = [migration.name for migration in migrations]
    if versions != list(range(1, len(migrations) + 1)):
        raise DatabaseCompatibilityError("Migration versions must be contiguous")
    if len(names) != len(set(names)):
        raise DatabaseCompatibilityError("Migration names must be unique")


def _integrity(connection: sqlite3.Connection) -> None:
    row = connection.execute("PRAGMA quick_check").fetchone()
    if not row or str(row[0]).lower() != "ok":
        raise DatabaseIntegrityError("Database integrity check failed")
    violations = connection.execute("PRAGMA foreign_key_check").fetchall()
    if violations:
        tables = ", ".join(sorted({str(row[0]) for row in violations}))
        raise DatabaseIntegrityError(
            f"Database foreign-key check failed for table(s): {tables}"
        )


def _has_table(connection: sqlite3.Connection, table: str) -> bool:
    return (
        connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        is not None
    )


def _create_ledger(connection: sqlite3.Connection) -> None:
    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute(f"""CREATE TABLE IF NOT EXISTS {LEDGER_TABLE} (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            checksum TEXT NOT NULL,
            applied_at TEXT NOT NULL,
            duration_ms INTEGER NOT NULL,
            product_version TEXT NOT NULL
        )""")
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def ledger_entries(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    if not _has_table(connection, LEDGER_TABLE):
        return []
    return [
        dict(row)
        for row in connection.execute(f"SELECT * FROM {LEDGER_TABLE} ORDER BY version")
    ]


def _validate_ledger(
    entries: Sequence[dict[str, Any]], migrations: Sequence[Migration]
) -> None:
    if len(entries) > len(migrations):
        raise DatabaseCompatibilityError(
            "Database schema is newer than this Wright version"
        )
    for index, entry in enumerate(entries):
        migration = migrations[index]
        if int(entry["version"]) != migration.version:
            raise DatabaseCompatibilityError("Migration ledger contains a version gap")
        if entry["name"] != migration.name or entry["checksum"] != migration.checksum:
            raise DatabaseCompatibilityError(
                f"Migration checksum mismatch at version {migration.version}"
            )


def database_status(
    database_path: str | os.PathLike[str],
    migrations: Sequence[Migration] = MIGRATIONS,
) -> DatabaseStatus:
    validate_definitions(migrations)
    path = Path(database_path)
    if not path.exists():
        return DatabaseStatus(
            database=path.name,
            exists=False,
            integrity="ok",
            foreign_keys_ok=True,
            current_version=0,
            target_version=len(migrations),
            pending=tuple(m.version for m in migrations),
            ready=False,
            message="Database does not exist; initialization is pending",
        )
    try:
        with connect_state_db(path, read_only=True, wal=False) as connection:
            _integrity(connection)
            entries = ledger_entries(connection)
            _validate_ledger(entries, migrations)
    except DatabaseLifecycleError:
        raise
    except sqlite3.DatabaseError as exc:
        if "locked" in str(exc).lower() or "busy" in str(exc).lower():
            raise DatabaseBusyError("Database is busy") from exc
        raise DatabaseIntegrityError("Database cannot be inspected") from exc
    current = len(entries)
    pending = tuple(m.version for m in migrations[current:])
    return DatabaseStatus(
        database=path.name,
        exists=True,
        integrity="ok",
        foreign_keys_ok=True,
        current_version=current,
        target_version=len(migrations),
        pending=pending,
        ready=not pending,
        message="Database is ready" if not pending else "Database upgrade is pending",
    )


def upgrade_database(
    database_path: str | os.PathLike[str],
    *,
    migrations: Sequence[Migration] = MIGRATIONS,
    failure_hook: Callable[[Migration, sqlite3.Connection], None] | None = None,
    lock_timeout: float = 5.0,
    backup_dir: str | os.PathLike[str] | None = None,
) -> UpgradeResult:
    validate_definitions(migrations)
    path = Path(database_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DatabaseFilesystemError("Unable to create database directory") from exc
    with lifecycle_lock(path, timeout=lock_timeout):
        existed = path.exists()
        starting = database_status(path, migrations).current_version if existed else 0
        backup_manifest: str | None = None
        if existed and starting < len(migrations):
            from .backup import create_backup

            backup = create_backup(
                path,
                output_dir=backup_dir or path.parent / "backups",
                acquire_lock=False,
                migrations=migrations,
            )
            backup_manifest = backup.manifest_path
        applied: list[dict[str, Any]] = []
        try:
            with connect_state_db(path, ensure_parent=True) as connection:
                _integrity(connection)
                _create_ledger(connection)
                entries = ledger_entries(connection)
                _validate_ledger(entries, migrations)
                for migration in migrations[len(entries) :]:
                    started = time.monotonic()
                    connection.execute("BEGIN IMMEDIATE")
                    try:
                        for operation in migration.operations:
                            operation.apply(connection)
                        if failure_hook:
                            failure_hook(migration, connection)
                        duration = int((time.monotonic() - started) * 1000)
                        connection.execute(
                            f"INSERT INTO {LEDGER_TABLE} "
                            "(version, name, checksum, applied_at, duration_ms, product_version) "
                            "VALUES (?, ?, ?, ?, ?, ?)",
                            (
                                migration.version,
                                migration.name,
                                migration.checksum,
                                datetime.now(UTC).isoformat(),
                                duration,
                                PRODUCT_VERSION,
                            ),
                        )
                        connection.commit()
                    except Exception:
                        connection.rollback()
                        raise
                    applied.append(
                        {"version": migration.version, "name": migration.name}
                    )
                _integrity(connection)
        except DatabaseLifecycleError:
            raise
        except sqlite3.DatabaseError as exc:
            if "locked" in str(exc).lower() or "busy" in str(exc).lower():
                raise DatabaseBusyError("Database is busy") from exc
            raise DatabaseLifecycleError("Database migration failed") from exc
        final = database_status(path, migrations)
        if not final.ready:
            raise DatabaseLifecycleError("Database did not reach ready state")
        return UpgradeResult(
            database=path.name,
            starting_version=starting,
            ending_version=final.current_version,
            applied=tuple(applied),
            ready=True,
            backup_manifest=backup_manifest,
        )
