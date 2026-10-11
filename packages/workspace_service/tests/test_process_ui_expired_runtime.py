"""Actual isolated static processes; synthetic UI/model, no engineering execution.

The presentation clock advances in this test, never the host clock. CAD hosts,
live workspace databases and external providers are not involved.
"""

from datetime import timedelta
from unittest.mock import AsyncMock

import httpx
import psutil
import pytest

from core.surfaces.models import SurfaceLifecycle
from workspace_service.config import (
    SurfaceFeatureFlags,
    SurfacePolicySettings,
    SurfacePreviewSettings,
    WorkspaceSurfaceSettings,
)
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.surfaces.live_app_runtime import LiveAppRuntimeRegistry
from workspace_service.surfaces.live_app_service import LiveAppControlService
from workspace_service.surfaces.revocation import RevocationCoordinator
from packages.workspace_service.tests.test_process_ui_presentations import (
    native_case,
    build,
)


@pytest.mark.asyncio
async def test_expired_static_host_releases_real_capacity_and_preserves_saved_artifacts(
    tmp_path, monkeypatch
):
    case = native_case(tmp_path, monkeypatch)
    job = await build(case)
    immutable = {
        str(path.relative_to(tmp_path)): path.read_bytes()
        for path in (tmp_path / ".wright/process-uis").rglob("*")
        if path.is_file()
    }
    accepted_source = (tmp_path / case.process.source_path).read_bytes()
    assert immutable
    registry = LiveAppRuntimeRegistry(
        tmp_path / "state.db",
        settings=WorkspaceSurfaceSettings(
            flags=SurfaceFeatureFlags(model=True, live_apps=True),
            preview=SurfacePreviewSettings(),
            policy=SurfacePolicySettings(owned_apps_per_workspace=1),
        ),
        revocation=RevocationCoordinator(tmp_path / "state.db"),
    )
    case.surfaces.live_apps = LiveAppControlService(
        surfaces=case.surfaces.service, manager_for_workspace=registry.manager_for
    )
    case.application.runs.start = AsyncMock(side_effect=AssertionError("No run start"))
    case.author.engine.stream_chat = AsyncMock(
        side_effect=AssertionError("No model call")
    )
    presentations = case.surfaces.presentation_service
    now = presentations.clock()
    monkeypatch.setattr(presentations, "clock", lambda: now)
    processes = []
    try:
        old = await case.owner.open(
            case.scope,
            case.process,
            case.actor,
            job.job_id,
            "abandoned",
            read_only=True,
        )
        manager = registry.manager_for("workspace")
        old_host = manager.get(old["launch"].instance_id)
        # Native supervisor evidence includes PID and creation time.
        identity = manager._supervisor.snapshot(old_host.runtime_id).identity
        processes.append((identity.pid, identity.creation_time))
        assert psutil.Process(identity.pid).is_running()
        with pytest.raises(ProcessInterfaceError, match="open interface limit"):
            await case.owner.open(
                case.scope,
                case.process,
                case.actor,
                job.job_id,
                "before-expiry",
                read_only=True,
            )
        assert manager.get(old_host.instance_id).state == "ready"
        now += timedelta(hours=8)
        fresh = await case.owner.open(
            case.scope,
            case.process,
            case.actor,
            job.job_id,
            "after-expiry",
            read_only=True,
        )
        assert (
            presentations.get_record(
                actor=case.actor, presentation_id=old["launch"].presentation_id
            ).state
            == "closed"
        )
        assert manager.get(old_host.instance_id).state == "stopped"
        assert not psutil.pid_exists(identity.pid) or (
            psutil.Process(identity.pid).create_time() != identity.creation_time
        )
        assert fresh["descriptor"].lifecycle is SurfaceLifecycle.READY
        new_host = manager.get(fresh["launch"].instance_id)
        new_identity = manager._supervisor.snapshot(new_host.runtime_id).identity
        processes.append((new_identity.pid, new_identity.creation_time))
        target = manager.resolve_route(
            new_host.instance_id, generation=new_host.generation
        ).target
        async with httpx.AsyncClient(trust_env=False) as client:
            response = await client.get(
                f"http://127.0.0.1:{target.port}/__wright/health"
            )
            assert response.status_code == 200
        assert (tmp_path / case.process.source_path).read_bytes() == accepted_source
        assert {
            str(path.relative_to(tmp_path)): path.read_bytes()
            for path in (tmp_path / ".wright/process-uis").rglob("*")
            if path.is_file()
        } == immutable
        case.application.runs.start.assert_not_called()
        case.application.runs.cancel.assert_not_called()
    finally:
        await registry.shutdown()
    assert all(
        not psutil.pid_exists(pid) or psutil.Process(pid).create_time() != created
        for pid, created in processes
    )
