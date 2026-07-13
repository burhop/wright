from __future__ import annotations

import asyncio

import pytest

from tool_registry.lifecycle import McpLifecycleCoordinator


class FakeRunner:
    def __init__(self, name: str, *, gate: asyncio.Event | None = None) -> None:
        self.name = name
        self.gate = gate
        self.running = False
        self.stop_count = 0

    async def start(self) -> None:
        if self.gate is not None:
            await self.gate.wait()
        self.running = True

    async def stop(self) -> None:
        self.running = False
        self.stop_count += 1

    async def list_tools(self) -> list[dict]:
        return [{"name": self.name}]

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        return {"runner": self.name, **arguments}

    def is_running(self) -> bool:
        return self.running


@pytest.mark.asyncio
async def test_concurrent_starts_leave_one_current_generation() -> None:
    runners: list[FakeRunner] = []

    def factory(
        server_id: str, workspace_path: str | None, approval_context
    ) -> FakeRunner:
        runner = FakeRunner(f"runner-{len(runners) + 1}")
        runners.append(runner)
        return runner

    coordinator = McpLifecycleCoordinator(factory)
    generations = await asyncio.gather(
        *(coordinator.start("cad", workspace_path="/w") for _ in range(20))
    )

    assert generations == list(range(1, 21))
    assert coordinator.generation_for("cad") == 20
    assert coordinator.live_runner_count() == 1
    assert sum(runner.is_running() for runner in runners) == 1
    assert runners[-1].is_running()

    await coordinator.shutdown()
    assert coordinator.live_runner_count() == 0
    assert sum(runner.is_running() for runner in runners) == 0


@pytest.mark.asyncio
async def test_restart_invalidates_in_flight_tool_result() -> None:
    runners: list[FakeRunner] = []

    def factory(
        server_id: str, workspace_path: str | None, approval_context
    ) -> FakeRunner:
        runner = FakeRunner(f"runner-{len(runners) + 1}")

        async def slow_call(tool_name: str, arguments: dict) -> dict:
            await asyncio.sleep(0.02)
            return {"stale": True}

        runner.call_tool = slow_call  # type: ignore[method-assign]
        runners.append(runner)
        return runner

    coordinator = McpLifecycleCoordinator(factory)
    await coordinator.start("cad")
    call = asyncio.create_task(coordinator.call_tool("cad", "draw", {}))
    await asyncio.sleep(0)
    await coordinator.restart("cad")

    with pytest.raises(asyncio.CancelledError):
        await call


@pytest.mark.asyncio
async def test_shutdown_is_bounded_and_rejects_new_starts() -> None:
    runner = FakeRunner("runner")
    coordinator = McpLifecycleCoordinator(lambda *_: runner, shutdown_timeout=0.1)
    await coordinator.start("cad")
    await coordinator.shutdown()

    assert not runner.is_running()
    assert coordinator.owned_task_count() == 0
    with pytest.raises(RuntimeError, match="shutting down"):
        await coordinator.start("cad")
