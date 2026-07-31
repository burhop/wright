"""Scoped persistence for ephemeral Workspace Surface presentation authority."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

from opentelemetry import trace

from .state_store import connect_state_db


@dataclass(frozen=True, slots=True)
class SurfacePresentationRecord:
    presentation_id: str
    instance_id: str
    surface_id: str
    workspace_id: str
    user_id: str
    session_id: str
    kind: str
    state: str
    generation: int
    source_id: str
    source_version: str
    effective_origin: str
    bootstrap_nonce_hash: str | None
    cookie_audience: str
    idempotency_key: str
    created_at: datetime
    bootstrap_expires_at: datetime
    expires_at: datetime
    presentation_cookie_hash: str | None = None
    last_seen_at: datetime | None = None
    closed_at: datetime | None = None


def _from_row(row) -> SurfacePresentationRecord:
    return SurfacePresentationRecord(
        presentation_id=row["presentation_id"],
        instance_id=row["instance_id"],
        surface_id=row["surface_id"],
        workspace_id=row["workspace_id"],
        user_id=row["user_id"],
        session_id=row["session_id"],
        kind=row["kind"],
        state=row["state"],
        generation=int(row["generation"]),
        source_id=row["source_id"],
        source_version=row["source_version"],
        effective_origin=row["effective_origin"],
        bootstrap_nonce_hash=row["bootstrap_nonce_hash"],
        cookie_audience=row["cookie_audience"],
        idempotency_key=row["idempotency_key"],
        created_at=datetime.fromisoformat(row["created_at"]),
        bootstrap_expires_at=datetime.fromisoformat(
            row["bootstrap_expires_at"] or row["expires_at"]
        ),
        expires_at=datetime.fromisoformat(row["expires_at"]),
        presentation_cookie_hash=row["presentation_cookie_hash"],
        last_seen_at=(
            datetime.fromisoformat(row["last_seen_at"]) if row["last_seen_at"] else None
        ),
        closed_at=(
            datetime.fromisoformat(row["closed_at"]) if row["closed_at"] else None
        ),
    )


class SurfacePresentationRepository:
    def __init__(self, db_path: str | Path, *, tracer=None) -> None:
        self.db_path = str(db_path)
        self.tracer = tracer or trace.get_tracer(__name__)

    def create(self, record: SurfacePresentationRecord) -> SurfacePresentationRecord:
        with self.tracer.start_as_current_span(
            "surface.sqlite.presentation.create",
            attributes={"wright.workspace_id": record.workspace_id},
        ):
            with connect_state_db(self.db_path) as connection:
                try:
                    connection.execute(
                        """INSERT INTO surface_presentations (
                            presentation_id, instance_id, surface_id, workspace_id,
                            user_id, session_id, kind, state, generation, source_id,
                            source_version, effective_origin, bootstrap_nonce_hash,
                            cookie_audience, idempotency_key, created_at, last_seen_at,
                            bootstrap_expires_at, expires_at,
                            presentation_cookie_hash, closed_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            record.presentation_id,
                            record.instance_id,
                            record.surface_id,
                            record.workspace_id,
                            record.user_id,
                            record.session_id,
                            record.kind,
                            record.state,
                            record.generation,
                            record.source_id,
                            record.source_version,
                            record.effective_origin,
                            record.bootstrap_nonce_hash,
                            record.cookie_audience,
                            record.idempotency_key,
                            record.created_at.isoformat(),
                            record.last_seen_at.isoformat()
                            if record.last_seen_at
                            else None,
                            record.bootstrap_expires_at.isoformat(),
                            record.expires_at.isoformat(),
                            record.presentation_cookie_hash,
                            record.closed_at.isoformat() if record.closed_at else None,
                        ),
                    )
                    connection.commit()
                except sqlite3.IntegrityError:
                    connection.rollback()
                    raise
        return record

    def get(
        self,
        presentation_id: str,
        *,
        user_id: str,
        workspace_id: str,
        session_id: str,
    ) -> SurfacePresentationRecord | None:
        with self.tracer.start_as_current_span(
            "surface.sqlite.presentation.get",
            attributes={"wright.workspace_id": workspace_id},
        ):
            with connect_state_db(self.db_path) as connection:
                row = connection.execute(
                    """SELECT * FROM surface_presentations
                    WHERE presentation_id=? AND user_id=? AND workspace_id=?
                      AND session_id=?""",
                    (presentation_id, user_id, workspace_id, session_id),
                ).fetchone()
        return _from_row(row) if row else None

    def get_by_idempotency(
        self,
        *,
        user_id: str,
        workspace_id: str,
        session_id: str,
        idempotency_key: str,
    ) -> SurfacePresentationRecord | None:
        with self.tracer.start_as_current_span(
            "surface.sqlite.presentation.get_by_idempotency",
            attributes={"wright.workspace_id": workspace_id},
        ):
            with connect_state_db(self.db_path) as connection:
                row = connection.execute(
                    """SELECT * FROM surface_presentations
                    WHERE user_id=? AND workspace_id=? AND session_id=?
                      AND idempotency_key=?""",
                    (user_id, workspace_id, session_id, idempotency_key),
                ).fetchone()
        return _from_row(row) if row else None

    def rotate_bootstrap(
        self,
        record: SurfacePresentationRecord,
        *,
        bootstrap_nonce_hash: str,
        bootstrap_expires_at: datetime,
    ) -> SurfacePresentationRecord:
        if record.state in {"closed", "expired"}:
            raise ValueError("closed presentation authority cannot be rotated")
        updated = replace(
            record,
            bootstrap_nonce_hash=bootstrap_nonce_hash,
            bootstrap_expires_at=bootstrap_expires_at,
        )
        with self.tracer.start_as_current_span(
            "surface.sqlite.presentation.rotate_bootstrap",
            attributes={"wright.workspace_id": record.workspace_id},
        ):
            with connect_state_db(self.db_path) as connection:
                cursor = connection.execute(
                    """UPDATE surface_presentations
                    SET bootstrap_nonce_hash=?, bootstrap_expires_at=?
                    WHERE presentation_id=? AND user_id=? AND workspace_id=?
                      AND session_id=? AND state NOT IN ('closed', 'expired')""",
                    (
                        bootstrap_nonce_hash,
                        bootstrap_expires_at.isoformat(),
                        record.presentation_id,
                        record.user_id,
                        record.workspace_id,
                        record.session_id,
                    ),
                )
                if cursor.rowcount != 1:
                    raise KeyError(record.presentation_id)
                connection.commit()
        return updated

    def get_for_preview(self, presentation_id: str) -> SurfacePresentationRecord | None:
        """Resolve opaque preview authority without crossing its host audience."""
        with self.tracer.start_as_current_span(
            "surface.sqlite.presentation.preview_get"
        ):
            with connect_state_db(self.db_path) as connection:
                row = connection.execute(
                    "SELECT * FROM surface_presentations WHERE presentation_id=?",
                    (presentation_id,),
                ).fetchone()
        return _from_row(row) if row else None

    def activate_with_cookie(
        self,
        record: SurfacePresentationRecord,
        *,
        expected_bootstrap_hash: str,
        presentation_cookie_hash: str,
        activated_at: datetime,
    ) -> SurfacePresentationRecord | None:
        """Atomically consume a bootstrap token and establish cookie authority."""
        with self.tracer.start_as_current_span(
            "surface.sqlite.presentation.activate",
            attributes={"wright.workspace_id": record.workspace_id},
        ):
            with connect_state_db(self.db_path) as connection:
                cursor = connection.execute(
                    """UPDATE surface_presentations
                    SET state='active', bootstrap_nonce_hash=NULL,
                        presentation_cookie_hash=?, last_seen_at=?
                    WHERE presentation_id=?
                      AND state IN ('issued', 'inactive')
                      AND bootstrap_nonce_hash=?
                      AND bootstrap_expires_at>=?
                      AND expires_at>=?""",
                    (
                        presentation_cookie_hash,
                        activated_at.isoformat(),
                        record.presentation_id,
                        expected_bootstrap_hash,
                        activated_at.isoformat(),
                        activated_at.isoformat(),
                    ),
                )
                if cursor.rowcount != 1:
                    connection.rollback()
                    return None
                connection.commit()
                row = connection.execute(
                    "SELECT * FROM surface_presentations WHERE presentation_id=?",
                    (record.presentation_id,),
                ).fetchone()
        return _from_row(row) if row else None

    def close(
        self, record: SurfacePresentationRecord, *, closed_at: datetime
    ) -> SurfacePresentationRecord:
        if record.state == "closed":
            return record
        updated = replace(
            record,
            state="closed",
            bootstrap_nonce_hash=None,
            presentation_cookie_hash=None,
            closed_at=closed_at,
        )
        with self.tracer.start_as_current_span(
            "surface.sqlite.presentation.close",
            attributes={"wright.workspace_id": record.workspace_id},
        ):
            with connect_state_db(self.db_path) as connection:
                cursor = connection.execute(
                    """UPDATE surface_presentations
                    SET state='closed', bootstrap_nonce_hash=NULL,
                        presentation_cookie_hash=NULL, closed_at=?
                    WHERE presentation_id=? AND user_id=? AND workspace_id=?
                      AND session_id=?""",
                    (
                        closed_at.isoformat(),
                        record.presentation_id,
                        record.user_id,
                        record.workspace_id,
                        record.session_id,
                    ),
                )
                if cursor.rowcount != 1:
                    raise KeyError(record.presentation_id)
                connection.commit()
        return updated

    def list_for_surface(
        self,
        *,
        surface_id: str,
        user_id: str,
        workspace_id: str,
        session_id: str,
    ) -> list[SurfacePresentationRecord]:
        with self.tracer.start_as_current_span(
            "surface.sqlite.presentation.list",
            attributes={"wright.workspace_id": workspace_id},
        ):
            with connect_state_db(self.db_path) as connection:
                rows = connection.execute(
                    """SELECT * FROM surface_presentations
                    WHERE surface_id=? AND user_id=? AND workspace_id=?
                      AND session_id=? ORDER BY created_at, presentation_id""",
                    (surface_id, user_id, workspace_id, session_id),
                ).fetchall()
        return [_from_row(row) for row in rows]
