"""SQLite persistence for immutable workflow trace records."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from core.workflow_trace import (
    TraceArtifactVersion,
    TraceCaptureEvent,
    TraceEvidenceLink,
    TraceEvidenceRecord,
    TraceOccurrence,
    TraceReportRevision,
    TraceRunRecord,
    TraceTraversal,
)

from .state_store import connect_state_db


class WorkflowTraceStorageError(RuntimeError):
    pass


_T = TypeVar("_T", bound=BaseModel)


_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS workflow_trace_runs (
        run_id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        record_json BLOB NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS workflow_trace_events (
        run_id TEXT NOT NULL,
        sequence INTEGER NOT NULL,
        event_id TEXT NOT NULL UNIQUE,
        producer TEXT NOT NULL,
        producer_event_id TEXT NOT NULL,
        record_json BLOB NOT NULL,
        PRIMARY KEY (run_id, sequence),
        UNIQUE (run_id, producer, producer_event_id),
        FOREIGN KEY (run_id) REFERENCES workflow_trace_runs(run_id)
    )""",
    """CREATE TABLE IF NOT EXISTS workflow_trace_occurrences (
        occurrence_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        block_id TEXT NOT NULL,
        attempt INTEGER NOT NULL,
        record_json BLOB NOT NULL,
        UNIQUE (run_id, block_id, attempt),
        FOREIGN KEY (run_id) REFERENCES workflow_trace_runs(run_id)
    )""",
    """CREATE TABLE IF NOT EXISTS workflow_trace_traversals (
        traversal_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        relationship_id TEXT NOT NULL,
        sequence INTEGER NOT NULL,
        record_json BLOB NOT NULL,
        UNIQUE (run_id, relationship_id, sequence),
        FOREIGN KEY (run_id) REFERENCES workflow_trace_runs(run_id)
    )""",
    """CREATE TABLE IF NOT EXISTS workflow_trace_artifact_versions (
        version_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        occurrence_id TEXT NOT NULL,
        record_json BLOB NOT NULL,
        FOREIGN KEY (run_id) REFERENCES workflow_trace_runs(run_id),
        FOREIGN KEY (occurrence_id) REFERENCES workflow_trace_occurrences(occurrence_id)
    )""",
    """CREATE TABLE IF NOT EXISTS workflow_trace_evidence (
        evidence_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        producer TEXT NOT NULL,
        producer_record_id TEXT NOT NULL,
        record_json BLOB NOT NULL,
        UNIQUE (run_id, producer, producer_record_id),
        FOREIGN KEY (run_id) REFERENCES workflow_trace_runs(run_id)
    )""",
    """CREATE TABLE IF NOT EXISTS workflow_trace_links (
        link_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        record_json BLOB NOT NULL,
        FOREIGN KEY (run_id) REFERENCES workflow_trace_runs(run_id)
    )""",
    """CREATE TABLE IF NOT EXISTS workflow_trace_reports (
        report_id TEXT NOT NULL,
        revision INTEGER NOT NULL,
        run_id TEXT NOT NULL,
        record_json BLOB NOT NULL,
        PRIMARY KEY (report_id, revision),
        FOREIGN KEY (run_id) REFERENCES workflow_trace_runs(run_id)
    )""",
    "CREATE INDEX IF NOT EXISTS workflow_trace_occurrences_run ON workflow_trace_occurrences(run_id, block_id, attempt)",
    "CREATE INDEX IF NOT EXISTS workflow_trace_evidence_run ON workflow_trace_evidence(run_id, evidence_id)",
)


def _encoded(record: BaseModel) -> bytes:
    return json.dumps(
        record.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _decoded(model: type[_T], value: bytes | str) -> _T:
    return model.model_validate_json(value)


class WorkflowTraceRepository:
    """Append-only trace index. Existing identities are immutable and idempotent."""

    def __init__(self, database_path: str | Path) -> None:
        self.db_path = Path(database_path)

    def _connect(self):
        connection = connect_state_db(self.db_path, ensure_parent=True)
        for statement in _SCHEMA:
            connection.execute(statement)
        return connection

    @staticmethod
    def _put_immutable(
        connection: sqlite3.Connection,
        *,
        table: str,
        identity_columns: tuple[str, ...],
        identity_values: tuple[object, ...],
        insert_columns: tuple[str, ...],
        insert_values: tuple[object, ...],
        encoded: bytes,
    ) -> bool:
        where = " AND ".join(f"{column}=?" for column in identity_columns)
        existing = connection.execute(
            f"SELECT record_json FROM {table} WHERE {where}", identity_values
        ).fetchone()
        if existing is not None:
            if bytes(existing[0]) != encoded:
                raise WorkflowTraceStorageError(
                    f"immutable workflow trace identity changed in {table}"
                )
            return False
        columns = insert_columns + ("record_json",)
        placeholders = ",".join("?" for _ in columns)
        connection.execute(
            f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
            insert_values + (encoded,),
        )
        return True

    def put_run(self, record: TraceRunRecord) -> bool:
        encoded = _encoded(record)
        with self._connect() as connection:
            return self._put_immutable(
                connection,
                table="workflow_trace_runs",
                identity_columns=("run_id",),
                identity_values=(record.run_id,),
                insert_columns=("run_id", "workspace_id"),
                insert_values=(record.run_id, record.workspace_id),
                encoded=encoded,
            )

    def get_run(self, run_id: str) -> TraceRunRecord | None:
        if not self.db_path.exists():
            return None
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM workflow_trace_runs WHERE run_id=?", (run_id,)
            ).fetchone()
        return _decoded(TraceRunRecord, row[0]) if row else None

    def append_event(self, event: TraceCaptureEvent) -> bool:
        encoded = _encoded(event)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                """SELECT record_json FROM workflow_trace_events
                WHERE run_id=? AND producer=? AND producer_event_id=?""",
                (event.run_id, event.producer, event.producer_event_id),
            ).fetchone()
            if existing is not None:
                if bytes(existing[0]) != encoded:
                    raise WorkflowTraceStorageError("producer event identity changed")
                return False
            latest = connection.execute(
                "SELECT MAX(sequence) FROM workflow_trace_events WHERE run_id=?",
                (event.run_id,),
            ).fetchone()[0]
            expected = 1 if latest is None else int(latest) + 1
            if event.sequence != expected:
                raise WorkflowTraceStorageError(
                    "trace event sequence is not contiguous"
                )
            self._put_immutable(
                connection,
                table="workflow_trace_events",
                identity_columns=("event_id",),
                identity_values=(event.event_id,),
                insert_columns=(
                    "run_id",
                    "sequence",
                    "event_id",
                    "producer",
                    "producer_event_id",
                ),
                insert_values=(
                    event.run_id,
                    event.sequence,
                    event.event_id,
                    event.producer,
                    event.producer_event_id,
                ),
                encoded=encoded,
            )
            return True

    def put_occurrence(self, record: TraceOccurrence) -> bool:
        return self._put_record(
            record,
            table="workflow_trace_occurrences",
            identity_columns=("occurrence_id",),
            identity_values=(record.occurrence_id,),
            insert_columns=("occurrence_id", "run_id", "block_id", "attempt"),
            insert_values=(
                record.occurrence_id,
                record.run_id,
                record.block_id,
                record.attempt,
            ),
        )

    def put_traversal(self, record: TraceTraversal) -> bool:
        return self._put_record(
            record,
            table="workflow_trace_traversals",
            identity_columns=("traversal_id",),
            identity_values=(record.traversal_id,),
            insert_columns=("traversal_id", "run_id", "relationship_id", "sequence"),
            insert_values=(
                record.traversal_id,
                record.run_id,
                record.relationship_id,
                record.sequence,
            ),
        )

    def put_artifact_version(self, record: TraceArtifactVersion) -> bool:
        return self._put_record(
            record,
            table="workflow_trace_artifact_versions",
            identity_columns=("version_id",),
            identity_values=(record.version_id,),
            insert_columns=("version_id", "run_id", "occurrence_id"),
            insert_values=(record.version_id, record.run_id, record.occurrence_id),
        )

    def put_evidence(self, record: TraceEvidenceRecord) -> bool:
        return self._put_record(
            record,
            table="workflow_trace_evidence",
            identity_columns=("evidence_id",),
            identity_values=(record.evidence_id,),
            insert_columns=("evidence_id", "run_id", "producer", "producer_record_id"),
            insert_values=(
                record.evidence_id,
                record.run_id,
                record.producer,
                record.producer_record_id,
            ),
        )

    def put_link(self, record: TraceEvidenceLink) -> bool:
        return self._put_record(
            record,
            table="workflow_trace_links",
            identity_columns=("link_id",),
            identity_values=(record.link_id,),
            insert_columns=("link_id", "run_id"),
            insert_values=(record.link_id, record.run_id),
        )

    def put_report(self, record: TraceReportRevision) -> bool:
        return self._put_record(
            record,
            table="workflow_trace_reports",
            identity_columns=("report_id", "revision"),
            identity_values=(record.report_id, record.revision),
            insert_columns=("report_id", "revision", "run_id"),
            insert_values=(record.report_id, record.revision, record.run_id),
        )

    def _put_record(
        self,
        record: BaseModel,
        *,
        table: str,
        identity_columns: tuple[str, ...],
        identity_values: tuple[object, ...],
        insert_columns: tuple[str, ...],
        insert_values: tuple[object, ...],
    ) -> bool:
        encoded = _encoded(record)
        try:
            with self._connect() as connection:
                return self._put_immutable(
                    connection,
                    table=table,
                    identity_columns=identity_columns,
                    identity_values=identity_values,
                    insert_columns=insert_columns,
                    insert_values=insert_values,
                    encoded=encoded,
                )
        except sqlite3.IntegrityError as error:
            raise WorkflowTraceStorageError("trace reference does not exist") from error

    def occurrences(
        self,
        run_id: str,
        *,
        block_id: str | None = None,
        after: int = 0,
        limit: int = 100,
    ) -> tuple[TraceOccurrence, ...]:
        bounded = max(1, min(int(limit), 200))
        query = """SELECT record_json FROM workflow_trace_occurrences
            WHERE run_id=? AND attempt>?"""
        values: list[object] = [run_id, max(0, int(after))]
        if block_id is not None:
            query += " AND block_id=?"
            values.append(block_id)
        query += " ORDER BY attempt, occurrence_id LIMIT ?"
        values.append(bounded)
        with self._connect() as connection:
            rows = connection.execute(query, tuple(values)).fetchall()
        return tuple(_decoded(TraceOccurrence, row[0]) for row in rows)

    def evidence(
        self, run_id: str, *, after_id: str = "", limit: int = 100
    ) -> tuple[TraceEvidenceRecord, ...]:
        bounded = max(1, min(int(limit), 200))
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT record_json FROM workflow_trace_evidence
                WHERE run_id=? AND evidence_id>? ORDER BY evidence_id LIMIT ?""",
                (run_id, after_id, bounded),
            ).fetchall()
        return tuple(_decoded(TraceEvidenceRecord, row[0]) for row in rows)


__all__ = ["WorkflowTraceRepository", "WorkflowTraceStorageError"]
