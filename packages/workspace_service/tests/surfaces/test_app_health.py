from __future__ import annotations

from collections import deque

import pytest

from core.surfaces.live_app_manifest import Probe
from workspace_service.surfaces.health import (
    HealthProber,
    ProbeResponse,
    ProbeTarget,
    RestartBudget,
)


pytestmark = pytest.mark.workspace_surfaces


class Clock:
    def __init__(self) -> None:
        self.value = 100.0

    def monotonic(self) -> float:
        return self.value

    async def sleep(self, seconds: float) -> None:
        self.value += seconds


class FakeTransport:
    def __init__(self, *results) -> None:
        self.results = deque(results)
        self.calls = 0

    async def request(self, *, target, probe, timeout_seconds):
        self.calls += 1
        result = self.results.popleft()
        if isinstance(result, BaseException):
            raise result
        return result


def _probe(timeout_ms: int = 1_000) -> Probe:
    return Probe(
        path="/health",
        method="GET",
        expected_status=200,
        timeout_ms=timeout_ms,
        interval_ms=100,
    )


def _target() -> ProbeTarget:
    return ProbeTarget(
        scheme="http",
        numeric_address="127.0.0.1",
        port=43123,
        host_header="127.0.0.1:43123",
        server_name=None,
    )


@pytest.mark.asyncio
async def test_readiness_retries_transport_failures_then_succeeds() -> None:
    clock = Clock()
    transport = FakeTransport(
        ConnectionRefusedError(),
        ProbeResponse(status=200, body_bytes=0),
    )
    result = await HealthProber(
        transport=transport,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    ).wait_ready(
        target=_target(),
        probe=_probe(),
        process_alive=lambda: True,
        ownership_valid=lambda: True,
    )

    assert result.ok is True
    assert result.attempts == 2
    assert result.last_failure_kind == "target-transport"


@pytest.mark.asyncio
async def test_application_status_failure_is_distinct_and_actionable() -> None:
    clock = Clock()
    transport = FakeTransport(*(ProbeResponse(status=503, body_bytes=12) for _ in range(20)))
    result = await HealthProber(
        transport=transport,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    ).wait_ready(
        target=_target(),
        probe=_probe(timeout_ms=300),
        process_alive=lambda: True,
        ownership_valid=lambda: True,
    )

    assert result.ok is False
    assert result.failure_kind == "application-status"
    assert result.diagnostic_code == "SURFACE_READINESS_STATUS_MISMATCH"
    assert result.observed_status == 503
    assert "expected HTTP 200" in result.message


@pytest.mark.asyncio
async def test_crash_timeout_and_ownership_failure_are_not_reported_as_health() -> None:
    clock = Clock()
    crash = await HealthProber(
        transport=FakeTransport(ConnectionRefusedError()),
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    ).wait_ready(
        target=_target(),
        probe=_probe(),
        process_alive=lambda: False,
        ownership_valid=lambda: True,
    )
    assert crash.failure_kind == "process-exit"
    assert crash.diagnostic_code == "SURFACE_PROCESS_EXITED_BEFORE_READY"

    ownership = await HealthProber(
        transport=FakeTransport(ConnectionRefusedError()),
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    ).wait_ready(
        target=_target(),
        probe=_probe(),
        process_alive=lambda: True,
        ownership_valid=lambda: False,
    )
    assert ownership.failure_kind == "ownership"
    assert ownership.diagnostic_code == "SURFACE_TARGET_OWNERSHIP_MISMATCH"


@pytest.mark.asyncio
async def test_single_health_check_classifies_transport_and_application() -> None:
    transport = FakeTransport(ConnectionResetError())
    prober = HealthProber(transport=transport)
    transport_result = await prober.check(target=_target(), probe=_probe())
    assert transport_result.failure_kind == "target-transport"

    application = await HealthProber(
        transport=FakeTransport(ProbeResponse(status=500, body_bytes=0))
    ).check(target=_target(), probe=_probe())
    assert application.failure_kind == "application-status"


def test_restart_budget_is_exact_rolling_window_and_never_implicit_unlimited() -> None:
    current = [100.0]
    budget = RestartBudget(
        maximum_restarts=2,
        window_seconds=300,
        monotonic=lambda: current[0],
    )
    assert budget.consume() is True
    assert budget.consume() is True
    assert budget.consume() is False
    assert budget.remaining == 0

    current[0] += 301
    assert budget.consume() is True
    assert budget.remaining == 1
