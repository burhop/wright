"""Immutable scoped inputs and receipts, not another run lifecycle store."""

from __future__ import annotations

import sqlite3

from core.process_interactions import (
    InputSnapshot,
    InteractionResponse,
    ProcessRef,
    StartReceipt,
)
from core.process_validation import canonical_json
from core.tracing import traced

from .state_store import connect_state_db


class ProcessRecordConflict(ValueError):
    """The retained identity cannot be replaced or consumed twice."""


PROCESS_INPUT_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS process_input_snapshots (
        workspace_id TEXT NOT NULL, snapshot_id TEXT NOT NULL,
        digest TEXT NOT NULL CHECK(length(digest)=64), payload_json TEXT NOT NULL,
        PRIMARY KEY(workspace_id,snapshot_id)
    )""",
    """CREATE TABLE IF NOT EXISTS process_start_receipts (
        workspace_id TEXT NOT NULL, principal_id TEXT NOT NULL,
        source_path TEXT NOT NULL, request_id TEXT NOT NULL,
        run_id TEXT NOT NULL, snapshot_id TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        PRIMARY KEY(workspace_id,principal_id,source_path,request_id),
        UNIQUE(workspace_id,run_id),
        FOREIGN KEY(workspace_id,snapshot_id)
            REFERENCES process_input_snapshots(workspace_id,snapshot_id)
    )""",
    """CREATE TABLE IF NOT EXISTS process_interaction_responses (
        workspace_id TEXT NOT NULL, response_id TEXT NOT NULL,
        run_id TEXT NOT NULL, checkpoint_id TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        PRIMARY KEY(workspace_id,response_id),
        UNIQUE(workspace_id,run_id,checkpoint_id)
    )""",
    *(
        f"""CREATE TRIGGER IF NOT EXISTS {table}_no_{operation.lower()}
        BEFORE {operation} ON {table}
        BEGIN SELECT RAISE(ABORT, 'Process input evidence is immutable'); END"""
        for table in (
            "process_input_snapshots",
            "process_start_receipts",
            "process_interaction_responses",
        )
        for operation in ("UPDATE", "DELETE")
    ),
)


def encoded(value) -> str:
    # Revalidate even model_copy values; a frozen model can contain mutable JSON.
    checked = type(value).model_validate_json(value.model_dump_json())
    raw = canonical_json(checked)
    if len(raw.encode("utf-8")) > 20_971_520:
        raise ValueError("Process record exceeds 20 MiB")
    return raw


class ProcessInputRepository:
    def __init__(self, db_path):
        self.db_path = db_path
        with connect_state_db(db_path, ensure_parent=True) as db:
            for statement in PROCESS_INPUT_SCHEMA:
                db.execute(statement)

    @staticmethod
    def _put_snapshot(db, snapshot: InputSnapshot, raw: str) -> InputSnapshot:
        scope = (snapshot.process.workspace_id, snapshot.snapshot_id)
        row = db.execute(
            "SELECT payload_json FROM process_input_snapshots WHERE workspace_id=? AND snapshot_id=?",
            scope,
        ).fetchone()
        if row:
            if row["payload_json"] != raw:
                raise ProcessRecordConflict(
                    "Input snapshot identity already has different content"
                )
            return InputSnapshot.model_validate_json(row["payload_json"])
        db.execute(
            "INSERT INTO process_input_snapshots VALUES (?,?,?,?)",
            (*scope, snapshot.digest, raw),
        )
        return InputSnapshot.model_validate_json(raw)

    @traced("process.inputs.persist")
    def put_snapshot(self, snapshot: InputSnapshot) -> InputSnapshot:
        raw = encoded(snapshot)
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            return self._put_snapshot(db, snapshot, raw)

    @traced("process.inputs.read")
    def get_snapshot(self, workspace_id: str, snapshot_id: str) -> InputSnapshot:
        with connect_state_db(self.db_path, read_only=True) as db:
            row = db.execute(
                "SELECT payload_json FROM process_input_snapshots WHERE workspace_id=? AND snapshot_id=?",
                (workspace_id, snapshot_id),
            ).fetchone()
        if not row:
            raise KeyError("Input snapshot not found in workspace")
        return InputSnapshot.model_validate_json(row["payload_json"])

    @traced("process.start.reserve")
    def reserve_start(
        self, snapshot: InputSnapshot, receipt: StartReceipt
    ) -> tuple[StartReceipt, bool]:
        snapshot_raw, receipt_raw = encoded(snapshot), encoded(receipt)
        if (
            receipt.process != snapshot.process
            or receipt.input_snapshot_id != snapshot.snapshot_id
            or receipt.input_digest != snapshot.digest
        ):
            raise ProcessRecordConflict(
                "Start receipt must identify its exact input snapshot"
            )
        scope = (
            receipt.process.workspace_id,
            receipt.principal_id,
            receipt.process.source_path,
            receipt.request_id,
        )
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT payload_json FROM process_start_receipts WHERE workspace_id=? AND principal_id=? AND source_path=? AND request_id=?",
                scope,
            ).fetchone()
            if row:
                prior = StartReceipt.model_validate_json(row["payload_json"])
                previous_snapshot = db.execute(
                    "SELECT payload_json FROM process_input_snapshots WHERE workspace_id=? AND snapshot_id=?",
                    (prior.process.workspace_id, prior.input_snapshot_id),
                ).fetchone()
                prior_inputs = InputSnapshot.model_validate_json(
                    previous_snapshot["payload_json"]
                )
                if (
                    prior.payload_digest != receipt.payload_digest
                    or prior.process != receipt.process
                    or prior_inputs.bindings != snapshot.bindings
                ):
                    raise ProcessRecordConflict(
                        "Start request identity already has different content"
                    )
                return prior, False
            self._put_snapshot(db, snapshot, snapshot_raw)
            try:
                db.execute(
                    "INSERT INTO process_start_receipts VALUES (?,?,?,?,?,?,?)",
                    (*scope, receipt.run_id, receipt.input_snapshot_id, receipt_raw),
                )
            except sqlite3.IntegrityError as exc:
                raise ProcessRecordConflict(
                    "Run identity already belongs to another start request"
                ) from exc
        return StartReceipt.model_validate_json(receipt_raw), True

    @traced("process.start.receipt")
    def start_receipt(
        self, principal_id: str, process: ProcessRef, request_id: str
    ) -> StartReceipt:
        with connect_state_db(self.db_path, read_only=True) as db:
            row = db.execute(
                "SELECT payload_json FROM process_start_receipts WHERE workspace_id=? AND principal_id=? AND source_path=? AND request_id=?",
                (process.workspace_id, principal_id, process.source_path, request_id),
            ).fetchone()
        if not row:
            raise KeyError("Start request not found in principal/process scope")
        return StartReceipt.model_validate_json(row["payload_json"])

    @traced("process.start.run_receipt")
    def receipt_for_run(
        self, workspace_id: str, source_path: str, run_id: str
    ) -> StartReceipt | None:
        """Resolve frozen input identity; this receipt never determines run state."""
        with connect_state_db(self.db_path, read_only=True) as db:
            row = db.execute(
                "SELECT payload_json FROM process_start_receipts WHERE workspace_id=? AND source_path=? AND run_id=?",
                (workspace_id, source_path, run_id),
            ).fetchone()
        return StartReceipt.model_validate_json(row["payload_json"]) if row else None

    @traced("process.response.persist")
    def put_response(
        self, response: InteractionResponse
    ) -> tuple[InteractionResponse, bool]:
        raw = encoded(response)
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT payload_json FROM process_interaction_responses WHERE workspace_id=? AND run_id=? AND checkpoint_id=?",
                (response.workspace_id, response.run_id, response.checkpoint_id),
            ).fetchone()
            if row:
                prior = InteractionResponse.model_validate_json(row["payload_json"])
                retry_fields = {"response_id", "created_at", "digest"}
                if prior.model_dump(exclude=retry_fields) != response.model_dump(
                    exclude=retry_fields
                ):
                    raise ProcessRecordConflict(
                        "Checkpoint already has a different exact response"
                    )
                return prior, False
            try:
                db.execute(
                    "INSERT INTO process_interaction_responses VALUES (?,?,?,?,?)",
                    (
                        response.workspace_id,
                        response.response_id,
                        response.run_id,
                        response.checkpoint_id,
                        raw,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise ProcessRecordConflict(
                    "Response identity already belongs to another checkpoint"
                ) from exc
        return InteractionResponse.model_validate_json(raw), True

    @traced("process.response.read")
    def get_response(self, workspace_id: str, response_id: str) -> InteractionResponse:
        with connect_state_db(self.db_path, read_only=True) as db:
            row = db.execute(
                "SELECT payload_json FROM process_interaction_responses WHERE workspace_id=? AND response_id=?",
                (workspace_id, response_id),
            ).fetchone()
        if not row:
            raise KeyError("Response not found in workspace")
        return InteractionResponse.model_validate_json(row["payload_json"])
