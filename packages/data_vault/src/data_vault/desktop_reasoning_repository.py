"""Append-only scoped handoff evidence. The workflow recorder owns run state."""

from core.desktop_reasoning import (
    DesktopActionReply,
    DesktopReasoningRequest,
    DesktopReasoningResponse,
)
from core.process_validation import canonical_json

from .state_store import connect_state_db


class DesktopHandoffConflict(ValueError):
    """A stale, interrupted or already consumed response cannot advance work."""


SCHEMA = (
    """CREATE TABLE IF NOT EXISTS desktop_reasoning_requests (
        workspace_id TEXT NOT NULL, session_id TEXT NOT NULL,
        run_id TEXT NOT NULL, ordinal INTEGER NOT NULL,
        request_id TEXT NOT NULL, request_digest TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        PRIMARY KEY(workspace_id,session_id,request_id),
        UNIQUE(workspace_id,session_id,run_id,ordinal)
    )""",
    """CREATE TABLE IF NOT EXISTS desktop_reasoning_responses (
        workspace_id TEXT NOT NULL, session_id TEXT NOT NULL,
        request_id TEXT NOT NULL, response_id TEXT NOT NULL,
        response_digest TEXT NOT NULL, payload_json TEXT NOT NULL,
        PRIMARY KEY(workspace_id,session_id,request_id),
        UNIQUE(workspace_id,session_id,response_id),
        FOREIGN KEY(workspace_id,session_id,request_id)
            REFERENCES desktop_reasoning_requests(workspace_id,session_id,request_id)
    )""",
    """CREATE TABLE IF NOT EXISTS desktop_reasoning_terminal_receipts (
        workspace_id TEXT NOT NULL, session_id TEXT NOT NULL,
        request_id TEXT NOT NULL, outcome TEXT NOT NULL
            CHECK(outcome IN ('consumed','cancelled','owner_interrupted')),
        PRIMARY KEY(workspace_id,session_id,request_id),
        FOREIGN KEY(workspace_id,session_id,request_id)
            REFERENCES desktop_reasoning_requests(workspace_id,session_id,request_id)
    )""",
    *(
        f"""CREATE TRIGGER IF NOT EXISTS {table}_no_{operation.lower()}
        BEFORE {operation} ON {table}
        BEGIN SELECT RAISE(ABORT, 'Desktop handoff evidence is immutable'); END"""
        for table in (
            "desktop_reasoning_requests",
            "desktop_reasoning_responses",
            "desktop_reasoning_terminal_receipts",
        )
        for operation in ("UPDATE", "DELETE")
    ),
)


class DesktopReasoningRepository:
    def __init__(self, db_path):
        self.db_path = db_path
        with connect_state_db(db_path, ensure_parent=True) as db:
            for statement in SCHEMA:
                db.execute(statement)

    @staticmethod
    def _request(db, workspace_id, session_id, request_id):
        row = db.execute(
            "SELECT payload_json FROM desktop_reasoning_requests "
            "WHERE workspace_id=? AND session_id=? AND request_id=?",
            (workspace_id, session_id, request_id),
        ).fetchone()
        if row is None:
            raise KeyError("Desktop request not found in connection scope")
        return DesktopReasoningRequest.model_validate_json(row["payload_json"])

    @staticmethod
    def _terminal(db, scope):
        row = db.execute(
            "SELECT outcome FROM desktop_reasoning_terminal_receipts "
            "WHERE workspace_id=? AND session_id=? AND request_id=?",
            scope,
        ).fetchone()
        return row["outcome"] if row else None

    def put_request(self, request):
        request = DesktopReasoningRequest.model_validate_json(request.model_dump_json())
        scope = (request.workspace_id, request.session_id, request.request_id)
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT request_digest FROM desktop_reasoning_requests "
                "WHERE workspace_id=? AND session_id=? AND request_id=?",
                scope,
            ).fetchone()
            if row:
                if row["request_digest"] != request.digest:
                    raise DesktopHandoffConflict(
                        "Request identity already has different content"
                    )
                return self._request(db, *scope)
            import sqlite3

            try:
                db.execute(
                    "INSERT INTO desktop_reasoning_requests VALUES (?,?,?,?,?,?,?)",
                    (
                        request.workspace_id,
                        request.session_id,
                        request.run_id,
                        request.ordinal,
                        request.request_id,
                        request.digest,
                        canonical_json(request),
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise DesktopHandoffConflict(
                    "Run decision ordinal already exists; reconcile its retained request"
                ) from exc
        return request

    def get_request(self, workspace_id, session_id, request_id):
        with connect_state_db(self.db_path, read_only=True) as db:
            return self._request(db, workspace_id, session_id, request_id)

    def continuation_ordinal(self, workspace_id, session_id, run_id):
        """Advance only past consumed replies at a canonical continuation.

        This does not authorize continuation or claim an effect completed. The
        caller must first use Wright's existing checkpoint/run qualification.
        Pending or interrupted requests require reconciliation, never replay.
        """
        with connect_state_db(self.db_path, read_only=True) as db:
            rows = db.execute(
                "SELECT r.ordinal,t.outcome FROM desktop_reasoning_requests r "
                "LEFT JOIN desktop_reasoning_terminal_receipts t ON "
                "t.workspace_id=r.workspace_id AND t.session_id=r.session_id "
                "AND t.request_id=r.request_id WHERE r.workspace_id=? AND "
                "r.session_id=? AND r.run_id=? ORDER BY r.ordinal",
                (workspace_id, session_id, run_id),
            ).fetchall()
        if any(row["outcome"] != "consumed" for row in rows):
            raise DesktopHandoffConflict(
                "The prior desktop request requires reconciliation before continuation"
            )
        return rows[-1]["ordinal"] if rows else 0

    def pending(self, workspace_id, session_id, *, limit=32):
        if not 1 <= limit <= 32:
            raise ValueError("Desktop request page requires a limit from 1 to 32")
        with connect_state_db(self.db_path, read_only=True) as db:
            rows = db.execute(
                "SELECT r.payload_json FROM desktop_reasoning_requests r "
                "WHERE r.workspace_id=? AND r.session_id=? AND NOT EXISTS "
                "(SELECT 1 FROM desktop_reasoning_terminal_receipts t WHERE "
                "t.workspace_id=r.workspace_id AND t.session_id=r.session_id "
                "AND t.request_id=r.request_id) ORDER BY r.rowid LIMIT ?",
                (workspace_id, session_id, limit),
            ).fetchall()
        return [
            DesktopReasoningRequest.model_validate_json(row["payload_json"])
            for row in rows
        ]

    def submit_response(self, workspace_id, session_id, response):
        response = DesktopReasoningResponse.model_validate_json(
            response.model_dump_json()
        )
        scope = (workspace_id, session_id, response.request_id)
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            request = self._request(db, *scope)
            if (
                response.request_digest != request.digest
                or response.binding_digest != request.binding.digest
            ):
                raise DesktopHandoffConflict(
                    "Desktop reply does not match the frozen task and binding"
                )
            if self._terminal(db, scope):
                raise DesktopHandoffConflict(
                    "Desktop request is terminal; no reply can advance it"
                )
            if (request.kind == "action") != isinstance(
                response.reply, DesktopActionReply
            ):
                raise DesktopHandoffConflict("Desktop reply kind differs from its task")
            row = db.execute(
                "SELECT payload_json FROM desktop_reasoning_responses "
                "WHERE workspace_id=? AND session_id=? AND request_id=?",
                scope,
            ).fetchone()
            if row:
                if row["payload_json"] != canonical_json(response):
                    raise DesktopHandoffConflict(
                        "A different reply already exists for this task"
                    )
                return response, False
            import sqlite3

            try:
                db.execute(
                    "INSERT INTO desktop_reasoning_responses VALUES (?,?,?,?,?,?)",
                    (
                        *scope,
                        response.response_id,
                        response.digest,
                        canonical_json(response),
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise DesktopHandoffConflict(
                    "Response identity already belongs to another task"
                ) from exc
        return response, True

    def consume_response(self, workspace_id, session_id, request_id):
        scope = (workspace_id, session_id, request_id)
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            self._request(db, *scope)
            if self._terminal(db, scope):
                raise DesktopHandoffConflict(
                    "Desktop request is terminal; reconcile its outcome"
                )
            row = db.execute(
                "SELECT payload_json FROM desktop_reasoning_responses "
                "WHERE workspace_id=? AND session_id=? AND request_id=?",
                scope,
            ).fetchone()
            if not row:
                return None
            response = DesktopReasoningResponse.model_validate_json(row["payload_json"])
            db.execute(
                "INSERT INTO desktop_reasoning_terminal_receipts VALUES (?,?,?,?)",
                (*scope, "consumed"),
            )
            return response

    def interrupt(
        self, workspace_id, session_id, request_id, *, outcome="owner_interrupted"
    ):
        if outcome not in {"cancelled", "owner_interrupted"}:
            raise ValueError("Invalid desktop interruption outcome")
        scope = (workspace_id, session_id, request_id)
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            self._request(db, *scope)
            if self._terminal(db, scope):
                return False
            db.execute(
                "INSERT INTO desktop_reasoning_terminal_receipts VALUES (?,?,?,?)",
                (*scope, outcome),
            )
        return True
