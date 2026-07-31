from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from core.surfaces.models import (
    DisplaySurfaceSource,
    ExternalUrlSurfaceSource,
    LiveAppOwnership,
    LiveAppSurfaceSource,
    SurfaceLifecycle,
    SurfaceRevision,
)
from workspace_service.surfaces.service import (
    ActorRole,
    SurfaceActor,
    SurfaceForbiddenError,
    SurfaceNotFoundError,
    SurfaceRevisionConflictError,
    SurfaceService,
)


pytestmark = [pytest.mark.workspace_surfaces, pytest.mark.asyncio]


class MemorySurfaceRepository:
    def __init__(self) -> None:
        self.rows = {}
        self.requests = {}
        self.scopes = {}

    def create(
        self,
        descriptor,
        *,
        user_id,
        session_id,
        idempotency_key=None,
    ):
        scope = (user_id, descriptor.workspace_id, session_id, idempotency_key)
        if idempotency_key and scope in self.requests:
            surface_id = self.requests[scope]
            return self.rows[surface_id]
        self.rows[str(descriptor.surface_id)] = descriptor
        self.scopes[str(descriptor.surface_id)] = (user_id, session_id)
        if idempotency_key:
            self.requests[scope] = str(descriptor.surface_id)
        return descriptor

    def get(self, surface_id, *, workspace_id, user_id, session_id):
        descriptor = self.rows.get(str(surface_id))
        if not descriptor:
            return None
        owner, scope = self.scopes[str(descriptor.surface_id)]
        if descriptor.workspace_id != workspace_id:
            return None
        if owner != user_id:
            return None
        if scope != session_id:
            return None
        return descriptor

    def get_by_idempotency(self, *, workspace_id, user_id, session_id, idempotency_key):
        surface_id = self.requests.get(
            (user_id, workspace_id, session_id, idempotency_key)
        )
        return self.rows.get(surface_id) if surface_id else None

    def list(self, *, workspace_id, user_id, session_id):
        return [
            descriptor
            for descriptor in self.rows.values()
            if descriptor.workspace_id == workspace_id
            and self.scopes[str(descriptor.surface_id)] == (user_id, session_id)
        ]

    def compare_and_set(
        self,
        descriptor,
        *,
        expected_revision,
        user_id,
        session_id,
    ):
        existing = self.get(
            descriptor.surface_id,
            workspace_id=descriptor.workspace_id,
            user_id=user_id,
            session_id=session_id,
        )
        if existing is None:
            raise SurfaceNotFoundError(str(descriptor.surface_id))
        if existing.revision != expected_revision:
            raise SurfaceRevisionConflictError(
                str(descriptor.surface_id), expected_revision, existing.revision
            )
        self.rows[str(descriptor.surface_id)] = descriptor
        return descriptor


def _actor(
    *,
    user: str = "user-1",
    workspace: str = "workspace-1",
    session: str = "session-1",
    role: ActorRole = ActorRole.ENGINEER,
) -> SurfaceActor:
    return SurfaceActor(
        user_id=user,
        workspace_id=workspace,
        session_id=session,
        role=role,
    )


def _display() -> DisplaySurfaceSource:
    return DisplaySurfaceSource(
        execution_id="execution-1",
        display_id="loads",
        artifact_revision=1,
        durability="durable",
        media_types=("text/plain",),
    )


def _service() -> tuple[SurfaceService, MemorySurfaceRepository]:
    repository = MemorySurfaceRepository()
    ids = iter(("surface-1", "surface-2", "surface-3", "surface-4"))
    service = SurfaceService(
        repository=repository,
        id_factory=lambda: next(ids),
        clock=lambda: datetime(2026, 7, 30, 12, 0, tzinfo=UTC),
    )
    return service, repository


async def test_engineer_can_declare_display_and_view_only_external_surface() -> None:
    service, _ = _service()
    display = await service.declare(
        actor=_actor(), source=_display(), title="Loads", idempotency_key="display-1"
    )
    external = await service.declare(
        actor=_actor(),
        source=ExternalUrlSurfaceSource(
            normalized_url="https://docs.example.test/guide",
            approval_id="approval-1",
            view_only=True,
        ),
        title="Guide",
        idempotency_key="external-1",
    )
    assert display.lifecycle is SurfaceLifecycle.DECLARED
    assert external.source.view_only is True


async def test_engineer_may_run_admin_approved_manifest_but_not_approve_attach() -> (
    None
):
    service, _ = _service()
    approved = LiveAppSurfaceSource(
        manifest_id="brep",
        manifest_version="1.0.0",
        manifest_hash="a" * 64,
        ownership=LiveAppOwnership.WRIGHT_OWNED,
        administrator_approved=True,
        sharing_mode="shared",
    )
    descriptor = await service.declare(
        actor=_actor(),
        source=approved,
        title="BREP",
        idempotency_key="brep-1",
    )
    assert descriptor.source == approved

    attached = replace(
        approved,
        ownership=LiveAppOwnership.APPROVED_ATTACH,
        administrator_approved=False,
    )
    with pytest.raises(SurfaceForbiddenError, match="administrator"):
        await service.declare(
            actor=_actor(),
            source=attached,
            title="Attached",
            idempotency_key="attach-1",
        )


async def test_administrator_can_approve_attached_target() -> None:
    service, _ = _service()
    attached = LiveAppSurfaceSource(
        manifest_id="approved-attach",
        manifest_version="1.0.0",
        manifest_hash="b" * 64,
        ownership=LiveAppOwnership.APPROVED_ATTACH,
        administrator_approved=True,
        sharing_mode="shared",
    )
    descriptor = await service.declare(
        actor=_actor(role=ActorRole.ADMIN),
        source=attached,
        title="Attached",
        idempotency_key="attach-1",
    )
    assert descriptor.source.ownership is LiveAppOwnership.APPROVED_ATTACH


async def test_queries_never_cross_user_workspace_or_session_scope() -> None:
    service, _ = _service()
    descriptor = await service.declare(
        actor=_actor(), source=_display(), title="Loads", idempotency_key="display-1"
    )
    assert (
        await service.get(actor=_actor(), surface_id=descriptor.surface_id)
        == descriptor
    )
    for foreign in (
        _actor(user="user-2"),
        _actor(workspace="workspace-2"),
        _actor(session="session-2"),
    ):
        with pytest.raises(SurfaceNotFoundError):
            await service.get(actor=foreign, surface_id=descriptor.surface_id)
        assert await service.list(actor=foreign) == []


async def test_declare_idempotency_returns_one_logical_surface() -> None:
    service, repository = _service()
    first = await service.declare(
        actor=_actor(), source=_display(), title="Loads", idempotency_key="same"
    )
    replay = await service.declare(
        actor=_actor(), source=_display(), title="Loads", idempotency_key="same"
    )
    assert replay == first
    assert len(repository.rows) == 1


async def test_transition_requires_current_revision_and_legal_state() -> None:
    service, _ = _service()
    descriptor = await service.declare(
        actor=_actor(), source=_display(), title="Loads", idempotency_key="display-1"
    )
    starting = await service.transition(
        actor=_actor(),
        surface_id=descriptor.surface_id,
        target=SurfaceLifecycle.STARTING,
        expected_revision=SurfaceRevision(1),
    )
    assert starting.lifecycle is SurfaceLifecycle.STARTING
    assert starting.revision == SurfaceRevision(2)
    with pytest.raises(SurfaceRevisionConflictError):
        await service.transition(
            actor=_actor(),
            surface_id=descriptor.surface_id,
            target=SurfaceLifecycle.READY,
            expected_revision=SurfaceRevision(1),
        )
    with pytest.raises(Exception, match="transition"):
        await service.transition(
            actor=_actor(),
            surface_id=descriptor.surface_id,
            target=SurfaceLifecycle.DECLARED,
            expected_revision=SurfaceRevision(2),
        )
