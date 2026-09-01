"""Append-only persistence for promoted canonical workflow definitions.

Definitions use a sidecar that is independent from Wright's primary database,
legacy workflow drafts, future layout records, and future run records.
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from pydantic import ValidationError

from core.workflow_definitions import (
    WorkflowDefinition,
    WorkflowDraftPromotion,
    WorkflowRecoveryPromotion,
    canonical_definition_sha256,
    definition_envelope_bytes,
)
from core.workflow_drafts import WorkflowDraft

from .state_store import connect_state_db


_SIDECAR_NAME = "workflow-definitions.sqlite3"
_MAX_ENVELOPE_BYTES = 4 * 1024 * 1024


class WorkflowDefinitionRevisionConflict(RuntimeError):
    """The requested definition head is no longer current."""


class WorkflowDefinitionAlreadyExists(RuntimeError):
    """A definition already owns the stable workflow identity."""


class WorkflowDefinitionSchemaError(RuntimeError):
    """Definition persistence is incompatible or failed closed."""


@dataclass(frozen=True, slots=True)
class WorkflowDefinitionSchemaMigration:
    version: int
    name: str
    up_sql: tuple[str, ...]
    down_sql: tuple[str, ...]

    @property
    def checksum(self) -> str:
        material = "\n".join((self.name, *self.up_sql, "-- DOWN --", *self.down_sql))
        return hashlib.sha256(material.encode("utf-8")).hexdigest()


WORKFLOW_DEFINITION_MIGRATIONS = (
    WorkflowDefinitionSchemaMigration(
        version=1,
        name="canonical_workflow_definitions",
        up_sql=(
            """CREATE TABLE workflow_definition_revisions (
                workflow_id TEXT NOT NULL,
                revision INTEGER NOT NULL CHECK(revision >= 1),
                parent_revision INTEGER,
                semantic_sha256 TEXT NOT NULL CHECK(length(semantic_sha256) = 64),
                envelope_json BLOB NOT NULL CHECK(length(envelope_json) <= 4194304),
                source_document_kind TEXT,
                source_schema_version TEXT,
                source_envelope_json BLOB,
                source_envelope_sha256 TEXT,
                PRIMARY KEY (workflow_id, revision),
                CHECK(parent_revision IS NULL OR parent_revision >= 1),
                CHECK(
                    (source_envelope_json IS NULL AND source_envelope_sha256 IS NULL
                     AND source_document_kind IS NULL AND source_schema_version IS NULL)
                    OR
                    (source_envelope_json IS NOT NULL AND length(source_envelope_sha256) = 64
                     AND source_document_kind IS NOT NULL AND source_schema_version IS NOT NULL)
                )
            )""",
            """CREATE TABLE workflow_definition_heads (
                workflow_id TEXT PRIMARY KEY,
                current_revision INTEGER NOT NULL CHECK(current_revision >= 1),
                semantic_sha256 TEXT NOT NULL CHECK(length(semantic_sha256) = 64)
            )""",
            """CREATE TRIGGER workflow_definition_revisions_no_update
            BEFORE UPDATE ON workflow_definition_revisions
            BEGIN
                SELECT RAISE(ABORT, 'workflow definition revisions are immutable');
            END""",
            """CREATE TRIGGER workflow_definition_revisions_no_delete
            BEFORE DELETE ON workflow_definition_revisions
            BEGIN
                SELECT RAISE(ABORT, 'workflow definition revisions are immutable');
            END""",
        ),
        down_sql=(
            "DROP TRIGGER IF EXISTS workflow_definition_revisions_no_delete",
            "DROP TRIGGER IF EXISTS workflow_definition_revisions_no_update",
            "DROP TABLE IF EXISTS workflow_definition_heads",
            "DROP TABLE IF EXISTS workflow_definition_revisions",
        ),
    ),
)


def _ensure_ledger(connection: sqlite3.Connection) -> None:
    connection.execute(
        """CREATE TABLE IF NOT EXISTS workflow_definition_schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            checksum TEXT NOT NULL CHECK(length(checksum) = 64)
        )"""
    )


def _migration_rows(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    return connection.execute(
        """SELECT version, name, checksum
        FROM workflow_definition_schema_migrations ORDER BY version"""
    ).fetchall()


def _validate_migration_ledger(connection: sqlite3.Connection) -> int:
    rows = _migration_rows(connection)
    if len(rows) > len(WORKFLOW_DEFINITION_MIGRATIONS):
        raise WorkflowDefinitionSchemaError(
            "Workflow definition schema is newer than this runtime"
        )
    for index, row in enumerate(rows):
        migration = WORKFLOW_DEFINITION_MIGRATIONS[index]
        version, name, checksum = row[0], row[1], row[2]
        if (
            version != migration.version
            or name != migration.name
            or checksum != migration.checksum
        ):
            raise WorkflowDefinitionSchemaError(
                "Workflow definition migration ledger does not match this runtime"
            )
    return len(rows)


def upgrade_workflow_definition_schema(connection: sqlite3.Connection) -> int:
    """Apply missing sidecar migrations atomically and return current version."""

    connection.execute("BEGIN IMMEDIATE")
    try:
        _ensure_ledger(connection)
        current = _validate_migration_ledger(connection)
        for migration in WORKFLOW_DEFINITION_MIGRATIONS[current:]:
            for statement in migration.up_sql:
                connection.execute(statement)
            connection.execute(
                """INSERT INTO workflow_definition_schema_migrations
                (version, name, checksum) VALUES (?, ?, ?)""",
                (migration.version, migration.name, migration.checksum),
            )
        connection.commit()
        return len(WORKFLOW_DEFINITION_MIGRATIONS)
    except (sqlite3.DatabaseError, WorkflowDefinitionSchemaError) as error:
        connection.rollback()
        if isinstance(error, WorkflowDefinitionSchemaError):
            raise
        raise WorkflowDefinitionSchemaError(
            "Workflow definition schema upgrade failed and was rolled back"
        ) from error


def rollback_workflow_definition_schema(
    connection: sqlite3.Connection, *, target_version: int
) -> int:
    """Roll back only an empty sidecar; populated definition history is immutable."""

    if target_version not in {0, len(WORKFLOW_DEFINITION_MIGRATIONS)}:
        raise ValueError("Unsupported workflow definition schema rollback target")
    connection.execute("BEGIN IMMEDIATE")
    try:
        _ensure_ledger(connection)
        current = _validate_migration_ledger(connection)
        if target_version == current:
            connection.commit()
            return current
        if target_version > current:
            raise WorkflowDefinitionSchemaError(
                "Use schema upgrade rather than rollback for a newer target"
            )
        if (
            current
            and connection.execute(
                "SELECT 1 FROM workflow_definition_revisions LIMIT 1"
            ).fetchone()
        ):
            raise WorkflowDefinitionSchemaError(
                "Workflow definition schema contains definitions; exact envelope rollback must be used"
            )
        for migration in reversed(
            WORKFLOW_DEFINITION_MIGRATIONS[target_version:current]
        ):
            for statement in migration.down_sql:
                connection.execute(statement)
            connection.execute(
                "DELETE FROM workflow_definition_schema_migrations WHERE version = ?",
                (migration.version,),
            )
        if target_version == 0:
            connection.execute("DROP TABLE workflow_definition_schema_migrations")
        connection.commit()
        return target_version
    except (sqlite3.DatabaseError, WorkflowDefinitionSchemaError) as error:
        connection.rollback()
        if isinstance(error, WorkflowDefinitionSchemaError):
            raise
        raise WorkflowDefinitionSchemaError(
            "Workflow definition schema rollback failed without changing stored data"
        ) from error


class WorkflowDefinitionRepository:
    """Store immutable canonical definitions and compare-and-set their heads."""

    def __init__(self, primary_database_path: str | os.PathLike[str]) -> None:
        primary = Path(primary_database_path)
        self.db_path = primary.parent / _SIDECAR_NAME

    def create(self, definition: WorkflowDefinition) -> None:
        if definition.revision != 1 or definition.parent_revision is not None:
            raise ValueError("A new workflow definition must begin at revision 1")
        self._create(
            definition,
            source_kind=None,
            source_version=None,
            source_envelope=None,
            source_sha256=None,
        )

    def create_from_promotion(self, promotion: WorkflowDraftPromotion) -> None:
        self._create(
            promotion.definition,
            source_kind="workflow-draft",
            source_version="1.0.0-draft.1",
            source_envelope=promotion.source_envelope,
            source_sha256=promotion.source_envelope_sha256,
        )

    def create_from_recovery_promotion(
        self, promotion: WorkflowRecoveryPromotion
    ) -> None:
        self._create(
            promotion.definition,
            source_kind="workflow-ir",
            source_version="2.0.0-recovery.1",
            source_envelope=promotion.source_envelope,
            source_sha256=promotion.source_envelope_sha256,
        )

    def _create(
        self,
        definition: WorkflowDefinition,
        *,
        source_kind: str | None,
        source_version: str | None,
        source_envelope: bytes | None,
        source_sha256: str | None,
    ) -> None:
        envelope, digest = _bounded_definition(definition)
        try:
            with connect_state_db(self.db_path, ensure_parent=True) as connection:
                upgrade_workflow_definition_schema(connection)
                connection.execute("BEGIN IMMEDIATE")
                if connection.execute(
                    "SELECT 1 FROM workflow_definition_heads WHERE workflow_id = ?",
                    (definition.workflow_id,),
                ).fetchone():
                    raise WorkflowDefinitionAlreadyExists(
                        "A workflow definition with that identity already exists"
                    )
                self._insert_revision(
                    connection,
                    definition,
                    envelope,
                    source_kind=source_kind,
                    source_version=source_version,
                    source_envelope=source_envelope,
                    source_sha256=source_sha256,
                )
                connection.execute(
                    """INSERT INTO workflow_definition_heads
                    (workflow_id, current_revision, semantic_sha256)
                    VALUES (?, ?, ?)""",
                    (definition.workflow_id, definition.revision, digest),
                )
        except (WorkflowDefinitionAlreadyExists, WorkflowDefinitionSchemaError):
            raise
        except sqlite3.DatabaseError as error:
            raise WorkflowDefinitionSchemaError(
                "Workflow definition storage is unavailable or incompatible"
            ) from error

    def read(self, workflow_id: str) -> WorkflowDefinition | None:
        if not self.db_path.exists():
            return None
        try:
            with connect_state_db(
                self.db_path, read_only=True, wal=False
            ) as connection:
                row = connection.execute(
                    """SELECT r.envelope_json, r.semantic_sha256, r.revision,
                              r.parent_revision,
                              h.semantic_sha256 AS head_semantic_sha256,
                              h.current_revision AS head_revision
                    FROM workflow_definition_heads AS h
                    JOIN workflow_definition_revisions AS r
                      ON r.workflow_id = h.workflow_id
                     AND r.revision = h.current_revision
                    WHERE h.workflow_id = ?""",
                    (workflow_id,),
                ).fetchone()
            return _decode_definition(row)
        except (sqlite3.DatabaseError, ValidationError, ValueError) as error:
            raise WorkflowDefinitionSchemaError(
                "Workflow definition storage is unavailable or incompatible"
            ) from error

    def read_revision(
        self, workflow_id: str, revision: int
    ) -> WorkflowDefinition | None:
        if revision < 1:
            raise ValueError("Workflow definition revision must be positive")
        if not self.db_path.exists():
            return None
        try:
            with connect_state_db(
                self.db_path, read_only=True, wal=False
            ) as connection:
                row = connection.execute(
                    """SELECT envelope_json, semantic_sha256, revision, parent_revision
                    FROM workflow_definition_revisions
                    WHERE workflow_id = ? AND revision = ?""",
                    (workflow_id, revision),
                ).fetchone()
            return _decode_definition(row)
        except (sqlite3.DatabaseError, ValidationError, ValueError) as error:
            raise WorkflowDefinitionSchemaError(
                "Workflow definition storage is unavailable or incompatible"
            ) from error

    def read_legacy_rollback(
        self, workflow_id: str, revision: int
    ) -> WorkflowDraft | None:
        envelope = self._read_source_rollback(
            workflow_id,
            revision,
            expected_kind="workflow-draft",
            expected_version="1.0.0-draft.1",
        )
        if envelope is None:
            return None
        try:
            return WorkflowDraft.model_validate_json(envelope)
        except ValidationError as error:
            raise WorkflowDefinitionSchemaError(
                "Workflow definition rollback envelope is unavailable or incompatible"
            ) from error

    def read_recovery_rollback(self, workflow_id: str, revision: int) -> bytes | None:
        """Return the exact approved recovery wire retained at promotion."""

        return self._read_source_rollback(
            workflow_id,
            revision,
            expected_kind="workflow-ir",
            expected_version="2.0.0-recovery.1",
        )

    def _read_source_rollback(
        self,
        workflow_id: str,
        revision: int,
        *,
        expected_kind: str,
        expected_version: str,
    ) -> bytes | None:
        if revision < 1:
            raise ValueError("Workflow definition revision must be positive")
        if not self.db_path.exists():
            return None
        try:
            with connect_state_db(
                self.db_path, read_only=True, wal=False
            ) as connection:
                row = connection.execute(
                    """SELECT source_document_kind, source_schema_version,
                              source_envelope_json, source_envelope_sha256
                    FROM workflow_definition_revisions
                    WHERE workflow_id = ? AND revision = ?""",
                    (workflow_id, revision),
                ).fetchone()
            if row is None or row["source_envelope_json"] is None:
                return None
            if row["source_document_kind"] != expected_kind or (
                row["source_schema_version"] != expected_version
            ):
                return None
            envelope = bytes(row["source_envelope_json"])
            if hashlib.sha256(envelope).hexdigest() != row["source_envelope_sha256"]:
                raise ValueError("Source rollback envelope digest mismatch")
            return envelope
        except (sqlite3.DatabaseError, ValueError) as error:
            raise WorkflowDefinitionSchemaError(
                "Workflow definition rollback envelope is unavailable or incompatible"
            ) from error

    def save(self, definition: WorkflowDefinition, *, expected_revision: int) -> None:
        if (
            expected_revision < 1
            or definition.revision != expected_revision + 1
            or definition.parent_revision != expected_revision
        ):
            raise ValueError(
                "A workflow definition save must provide the next child revision"
            )
        envelope, digest = _bounded_definition(definition)
        try:
            with connect_state_db(self.db_path, ensure_parent=True) as connection:
                upgrade_workflow_definition_schema(connection)
                connection.execute("BEGIN IMMEDIATE")
                updated = connection.execute(
                    """UPDATE workflow_definition_heads
                    SET current_revision = ?, semantic_sha256 = ?
                    WHERE workflow_id = ? AND current_revision = ?""",
                    (
                        definition.revision,
                        digest,
                        definition.workflow_id,
                        expected_revision,
                    ),
                )
                if updated.rowcount != 1:
                    raise WorkflowDefinitionRevisionConflict(
                        "The workflow definition revision is no longer current"
                    )
                self._insert_revision(
                    connection,
                    definition,
                    envelope,
                    source_kind=None,
                    source_version=None,
                    source_envelope=None,
                    source_sha256=None,
                )
        except WorkflowDefinitionRevisionConflict:
            raise
        except WorkflowDefinitionSchemaError:
            raise
        except sqlite3.DatabaseError as error:
            raise WorkflowDefinitionSchemaError(
                "Workflow definition storage is unavailable or incompatible"
            ) from error

    @staticmethod
    def _insert_revision(
        connection: sqlite3.Connection,
        definition: WorkflowDefinition,
        envelope: bytes,
        *,
        source_kind: str | None,
        source_version: str | None,
        source_envelope: bytes | None,
        source_sha256: str | None,
    ) -> None:
        connection.execute(
            """INSERT INTO workflow_definition_revisions
            (workflow_id, revision, parent_revision, semantic_sha256,
             envelope_json, source_document_kind, source_schema_version,
             source_envelope_json, source_envelope_sha256)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                definition.workflow_id,
                definition.revision,
                definition.parent_revision,
                definition.semantic_sha256,
                envelope,
                source_kind,
                source_version,
                source_envelope,
                source_sha256,
            ),
        )


def _bounded_definition(definition: WorkflowDefinition) -> tuple[bytes, str]:
    digest = canonical_definition_sha256(definition)
    if definition.semantic_sha256 != digest:
        raise ValueError(
            "A persisted workflow definition requires its exact semantic digest"
        )
    envelope = definition_envelope_bytes(definition)
    if len(envelope) > _MAX_ENVELOPE_BYTES:
        raise ValueError("Workflow definition envelope exceeds the 4 MiB limit")
    return envelope, digest


def _decode_definition(row: Mapping[str, Any] | None) -> WorkflowDefinition | None:
    if row is None:
        return None
    definition = WorkflowDefinition.model_validate_json(bytes(row["envelope_json"]))
    digest = canonical_definition_sha256(definition)
    if (
        definition.revision != row["revision"]
        or definition.parent_revision != row["parent_revision"]
        or definition.semantic_sha256 != row["semantic_sha256"]
        or digest != row["semantic_sha256"]
        or (
            "head_revision" in row.keys()
            and definition.revision != row["head_revision"]
        )
        or (
            "head_semantic_sha256" in row.keys()
            and digest != row["head_semantic_sha256"]
        )
    ):
        raise ValueError(
            "Persisted workflow definition identity does not match its envelope"
        )
    return definition


__all__ = [
    "WORKFLOW_DEFINITION_MIGRATIONS",
    "WorkflowDefinitionAlreadyExists",
    "WorkflowDefinitionRepository",
    "WorkflowDefinitionRevisionConflict",
    "WorkflowDefinitionSchemaError",
    "rollback_workflow_definition_schema",
    "upgrade_workflow_definition_schema",
]
