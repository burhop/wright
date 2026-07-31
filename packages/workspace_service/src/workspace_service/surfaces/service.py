"""Workspace-scoped Surface state machine and authority boundary."""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import UTC, datetime
from enum import StrEnum

from core.surfaces.errors import (
    SurfaceError,
    SurfaceErrorCode,
    SurfaceOptimisticLockError,
)
from core.surfaces.models import (
    LiveAppOwnership,
    LiveAppSurfaceSource,
    SurfaceDescriptor,
    SurfaceId,
    SurfaceLifecycle,
    SurfaceRevision,
    SurfaceSource,
)

from .ports import SurfaceEventPublisherPort, SurfaceRepositoryPort


class ActorRole(StrEnum):
    ENGINEER = "engineer"
    ADMIN = "admin"


class SurfaceActor:
    __slots__ = ("user_id", "workspace_id", "session_id", "role")

    def __init__(
        self,
        *,
        user_id: str,
        workspace_id: str,
        session_id: str,
        role: ActorRole | str,
    ) -> None:
        for label, value in (
            ("user_id", user_id),
            ("workspace_id", workspace_id),
            ("session_id", session_id),
        ):
            if not value.strip():
                raise ValueError(f"{label} is required")
            setattr(self, label, value.strip())
        self.role = ActorRole(role)


class SurfaceNotFoundError(SurfaceError):
    def __init__(self, surface_id: str) -> None:
        super().__init__(
            code=SurfaceErrorCode.NOT_FOUND,
            message="Surface not found in the authorized workspace scope.",
            retryable=False,
            context={"surface_id": surface_id},
        )


class SurfaceForbiddenError(SurfaceError):
    def __init__(self, message: str) -> None:
        super().__init__(
            code=SurfaceErrorCode.FORBIDDEN, message=message, retryable=False
        )


class SurfaceRevisionConflictError(SurfaceError):
    def __init__(
        self,
        surface_id: str,
        expected: SurfaceRevision,
        current: SurfaceRevision,
    ) -> None:
        super().__init__(
            code=SurfaceErrorCode.STALE_REVISION,
            message="The surface changed; refresh before retrying.",
            retryable=True,
            context={
                "surface_id": surface_id,
                "expected_revision": int(expected),
                "current_revision": int(current),
            },
        )


class SurfaceService:
    def __init__(
        self,
        *,
        repository: SurfaceRepositoryPort,
        id_factory=lambda: str(uuid.uuid4()),
        clock=lambda: datetime.now(UTC),
        events: SurfaceEventPublisherPort | None = None,
    ) -> None:
        self.repository = repository
        self.id_factory = id_factory
        self.clock = clock
        self.events = events

    @staticmethod
    def _require_authorized_actor(actor: SurfaceActor) -> None:
        if actor.role not in {ActorRole.ENGINEER, ActorRole.ADMIN}:
            raise SurfaceForbiddenError("Engineer or administrator role required.")

    @staticmethod
    def _authorize_source(actor: SurfaceActor, source: SurfaceSource) -> None:
        if not isinstance(source, LiveAppSurfaceSource):
            return
        if source.ownership is LiveAppOwnership.APPROVED_ATTACH:
            if actor.role is not ActorRole.ADMIN:
                raise SurfaceForbiddenError(
                    "Only an administrator may approve an attached target."
                )
        elif actor.role is ActorRole.ENGINEER and not source.administrator_approved:
            raise SurfaceForbiddenError(
                "An administrator must approve the workspace manifest first."
            )

    async def declare(
        self,
        *,
        actor: SurfaceActor,
        source: SurfaceSource,
        title: str,
        idempotency_key: str,
    ) -> SurfaceDescriptor:
        self._require_authorized_actor(actor)
        self._authorize_source(actor, source)
        existing = self.repository.get_by_idempotency(
            workspace_id=actor.workspace_id,
            user_id=actor.user_id,
            session_id=actor.session_id,
            idempotency_key=idempotency_key,
        )
        if existing is not None:
            return existing
        now = self.clock()
        descriptor = SurfaceDescriptor(
            schema_version=1,
            surface_id=SurfaceId(self.id_factory()),
            workspace_id=actor.workspace_id,
            source=source,
            title=title,
            lifecycle=SurfaceLifecycle.DECLARED,
            revision=SurfaceRevision(1),
            created_at=now,
            updated_at=now,
        )
        result = self.repository.create(
            descriptor,
            user_id=actor.user_id,
            session_id=actor.session_id,
            idempotency_key=idempotency_key,
        )
        if self.events:
            self.events.publish(
                result,
                event_type="surface.declared",
                user_id=actor.user_id,
                session_id=actor.session_id,
            )
        return result

    async def get(
        self, *, actor: SurfaceActor, surface_id: SurfaceId
    ) -> SurfaceDescriptor:
        self._require_authorized_actor(actor)
        descriptor = self.repository.get(
            surface_id,
            workspace_id=actor.workspace_id,
            user_id=actor.user_id,
            session_id=actor.session_id,
        )
        if descriptor is None:
            raise SurfaceNotFoundError(str(surface_id))
        return descriptor

    async def list(self, *, actor: SurfaceActor) -> list[SurfaceDescriptor]:
        self._require_authorized_actor(actor)
        return list(
            self.repository.list(
                workspace_id=actor.workspace_id,
                user_id=actor.user_id,
                session_id=actor.session_id,
            )
        )

    async def transition(
        self,
        *,
        actor: SurfaceActor,
        surface_id: SurfaceId,
        target: SurfaceLifecycle,
        expected_revision: SurfaceRevision,
    ) -> SurfaceDescriptor:
        current = await self.get(actor=actor, surface_id=surface_id)
        if current.revision != expected_revision:
            raise SurfaceRevisionConflictError(
                str(surface_id), expected_revision, current.revision
            )
        updated = current.with_lifecycle(target, updated_at=self.clock())
        try:
            result = self.repository.compare_and_set(
                updated,
                expected_revision=expected_revision,
                user_id=actor.user_id,
                session_id=actor.session_id,
            )
        except SurfaceOptimisticLockError as error:
            latest = await self.get(actor=actor, surface_id=surface_id)
            raise SurfaceRevisionConflictError(
                str(surface_id), expected_revision, latest.revision
            ) from error
        if self.events:
            self.events.publish(
                result,
                event_type="surface.updated",
                user_id=actor.user_id,
                session_id=actor.session_id,
            )
        return result

    async def project_runtime(
        self,
        *,
        actor: SurfaceActor,
        surface_id: SurfaceId,
        target: SurfaceLifecycle,
        expected_revision: SurfaceRevision,
        instance: dict[str, object] | None,
        presentations: tuple[dict[str, object], ...],
        diagnostic_summary: dict[str, object] | None = None,
    ) -> SurfaceDescriptor:
        current = await self.get(actor=actor, surface_id=surface_id)
        if current.revision != expected_revision:
            raise SurfaceRevisionConflictError(
                str(surface_id), expected_revision, current.revision
            )
        updated = replace(
            current.with_lifecycle(target, updated_at=self.clock()),
            instance=instance,
            presentations=presentations,
            diagnostic_summary=diagnostic_summary,
        )
        try:
            result = self.repository.compare_and_set(
                updated,
                expected_revision=expected_revision,
                user_id=actor.user_id,
                session_id=actor.session_id,
            )
        except SurfaceOptimisticLockError as error:
            latest = await self.get(actor=actor, surface_id=surface_id)
            raise SurfaceRevisionConflictError(
                str(surface_id), expected_revision, latest.revision
            ) from error
        if self.events:
            self.events.publish(
                result,
                event_type="surface.updated",
                user_id=actor.user_id,
                session_id=actor.session_id,
            )
        return result
