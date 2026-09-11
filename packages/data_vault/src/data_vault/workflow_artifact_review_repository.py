"""Durable, immutable review subjects; workspace log files are not authority."""

import json
from .state_store import connect_state_db

REVIEW_SCHEMA = """CREATE TABLE IF NOT EXISTS workflow_artifact_reviews (
 review_id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL, workflow_path TEXT NOT NULL,
 package_digest TEXT NOT NULL CHECK(length(package_digest)=64),
 package_json TEXT NOT NULL CHECK(length(package_json)<=16777216),
 state TEXT NOT NULL CHECK(state IN ('pending','approved','changes_requested')),
 decision_json TEXT, UNIQUE(workspace_id, package_digest))"""


class ArtifactReviewConflict(ValueError):
    pass


class WorkflowArtifactReviewRepository:
    def __init__(self, db_path):
        self.db_path = db_path

    def create(self, review_id, workspace_id, path, digest, package):
        raw = json.dumps(
            package, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        )
        if len(raw.encode()) > 16 * 1024 * 1024:
            raise ValueError("Review evidence exceeds 16 MiB")
        with connect_state_db(self.db_path, ensure_parent=True) as db:
            db.execute(REVIEW_SCHEMA)
            db.execute(
                "INSERT INTO workflow_artifact_reviews VALUES (?,?,?,?,?,?,?)",
                (review_id, workspace_id, path, digest, raw, "pending", None),
            )

    def get(self, workspace_id, review_id):
        with connect_state_db(self.db_path, ensure_parent=True) as db:
            db.execute(REVIEW_SCHEMA)
            row = db.execute(
                "SELECT * FROM workflow_artifact_reviews WHERE workspace_id=? AND review_id=?",
                (workspace_id, review_id),
            ).fetchone()
        if row is None:
            raise KeyError("Review not found in this workspace")
        return dict(row)

    def list(self, workspace_id, path):
        with connect_state_db(self.db_path, ensure_parent=True) as db:
            db.execute(REVIEW_SCHEMA)
            rows = db.execute(
                "SELECT * FROM workflow_artifact_reviews WHERE workspace_id=? AND workflow_path=? ORDER BY rowid DESC LIMIT 20",
                (workspace_id, path),
            ).fetchall()
        return [dict(row) for row in rows]

    def decide(self, workspace_id, review_id, digest, decision):
        raw = json.dumps(decision, sort_keys=True, separators=(",", ":"))
        with connect_state_db(self.db_path, ensure_parent=True) as db:
            db.execute(REVIEW_SCHEMA)
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute(
                    "SELECT * FROM workflow_artifact_reviews WHERE workspace_id=? AND review_id=?",
                    (workspace_id, review_id),
                ).fetchone()
                if row is None:
                    raise KeyError("Review not found in this workspace")
                if row["package_digest"] != digest:
                    raise ArtifactReviewConflict("The reviewed package changed")
                if row["state"] != "pending":
                    previous = json.loads(row["decision_json"])
                    if any(
                        previous.get(key) != decision.get(key)
                        for key in ("state", "actor", "reason")
                    ):
                        raise ArtifactReviewConflict(
                            "A different decision was already recorded"
                        )
                else:
                    db.execute(
                        "UPDATE workflow_artifact_reviews SET state=?, decision_json=? WHERE review_id=? AND state=?",
                        (decision["state"], raw, review_id, "pending"),
                    )
                db.commit()
            except BaseException:
                db.rollback()
                raise
        return self.get(workspace_id, review_id)
