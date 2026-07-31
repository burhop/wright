"""Transactional revocation across presentation and capability authority."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

from data_vault import connect_state_db


@dataclass(frozen=True, slots=True)
class RevocationResult:
    presentations: int
    grants: int
    revoked_at: datetime


class RevocationCoordinator:
    def __init__(
        self,
        db_path: str | Path,
        *,
        clock=lambda: datetime.now(UTC),
    ) -> None:
        self.db_path = str(db_path)
        self.clock = clock

    def _revoke(
        self,
        *,
        presentation_scope: str,
        presentation_parameters: Sequence[str],
        grant_scope: str | None,
        grant_parameters: Sequence[str] = (),
    ) -> RevocationResult:
        now = self.clock()
        with connect_state_db(self.db_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                presentations = connection.execute(
                    """UPDATE surface_presentations
                    SET state='closed', bootstrap_nonce_hash=NULL,
                        presentation_cookie_hash=NULL, closed_at=?
                    WHERE state NOT IN ('closed', 'expired') AND """
                    + presentation_scope,
                    (now.isoformat(), *presentation_parameters),
                ).rowcount
                grants = 0
                if grant_scope is not None:
                    grants = connection.execute(
                        """UPDATE surface_capability_grants SET revoked_at=?
                        WHERE revoked_at IS NULL AND """
                        + grant_scope,
                        (now.isoformat(), *grant_parameters),
                    ).rowcount
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return RevocationResult(
            presentations=presentations,
            grants=grants,
            revoked_at=now,
        )

    def presentation_disposed(
        self,
        *,
        workspace_id: str,
        user_id: str,
        presentation_id: str,
    ) -> RevocationResult:
        return self._revoke(
            presentation_scope="workspace_id=? AND user_id=? AND presentation_id=?",
            presentation_parameters=(workspace_id, user_id, presentation_id),
            grant_scope=None,
        )

    def runtime_replaced(
        self, *, workspace_id: str, instance_id: str
    ) -> RevocationResult:
        return self._revoke(
            presentation_scope="workspace_id=? AND instance_id=?",
            presentation_parameters=(workspace_id, instance_id),
            grant_scope="workspace_id=? AND instance_id=?",
            grant_parameters=(workspace_id, instance_id),
        )

    def logout(self, *, workspace_id: str, user_id: str) -> RevocationResult:
        return self._revoke(
            presentation_scope="workspace_id=? AND user_id=?",
            presentation_parameters=(workspace_id, user_id),
            grant_scope="workspace_id=? AND user_id=?",
            grant_parameters=(workspace_id, user_id),
        )

    def user_logout(self, *, user_id: str) -> RevocationResult:
        return self._revoke(
            presentation_scope="user_id=?",
            presentation_parameters=(user_id,),
            grant_scope="user_id=?",
            grant_parameters=(user_id,),
        )

    def workspace_closed(self, *, workspace_id: str) -> RevocationResult:
        return self._revoke(
            presentation_scope="workspace_id=?",
            presentation_parameters=(workspace_id,),
            grant_scope="workspace_id=?",
            grant_parameters=(workspace_id,),
        )


__all__ = ["RevocationCoordinator", "RevocationResult"]
