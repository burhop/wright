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
    workflow_digest: str | None = None
    graph_id: str | None = None
    binding_set_id: str | None = None
    binding_set_digest: str | None = None
    policy_snapshot_digest: str | None = None
    review_digest: str | None = None


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
                workflow_digest TEXT,
                graph_id TEXT,
                binding_set_id TEXT,
                binding_set_digest TEXT,
                policy_snapshot_digest TEXT,
                review_digest TEXT,
                PRIMARY KEY(workspace_id, workflow_id)
            )"""
        )
        columns = {
            str(row[1])
            for row in conn.execute("PRAGMA table_info(workspace_workflow_reviews)")
        }
        additions = {
            "workflow_digest": "TEXT",
            "graph_id": "TEXT",
            "binding_set_id": "TEXT",
            "binding_set_digest": "TEXT",
            "policy_snapshot_digest": "TEXT",
            "review_digest": "TEXT",
        }
        for name, definition in additions.items():
            if name not in columns:
                conn.execute(
                    f'ALTER TABLE workspace_workflow_reviews ADD COLUMN "{name}" {definition}'
                )

    def set(self, review: WorkflowReview) -> None:
        if review.state not in {"approved", "rejected"}:
            raise ValueError("Workflow review state must be approved or rejected")
        with connect_state_db(self.db_path, ensure_parent=True) as conn:
            self._ensure(conn)
            conn.execute(
                """INSERT INTO workspace_workflow_reviews
                (workspace_id, workflow_id, revision, state, reviewer, updated_at,
                 workflow_digest, graph_id, binding_set_id, binding_set_digest,
                 policy_snapshot_digest, review_digest)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(workspace_id, workflow_id) DO UPDATE SET
                    revision=excluded.revision, state=excluded.state,
                    reviewer=excluded.reviewer, updated_at=excluded.updated_at,
                    workflow_digest=excluded.workflow_digest,
                    graph_id=excluded.graph_id,
                    binding_set_id=excluded.binding_set_id,
                    binding_set_digest=excluded.binding_set_digest,
                    policy_snapshot_digest=excluded.policy_snapshot_digest,
                    review_digest=excluded.review_digest""",
                (
                    review.workspace_id,
                    review.workflow_id,
                    review.revision,
                    review.state,
                    review.reviewer,
                    review.updated_at,
                    review.workflow_digest,
                    review.graph_id,
                    review.binding_set_id,
                    review.binding_set_digest,
                    review.policy_snapshot_digest,
                    review.review_digest,
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

    def approved_exact(
        self,
        workspace_id: str,
        workflow_id: str,
        revision: int,
        *,
        workflow_digest: str,
        graph_id: str,
        binding_set_digest: str,
        review_digest: str | None = None,
    ) -> bool:
        review = self.get(workspace_id, workflow_id)
        return bool(
            review is not None
            and review.state == "approved"
            and review.revision == revision
            and review.workflow_digest == workflow_digest
            and review.graph_id == graph_id
            and review.binding_set_digest == binding_set_digest
            and (review_digest is None or review.review_digest == review_digest)
        )
