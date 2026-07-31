"""One-time preview bootstrap exchange and host-bound presentation sessions."""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

from data_vault import SurfacePresentationRecord, SurfacePresentationRepository

from ..config import SurfacePreviewSettings


_CREDENTIAL = re.compile(r"^[A-Za-z0-9_-]{32,2048}$")
_PRESENTATION_ID = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,59}[a-z0-9])?$")


class PresentationTokenError(RuntimeError):
    def __init__(self, code: str, message: str, *, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


@dataclass(frozen=True, slots=True)
class PreviewSession:
    cookie_value: str
    expires_at: datetime
    presentation: SurfacePresentationRecord


class PresentationTokenService:
    """Keep raw authority in the browser and persist only credential digests."""

    def __init__(
        self,
        db_path: str | Path,
        *,
        preview: SurfacePreviewSettings,
        clock=lambda: datetime.now(UTC),
        cookie_factory=lambda: secrets.token_urlsafe(32),
    ) -> None:
        self.presentations = SurfacePresentationRepository(db_path)
        self.preview = preview
        self.clock = clock
        self.cookie_factory = cookie_factory

    @staticmethod
    def _digest(value: str) -> str:
        return hashlib.sha256(value.encode("ascii")).hexdigest()

    def _host_identity(self, host: str) -> tuple[str, int]:
        if (
            not host
            or host != host.strip()
            or any(character in host for character in "@/\\?#")
            or any(character.isspace() for character in host)
        ):
            raise self._not_found()
        try:
            parsed = urlsplit(f"{self.preview.scheme}://{host}")
            hostname = parsed.hostname
            explicit_port = parsed.port
        except ValueError as error:
            raise self._not_found() from error
        if not hostname or parsed.path or parsed.query or parsed.fragment:
            raise self._not_found()
        default_port = 443 if self.preview.scheme == "https" else 80
        return hostname.lower(), explicit_port or default_port

    @staticmethod
    def _not_found() -> PresentationTokenError:
        return PresentationTokenError(
            "SURFACE_PREVIEW_NOT_FOUND",
            "Preview presentation not found",
            status_code=404,
        )

    @staticmethod
    def _unauthorized() -> PresentationTokenError:
        return PresentationTokenError(
            "SURFACE_PREVIEW_UNAUTHORIZED",
            "Preview credential is invalid",
            status_code=401,
        )

    @staticmethod
    def _gone() -> PresentationTokenError:
        return PresentationTokenError(
            "SURFACE_PREVIEW_GONE",
            "Preview authority is no longer available",
            status_code=410,
        )

    def _record_for_host(self, host: str) -> SurfacePresentationRecord:
        hostname, port = self._host_identity(host)
        domain = self.preview.domain.lower().rstrip(".")
        suffix = f".{domain}"
        if not hostname.endswith(suffix):
            raise self._not_found()
        label = hostname[: -len(suffix)]
        if not label.startswith("s-") or "." in label:
            raise self._not_found()
        presentation_id = label[2:]
        if not _PRESENTATION_ID.fullmatch(presentation_id):
            raise self._not_found()
        if port != self.preview.public_port:
            raise self._not_found()
        record = self.presentations.get_for_preview(presentation_id)
        if record is None:
            raise self._not_found()
        expected = urlsplit(record.effective_origin)
        expected_port = expected.port or (443 if expected.scheme == "https" else 80)
        if (
            expected.scheme != self.preview.scheme
            or expected.hostname != hostname
            or expected_port != port
            or expected.path
            or expected.query
            or expected.fragment
        ):
            raise self._not_found()
        return record

    def require_bound_host(self, host: str) -> SurfacePresentationRecord:
        record = self._record_for_host(host)
        now = self.clock()
        if record.state in {"closed", "expired"} or record.expires_at < now:
            raise self._gone()
        return record

    def exchange(self, *, host: str, token: str) -> PreviewSession:
        record = self.require_bound_host(host)
        now = self.clock()
        if (
            record.bootstrap_nonce_hash is None
            or record.bootstrap_expires_at < now
            or record.state not in {"issued", "inactive"}
        ):
            raise self._gone()
        if not _CREDENTIAL.fullmatch(token):
            raise self._unauthorized()
        candidate_hash = self._digest(token)
        if not hmac.compare_digest(record.bootstrap_nonce_hash, candidate_hash):
            raise self._unauthorized()
        cookie = self.cookie_factory()
        if not _CREDENTIAL.fullmatch(cookie):
            raise RuntimeError("presentation cookie factory returned an invalid value")
        activated = self.presentations.activate_with_cookie(
            record,
            expected_bootstrap_hash=candidate_hash,
            presentation_cookie_hash=self._digest(cookie),
            activated_at=now,
        )
        if activated is None:
            raise self._gone()
        return PreviewSession(
            cookie_value=cookie,
            expires_at=activated.expires_at,
            presentation=activated,
        )

    def authorize(self, *, host: str, cookie: str) -> SurfacePresentationRecord:
        record = self.require_bound_host(host)
        if record.state != "active" or record.presentation_cookie_hash is None:
            raise self._gone()
        if not _CREDENTIAL.fullmatch(cookie):
            raise self._unauthorized()
        if not hmac.compare_digest(
            record.presentation_cookie_hash, self._digest(cookie)
        ):
            raise self._unauthorized()
        return record


__all__ = [
    "PresentationTokenError",
    "PresentationTokenService",
    "PreviewSession",
]
