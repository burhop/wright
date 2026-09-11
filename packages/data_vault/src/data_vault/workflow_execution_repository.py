"""Durable canonical workflow runs, activities, steps, artifacts, and cleanup."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from core.canonical_workflow_runs import (
    CanonicalWorkflowRun,
    RecoveryWorkflowRunEnvelope,
    WorkflowArtifactRecord,
    WorkflowRunActivity,
    WorkflowRunStepRecord,
    capture_recovery_workflow_run,
    validate_artifact_subject,
    validate_run_subject,
    validate_step_subject,
)
from core.workflow_definitions import WorkflowDefinition

from .state_store import connect_state_db


_SIDECAR_NAME = "workflow-runs.sqlite3"
_TERMINAL = {"cancelled", "succeeded", "failed", "blocked", "stale"}
_TRANSITIONS = {
    "idle": {"queued", "cancelled", "failed", "blocked"},
    "queued": {"running", "cancelled", "failed", "blocked"},
    "running": {"needs_input", "cancelling", "succeeded", "failed", "blocked", "stale"},
    "needs_input": {"running", "cancelling", "failed", "blocked", "stale"},
    "cancelling": {"cancelled", "failed"},
}


class WorkflowRunStateConflict(RuntimeError):
    """The durable run state no longer matches the caller's expectation."""


class WorkflowExecutionSchemaError(RuntimeError):
    """Canonical workflow execution storage failed closed."""


@dataclass(frozen=True, slots=True)
class WorkflowExecutionSchemaMigration:
    version: int
    name: str
    up_sql: tuple[str, ...]
    down_sql: tuple[str, ...]

    @property
    def checksum(self) -> str:
        material = "\n".join((self.name, *self.up_sql, "-- DOWN --", *self.down_sql))
        return hashlib.sha256(material.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class WorkflowRunReconnectSnapshot:
    run: CanonicalWorkflowRun
    steps: tuple[WorkflowRunStepRecord, ...]
    activities: tuple[WorkflowRunActivity, ...]
    artifacts: tuple[WorkflowArtifactRecord, ...]
    cursor: int


WORKFLOW_EXECUTION_MIGRATIONS = (
    WorkflowExecutionSchemaMigration(
        version=1,
        name="canonical_workflow_execution_records",
        up_sql=(
            """CREATE TABLE canonical_workflow_runs (
                run_id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                workflow_revision INTEGER NOT NULL CHECK(workflow_revision >= 1),
                semantic_sha256 TEXT NOT NULL CHECK(length(semantic_sha256) = 64),
                state TEXT NOT NULL,
                completed_at INTEGER,
                cleanup_state TEXT NOT NULL CHECK(cleanup_state IN ('retained', 'cleaned')),
                run_json BLOB NOT NULL CHECK(length(run_json) <= 2097152)
            )""",
            """CREATE TABLE canonical_workflow_run_activities (
                run_id TEXT NOT NULL,
                sequence INTEGER NOT NULL CHECK(sequence >= 1),
                occurred_at INTEGER NOT NULL,
                kind TEXT NOT NULL,
                activity_json BLOB NOT NULL CHECK(length(activity_json) <= 131072),
                PRIMARY KEY (run_id, sequence),
                FOREIGN KEY (run_id) REFERENCES canonical_workflow_runs(run_id)
                    ON DELETE RESTRICT
            )""",
            """CREATE TABLE canonical_workflow_run_steps (
                run_id TEXT NOT NULL,
                step_id TEXT NOT NULL,
                attempt INTEGER NOT NULL CHECK(attempt >= 1),
                block_id TEXT NOT NULL,
                step_json BLOB NOT NULL CHECK(length(step_json) <= 524288),
                PRIMARY KEY (run_id, step_id, attempt),
                FOREIGN KEY (run_id) REFERENCES canonical_workflow_runs(run_id)
                    ON DELETE RESTRICT
            )""",
            """CREATE TABLE canonical_workflow_artifacts (
                artifact_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                step_id TEXT NOT NULL,
                contract_id TEXT NOT NULL,
                digest_sha256 TEXT NOT NULL CHECK(length(digest_sha256) = 64),
                cleanup_state TEXT NOT NULL CHECK(cleanup_state IN ('retained', 'cleaned')),
                artifact_json BLOB NOT NULL CHECK(length(artifact_json) <= 524288),
                FOREIGN KEY (run_id) REFERENCES canonical_workflow_runs(run_id)
                    ON DELETE RESTRICT
            )""",
            """CREATE TABLE recovery_workflow_run_envelopes (
                run_id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                workflow_revision INTEGER NOT NULL CHECK(workflow_revision >= 1),
                semantic_sha256 TEXT NOT NULL CHECK(length(semantic_sha256) = 64),
                envelope_sha256 TEXT NOT NULL CHECK(length(envelope_sha256) = 64),
                envelope_json BLOB NOT NULL CHECK(length(envelope_json) <= 2097152)
            )""",
            """CREATE TRIGGER canonical_workflow_runs_identity_no_update
            BEFORE UPDATE ON canonical_workflow_runs
            WHEN OLD.run_id != NEW.run_id
              OR OLD.workflow_id != NEW.workflow_id
              OR OLD.workflow_revision != NEW.workflow_revision
              OR OLD.semantic_sha256 != NEW.semantic_sha256
            BEGIN
                SELECT RAISE(ABORT, 'canonical workflow run identity is immutable');
            END""",
            """CREATE TRIGGER canonical_workflow_runs_no_delete
            BEFORE DELETE ON canonical_workflow_runs
            BEGIN
                SELECT RAISE(ABORT, 'canonical workflow runs are immutable');
            END""",
            """CREATE TRIGGER canonical_workflow_activities_no_update
            BEFORE UPDATE ON canonical_workflow_run_activities
            BEGIN
                SELECT RAISE(ABORT, 'canonical workflow activities are immutable');
            END""",
            """CREATE TRIGGER canonical_workflow_activities_no_delete
            BEFORE DELETE ON canonical_workflow_run_activities
            BEGIN
                SELECT RAISE(ABORT, 'canonical workflow activities are immutable');
            END""",
            """CREATE TRIGGER canonical_workflow_steps_no_update
            BEFORE UPDATE ON canonical_workflow_run_steps
            BEGIN
                SELECT RAISE(ABORT, 'canonical workflow steps are immutable');
            END""",
            """CREATE TRIGGER canonical_workflow_steps_no_delete
            BEFORE DELETE ON canonical_workflow_run_steps
            BEGIN
                SELECT RAISE(ABORT, 'canonical workflow steps are immutable');
            END""",
            """CREATE TRIGGER canonical_workflow_artifacts_identity_no_update
            BEFORE UPDATE ON canonical_workflow_artifacts
            WHEN OLD.artifact_id != NEW.artifact_id
              OR OLD.run_id != NEW.run_id
              OR OLD.step_id != NEW.step_id
              OR OLD.contract_id != NEW.contract_id
              OR OLD.digest_sha256 != NEW.digest_sha256
            BEGIN
                SELECT RAISE(ABORT, 'canonical workflow artifact identity is immutable');
            END""",
            """CREATE TRIGGER canonical_workflow_artifacts_no_delete
            BEFORE DELETE ON canonical_workflow_artifacts
            BEGIN
                SELECT RAISE(ABORT, 'canonical workflow artifacts are immutable');
            END""",
            """CREATE TRIGGER recovery_workflow_run_envelopes_no_update
            BEFORE UPDATE ON recovery_workflow_run_envelopes
            BEGIN
                SELECT RAISE(ABORT, 'recovery workflow run envelopes are immutable');
            END""",
            """CREATE TRIGGER recovery_workflow_run_envelopes_no_delete
            BEFORE DELETE ON recovery_workflow_run_envelopes
            BEGIN
                SELECT RAISE(ABORT, 'recovery workflow run envelopes are immutable');
            END""",
        ),
        down_sql=(
            "DROP TRIGGER IF EXISTS recovery_workflow_run_envelopes_no_delete",
            "DROP TRIGGER IF EXISTS recovery_workflow_run_envelopes_no_update",
            "DROP TRIGGER IF EXISTS canonical_workflow_artifacts_no_delete",
            "DROP TRIGGER IF EXISTS canonical_workflow_artifacts_identity_no_update",
            "DROP TRIGGER IF EXISTS canonical_workflow_steps_no_delete",
            "DROP TRIGGER IF EXISTS canonical_workflow_steps_no_update",
            "DROP TRIGGER IF EXISTS canonical_workflow_activities_no_delete",
            "DROP TRIGGER IF EXISTS canonical_workflow_activities_no_update",
            "DROP TRIGGER IF EXISTS canonical_workflow_runs_no_delete",
            "DROP TRIGGER IF EXISTS canonical_workflow_runs_identity_no_update",
            "DROP TABLE IF EXISTS recovery_workflow_run_envelopes",
            "DROP TABLE IF EXISTS canonical_workflow_artifacts",
            "DROP TABLE IF EXISTS canonical_workflow_run_steps",
            "DROP TABLE IF EXISTS canonical_workflow_run_activities",
            "DROP TABLE IF EXISTS canonical_workflow_runs",
        ),
    ),
)


def _json_bytes(value) -> bytes:
    return json.dumps(
        value.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _ensure_ledger(connection: sqlite3.Connection) -> None:
    connection.execute(
        """CREATE TABLE IF NOT EXISTS workflow_execution_schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            checksum TEXT NOT NULL CHECK(length(checksum) = 64)
        )"""
    )


def _validate_ledger(connection: sqlite3.Connection) -> int:
    rows = connection.execute(
        """SELECT version, name, checksum
        FROM workflow_execution_schema_migrations ORDER BY version"""
    ).fetchall()
    if len(rows) > len(WORKFLOW_EXECUTION_MIGRATIONS):
        raise WorkflowExecutionSchemaError(
            "Workflow execution schema is newer than this runtime"
        )
    for index, row in enumerate(rows):
        migration = WORKFLOW_EXECUTION_MIGRATIONS[index]
        if tuple(row) != (migration.version, migration.name, migration.checksum):
            raise WorkflowExecutionSchemaError(
                "Workflow execution migration ledger does not match this runtime"
            )
    return len(rows)


def upgrade_workflow_execution_schema(connection: sqlite3.Connection) -> int:
    connection.execute("BEGIN IMMEDIATE")
    try:
        _ensure_ledger(connection)
        current = _validate_ledger(connection)
        for migration in WORKFLOW_EXECUTION_MIGRATIONS[current:]:
            for statement in migration.up_sql:
                connection.execute(statement)
            connection.execute(
                """INSERT INTO workflow_execution_schema_migrations
                (version, name, checksum) VALUES (?, ?, ?)""",
                (migration.version, migration.name, migration.checksum),
            )
        connection.commit()
        return len(WORKFLOW_EXECUTION_MIGRATIONS)
    except (sqlite3.DatabaseError, WorkflowExecutionSchemaError) as error:
        connection.rollback()
        if isinstance(error, WorkflowExecutionSchemaError):
            raise
        raise WorkflowExecutionSchemaError(
            "Workflow execution schema upgrade failed and was rolled back"
        ) from error


def rollback_workflow_execution_schema(
    connection: sqlite3.Connection, *, target_version: int
) -> int:
    if target_version not in {0, len(WORKFLOW_EXECUTION_MIGRATIONS)}:
        raise ValueError("Unsupported workflow execution schema rollback target")
    connection.execute("BEGIN IMMEDIATE")
    try:
        _ensure_ledger(connection)
        current = _validate_ledger(connection)
        if target_version == current:
            connection.commit()
            return current
        if target_version > current:
            raise WorkflowExecutionSchemaError(
                "Use schema upgrade rather than rollback for a newer target"
            )
        if (
            current
            and connection.execute(
                """SELECT 1 FROM canonical_workflow_runs
                UNION ALL SELECT 1 FROM recovery_workflow_run_envelopes
                LIMIT 1"""
            ).fetchone()
        ):
            raise WorkflowExecutionSchemaError(
                "Workflow execution schema contains runs and cannot be destructively rolled back"
            )
        for migration in reversed(
            WORKFLOW_EXECUTION_MIGRATIONS[target_version:current]
        ):
            for statement in migration.down_sql:
                connection.execute(statement)
            connection.execute(
                "DELETE FROM workflow_execution_schema_migrations WHERE version = ?",
                (migration.version,),
            )
        if target_version == 0:
            connection.execute("DROP TABLE workflow_execution_schema_migrations")
        connection.commit()
        return target_version
    except (sqlite3.DatabaseError, WorkflowExecutionSchemaError) as error:
        connection.rollback()
        if isinstance(error, WorkflowExecutionSchemaError):
            raise
        raise WorkflowExecutionSchemaError(
            "Workflow execution schema rollback failed without changing records"
        ) from error


class CanonicalWorkflowRunRepository:
    def __init__(self, primary_database_path: str | os.PathLike[str]) -> None:
        primary = Path(primary_database_path)
        self.db_path = primary.parent / _SIDECAR_NAME

    def create(self, run: CanonicalWorkflowRun, definition: WorkflowDefinition) -> None:
        validate_run_subject(definition, run)
        envelope = _json_bytes(run)
        try:
            with connect_state_db(self.db_path, ensure_parent=True) as connection:
                upgrade_workflow_execution_schema(connection)
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    """INSERT INTO canonical_workflow_runs
                    (run_id, workflow_id, workflow_revision, semantic_sha256,
                     state, completed_at, cleanup_state, run_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        run.run_id,
                        run.workflow_id,
                        run.workflow_revision,
                        run.semantic_sha256,
                        run.state,
                        run.completed_at,
                        run.cleanup_state,
                        envelope,
                    ),
                )
        except sqlite3.DatabaseError as error:
            raise WorkflowExecutionSchemaError(
                "Workflow run creation failed without changing durable history"
            ) from error

    def archive_recovery_run(self, original: bytes) -> RecoveryWorkflowRunEnvelope:
        captured = capture_recovery_workflow_run(original)
        if len(original) > 2 * 1024 * 1024:
            raise ValueError("Recovery workflow run envelope exceeds the 2 MiB limit")
        try:
            with connect_state_db(self.db_path, ensure_parent=True) as connection:
                upgrade_workflow_execution_schema(connection)
                connection.execute(
                    """INSERT INTO recovery_workflow_run_envelopes
                    (run_id, workflow_id, workflow_revision, semantic_sha256,
                     envelope_sha256, envelope_json)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        captured.run_id,
                        captured.workflow_id,
                        captured.workflow_revision,
                        captured.semantic_sha256,
                        captured.envelope_sha256,
                        captured.original,
                    ),
                )
            return captured
        except sqlite3.DatabaseError as error:
            raise WorkflowExecutionSchemaError(
                "Recovery workflow run envelope could not be archived"
            ) from error

    def read_recovery_run(self, run_id: str) -> bytes | None:
        if not self.db_path.exists():
            return None
        try:
            with connect_state_db(
                self.db_path, read_only=True, wal=False
            ) as connection:
                row = connection.execute(
                    """SELECT * FROM recovery_workflow_run_envelopes
                    WHERE run_id = ?""",
                    (run_id,),
                ).fetchone()
            if row is None:
                return None
            original = bytes(row["envelope_json"])
            captured = capture_recovery_workflow_run(original)
            if (
                captured.run_id != row["run_id"]
                or captured.workflow_id != row["workflow_id"]
                or captured.workflow_revision != row["workflow_revision"]
                or captured.semantic_sha256 != row["semantic_sha256"]
                or captured.envelope_sha256 != row["envelope_sha256"]
            ):
                raise ValueError(
                    "Persisted recovery workflow run identity does not match its envelope"
                )
            return original
        except (sqlite3.DatabaseError, ValueError) as error:
            raise WorkflowExecutionSchemaError(
                "Recovery workflow run envelope is unavailable or incompatible"
            ) from error

    def get(self, run_id: str) -> CanonicalWorkflowRun | None:
        if not self.db_path.exists():
            return None
        try:
            with connect_state_db(
                self.db_path, read_only=True, wal=False
            ) as connection:
                row = connection.execute(
                    "SELECT * FROM canonical_workflow_runs WHERE run_id = ?",
                    (run_id,),
                ).fetchone()
            return _decode_run(row)
        except (sqlite3.DatabaseError, ValueError) as error:
            raise WorkflowExecutionSchemaError(
                "Workflow run storage is unavailable or incompatible"
            ) from error

    def append_activity(self, activity: WorkflowRunActivity) -> None:
        try:
            with connect_state_db(self.db_path, ensure_parent=True) as connection:
                connection.execute("BEGIN IMMEDIATE")
                self._append_activity(connection, activity)
        except sqlite3.IntegrityError as error:
            raise WorkflowExecutionSchemaError(
                "Workflow run activity could not be appended"
            ) from error

    def _append_activity(
        self, connection: sqlite3.Connection, activity: WorkflowRunActivity
    ) -> None:
        if not connection.execute(
            "SELECT 1 FROM canonical_workflow_runs WHERE run_id = ?",
            (activity.run_id,),
        ).fetchone():
            raise KeyError(activity.run_id)
        latest = connection.execute(
            """SELECT MAX(sequence) FROM canonical_workflow_run_activities
            WHERE run_id = ?""",
            (activity.run_id,),
        ).fetchone()[0]
        expected = 1 if latest is None else int(latest) + 1
        if activity.sequence != expected:
            raise ValueError("Workflow run activity sequence is not contiguous")
        connection.execute(
            """INSERT INTO canonical_workflow_run_activities
            (run_id, sequence, occurred_at, kind, activity_json)
            VALUES (?, ?, ?, ?, ?)""",
            (
                activity.run_id,
                activity.sequence,
                activity.occurred_at,
                activity.kind,
                _json_bytes(activity),
            ),
        )

    @staticmethod
    def _next_sequence(connection: sqlite3.Connection, run_id: str) -> int:
        latest = connection.execute(
            """SELECT MAX(sequence) FROM canonical_workflow_run_activities
            WHERE run_id = ?""",
            (run_id,),
        ).fetchone()[0]
        return 1 if latest is None else int(latest) + 1

    def transition(
        self,
        run_id: str,
        state: str,
        *,
        expected_state: str,
        at: int,
    ) -> CanonicalWorkflowRun:
        kind = (
            "terminal"
            if state in _TERMINAL
            else "needs_input"
            if state == "needs_input"
            else (
                "resumed"
                if expected_state == "needs_input" and state == "running"
                else "progress"
            )
        )
        return self._transition(
            run_id,
            state,
            expected_state=expected_state,
            at=at,
            activity_kind=kind,
        )

    def transition_projection(
        self,
        candidate: CanonicalWorkflowRun,
        definition: WorkflowDefinition,
        *,
        expected_state: str,
        at: int,
    ) -> CanonicalWorkflowRun:
        """Atomically accept a complete state/projection candidate and activity."""

        validate_run_subject(definition, candidate)
        kind = (
            "terminal"
            if candidate.state in _TERMINAL
            else "needs_input"
            if candidate.state == "needs_input"
            else "resumed"
            if expected_state == "needs_input" and candidate.state == "running"
            else "progress"
        )
        return self._transition(
            candidate.run_id,
            candidate.state,
            expected_state=expected_state,
            at=at,
            activity_kind=kind,
            candidate=candidate,
            definition=definition,
        )

    def _transition(
        self,
        run_id: str,
        state: str,
        *,
        expected_state: str,
        at: int,
        activity_kind: str | tuple[str, ...],
        candidate: CanonicalWorkflowRun | None = None,
        definition: WorkflowDefinition | None = None,
    ) -> CanonicalWorkflowRun:
        if state not in _TRANSITIONS.get(expected_state, set()):
            raise WorkflowRunStateConflict(
                f"Invalid workflow run transition {expected_state} -> {state}"
            )
        try:
            with connect_state_db(self.db_path, ensure_parent=True) as connection:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    "SELECT * FROM canonical_workflow_runs WHERE run_id = ?",
                    (run_id,),
                ).fetchone()
                current = _decode_run(row)
                if current is None:
                    raise KeyError(run_id)
                if current.state != expected_state:
                    raise WorkflowRunStateConflict(
                        "The workflow run state no longer matches the expected state"
                    )
                if candidate is not None:
                    immutable = (
                        "run_id",
                        "workflow_id",
                        "workflow_revision",
                        "semantic_sha256",
                        "created_at",
                        "mode",
                        "cleanup_state",
                    )
                    if any(
                        getattr(candidate, field) != getattr(current, field)
                        for field in immutable
                    ):
                        raise WorkflowRunStateConflict(
                            "Workflow run projection changed immutable identity"
                        )
                    updated = candidate.model_copy(
                        update={"completed_at": at if state in _TERMINAL else None}
                    )
                else:
                    updated = current.model_copy(
                        update={
                            "state": state,
                            "completed_at": at if state in _TERMINAL else None,
                        }
                    )
                updated = CanonicalWorkflowRun.model_validate(
                    updated.model_dump(mode="json")
                )
                if definition is not None:
                    validate_run_subject(definition, updated)
                result = connection.execute(
                    """UPDATE canonical_workflow_runs
                    SET state = ?, completed_at = ?, cleanup_state = ?, run_json = ?
                    WHERE run_id = ? AND state = ?""",
                    (
                        updated.state,
                        updated.completed_at,
                        updated.cleanup_state,
                        _json_bytes(updated),
                        run_id,
                        expected_state,
                    ),
                )
                if result.rowcount != 1:
                    raise WorkflowRunStateConflict(
                        "The workflow run state changed concurrently"
                    )
                kinds = (
                    activity_kind
                    if isinstance(activity_kind, tuple)
                    else (activity_kind,)
                )
                for kind in kinds:
                    sequence = self._next_sequence(connection, run_id)
                    self._append_activity(
                        connection,
                        WorkflowRunActivity(
                            run_id=run_id,
                            sequence=sequence,
                            occurred_at=at,
                            kind=kind,
                            summary=f"State {expected_state} -> {state}",
                            evidence_reference=None,
                        ),
                    )
                return updated
        except (WorkflowRunStateConflict, KeyError, ValueError):
            raise
        except sqlite3.DatabaseError as error:
            raise WorkflowExecutionSchemaError(
                "Workflow run transition failed without changing durable history"
            ) from error

    def request_cancel(self, run_id: str, *, at: int) -> CanonicalWorkflowRun:
        current = self.get(run_id)
        if current is None:
            raise KeyError(run_id)
        target = "cancelled" if current.state in {"idle", "queued"} else "cancelling"
        return self._transition(
            run_id,
            target,
            expected_state=current.state,
            at=at,
            activity_kind=("cancel_requested", "terminal")
            if target == "cancelled"
            else "cancel_requested",
        )

    def complete_cancel(self, run_id: str, *, at: int) -> CanonicalWorkflowRun:
        return self._transition(
            run_id,
            "cancelled",
            expected_state="cancelling",
            at=at,
            activity_kind="terminal",
        )

    def record_step(
        self, step: WorkflowRunStepRecord, definition: WorkflowDefinition
    ) -> None:
        validate_step_subject(definition, step)
        run = self.get(step.run_id)
        if run is None:
            raise KeyError(step.run_id)
        validate_run_subject(definition, run)
        try:
            with connect_state_db(self.db_path, ensure_parent=True) as connection:
                connection.execute(
                    """INSERT INTO canonical_workflow_run_steps
                    (run_id, step_id, attempt, block_id, step_json)
                    VALUES (?, ?, ?, ?, ?)""",
                    (
                        step.run_id,
                        step.step_id,
                        step.attempt,
                        step.block_id,
                        _json_bytes(step),
                    ),
                )
        except sqlite3.DatabaseError as error:
            raise WorkflowExecutionSchemaError(
                "Workflow step record could not be appended"
            ) from error

    def record_artifact(
        self, artifact: WorkflowArtifactRecord, definition: WorkflowDefinition
    ) -> None:
        validate_artifact_subject(definition, artifact)
        run = self.get(artifact.run_id)
        if run is None:
            raise KeyError(artifact.run_id)
        validate_run_subject(definition, run)
        try:
            with connect_state_db(self.db_path, ensure_parent=True) as connection:
                if not connection.execute(
                    """SELECT 1 FROM canonical_workflow_run_steps
                    WHERE run_id = ? AND step_id = ?""",
                    (artifact.run_id, artifact.step_id),
                ).fetchone():
                    raise ValueError("Workflow artifact step does not exist")
                for upstream_id in artifact.upstream_artifact_ids:
                    if not connection.execute(
                        """SELECT 1 FROM canonical_workflow_artifacts
                        WHERE run_id = ? AND artifact_id = ?""",
                        (artifact.run_id, upstream_id),
                    ).fetchone():
                        raise ValueError(
                            f"Workflow artifact upstream record {upstream_id} does not exist"
                        )
                connection.execute(
                    """INSERT INTO canonical_workflow_artifacts
                    (artifact_id, run_id, step_id, contract_id, digest_sha256,
                     cleanup_state, artifact_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        artifact.artifact_id,
                        artifact.run_id,
                        artifact.step_id,
                        artifact.contract_id,
                        artifact.digest_sha256,
                        artifact.cleanup_state,
                        _json_bytes(artifact),
                    ),
                )
        except ValueError:
            raise
        except sqlite3.DatabaseError as error:
            raise WorkflowExecutionSchemaError(
                "Workflow artifact record could not be appended"
            ) from error

    def reconnect(
        self, run_id: str, *, after_sequence: int = 0
    ) -> WorkflowRunReconnectSnapshot:
        if after_sequence < 0:
            raise ValueError("Workflow reconnect cursor cannot be negative")
        try:
            with connect_state_db(
                self.db_path, read_only=True, wal=False
            ) as connection:
                run = _decode_run(
                    connection.execute(
                        "SELECT * FROM canonical_workflow_runs WHERE run_id = ?",
                        (run_id,),
                    ).fetchone()
                )
                if run is None:
                    raise KeyError(run_id)
                step_rows = connection.execute(
                    """SELECT * FROM canonical_workflow_run_steps
                    WHERE run_id = ? ORDER BY step_id, attempt""",
                    (run_id,),
                ).fetchall()
                activity_rows = connection.execute(
                    """SELECT * FROM canonical_workflow_run_activities
                    WHERE run_id = ? AND sequence > ? ORDER BY sequence""",
                    (run_id, after_sequence),
                ).fetchall()
                artifact_rows = connection.execute(
                    """SELECT * FROM canonical_workflow_artifacts
                    WHERE run_id = ? ORDER BY artifact_id""",
                    (run_id,),
                ).fetchall()
                cursor = connection.execute(
                    """SELECT COALESCE(MAX(sequence), 0)
                    FROM canonical_workflow_run_activities WHERE run_id = ?""",
                    (run_id,),
                ).fetchone()[0]
            return WorkflowRunReconnectSnapshot(
                run=run,
                steps=tuple(_decode_step(row) for row in step_rows),
                activities=tuple(_decode_activity(row) for row in activity_rows),
                artifacts=tuple(_decode_artifact(row) for row in artifact_rows),
                cursor=int(cursor),
            )
        except KeyError:
            raise
        except (sqlite3.DatabaseError, ValueError) as error:
            raise WorkflowExecutionSchemaError(
                "Workflow reconnect snapshot is unavailable or incompatible"
            ) from error

    def cleanup(self, run_id: str, *, at: int) -> WorkflowRunReconnectSnapshot:
        try:
            with connect_state_db(self.db_path, ensure_parent=True) as connection:
                connection.execute("BEGIN IMMEDIATE")
                current = _decode_run(
                    connection.execute(
                        "SELECT * FROM canonical_workflow_runs WHERE run_id = ?",
                        (run_id,),
                    ).fetchone()
                )
                if current is None:
                    raise KeyError(run_id)
                if current.state not in _TERMINAL:
                    raise WorkflowRunStateConflict(
                        "Workflow run must be terminal before cleanup"
                    )
                if current.cleanup_state == "cleaned":
                    connection.rollback()
                    return self.reconnect(run_id)
                updated_run = CanonicalWorkflowRun.model_validate(
                    current.model_copy(update={"cleanup_state": "cleaned"}).model_dump(
                        mode="json"
                    )
                )
                connection.execute(
                    """UPDATE canonical_workflow_runs
                    SET cleanup_state = 'cleaned', run_json = ? WHERE run_id = ?""",
                    (_json_bytes(updated_run), run_id),
                )
                artifact_rows = connection.execute(
                    """SELECT * FROM canonical_workflow_artifacts
                    WHERE run_id = ? AND cleanup_state != 'cleaned'""",
                    (run_id,),
                ).fetchall()
                for row in artifact_rows:
                    artifact = _decode_artifact(row)
                    if artifact.lifetime == "retained":
                        continue
                    cleaned = WorkflowArtifactRecord.model_validate(
                        artifact.model_copy(
                            update={"cleanup_state": "cleaned"}
                        ).model_dump(mode="json")
                    )
                    connection.execute(
                        """UPDATE canonical_workflow_artifacts
                        SET cleanup_state = 'cleaned', artifact_json = ?
                        WHERE artifact_id = ?""",
                        (_json_bytes(cleaned), artifact.artifact_id),
                    )
                sequence = self._next_sequence(connection, run_id)
                self._append_activity(
                    connection,
                    WorkflowRunActivity(
                        run_id=run_id,
                        sequence=sequence,
                        occurred_at=at,
                        kind="cleanup",
                        summary="Run artifact cleanup completed",
                        evidence_reference=None,
                    ),
                )
            return self.reconnect(run_id)
        except (KeyError, WorkflowRunStateConflict):
            raise
        except (sqlite3.DatabaseError, ValueError) as error:
            raise WorkflowExecutionSchemaError(
                "Workflow cleanup failed without discarding lineage"
            ) from error


def _decode_run(row) -> CanonicalWorkflowRun | None:
    if row is None:
        return None
    run = CanonicalWorkflowRun.model_validate_json(bytes(row["run_json"]))
    if (
        run.run_id != row["run_id"]
        or run.workflow_id != row["workflow_id"]
        or run.workflow_revision != row["workflow_revision"]
        or run.semantic_sha256 != row["semantic_sha256"]
        or run.state != row["state"]
        or run.completed_at != row["completed_at"]
        or run.cleanup_state != row["cleanup_state"]
    ):
        raise ValueError("Persisted workflow run fields do not match its envelope")
    return run


def _decode_step(row) -> WorkflowRunStepRecord:
    step = WorkflowRunStepRecord.model_validate_json(bytes(row["step_json"]))
    if (
        step.run_id != row["run_id"]
        or step.step_id != row["step_id"]
        or step.attempt != row["attempt"]
        or step.block_id != row["block_id"]
    ):
        raise ValueError("Persisted workflow step fields do not match its envelope")
    return step


def _decode_activity(row) -> WorkflowRunActivity:
    activity = WorkflowRunActivity.model_validate_json(bytes(row["activity_json"]))
    if (
        activity.run_id != row["run_id"]
        or activity.sequence != row["sequence"]
        or activity.occurred_at != row["occurred_at"]
        or activity.kind != row["kind"]
    ):
        raise ValueError("Persisted workflow activity fields do not match its envelope")
    return activity


def _decode_artifact(row) -> WorkflowArtifactRecord:
    artifact = WorkflowArtifactRecord.model_validate_json(bytes(row["artifact_json"]))
    if (
        artifact.artifact_id != row["artifact_id"]
        or artifact.run_id != row["run_id"]
        or artifact.step_id != row["step_id"]
        or artifact.contract_id != row["contract_id"]
        or artifact.digest_sha256 != row["digest_sha256"]
        or artifact.cleanup_state != row["cleanup_state"]
    ):
        raise ValueError("Persisted workflow artifact fields do not match its envelope")
    return artifact


__all__ = [
    "WORKFLOW_EXECUTION_MIGRATIONS",
    "CanonicalWorkflowRunRepository",
    "WorkflowExecutionSchemaError",
    "WorkflowRunReconnectSnapshot",
    "WorkflowRunStateConflict",
    "rollback_workflow_execution_schema",
    "upgrade_workflow_execution_schema",
]
