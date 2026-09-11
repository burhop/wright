from __future__ import annotations

import asyncio
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


def _instance(
    *,
    state: str = "ready",
    generation: int = 1,
    instance_id: str = "instance-1",
) -> LiveAppInstance:
    return LiveAppInstance(
        instance_id=instance_id,
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
        self.start_requests: list[object] = []
        self.compensations: list[tuple[str, int, str]] = []
        self.start_error: LiveAppManagerError | None = None
        self.restart_error: LiveAppManagerError | None = None
        self.health_error: LiveAppManagerError | None = None
        self.get_error: LiveAppManagerError | None = None

    async def start(self, request):
        self.calls.append(f"start:{request.idempotency_key}")
        self.start_requests.append(request)
        if self.start_error:
            raise self.start_error
        return self.instance

    async def restart(self, instance_id: str, *, idempotency_key: str):
        self.calls.append(f"restart:{instance_id}:{idempotency_key}")
        if self.restart_error:
            raise self.restart_error
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

    async def compensate_uncommitted(
        self,
        instance_id: str,
        *,
        generation: int,
        correlation_id: str,
    ):
        assert instance_id == self.instance.instance_id
        assert generation == self.instance.generation
        self.compensations.append((instance_id, generation, correlation_id))
        self.instance = replace(
            self.instance,
            state="failed",
            ended_at=NOW,
            failure=LiveAppFailure(
                "SURFACE_DESCRIPTOR_COMMIT_FAILED",
                f"Runtime contained. Reference {correlation_id}.",
                True,
            ),
        )
        return self.instance

    def get(self, instance_id: str):
        if self.get_error:
            raise self.get_error
        assert instance_id == self.instance.instance_id
        return self.instance

    def presentation_projection(self, instance_id: str):
        assert instance_id == self.instance.instance_id
        return (
            {"kind": "panel", "eligible": True},
            {"kind": "browser", "eligible": True},
        )

    async def check_health(self, instance_id: str):
        assert instance_id == self.instance.instance_id
        if self.health_error:
            raise self.health_error
        return self.instance


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
    current = await surfaces.get(actor=_actor(), surface_id=SurfaceId("surface-app"))
    assert current.lifecycle is SurfaceLifecycle.FAILED
    assert current.diagnostic_summary == {
        "code": "SURFACE_START_FAILED",
        "message": "App failed",
        "retryable": True,
    }


async def test_ready_runtime_is_compensated_when_descriptor_commit_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    control, surfaces, manager = _service(tmp_path)
    project_runtime = surfaces.project_runtime

    async def fail_ready_projection(**kwargs):
        if kwargs["target"] is SurfaceLifecycle.READY:
            raise RuntimeError("simulated descriptor commit failure")
        return await project_runtime(**kwargs)

    monkeypatch.setattr(surfaces, "project_runtime", fail_ready_projection)

    with pytest.raises(LiveAppControlError) as raised:
        await control.start(
            actor=_actor(),
            surface_id=SurfaceId("surface-app"),
            idempotency_key="ready-commit-failure-0001",
        )

    current = await surfaces.get(actor=_actor(), surface_id=SurfaceId("surface-app"))
    assert raised.value.code == "SURFACE_DESCRIPTOR_COMMIT_FAILED"
    assert raised.value.retryable is True
    assert raised.value.correlation_id is not None
    assert manager.compensations == [("instance-1", 1, raised.value.correlation_id)]
    assert manager.instance.state == "failed"
    assert current.lifecycle is SurfaceLifecycle.FAILED
    assert current.instance["generation"] == 1
    assert current.diagnostic_summary["code"] == "SURFACE_DESCRIPTOR_COMMIT_FAILED"
    assert raised.value.correlation_id in current.diagnostic_summary["message"]
    assert "simulated descriptor commit failure" not in str(raised.value)


async def test_after_commit_error_recognizes_authoritative_ready_descriptor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    control, surfaces, manager = _service(tmp_path)
    project_runtime = surfaces.project_runtime

    async def commit_then_raise(**kwargs):
        result = await project_runtime(**kwargs)
        if kwargs["target"] is SurfaceLifecycle.READY:
            raise RuntimeError("simulated post-commit event failure")
        return result

    monkeypatch.setattr(surfaces, "project_runtime", commit_then_raise)

    instance = await control.start(
        actor=_actor(),
        surface_id=SurfaceId("surface-app"),
        idempotency_key="ambiguous-ready-commit-0001",
    )
    current = await surfaces.get(actor=_actor(), surface_id=SurfaceId("surface-app"))

    assert instance.state == "ready"
    assert current.lifecycle is SurfaceLifecycle.READY
    assert manager.compensations == []


async def test_request_cancellation_waits_for_authoritative_ready_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    control, surfaces, manager = _service(tmp_path)
    project_runtime = surfaces.project_runtime
    entered = asyncio.Event()
    release = asyncio.Event()

    async def delayed_ready_projection(**kwargs):
        if kwargs["target"] is SurfaceLifecycle.READY:
            entered.set()
            await release.wait()
        return await project_runtime(**kwargs)

    monkeypatch.setattr(surfaces, "project_runtime", delayed_ready_projection)
    request = asyncio.create_task(
        control.start(
            actor=_actor(),
            surface_id=SurfaceId("surface-app"),
            idempotency_key="cancelled-ready-commit-0001",
        )
    )
    await entered.wait()
    request.cancel()
    await asyncio.sleep(0)
    assert request.done() is False

    release.set()
    with pytest.raises(asyncio.CancelledError):
        await request

    current = await surfaces.get(actor=_actor(), surface_id=SurfaceId("surface-app"))
    assert current.lifecycle is SurfaceLifecycle.READY
    assert current.instance["generation"] == 1
    assert manager.compensations == []


async def test_health_translates_manager_lifecycle_error(tmp_path: Path) -> None:
    control, _surfaces, manager = _service(tmp_path)
    await control.start(
        actor=_actor(),
        surface_id=SurfaceId("surface-app"),
        idempotency_key="start-before-health-0001",
    )
    failed = _instance(state="failed")
    manager.health_error = LiveAppManagerError(
        "SURFACE_LIFECYCLE_CONFLICT",
        "Health cannot be checked from failed",
        instance=failed,
        retryable=False,
    )

    with pytest.raises(LiveAppControlError) as error:
        await control.health(
            actor=_actor(),
            surface_id=SurfaceId("surface-app"),
        )

    assert error.value.code == "SURFACE_LIFECYCLE_CONFLICT"
    assert str(error.value) == "Health cannot be checked from failed"


async def test_inspect_translates_missing_runtime_after_restart(tmp_path: Path) -> None:
    control, _surfaces, manager = _service(tmp_path)
    await control.start(
        actor=_actor(),
        surface_id=SurfaceId("surface-app"),
        idempotency_key="start-before-inspect-0001",
    )
    manager.get_error = LiveAppManagerError(
        "SURFACE_INSTANCE_NOT_FOUND",
        "Live-app instance was not found",
        retryable=True,
    )

    with pytest.raises(LiveAppControlError) as error:
        await control.inspect(
            actor=_actor(),
            surface_id=SurfaceId("surface-app"),
        )

    assert error.value.code == "SURFACE_INSTANCE_NOT_FOUND"
    assert str(error.value) == "Live-app instance was not found"
    assert error.value.retryable is True


async def test_restart_recovers_terminal_surface_when_manager_lost_runtime(
    tmp_path: Path,
) -> None:
    control, surfaces, manager = _service(tmp_path)
    actor = _actor()
    await control.start(
        actor=actor,
        surface_id=SurfaceId("surface-app"),
        idempotency_key="start-before-stale-restart-0001",
    )
    await control.stop(
        actor=actor,
        surface_id=SurfaceId("surface-app"),
        idempotency_key="stop-before-stale-restart-0001",
    )
    manager.restart_error = LiveAppManagerError(
        "SURFACE_INSTANCE_NOT_FOUND",
        "Live-app instance was not found",
        retryable=True,
    )
    manager.instance = _instance(generation=3)

    restarted = await control.restart(
        actor=actor,
        surface_id=SurfaceId("surface-app"),
        idempotency_key="restart-stale-runtime-0001",
    )
    current = await surfaces.get(actor=actor, surface_id=SurfaceId("surface-app"))

    assert restarted.state == "ready"
    assert restarted.generation == 3
    assert current.lifecycle is SurfaceLifecycle.READY
    assert current.instance["generation"] == 3
    assert manager.calls[-2:] == [
        "restart:instance-1:restart-stale-runtime-0001",
        "start:restart-stale-runtime-0001",
    ]


async def test_explicit_retry_after_manager_restart_commits_fresh_authority(
    tmp_path: Path,
) -> None:
    control, surfaces, manager = _service(tmp_path)
    actor = _actor()
    await control.start(
        actor=actor,
        surface_id=SurfaceId("surface-app"),
        idempotency_key="start-before-api-restart-0001",
    )
    current = await surfaces.get(actor=actor, surface_id=SurfaceId("surface-app"))
    failed = await surfaces.project_runtime(
        actor=actor,
        surface_id=SurfaceId("surface-app"),
        target=SurfaceLifecycle.FAILED,
        expected_revision=current.revision,
        instance=current.instance,
        presentations=current.presentations,
        diagnostic_summary={
            "code": "SURFACE_RECONCILE_OWNERSHIP_UNPROVABLE",
            "message": "Runtime authority was revoked during startup reconciliation.",
            "retryable": True,
        },
    )
    assert failed.instance["instanceId"] == "instance-1"
    assert failed.instance["generation"] == 1

    manager.restart_error = LiveAppManagerError(
        "SURFACE_INSTANCE_NOT_FOUND",
        "Live-app instance was not found after API restart",
        retryable=True,
    )
    manager.instance = _instance(
        generation=2,
        instance_id="instance-after-api-restart",
    )

    retried = await control.retry(
        actor=actor,
        surface_id=SurfaceId("surface-app"),
        idempotency_key="retry-after-api-restart-0001",
    )
    committed = await surfaces.get(actor=actor, surface_id=SurfaceId("surface-app"))

    assert retried.instance_id == "instance-after-api-restart"
    assert retried.generation == 2
    assert committed.lifecycle is SurfaceLifecycle.READY
    assert committed.instance["instanceId"] == retried.instance_id
    assert committed.instance["generation"] == retried.generation
    assert manager.start_requests[-1].initial_generation == 2
    assert manager.calls[-2:] == [
        "restart:instance-1:retry-after-api-restart-0001",
        "start:retry-after-api-restart-0001",
    ]
