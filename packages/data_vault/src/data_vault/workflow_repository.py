"""Rebuildable metadata index for workspace-authored workflow files."""

from __future__ import annotations

import time
from dataclasses import dataclass

from .state_store import connect_state_db


@dataclass(frozen=True, slots=True)
class WorkflowIndexRecord:
    workspace_id: str
    workflow_id: str
    slug: str
    revision: int
    digest: str
    state: str
    updated_at: int


class WorkflowRepository:
    """Stores metadata only; project and dataset content never enter SQLite."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def _ensure(self, conn) -> None:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS workspace_workflows (
                workspace_id TEXT NOT NULL,
                workflow_id TEXT NOT NULL,
                slug TEXT NOT NULL,
                revision INTEGER NOT NULL,
                digest TEXT NOT NULL,
                state TEXT NOT NULL DEFAULT 'active',
                updated_at INTEGER NOT NULL,
                PRIMARY KEY (workspace_id, workflow_id),
                UNIQUE (workspace_id, slug)
            )"""
        )

    def upsert(self, record: WorkflowIndexRecord) -> None:
        with connect_state_db(self.db_path, ensure_parent=True) as conn:
            self._ensure(conn)
            conn.execute(
                """INSERT INTO workspace_workflows
                (workspace_id, workflow_id, slug, revision, digest, state, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(workspace_id, workflow_id) DO UPDATE SET
                    slug=excluded.slug, revision=excluded.revision, digest=excluded.digest,
                    state=excluded.state, updated_at=excluded.updated_at""",
                (record.workspace_id, record.workflow_id, record.slug, record.revision,
                 record.digest, record.state, record.updated_at),
            )

    def list(self, workspace_id: str, *, include_deleted: bool = False) -> list[WorkflowIndexRecord]:
        with connect_state_db(self.db_path, ensure_parent=True) as conn:
            self._ensure(conn)
            clause = "" if include_deleted else " AND state = 'active'"
            rows = conn.execute(
                "SELECT * FROM workspace_workflows WHERE workspace_id = ?" + clause + " ORDER BY slug",
                (workspace_id,),
            ).fetchall()
        return [WorkflowIndexRecord(**dict(row)) for row in rows]

    def mark_deleted(self, workspace_id: str, workflow_id: str) -> None:
        with connect_state_db(self.db_path, ensure_parent=True) as conn:
            self._ensure(conn)
            conn.execute("UPDATE workspace_workflows SET state='deleted', updated_at=? WHERE workspace_id=? AND workflow_id=?", (int(time.time()), workspace_id, workflow_id))
