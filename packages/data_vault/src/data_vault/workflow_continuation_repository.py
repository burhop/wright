"""Durable one-shot approval checkpoints for canonical workflow continuations."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .state_store import connect_state_db


WORKFLOW_CONTINUATION_SCHEMA = """CREATE TABLE IF NOT EXISTS workflow_continuation_checkpoints (
    checkpoint_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    workflow_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    step_id TEXT NOT NULL,
    action_kind TEXT NOT NULL,
    subject_json TEXT NOT NULL,
    subject_digest TEXT NOT NULL CHECK(length(subject_digest) = 64),
    state TEXT NOT NULL CHECK(state IN
        ('pending','approved','changes_requested','expired','stale','consumed')),
    continuation_json TEXT NOT NULL,
    actor TEXT,
    reason TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    expires_at INTEGER,
    external_action_json TEXT,
    UNIQUE(workspace_id, run_id, step_id, subject_digest)
)"""


@dataclass(frozen=True, slots=True)
class WorkflowContinuationCheckpoint:
    checkpoint_id: str
    workspace_id: str
    workflow_id: str
    run_id: str
    step_id: str
    action_kind: str
    subject: dict[str, Any]
    subject_digest: str
    state: str
    continuation: dict[str, Any]
    actor: str | None
    reason: str | None
    created_at: int
    updated_at: int
    expires_at: int | None
    external_action: dict[str, Any] | None


class WorkflowContinuationStateConflict(RuntimeError):
    pass


class WorkflowContinuationRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    @staticmethod
    def _ensure(connection) -> None:
        connection.execute(WORKFLOW_CONTINUATION_SCHEMA)
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_workflow_continuation_run ON workflow_continuation_checkpoints(workspace_id, run_id, updated_at)"
        )

    @staticmethod
    def _record(row) -> WorkflowContinuationCheckpoint:
        value = dict(row)
        return WorkflowContinuationCheckpoint(
            checkpoint_id=value["checkpoint_id"],
            workspace_id=value["workspace_id"],
            workflow_id=value["workflow_id"],
            run_id=value["run_id"],
            step_id=value["step_id"],
            action_kind=value["action_kind"],
            subject=json.loads(value["subject_json"]),
            subject_digest=value["subject_digest"],
            state=value["state"],
            continuation=json.loads(value["continuation_json"]),
            actor=value["actor"],
            reason=value["reason"],
            created_at=value["created_at"],
            updated_at=value["updated_at"],
            expires_at=value["expires_at"],
            external_action=(
                json.loads(value["external_action_json"])
                if value["external_action_json"]
                else None
            ),
        )

    def create(
        self, checkpoint: WorkflowContinuationCheckpoint
    ) -> WorkflowContinuationCheckpoint:
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            self._ensure(connection)
            connection.execute(
                """INSERT INTO workflow_continuation_checkpoints
                (checkpoint_id,workspace_id,workflow_id,run_id,step_id,action_kind,
                 subject_json,subject_digest,state,continuation_json,actor,reason,
                 created_at,updated_at,expires_at,external_action_json)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    checkpoint.checkpoint_id,
                    checkpoint.workspace_id,
                    checkpoint.workflow_id,
                    checkpoint.run_id,
                    checkpoint.step_id,
                    checkpoint.action_kind,
                    json.dumps(
                        checkpoint.subject, sort_keys=True, separators=(",", ":")
                    ),
                    checkpoint.subject_digest,
                    checkpoint.state,
                    json.dumps(
                        checkpoint.continuation, sort_keys=True, separators=(",", ":")
                    ),
                    checkpoint.actor,
                    checkpoint.reason,
                    checkpoint.created_at,
                    checkpoint.updated_at,
                    checkpoint.expires_at,
                    None,
                ),
            )
        return checkpoint

    def get(self, checkpoint_id: str) -> WorkflowContinuationCheckpoint | None:
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            self._ensure(connection)
            row = connection.execute(
                "SELECT * FROM workflow_continuation_checkpoints WHERE checkpoint_id=?",
                (checkpoint_id,),
            ).fetchone()
        return self._record(row) if row else None

    def list_for_run(
        self, workspace_id: str, run_id: str
    ) -> tuple[WorkflowContinuationCheckpoint, ...]:
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            self._ensure(connection)
            rows = connection.execute(
                """SELECT * FROM workflow_continuation_checkpoints
                WHERE workspace_id=? AND run_id=?
                ORDER BY created_at, checkpoint_id""",
                (workspace_id, run_id),
            ).fetchall()
        return tuple(self._record(row) for row in rows)

    def transition(
        self,
        checkpoint_id: str,
        *,
        expected_state: str,
        state: str,
        updated_at: int,
        actor: str | None = None,
        reason: str | None = None,
        external_action: dict[str, Any] | None = None,
    ) -> WorkflowContinuationCheckpoint:
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            self._ensure(connection)
            cursor = connection.execute(
                """UPDATE workflow_continuation_checkpoints
                SET state=?,updated_at=?,actor=COALESCE(?,actor),reason=COALESCE(?,reason),
                    external_action_json=COALESCE(?,external_action_json)
                WHERE checkpoint_id=? AND state=?""",
                (
                    state,
                    updated_at,
                    actor,
                    reason,
                    json.dumps(external_action, sort_keys=True, separators=(",", ":"))
                    if external_action is not None
                    else None,
                    checkpoint_id,
                    expected_state,
                ),
            )
            if cursor.rowcount != 1:
                raise WorkflowContinuationStateConflict(
                    "Approval checkpoint changed before this operation completed"
                )
            row = connection.execute(
                "SELECT * FROM workflow_continuation_checkpoints WHERE checkpoint_id=?",
                (checkpoint_id,),
            ).fetchone()
        return self._record(row)
