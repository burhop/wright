from __future__ import annotations

import asyncio
import threading
import time

import pytest

from workspace_service.errors import WorkspaceTimeoutError
from workspace_service.executor import BoundedExecutor


@pytest.mark.asyncio
async def test_bounded_executor_returns_results_and_rejects_after_close():
    executor = BoundedExecutor(max_workers=1)
    assert await executor.run("answer", lambda: 42, timeout_seconds=1) == 42
    await executor.close()
    with pytest.raises(RuntimeError, match="closed"):
        await executor.run("answer", lambda: 42, timeout_seconds=1)


@pytest.mark.asyncio
async def test_bounded_executor_enforces_deadline():
    executor = BoundedExecutor(max_workers=1)
    started = time.monotonic()
    with pytest.raises(WorkspaceTimeoutError):
        await executor.run("slow", lambda: time.sleep(0.2), timeout_seconds=0.02)
    assert time.monotonic() - started < 0.15
    await executor.close()


@pytest.mark.asyncio
async def test_bounded_executor_limits_concurrency():
    executor = BoundedExecutor(max_workers=2)
    active = 0
    peak = 0
    lock = threading.Lock()

    def work() -> None:
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        time.sleep(0.03)
        with lock:
            active -= 1

    await asyncio.gather(
        *(executor.run("bounded", work, timeout_seconds=1) for _ in range(8))
    )
    assert peak == 2
    await executor.close()
