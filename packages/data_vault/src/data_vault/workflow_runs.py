from __future__ import annotations

import json
import hashlib
import time
from dataclasses import dataclass, replace
from typing import Any

from .state_store import connect_state_db


_STATES = {"queued", "running", "cancelling", "cancelled", "succeeded", "failed"}
_TERMINAL = {"cancelled", "succeeded", "failed"}
_TRANSITIONS = {
    "queued": {"running", "cancelled", "failed"},
    "running": {"cancelling", "succeeded", "failed"},
    "cancelling": {"cancelled", "failed"},
}


@dataclass(frozen=True, slots=True)
class WorkflowRunRecord:
    run_id: str
    workspace_id: str
    session_id: str
    workflow_id: str
    revision: int
    digest: str
    graph: str
    state: str
    generation: int
    started_at: int | None
    completed_at: int | None
    reason_code: str | None
    output_summary: dict[str, Any] | None
    output_truncated: bool
    trace_id: str | None = None


@dataclass(frozen=True, slots=True)
class WorkflowRunEventRecord:
    run_id: str
    sequence: int
    occurred_at: int
    kind: str
    payload: dict[str, Any]


class WorkflowRunRepository:
    def __init__(
        self,
        db_path: str,
        *,
        maximum_output_bytes: int = 1024 * 1024,
        maximum_event_bytes: int = 64 * 1024,
    ) -> None:
        self.db_path = db_path
        self.maximum_output_bytes = maximum_output_bytes
        self.maximum_event_bytes = maximum_event_bytes

    @staticmethod
    def _json(value: dict[str, Any] | None) -> str | None:
        return (
            json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
            if value is not None
            else None
        )

    def _bounded_json(
        self, value: dict[str, Any] | None, *, limit: int, label: str
    ) -> str | None:
        encoded = self._json(value)
        if encoded is not None and len(encoded.encode("utf-8")) > limit:
            raise ValueError(f"Workflow run {label} exceeds the configured limit")
        return encoded

    def create(self, record: WorkflowRunRecord) -> None:
        if record.state not in _STATES:
            raise ValueError("Invalid workflow run state")
        if record.revision < 1 or record.generation < 1 or len(record.digest) != 64:
            raise ValueError("Invalid workflow run identity")
        output_json = self._bounded_json(
            record.output_summary,
            limit=self.maximum_output_bytes,
            label="output",
        )
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            existing = connection.execute(
                "SELECT workflow_id, revision, digest FROM workspace_workflow_runs WHERE run_id=?",
                (record.run_id,),
            ).fetchone()
            if existing is not None:
                identity = (record.workflow_id, record.revision, record.digest)
                if tuple(existing) != identity:
                    raise ValueError("Workflow run identity is immutable")
                raise ValueError("Workflow run already exists")
            connection.execute(
                """INSERT INTO workspace_workflow_runs
                (run_id, workspace_id, session_id, workflow_id, revision, digest,
                 graph, state, generation, started_at, completed_at, reason_code,
                 output_json, output_truncated, trace_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.run_id,
                    record.workspace_id,
                    record.session_id,
                    record.workflow_id,
                    record.revision,
                    record.digest,
                    record.graph,
                    record.state,
                    record.generation,
                    record.started_at,
                    record.completed_at,
                    record.reason_code,
                    output_json,
                    int(record.output_truncated),
                    record.trace_id,
                ),
            )

    @staticmethod
    def _record(row) -> WorkflowRunRecord:
        return WorkflowRunRecord(
            run_id=str(row["run_id"]),
            workspace_id=str(row["workspace_id"]),
            session_id=str(row["session_id"]),
            workflow_id=str(row["workflow_id"]),
            revision=int(row["revision"]),
            digest=str(row["digest"]),
            graph=str(row["graph"]),
            state=str(row["state"]),
            generation=int(row["generation"]),
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            reason_code=row["reason_code"],
            output_summary=(
                json.loads(row["output_json"]) if row["output_json"] else None
            ),
            output_truncated=bool(row["output_truncated"]),
            trace_id=row["trace_id"],
        )

    def get(self, run_id: str) -> WorkflowRunRecord | None:
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            row = connection.execute(
                "SELECT * FROM workspace_workflow_runs WHERE run_id=?", (run_id,)
            ).fetchone()
        if row is None:
            return None
        return self._record(row)

    def transition(
        self,
        run_id: str,
        state: str,
        *,
        completed_at: int | None = None,
        reason_code: str | None = None,
        output_summary: dict[str, Any] | None = None,
        output_truncated: bool = False,
    ) -> WorkflowRunRecord:
        current = self.get(run_id)
        if current is None:
            raise KeyError(run_id)
        if current.state in _TERMINAL:
            raise ValueError("Workflow run is already terminal")
        if state not in _TRANSITIONS.get(current.state, set()):
            raise ValueError(
                f"Invalid workflow run transition {current.state} -> {state}"
            )
        updated = replace(
            current,
            state=state,
            started_at=(
                current.started_at
                if current.started_at is not None or state != "running"
                else int(time.time())
            ),
            completed_at=completed_at,
            reason_code=reason_code,
            output_summary=output_summary,
            output_truncated=output_truncated,
        )
        try:
            output_json = self._bounded_json(
                updated.output_summary,
                limit=self.maximum_output_bytes,
                label="output",
            )
        except ValueError:
            encoded = self._json(updated.output_summary) or "{}"
            output_json = self._json(
                {
                    "complete": False,
                    "truncation_reason": "repository_limit",
                    "original_bytes": len(encoded.encode("utf-8")),
                    "digest": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
                }
            )
            output_truncated = True
            updated = replace(
                updated, output_summary=json.loads(output_json), output_truncated=True
            )
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            connection.execute(
                """UPDATE workspace_workflow_runs SET
                    state=?, started_at=?, completed_at=?, reason_code=?, output_json=?,
                    output_truncated=? WHERE run_id=?""",
                (
                    state,
                    updated.started_at,
                    completed_at,
                    reason_code,
                    output_json,
                    int(output_truncated),
                    run_id,
                ),
            )
        return updated

    def latest_sequence(self, run_id: str) -> int:
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            value = connection.execute(
                "SELECT MAX(sequence) FROM workspace_workflow_run_events WHERE run_id=?",
                (run_id,),
            ).fetchone()[0]
        return int(value or 0)

    def recent(
        self,
        *,
        workspace_id: str,
        session_id: str,
        workflow_id: str,
        limit: int = 20,
    ) -> tuple[WorkflowRunRecord, ...]:
        bounded = max(1, min(int(limit), 50))
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            rows = connection.execute(
                """SELECT * FROM workspace_workflow_runs
                WHERE workspace_id=? AND session_id=? AND workflow_id=?
                ORDER BY COALESCE(started_at, completed_at, 0) DESC, run_id DESC
                LIMIT ?""",
                (workspace_id, session_id, workflow_id, bounded),
            ).fetchall()
        return tuple(self._record(row) for row in rows)

    def append_event(self, event: WorkflowRunEventRecord) -> None:
        if event.sequence < 1 or not event.kind:
            raise ValueError("Invalid workflow run event")
        payload_json = self._bounded_json(
            event.payload,
            limit=self.maximum_event_bytes,
            label="event",
        )
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            latest = connection.execute(
                "SELECT MAX(sequence) FROM workspace_workflow_run_events WHERE run_id=?",
                (event.run_id,),
            ).fetchone()[0]
            expected = 1 if latest is None else int(latest) + 1
            if event.sequence != expected:
                raise ValueError("Workflow run event sequence is not contiguous")
            connection.execute(
                """INSERT INTO workspace_workflow_run_events
                (run_id, sequence, occurred_at, kind, payload_json)
                VALUES (?, ?, ?, ?, ?)""",
                (
                    event.run_id,
                    event.sequence,
                    event.occurred_at,
                    event.kind,
                    payload_json or "{}",
                ),
            )

    def events(
        self, run_id: str, *, after_sequence: int = 0, limit: int = 256
    ) -> tuple[WorkflowRunEventRecord, ...]:
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            rows = connection.execute(
                """SELECT * FROM workspace_workflow_run_events
                WHERE run_id=? AND sequence>? ORDER BY sequence LIMIT ?""",
                (run_id, after_sequence, max(1, min(limit, 256))),
            ).fetchall()
        return tuple(
            WorkflowRunEventRecord(
                run_id=str(row["run_id"]),
                sequence=int(row["sequence"]),
                occurred_at=int(row["occurred_at"]),
                kind=str(row["kind"]),
                payload=json.loads(row["payload_json"]),
            )
            for row in rows
        )
