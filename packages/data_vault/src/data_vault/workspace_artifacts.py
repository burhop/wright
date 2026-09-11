"""Immutable records for workspace-confined workflow artifacts."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime

from core.rivet_mcp import canonical_digest

from .state_store import connect_state_db


class WorkspaceArtifactConflict(ValueError):
    """Raised when an immutable artifact identity is reused inconsistently."""


@dataclass(frozen=True, slots=True)
class WorkspaceArtifactRecord:
    artifact_id: str
    workspace_id: str
    session_id: str
    principal_id: str
    relative_path: str
    media_type: str
    sha256: str
    byte_count: int
    producer_provider_id: str
    producer_tool_name: str
    producer_declaration_digest: str
    request_id: str
    correlation_id: str
    created_at: datetime

    def digest_material(self) -> dict[str, object]:
        return {
            "artifact_id": self.artifact_id,
            "workspace_id": self.workspace_id,
            "session_id": self.session_id,
            "principal_id": self.principal_id,
            "relative_path": self.relative_path,
            "media_type": self.media_type,
            "sha256": self.sha256,
            "byte_count": self.byte_count,
            "producer_provider_id": self.producer_provider_id,
            "producer_tool_name": self.producer_tool_name,
            "producer_declaration_digest": self.producer_declaration_digest,
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "created_at": _epoch(self.created_at),
        }

    @property
    def record_digest(self) -> str:
        return canonical_digest(self.digest_material())


def _epoch(value: datetime) -> int:
    return int(value.astimezone(UTC).timestamp())


def _record(row) -> WorkspaceArtifactRecord:
    return WorkspaceArtifactRecord(
        artifact_id=str(row["artifact_id"]),
        workspace_id=str(row["workspace_id"]),
        session_id=str(row["session_id"]),
        principal_id=str(row["principal_id"]),
        relative_path=str(row["relative_path"]),
        media_type=str(row["media_type"]),
        sha256=str(row["sha256"]),
        byte_count=int(row["byte_count"]),
        producer_provider_id=str(row["producer_provider_id"]),
        producer_tool_name=str(row["producer_tool_name"]),
        producer_declaration_digest=str(row["producer_declaration_digest"]),
        request_id=str(row["request_id"]),
        correlation_id=str(row["correlation_id"]),
        created_at=datetime.fromtimestamp(int(row["created_at"]), tz=UTC),
    )


class WorkspaceArtifactRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def insert(self, record: WorkspaceArtifactRecord) -> None:
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT * FROM workspace_artifacts WHERE artifact_id=?",
                (record.artifact_id,),
            ).fetchone()
            if existing is not None:
                if _record(existing).record_digest != record.record_digest:
                    raise WorkspaceArtifactConflict("Artifact identity is immutable")
                connection.rollback()
                return
            try:
                connection.execute(
                    """INSERT INTO workspace_artifacts
                    (artifact_id, workspace_id, session_id, principal_id,
                     relative_path, media_type, sha256, byte_count,
                     producer_provider_id, producer_tool_name,
                     producer_declaration_digest, request_id, correlation_id,
                     record_digest, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        record.artifact_id,
                        record.workspace_id,
                        record.session_id,
                        record.principal_id,
                        record.relative_path,
                        record.media_type,
                        record.sha256,
                        record.byte_count,
                        record.producer_provider_id,
                        record.producer_tool_name,
                        record.producer_declaration_digest,
                        record.request_id,
                        record.correlation_id,
                        record.record_digest,
                        _epoch(record.created_at),
                    ),
                )
                connection.commit()
            except sqlite3.IntegrityError as error:
                connection.rollback()
                raise WorkspaceArtifactConflict(
                    "Artifact target is already registered"
                ) from error

    def get(
        self, artifact_id: str, *, workspace_id: str
    ) -> WorkspaceArtifactRecord | None:
        with connect_state_db(self.db_path, read_only=True) as connection:
            row = connection.execute(
                """SELECT * FROM workspace_artifacts
                WHERE artifact_id=? AND workspace_id=?""",
                (artifact_id, workspace_id),
            ).fetchone()
        return _record(row) if row is not None else None

    def list_for_scope(
        self, *, workspace_id: str, session_id: str, limit: int = 100
    ) -> tuple[WorkspaceArtifactRecord, ...]:
        bounded = max(1, min(int(limit), 100))
        with connect_state_db(self.db_path, read_only=True) as connection:
            rows = connection.execute(
                """SELECT * FROM workspace_artifacts
                WHERE workspace_id=? AND session_id=?
                ORDER BY created_at DESC, artifact_id DESC LIMIT ?""",
                (workspace_id, session_id, bounded),
            ).fetchall()
        return tuple(_record(row) for row in rows)

    def link_run(
        self,
        *,
        artifact_id: str,
        workspace_id: str,
        session_id: str,
        run_id: str,
        linked_at: datetime,
    ) -> None:
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            connection.execute("BEGIN IMMEDIATE")
            record = connection.execute(
                """SELECT session_id FROM workspace_artifacts
                WHERE artifact_id=? AND workspace_id=?""",
                (artifact_id, workspace_id),
            ).fetchone()
            run = connection.execute(
                """SELECT session_id FROM workspace_workflow_runs
                WHERE run_id=? AND workspace_id=?""",
                (run_id, workspace_id),
            ).fetchone()
            if (
                record is None
                or run is None
                or str(record["session_id"]) != session_id
                or str(run["session_id"]) != session_id
            ):
                connection.rollback()
                raise WorkspaceArtifactConflict("Artifact run scope is invalid")
            existing = connection.execute(
                "SELECT run_id FROM workspace_run_artifacts WHERE artifact_id=?",
                (artifact_id,),
            ).fetchone()
            if existing is not None:
                if str(existing["run_id"]) != run_id:
                    connection.rollback()
                    raise WorkspaceArtifactConflict("Artifact run linkage is immutable")
                connection.rollback()
                return
            connection.execute(
                """INSERT INTO workspace_run_artifacts
                (run_id, artifact_id, linked_at) VALUES (?, ?, ?)""",
                (run_id, artifact_id, _epoch(linked_at)),
            )
            connection.commit()

    def get_for_run(
        self,
        *,
        workspace_id: str,
        session_id: str,
        run_id: str,
        artifact_id: str,
    ) -> WorkspaceArtifactRecord | None:
        with connect_state_db(self.db_path, read_only=True) as connection:
            row = connection.execute(
                """SELECT a.* FROM workspace_artifacts AS a
                JOIN workspace_run_artifacts AS ra
                  ON ra.artifact_id=a.artifact_id
                JOIN workspace_workflow_runs AS r ON r.run_id=ra.run_id
                WHERE a.artifact_id=? AND a.workspace_id=? AND a.session_id=?
                  AND ra.run_id=? AND r.workspace_id=? AND r.session_id=?""",
                (
                    artifact_id,
                    workspace_id,
                    session_id,
                    run_id,
                    workspace_id,
                    session_id,
                ),
            ).fetchone()
        return _record(row) if row is not None else None
