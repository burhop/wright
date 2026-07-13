from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol

from core.logging import get_logger  # type: ignore[import-untyped]
from core.redaction import redact_text  # type: ignore[import-untyped]

logger = get_logger(__name__)


class Runner(Protocol):
    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    async def list_tools(self) -> list[dict[str, Any]]: ...

    async def call_tool(
        self, tool_name: str, arguments: Mapping[str, Any]
    ) -> dict[str, Any]: ...

    def is_running(self) -> bool: ...


class DesiredState(StrEnum):
    STOPPED = "stopped"
    RUNNING = "running"


@dataclass(slots=True)
class LifecycleSlot:
    server_id: str
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    generation: int = 0
    runner: Runner | None = None
    desired_state: DesiredState = DesiredState.STOPPED
    owned_tasks: set[asyncio.Task[Any]] = field(default_factory=set)


RunnerFactory = Callable[[str, str | None, Any], Awaitable[Runner] | Runner]
ToolPublisher = Callable[[str, Sequence[dict[str, Any]], int], Awaitable[None]]
StatusPublisher = Callable[[str, str, str | None, int], Awaitable[None]]


class McpLifecycleCoordinator:
    def __init__(
        self,
        runner_factory: RunnerFactory,
        *,
        publish_tools: ToolPublisher | None = None,
        publish_status: StatusPublisher | None = None,
        operation_timeout: float = 30.0,
        shutdown_timeout: float = 10.0,
    ) -> None:
        self._runner_factory = runner_factory
        self._publish_tools = publish_tools or _noop_tools
        self._publish_status = publish_status or _noop_status
        self._operation_timeout = operation_timeout
        self._shutdown_timeout = shutdown_timeout
        self._slots: dict[str, LifecycleSlot] = {}
        self._slots_lock = asyncio.Lock()
        self._closing = False

    async def start(
        self,
        server_id: str,
        *,
        workspace_path: str | None = None,
        approval_context: Any = None,
    ) -> int:
        slot = await self._slot(server_id)
        async with slot.lock:
            self._ensure_open()
            generation = slot.generation + 1
            slot.generation = generation
            slot.desired_state = DesiredState.RUNNING
            previous = slot.runner
            slot.runner = None
            if previous is not None:
                await self._bounded_stop(previous, server_id, generation)

            candidate = self._runner_factory(
                server_id, workspace_path, approval_context
            )
            runner = await candidate if isinstance(candidate, Awaitable) else candidate
            try:
                await asyncio.wait_for(runner.start(), self._operation_timeout)
                tools = await asyncio.wait_for(
                    runner.list_tools(), self._operation_timeout
                )
            except BaseException as exc:
                await self._bounded_stop(runner, server_id, generation)
                if self._current(slot, generation):
                    slot.desired_state = DesiredState.STOPPED
                    await self._publish_status(
                        server_id, "error", redact_text(exc), generation
                    )
                raise

            if not self._current(slot, generation) or self._closing:
                await self._bounded_stop(runner, server_id, generation)
                return generation

            slot.runner = runner
            await self._publish_tools(server_id, tools, generation)
            await self._publish_status(server_id, "active", None, generation)
            return generation

    async def stop(self, server_id: str) -> int:
        slot = await self._slot(server_id)
        async with slot.lock:
            generation = slot.generation + 1
            slot.generation = generation
            slot.desired_state = DesiredState.STOPPED
            runner, slot.runner = slot.runner, None
            if runner is not None:
                await self._bounded_stop(runner, server_id, generation)
            await self._publish_tools(server_id, (), generation)
            await self._publish_status(server_id, "inactive", None, generation)
            return generation

    async def restart(
        self,
        server_id: str,
        *,
        workspace_path: str | None = None,
        approval_context: Any = None,
    ) -> int:
        await self.stop(server_id)
        return await self.start(
            server_id,
            workspace_path=workspace_path,
            approval_context=approval_context,
        )

    async def call_tool(
        self,
        server_id: str,
        tool_name: str,
        arguments: Mapping[str, Any],
        *,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        slot = await self._slot(server_id)
        async with slot.lock:
            runner = slot.runner
            generation = slot.generation
            if runner is None or not runner.is_running():
                raise RuntimeError(f"MCP server '{server_id}' is not active")
        result = await asyncio.wait_for(
            runner.call_tool(tool_name, arguments),
            min(timeout or self._operation_timeout, self._operation_timeout),
        )
        if not self._current(slot, generation):
            raise asyncio.CancelledError("MCP server generation was superseded")
        return result

    async def reconcile(
        self, desired: Mapping[str, str | None]
    ) -> dict[str, BaseException]:
        failures: dict[str, BaseException] = {}

        async def start_one(server_id: str, workspace_path: str | None) -> None:
            try:
                await self.start(server_id, workspace_path=workspace_path)
            except BaseException as exc:
                failures[server_id] = exc

        tasks = [
            asyncio.create_task(start_one(server_id, workspace_path))
            for server_id, workspace_path in desired.items()
        ]
        if tasks:
            await asyncio.gather(*tasks)
        return failures

    async def shutdown(self) -> None:
        self._closing = True
        slots = list(self._slots.values())

        async def close_slot(slot: LifecycleSlot) -> None:
            async with slot.lock:
                slot.generation += 1
                slot.desired_state = DesiredState.STOPPED
                runner, slot.runner = slot.runner, None
                tasks = list(slot.owned_tasks)
                for task in tasks:
                    task.cancel()
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                if runner is not None:
                    await self._bounded_stop(runner, slot.server_id, slot.generation)

        try:
            await asyncio.wait_for(
                asyncio.gather(*(close_slot(slot) for slot in slots)),
                self._shutdown_timeout,
            )
        except TimeoutError:
            logger.error("mcp_lifecycle_shutdown_timed_out")

    def runner_for(self, server_id: str) -> Runner | None:
        slot = self._slots.get(server_id)
        return slot.runner if slot else None

    def generation_for(self, server_id: str) -> int:
        slot = self._slots.get(server_id)
        return slot.generation if slot else 0

    def live_runner_count(self) -> int:
        return sum(slot.runner is not None for slot in self._slots.values())

    def owned_task_count(self) -> int:
        return sum(len(slot.owned_tasks) for slot in self._slots.values())

    async def _slot(self, server_id: str) -> LifecycleSlot:
        async with self._slots_lock:
            return self._slots.setdefault(server_id, LifecycleSlot(server_id))

    def _current(self, slot: LifecycleSlot, generation: int) -> bool:
        return (
            slot.generation == generation and slot.desired_state is DesiredState.RUNNING
        )

    def _ensure_open(self) -> None:
        if self._closing:
            raise RuntimeError("MCP lifecycle coordinator is shutting down")

    async def _bounded_stop(
        self, runner: Runner, server_id: str, generation: int
    ) -> None:
        try:
            await asyncio.wait_for(runner.stop(), self._operation_timeout)
        except BaseException as exc:
            logger.warning(
                "mcp_runner_stop_failed",
                server_id=server_id,
                generation=generation,
                error=redact_text(exc),
            )


async def _noop_tools(
    server_id: str, tools: Sequence[dict[str, Any]], generation: int
) -> None:
    return None


async def _noop_status(
    server_id: str, status: str, error: str | None, generation: int
) -> None:
    return None
