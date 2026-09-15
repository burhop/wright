"""Immutable locally enrolled integration authority, separate from qualification."""

from __future__ import annotations

import json

from .state_store import connect_state_db


class WorkflowIntegrationRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    @staticmethod
    def _ensure(db) -> None:
        db.execute("""CREATE TABLE IF NOT EXISTS workflow_integration_grants (
            policy_digest TEXT PRIMARY KEY CHECK(length(policy_digest)=64),
            document TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS workflow_integration_revocations (
            policy_digest TEXT PRIMARY KEY REFERENCES workflow_integration_grants(policy_digest),
            revoked_at INTEGER NOT NULL
        )""")
        for operation in ("UPDATE", "DELETE"):
            db.execute(f"""CREATE TRIGGER IF NOT EXISTS integration_grants_no_{operation.lower()}
                BEFORE {operation} ON workflow_integration_grants
                BEGIN SELECT RAISE(ABORT, 'Integration grants are immutable'); END""")

    def enroll(self, policy_digest: str, document: dict) -> None:
        encoded = json.dumps(document, sort_keys=True, separators=(",", ":"))
        with connect_state_db(self.db_path, ensure_parent=True) as db:
            self._ensure(db)
            db.execute(
                "INSERT OR IGNORE INTO workflow_integration_grants VALUES (?,?,?)",
                (policy_digest, encoded, document["created_at"]),
            )
            row = db.execute(
                "SELECT document FROM workflow_integration_grants WHERE policy_digest=?",
                (policy_digest,),
            ).fetchone()
            if row["document"] != encoded:
                raise ValueError("Integration grant identity conflict")

    def get(self, policy_digest: str) -> dict | None:
        with connect_state_db(self.db_path, ensure_parent=True) as db:
            self._ensure(db)
            row = db.execute(
                """SELECT g.document, r.revoked_at
                FROM workflow_integration_grants g
                LEFT JOIN workflow_integration_revocations r USING(policy_digest)
                WHERE g.policy_digest=?""",
                (policy_digest,),
            ).fetchone()
        if row is None:
            return None
        return {
            "document": json.loads(row["document"]),
            "revoked_at": row["revoked_at"],
        }

    def revoke(self, policy_digest: str, revoked_at: int) -> None:
        with connect_state_db(self.db_path, ensure_parent=True) as db:
            self._ensure(db)
            db.execute(
                "INSERT OR IGNORE INTO workflow_integration_revocations VALUES (?,?)",
                (policy_digest, revoked_at),
            )
