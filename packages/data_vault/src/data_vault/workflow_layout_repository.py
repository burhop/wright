"""Append-only persistence and recoverable reopen for workflow layouts."""

from __future__ import annotations

import hashlib
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from core.workflow_definitions import WorkflowDefinition
from core.workflow_layouts import (
    WorkflowLayout,
    WorkflowLayoutDecodeResult,
    WorkflowLayoutPromotion,
    canonical_layout_sha256,
    decode_workflow_layout,
    layout_envelope_bytes,
    validate_workflow_layout_subject,
)

from .state_store import connect_state_db


_SIDECAR_NAME = "workflow-layouts.sqlite3"
_MAX_ENVELOPE_BYTES = 2 * 1024 * 1024


class WorkflowLayoutRevisionConflict(RuntimeError):
    """The requested layout head is no longer current."""


class WorkflowLayoutAlreadyExists(RuntimeError):
    """A layout already owns the stable workflow identity."""


class WorkflowLayoutSchemaError(RuntimeError):
    """Layout persistence is incompatible or failed closed."""


@dataclass(frozen=True, slots=True)
class WorkflowLayoutSchemaMigration:
    version: int
    name: str
    up_sql: tuple[str, ...]
    down_sql: tuple[str, ...]

    @property
    def checksum(self) -> str:
        material = "\n".join((self.name, *self.up_sql, "-- DOWN --", *self.down_sql))
        return hashlib.sha256(material.encode("utf-8")).hexdigest()


WORKFLOW_LAYOUT_MIGRATIONS = (
    WorkflowLayoutSchemaMigration(
        version=1,
        name="canonical_workflow_layouts",
        up_sql=(
            """CREATE TABLE workflow_layout_revisions (
                workflow_id TEXT NOT NULL,
                layout_revision INTEGER NOT NULL CHECK(layout_revision >= 1),
                parent_layout_revision INTEGER,
                semantic_revision INTEGER NOT NULL CHECK(semantic_revision >= 1),
                layout_sha256 TEXT NOT NULL CHECK(length(layout_sha256) = 64),
                envelope_json BLOB NOT NULL CHECK(length(envelope_json) <= 2097152),
                source_document_kind TEXT,
                source_schema_version TEXT,
                source_envelope_json BLOB,
                source_envelope_sha256 TEXT,
                PRIMARY KEY (workflow_id, layout_revision),
                CHECK(parent_layout_revision IS NULL OR parent_layout_revision >= 1),
                CHECK(
                    (source_envelope_json IS NULL AND source_envelope_sha256 IS NULL
                     AND source_document_kind IS NULL AND source_schema_version IS NULL)
                    OR
                    (source_envelope_json IS NOT NULL AND length(source_envelope_sha256) = 64
                     AND source_document_kind IS NOT NULL AND source_schema_version IS NOT NULL)
                )
            )""",
            """CREATE TABLE workflow_layout_heads (
                workflow_id TEXT PRIMARY KEY,
                current_layout_revision INTEGER NOT NULL CHECK(current_layout_revision >= 1),
                layout_sha256 TEXT NOT NULL CHECK(length(layout_sha256) = 64)
            )""",
            """CREATE TRIGGER workflow_layout_revisions_no_update
            BEFORE UPDATE ON workflow_layout_revisions
            BEGIN
                SELECT RAISE(ABORT, 'workflow layout revisions are immutable');
            END""",
            """CREATE TRIGGER workflow_layout_revisions_no_delete
            BEFORE DELETE ON workflow_layout_revisions
            BEGIN
                SELECT RAISE(ABORT, 'workflow layout revisions are immutable');
            END""",
        ),
        down_sql=(
            "DROP TRIGGER IF EXISTS workflow_layout_revisions_no_delete",
            "DROP TRIGGER IF EXISTS workflow_layout_revisions_no_update",
            "DROP TABLE IF EXISTS workflow_layout_heads",
            "DROP TABLE IF EXISTS workflow_layout_revisions",
        ),
    ),
)


def _ensure_ledger(connection: sqlite3.Connection) -> None:
    connection.execute(
        """CREATE TABLE IF NOT EXISTS workflow_layout_schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            checksum TEXT NOT NULL CHECK(length(checksum) = 64)
        )"""
    )


def _validate_migration_ledger(connection: sqlite3.Connection) -> int:
    rows = connection.execute(
        """SELECT version, name, checksum
        FROM workflow_layout_schema_migrations ORDER BY version"""
    ).fetchall()
    if len(rows) > len(WORKFLOW_LAYOUT_MIGRATIONS):
        raise WorkflowLayoutSchemaError(
            "Workflow layout schema is newer than this runtime"
        )
    for index, row in enumerate(rows):
        migration = WORKFLOW_LAYOUT_MIGRATIONS[index]
        if tuple(row) != (migration.version, migration.name, migration.checksum):
            raise WorkflowLayoutSchemaError(
                "Workflow layout migration ledger does not match this runtime"
            )
    return len(rows)


def upgrade_workflow_layout_schema(connection: sqlite3.Connection) -> int:
    connection.execute("BEGIN IMMEDIATE")
    try:
        _ensure_ledger(connection)
        current = _validate_migration_ledger(connection)
        for migration in WORKFLOW_LAYOUT_MIGRATIONS[current:]:
            for statement in migration.up_sql:
                connection.execute(statement)
            connection.execute(
                """INSERT INTO workflow_layout_schema_migrations
                (version, name, checksum) VALUES (?, ?, ?)""",
                (migration.version, migration.name, migration.checksum),
            )
        connection.commit()
        return len(WORKFLOW_LAYOUT_MIGRATIONS)
    except (sqlite3.DatabaseError, WorkflowLayoutSchemaError) as error:
        connection.rollback()
        if isinstance(error, WorkflowLayoutSchemaError):
            raise
        raise WorkflowLayoutSchemaError(
            "Workflow layout schema upgrade failed and was rolled back"
        ) from error


def rollback_workflow_layout_schema(
    connection: sqlite3.Connection, *, target_version: int
) -> int:
    if target_version not in {0, len(WORKFLOW_LAYOUT_MIGRATIONS)}:
        raise ValueError("Unsupported workflow layout schema rollback target")
    connection.execute("BEGIN IMMEDIATE")
    try:
        _ensure_ledger(connection)
        current = _validate_migration_ledger(connection)
        if target_version == current:
            connection.commit()
            return current
        if target_version > current:
            raise WorkflowLayoutSchemaError(
                "Use schema upgrade rather than rollback for a newer target"
            )
        if (
            current
            and connection.execute(
                "SELECT 1 FROM workflow_layout_revisions LIMIT 1"
            ).fetchone()
        ):
            raise WorkflowLayoutSchemaError(
                "Workflow layout schema contains layouts; exact envelope rollback must be used"
            )
        for migration in reversed(WORKFLOW_LAYOUT_MIGRATIONS[target_version:current]):
            for statement in migration.down_sql:
                connection.execute(statement)
            connection.execute(
                "DELETE FROM workflow_layout_schema_migrations WHERE version = ?",
                (migration.version,),
            )
        if target_version == 0:
            connection.execute("DROP TABLE workflow_layout_schema_migrations")
        connection.commit()
        return target_version
    except (sqlite3.DatabaseError, WorkflowLayoutSchemaError) as error:
        connection.rollback()
        if isinstance(error, WorkflowLayoutSchemaError):
            raise
        raise WorkflowLayoutSchemaError(
            "Workflow layout schema rollback failed without changing stored data"
        ) from error


class WorkflowLayoutRepository:
    def __init__(self, primary_database_path: str | os.PathLike[str]) -> None:
        primary = Path(primary_database_path)
        self.db_path = primary.parent / _SIDECAR_NAME

    def create(self, layout: WorkflowLayout, definition: WorkflowDefinition) -> None:
        if layout.layout_revision != 1:
            raise ValueError("A new workflow layout must begin at revision 1")
        validate_workflow_layout_subject(definition, layout)
        self._create(layout, source_envelope=None, source_sha256=None)

    def create_from_recovery_promotion(
        self, promotion: WorkflowLayoutPromotion
    ) -> None:
        if promotion.layout.layout_revision != 1:
            raise ValueError("A promoted workflow layout must begin at revision 1")
        if canonical_layout_sha256(promotion.layout) != promotion.layout_sha256:
            raise ValueError("Workflow layout promotion target digest mismatch")
        if hashlib.sha256(promotion.source_envelope).hexdigest() != (
            promotion.source_envelope_sha256
        ):
            raise ValueError("Workflow layout promotion source digest mismatch")
        if len(promotion.source_envelope) > _MAX_ENVELOPE_BYTES:
            raise ValueError("Workflow layout source envelope exceeds the 2 MiB limit")
        self._create(
            promotion.layout,
            source_envelope=promotion.source_envelope,
            source_sha256=promotion.source_envelope_sha256,
        )

    def _create(
        self,
        layout: WorkflowLayout,
        *,
        source_envelope: bytes | None,
        source_sha256: str | None,
    ) -> None:
        envelope, digest = _bounded_layout(layout)
        try:
            with connect_state_db(self.db_path, ensure_parent=True) as connection:
                upgrade_workflow_layout_schema(connection)
                connection.execute("BEGIN IMMEDIATE")
                if connection.execute(
                    "SELECT 1 FROM workflow_layout_heads WHERE workflow_id = ?",
                    (layout.workflow_id,),
                ).fetchone():
                    raise WorkflowLayoutAlreadyExists(
                        "A workflow layout with that identity already exists"
                    )
                self._insert_revision(
                    connection,
                    layout,
                    envelope,
                    parent_layout_revision=None,
                    source_envelope=source_envelope,
                    source_sha256=source_sha256,
                )
                connection.execute(
                    """INSERT INTO workflow_layout_heads
                    (workflow_id, current_layout_revision, layout_sha256)
                    VALUES (?, ?, ?)""",
                    (layout.workflow_id, layout.layout_revision, digest),
                )
        except (WorkflowLayoutAlreadyExists, WorkflowLayoutSchemaError):
            raise
        except sqlite3.DatabaseError as error:
            raise WorkflowLayoutSchemaError(
                "Workflow layout storage is unavailable or incompatible"
            ) from error

    def reopen(self, workflow_id: str) -> WorkflowLayoutDecodeResult:
        if not self.db_path.exists():
            return WorkflowLayoutDecodeResult(None, (), b"")
        try:
            with connect_state_db(
                self.db_path, read_only=True, wal=False
            ) as connection:
                row = connection.execute(
                    """SELECT r.workflow_id, r.layout_revision,
                              r.parent_layout_revision, r.semantic_revision,
                              r.layout_sha256, r.envelope_json,
                              h.current_layout_revision AS head_layout_revision,
                              h.layout_sha256 AS head_layout_sha256
                    FROM workflow_layout_heads AS h
                    JOIN workflow_layout_revisions AS r
                      ON r.workflow_id = h.workflow_id
                     AND r.layout_revision = h.current_layout_revision
                    WHERE h.workflow_id = ?""",
                    (workflow_id,),
                ).fetchone()
            if row is None:
                return WorkflowLayoutDecodeResult(None, (), b"")
            return _decode_row(row)
        except (sqlite3.DatabaseError, ValueError) as error:
            raise WorkflowLayoutSchemaError(
                "Workflow layout storage is unavailable or incompatible"
            ) from error

    def read(self, workflow_id: str) -> WorkflowLayout | None:
        result = self.reopen(workflow_id)
        if not result.original:
            return None
        if result.layout is None:
            raise WorkflowLayoutSchemaError(
                "Workflow layout version is unsupported; original bytes were preserved"
            )
        return result.layout

    def read_revision(
        self, workflow_id: str, layout_revision: int
    ) -> WorkflowLayout | None:
        if layout_revision < 1:
            raise ValueError("Workflow layout revision must be positive")
        if not self.db_path.exists():
            return None
        try:
            with connect_state_db(
                self.db_path, read_only=True, wal=False
            ) as connection:
                row = connection.execute(
                    """SELECT workflow_id, layout_revision,
                              parent_layout_revision, semantic_revision,
                              layout_sha256, envelope_json
                    FROM workflow_layout_revisions
                    WHERE workflow_id = ? AND layout_revision = ?""",
                    (workflow_id, layout_revision),
                ).fetchone()
            if row is None:
                return None
            result = _decode_row(row)
            if result.layout is None:
                raise WorkflowLayoutSchemaError(
                    "Workflow layout revision version is unsupported"
                )
            return result.layout
        except WorkflowLayoutSchemaError:
            raise
        except (sqlite3.DatabaseError, ValueError) as error:
            raise WorkflowLayoutSchemaError(
                "Workflow layout storage is unavailable or incompatible"
            ) from error

    def read_recovery_rollback(
        self, workflow_id: str, layout_revision: int
    ) -> bytes | None:
        if layout_revision < 1:
            raise ValueError("Workflow layout revision must be positive")
        if not self.db_path.exists():
            return None
        try:
            with connect_state_db(
                self.db_path, read_only=True, wal=False
            ) as connection:
                row = connection.execute(
                    """SELECT source_document_kind, source_schema_version,
                              source_envelope_json, source_envelope_sha256
                    FROM workflow_layout_revisions
                    WHERE workflow_id = ? AND layout_revision = ?""",
                    (workflow_id, layout_revision),
                ).fetchone()
            if row is None or row["source_envelope_json"] is None:
                return None
            if row["source_document_kind"] != "workflow-layout" or (
                row["source_schema_version"] != "1.0.0-recovery.1"
            ):
                return None
            envelope = bytes(row["source_envelope_json"])
            if hashlib.sha256(envelope).hexdigest() != row["source_envelope_sha256"]:
                raise ValueError("Recovery layout envelope digest mismatch")
            return envelope
        except (sqlite3.DatabaseError, ValueError) as error:
            raise WorkflowLayoutSchemaError(
                "Workflow layout rollback envelope is unavailable or incompatible"
            ) from error

    def save(
        self,
        layout: WorkflowLayout,
        definition: WorkflowDefinition,
        *,
        expected_layout_revision: int,
    ) -> None:
        if expected_layout_revision < 1 or (
            layout.layout_revision != expected_layout_revision + 1
        ):
            raise ValueError("A workflow layout save must provide the next revision")
        validate_workflow_layout_subject(definition, layout)
        envelope, digest = _bounded_layout(layout)
        try:
            with connect_state_db(self.db_path, ensure_parent=True) as connection:
                upgrade_workflow_layout_schema(connection)
                connection.execute("BEGIN IMMEDIATE")
                updated = connection.execute(
                    """UPDATE workflow_layout_heads
                    SET current_layout_revision = ?, layout_sha256 = ?
                    WHERE workflow_id = ? AND current_layout_revision = ?""",
                    (
                        layout.layout_revision,
                        digest,
                        layout.workflow_id,
                        expected_layout_revision,
                    ),
                )
                if updated.rowcount != 1:
                    raise WorkflowLayoutRevisionConflict(
                        "The workflow layout revision is no longer current"
                    )
                self._insert_revision(
                    connection,
                    layout,
                    envelope,
                    parent_layout_revision=expected_layout_revision,
                    source_envelope=None,
                    source_sha256=None,
                )
        except WorkflowLayoutRevisionConflict:
            raise
        except WorkflowLayoutSchemaError:
            raise
        except sqlite3.DatabaseError as error:
            raise WorkflowLayoutSchemaError(
                "Workflow layout storage is unavailable or incompatible"
            ) from error

    @staticmethod
    def _insert_revision(
        connection: sqlite3.Connection,
        layout: WorkflowLayout,
        envelope: bytes,
        *,
        parent_layout_revision: int | None,
        source_envelope: bytes | None,
        source_sha256: str | None,
    ) -> None:
        connection.execute(
            """INSERT INTO workflow_layout_revisions
            (workflow_id, layout_revision, parent_layout_revision,
             semantic_revision, layout_sha256, envelope_json,
             source_document_kind, source_schema_version,
             source_envelope_json, source_envelope_sha256)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                layout.workflow_id,
                layout.layout_revision,
                parent_layout_revision,
                layout.semantic_revision,
                canonical_layout_sha256(layout),
                envelope,
                "workflow-layout" if source_envelope is not None else None,
                "1.0.0-recovery.1" if source_envelope is not None else None,
                source_envelope,
                source_sha256,
            ),
        )


def _bounded_layout(layout: WorkflowLayout) -> tuple[bytes, str]:
    envelope = layout_envelope_bytes(layout)
    if len(envelope) > _MAX_ENVELOPE_BYTES:
        raise ValueError("Workflow layout envelope exceeds the 2 MiB limit")
    return envelope, hashlib.sha256(envelope).hexdigest()


def _decode_row(row: Mapping[str, Any]) -> WorkflowLayoutDecodeResult:
    envelope = bytes(row["envelope_json"])
    digest = hashlib.sha256(envelope).hexdigest()
    if (
        digest != row["layout_sha256"]
        or (
            "head_layout_revision" in row.keys()
            and row["layout_revision"] != row["head_layout_revision"]
        )
        or ("head_layout_sha256" in row.keys() and digest != row["head_layout_sha256"])
        or (
            "parent_layout_revision" in row.keys()
            and (
                (
                    row["layout_revision"] == 1
                    and row["parent_layout_revision"] is not None
                )
                or (
                    row["layout_revision"] > 1
                    and row["parent_layout_revision"] != row["layout_revision"] - 1
                )
            )
        )
    ):
        raise ValueError(
            "Persisted workflow layout identity does not match its envelope"
        )
    result = decode_workflow_layout(envelope)
    if result.layout is not None and (
        result.layout.workflow_id != row["workflow_id"]
        or result.layout.layout_revision != row["layout_revision"]
        or result.layout.semantic_revision != row["semantic_revision"]
        or canonical_layout_sha256(result.layout) != digest
    ):
        raise ValueError("Persisted workflow layout fields do not match its envelope")
    return result


__all__ = [
    "WORKFLOW_LAYOUT_MIGRATIONS",
    "WorkflowLayoutAlreadyExists",
    "WorkflowLayoutRepository",
    "WorkflowLayoutRevisionConflict",
    "WorkflowLayoutSchemaError",
    "rollback_workflow_layout_schema",
    "upgrade_workflow_layout_schema",
]
