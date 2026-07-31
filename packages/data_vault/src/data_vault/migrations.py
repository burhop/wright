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
    Migration(
        4,
        "gateway_audit",
        (
            sql("""CREATE TABLE IF NOT EXISTS gateway_audit_events (
                event_id TEXT PRIMARY KEY,
                occurred_at INTEGER NOT NULL,
                correlation_id TEXT NOT NULL,
                request_id TEXT,
                session_id TEXT NOT NULL,
                principal_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                operation TEXT NOT NULL,
                server_id TEXT,
                target_name TEXT,
                allowed INTEGER NOT NULL CHECK(allowed IN (0, 1)),
                reason_code TEXT NOT NULL,
                outcome TEXT NOT NULL,
                duration_ms INTEGER NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                FOREIGN KEY (workspace_id) REFERENCES engineering_workspaces(workspace_id) ON DELETE CASCADE
            )"""),
            sql(
                "CREATE INDEX IF NOT EXISTS idx_gateway_audit_session "
                "ON gateway_audit_events(session_id, occurred_at)"
            ),
        ),
    ),
    Migration(
        5,
        "provider_neutral_mcp_contract",
        (
            add_column("mcp_servers", "launch_env", "TEXT"),
            add_column("mcp_tools", "title", "TEXT"),
            add_column("mcp_tools", "output_schema", "TEXT"),
            add_column("mcp_tools", "annotations", "TEXT"),
        ),
    ),
    Migration(
        6,
        "workspace_surfaces",
        (
            sql("""CREATE TABLE IF NOT EXISTS workspace_surfaces (
                surface_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                schema_version INTEGER NOT NULL CHECK(schema_version = 1),
                source_kind TEXT NOT NULL CHECK(source_kind IN
                    ('file', 'display', 'live_app', 'mcp_app', 'external_url')),
                source_id TEXT NOT NULL,
                source_version TEXT NOT NULL,
                source_json TEXT NOT NULL,
                title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 256),
                lifecycle TEXT NOT NULL CHECK(lifecycle IN
                    ('declared', 'starting', 'ready', 'unhealthy', 'stopping', 'stopped', 'failed')),
                instance_json TEXT,
                presentations_json TEXT NOT NULL DEFAULT '[]',
                capabilities_json TEXT NOT NULL DEFAULT '[]',
                diagnostic_summary_json TEXT,
                generation_provenance_json TEXT,
                revision INTEGER NOT NULL CHECK(revision >= 1),
                idempotency_key TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (workspace_id) REFERENCES engineering_workspaces(workspace_id) ON DELETE CASCADE
            )"""),
            sql("""CREATE UNIQUE INDEX IF NOT EXISTS idx_workspace_surfaces_request
                ON workspace_surfaces(user_id, workspace_id, session_id, idempotency_key)
                WHERE idempotency_key IS NOT NULL"""),
            sql("""CREATE INDEX IF NOT EXISTS idx_workspace_surfaces_scope
                ON workspace_surfaces(workspace_id, user_id, session_id, updated_at)"""),
            sql("""CREATE TABLE IF NOT EXISTS surface_presentations (
                presentation_id TEXT PRIMARY KEY,
                instance_id TEXT NOT NULL,
                surface_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                kind TEXT NOT NULL CHECK(kind IN ('panel', 'browser')),
                state TEXT NOT NULL CHECK(state IN ('issued', 'active', 'inactive', 'closed', 'expired')),
                effective_origin TEXT NOT NULL,
                bootstrap_nonce_hash TEXT,
                cookie_audience TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_seen_at TEXT,
                expires_at TEXT NOT NULL,
                closed_at TEXT,
                FOREIGN KEY (surface_id) REFERENCES workspace_surfaces(surface_id) ON DELETE CASCADE,
                FOREIGN KEY (workspace_id) REFERENCES engineering_workspaces(workspace_id) ON DELETE CASCADE
            )"""),
            sql("""CREATE INDEX IF NOT EXISTS idx_surface_presentations_scope
                ON surface_presentations(workspace_id, user_id, surface_id, state)"""),
            sql("""CREATE TABLE IF NOT EXISTS surface_display_artifacts (
                artifact_id TEXT PRIMARY KEY,
                surface_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                display_id TEXT NOT NULL,
                revision INTEGER NOT NULL CHECK(revision >= 1),
                producer_execution_id TEXT NOT NULL,
                producer_task_id TEXT NOT NULL,
                representations_json TEXT NOT NULL,
                title TEXT,
                accessibility_description TEXT,
                dimensions_json TEXT,
                durability TEXT NOT NULL CHECK(durability IN ('durable', 'session', 'ephemeral')),
                current INTEGER NOT NULL DEFAULT 0 CHECK(current IN (0, 1)),
                idempotency_key TEXT NOT NULL,
                supersedes_artifact_id TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(workspace_id, producer_task_id, display_id, revision),
                UNIQUE(workspace_id, producer_execution_id, idempotency_key),
                FOREIGN KEY (surface_id) REFERENCES workspace_surfaces(surface_id) ON DELETE CASCADE,
                FOREIGN KEY (supersedes_artifact_id) REFERENCES surface_display_artifacts(artifact_id)
            )"""),
            sql("""CREATE UNIQUE INDEX IF NOT EXISTS idx_surface_display_current
                ON surface_display_artifacts(workspace_id, producer_task_id, display_id)
                WHERE current = 1"""),
            sql("""CREATE TABLE IF NOT EXISTS surface_generation_provenance (
                artifact_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                mode TEXT NOT NULL CHECK(mode IN ('agent_generated', 'direct_execution')),
                prompt_vault_digest TEXT,
                no_prompt INTEGER NOT NULL CHECK(no_prompt IN (0, 1)),
                constraints_vault_digest TEXT NOT NULL,
                script_vault_digest TEXT NOT NULL,
                script_content_hash TEXT NOT NULL,
                script_revision INTEGER NOT NULL CHECK(script_revision >= 1),
                task_id TEXT NOT NULL,
                execution_id TEXT NOT NULL,
                trace_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (artifact_id) REFERENCES surface_display_artifacts(artifact_id) ON DELETE CASCADE
            )"""),
            sql("""CREATE TABLE IF NOT EXISTS surface_runtimes (
                runtime_id TEXT PRIMARY KEY,
                instance_id TEXT NOT NULL UNIQUE,
                surface_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                generation INTEGER NOT NULL CHECK(generation >= 1),
                ownership TEXT NOT NULL CHECK(ownership IN ('launched', 'attached_verified', 'external')),
                platform TEXT NOT NULL CHECK(platform IN ('posix', 'windows_job', 'container', 'remote_adapter')),
                state TEXT NOT NULL,
                process_identity_json TEXT,
                manifest_hash TEXT,
                lifetime_json TEXT NOT NULL,
                limits_json TEXT NOT NULL,
                target_pin_json TEXT,
                revision INTEGER NOT NULL CHECK(revision >= 1),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (surface_id) REFERENCES workspace_surfaces(surface_id) ON DELETE CASCADE,
                FOREIGN KEY (workspace_id) REFERENCES engineering_workspaces(workspace_id) ON DELETE CASCADE
            )"""),
            sql("""CREATE INDEX IF NOT EXISTS idx_surface_runtimes_reconcile
                ON surface_runtimes(workspace_id, state, generation)"""),
            sql("""CREATE TABLE IF NOT EXISTS surface_preferences (
                user_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                source_id TEXT NOT NULL,
                source_version TEXT NOT NULL,
                preferred_kind TEXT NOT NULL CHECK(preferred_kind IN ('panel', 'browser')),
                revision INTEGER NOT NULL CHECK(revision >= 1),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (user_id, workspace_id, source_id),
                FOREIGN KEY (workspace_id) REFERENCES engineering_workspaces(workspace_id) ON DELETE CASCADE
            )"""),
            sql("""CREATE TABLE IF NOT EXISTS surface_capability_grants (
                grant_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                source_id TEXT NOT NULL,
                source_version TEXT NOT NULL,
                instance_id TEXT,
                capability TEXT NOT NULL,
                operation TEXT NOT NULL,
                constraints_json TEXT NOT NULL,
                risk_tier TEXT NOT NULL CHECK(risk_tier IN ('low', 'high', 'mutating')),
                persistence TEXT NOT NULL CHECK(persistence IN ('remembered_exact', 'instance', 'operation')),
                decision TEXT NOT NULL CHECK(decision IN ('allow', 'deny')),
                decision_source TEXT NOT NULL,
                expires_at TEXT,
                revoked_at TEXT,
                used_at TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (workspace_id) REFERENCES engineering_workspaces(workspace_id) ON DELETE CASCADE
            )"""),
            sql("""CREATE INDEX IF NOT EXISTS idx_surface_grants_scope
                ON surface_capability_grants(user_id, workspace_id, source_id, source_version, capability, operation)"""),
            sql("""CREATE TABLE IF NOT EXISTS surface_mcp_bindings (
                gateway_session_id TEXT NOT NULL,
                server_connection_id TEXT NOT NULL,
                upstream_resource_uri TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                media_type TEXT NOT NULL,
                visibility_json TEXT NOT NULL,
                tool_association_json TEXT,
                subscription_state TEXT,
                cache_expires_at TEXT,
                source_version TEXT NOT NULL,
                fallback_vault_digest TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (gateway_session_id, server_connection_id, upstream_resource_uri, content_hash),
                FOREIGN KEY (workspace_id) REFERENCES engineering_workspaces(workspace_id) ON DELETE CASCADE
            )"""),
            sql("""CREATE TABLE IF NOT EXISTS surface_diagnostic_events (
                event_id TEXT PRIMARY KEY,
                occurred_at TEXT NOT NULL,
                severity TEXT NOT NULL CHECK(severity IN ('debug', 'info', 'warning', 'error')),
                code TEXT NOT NULL,
                message TEXT NOT NULL,
                user_id TEXT,
                workspace_id TEXT NOT NULL,
                session_id TEXT,
                surface_id TEXT,
                instance_id TEXT,
                presentation_id TEXT,
                runtime_id TEXT,
                transition_json TEXT,
                attributes_json TEXT NOT NULL DEFAULT '{}',
                trace_id TEXT NOT NULL,
                span_id TEXT NOT NULL,
                correlation_id TEXT NOT NULL,
                retryable INTEGER NOT NULL CHECK(retryable IN (0, 1)),
                retention_class TEXT NOT NULL,
                FOREIGN KEY (workspace_id) REFERENCES engineering_workspaces(workspace_id) ON DELETE CASCADE
            )"""),
            sql("""CREATE INDEX IF NOT EXISTS idx_surface_diagnostics_scope
                ON surface_diagnostic_events(workspace_id, surface_id, occurred_at)"""),
            sql("""CREATE TABLE IF NOT EXISTS surface_outbox (
                event_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                aggregate_id TEXT NOT NULL,
                aggregate_revision INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                trace_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                published_at TEXT,
                attempts INTEGER NOT NULL DEFAULT 0,
                UNIQUE(aggregate_id, aggregate_revision, event_type),
                FOREIGN KEY (workspace_id) REFERENCES engineering_workspaces(workspace_id) ON DELETE CASCADE
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


def schema_bounds(
    migrations: Sequence[Migration] = MIGRATIONS,
) -> tuple[int, int]:
    """Return the inclusive schemas this runtime can initialize or open."""
    validate_definitions(migrations)
    return 0, len(migrations)


def require_schema_compatible(
    schema_version: int,
    *,
    minimum: int,
    maximum: int,
) -> None:
    if not minimum <= schema_version <= maximum:
        raise DatabaseCompatibilityError(
            f"Database schema {schema_version} is outside supported range "
            f"{minimum}..{maximum}"
        )


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
