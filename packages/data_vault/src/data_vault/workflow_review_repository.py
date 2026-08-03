from dataclasses import dataclass

from .state_store import connect_state_db


@dataclass(frozen=True, slots=True)
class WorkflowReview:
    workspace_id: str
    workflow_id: str
    revision: int
    state: str
    reviewer: str
    updated_at: int


class WorkflowReviewRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def _ensure(self, conn) -> None:
        # Runtime creation keeps independently-created workspace state usable;
        # migration 11 is the authoritative upgrade path for managed databases.
        conn.execute(
            """CREATE TABLE IF NOT EXISTS workspace_workflow_reviews (
                workspace_id TEXT NOT NULL,
                workflow_id TEXT NOT NULL,
                revision INTEGER NOT NULL CHECK(revision >= 1),
                state TEXT NOT NULL CHECK(state IN ('approved', 'rejected')),
                reviewer TEXT NOT NULL,
                updated_at INTEGER NOT NULL,
                PRIMARY KEY(workspace_id, workflow_id)
            )"""
        )

    def set(self, review: WorkflowReview) -> None:
        if review.state not in {"approved", "rejected"}:
            raise ValueError("Workflow review state must be approved or rejected")
        with connect_state_db(self.db_path, ensure_parent=True) as conn:
            self._ensure(conn)
            conn.execute(
                """INSERT INTO workspace_workflow_reviews
                (workspace_id, workflow_id, revision, state, reviewer, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(workspace_id, workflow_id) DO UPDATE SET
                    revision=excluded.revision, state=excluded.state,
                    reviewer=excluded.reviewer, updated_at=excluded.updated_at""",
                (
                    review.workspace_id,
                    review.workflow_id,
                    review.revision,
                    review.state,
                    review.reviewer,
                    review.updated_at,
                ),
            )

    def get(self, workspace_id: str, workflow_id: str) -> WorkflowReview | None:
        with connect_state_db(self.db_path, ensure_parent=True) as conn:
            self._ensure(conn)
            row = conn.execute(
                "SELECT * FROM workspace_workflow_reviews WHERE workspace_id=? AND workflow_id=?",
                (workspace_id, workflow_id),
            ).fetchone()
        return WorkflowReview(**dict(row)) if row else None

    def approved(self, workspace_id: str, workflow_id: str, revision: int) -> bool:
        with connect_state_db(self.db_path, ensure_parent=True) as conn:
            self._ensure(conn)
            row = conn.execute(
                "SELECT state, revision FROM workspace_workflow_reviews WHERE workspace_id=? AND workflow_id=?",
                (workspace_id, workflow_id),
            ).fetchone()
        return (
            row is not None
            and row["state"] == "approved"
            and row["revision"] == revision
        )
