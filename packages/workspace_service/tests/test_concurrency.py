from __future__ import annotations

import asyncio
import threading

import pytest

from workspace_service.adapters.filesystem import LocalWorkspaceFiles
from workspace_service.executor import BoundedExecutor
from workspace_service.use_cases.files import WorkspaceFileUseCases


@pytest.mark.asyncio
async def test_one_hundred_concurrent_workspace_iterations_remain_isolated(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    executor = BoundedExecutor(max_workers=4)
    use_cases = WorkspaceFileUseCases("unused", executor, LocalWorkspaceFiles)

    async def iteration(index: int) -> None:
        await asyncio.gather(
            use_cases.write(str(first), f"first-{index}.txt", f"A-{index}"),
            use_cases.write(str(second), f"second-{index}.txt", f"B-{index}"),
        )

    for index in range(100):
        await iteration(index)

    assert not list(first.glob("second-*.txt"))
    assert not list(second.glob("first-*.txt"))
    assert len(list(first.glob("first-*.txt"))) == 100
    assert len(list(second.glob("second-*.txt"))) == 100
    await executor.close()


@pytest.mark.asyncio
async def test_cancellation_returns_promptly_and_executor_owns_worker_shutdown():
    executor = BoundedExecutor(max_workers=1)
    release = threading.Event()
    task = asyncio.create_task(
        executor.run("cancelled", release.wait, timeout_seconds=5)
    )
    await asyncio.sleep(0.02)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    release.set()
    await executor.close()
