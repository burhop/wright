"""Workspace-scoped orchestration for managed application lifecycle controls."""

from __future__ import annotations

import asyncio
import secrets
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from core.surfaces.models import (
    LiveAppSurfaceSource,
    SurfaceDescriptor,
    SurfaceId,
    SurfaceLifecycle,
)

from .live_app_manager import (
    LiveAppInstance,
    LiveAppManagerError,
    LiveAppStartRequest,
)
from .service import SurfaceActor, SurfaceRevisionConflictError, SurfaceService


class LiveAppControlError(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        correlation_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.correlation_id = correlation_id


class LiveAppControlManager(Protocol):
    async def start(self, request: LiveAppStartRequest) -> LiveAppInstance: ...

    async def retry(
        self, instance_id: str, *, idempotency_key: str
    ) -> LiveAppInstance: ...

    async def restart(
        self, instance_id: str, *, idempotency_key: str
    ) -> LiveAppInstance: ...

    async def stop(
        self, instance_id: str, *, idempotency_key: str
    ) -> LiveAppInstance: ...

    async def compensate_uncommitted(
        self,
        instance_id: str,
        *,
        generation: int,
        correlation_id: str,
    ) -> LiveAppInstance: ...

    async def check_health(self, instance_id: str) -> LiveAppInstance: ...

    def get(self, instance_id: str) -> LiveAppInstance: ...

    def presentation_projection(
        self, instance_id: str
    ) -> tuple[dict[str, Any], ...]: ...

    def logs(self, instance_id: str, *, after_sequence: int, limit: int) -> Any: ...


class LiveAppControlService:
    def __init__(
        self,
        *,
        surfaces: SurfaceService,
        manager_for_workspace: Callable[[str], LiveAppControlManager],
    ) -> None:
        self._surfaces = surfaces
        self._manager_for_workspace = manager_for_workspace
        self._locks: dict[tuple[str, str], asyncio.Lock] = {}
        self._registry_lock = asyncio.Lock()

    async def _lock(self, actor: SurfaceActor, surface_id: SurfaceId) -> asyncio.Lock:
        key = (actor.workspace_id, str(surface_id))
        async with self._registry_lock:
            return self._locks.setdefault(key, asyncio.Lock())

    async def _surface(
        self, actor: SurfaceActor, surface_id: SurfaceId
    ) -> tuple[SurfaceDescriptor, LiveAppSurfaceSource, LiveAppControlManager]:
        descriptor = await self._surfaces.get(actor=actor, surface_id=surface_id)
        if not isinstance(descriptor.source, LiveAppSurfaceSource):
            raise LiveAppControlError(
                "SURFACE_RUNTIME_NOT_MANAGED_APP",
                "Surface is not backed by a managed application",
            )
        try:
            manager = self._manager_for_workspace(actor.workspace_id)
        except LiveAppManagerError as error:
            raise LiveAppControlError(
                error.code, str(error), retryable=error.retryable
            ) from error
        return descriptor, descriptor.source, manager

    @staticmethod
    def _instance_id(descriptor: SurfaceDescriptor) -> str:
        value = descriptor.instance or {}
        instance_id = value.get("instanceId")
        if not isinstance(instance_id, str) or not instance_id:
            raise LiveAppControlError(
                "SURFACE_RUNTIME_INSTANCE_UNAVAILABLE",
                "Surface has no managed application instance",
            )
        return instance_id

    @staticmethod
    def _replacement_generation(descriptor: SurfaceDescriptor) -> int:
        value = (descriptor.instance or {}).get("generation")
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise LiveAppControlError(
                "SURFACE_RUNTIME_GENERATION_UNAVAILABLE",
                "Surface has no valid managed application generation",
            )
        return value + 1

    @staticmethod
    def _instance_projection(instance: LiveAppInstance) -> dict[str, object]:
        def timestamp(value):
            return value.isoformat().replace("+00:00", "Z") if value else None

        return {
            "instanceId": instance.instance_id,
            "generation": instance.generation,
            "sharing": instance.sharing,
            "ownership": instance.ownership,
            "platform": instance.platform,
            "lifetimePolicy": instance.lifetime_policy,
            "leaseExpiresAt": timestamp(instance.lease_expires_at),
            "idleSeconds": instance.idle_seconds,
            "lastActivityAt": timestamp(instance.last_activity_at),
        }

    @staticmethod
    def _diagnostic(instance: LiveAppInstance) -> dict[str, object] | None:
        if instance.failure is None:
            return None
        return {
            "code": instance.failure.code,
            "message": instance.failure.message,
            "retryable": instance.failure.retryable,
        }

    async def _project(
        self,
        *,
        actor: SurfaceActor,
        descriptor: SurfaceDescriptor,
        target: SurfaceLifecycle,
        manager: LiveAppControlManager,
        instance: LiveAppInstance | None = None,
    ) -> SurfaceDescriptor:
        return await self._surfaces.project_runtime(
            actor=actor,
            surface_id=descriptor.surface_id,
            target=target,
            expected_revision=descriptor.revision,
            instance=(
                self._instance_projection(instance)
                if instance is not None
                else descriptor.instance
            ),
            presentations=(
                manager.presentation_projection(instance.instance_id)
                if instance is not None
                else descriptor.presentations
            ),
            diagnostic_summary=(
                self._diagnostic(instance)
                if instance is not None
                else descriptor.diagnostic_summary
            ),
        )

    @staticmethod
    async def _finish_despite_cancellation(
        operation: Awaitable[LiveAppInstance],
    ) -> LiveAppInstance:
        """Let the server reach one durable lifecycle outcome before cancelling."""

        task = asyncio.create_task(operation)
        cancellation: asyncio.CancelledError | None = None
        while not task.done():
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError as error:
                cancellation = error
            except BaseException:
                break
        if cancellation is not None:
            try:
                task.result()
            except BaseException:
                pass
            raise cancellation
        return task.result()

    @staticmethod
    def _descriptor_matches(
        descriptor: SurfaceDescriptor,
        instance: LiveAppInstance,
        target: SurfaceLifecycle,
    ) -> bool:
        projected = descriptor.instance or {}
        return (
            descriptor.lifecycle is target
            and projected.get("instanceId") == instance.instance_id
            and projected.get("generation") == instance.generation
        )

    async def _reconcile_projection(
        self,
        *,
        actor: SurfaceActor,
        surface_id: SurfaceId,
        manager: LiveAppControlManager,
        instance: LiveAppInstance,
        target: SurfaceLifecycle,
    ) -> bool:
        allowed_from = {
            SurfaceLifecycle.FAILED: {
                SurfaceLifecycle.STARTING,
                SurfaceLifecycle.READY,
                SurfaceLifecycle.UNHEALTHY,
                SurfaceLifecycle.STOPPING,
            },
            SurfaceLifecycle.STOPPED: {SurfaceLifecycle.STOPPING},
        }[target]
        for _ in range(3):
            latest = await self._surfaces.get(actor=actor, surface_id=surface_id)
            if self._descriptor_matches(latest, instance, target):
                return True
            if latest.lifecycle in {SurfaceLifecycle.FAILED, SurfaceLifecycle.STOPPED}:
                return True
            if latest.lifecycle not in allowed_from:
                return False
            try:
                await self._project(
                    actor=actor,
                    descriptor=latest,
                    target=target,
                    manager=manager,
                    instance=instance,
                )
                return True
            except SurfaceRevisionConflictError:
                continue
        return False

    async def _commit_manager_result(
        self,
        *,
        actor: SurfaceActor,
        descriptor: SurfaceDescriptor,
        manager: LiveAppControlManager,
        instance: LiveAppInstance,
        transitions: tuple[SurfaceLifecycle, ...],
    ) -> LiveAppInstance:
        current = descriptor
        try:
            for target in transitions:
                current = await self._project(
                    actor=actor,
                    descriptor=current,
                    target=target,
                    manager=manager,
                    instance=instance,
                )
            return instance
        except BaseException as projection_error:
            final_target = transitions[-1]
            try:
                latest = await self._surfaces.get(
                    actor=actor, surface_id=descriptor.surface_id
                )
            except BaseException:
                latest = None
            if latest is not None and self._descriptor_matches(
                latest, instance, final_target
            ):
                return instance

            correlation_id = secrets.token_hex(8)
            reconciled = instance
            target = final_target
            if instance.state in {"ready", "unhealthy"}:
                try:
                    reconciled = await manager.compensate_uncommitted(
                        instance.instance_id,
                        generation=instance.generation,
                        correlation_id=correlation_id,
                    )
                except BaseException as compensation_error:
                    if isinstance(compensation_error, asyncio.CancelledError):
                        raise
                    raise LiveAppControlError(
                        "SURFACE_DESCRIPTOR_COMPENSATION_FAILED",
                        (
                            "Managed runtime authority could not be reconciled after "
                            f"a surface commit failure. Reference {correlation_id}."
                        ),
                        retryable=False,
                        correlation_id=correlation_id,
                    ) from compensation_error
                target = SurfaceLifecycle.FAILED

            try:
                projected = await self._reconcile_projection(
                    actor=actor,
                    surface_id=descriptor.surface_id,
                    manager=manager,
                    instance=reconciled,
                    target=target,
                )
            except BaseException as reconciliation_error:
                if isinstance(reconciliation_error, asyncio.CancelledError):
                    raise
                projected = False
            if not projected:
                raise LiveAppControlError(
                    "SURFACE_DESCRIPTOR_RECONCILIATION_FAILED",
                    (
                        "Managed runtime was contained, but its surface descriptor could "
                        f"not be reconciled. Reference {correlation_id}."
                    ),
                    retryable=False,
                    correlation_id=correlation_id,
                ) from projection_error
            if isinstance(projection_error, asyncio.CancelledError):
                raise projection_error
            raise LiveAppControlError(
                "SURFACE_DESCRIPTOR_COMMIT_FAILED",
                (
                    "Managed runtime was safely contained after its surface state could "
                    f"not be committed. Reference {correlation_id}."
                ),
                retryable=True,
                correlation_id=correlation_id,
            ) from projection_error

    async def _start_from_starting(
        self,
        *,
        actor: SurfaceActor,
        surface_id: SurfaceId,
        source: LiveAppSurfaceSource,
        descriptor: SurfaceDescriptor,
        manager: LiveAppControlManager,
        idempotency_key: str,
        initial_generation: int = 1,
    ) -> LiveAppInstance:
        try:
            instance = await manager.start(
                LiveAppStartRequest(
                    workspace_id=actor.workspace_id,
                    surface_id=str(surface_id),
                    manifest_id=source.manifest_id,
                    user_id=actor.user_id,
                    session_id=actor.session_id,
                    idempotency_key=idempotency_key,
                    initial_generation=initial_generation,
                )
            )
        except LiveAppManagerError as error:
            if error.instance is not None:
                await self._project(
                    actor=actor,
                    descriptor=descriptor,
                    target=SurfaceLifecycle.FAILED,
                    manager=manager,
                    instance=error.instance,
                )
            raise LiveAppControlError(
                error.code, str(error), retryable=error.retryable
            ) from error
        return await self._commit_manager_result(
            actor=actor,
            descriptor=descriptor,
            manager=manager,
            instance=instance,
            transitions=(SurfaceLifecycle.READY,),
        )

    async def start(
        self,
        *,
        actor: SurfaceActor,
        surface_id: SurfaceId,
        idempotency_key: str,
    ) -> LiveAppInstance:
        lock = await self._lock(actor, surface_id)
        async with lock:
            descriptor, source, manager = await self._surface(actor, surface_id)
            if descriptor.lifecycle is not SurfaceLifecycle.DECLARED:
                raise LiveAppControlError(
                    "SURFACE_LIFECYCLE_CONFLICT",
                    f"Start is not available from {descriptor.lifecycle.value}",
                )
            descriptor = await self._project(
                actor=actor,
                descriptor=descriptor,
                target=SurfaceLifecycle.STARTING,
                manager=manager,
            )
            return await self._finish_despite_cancellation(
                self._start_from_starting(
                    actor=actor,
                    surface_id=surface_id,
                    source=source,
                    descriptor=descriptor,
                    manager=manager,
                    idempotency_key=idempotency_key,
                )
            )

    async def _existing_operation(
        self,
        *,
        actor: SurfaceActor,
        surface_id: SurfaceId,
        idempotency_key: str,
        operation: str,
    ) -> LiveAppInstance:
        lock = await self._lock(actor, surface_id)
        async with lock:
            descriptor, source, manager = await self._surface(actor, surface_id)
            instance_id = self._instance_id(descriptor)
            if operation == "stop":
                allowed = {SurfaceLifecycle.READY, SurfaceLifecycle.UNHEALTHY}
                if descriptor.lifecycle not in allowed:
                    raise LiveAppControlError(
                        "SURFACE_LIFECYCLE_CONFLICT",
                        f"Stop is not available from {descriptor.lifecycle.value}",
                    )
                descriptor = await self._project(
                    actor=actor,
                    descriptor=descriptor,
                    target=SurfaceLifecycle.STOPPING,
                    manager=manager,
                )
                invoke = manager.stop
            elif operation == "retry":
                if descriptor.lifecycle not in {
                    SurfaceLifecycle.FAILED,
                    SurfaceLifecycle.STOPPED,
                }:
                    raise LiveAppControlError(
                        "SURFACE_LIFECYCLE_CONFLICT",
                        f"Retry is not available from {descriptor.lifecycle.value}",
                    )
                descriptor = await self._project(
                    actor=actor,
                    descriptor=descriptor,
                    target=SurfaceLifecycle.STARTING,
                    manager=manager,
                )
                invoke = manager.retry
            elif operation == "restart":
                if descriptor.lifecycle not in {
                    SurfaceLifecycle.READY,
                    SurfaceLifecycle.UNHEALTHY,
                    SurfaceLifecycle.FAILED,
                    SurfaceLifecycle.STOPPED,
                }:
                    raise LiveAppControlError(
                        "SURFACE_LIFECYCLE_CONFLICT",
                        f"Restart is not available from {descriptor.lifecycle.value}",
                    )
                restart_from_active = descriptor.lifecycle in {
                    SurfaceLifecycle.READY,
                    SurfaceLifecycle.UNHEALTHY,
                }
                if restart_from_active:
                    descriptor = await self._project(
                        actor=actor,
                        descriptor=descriptor,
                        target=SurfaceLifecycle.STOPPING,
                        manager=manager,
                    )
                else:
                    descriptor = await self._project(
                        actor=actor,
                        descriptor=descriptor,
                        target=SurfaceLifecycle.STARTING,
                        manager=manager,
                    )
                invoke = manager.restart
            else:
                raise AssertionError("unknown live-app operation")

            async def complete_operation() -> LiveAppInstance:
                current = descriptor
                try:
                    instance = await invoke(
                        instance_id, idempotency_key=idempotency_key
                    )
                except LiveAppManagerError as error:
                    if error.code == "SURFACE_INSTANCE_NOT_FOUND" and operation in {
                        "retry",
                        "restart",
                    }:
                        if current.lifecycle is SurfaceLifecycle.STOPPING:
                            current = await self._project(
                                actor=actor,
                                descriptor=current,
                                target=SurfaceLifecycle.STOPPED,
                                manager=manager,
                            )
                            current = await self._project(
                                actor=actor,
                                descriptor=current,
                                target=SurfaceLifecycle.STARTING,
                                manager=manager,
                            )
                        return await self._start_from_starting(
                            actor=actor,
                            surface_id=surface_id,
                            source=source,
                            descriptor=current,
                            manager=manager,
                            idempotency_key=idempotency_key,
                            initial_generation=self._replacement_generation(current),
                        )
                    if error.instance is not None:
                        await self._project(
                            actor=actor,
                            descriptor=current,
                            target=SurfaceLifecycle.FAILED,
                            manager=manager,
                            instance=error.instance,
                        )
                    raise LiveAppControlError(
                        error.code, str(error), retryable=error.retryable
                    ) from error

                target = (
                    SurfaceLifecycle.STOPPED
                    if operation == "stop" and instance.state == "stopped"
                    else SurfaceLifecycle.FAILED
                    if instance.state == "failed"
                    else SurfaceLifecycle.READY
                )
                transitions = (
                    (
                        SurfaceLifecycle.STOPPED,
                        SurfaceLifecycle.STARTING,
                        target,
                    )
                    if operation == "restart" and restart_from_active
                    else (target,)
                )
                return await self._commit_manager_result(
                    actor=actor,
                    descriptor=current,
                    manager=manager,
                    instance=instance,
                    transitions=transitions,
                )

            return await self._finish_despite_cancellation(complete_operation())

    async def retry(self, **kwargs: Any) -> LiveAppInstance:
        return await self._existing_operation(operation="retry", **kwargs)

    async def restart(self, **kwargs: Any) -> LiveAppInstance:
        return await self._existing_operation(operation="restart", **kwargs)

    async def stop(self, **kwargs: Any) -> LiveAppInstance:
        return await self._existing_operation(operation="stop", **kwargs)

    async def inspect(
        self, *, actor: SurfaceActor, surface_id: SurfaceId
    ) -> LiveAppInstance:
        descriptor, _source, manager = await self._surface(actor, surface_id)
        try:
            instance = manager.get(self._instance_id(descriptor))
        except LiveAppManagerError as error:
            raise LiveAppControlError(
                error.code, str(error), retryable=error.retryable
            ) from error
        if instance.workspace_id != actor.workspace_id or instance.surface_id != str(
            surface_id
        ):
            raise LiveAppControlError(
                "SURFACE_RUNTIME_NOT_FOUND", "Managed application was not found"
            )
        return instance

    async def health(
        self, *, actor: SurfaceActor, surface_id: SurfaceId
    ) -> LiveAppInstance:
        descriptor, _source, manager = await self._surface(actor, surface_id)
        try:
            return await manager.check_health(self._instance_id(descriptor))
        except LiveAppManagerError as error:
            raise LiveAppControlError(
                error.code, str(error), retryable=error.retryable
            ) from error

    async def logs(
        self,
        *,
        actor: SurfaceActor,
        surface_id: SurfaceId,
        after_sequence: int,
        limit: int,
    ) -> Any:
        descriptor, _source, manager = await self._surface(actor, surface_id)
        try:
            return manager.logs(
                self._instance_id(descriptor),
                after_sequence=after_sequence,
                limit=limit,
            )
        except LiveAppManagerError as error:
            raise LiveAppControlError(error.code, str(error)) from error


__all__ = [
    "LiveAppControlError",
    "LiveAppControlManager",
    "LiveAppControlService",
]
