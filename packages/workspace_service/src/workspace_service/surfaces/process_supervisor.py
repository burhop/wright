"""Async process-supervisor port for owned live applications."""

from __future__ import annotations

import asyncio
import secrets
from collections.abc import AsyncIterator, Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any, Protocol

from workspace_service.surfaces.endpoints import RuntimeIdentity
from workspace_service.surfaces.runtime_logs import RuntimeLogBuffer, RuntimeLogTail


class ProcessSupervisorError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class PlatformProcessIdentity:
    adapter: str
    pid: int | None
    creation_time: float | None
    containment_id: str
    containment_mode: str
    executable: str | None = None
    command_digest: str | None = None


@dataclass(frozen=True, slots=True)
class ProcessLaunchRequest:
    workspace_id: str
    instance_id: str
    generation: int
    argv: tuple[str, ...]
    cwd: str
    environment: Mapping[str, str]
    limits: Mapping[str, int | float]
    listener_handle: int | None
    shell: bool = False
    stdin_payload: bytes | None = None


@dataclass(frozen=True, slots=True)
class ProcessStopResult:
    exit_code: int | None
    graceful: bool
    forced: bool
    descendants_remaining: tuple[str, ...]
    listeners_remaining: tuple[str, ...]
    degraded_reason: str | None = None

    @property
    def complete(self) -> bool:
        return not self.descendants_remaining and not self.listeners_remaining


class PlatformProcess(Protocol):
    identity: PlatformProcessIdentity

    def stdout(self) -> AsyncIterator[bytes]: ...

    def stderr(self) -> AsyncIterator[bytes]: ...

    async def wait(self) -> int: ...

    async def stop(self, *, deadline: datetime) -> ProcessStopResult: ...

    def owned_processes(self) -> tuple[tuple[int, float], ...]: ...


class ProcessAdapter(Protocol):
    async def launch(self, request: ProcessLaunchRequest) -> PlatformProcess: ...


@dataclass(frozen=True, slots=True)
class RuntimeSnapshot:
    runtime_id: str
    workspace_id: str
    instance_id: str
    generation: int
    status: str
    identity: PlatformProcessIdentity
    started_at: datetime
    exit_code: int | None = None
    stop_result: ProcessStopResult | None = None


@dataclass(slots=True)
class _Runtime:
    snapshot: RuntimeSnapshot
    process: PlatformProcess
    logs: RuntimeLogBuffer
    tasks: tuple[asyncio.Task[None], ...]
    lock: asyncio.Lock


class ProcessSupervisor:
    """Serialize owned launch/stop operations and retain only safe snapshots."""

    def __init__(
        self,
        *,
        adapter: ProcessAdapter,
        id_factory: Callable[[], str] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._adapter = adapter
        self._id_factory = id_factory or (lambda: secrets.token_urlsafe(24))
        self._clock = clock or (lambda: datetime.now(UTC))
        self._runtimes: dict[str, _Runtime] = {}
        self._idempotency: dict[tuple[str, str], str] = {}
        self._identities: dict[tuple[str, str, int], str] = {}
        self._identity_locks: dict[tuple[str, str, int], asyncio.Lock] = {}
        self._lock = asyncio.Lock()

    async def _identity_lock(self, key: tuple[str, str, int]) -> asyncio.Lock:
        async with self._lock:
            return self._identity_locks.setdefault(key, asyncio.Lock())

    async def start(
        self,
        *,
        workspace_id: str,
        instance_id: str,
        generation: int,
        argv: Sequence[str],
        cwd: str,
        environment: Mapping[str, str],
        secret_environment_names: frozenset[str],
        redaction_query_names: frozenset[str],
        limits: Mapping[str, int | float],
        idempotency_key: str,
        listener_handle: int | None = None,
        stdin_payload: bytes | None = None,
        secret_values: tuple[str, ...] = (),
        stdout_callback: Callable[[bytes], Any] | None = None,
        stderr_callback: Callable[[bytes], Any] | None = None,
    ) -> RuntimeSnapshot:
        if (
            not workspace_id
            or not instance_id
            or generation < 1
            or not idempotency_key
            or not argv
        ):
            raise ProcessSupervisorError(
                "SURFACE_PROCESS_REQUEST_INVALID", "Process launch identity is invalid"
            )
        if not Path(cwd).is_absolute():
            raise ProcessSupervisorError(
                "SURFACE_PROCESS_CWD_INVALID",
                "Process working directory must be absolute",
            )
        if stdin_payload is not None and len(stdin_payload) > 4 * 1024 * 1024:
            raise ProcessSupervisorError(
                "SURFACE_PROCESS_STDIN_TOO_LARGE",
                "Process standard input exceeds the 4 MiB limit",
            )
        identity_key = (workspace_id, instance_id, generation)
        operation_lock = await self._identity_lock(identity_key)
        async with operation_lock:
            async with self._lock:
                prior_id = self._idempotency.get((workspace_id, idempotency_key))
                if prior_id is not None:
                    return self._runtimes[prior_id].snapshot
                prior_id = self._identities.get(identity_key)
                if prior_id is not None:
                    self._idempotency[(workspace_id, idempotency_key)] = prior_id
                    return self._runtimes[prior_id].snapshot

            request = ProcessLaunchRequest(
                workspace_id=workspace_id,
                instance_id=instance_id,
                generation=generation,
                argv=tuple(argv),
                cwd=cwd,
                environment=MappingProxyType(dict(environment)),
                limits=MappingProxyType(dict(limits)),
                listener_handle=listener_handle,
                stdin_payload=stdin_payload,
            )
            process = await self._adapter.launch(request)
            runtime_id = self._id_factory()
            if not runtime_id:
                raise ProcessSupervisorError(
                    "SURFACE_PROCESS_ID_INVALID",
                    "Process runtime ID factory returned empty",
                )
            redacted_values = tuple(
                environment[name]
                for name in secret_environment_names
                if name in environment and environment[name]
            ) + tuple(value for value in secret_values if value)
            logs = RuntimeLogBuffer(
                maximum_bytes=int(limits.get("captured_log_bytes", 10 * 1024 * 1024)),
                bytes_per_second=int(
                    limits.get("captured_log_bytes_per_second", 256 * 1024)
                ),
                burst_bytes=int(limits.get("captured_log_burst_bytes", 1024 * 1024)),
                secret_values=redacted_values,
                environment_names=secret_environment_names,
                query_names=redaction_query_names,
            )
            snapshot = RuntimeSnapshot(
                runtime_id=runtime_id,
                workspace_id=workspace_id,
                instance_id=instance_id,
                generation=generation,
                status="running",
                identity=process.identity,
                started_at=self._clock(),
            )
            runtime = _Runtime(
                snapshot=snapshot,
                process=process,
                logs=logs,
                tasks=(),
                lock=asyncio.Lock(),
            )
            async with self._lock:
                if runtime_id in self._runtimes:
                    raise ProcessSupervisorError(
                        "SURFACE_PROCESS_ID_COLLISION", "Process runtime ID collided"
                    )
                self._runtimes[runtime_id] = runtime
                self._identities[identity_key] = runtime_id
                self._idempotency[(workspace_id, idempotency_key)] = runtime_id
            runtime.tasks = (
                asyncio.create_task(
                    self._pump(runtime_id, "stdout", process.stdout(), stdout_callback),
                    name=f"surface-{runtime_id}-stdout",
                ),
                asyncio.create_task(
                    self._pump(runtime_id, "stderr", process.stderr(), stderr_callback),
                    name=f"surface-{runtime_id}-stderr",
                ),
                asyncio.create_task(
                    self._watch(runtime_id), name=f"surface-{runtime_id}-wait"
                ),
            )
            return snapshot

    async def _pump(
        self,
        runtime_id: str,
        stream: str,
        source: AsyncIterator[bytes],
        callback: Callable[[bytes], Any] | None,
    ) -> None:
        try:
            async for payload in source:
                runtime = self._runtimes.get(runtime_id)
                if runtime is None:
                    return
                runtime.logs.write(stream, payload)
                if callback is not None:
                    result = callback(payload)
                    if hasattr(result, "__await__"):
                        await result
        except asyncio.CancelledError:
            raise
        except Exception:
            runtime = self._runtimes.get(runtime_id)
            if runtime is not None:
                runtime.logs.write(
                    "system", f"{stream} capture failed.\n".encode("utf-8")
                )

    async def _watch(self, runtime_id: str) -> None:
        runtime = self._runtimes.get(runtime_id)
        if runtime is None:
            return
        try:
            exit_code = await runtime.process.wait()
        except asyncio.CancelledError:
            raise
        except Exception:
            exit_code = None
        async with runtime.lock:
            if runtime.snapshot.status not in {"stopped", "failed-stop"}:
                runtime.snapshot = replace(
                    runtime.snapshot, status="exited", exit_code=exit_code
                )

    def _get(self, runtime_id: str) -> _Runtime:
        runtime = self._runtimes.get(runtime_id)
        if runtime is None:
            raise ProcessSupervisorError(
                "SURFACE_PROCESS_NOT_FOUND", "Managed process runtime was not found"
            )
        return runtime

    def snapshot(self, runtime_id: str) -> RuntimeSnapshot:
        return self._get(runtime_id).snapshot

    def runtime_identity(self, runtime_id: str) -> RuntimeIdentity:
        runtime = self._get(runtime_id)
        snapshot = runtime.snapshot
        if snapshot.identity.pid is None or snapshot.identity.creation_time is None:
            raise ProcessSupervisorError(
                "SURFACE_PROCESS_IDENTITY_UNAVAILABLE",
                "Runtime adapter does not expose a host process identity",
            )
        owned = runtime.process.owned_processes()
        root = (snapshot.identity.pid, snapshot.identity.creation_time)
        return RuntimeIdentity(
            instance_id=snapshot.instance_id,
            generation=snapshot.generation,
            pid=root[0],
            creation_time=root[1],
            descendants=tuple(item for item in owned if item != root),
        )

    def logs(
        self, runtime_id: str, *, after_sequence: int = 0, limit: int = 200
    ) -> RuntimeLogTail:
        return self._get(runtime_id).logs.tail(
            after_sequence=after_sequence, limit=limit
        )

    def diagnostics(self, runtime_id: str) -> dict[str, Any]:
        runtime = self._get(runtime_id)
        snapshot = runtime.snapshot
        return {
            "runtime_id": snapshot.runtime_id,
            "workspace_id": snapshot.workspace_id,
            "instance_id": snapshot.instance_id,
            "generation": snapshot.generation,
            "status": snapshot.status,
            "adapter": snapshot.identity.adapter,
            "containment_mode": snapshot.identity.containment_mode,
            "logs": runtime.logs.diagnostic_projection(),
        }

    async def stop(
        self, *, runtime_id: str, generation: int, deadline: datetime
    ) -> RuntimeSnapshot:
        runtime = self._get(runtime_id)
        if runtime.snapshot.generation != generation:
            raise ProcessSupervisorError(
                "SURFACE_PROCESS_GENERATION_MISMATCH",
                "Process generation does not match stop authority",
            )
        async with runtime.lock:
            if runtime.snapshot.status in {"stopped", "failed-stop"}:
                return runtime.snapshot
            runtime.snapshot = replace(runtime.snapshot, status="stopping")
            result = await runtime.process.stop(deadline=deadline)
            runtime.snapshot = replace(
                runtime.snapshot,
                status="stopped" if result.complete else "failed-stop",
                exit_code=result.exit_code,
                stop_result=result,
            )
            return runtime.snapshot

    async def shutdown(self, *, deadline: datetime) -> tuple[RuntimeSnapshot, ...]:
        targets = [
            runtime.snapshot
            for runtime in self._runtimes.values()
            if runtime.snapshot.status not in {"stopped", "failed-stop"}
        ]
        if not targets:
            return ()
        return tuple(
            await asyncio.gather(
                *(
                    self.stop(
                        runtime_id=item.runtime_id,
                        generation=item.generation,
                        deadline=deadline,
                    )
                    for item in targets
                )
            )
        )


__all__ = [
    "PlatformProcess",
    "PlatformProcessIdentity",
    "ProcessAdapter",
    "ProcessLaunchRequest",
    "ProcessStopResult",
    "ProcessSupervisor",
    "ProcessSupervisorError",
    "RuntimeSnapshot",
]
