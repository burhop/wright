"""Bounded readiness and health probes with actionable failure classes."""

from __future__ import annotations

import asyncio
import time
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Protocol

from core.surfaces.live_app_manifest import Probe


@dataclass(frozen=True, slots=True)
class ProbeTarget:
    scheme: str
    numeric_address: str
    port: int
    host_header: str
    server_name: str | None

    def __post_init__(self) -> None:
        if self.scheme not in {"http", "https"} or not 1 <= self.port <= 65_535:
            raise ValueError("probe target is invalid")


@dataclass(frozen=True, slots=True)
class ProbeResponse:
    status: int
    body_bytes: int

    def __post_init__(self) -> None:
        if not 100 <= self.status <= 599 or not 0 <= self.body_bytes <= 4096:
            raise ValueError("probe response is outside bounded health limits")


class ProbeTransport(Protocol):
    async def request(
        self, *, target: ProbeTarget, probe: Probe, timeout_seconds: float
    ) -> ProbeResponse: ...


@dataclass(frozen=True, slots=True)
class ProbeResult:
    ok: bool
    attempts: int
    elapsed_seconds: float
    failure_kind: str | None
    diagnostic_code: str | None
    message: str
    observed_status: int | None = None
    last_failure_kind: str | None = None


def _failure(
    *,
    attempts: int,
    elapsed: float,
    kind: str,
    code: str,
    message: str,
    status: int | None = None,
    last_failure_kind: str | None = None,
) -> ProbeResult:
    return ProbeResult(
        ok=False,
        attempts=attempts,
        elapsed_seconds=elapsed,
        failure_kind=kind,
        diagnostic_code=code,
        message=message,
        observed_status=status,
        last_failure_kind=last_failure_kind,
    )


class HealthProber:
    def __init__(
        self,
        *,
        transport: ProbeTransport,
        monotonic: Callable[[], float] | None = None,
        sleep: Callable[[float], Awaitable[None]] | None = None,
    ) -> None:
        self._transport = transport
        self._monotonic = monotonic or time.monotonic
        self._sleep = sleep or asyncio.sleep

    async def check(
        self,
        *,
        target: ProbeTarget,
        probe: Probe,
        timeout_seconds: float | None = None,
    ) -> ProbeResult:
        started = self._monotonic()
        bound = timeout_seconds or max(0.1, probe.timeout_ms / 1000)
        try:
            response = await asyncio.wait_for(
                self._transport.request(
                    target=target, probe=probe, timeout_seconds=bound
                ),
                timeout=bound,
            )
        except (TimeoutError, OSError, ConnectionError) as error:
            return _failure(
                attempts=1,
                elapsed=self._monotonic() - started,
                kind="target-transport",
                code="SURFACE_TARGET_TRANSPORT_UNAVAILABLE",
                message=f"Target transport failed before an application response ({type(error).__name__})",
            )
        if response.status != probe.expected_status:
            return _failure(
                attempts=1,
                elapsed=self._monotonic() - started,
                kind="application-status",
                code="SURFACE_READINESS_STATUS_MISMATCH",
                message=(
                    f"Application returned HTTP {response.status}; expected HTTP "
                    f"{probe.expected_status} at the declared probe path"
                ),
                status=response.status,
            )
        return ProbeResult(
            ok=True,
            attempts=1,
            elapsed_seconds=self._monotonic() - started,
            failure_kind=None,
            diagnostic_code=None,
            message="Application probe succeeded",
            observed_status=response.status,
        )

    async def wait_ready(
        self,
        *,
        target: ProbeTarget,
        probe: Probe,
        process_alive: Callable[[], bool],
        ownership_valid: Callable[[], bool],
    ) -> ProbeResult:
        started = self._monotonic()
        deadline = started + probe.timeout_ms / 1000
        attempts = 0
        last: ProbeResult | None = None
        last_failure_kind: str | None = None
        while self._monotonic() <= deadline:
            if not process_alive():
                return _failure(
                    attempts=attempts,
                    elapsed=self._monotonic() - started,
                    kind="process-exit",
                    code="SURFACE_PROCESS_EXITED_BEFORE_READY",
                    message="Managed process exited before the readiness probe succeeded",
                )
            if not ownership_valid():
                return _failure(
                    attempts=attempts,
                    elapsed=self._monotonic() - started,
                    kind="ownership",
                    code="SURFACE_TARGET_OWNERSHIP_MISMATCH",
                    message="Listener ownership no longer matches the managed runtime generation",
                )
            remaining = max(0.001, deadline - self._monotonic())
            attempts += 1
            last = await self.check(
                target=target,
                probe=probe,
                timeout_seconds=min(remaining, max(0.1, probe.interval_ms / 1000)),
            )
            if last.ok:
                return ProbeResult(
                    ok=True,
                    attempts=attempts,
                    elapsed_seconds=self._monotonic() - started,
                    failure_kind=None,
                    diagnostic_code=None,
                    message=last.message,
                    observed_status=last.observed_status,
                    last_failure_kind=last_failure_kind,
                )
            last_failure_kind = last.failure_kind
            if self._monotonic() >= deadline:
                break
            await self._sleep(
                min(probe.interval_ms / 1000, max(0.0, deadline - self._monotonic()))
            )

        if last is not None and last.failure_kind == "application-status":
            return ProbeResult(
                ok=False,
                attempts=attempts,
                elapsed_seconds=self._monotonic() - started,
                failure_kind=last.failure_kind,
                diagnostic_code=last.diagnostic_code,
                message=last.message,
                observed_status=last.observed_status,
                last_failure_kind=last.failure_kind,
            )
        return _failure(
            attempts=attempts,
            elapsed=self._monotonic() - started,
            kind="timeout",
            code="SURFACE_READINESS_TIMEOUT",
            message="Application did not become ready within the declared startup timeout",
            last_failure_kind=last.failure_kind if last else None,
        )


class RestartBudget:
    """Exact rolling-window restart allowance for one runtime generation chain."""

    def __init__(
        self,
        *,
        maximum_restarts: int,
        window_seconds: int,
        monotonic: Callable[[], float] | None = None,
    ) -> None:
        if maximum_restarts < 0 or window_seconds < 1:
            raise ValueError("restart budget bounds are invalid")
        self.maximum_restarts = maximum_restarts
        self.window_seconds = window_seconds
        self._monotonic = monotonic or time.monotonic
        self._events: deque[float] = deque()

    def _prune(self, current: float) -> None:
        boundary = current - self.window_seconds
        while self._events and self._events[0] <= boundary:
            self._events.popleft()

    @property
    def remaining(self) -> int:
        self._prune(self._monotonic())
        return max(0, self.maximum_restarts - len(self._events))

    def consume(self) -> bool:
        current = self._monotonic()
        self._prune(current)
        if len(self._events) >= self.maximum_restarts:
            return False
        self._events.append(current)
        return True


__all__ = [
    "HealthProber",
    "ProbeResponse",
    "ProbeResult",
    "ProbeTarget",
    "ProbeTransport",
    "RestartBudget",
]
