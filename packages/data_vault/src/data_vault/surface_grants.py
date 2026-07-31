"""Transactional persistence operations for Workspace Surface grants."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from .state_store import connect_state_db
from .surface_repository import (
    SurfaceGrantRecord,
    SurfaceGrantRepository as _BaseSurfaceGrantRepository,
    _grant_from_row,
)


class SurfaceGrantRepository(_BaseSurfaceGrantRepository):
    def get(
        self, *, grant_id: str, user_id: str, workspace_id: str
    ) -> SurfaceGrantRecord | None:
        with self.tracer.start_as_current_span(
            "surface.sqlite.grant.get",
            attributes=self._attributes(workspace_id),
        ):
            with connect_state_db(self.db_path) as connection:
                row = connection.execute(
                    """SELECT * FROM surface_capability_grants
                    WHERE grant_id=? AND user_id=? AND workspace_id=?""",
                    (grant_id, user_id, workspace_id),
                ).fetchone()
        return _grant_from_row(row) if row is not None else None

    def consume_operation(
        self,
        record: SurfaceGrantRecord,
        *,
        used_at: datetime,
    ) -> SurfaceGrantRecord | None:
        with self.tracer.start_as_current_span(
            "surface.sqlite.grant.consume",
            attributes=self._attributes(record.workspace_id),
        ):
            with connect_state_db(self.db_path) as connection:
                cursor = connection.execute(
                    """UPDATE surface_capability_grants SET used_at=?
                    WHERE grant_id=? AND user_id=? AND workspace_id=?
                      AND persistence='operation' AND used_at IS NULL
                      AND revoked_at IS NULL
                      AND (expires_at IS NULL OR expires_at>=?)""",
                    (
                        used_at.isoformat(),
                        record.grant_id,
                        record.user_id,
                        record.workspace_id,
                        used_at.isoformat(),
                    ),
                )
                if cursor.rowcount != 1:
                    connection.rollback()
                    return None
                connection.commit()
        return replace(record, used_at=used_at)

    def revoke(
        self,
        record: SurfaceGrantRecord,
        *,
        revoked_at: datetime,
    ) -> SurfaceGrantRecord:
        if record.revoked_at is not None:
            return record
        with self.tracer.start_as_current_span(
            "surface.sqlite.grant.revoke",
            attributes=self._attributes(record.workspace_id),
        ):
            with connect_state_db(self.db_path) as connection:
                cursor = connection.execute(
                    """UPDATE surface_capability_grants SET revoked_at=?
                    WHERE grant_id=? AND user_id=? AND workspace_id=?
                      AND revoked_at IS NULL""",
                    (
                        revoked_at.isoformat(),
                        record.grant_id,
                        record.user_id,
                        record.workspace_id,
                    ),
                )
                if cursor.rowcount != 1:
                    raise KeyError(record.grant_id)
                connection.commit()
        return replace(record, revoked_at=revoked_at)

    def revoke_scope(
        self,
        *,
        workspace_id: str,
        revoked_at: datetime,
        user_id: str | None = None,
        source_id: str | None = None,
        instance_id: str | None = None,
    ) -> int:
        clauses = ["workspace_id=?", "revoked_at IS NULL"]
        parameters: list[str] = [workspace_id]
        for column, value in (
            ("user_id", user_id),
            ("source_id", source_id),
            ("instance_id", instance_id),
        ):
            if value is not None:
                clauses.append(f"{column}=?")
                parameters.append(value)
        with self.tracer.start_as_current_span(
            "surface.sqlite.grant.revoke_scope",
            attributes=self._attributes(workspace_id),
        ):
            with connect_state_db(self.db_path) as connection:
                cursor = connection.execute(
                    "UPDATE surface_capability_grants SET revoked_at=? WHERE "
                    + " AND ".join(clauses),
                    (revoked_at.isoformat(), *parameters),
                )
                connection.commit()
                return cursor.rowcount


__all__ = ["SurfaceGrantRecord", "SurfaceGrantRepository"]
