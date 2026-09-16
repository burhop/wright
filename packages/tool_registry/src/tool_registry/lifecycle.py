from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol

from core.logging import get_logger  # type: ignore[import-untyped]
from core.redaction import redact_text  # type: ignore[import-untyped]
from .runners.base import ProgressCallback

logger = get_logger(__name__)


class Runner(Protocol):
    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    async def list_tools(self) -> list[dict[str, Any]]: ...

    async def call_tool(
        self,
        tool_name: str,
        arguments: Mapping[str, Any],
        *,
        progress_callback: ProgressCallback | None = None,
    ) -> dict[str, Any]: ...

    def is_running(self) -> bool: ...

    async def list_resources(self, cursor: str | None = None) -> dict[str, Any]: ...

    async def list_resource_templates(
        self, cursor: str | None = None
    ) -> dict[str, Any]: ...

    async def read_resource(self, uri: str) -> dict[str, Any]: ...

    async def subscribe_resource(self, uri: str) -> None: ...

    async def unsubscribe_resource(self, uri: str) -> None: ...


class DesiredState(StrEnum):
    STOPPED = "stopped"
    RUNNING = "running"


class SpecializedLifecycleKind(StrEnum):
    ORDINARY = "ordinary"
    PANEL = "panel"
    HOST_BRIDGE = "host_bridge"


@dataclass(frozen=True, slots=True)
class LifecycleProjection:
    """Provider-neutral lifecycle facts safe to expose to governed callers."""

    kind: SpecializedLifecycleKind = SpecializedLifecycleKind.ORDINARY
    visible_application: bool = False
    cancellation_supported: bool = True
    recovery_action: str | None = None

    def canonical(self) -> dict[str, Any]:
        return {
            "kind": str(self.kind),
            "visible_application": self.visible_application,
            "cancellation_supported": self.cancellation_supported,
            "recovery_action": self.recovery_action,
        }


@dataclass(slots=True)
class LifecycleSlot:
    server_id: str
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    generation: int = 0
    runner: Runner | None = None
    desired_state: DesiredState = DesiredState.STOPPED
    owned_tasks: set[asyncio.Task[Any]] = field(default_factory=set)
    active_calls: int = 0
    native_quarantined: bool = False
    native_unknown_operation: bool = False
    native_receipt: dict[str, Any] | None = None


class NativeLifecycleBlocked(RuntimeError):
    """The native resource needs reconciliation; its transport is retained."""


class NativeLifecycleHooks(Protocol):
    """Injected native resource service; callbacks persist their own receipts.

    These hooks must use an independent native control channel or the supplied
    runner directly, rather than re-entering the coordinator's per-server lock.
    The unresolved callback records quarantine without mutating the application.
    """

    def manages(self, server_id: str) -> bool: ...

    async def reconcile(
        self, server_id: str, runner: Runner | None, generation: int
    ) -> Mapping[str, Any]: ...

    async def cleanup(
        self, server_id: str, runner: Runner, generation: int, reason: str
    ) -> Mapping[str, Any]: ...

    async def unresolved(
        self, server_id: str, runner: Runner, generation: int, reason: str
    ) -> Mapping[str, Any]: ...


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
        native_hooks: NativeLifecycleHooks | None = None,
        native_timeout: float = 120.0,
    ) -> None:
        self._runner_factory = runner_factory
        self._publish_tools = publish_tools or _noop_tools
        self._publish_status = publish_status or _noop_status
        self._operation_timeout = operation_timeout
        self._shutdown_timeout = shutdown_timeout
        self._slots: dict[str, LifecycleSlot] = {}
        self._slots_lock = asyncio.Lock()
        self._closing = False
        self._native_hooks = native_hooks
        self._native_timeout = native_timeout

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
            if self._native_managed(server_id) and (
                slot.runner is None or slot.native_quarantined
            ):
                if slot.active_calls:
                    raise NativeLifecycleBlocked(
                        "Native application still has an active operation"
                    )
                await self._reconcile_native(slot)
            # Starting is an idempotent desire, not an implicit restart. Status
            # refreshes and gateway observation may race with a long remote MCP
            # call; replacing a healthy runner here used to cancel that call by
            # changing its generation. Explicit replacement remains `restart()`.
            if (
                slot.desired_state is DesiredState.RUNNING
                and slot.runner is not None
                and slot.runner.is_running()
            ):
                return slot.generation
            generation = slot.generation + 1
            slot.generation = generation
            slot.desired_state = DesiredState.RUNNING
            previous = slot.runner
            if previous is not None:
                if not await self._stop_with_native(
                    slot, previous, generation, "replace"
                ):
                    raise NativeLifecycleBlocked(
                        "Native cleanup blocked transport replacement"
                    )
            slot.runner = None

            candidate = self._runner_factory(
                server_id, workspace_path, approval_context
            )
            runner = await candidate if isinstance(candidate, Awaitable) else candidate
            try:
                startup_timeout = (
                    getattr(runner, "startup_timeout", None) or self._operation_timeout
                )
                await asyncio.wait_for(runner.start(), startup_timeout)
                tools = await asyncio.wait_for(
                    runner.list_tools(), self._operation_timeout
                )
            except BaseException as exc:
                if not await self._stop_with_native(
                    slot, runner, generation, "startup_failed"
                ):
                    slot.runner = runner
                if self._current(slot, generation):
                    slot.desired_state = DesiredState.STOPPED
                    await self._publish_status(
                        server_id, "error", redact_text(exc), generation
                    )
                raise

            if not self._current(slot, generation) or self._closing:
                if not await self._stop_with_native(
                    slot, runner, generation, "startup_superseded"
                ):
                    slot.runner = runner
                return generation

            slot.runner = runner
            await self._publish_tools(server_id, tools, generation)
            await self._publish_status(server_id, "active", None, generation)
            return generation

    async def stop(self, server_id: str) -> int:
        slot = await self._slot(server_id)
        async with slot.lock:
            generation = slot.generation + 1
            runner = slot.runner
            if runner is not None and not await self._stop_with_native(
                slot, runner, generation, "stop"
            ):
                raise NativeLifecycleBlocked(
                    "Native cleanup blocked; control channel retained"
                )
            slot.generation = generation
            slot.desired_state = DesiredState.STOPPED
            slot.runner = None
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
        progress_callback: ProgressCallback | None = None,
    ) -> dict[str, Any]:
        slot = await self._slot(server_id)
        async with slot.lock:
            runner = slot.runner
            generation = slot.generation
            if runner is None or not runner.is_running():
                raise RuntimeError(f"MCP server '{server_id}' is not active")
            if slot.native_quarantined:
                raise NativeLifecycleBlocked(
                    "Native resource is quarantined pending reconciliation"
                )
            slot.active_calls += 1
        operation = (
            runner.call_tool(tool_name, arguments)
            if progress_callback is None
            else runner.call_tool(
                tool_name,
                arguments,
                progress_callback=progress_callback,
            )
        )
        timeout_budget = min(
            timeout or self._operation_timeout, self._operation_timeout
        )
        # GatewayService applies the same outer deadline. Finish this lifecycle
        # deadline slightly earlier so we can retire a transport whose request
        # timed out instead of leaving a poisoned remote session marked active.
        lifecycle_timeout = max(
            0.001,
            timeout_budget - min(0.05, timeout_budget * 0.1),
        )
        try:
            result = await asyncio.wait_for(operation, lifecycle_timeout)
        except TimeoutError:
            await self._retire_runner(slot, runner, generation)
            raise
        except asyncio.CancelledError:
            if self._native_managed(server_id):
                async with slot.lock:
                    await self._mark_native_unknown(
                        slot, runner, generation, "tool_cancelled"
                    )
            raise
        except Exception:
            if self._native_managed(server_id):
                async with slot.lock:
                    await self._mark_native_unknown(
                        slot, runner, generation, "tool_transport_failed"
                    )
            raise
        finally:
            async with slot.lock:
                slot.active_calls -= 1
        if not self._current(slot, generation):
            raise asyncio.CancelledError("MCP server generation was superseded")
        return result

    async def list_resources(
        self, server_id: str, cursor: str | None = None
    ) -> dict[str, Any]:
        return await self._child_operation(server_id, "list_resources", cursor)

    async def list_resource_templates(
        self, server_id: str, cursor: str | None = None
    ) -> dict[str, Any]:
        return await self._child_operation(
            server_id,
            "list_resource_templates",
            cursor,
        )

    async def read_resource(self, server_id: str, uri: str) -> dict[str, Any]:
        return await self._child_operation(server_id, "read_resource", uri)

    async def subscribe_resource(self, server_id: str, uri: str) -> None:
        await self._child_operation(server_id, "subscribe_resource", uri)

    async def unsubscribe_resource(self, server_id: str, uri: str) -> None:
        await self._child_operation(server_id, "unsubscribe_resource", uri)

    async def _child_operation(
        self,
        server_id: str,
        method: str,
        argument: str | None,
    ) -> Any:
        slot = await self._slot(server_id)
        async with slot.lock:
            runner = slot.runner
            generation = slot.generation
            if runner is None or not runner.is_running():
                raise RuntimeError(f"MCP server '{server_id}' is not active")
            if slot.native_quarantined:
                raise NativeLifecycleBlocked(
                    "Native resource is quarantined pending reconciliation"
                )
        operation = getattr(runner, method)
        result = await asyncio.wait_for(
            operation(argument),
            self._operation_timeout,
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
                generation = slot.generation + 1
                runner = slot.runner
                if runner is not None and not await self._stop_with_native(
                    slot, runner, generation, "shutdown"
                ):
                    return
                slot.generation = generation
                slot.desired_state = DesiredState.STOPPED
                slot.runner = None
                tasks = list(slot.owned_tasks)
                for task in tasks:
                    task.cancel()
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

        try:
            shutdown_budget = self._shutdown_timeout
            if any(self._native_managed(slot.server_id) for slot in slots):
                shutdown_budget = max(shutdown_budget, self._native_timeout)
            await asyncio.wait_for(
                asyncio.gather(*(close_slot(slot) for slot in slots)),
                shutdown_budget,
            )
        except TimeoutError:
            logger.error("mcp_lifecycle_shutdown_timed_out")

    def runner_for(self, server_id: str) -> Runner | None:
        slot = self._slots.get(server_id)
        return slot.runner if slot else None

    def native_status_for(self, server_id: str) -> dict[str, Any] | None:
        slot = self._slots.get(server_id)
        if slot is None or slot.native_receipt is None:
            return None
        return {
            **slot.native_receipt,
            "quarantined": slot.native_quarantined,
            "unknown_operation": slot.native_unknown_operation,
            "transport_retained": slot.runner is not None,
        }

    def _native_managed(self, server_id: str) -> bool:
        return self._native_hooks is not None and self._native_hooks.manages(server_id)

    async def _reconcile_native(self, slot: LifecycleSlot) -> None:
        assert self._native_hooks is not None
        try:
            receipt = await asyncio.wait_for(
                self._native_hooks.reconcile(
                    slot.server_id, slot.runner, slot.generation
                ),
                self._native_timeout,
            )
            slot.native_receipt = dict(receipt)
            if receipt.get("status") not in ("ready", "not_managed"):
                raise NativeLifecycleBlocked("Native reconciliation is incomplete")
            slot.native_quarantined = False
            slot.native_unknown_operation = False
        except BaseException as exc:
            slot.native_quarantined = True
            slot.native_receipt = {
                "status": "cleanup_blocked",
                "blocker": redact_text(exc),
            }
            raise NativeLifecycleBlocked(
                "Native startup reconciliation blocked"
            ) from exc

    async def _mark_native_unknown(
        self, slot: LifecycleSlot, runner: Runner, generation: int, reason: str
    ) -> None:
        assert self._native_hooks is not None
        slot.native_quarantined = True
        slot.native_unknown_operation = True
        try:
            receipt = await asyncio.wait_for(
                self._native_hooks.unresolved(
                    slot.server_id, runner, generation, reason
                ),
                self._native_timeout,
            )
            slot.native_receipt = {
                **receipt,
                "status": "cleanup_blocked",
                "reason": reason,
            }
        except BaseException as exc:
            slot.native_receipt = {
                "status": "cleanup_blocked",
                "reason": reason,
                "blocker": redact_text(exc),
            }

    async def _stop_with_native(
        self, slot: LifecycleSlot, runner: Runner, generation: int, reason: str
    ) -> bool:
        if self._native_managed(slot.server_id):
            assert self._native_hooks is not None
            if slot.active_calls or slot.native_unknown_operation:
                slot.native_quarantined = True
                slot.native_receipt = {
                    "status": "cleanup_blocked",
                    "reason": reason,
                    "blocker": "Active or unknown native operation retains its control channel",
                }
                return False
            try:
                receipt = await asyncio.wait_for(
                    self._native_hooks.cleanup(
                        slot.server_id, runner, generation, reason
                    ),
                    self._native_timeout,
                )
                slot.native_receipt = dict(receipt)
                if receipt.get("status") not in ("completed", "not_managed"):
                    slot.native_quarantined = True
                    return False
                slot.native_quarantined = False
            except BaseException as exc:
                await self._mark_native_unknown(
                    slot, runner, generation, "native_cleanup_interrupted"
                )
                slot.native_receipt = {
                    **(slot.native_receipt or {}),
                    "blocker": redact_text(exc),
                }
                return False
        await self._bounded_stop(runner, slot.server_id, generation)
        return True

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

    async def _retire_runner(
        self, slot: LifecycleSlot, runner: Runner, generation: int
    ) -> None:
        """Remove a timed-out runner so the next call starts a clean transport."""

        async with slot.lock:
            if slot.runner is not runner or slot.generation != generation:
                return
            if self._native_managed(slot.server_id):
                await self._mark_native_unknown(
                    slot, runner, generation, "tool_timeout"
                )
                return
            slot.generation += 1
            slot.runner = None
            await self._bounded_stop(runner, slot.server_id, slot.generation)


async def _noop_tools(
    server_id: str, tools: Sequence[dict[str, Any]], generation: int
) -> None:
    return None


async def _noop_status(
    server_id: str, status: str, error: str | None, generation: int
) -> None:
    return None
