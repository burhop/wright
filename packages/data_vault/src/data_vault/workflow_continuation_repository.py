"""Durable one-shot checkpoints for the existing canonical workflow executor."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from core.process_interactions import InteractionResponse, validate_response
from core.process_validation import canonical_digest
from .process_input_repository import ProcessInputRepository, encoded
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

    @property
    def checkpoint_kind(self) -> str:
        """Old approval records remain unchanged; kind is explicit in v3 JSON."""
        return self.continuation.get("checkpoint_kind", "approval")


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

    def pending_navigation(
        self, workspace_id: str, *, after: str = "", limit: int = 20
    ) -> dict[str, Any]:
        """Read compact recorded waits, not eligibility or dispatch authority."""
        if not 1 <= limit <= 50:
            raise ValueError("Pending navigation page size must be 1 through 50")
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            self._ensure(connection)
            rows = connection.execute(
                """SELECT checkpoint_id, workflow_id AS workflow_path, run_id,
                step_id, action_kind, state, expires_at,
                json_extract(continuation_json, '$.checkpoint_kind') AS checkpoint_kind,
                json_extract(continuation_json, '$.response_id') AS response_id,
                json_extract(continuation_json, '$.run_log_path') AS path,
                json_extract(continuation_json, '$.source_digest') AS source_digest,
                json_extract(continuation_json, '$.step_title') AS step_title
                FROM workflow_continuation_checkpoints
                WHERE workspace_id=? AND state IN ('pending', 'approved')
                AND checkpoint_id>? ORDER BY checkpoint_id LIMIT ?""",
                (workspace_id, after, limit + 1),
            ).fetchall()
        return {
            "items": [dict(row) for row in rows[:limit]],
            "next_cursor": rows[limit - 1]["checkpoint_id"]
            if len(rows) > limit
            else None,
        }

    @staticmethod
    def _input_checkpoint(connection, checkpoint_id):
        row = connection.execute(
            "SELECT * FROM workflow_continuation_checkpoints WHERE checkpoint_id=?",
            (checkpoint_id,),
        ).fetchone()
        checkpoint = WorkflowContinuationRepository._record(row) if row else None
        if (
            checkpoint is None
            or checkpoint.action_kind != "human_input"
            or checkpoint.continuation.get("schema_version") != 3
            or checkpoint.checkpoint_kind != "input"
            or checkpoint.external_action is not None
        ):
            raise WorkflowContinuationStateConflict(
                "This checkpoint is not a declared input continuation"
            )
        return checkpoint

    def attach_input_response(
        self, response: InteractionResponse, *, updated_at: int
    ) -> tuple[WorkflowContinuationCheckpoint, InteractionResponse, bool]:
        """Retain the exact response and its cursor reference in one transaction.

        This records an answer, not approval or permission to dispatch an action.
        The recorder still claims the execution segment separately, before work.
        """
        raw = encoded(response)
        # Initialize additive evidence tables before the write transaction.
        ProcessInputRepository(self.db_path)
        with connect_state_db(self.db_path) as connection:
            self._ensure(connection)
            connection.execute("BEGIN IMMEDIATE")
            checkpoint = self._input_checkpoint(connection, response.checkpoint_id)
            schema = checkpoint.subject.get("declaration", {}).get("response_schema")
            if (
                checkpoint.workspace_id != response.workspace_id
                or checkpoint.run_id != response.run_id
                or checkpoint.subject_digest != response.subject_digest
                or checkpoint.subject.get("input_digest") != response.input_digest
                or not isinstance(schema, dict)
                or canonical_digest(schema) != response.schema_digest
                or checkpoint.state not in {"pending", "consumed"}
                or (
                    checkpoint.expires_at is not None
                    and updated_at >= checkpoint.expires_at
                    and checkpoint.state != "consumed"
                )
            ):
                raise WorkflowContinuationStateConflict(
                    "The input response does not match a current checkpoint"
                )
            validate_response(schema, response.value)
            reference = checkpoint.continuation.get("response_id")
            if checkpoint.state == "consumed" and reference is None:
                raise WorkflowContinuationStateConflict(
                    "A consumed checkpoint cannot accept a new response"
                )
            retained, created = ProcessInputRepository._put_response(
                connection, response, raw
            )
            if reference is not None:
                if (
                    reference != retained.response_id
                    or checkpoint.continuation.get("response_digest") != retained.digest
                    or created
                ):
                    raise WorkflowContinuationStateConflict(
                        "The retained response and continuation disagree"
                    )
                return checkpoint, retained, False
            continuation = {
                **checkpoint.continuation,
                "response_id": retained.response_id,
                "response_digest": retained.digest,
            }
            connection.execute(
                """UPDATE workflow_continuation_checkpoints
                SET continuation_json=?,actor=?,reason=?,updated_at=?
                WHERE checkpoint_id=?""",
                (
                    json.dumps(continuation, sort_keys=True, separators=(",", ":")),
                    retained.actor,
                    retained.reason,
                    updated_at,
                    checkpoint.checkpoint_id,
                ),
            )
            return (
                self._input_checkpoint(connection, checkpoint.checkpoint_id),
                retained,
                created,
            )

    def consume_input_response(
        self,
        checkpoint_id: str,
        *,
        workspace_id: str,
        run_id: str,
        subject_digest: str,
        response_id: str,
        response_digest: str,
        updated_at: int,
    ) -> WorkflowContinuationCheckpoint:
        """Compare and consume one input barrier; never creates an action receipt."""
        with connect_state_db(self.db_path) as connection:
            self._ensure(connection)
            connection.execute("BEGIN IMMEDIATE")
            checkpoint = self._input_checkpoint(connection, checkpoint_id)
            if (
                checkpoint.workspace_id != workspace_id
                or checkpoint.run_id != run_id
                or checkpoint.subject_digest != subject_digest
                or checkpoint.continuation.get("response_id") != response_id
                or checkpoint.continuation.get("response_digest") != response_digest
                or checkpoint.state != "pending"
                or (
                    checkpoint.expires_at is not None
                    and updated_at >= checkpoint.expires_at
                )
            ):
                raise WorkflowContinuationStateConflict(
                    "Input continuation changed before its response was consumed"
                )
            row = connection.execute(
                """SELECT payload_json FROM process_interaction_responses
                WHERE workspace_id=? AND response_id=? AND run_id=? AND checkpoint_id=?""",
                (workspace_id, response_id, run_id, checkpoint_id),
            ).fetchone()
            if row is None or (
                InteractionResponse.model_validate_json(row["payload_json"]).digest
                != response_digest
            ):
                raise WorkflowContinuationStateConflict(
                    "The continuation has no matching immutable input response"
                )
            connection.execute(
                """UPDATE workflow_continuation_checkpoints
                SET state='consumed',updated_at=? WHERE checkpoint_id=?""",
                (updated_at, checkpoint_id),
            )
            return self._input_checkpoint(connection, checkpoint_id)

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
        continuation: dict[str, Any] | None = None,
    ) -> WorkflowContinuationCheckpoint:
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            self._ensure(connection)
            cursor = connection.execute(
                """UPDATE workflow_continuation_checkpoints
                SET state=?,updated_at=?,actor=COALESCE(?,actor),reason=COALESCE(?,reason),
                    external_action_json=COALESCE(?,external_action_json),
                    continuation_json=COALESCE(?,continuation_json)
                WHERE checkpoint_id=? AND state=?""",
                (
                    state,
                    updated_at,
                    actor,
                    reason,
                    json.dumps(external_action, sort_keys=True, separators=(",", ":"))
                    if external_action is not None
                    else None,
                    json.dumps(
                        continuation,
                        sort_keys=True,
                        separators=(",", ":"),
                        allow_nan=False,
                    )
                    if continuation is not None
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
