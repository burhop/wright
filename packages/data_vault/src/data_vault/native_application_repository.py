"""Durable native application ownership, leases and append-only cleanup evidence.

This repository does not discover, adopt or terminate operating-system processes.
Application services supply verified native observations and own those decisions.
"""

from __future__ import annotations

import json
from typing import Any

from core.native_application import NativeApplicationConflict, utc_now
from core.native_tracing import traced_native
from core.redaction import redact_mapping

from .state_store import connect_state_db


NATIVE_APPLICATION_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS native_application_sessions (
        session_id TEXT PRIMARY KEY, resource_id TEXT NOT NULL,
        record TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1
    )""",
    """CREATE TABLE IF NOT EXISTS native_application_documents (
        session_id TEXT NOT NULL REFERENCES native_application_sessions(session_id),
        native_id TEXT NOT NULL, record TEXT NOT NULL,
        PRIMARY KEY(session_id,native_id)
    )""",
    """CREATE TABLE IF NOT EXISTS native_application_leases (
        lease_id TEXT PRIMARY KEY, resource_id TEXT NOT NULL,
        session_id TEXT NOT NULL REFERENCES native_application_sessions(session_id),
        state TEXT NOT NULL CHECK(state IN
            ('available','leased','reconciling','quarantined','released')),
        record TEXT NOT NULL
    )""",
    """CREATE UNIQUE INDEX IF NOT EXISTS native_application_exclusive_resource
        ON native_application_leases(resource_id)
        WHERE state IN ('leased','reconciling','quarantined')""",
    """CREATE TABLE IF NOT EXISTS native_application_cleanup (
        session_id TEXT NOT NULL REFERENCES native_application_sessions(session_id),
        cleanup_id TEXT NOT NULL, record TEXT NOT NULL,
        PRIMARY KEY(session_id,cleanup_id)
    )""",
    """CREATE TABLE IF NOT EXISTS native_application_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL REFERENCES native_application_sessions(session_id),
        kind TEXT NOT NULL, occurred_at TEXT NOT NULL, record TEXT NOT NULL
    )""",
    *(
        f"""CREATE TRIGGER IF NOT EXISTS {table}_no_{operation.lower()}
        BEFORE {operation} ON {table}
        BEGIN SELECT RAISE(ABORT, 'Native lifecycle evidence is immutable'); END"""
        for table in ("native_application_events", "native_application_cleanup")
        for operation in ("UPDATE", "DELETE")
    ),
)


def _encoded(record: dict[str, Any]) -> str:
    # Native diagnostics must never persist environment values or credentials.
    return json.dumps(redact_mapping(record), sort_keys=True, separators=(",", ":"))


class NativeApplicationRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    @staticmethod
    def _event(db, session_id: str, kind: str, record: dict) -> None:
        db.execute(
            "INSERT INTO native_application_events(session_id,kind,occurred_at,record) VALUES(?,?,?,?)",
            (session_id, kind, utc_now(), _encoded(record)),
        )

    @traced_native("native.application.register")
    def register_session(self, record: dict) -> dict:
        encoded = _encoded(record)
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            current = db.execute(
                "SELECT record FROM native_application_sessions WHERE session_id=?",
                (record["session_id"],),
            ).fetchone()
            if current:
                if current[0] != encoded:
                    raise NativeApplicationConflict(
                        "Native session identity already exists"
                    )
            else:
                db.execute(
                    "INSERT INTO native_application_sessions(session_id,resource_id,record) VALUES(?,?,?)",
                    (record["session_id"], record["resource_id"], encoded),
                )
                self._event(db, record["session_id"], "session_registered", record)
        return self.get_session(record["session_id"])

    @traced_native("native.application.read")
    def get_session(self, session_id: str) -> dict:
        with connect_state_db(self.db_path, read_only=True) as db:
            row = db.execute(
                "SELECT record,revision FROM native_application_sessions WHERE session_id=?",
                (session_id,),
            ).fetchone()
        if row is None:
            raise KeyError(session_id)
        return {**json.loads(row["record"]), "revision": row["revision"]}

    def list_sessions(self) -> list[dict]:
        with connect_state_db(self.db_path, read_only=True) as db:
            rows = db.execute(
                "SELECT record,revision FROM native_application_sessions ORDER BY session_id"
            ).fetchall()
        return [{**json.loads(row[0]), "revision": row[1]} for row in rows]

    @traced_native("native.application.transition")
    def update_session(self, session: dict, *, kind: str, trace_id: str) -> dict:
        record = {key: value for key, value in session.items() if key != "revision"}
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute(
                "SELECT record FROM native_application_sessions WHERE session_id=?",
                (session["session_id"],),
            ).fetchone()
            if old is None:
                raise KeyError(session["session_id"])
            previous = json.loads(old[0])
            for key in (
                "identity",
                "resource_id",
                "ownership",
                "launch_receipt",
                "native_session_id",
                "app_kind",
                "version",
                "host",
            ):
                if record[key] != previous[key]:
                    raise NativeApplicationConflict(
                        f"Immutable native session field: {key}"
                    )
            changed = db.execute(
                "UPDATE native_application_sessions SET record=?,revision=revision+1 WHERE session_id=? AND revision=?",
                (_encoded(record), session["session_id"], session["revision"]),
            ).rowcount
            if changed != 1:
                raise NativeApplicationConflict(
                    "Native session changed; reconcile before retry"
                )
            self._event(
                db, session["session_id"], kind, {**record, "trace_id": trace_id}
            )
        return self.get_session(session["session_id"])

    @traced_native("native.application.lease.acquire")
    def acquire_lease(self, lease: dict, *, expected_revision: int) -> dict:
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            current = db.execute(
                "SELECT record,revision FROM native_application_sessions WHERE session_id=?",
                (lease["session_id"],),
            ).fetchone()
            session = json.loads(current[0]) if current else {}
            if (
                not current
                or current[1] != expected_revision
                or session.get("active_operation")
                or session.get("cleanup_in_progress")
                or session.get("lease_id")
                or session.get("state") in ("exited", "cleanup_blocked", "unknown")
            ):
                raise NativeApplicationConflict(
                    "Native session is not available for acquisition"
                )
            if lease["resource_id"] != session["resource_id"]:
                raise NativeApplicationConflict(
                    "Lease resource does not match application identity"
                )
            active = db.execute(
                "SELECT lease_id FROM native_application_leases WHERE resource_id=? AND state IN ('leased','reconciling','quarantined')",
                (lease["resource_id"],),
            ).fetchone()
            if active:
                raise NativeApplicationConflict(
                    "Native resource has an outstanding lease"
                )
            db.execute(
                "INSERT INTO native_application_leases VALUES(?,?,?,?,?)",
                (
                    lease["lease_id"],
                    lease["resource_id"],
                    lease["session_id"],
                    "leased",
                    _encoded(lease),
                ),
            )
            session.update(lease_id=lease["lease_id"], idle_deadline=None)
            db.execute(
                "UPDATE native_application_sessions SET record=?,revision=revision+1 WHERE session_id=?",
                (_encoded(session), lease["session_id"]),
            )
            self._event(db, lease["session_id"], "lease_acquired", lease)
        return lease

    def get_lease(self, lease_id: str) -> dict:
        with connect_state_db(self.db_path, read_only=True) as db:
            row = db.execute(
                "SELECT record FROM native_application_leases WHERE lease_id=?",
                (lease_id,),
            ).fetchone()
        if row is None:
            raise KeyError(lease_id)
        return json.loads(row[0])

    @traced_native("native.application.lease.transition")
    def transition_lease(
        self, lease_id: str, state: str, *, reason: str, trace_id: str
    ) -> None:
        if state not in ("leased", "reconciling", "quarantined", "released"):
            raise NativeApplicationConflict("An existing lease cannot become available")
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT record,state FROM native_application_leases WHERE lease_id=?",
                (lease_id,),
            ).fetchone()
            if row is None:
                raise KeyError(lease_id)
            lease = json.loads(row[0])
            if row[1] == "released" and state != "released":
                raise NativeApplicationConflict("Released leases cannot be revived")
            session_row = db.execute(
                "SELECT record FROM native_application_sessions WHERE session_id=?",
                (lease["session_id"],),
            ).fetchone()
            session = json.loads(session_row[0])
            if state == "released" and session.get("active_operation"):
                raise NativeApplicationConflict(
                    "Unknown native outcome retains its lease"
                )
            if state == "released" and (
                session.get("cleanup_in_progress")
                or session.get("state") == "cleanup_blocked"
            ):
                raise NativeApplicationConflict(
                    "Unresolved native cleanup retains its lease"
                )
            lease.update(
                state=state, reason=reason, updated_at=utc_now(), trace_id=trace_id
            )
            db.execute(
                "UPDATE native_application_leases SET state=?,record=? WHERE lease_id=?",
                (state, _encoded(lease), lease_id),
            )
            if state == "released" and session.get("lease_id") == lease_id:
                session["lease_id"] = None
                db.execute(
                    "UPDATE native_application_sessions SET record=?,revision=revision+1 WHERE session_id=?",
                    (_encoded(session), lease["session_id"]),
                )
            self._event(db, lease["session_id"], "lease_" + state, lease)

    @traced_native("native.application.document.record")
    def put_document(self, session_id: str, document: dict, *, trace_id: str) -> None:
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute(
                "SELECT record FROM native_application_documents WHERE session_id=? AND native_id=?",
                (session_id, document["native_id"]),
            ).fetchone()
            if old:
                previous = json.loads(old[0])
                for key in (
                    "native_id",
                    "path",
                    "ownership",
                    "preexisted",
                    "case_id",
                    "attempt",
                ):
                    if previous.get(key) != document.get(key):
                        raise NativeApplicationConflict(
                            f"Immutable native document field: {key}"
                        )
            db.execute(
                "INSERT INTO native_application_documents VALUES(?,?,?) ON CONFLICT(session_id,native_id) DO UPDATE SET record=excluded.record",
                (session_id, document["native_id"], _encoded(document)),
            )
            self._event(
                db, session_id, "document_recorded", {**document, "trace_id": trace_id}
            )

    def list_documents(self, session_id: str) -> list[dict]:
        with connect_state_db(self.db_path, read_only=True) as db:
            rows = db.execute(
                "SELECT record FROM native_application_documents WHERE session_id=? ORDER BY native_id",
                (session_id,),
            ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def get_cleanup(self, session_id: str, cleanup_id: str) -> dict | None:
        with connect_state_db(self.db_path, read_only=True) as db:
            row = db.execute(
                "SELECT record FROM native_application_cleanup WHERE session_id=? AND cleanup_id=?",
                (session_id, cleanup_id),
            ).fetchone()
        return json.loads(row[0]) if row else None

    @traced_native("native.application.cleanup.record")
    def record_cleanup(self, receipt: dict) -> dict:
        encoded = _encoded(receipt)
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            prior = db.execute(
                "SELECT record FROM native_application_cleanup WHERE session_id=? AND cleanup_id=?",
                (receipt["session_id"], receipt["cleanup_id"]),
            ).fetchone()
            if prior:
                if prior[0] != encoded:
                    raise NativeApplicationConflict("Cleanup receipt is immutable")
            else:
                db.execute(
                    "INSERT INTO native_application_cleanup VALUES(?,?,?)",
                    (receipt["session_id"], receipt["cleanup_id"], encoded),
                )
                self._event(
                    db, receipt["session_id"], "cleanup_" + receipt["status"], receipt
                )
        return json.loads(encoded)
