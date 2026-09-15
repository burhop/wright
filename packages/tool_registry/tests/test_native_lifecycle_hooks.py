from __future__ import annotations

import asyncio

import pytest

from tool_registry.lifecycle import McpLifecycleCoordinator, NativeLifecycleBlocked


class Runner:
    def __init__(self, events):
        self.events = events
        self.running = False
        self.gate = None

    async def start(self):
        self.events.append("transport_start")
        self.running = True

    async def stop(self):
        self.events.append("transport_stop")
        self.running = False

    def is_running(self):
        return self.running

    async def list_tools(self):
        return [{"name": "cad"}]

    async def call_tool(self, tool_name, arguments):
        if self.gate:
            await self.gate.wait()
        return {"ok": True}


class Hooks:
    def __init__(self, events):
        self.events = events
        self.cleanup_status = "completed"
        self.reconcile_status = "ready"
        self.hang_cleanup = False
        self.has_unknown = False

    def manages(self, server_id):
        return server_id == "native"

    async def reconcile(self, server_id, runner, generation):
        self.events.append("native_reconcile")
        return {
            "status": "cleanup_blocked" if self.has_unknown else self.reconcile_status
        }

    async def cleanup(self, server_id, runner, generation, reason):
        self.events.append("native_cleanup:" + reason)
        assert (
            runner.is_running()
        )  # transport must remain available for native save/close
        if self.hang_cleanup:
            await asyncio.Event().wait()
        return {"status": self.cleanup_status, "cleanup_id": "durable-cleanup"}

    async def unresolved(self, server_id, runner, generation, reason):
        self.events.append("native_unresolved:" + reason)
        self.has_unknown = True
        return {
            "status": "cleanup_blocked",
            "evidence_reference": "native-unknown.json",
        }


@pytest.fixture
def setup():
    events = []
    runner = Runner(events)
    hooks = Hooks(events)
    coordinator = McpLifecycleCoordinator(
        lambda *_: runner, native_hooks=hooks, operation_timeout=0.1, native_timeout=0.1
    )
    return coordinator, runner, hooks, events


@pytest.mark.asyncio
async def test_cleanup_precedes_transport_shutdown_and_does_not_repeat(setup):
    coordinator, runner, _, events = setup
    await coordinator.start("native")
    await coordinator.stop("native")
    await coordinator.stop("native")
    assert events == [
        "native_reconcile",
        "transport_start",
        "native_cleanup:stop",
        "transport_stop",
    ]
    assert not runner.running
    assert coordinator.native_status_for("native") == {
        "status": "completed",
        "cleanup_id": "durable-cleanup",
        "quarantined": False,
        "unknown_operation": False,
        "transport_retained": False,
    }


@pytest.mark.asyncio
async def test_failed_cleanup_preserves_transport_and_blocks_restart(setup):
    coordinator, runner, hooks, events = setup
    await coordinator.start("native")
    hooks.cleanup_status = "cleanup_blocked"
    with pytest.raises(NativeLifecycleBlocked):
        await coordinator.restart("native")
    assert coordinator.runner_for("native") is runner and runner.running
    assert events.count("transport_start") == 1 and "transport_stop" not in events
    with pytest.raises(NativeLifecycleBlocked):
        await coordinator.call_tool("native", "cad", {})
    hooks.cleanup_status = "completed"
    await coordinator.stop("native")
    assert not runner.running


@pytest.mark.asyncio
async def test_native_timeout_keeps_unknown_operation_until_reconciled(setup):
    coordinator, runner, hooks, events = setup
    await coordinator.start("native")
    runner.gate = asyncio.Event()
    with pytest.raises(TimeoutError):
        await coordinator.call_tool("native", "create", {}, timeout=0.01)
    assert "native_unresolved:tool_timeout" in events
    assert runner.running and "transport_stop" not in events
    with pytest.raises(NativeLifecycleBlocked):
        await coordinator.start("native")
    with pytest.raises(NativeLifecycleBlocked):
        await coordinator.stop("native")
    assert not any(event.startswith("native_cleanup:") for event in events)
    # A concrete adapter reconciliation now establishes the prior outcome.
    hooks.has_unknown = False
    await coordinator.start("native")
    runner.gate.set()
    assert await coordinator.call_tool("native", "create", {}) == {"ok": True}
    await coordinator.stop("native")


@pytest.mark.asyncio
async def test_native_cancellation_does_not_destroy_control_channel(setup):
    coordinator, runner, _, events = setup
    await coordinator.start("native")
    runner.gate = asyncio.Event()
    operation = asyncio.create_task(coordinator.call_tool("native", "create", {}))
    await asyncio.sleep(0)
    operation.cancel()
    with pytest.raises(asyncio.CancelledError):
        await operation
    assert runner.running and coordinator.runner_for("native") is runner
    assert "native_unresolved:tool_cancelled" in events


@pytest.mark.asyncio
async def test_cleanup_timeout_is_recorded_and_channel_retained(setup):
    coordinator, runner, hooks, events = setup
    await coordinator.start("native")
    hooks.hang_cleanup = True
    with pytest.raises(NativeLifecycleBlocked):
        await asyncio.wait_for(coordinator.stop("native"), timeout=0.5)
    assert runner.running and "native_unresolved:native_cleanup_interrupted" in events
    assert coordinator.native_status_for("native")["unknown_operation"]


@pytest.mark.asyncio
async def test_shutdown_keeps_blocked_native_but_stops_independent_transport(setup):
    coordinator, native_runner, hooks, events = setup
    other = Runner(events)
    coordinator._runner_factory = lambda server_id, *_: (
        native_runner if server_id == "native" else other
    )
    await coordinator.start("native")
    await coordinator.start("other")
    hooks.cleanup_status = "cleanup_blocked"
    await coordinator.shutdown()
    assert native_runner.running and not other.running
    assert coordinator.native_status_for("native")["quarantined"]


@pytest.mark.asyncio
async def test_stopping_active_native_call_does_not_invoke_cleanup(setup):
    coordinator, runner, _, events = setup
    await coordinator.start("native")
    runner.gate = asyncio.Event()
    operation = asyncio.create_task(coordinator.call_tool("native", "create", {}))
    await asyncio.sleep(0)
    with pytest.raises(NativeLifecycleBlocked):
        await coordinator.stop("native")
    assert not any(event.startswith("native_cleanup:") for event in events)
    runner.gate.set()
    assert await operation == {"ok": True}
    await coordinator.stop("native")


@pytest.mark.asyncio
async def test_transport_exception_quarantines_native_mutation_without_replay(setup):
    coordinator, runner, _, events = setup
    await coordinator.start("native")

    async def disconnected(*_):
        raise ConnectionError("MCP connection closed after dispatch")

    runner.call_tool = disconnected
    with pytest.raises(ConnectionError):
        await coordinator.call_tool("native", "create", {})
    assert "native_unresolved:tool_transport_failed" in events
    assert runner.running
    with pytest.raises(NativeLifecycleBlocked):
        await coordinator.call_tool("native", "create", {})


@pytest.mark.asyncio
async def test_native_cleanup_uses_native_budget_before_short_transport_shutdown():
    events = []
    runner = Runner(events)
    hooks = Hooks(events)
    cleanup = hooks.cleanup

    async def native_cleanup(*args):
        await asyncio.sleep(0.03)
        return await cleanup(*args)

    hooks.cleanup = native_cleanup
    coordinator = McpLifecycleCoordinator(
        lambda *_: runner, native_hooks=hooks, native_timeout=0.1, shutdown_timeout=0.01
    )
    await coordinator.start("native")
    await coordinator.shutdown()
    assert not runner.running
    assert coordinator.native_status_for("native")["status"] == "completed"
