"""Short-lived opaque execution tokens for display ingestion."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock
from typing import Any


class DisplayTokenRejected(PermissionError):
    """The bearer is invalid, expired, revoked, or outside its exact scope."""


@dataclass(frozen=True, slots=True)
class DisplayExecutionClaims:
    audience: str
    user_id: str
    workspace_id: str
    session_id: str
    task_id: str
    execution_id: str
    expires_at: datetime
    prompt: str | None
    effective_constraints: dict[str, Any]
    script: str
    script_revision: int
    trace_id: str

    def __post_init__(self) -> None:
        if self.expires_at.tzinfo is None:
            raise ValueError("display token expiry must be timezone-aware")
        if self.script_revision < 1:
            raise ValueError("script revision must be positive")


class DisplayExecutionTokenService:
    """Issues opaque signed handles; protected provenance stays server-side."""

    def __init__(self, *, secret: bytes, clock=lambda: datetime.now(UTC)) -> None:
        if len(secret) < 32:
            raise ValueError("display token secret must contain at least 32 bytes")
        self._secret = bytes(secret)
        self._clock = clock
        self._claims: dict[str, DisplayExecutionClaims] = {}
        self._revoked_executions: set[str] = set()
        self._lock = RLock()

    @staticmethod
    def generate_secret() -> bytes:
        return secrets.token_bytes(32)

    def _signature(self, token_id: str) -> str:
        return hmac.new(
            self._secret, token_id.encode("ascii"), hashlib.sha256
        ).hexdigest()

    def issue(self, claims: DisplayExecutionClaims) -> str:
        token_id = secrets.token_hex(24)
        with self._lock:
            self._claims[token_id] = claims
        return f"v1.{token_id}.{self._signature(token_id)}"

    def validate(
        self,
        token: str,
        *,
        audience: str,
        workspace_id: str,
    ) -> DisplayExecutionClaims:
        try:
            version, token_id, signature = token.split(".", 2)
        except ValueError as error:
            raise DisplayTokenRejected("Malformed display token") from error
        if version != "v1" or not hmac.compare_digest(
            signature, self._signature(token_id)
        ):
            raise DisplayTokenRejected("Invalid display token")
        with self._lock:
            claims = self._claims.get(token_id)
            revoked = bool(
                claims and claims.execution_id in self._revoked_executions
            )
        if claims is None or revoked:
            raise DisplayTokenRejected("Display token is unknown or revoked")
        if claims.expires_at <= self._clock():
            raise DisplayTokenRejected("Display token expired")
        if claims.audience != audience or claims.workspace_id != workspace_id:
            raise DisplayTokenRejected("Display token audience or workspace mismatch")
        return claims

    def revoke_execution(self, execution_id: str) -> None:
        with self._lock:
            self._revoked_executions.add(execution_id)
