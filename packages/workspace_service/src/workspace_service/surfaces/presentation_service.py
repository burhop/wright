"""Presentation eligibility, preference, and short-lived bootstrap issuance."""

from __future__ import annotations

import hashlib
import re
import secrets
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlunsplit

from core.surfaces.models import (
    LiveAppSurfaceSource,
    SharingMode,
    SurfaceDescriptor,
    SurfaceId,
    SurfaceLifecycle,
)
from data_vault import (
    PresentationPreferenceRecord,
    SurfacePreferenceRepository,
    SurfacePresentationRecord,
    SurfacePresentationRepository,
    SurfaceRepository,
    SurfaceRevisionConflict,
)

from ..config import SurfacePreviewSettings
from .service import SurfaceActor


_BOOTSTRAP_TOKEN = re.compile(r"^[A-Za-z0-9_-]{32,2048}$")
_PRESENTATION_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,59}[a-z0-9])?$")
_INSTANCE_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class PresentationUnavailable(RuntimeError):
    pass


class IsolatedPresentationAcknowledgementRequired(PresentationUnavailable):
    pass


@dataclass(frozen=True, slots=True)
class PresentationLaunch:
    presentation_id: str
    instance_id: str
    generation: int
    kind: str
    absolute_bootstrap_url: str
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class PresentationOpenResult:
    launch: PresentationLaunch
    created: bool


@dataclass(frozen=True, slots=True)
class PresentationPreferenceDecision:
    kind: str
    remembered: bool
    reason: str


class PresentationService:
    def __init__(
        self,
        db_path: str | Path,
        *,
        preview: SurfacePreviewSettings,
        token_ttl_seconds: int = 60,
        clock=lambda: datetime.now(UTC),
        id_factory=lambda: str(uuid.uuid4()),
        token_factory=lambda: secrets.token_urlsafe(32),
    ) -> None:
        if not 1 <= token_ttl_seconds <= 300:
            raise ValueError("bootstrap token TTL must be between 1 and 300 seconds")
        self.surfaces = SurfaceRepository(db_path)
        self.presentations = SurfacePresentationRepository(db_path)
        self.preferences = SurfacePreferenceRepository(db_path)
        self.preview = preview
        self.token_ttl_seconds = token_ttl_seconds
        self.clock = clock
        self.id_factory = id_factory
        self.token_factory = token_factory

    def _surface(
        self, *, actor: SurfaceActor, surface_id: SurfaceId
    ) -> SurfaceDescriptor:
        descriptor = self.surfaces.get(
            surface_id,
            workspace_id=actor.workspace_id,
            user_id=actor.user_id,
            session_id=actor.session_id,
        )
        if descriptor is None:
            raise PresentationUnavailable("Surface or presentation unavailable")
        return descriptor

    @staticmethod
    def _options(descriptor: SurfaceDescriptor) -> dict[str, tuple[bool, str]]:
        options: dict[str, tuple[bool, str]] = {}
        for raw in descriptor.presentations:
            kind = raw.get("kind")
            if kind not in {"panel", "browser"}:
                continue
            options[str(kind)] = (
                raw.get("eligible") is True,
                str(raw.get("reason") or "Presentation is not eligible"),
            )
        return options

    def _ready_live_app(
        self, *, actor: SurfaceActor, surface_id: SurfaceId
    ) -> tuple[SurfaceDescriptor, LiveAppSurfaceSource, str, int]:
        descriptor = self._surface(actor=actor, surface_id=surface_id)
        if (
            not isinstance(descriptor.source, LiveAppSurfaceSource)
            or descriptor.lifecycle is not SurfaceLifecycle.READY
            or not isinstance(descriptor.instance, dict)
        ):
            raise PresentationUnavailable("A current ready instance is required")
        instance_id = descriptor.instance.get("instanceId")
        generation = descriptor.instance.get("generation")
        if (
            not isinstance(instance_id, str)
            or not instance_id.strip()
            or isinstance(generation, bool)
            or not isinstance(generation, int)
            or generation < 1
        ):
            raise PresentationUnavailable("A current ready instance is required")
        return descriptor, descriptor.source, instance_id, generation

    def _origin(self, presentation_id: str) -> str:
        if not _PRESENTATION_LABEL.fullmatch(presentation_id):
            raise RuntimeError("presentation ID factory returned an invalid ID")
        hostname = f"s-{presentation_id.lower()}.{self.preview.domain}"
        default_port = 443 if self.preview.scheme == "https" else 80
        authority = (
            hostname
            if self.preview.public_port == default_port
            else f"{hostname}:{self.preview.public_port}"
        )
        return urlunsplit((self.preview.scheme, authority, "", "", ""))

    def _token(self) -> tuple[str, str]:
        token = self.token_factory()
        if not _BOOTSTRAP_TOKEN.fullmatch(token):
            raise RuntimeError("bootstrap token factory returned an invalid token")
        return token, hashlib.sha256(token.encode("ascii")).hexdigest()

    @staticmethod
    def _launch(
        record: SurfacePresentationRecord, *, token: str
    ) -> PresentationLaunch:
        return PresentationLaunch(
            presentation_id=record.presentation_id,
            instance_id=record.instance_id,
            generation=record.generation,
            kind=record.kind,
            absolute_bootstrap_url=(
                f"{record.effective_origin}/__wright/bootstrap#{token}"
            ),
            expires_at=record.expires_at,
        )

    def resolve_preference(
        self, *, actor: SurfaceActor, surface_id: SurfaceId
    ) -> PresentationPreferenceDecision:
        descriptor, source, _instance_id, _generation = self._ready_live_app(
            actor=actor, surface_id=surface_id
        )
        options = self._options(descriptor)
        preferred = self.preferences.get(
            user_id=actor.user_id,
            workspace_id=actor.workspace_id,
            source_id=source.source_id,
        )
        if preferred is not None:
            if preferred.source_version != source.source_version:
                reason = "Remembered choice is for a different source version."
            elif options.get(preferred.preferred_kind, (False, ""))[0]:
                return PresentationPreferenceDecision(
                    kind=preferred.preferred_kind,
                    remembered=True,
                    reason="Remembered choice is current and eligible.",
                )
            else:
                reason = options.get(
                    preferred.preferred_kind,
                    (False, "Remembered choice is no longer available."),
                )[1]
        else:
            reason = "No remembered choice is available."
        for fallback in ("browser", "panel"):
            if options.get(fallback, (False, ""))[0]:
                return PresentationPreferenceDecision(
                    kind=fallback, remembered=False, reason=reason
                )
        raise PresentationUnavailable("No safe presentation is currently eligible")

    def _remember(
        self, *, actor: SurfaceActor, source: LiveAppSurfaceSource, kind: str
    ) -> None:
        for _attempt in range(2):
            now = self.clock()
            current = self.preferences.get(
                user_id=actor.user_id,
                workspace_id=actor.workspace_id,
                source_id=source.source_id,
            )
            record = PresentationPreferenceRecord(
                user_id=actor.user_id,
                workspace_id=actor.workspace_id,
                source_id=source.source_id,
                source_version=source.source_version,
                preferred_kind=kind,
                revision=1 if current is None else current.revision + 1,
                created_at=now if current is None else current.created_at,
                updated_at=now,
            )
            try:
                self.preferences.compare_and_set(
                    record,
                    expected_revision=None if current is None else current.revision,
                )
                return
            except SurfaceRevisionConflict:
                continue
        raise PresentationUnavailable(
            "Presentation preference changed concurrently; retry the request"
        )

    def set_preference(
        self,
        *,
        actor: SurfaceActor,
        surface_id: SurfaceId,
        kind: str,
    ) -> PresentationPreferenceDecision:
        descriptor, source, _instance_id, _generation = self._ready_live_app(
            actor=actor, surface_id=surface_id
        )
        eligible, reason = self._options(descriptor).get(
            kind, (False, "Presentation kind was not declared")
        )
        if kind not in {"panel", "browser"} or not eligible:
            raise PresentationUnavailable(reason)
        self._remember(actor=actor, source=source, kind=kind)
        return PresentationPreferenceDecision(
            kind=kind,
            remembered=True,
            reason="Remembered choice is current and eligible.",
        )

    def open(
        self,
        *,
        actor: SurfaceActor,
        surface_id: SurfaceId,
        kind: str,
        idempotency_key: str,
        remember_preference: bool = False,
        isolated_acknowledged: bool = False,
    ) -> PresentationOpenResult:
        if kind not in {"panel", "browser"}:
            raise PresentationUnavailable("Presentation kind is unsupported")
        if not 16 <= len(idempotency_key) <= 128:
            raise PresentationUnavailable("Idempotency key is invalid")
        descriptor, source, shared_instance_id, generation = self._ready_live_app(
            actor=actor, surface_id=surface_id
        )
        eligible, reason = self._options(descriptor).get(
            kind, (False, "Presentation kind was not declared")
        )
        if not eligible:
            raise PresentationUnavailable(reason)
        if (
            source.sharing_mode is SharingMode.ISOLATED
            and not isolated_acknowledged
        ):
            raise IsolatedPresentationAcknowledgementRequired(
                "Isolated presentation creates a separate application instance"
            )

        now = self.clock()
        expires_at = now + timedelta(seconds=self.token_ttl_seconds)
        token, token_hash = self._token()
        existing = self.presentations.get_by_idempotency(
            user_id=actor.user_id,
            workspace_id=actor.workspace_id,
            session_id=actor.session_id,
            idempotency_key=idempotency_key,
        )
        if existing is not None:
            if (
                existing.surface_id != str(surface_id)
                or existing.kind != kind
                or existing.source_id != source.source_id
                or existing.source_version != source.source_version
                or existing.generation != generation
                or (
                    source.sharing_mode is SharingMode.SHARED
                    and existing.instance_id != shared_instance_id
                )
            ):
                raise PresentationUnavailable(
                    "Idempotency key is already bound to another presentation"
                )
            existing = self.presentations.rotate_bootstrap(
                existing,
                bootstrap_nonce_hash=token_hash,
                expires_at=expires_at,
            )
            if remember_preference:
                self._remember(actor=actor, source=source, kind=kind)
            return PresentationOpenResult(
                launch=self._launch(existing, token=token), created=False
            )

        presentation_id = self.id_factory()
        instance_id = (
            shared_instance_id
            if source.sharing_mode is SharingMode.SHARED
            else self.id_factory()
        )
        if not _INSTANCE_ID.fullmatch(instance_id):
            raise RuntimeError("instance ID factory returned an invalid ID")
        origin = self._origin(presentation_id)
        record = SurfacePresentationRecord(
            presentation_id=presentation_id,
            instance_id=instance_id,
            surface_id=str(surface_id),
            workspace_id=actor.workspace_id,
            user_id=actor.user_id,
            session_id=actor.session_id,
            kind=kind,
            state="issued",
            generation=generation,
            source_id=source.source_id,
            source_version=source.source_version,
            effective_origin=origin,
            bootstrap_nonce_hash=token_hash,
            cookie_audience=f"surface-presentation:{presentation_id}:{origin}",
            idempotency_key=idempotency_key,
            created_at=now,
            expires_at=expires_at,
        )
        try:
            self.presentations.create(record)
        except sqlite3.IntegrityError as error:
            # A concurrent request with the same scoped idempotency key may
            # win after the initial lookup. Recover its result without
            # creating a second presentation or exposing database details.
            existing = self.presentations.get_by_idempotency(
                user_id=actor.user_id,
                workspace_id=actor.workspace_id,
                session_id=actor.session_id,
                idempotency_key=idempotency_key,
            )
            if existing is None:
                raise PresentationUnavailable(
                    "Presentation could not be created; retry the request"
                ) from error
            if (
                existing.surface_id != str(surface_id)
                or existing.kind != kind
                or existing.source_id != source.source_id
                or existing.source_version != source.source_version
                or existing.generation != generation
                or (
                    source.sharing_mode is SharingMode.SHARED
                    and existing.instance_id != shared_instance_id
                )
            ):
                raise PresentationUnavailable(
                    "Idempotency key is already bound to another presentation"
                ) from error
            existing = self.presentations.rotate_bootstrap(
                existing,
                bootstrap_nonce_hash=token_hash,
                expires_at=expires_at,
            )
            if remember_preference:
                self._remember(actor=actor, source=source, kind=kind)
            return PresentationOpenResult(
                launch=self._launch(existing, token=token), created=False
            )
        if remember_preference:
            self._remember(actor=actor, source=source, kind=kind)
        return PresentationOpenResult(
            launch=self._launch(record, token=token), created=True
        )

    def get_record(
        self, *, actor: SurfaceActor, presentation_id: str
    ) -> SurfacePresentationRecord:
        record = self.presentations.get(
            presentation_id,
            user_id=actor.user_id,
            workspace_id=actor.workspace_id,
            session_id=actor.session_id,
        )
        if record is None:
            raise PresentationUnavailable("Surface or presentation unavailable")
        return record

    def list_records(
        self, *, actor: SurfaceActor, surface_id: SurfaceId
    ) -> list[SurfacePresentationRecord]:
        self._surface(actor=actor, surface_id=surface_id)
        return self.presentations.list_for_surface(
            surface_id=str(surface_id),
            user_id=actor.user_id,
            workspace_id=actor.workspace_id,
            session_id=actor.session_id,
        )

    def close(
        self,
        *,
        actor: SurfaceActor,
        surface_id: SurfaceId,
        presentation_id: str,
    ) -> SurfacePresentationRecord:
        self._surface(actor=actor, surface_id=surface_id)
        record = self.get_record(actor=actor, presentation_id=presentation_id)
        if record.surface_id != str(surface_id):
            raise PresentationUnavailable("Surface or presentation unavailable")
        return self.presentations.close(record, closed_at=self.clock())
