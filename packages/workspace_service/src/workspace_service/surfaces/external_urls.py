"""Explicit, expiring, direct-navigation-only external URL approvals."""

from __future__ import annotations

import ipaddress
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import RLock
from urllib.parse import urlsplit, urlunsplit

from core.surfaces.network_values import AddressClass, classify_address

from .service import SurfaceActor


class ExternalUrlApprovalError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ExternalUrlApproval:
    approval_id: str
    user_id: str
    workspace_id: str
    session_id: str
    normalized_url: str
    reason: str
    created_at: datetime
    expires_at: datetime
    direct_navigation: bool = True
    proxied: bool = False
    wright_credentials: bool = False
    bridge_enabled: bool = False
    managed_lifecycle: bool = False


def normalize_external_url(value: str) -> str:
    if (
        not value
        or value != value.strip()
        or any(character in value for character in "\r\n\0\\")
    ):
        raise ExternalUrlApprovalError("External destination is invalid")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise ExternalUrlApprovalError("External destination is invalid") from error
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"} or not parsed.hostname:
        raise ExternalUrlApprovalError("External destination must use HTTP or HTTPS")
    if parsed.username is not None or parsed.password is not None:
        raise ExternalUrlApprovalError("External destination credentials are forbidden")
    hostname = parsed.hostname.lower().rstrip(".")
    if hostname == "localhost" or not hostname:
        raise ExternalUrlApprovalError("External destination is not eligible")
    try:
        numeric = ipaddress.ip_address(hostname)
    except ValueError:
        try:
            hostname = hostname.encode("idna").decode("ascii")
        except UnicodeError as error:
            raise ExternalUrlApprovalError("External destination host is invalid") from error
    else:
        if classify_address(str(numeric)) is not AddressClass.PUBLIC:
            raise ExternalUrlApprovalError("External destination address is denied")
    default_port = 443 if scheme == "https" else 80
    if port is not None and not 1 <= port <= 65535:
        raise ExternalUrlApprovalError("External destination port is invalid")
    host = f"[{hostname}]" if ":" in hostname else hostname
    authority = host if port in {None, default_port} else f"{host}:{port}"
    return urlunsplit(
        (scheme, authority, parsed.path or "/", parsed.query, parsed.fragment)
    )


class ExternalUrlApprovalService:
    def __init__(
        self,
        *,
        ttl_seconds: int = 5 * 60,
        clock=lambda: datetime.now(UTC),
        id_factory=lambda: secrets.token_urlsafe(24),
    ) -> None:
        if not 1 <= ttl_seconds <= 60 * 60:
            raise ValueError("external URL approval TTL must be between 1 second and 1 hour")
        self.ttl_seconds = ttl_seconds
        self.clock = clock
        self.id_factory = id_factory
        self._approvals: dict[str, ExternalUrlApproval] = {}
        self._lock = RLock()

    def approve(
        self,
        *,
        actor: SurfaceActor,
        url: str,
        acknowledged: bool,
        reason: str,
    ) -> ExternalUrlApproval:
        if not acknowledged:
            raise ExternalUrlApprovalError("External navigation acknowledgement is required")
        if not reason.strip() or len(reason) > 512:
            raise ExternalUrlApprovalError("External navigation reason is required")
        normalized = normalize_external_url(url)
        now = self.clock()
        approval = ExternalUrlApproval(
            approval_id=self.id_factory(),
            user_id=actor.user_id,
            workspace_id=actor.workspace_id,
            session_id=actor.session_id,
            normalized_url=normalized,
            reason=reason.strip(),
            created_at=now,
            expires_at=now + timedelta(seconds=self.ttl_seconds),
        )
        with self._lock:
            self._approvals[approval.approval_id] = approval
        return approval

    def authorize(
        self,
        *,
        actor: SurfaceActor,
        approval_id: str,
        url: str,
    ) -> ExternalUrlApproval:
        with self._lock:
            approval = self._approvals.get(approval_id)
        if approval is None:
            raise ExternalUrlApprovalError("External approval not found")
        if (
            approval.user_id != actor.user_id
            or approval.workspace_id != actor.workspace_id
            or approval.session_id != actor.session_id
        ):
            raise ExternalUrlApprovalError("External approval scope does not match")
        if approval.expires_at < self.clock():
            raise ExternalUrlApprovalError("External approval expired")
        if approval.normalized_url != normalize_external_url(url):
            raise ExternalUrlApprovalError("External approval destination changed")
        return approval


__all__ = [
    "ExternalUrlApproval",
    "ExternalUrlApprovalError",
    "ExternalUrlApprovalService",
    "normalize_external_url",
]
