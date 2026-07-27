from __future__ import annotations

import asyncio

import pytest

from tool_registry.lifecycle import McpLifecycleCoordinator


class Runner:
    def __init__(self, *, fail_start: bool = False, hang_stop: bool = False) -> None:
        self.fail_start = fail_start
        self.hang_stop = hang_stop
        self.running = False

    async def start(self) -> None:
        if self.fail_start:
            raise RuntimeError("start failed")
        self.running = True

    async def stop(self) -> None:
        if self.hang_stop:
            await asyncio.Event().wait()
        self.running = False

    async def list_tools(self) -> list[dict]:
        return []

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        await asyncio.Event().wait()
        return {}

    def is_running(self) -> bool:
        return self.running


@pytest.mark.asyncio
async def test_reconciliation_reports_failure_without_blocking_other_servers() -> None:
    runners = {"good": Runner(), "bad": Runner(fail_start=True)}
    coordinator = McpLifecycleCoordinator(
        lambda server_id, workspace_path, approval: runners[server_id]
    )

    failures = await coordinator.reconcile({"good": "/one", "bad": "/two"})

    assert set(failures) == {"bad"}
    assert runners["good"].running
    assert not runners["bad"].running
    await coordinator.shutdown()


@pytest.mark.asyncio
async def test_tool_timeout_and_shutdown_stop_are_bounded() -> None:
    runner = Runner(hang_stop=True)
    coordinator = McpLifecycleCoordinator(
        lambda *_: runner,
        operation_timeout=0.01,
        shutdown_timeout=0.05,
    )
    await coordinator.start("cad")

    with pytest.raises(TimeoutError):
        await coordinator.call_tool("cad", "hang", {}, timeout=0.005)

    await asyncio.wait_for(coordinator.shutdown(), timeout=0.1)
    assert coordinator.live_runner_count() == 0
    assert coordinator.owned_task_count() == 0
