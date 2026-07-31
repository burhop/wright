"""Execution-scoped display authority for workspace Python runs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from ..surfaces.display_tokens import (
    DisplayExecutionClaims,
    DisplayExecutionTokenService,
)


@dataclass(slots=True)
class DisplayExecutionLease:
    token_service: DisplayExecutionTokenService
    claims: DisplayExecutionClaims
    endpoint: str
    token: str
    contract_version: int = 1
    _revoked: bool = False

    def environment(self) -> dict[str, str]:
        return {
            "WRIGHT_DISPLAY_ENDPOINT": self.endpoint,
            "WRIGHT_DISPLAY_TOKEN": self.token,
            "WRIGHT_DISPLAY_WORKSPACE_ID": self.claims.workspace_id,
            "WRIGHT_DISPLAY_CONTRACT": str(self.contract_version),
        }

    def revoke(self) -> None:
        if not self._revoked:
            self._revoked = True
            self.token_service.revoke_execution(self.claims.execution_id)


def issue_display_execution_lease(
    *,
    token_service: DisplayExecutionTokenService,
    endpoint: str,
    user_id: str,
    workspace_id: str,
    session_id: str,
    task_id: str,
    execution_id: str,
    prompt: str | None,
    effective_constraints: dict[str, Any],
    script: str,
    script_revision: int,
    trace_id: str,
    lifetime_seconds: float,
    clock=lambda: datetime.now(UTC),
) -> DisplayExecutionLease:
    expires_at = clock() + timedelta(seconds=max(1.0, lifetime_seconds))
    claims = DisplayExecutionClaims(
        audience="wright-display-ingest-v1",
        user_id=user_id,
        workspace_id=workspace_id,
        session_id=session_id,
        task_id=task_id,
        execution_id=execution_id,
        expires_at=expires_at,
        prompt=prompt,
        effective_constraints=dict(effective_constraints),
        script=script,
        script_revision=script_revision,
        trace_id=trace_id,
    )
    return DisplayExecutionLease(
        token_service=token_service,
        claims=claims,
        endpoint=endpoint,
        token=token_service.issue(claims),
    )
