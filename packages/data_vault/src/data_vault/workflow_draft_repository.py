"""Atomic append-only persistence for provisional workflow drafts.

The repository owns a feature-specific SQLite sidecar beside Wright's primary
database. It never changes the primary database or its migration ledger.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Mapping

from pydantic import ValidationError

from core.workflow_drafts import WorkflowDraft, canonical_json_bytes

from .state_store import connect_state_db


_SIDECAR_NAME = "workflow-drafts.sqlite3"
_MAX_ENVELOPE_BYTES = 1024 * 1024


class WorkflowDraftRevisionConflict(RuntimeError):
    """The requested draft head was not the current persisted revision."""


class WorkflowDraftAlreadyExists(RuntimeError):
    """A draft already owns the requested stable identity."""


class WorkflowDraftStorageError(RuntimeError):
    """Draft persistence failed without exposing local or document details."""


class WorkflowDraftRepository:
    """Store immutable draft revisions and atomically advance their heads."""

    def __init__(self, primary_database_path: str | os.PathLike[str]) -> None:
        primary = Path(primary_database_path)
        self.db_path = primary.parent / _SIDECAR_NAME

    def create(self, draft: WorkflowDraft) -> None:
        if draft.revision != 1:
            raise ValueError("A new workflow draft must begin at revision 1")
        envelope = _bounded_envelope(draft)
        try:
            with connect_state_db(self.db_path, ensure_parent=True) as connection:
                self._ensure_schema(connection)
                connection.execute("BEGIN IMMEDIATE")
                if connection.execute(
                    "SELECT 1 FROM workflow_draft_heads WHERE draft_id = ?",
                    (draft.draft_id,),
                ).fetchone():
                    raise WorkflowDraftAlreadyExists(
                        "A workflow draft with that identity already exists"
                    )
                self._insert_revision(connection, draft, envelope)
                connection.execute(
                    """INSERT INTO workflow_draft_heads
                    (draft_id, current_revision, semantic_sha256, layout_sha256)
                    VALUES (?, ?, ?, ?)""",
                    (
                        draft.draft_id,
                        draft.revision,
                        draft.semantic_sha256,
                        draft.layout_sha256,
                    ),
                )
        except (WorkflowDraftAlreadyExists, WorkflowDraftStorageError):
            raise
        except sqlite3.DatabaseError as error:
            raise WorkflowDraftStorageError(
                "Workflow draft storage is unavailable or incompatible"
            ) from error

    def read(self, draft_id: str) -> WorkflowDraft | None:
        if not self.db_path.exists():
            return None
        try:
            with connect_state_db(
                self.db_path, read_only=True, wal=False
            ) as connection:
                row = connection.execute(
                    """SELECT r.envelope_json, r.semantic_sha256, r.layout_sha256,
                              h.current_revision AS revision,
                              h.semantic_sha256 AS head_semantic_sha256,
                              h.layout_sha256 AS head_layout_sha256
                    FROM workflow_draft_heads AS h
                    JOIN workflow_draft_revisions AS r
                      ON r.draft_id = h.draft_id
                     AND r.revision = h.current_revision
                    WHERE h.draft_id = ?""",
                    (draft_id,),
                ).fetchone()
            return _decode_revision(row)
        except (sqlite3.DatabaseError, ValidationError, ValueError) as error:
            raise WorkflowDraftStorageError(
                "Workflow draft storage is unavailable or incompatible"
            ) from error

    def read_revision(self, draft_id: str, revision: int) -> WorkflowDraft | None:
        if revision < 1:
            raise ValueError("Workflow draft revision must be positive")
        if not self.db_path.exists():
            return None
        try:
            with connect_state_db(
                self.db_path, read_only=True, wal=False
            ) as connection:
                row = connection.execute(
                    """SELECT envelope_json, semantic_sha256, layout_sha256, revision
                    FROM workflow_draft_revisions
                    WHERE draft_id = ? AND revision = ?""",
                    (draft_id, revision),
                ).fetchone()
            return _decode_revision(row)
        except (sqlite3.DatabaseError, ValidationError, ValueError) as error:
            raise WorkflowDraftStorageError(
                "Workflow draft storage is unavailable or incompatible"
            ) from error

    def save(self, draft: WorkflowDraft, *, expected_revision: int) -> None:
        if expected_revision < 1 or draft.revision != expected_revision + 1:
            raise ValueError(
                "A workflow draft save must provide the next consecutive revision"
            )
        envelope = _bounded_envelope(draft)
        try:
            with connect_state_db(self.db_path, ensure_parent=True) as connection:
                self._ensure_schema(connection)
                connection.execute("BEGIN IMMEDIATE")
                updated = connection.execute(
                    """UPDATE workflow_draft_heads
                    SET current_revision = ?, semantic_sha256 = ?, layout_sha256 = ?
                    WHERE draft_id = ? AND current_revision = ?""",
                    (
                        draft.revision,
                        draft.semantic_sha256,
                        draft.layout_sha256,
                        draft.draft_id,
                        expected_revision,
                    ),
                )
                if updated.rowcount != 1:
                    raise WorkflowDraftRevisionConflict(
                        "The workflow draft revision is no longer current"
                    )
                self._insert_revision(connection, draft, envelope)
        except WorkflowDraftRevisionConflict:
            raise
        except sqlite3.DatabaseError as error:
            raise WorkflowDraftStorageError(
                "Workflow draft storage is unavailable or incompatible"
            ) from error

    @staticmethod
    def _ensure_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS workflow_draft_revisions (
                draft_id TEXT NOT NULL,
                revision INTEGER NOT NULL CHECK(revision >= 1),
                semantic_sha256 TEXT NOT NULL CHECK(length(semantic_sha256) = 64),
                layout_sha256 TEXT NOT NULL CHECK(length(layout_sha256) = 64),
                envelope_json BLOB NOT NULL CHECK(length(envelope_json) <= 1048576),
                PRIMARY KEY (draft_id, revision)
            );
            CREATE TABLE IF NOT EXISTS workflow_draft_heads (
                draft_id TEXT PRIMARY KEY,
                current_revision INTEGER NOT NULL CHECK(current_revision >= 1),
                semantic_sha256 TEXT NOT NULL CHECK(length(semantic_sha256) = 64),
                layout_sha256 TEXT NOT NULL CHECK(length(layout_sha256) = 64)
            );
            CREATE TRIGGER IF NOT EXISTS workflow_draft_revisions_no_update
            BEFORE UPDATE ON workflow_draft_revisions
            BEGIN
                SELECT RAISE(ABORT, 'workflow draft revisions are immutable');
            END;
            CREATE TRIGGER IF NOT EXISTS workflow_draft_revisions_no_delete
            BEFORE DELETE ON workflow_draft_revisions
            BEGIN
                SELECT RAISE(ABORT, 'workflow draft revisions are append-only');
            END;
            """
        )

    @staticmethod
    def _insert_revision(
        connection: sqlite3.Connection,
        draft: WorkflowDraft,
        envelope: bytes,
    ) -> None:
        connection.execute(
            """INSERT INTO workflow_draft_revisions
            (draft_id, revision, semantic_sha256, layout_sha256, envelope_json)
            VALUES (?, ?, ?, ?, ?)""",
            (
                draft.draft_id,
                draft.revision,
                draft.semantic_sha256,
                draft.layout_sha256,
                envelope,
            ),
        )


def _bounded_envelope(draft: WorkflowDraft) -> bytes:
    envelope = canonical_json_bytes(draft)
    if len(envelope) > _MAX_ENVELOPE_BYTES:
        raise ValueError("Workflow draft envelope exceeds the 1 MiB limit")
    return envelope


def _decode_revision(row: Mapping[str, Any] | None) -> WorkflowDraft | None:
    if row is None:
        return None
    draft = WorkflowDraft.model_validate_json(bytes(row["envelope_json"]))
    if (
        draft.revision != row["revision"]
        or draft.semantic_sha256 != row["semantic_sha256"]
        or draft.layout_sha256 != row["layout_sha256"]
        or (
            "head_semantic_sha256" in row.keys()
            and draft.semantic_sha256 != row["head_semantic_sha256"]
        )
        or (
            "head_layout_sha256" in row.keys()
            and draft.layout_sha256 != row["head_layout_sha256"]
        )
    ):
        raise ValueError(
            "Persisted workflow draft identity does not match its envelope"
        )
    return draft


__all__ = [
    "WorkflowDraftAlreadyExists",
    "WorkflowDraftRepository",
    "WorkflowDraftRevisionConflict",
    "WorkflowDraftStorageError",
]
