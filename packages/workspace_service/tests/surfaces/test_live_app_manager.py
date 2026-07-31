from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from core.surfaces.live_app_manifest import parse_live_app_manifest
from workspace_service.config import SurfacePolicySettings
from workspace_service.surfaces.endpoints import (
    EndpointError,
    EndpointOwnershipProof,
    ListenerIdentity,
    RuntimeIdentity,
)
from workspace_service.surfaces.health import ProbeResult
from workspace_service.surfaces.limits import SurfaceLimitPolicy
from workspace_service.surfaces.live_app_manager import (
    LiveAppManager,
    LiveAppManagerError,
    LiveAppStartRequest,
)
from workspace_service.surfaces.manifests import AttachApproval, DiscoveredManifest
from workspace_service.surfaces.process_supervisor import (
    PlatformProcessIdentity,
    ProcessStopResult,
    RuntimeSnapshot,
)
from workspace_service.surfaces.target_pins import TargetPinError, TargetPinRegistry
from workspace_service.surfaces.target_policy import TargetPolicy


pytestmark = [pytest.mark.workspace_surfaces, pytest.mark.asyncio]


class Clock:
    def __init__(self) -> None:
        self.value = datetime(2026, 7, 30, tzinfo=UTC)
        self.monotonic_value = 100.0

    def now(self) -> datetime:
        return self.value

    def monotonic(self) -> float:
        return self.monotonic_value

    def advance(self, seconds: int) -> None:
        self.value += timedelta(seconds=seconds)
        self.monotonic_value += seconds


def _manifest(*, sharing: str = "shared", lifetime: dict | None = None):
    return parse_live_app_manifest(
        {
            "schemaVersion": 1,
            "id": "demo.app",
            "version": "1.0.0",
            "title": "Demo",
            "ownershipPolicy": "wright-owned",
            "launch": {
                "mode": "command",
                "argv": ["python", "app.py", "--port", "${WRIGHT_PORT}"],
                "workingDirectory": ".",
            },
            "readiness": {
                "path": "/health",
                "expectedStatus": 200,
                "timeoutMs": 1_000,
            },
            "presentation": {
                "panel": True,
                "browser": True,
                "sharing": sharing,
            },
            "transports": {"http": True, "websocket": True, "sse": True},
            "lifetime": lifetime or {"policy": "workspace"},
            "capabilities": [],
        }
    )


class FakeManifestStore:
    def __init__(self, manifest, root: Path) -> None:
        self.item = DiscoveredManifest(manifest, ".wright/apps/demo.surface.json", root)

    def authorize(self, manifest_id, *, attach_approval=None):
        assert manifest_id == "demo.app"
        return self.item


class FakeReservation:
    def __init__(
        self,
        instance_id,
        generation,
        port,
        fail_ownership=False,
        inherit_listener=False,
    ) -> None:
        self.instance_id = instance_id
        self.generation = generation
        self.address = "127.0.0.1"
        self.port = port
        self.listener_handle = None
        self.inherit_listener = inherit_listener
        self.fail_ownership = fail_ownership
        self.released = False
        self.closed = False

    def release_immediately_before_spawn(self):
        self.released = True

    def prove_listener_ownership(self, *, runtime, inspector):
        if self.fail_ownership:
            raise EndpointError(
                "SURFACE_TARGET_OWNERSHIP_MISMATCH", "listener was stolen"
            )
        return EndpointOwnershipProof(
            self.instance_id,
            self.generation,
            ListenerIdentity(
                self.address, self.port, runtime.pid, runtime.creation_time
            ),
        )

    def close(self):
        self.closed = True


class FakeAllocator:
    def __init__(self, *, ownership_failures=0) -> None:
        self.reservations = []
        self.ownership_failures = ownership_failures

    def reserve(self, *, instance_id, generation, inherit_listener):
        reservation = FakeReservation(
            instance_id,
            generation,
            43000 + len(self.reservations),
            fail_ownership=len(self.reservations) < self.ownership_failures,
            inherit_listener=inherit_listener,
        )
        self.reservations.append(reservation)
        return reservation


class FakeSupervisor:
    def __init__(self) -> None:
        self.starts = []
        self.stops = []
        self.snapshots = {}
        self.before_stop = None

    async def start(self, **request):
        self.starts.append(request)
        generation = request["generation"]
        runtime_id = f"runtime-{len(self.starts)}"
        snapshot = RuntimeSnapshot(
            runtime_id=runtime_id,
            workspace_id=request["workspace_id"],
            instance_id=request["instance_id"],
            generation=generation,
            status="running",
            identity=PlatformProcessIdentity(
                "fake",
                100 + generation,
                50.0 + generation,
                f"group-{generation}",
                "hard",
            ),
            started_at=datetime(2026, 7, 30, tzinfo=UTC),
        )
        self.snapshots[runtime_id] = snapshot
        return snapshot

    def runtime_identity(self, runtime_id):
        snapshot = self.snapshots[runtime_id]
        return RuntimeIdentity(
            snapshot.instance_id,
            snapshot.generation,
            snapshot.identity.pid,
            snapshot.identity.creation_time,
        )

    def snapshot(self, runtime_id):
        return self.snapshots[runtime_id]

    async def stop(self, *, runtime_id, generation, deadline):
        if self.before_stop:
            self.before_stop(runtime_id, generation)
        self.stops.append((runtime_id, generation))
        stopped = replace(
            self.snapshots[runtime_id],
            status="stopped",
            exit_code=0,
            stop_result=ProcessStopResult(0, True, False, (), ()),
        )
        self.snapshots[runtime_id] = stopped
        return stopped


class FakeHealth:
    def __init__(self, results=None) -> None:
        self.calls = 0
        self.results = list(results or [])

    async def wait_ready(self, **_kwargs):
        self.calls += 1
        await asyncio.sleep(0)
        if self.results:
            return self.results.pop(0)
        return ProbeResult(True, 1, 0.1, None, None, "ready", 200)


def _manager(
    tmp_path,
    *,
    manifest=None,
    allocator=None,
    clock=None,
    ids=None,
    policy=None,
    health=None,
    target_policy=None,
):
    clock = clock or Clock()
    supervisor = FakeSupervisor()
    target_policy = target_policy or TargetPolicy()
    pins = TargetPinRegistry(policy=target_policy, clock=clock.now)
    id_values = iter(ids or [f"instance-{index}" for index in range(1, 20)])
    manager = LiveAppManager(
        manifests=FakeManifestStore(manifest or _manifest(), tmp_path),
        allocator=allocator or FakeAllocator(),
        supervisor=supervisor,
        health=health or FakeHealth(),
        target_pins=pins,
        target_policy=target_policy,
        limit_policy=SurfaceLimitPolicy(policy or SurfacePolicySettings()),
        listener_inspector=object(),
        secret_resolver=lambda _workspace, _manifest: {},
        public_origin=lambda _workspace, instance: f"http://{instance}.localhost:8000",
        id_factory=lambda: next(id_values),
        clock=clock.now,
        monotonic=clock.monotonic,
    )
    return manager, supervisor, pins, clock


def _request(key: str) -> LiveAppStartRequest:
    return LiveAppStartRequest(
        workspace_id="workspace-1",
        surface_id="surface-1",
        manifest_id="demo.app",
        user_id="user-1",
        session_id="session-1",
        idempotency_key=key,
    )


async def test_shared_concurrent_and_idempotent_starts_return_one_ready_instance(
    tmp_path,
) -> None:
    manager, supervisor, _pins, _clock = _manager(tmp_path)
    first, second = await asyncio.gather(
        manager.start(_request("open-1")), manager.start(_request("open-2"))
    )
    repeated = await manager.start(_request("open-1"))

    assert first == second == repeated
    assert first.state == "ready"
    assert first.generation == 1
    assert len(supervisor.starts) == 1


async def test_isolated_starts_are_distinct_and_port_ownership_retry_increments_generation(
    tmp_path,
) -> None:
    allocator = FakeAllocator(ownership_failures=1)
    manager, supervisor, _pins, _clock = _manager(
        tmp_path, manifest=_manifest(sharing="isolated"), allocator=allocator
    )
    first = await manager.start(_request("isolated-1"))
    second = await manager.start(_request("isolated-2"))

    assert first.instance_id != second.instance_id
    assert first.generation == 2
    assert len(supervisor.starts) == 3
    assert allocator.reservations[0].closed is True
    assert allocator.reservations[0].port != allocator.reservations[1].port


async def test_restart_generation_budget_and_stop_are_exact_and_idempotent(
    tmp_path,
) -> None:
    policy = SurfacePolicySettings(restart_attempts=2, restart_window_seconds=300)
    manager, supervisor, pins, _clock = _manager(tmp_path, policy=policy)
    started = await manager.start(_request("start"))

    restarted = await manager.restart(
        started.instance_id, idempotency_key="restart-1", automatic=True
    )
    restarted = await manager.restart(
        restarted.instance_id, idempotency_key="restart-2", automatic=True
    )
    with pytest.raises(LiveAppManagerError) as raised:
        await manager.restart(
            restarted.instance_id, idempotency_key="restart-3", automatic=True
        )
    assert raised.value.code == "SURFACE_RESTART_BUDGET_EXHAUSTED"
    assert restarted.generation == 3

    def pin_was_revoked(_runtime_id, generation):
        with pytest.raises(TargetPinError):
            pins.resolve(instance_id=started.instance_id, generation=generation)

    supervisor.before_stop = pin_was_revoked
    stopped = await manager.stop(started.instance_id, idempotency_key="stop-1")
    repeated = await manager.stop(started.instance_id, idempotency_key="stop-1")
    assert stopped == repeated
    assert stopped.state == "stopped"


async def test_failed_start_can_be_retried_with_a_new_generation(tmp_path) -> None:
    health = FakeHealth(
        [
            ProbeResult(
                False,
                3,
                1.0,
                "timeout",
                "SURFACE_READINESS_TIMEOUT",
                "not ready",
            ),
            ProbeResult(True, 1, 0.1, None, None, "ready", 200),
        ]
    )
    manager, supervisor, _pins, _clock = _manager(tmp_path, health=health)
    with pytest.raises(LiveAppManagerError) as raised:
        await manager.start(_request("failed-start"))
    failed = raised.value.instance
    assert failed is not None and failed.state == "failed"

    retried = await manager.retry(
        failed.instance_id, idempotency_key="retry-after-failure"
    )
    assert retried.state == "ready"
    assert retried.generation == 2
    assert len(supervisor.starts) == 2


async def test_approved_attach_is_probed_and_pinned_without_process_ownership(
    tmp_path,
) -> None:
    manifest = parse_live_app_manifest(
        {
            "schemaVersion": 1,
            "id": "demo.app",
            "version": "1.0.0",
            "title": "Attached Demo",
            "ownershipPolicy": "approved-attach",
            "launch": {
                "mode": "attach",
                "url": "https://app.example.test/base",
                "ownershipProof": "operator-approved",
            },
            "readiness": {
                "path": "/health",
                "expectedStatus": 200,
                "timeoutMs": 1_000,
            },
            "presentation": {"panel": True, "browser": True, "sharing": "shared"},
            "transports": {"http": True, "websocket": True, "sse": True},
            "capabilities": [],
        }
    )

    class Resolver:
        def resolve_all(self, hostname):
            assert hostname == "app.example.test"
            return ("8.8.8.8",)

    manager, supervisor, pins, clock = _manager(
        tmp_path,
        manifest=manifest,
        target_policy=TargetPolicy(resolver=Resolver()),
    )
    approval = AttachApproval(
        "approval-1",
        "demo.app",
        manifest.canonical_hash,
        "https://app.example.test/base",
        "admin-1",
        clock.now(),
    )
    request = replace(_request("attach"), attach_approval=approval)
    instance = await manager.start(request)

    assert instance.state == "ready"
    assert instance.ownership == "attached_verified"
    assert supervisor.starts == []
    assert (
        pins.resolve(
            instance_id=instance.instance_id, generation=instance.generation
        ).target.numeric_address
        == "8.8.8.8"
    )


async def test_presentation_workspace_lease_idle_and_manual_lifetimes(tmp_path) -> None:
    scenarios = [
        ({"policy": "presentation"}, True),
        ({"policy": "workspace"}, False),
        ({"policy": "lease", "leaseSeconds": 30}, True),
        ({"policy": "idle", "idleSeconds": 30}, True),
        ({"policy": "manual"}, False),
    ]
    for index, (lifetime, should_expire) in enumerate(scenarios):
        manager, _supervisor, _pins, clock = _manager(
            tmp_path,
            manifest=_manifest(lifetime=lifetime),
            ids=[f"lifetime-{index}"],
        )
        instance = await manager.start(_request(f"start-{index}"))
        await manager.presentation_opened(instance.instance_id)
        if lifetime["policy"] == "idle":
            clock.advance(20)
            manager.record_activity(instance.instance_id, "unrelated-workspace-traffic")
            manager.record_activity(instance.instance_id, "presentation-traffic")
            clock.advance(31)
        else:
            clock.advance(31)
        await manager.presentation_closed(instance.instance_id)
        await manager.expire_due()
        state = manager.get(instance.instance_id).state
        assert (state == "stopped") is should_expire


async def test_workspace_shutdown_stops_workspace_lifetime_but_not_other_workspace(
    tmp_path,
) -> None:
    manager, _supervisor, _pins, _clock = _manager(
        tmp_path, manifest=_manifest(lifetime={"policy": "workspace"})
    )
    instance = await manager.start(_request("start"))
    await manager.shutdown_workspace("different-workspace")
    assert manager.get(instance.instance_id).state == "ready"
    await manager.shutdown_workspace("workspace-1")
    assert manager.get(instance.instance_id).state == "stopped"
