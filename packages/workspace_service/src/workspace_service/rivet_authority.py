"""Memory-only, audience-bound authority for one reviewed Rivet run."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from typing import Callable, Mapping


class RivetAuthorityError(PermissionError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class AuthorityState(StrEnum):
    ISSUED = "issued"
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    TERMINAL = "terminal"


@dataclass(frozen=True)
class AuthorityClaims:
    run_id: str
    generation: int
    workspace_id: str
    session_id: str
    workflow_id: str
    workflow_revision: int
    workflow_digest: str
    graph_id: str
    review_digest: str
    binding_set_digest: str
    audience: str
    node_bindings: Mapping[str, str]
    issued_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        if not self.audience.startswith("http://127.0.0.1:"):
            raise ValueError("Rivet authority audience must be exact loopback HTTP")
        if self.expires_at <= self.issued_at:
            raise ValueError("Rivet authority expiry is invalid")
        if self.generation < 1 or self.workflow_revision < 1:
            raise ValueError("Rivet authority revision is invalid")
        if len(set(self.node_bindings)) != len(self.node_bindings):
            raise ValueError("Rivet authority node handles must be unique")


@dataclass(frozen=True, slots=True)
class AuthorityRecord:
    authority_id: str
    token_digest: str
    claims: AuthorityClaims
    state: AuthorityState = AuthorityState.ISSUED
    revoked_at: datetime | None = None
    terminal_at: datetime | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class IssuedAuthority:
    authority_id: str
    token: str
    token_digest: str
    claims: AuthorityClaims


class RivetRunAuthorityService:
    """Holds only token digests; restart is implicit revocation."""

    def __init__(
        self,
        *,
        clock: Callable[[], datetime] | None = None,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._clock = clock or (lambda: datetime.now(UTC))
        self._id_factory = id_factory or (lambda: str(uuid.uuid4()))
        self._records_by_id: dict[str, AuthorityRecord] = {}
        self._authority_by_digest: dict[str, str] = {}

    @staticmethod
    def token_digest(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def mint(self, claims: AuthorityClaims) -> IssuedAuthority:
        now = self._clock()
        if claims.issued_at > now or claims.expires_at <= now:
            raise RivetAuthorityError(
                "RIVET_MCP_AUTHORITY_TIME_INVALID",
                "Rivet run authority lifetime is unavailable",
            )
        token = secrets.token_urlsafe(32)
        digest = self.token_digest(token)
        authority_id = self._id_factory()
        record = AuthorityRecord(authority_id, digest, claims)
        self._records_by_id[authority_id] = record
        self._authority_by_digest[digest] = authority_id
        return IssuedAuthority(authority_id, token, digest, claims)

    def snapshot(self, authority_id: str) -> AuthorityRecord | None:
        return self._records_by_id.get(authority_id)

    def validate(
        self,
        token: str,
        *,
        audience: str,
        run_id: str,
        generation: int,
        node_handle: str | None = None,
        binding_digest: str | None = None,
    ) -> AuthorityRecord:
        digest = self.token_digest(token)
        authority_id = self._authority_by_digest.get(digest)
        record = self._records_by_id.get(authority_id or "")
        if record is None or not secrets.compare_digest(record.token_digest, digest):
            raise RivetAuthorityError(
                "RIVET_MCP_AUTHORITY_UNAVAILABLE", "Rivet run authority is unavailable"
            )
        now = self._clock()
        if now >= record.claims.expires_at:
            expired = replace(record, state=AuthorityState.EXPIRED, reason="expired")
            self._records_by_id[record.authority_id] = expired
            raise RivetAuthorityError(
                "RIVET_MCP_AUTHORITY_EXPIRED", "Rivet run authority expired"
            )
        if record.state is AuthorityState.REVOKED:
            raise RivetAuthorityError(
                "RIVET_MCP_AUTHORITY_REVOKED", "Rivet run authority was revoked"
            )
        if record.state in {AuthorityState.EXPIRED, AuthorityState.TERMINAL}:
            raise RivetAuthorityError(
                "RIVET_MCP_AUTHORITY_UNAVAILABLE", "Rivet run authority is unavailable"
            )
        claims = record.claims
        if (
            not secrets.compare_digest(claims.audience, audience)
            or claims.run_id != run_id
            or claims.generation != generation
        ):
            raise RivetAuthorityError(
                "RIVET_MCP_AUTHORITY_SCOPE_DENIED",
                "Rivet run authority scope is denied",
            )
        if node_handle is not None:
            expected = claims.node_bindings.get(node_handle)
            if (
                expected is None
                or binding_digest is None
                or not secrets.compare_digest(expected, binding_digest)
            ):
                raise RivetAuthorityError(
                    "RIVET_MCP_BINDING_MISMATCH", "Rivet node binding is unavailable"
                )
        if record.state is AuthorityState.ISSUED:
            record = replace(record, state=AuthorityState.ACTIVE)
            self._records_by_id[record.authority_id] = record
        return record

    def revoke(self, authority_id: str, *, reason: str) -> bool:
        record = self._records_by_id.get(authority_id)
        if record is None or record.state in {
            AuthorityState.REVOKED,
            AuthorityState.EXPIRED,
            AuthorityState.TERMINAL,
        }:
            return False
        self._records_by_id[authority_id] = replace(
            record,
            state=AuthorityState.REVOKED,
            revoked_at=self._clock(),
            reason=reason,
        )
        return True

    def terminal(self, authority_id: str, *, reason: str | None = None) -> bool:
        record = self._records_by_id.get(authority_id)
        if record is None or record.state is AuthorityState.TERMINAL:
            return False
        self._records_by_id[authority_id] = replace(
            record,
            state=AuthorityState.TERMINAL,
            terminal_at=self._clock(),
            reason=reason or record.reason,
        )
        self._authority_by_digest.pop(record.token_digest, None)
        return True


__all__ = [
    "AuthorityClaims",
    "AuthorityRecord",
    "AuthorityState",
    "IssuedAuthority",
    "RivetAuthorityError",
    "RivetRunAuthorityService",
]
