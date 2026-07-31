from __future__ import annotations

import sqlite3
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from core.surfaces.models import (
    LiveAppOwnership,
    LiveAppSurfaceSource,
    SharingMode,
    SurfaceDescriptor,
    SurfaceId,
    SurfaceLifecycle,
    SurfaceRevision,
)
from data_vault import SurfaceRepository, upgrade_database
from workspace_service.surfaces.live_app_manager import (
    LiveAppFailure,
    LiveAppInstance,
    LiveAppManagerError,
)
from workspace_service.surfaces.live_app_service import (
    LiveAppControlError,
    LiveAppControlService,
)
from workspace_service.surfaces.service import ActorRole, SurfaceActor, SurfaceService


pytestmark = [pytest.mark.workspace_surfaces, pytest.mark.anyio]
NOW = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)


def _actor() -> SurfaceActor:
    return SurfaceActor(
        user_id="user-1",
        workspace_id="workspace-1",
        session_id="session-1",
        role=ActorRole.ENGINEER,
    )


def _instance(*, state: str = "ready", generation: int = 1) -> LiveAppInstance:
    return LiveAppInstance(
        instance_id="instance-1",
        workspace_id="workspace-1",
        surface_id="surface-app",
        manifest_id="demo.app",
        manifest_hash="a" * 64,
        generation=generation,
        revision=generation,
        state=state,
        sharing="shared",
        ownership="launched",
        platform="windows_job",
        runtime_id=f"runtime-{generation}",
        lifetime_policy="workspace",
        lease_expires_at=None,
        idle_seconds=None,
        last_activity_at=NOW,
        started_at=NOW,
        ready_at=NOW if state == "ready" else None,
        ended_at=NOW if state in {"failed", "stopped"} else None,
        last_health=None,
        failure=(
            LiveAppFailure("SURFACE_START_FAILED", "App failed", True)
            if state == "failed"
            else None
        ),
    )


class _Manager:
    def __init__(self) -> None:
        self.instance = _instance()
        self.calls: list[str] = []
        self.start_error: LiveAppManagerError | None = None

    async def start(self, request):
        self.calls.append(f"start:{request.idempotency_key}")
        if self.start_error:
            raise self.start_error
        return self.instance

    async def restart(self, instance_id: str, *, idempotency_key: str):
        self.calls.append(f"restart:{instance_id}:{idempotency_key}")
        self.instance = replace(
            self.instance,
            generation=self.instance.generation + 1,
            state="ready",
            failure=None,
        )
        return self.instance

    async def retry(self, instance_id: str, *, idempotency_key: str):
        return await self.restart(instance_id, idempotency_key=idempotency_key)

    async def stop(self, instance_id: str, *, idempotency_key: str):
        self.calls.append(f"stop:{instance_id}:{idempotency_key}")
        self.instance = replace(self.instance, state="stopped", ended_at=NOW)
        return self.instance

    def get(self, instance_id: str):
        assert instance_id == self.instance.instance_id
        return self.instance

    def presentation_projection(self, instance_id: str):
        assert instance_id == self.instance.instance_id
        return (
            {"kind": "panel", "eligible": True},
            {"kind": "browser", "eligible": True},
        )


def _service(tmp_path: Path):
    database = tmp_path / "state.db"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    upgrade_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES (?, ?, ?, 1, 1)""",
            ("workspace-1", "session-1", str(workspace)),
        )
        connection.commit()
    repository = SurfaceRepository(database)
    repository.create(
        SurfaceDescriptor(
            schema_version=1,
            surface_id=SurfaceId("surface-app"),
            workspace_id="workspace-1",
            source=LiveAppSurfaceSource(
                manifest_id="demo.app",
                manifest_version="1.0.0",
                manifest_hash="a" * 64,
                ownership=LiveAppOwnership.WRIGHT_OWNED,
                administrator_approved=True,
                sharing_mode=SharingMode.SHARED,
            ),
            title="Demo app",
            lifecycle=SurfaceLifecycle.DECLARED,
            revision=SurfaceRevision(1),
            created_at=NOW,
            updated_at=NOW,
        ),
        user_id="user-1",
        session_id="session-1",
        idempotency_key="declare-managed-app",
    )
    manager = _Manager()
    surfaces = SurfaceService(repository=repository, clock=lambda: NOW)
    return (
        LiveAppControlService(
            surfaces=surfaces,
            manager_for_workspace=lambda _workspace_id: manager,
        ),
        surfaces,
        manager,
    )


async def test_start_restart_and_stop_publish_truthful_surface_generations(
    tmp_path: Path,
) -> None:
    control, surfaces, manager = _service(tmp_path)
    actor = _actor()
    instance = await control.start(
        actor=actor,
        surface_id=SurfaceId("surface-app"),
        idempotency_key="start-operation-0001",
    )
    current = await surfaces.get(actor=actor, surface_id=SurfaceId("surface-app"))
    assert instance.state == "ready"
    assert current.lifecycle is SurfaceLifecycle.READY
    assert current.instance["instanceId"] == "instance-1"
    assert current.presentations[0]["kind"] == "panel"

    restarted = await control.restart(
        actor=actor,
        surface_id=SurfaceId("surface-app"),
        idempotency_key="restart-operation-0001",
    )
    current = await surfaces.get(actor=actor, surface_id=SurfaceId("surface-app"))
    assert restarted.generation == 2
    assert current.lifecycle is SurfaceLifecycle.READY
    assert current.instance["generation"] == 2

    stopped = await control.stop(
        actor=actor,
        surface_id=SurfaceId("surface-app"),
        idempotency_key="stop-operation-0001",
    )
    current = await surfaces.get(actor=actor, surface_id=SurfaceId("surface-app"))
    assert stopped.state == "stopped"
    assert current.lifecycle is SurfaceLifecycle.STOPPED
    with pytest.raises(LiveAppControlError, match="Stop is not available"):
        await control.stop(
            actor=actor,
            surface_id=SurfaceId("surface-app"),
            idempotency_key="stop-operation-0002",
        )
    assert manager.calls == [
        "start:start-operation-0001",
        "restart:instance-1:restart-operation-0001",
        "stop:instance-1:stop-operation-0001",
    ]


async def test_failed_start_projects_safe_retryable_diagnostic(tmp_path: Path) -> None:
    control, surfaces, manager = _service(tmp_path)
    failed = _instance(state="failed")
    manager.start_error = LiveAppManagerError(
        "SURFACE_START_FAILED",
        "Managed application could not start",
        instance=failed,
        retryable=True,
    )
    with pytest.raises(LiveAppControlError) as error:
        await control.start(
            actor=_actor(),
            surface_id=SurfaceId("surface-app"),
            idempotency_key="failed-start-0001",
        )
    assert error.value.code == "SURFACE_START_FAILED"
    current = await surfaces.get(
        actor=_actor(), surface_id=SurfaceId("surface-app")
    )
    assert current.lifecycle is SurfaceLifecycle.FAILED
    assert current.diagnostic_summary == {
        "code": "SURFACE_START_FAILED",
        "message": "App failed",
        "retryable": True,
    }
