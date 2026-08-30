"""Private, bounded subprocess runtime for reviewed engineering-model adapters."""

from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import inspect
import json
import math
import os
import re
import shutil
import stat
import subprocess
import sys
import time
import uuid
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .models import canonical_digest
from .observability import ModelBoundaryObserver

MAX_CONTROL_BYTES = 1024 * 1024
_IDENTITY = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}$")
_SAFE_PROGRESS = re.compile(
    r"(?i)(?:api[_-]?key|secret|token|password|authorization|credential|cookie)\s*[:=]"
)


class RuntimeFailure(RuntimeError):
    """Stable non-secret runtime failure."""

    def __init__(self, category: str, message: str) -> None:
        super().__init__(message)
        self.category = category


@dataclass(frozen=True, slots=True)
class AdapterRegistration:
    adapter_id: str
    adapter_version: str
    contract_version: str
    command: tuple[str, ...]
    formats: frozenset[str]
    tasks: frozenset[str]
    platforms: frozenset[str]
    architectures: frozenset[str]
    execution_providers: frozenset[str]
    maximum_control_bytes: int = MAX_CONTROL_BYTES

    def __post_init__(self) -> None:
        for value in (self.adapter_id, self.adapter_version, self.contract_version):
            if not _IDENTITY.fullmatch(value):
                raise RuntimeFailure("runtime_unhealthy", "Adapter identity is invalid")
        if not self.command or any(
            not isinstance(item, str) or not item or len(item) > 4096
            for item in self.command
        ):
            raise RuntimeFailure("runtime_unhealthy", "Adapter command is invalid")
        for values in (
            self.formats,
            self.tasks,
            self.platforms,
            self.architectures,
            self.execution_providers,
        ):
            if (
                not values
                or len(values) > 64
                or any(not item or len(item) > 128 for item in values)
            ):
                raise RuntimeFailure(
                    "runtime_unhealthy", "Adapter capability declaration is invalid"
                )
        if not 1024 <= self.maximum_control_bytes <= MAX_CONTROL_BYTES:
            raise RuntimeFailure(
                "runtime_unhealthy", "Adapter message limit is invalid"
            )


@dataclass(frozen=True, slots=True)
class AdapterDescriptor:
    adapter_id: str
    adapter_version: str
    contract_version: str
    formats: frozenset[str]
    tasks: frozenset[str]
    platforms: frozenset[str]
    architectures: frozenset[str]
    execution_providers: frozenset[str]
    maximum_message_bytes: int
    maximum_concurrency: int
    cancellation_supported: bool
    unload_supported: bool
    health: str
    diagnostics: Mapping[str, Any]

    @classmethod
    def parse(cls, value: Mapping[str, Any]) -> "AdapterDescriptor":
        try:
            result = cls(
                adapter_id=str(value["adapter_id"]),
                adapter_version=str(value["adapter_version"]),
                contract_version=str(value["contract_version"]),
                formats=frozenset(str(item) for item in value["formats"]),
                tasks=frozenset(str(item) for item in value["tasks"]),
                platforms=frozenset(str(item) for item in value["platforms"]),
                architectures=frozenset(str(item) for item in value["architectures"]),
                execution_providers=frozenset(
                    str(item) for item in value["execution_providers"]
                ),
                maximum_message_bytes=int(value["maximum_message_bytes"]),
                maximum_concurrency=int(value["maximum_concurrency"]),
                cancellation_supported=bool(value["cancellation_supported"]),
                unload_supported=bool(value["unload_supported"]),
                health=str(value["health"]),
                diagnostics=dict(value.get("diagnostics") or {}),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise RuntimeFailure(
                "runtime_unhealthy", "Adapter health response is invalid"
            ) from error
        if (
            result.maximum_message_bytes < 1024
            or result.maximum_message_bytes > MAX_CONTROL_BYTES
            or not 1 <= result.maximum_concurrency <= 64
            or result.health not in {"healthy", "degraded", "unhealthy"}
        ):
            raise RuntimeFailure(
                "runtime_unhealthy", "Adapter health response is invalid"
            )
        return result


@dataclass(frozen=True, slots=True)
class RuntimeProgress:
    request_id: str
    sequence: int
    phase: str
    completed_items: int | None
    total_items: int | None
    message: str


ProgressHandler = Callable[[RuntimeProgress], Any]


class RuntimeAdapterRegistry:
    def __init__(self, registrations: Iterable[AdapterRegistration] = ()) -> None:
        self._registrations: dict[str, AdapterRegistration] = {}
        for registration in registrations:
            self.register(registration)

    def register(self, registration: AdapterRegistration) -> None:
        if registration.adapter_id in self._registrations:
            raise RuntimeFailure(
                "runtime_unhealthy", "Adapter identity is already registered"
            )
        self._registrations[registration.adapter_id] = registration

    def get(self, adapter_id: str) -> AdapterRegistration:
        try:
            return self._registrations[adapter_id]
        except KeyError as error:
            raise RuntimeFailure(
                "runtime_missing", "Runtime adapter is unavailable"
            ) from error

    def versions(self) -> dict[str, str]:
        return {
            adapter_id: registration.adapter_version
            for adapter_id, registration in self._registrations.items()
        }


def _artifact_key(value: str) -> PurePosixPath:
    if "\\" in value or "//" in value:
        raise RuntimeFailure("artifact_invalid", "Artifact key is unsafe")
    parsed = PurePosixPath(value)
    if (
        not value
        or parsed.is_absolute()
        or any(part in {"", ".", ".."} for part in parsed.parts)
    ):
        raise RuntimeFailure("artifact_invalid", "Artifact key is unsafe")
    return parsed


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _remove_tree(path: Path) -> None:
    """Remove one supervisor-owned scratch tree, including read-only artifacts."""

    if not path.exists():
        return
    for item in sorted(
        path.rglob("*"), key=lambda value: len(value.parts), reverse=True
    ):
        try:
            item.chmod(
                stat.S_IWRITE | stat.S_IREAD | (stat.S_IEXEC if item.is_dir() else 0)
            )
        except OSError:
            pass
    try:
        path.chmod(stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
    except OSError:
        pass
    shutil.rmtree(path)


def _finite(value: Any) -> bool:
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, Mapping):
        return all(_finite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite(item) for item in value)
    return True


class RuntimeSession:
    def __init__(
        self,
        *,
        registration: AdapterRegistration,
        process: asyncio.subprocess.Process,
        scratch: Path,
        artifacts: Mapping[str, str],
        artifact_set_digest: str,
        model_format: str,
        task_id: str,
        descriptor: AdapterDescriptor,
        observer: ModelBoundaryObserver,
        trace_id: str,
        on_close: Callable[["RuntimeSession"], None],
    ) -> None:
        self.registration = registration
        self.process = process
        self.scratch = scratch
        self.artifacts = dict(artifacts)
        self.artifact_set_digest = artifact_set_digest
        self.model_format = model_format
        self.task_id = task_id
        self.descriptor = descriptor
        self.observer = observer
        self.trace_id = trace_id
        self._on_close = on_close
        self._exchange_lock = asyncio.Lock()
        self._write_lock = asyncio.Lock()
        self._current_request_id: str | None = None
        self._cancelled_request_ids: set[str] = set()
        self._closed = False
        self._stderr_task = asyncio.create_task(self._drain_stderr())

    async def _drain_stderr(self) -> None:
        if self.process.stderr is None:
            return
        while True:
            block = await self.process.stderr.read(4096)
            if not block:
                return

    async def _write(self, value: Mapping[str, Any]) -> None:
        if self.process.stdin is None or self.process.returncode is not None:
            raise RuntimeFailure("runtime_unhealthy", "Runtime adapter is unavailable")
        try:
            encoded = json.dumps(
                dict(value),
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        except (TypeError, ValueError) as error:
            raise RuntimeFailure(
                "input_invalid", "Runtime request is invalid"
            ) from error
        if len(encoded) > min(
            self.registration.maximum_control_bytes,
            self.descriptor.maximum_message_bytes,
        ):
            raise RuntimeFailure(
                "input_invalid", "Runtime request exceeds its byte limit"
            )
        async with self._write_lock:
            try:
                self.process.stdin.write(encoded + b"\n")
                await self.process.stdin.drain()
            except (BrokenPipeError, ConnectionError) as error:
                raise RuntimeFailure(
                    "runtime_unhealthy", "Runtime adapter is unavailable"
                ) from error

    @staticmethod
    def _progress(value: Mapping[str, Any], *, request_id: str) -> RuntimeProgress:
        try:
            message = str(value.get("message") or "")
            progress = RuntimeProgress(
                request_id=request_id,
                sequence=int(value["sequence"]),
                phase=str(value["phase"]),
                completed_items=(
                    int(value["completed_items"])
                    if value.get("completed_items") is not None
                    else None
                ),
                total_items=(
                    int(value["total_items"])
                    if value.get("total_items") is not None
                    else None
                ),
                message=message,
            )
        except (KeyError, TypeError, ValueError) as error:
            raise RuntimeFailure(
                "output_invalid", "Runtime progress is invalid"
            ) from error
        if (
            progress.sequence < 1
            or not progress.phase
            or len(progress.phase) > 64
            or len(progress.message) > 512
            or _SAFE_PROGRESS.search(progress.message)
            or (progress.completed_items is not None and progress.completed_items < 0)
            or (progress.total_items is not None and progress.total_items < 0)
            or (
                progress.completed_items is not None
                and progress.total_items is not None
                and progress.completed_items > progress.total_items
            )
        ):
            raise RuntimeFailure("output_invalid", "Runtime progress is invalid")
        return progress

    async def _exchange(
        self,
        operation: str,
        payload: Mapping[str, Any],
        *,
        timeout: float,
        progress_callback: ProgressHandler | None = None,
        fault_profile: str | None = None,
    ) -> Mapping[str, Any]:
        if self._closed:
            raise RuntimeFailure("runtime_unhealthy", "Runtime session is closed")
        request_id = "runtime-" + uuid.uuid4().hex
        request = {"operation": operation, "request_id": request_id, **dict(payload)}
        if fault_profile:
            request["fault_profile"] = fault_profile
        async with self._exchange_lock:
            self._current_request_id = request_id
            last_sequence = 0
            deadline = time.monotonic() + timeout
            await self._write(request)
            try:
                while True:
                    if self.process.stdout is None:
                        raise RuntimeFailure(
                            "runtime_unhealthy", "Runtime adapter is unavailable"
                        )
                    try:
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            raise TimeoutError
                        raw = await asyncio.wait_for(
                            self.process.stdout.readline(), timeout=remaining
                        )
                    except TimeoutError as error:
                        await self._terminate()
                        raise RuntimeFailure(
                            "runtime_timeout", "Runtime operation timed out"
                        ) from error
                    except (ValueError, asyncio.LimitOverrunError) as error:
                        await self._terminate()
                        raise RuntimeFailure(
                            "output_invalid", "Runtime response exceeds its byte limit"
                        ) from error
                    if not raw:
                        raise RuntimeFailure(
                            "runtime_unhealthy", "Runtime adapter exited unexpectedly"
                        )
                    if len(raw) > self.registration.maximum_control_bytes:
                        await self._terminate()
                        raise RuntimeFailure(
                            "output_invalid", "Runtime response exceeds its byte limit"
                        )
                    try:
                        message = json.loads(raw)
                    except (UnicodeDecodeError, json.JSONDecodeError) as error:
                        raise RuntimeFailure(
                            "output_invalid", "Runtime response is invalid"
                        ) from error
                    if not isinstance(message, Mapping):
                        raise RuntimeFailure(
                            "output_invalid", "Runtime response is invalid"
                        )
                    if message.get("request_id") != request_id:
                        # A cancelled request may produce a late terminal result. It is
                        # never published into the current request.
                        continue
                    if message.get("type") == "progress":
                        progress = self._progress(message, request_id=request_id)
                        if progress.sequence <= last_sequence:
                            raise RuntimeFailure(
                                "output_invalid", "Runtime progress is not monotonic"
                            )
                        last_sequence = progress.sequence
                        if progress_callback is not None:
                            callback_result = progress_callback(progress)
                            if inspect.isawaitable(callback_result):
                                await callback_result
                        continue
                    if message.get("type") != "result" or not isinstance(
                        message.get("ok"), bool
                    ):
                        raise RuntimeFailure(
                            "output_invalid", "Runtime response is invalid"
                        )
                    if request_id in self._cancelled_request_ids:
                        raise RuntimeFailure(
                            "cancelled", "Runtime operation was cancelled"
                        )
                    if not message["ok"]:
                        failure = message.get("failure")
                        category = (
                            str(failure.get("category"))
                            if isinstance(failure, Mapping)
                            else "internal_error"
                        )
                        raise RuntimeFailure(
                            category, "Runtime adapter rejected the operation"
                        )
                    result = message.get("result")
                    if not isinstance(result, Mapping) or not _finite(result):
                        raise RuntimeFailure(
                            "output_invalid", "Runtime output is invalid"
                        )
                    return dict(result)
            finally:
                self._current_request_id = None
                self._cancelled_request_ids.discard(request_id)

    async def verify(
        self,
        *,
        timeout: float = 5.0,
        progress_callback: ProgressHandler | None = None,
        fault_profile: str | None = None,
    ) -> Mapping[str, Any]:
        try:
            result = await self._exchange(
                "verify",
                {
                    "artifacts": self.artifacts,
                    "artifact_set_digest": self.artifact_set_digest,
                    "format": self.model_format,
                },
                timeout=timeout,
                progress_callback=progress_callback,
                fault_profile=fault_profile,
            )
        except RuntimeFailure as error:
            self.observer.record(
                "model.adapter.verify",
                trace_id=self.trace_id,
                state="failed",
                attributes={
                    "adapter_id": self.descriptor.adapter_id,
                    "artifact_set_digest": self.artifact_set_digest,
                    "failure_category": error.category,
                },
            )
            raise
        self.observer.record(
            "model.adapter.verify",
            trace_id=self.trace_id,
            attributes={
                "adapter_id": self.descriptor.adapter_id,
                "artifact_set_digest": self.artifact_set_digest,
            },
        )
        return result

    async def load(
        self,
        *,
        timeout: float = 5.0,
        progress_callback: ProgressHandler | None = None,
        fault_profile: str | None = None,
    ) -> str:
        result = await self._exchange(
            "load",
            {
                "artifacts": self.artifacts,
                "artifact_set_digest": self.artifact_set_digest,
                "format": self.model_format,
                "task_id": self.task_id,
                "execution_provider": "cpu",
            },
            timeout=timeout,
            progress_callback=progress_callback,
            fault_profile=fault_profile,
        )
        handle = str(result.get("model_handle") or "")
        if not _IDENTITY.fullmatch(handle):
            raise RuntimeFailure("load_failed", "Runtime model handle is invalid")
        return handle

    async def infer(
        self,
        model_handle: str,
        input_value: Mapping[str, Any],
        *,
        schema_digest: str,
        timeout: float,
        maximum_output_bytes: int,
        progress_callback: ProgressHandler | None = None,
        fault_profile: str | None = None,
        model_evidence: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        try:
            result = await self._exchange(
                "infer",
                {
                    "model_handle": model_handle,
                    "task_id": self.task_id,
                    "schema_digest": schema_digest,
                    "input": dict(input_value),
                    "maximum_output_bytes": maximum_output_bytes,
                    **(
                        {"model_evidence": dict(model_evidence)}
                        if model_evidence is not None
                        else {}
                    ),
                },
                timeout=timeout,
                progress_callback=progress_callback,
                fault_profile=fault_profile,
            )
        except RuntimeFailure as error:
            self.observer.record(
                "model.adapter.infer",
                trace_id=self.trace_id,
                state=("cancelled" if error.category == "cancelled" else "failed"),
                attributes={
                    "adapter_id": self.descriptor.adapter_id,
                    "task_id": self.task_id,
                    "failure_category": error.category,
                },
            )
            raise
        output = result.get("output")
        if not isinstance(output, Mapping) or not _finite(output):
            raise RuntimeFailure("output_invalid", "Runtime output is invalid")
        encoded = json.dumps(output, sort_keys=True, separators=(",", ":")).encode()
        if len(encoded) > maximum_output_bytes:
            raise RuntimeFailure(
                "output_invalid", "Runtime output exceeds its byte limit"
            )
        self.observer.record(
            "model.adapter.infer",
            trace_id=self.trace_id,
            attributes={
                "adapter_id": self.descriptor.adapter_id,
                "task_id": self.task_id,
                "schema_digest": schema_digest,
                "result_digest": canonical_digest(output),
            },
        )
        return dict(result)

    async def unload(self, model_handle: str, *, timeout: float = 2.0) -> None:
        if self._closed or self.process.returncode is not None:
            return
        await self._exchange("unload", {"model_handle": model_handle}, timeout=timeout)

    async def cancel_current(self, *, grace_seconds: float = 0.25) -> None:
        target = self._current_request_id
        if not target or self.process.returncode is not None:
            return
        cancel_id = "runtime-cancel-" + uuid.uuid4().hex
        self._cancelled_request_ids.add(target)
        try:
            await self._write(
                {
                    "operation": "cancel",
                    "request_id": cancel_id,
                    "target_request_id": target,
                }
            )
            await asyncio.sleep(max(0, grace_seconds))
        finally:
            if self._current_request_id == target:
                await self._terminate()

    async def _terminate(self) -> None:
        if self.process.returncode is None:
            self.process.kill()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=2.0)
            except TimeoutError:
                pass

    async def shutdown(self) -> str:
        if self._closed:
            return "clean" if not self.scratch.exists() else "residue"
        try:
            if self.process.returncode is None:
                try:
                    await self._exchange("shutdown", {}, timeout=1.0)
                except RuntimeFailure:
                    await self._terminate()
                if self.process.returncode is None:
                    try:
                        await asyncio.wait_for(self.process.wait(), timeout=1.0)
                    except TimeoutError:
                        await self._terminate()
        finally:
            self._closed = True
            if not self._stderr_task.done():
                self._stderr_task.cancel()
            await asyncio.gather(self._stderr_task, return_exceptions=True)
            try:
                _remove_tree(self.scratch)
            except OSError:
                pass
            self._on_close(self)
        cleanup_state = "clean" if not self.scratch.exists() else "residue"
        self.observer.record(
            "model.cleanup",
            trace_id=self.trace_id,
            state="succeeded" if cleanup_state == "clean" else "failed",
            attributes={
                "adapter_id": self.descriptor.adapter_id,
                "cleanup_state": cleanup_state,
            },
        )
        return cleanup_state


class RuntimeSupervisor:
    def __init__(
        self,
        registry: RuntimeAdapterRegistry,
        *,
        scratch_root: str | Path,
        observer: ModelBoundaryObserver | None = None,
        maximum_reserved_ram_bytes: int | None = None,
        maximum_reserved_disk_bytes: int | None = None,
    ) -> None:
        self.registry = registry
        root = Path(scratch_root).resolve()
        if root.parent == root:
            raise RuntimeFailure("runtime_unhealthy", "Runtime scratch root is unsafe")
        self.scratch_root = root
        self.scratch_root.mkdir(parents=True, exist_ok=True)
        self._sessions: set[RuntimeSession] = set()
        self.observer = observer or ModelBoundaryObserver()
        self.last_environment_keys: frozenset[str] = frozenset()
        self.maximum_reserved_ram_bytes = maximum_reserved_ram_bytes
        self.maximum_reserved_disk_bytes = maximum_reserved_disk_bytes
        self._reserved_ram_bytes = 0
        self._reserved_disk_bytes = 0
        for value in (maximum_reserved_ram_bytes, maximum_reserved_disk_bytes):
            if value is not None and not 1 <= value <= 1024**5:
                raise RuntimeFailure(
                    "resource_rejected", "Runtime reservation limit is invalid"
                )

    @property
    def active_process_count(self) -> int:
        return sum(session.process.returncode is None for session in self._sessions)

    @property
    def active_resource_reservations(self) -> tuple[int, int]:
        return self._reserved_ram_bytes, self._reserved_disk_bytes

    def _reserve(self, ram_bytes: int, disk_bytes: int) -> None:
        if not 0 <= ram_bytes <= 1024**5 or not 0 <= disk_bytes <= 1024**5:
            raise RuntimeFailure(
                "resource_rejected", "Runtime resource declaration is invalid"
            )
        next_ram = self._reserved_ram_bytes + ram_bytes
        next_disk = self._reserved_disk_bytes + disk_bytes
        if (
            self.maximum_reserved_ram_bytes is not None
            and next_ram > self.maximum_reserved_ram_bytes
        ) or (
            self.maximum_reserved_disk_bytes is not None
            and next_disk > self.maximum_reserved_disk_bytes
        ):
            raise RuntimeFailure(
                "resource_rejected", "Runtime resource reservation is unavailable"
            )
        self._reserved_ram_bytes = next_ram
        self._reserved_disk_bytes = next_disk

    def _release(self, ram_bytes: int, disk_bytes: int) -> None:
        self._reserved_ram_bytes = max(0, self._reserved_ram_bytes - ram_bytes)
        self._reserved_disk_bytes = max(0, self._reserved_disk_bytes - disk_bytes)

    def _close_session(
        self, session: RuntimeSession, ram_bytes: int, disk_bytes: int
    ) -> None:
        self._sessions.discard(session)
        self._release(ram_bytes, disk_bytes)

    @staticmethod
    def _clean_environment() -> dict[str, str]:
        result = {
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUNBUFFERED": "1",
        }
        for key in ("SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP"):
            if value := os.environ.get(key):
                result[key] = value
        return result

    @staticmethod
    def _validate_request(
        registration: AdapterRegistration,
        *,
        model_format: str,
        task_id: str,
        platform: str,
        architecture: str,
        execution_provider: str,
    ) -> None:
        if model_format not in registration.formats:
            raise RuntimeFailure("unsupported_format", "Model format is unsupported")
        if task_id not in registration.tasks:
            raise RuntimeFailure("unsupported_task", "Engineering task is unsupported")
        if (
            platform not in registration.platforms
            or architecture not in registration.architectures
            or execution_provider not in registration.execution_providers
        ):
            raise RuntimeFailure(
                "incompatible_provider", "Runtime execution provider is incompatible"
            )

    @staticmethod
    def _check_descriptor(
        registration: AdapterRegistration, descriptor: AdapterDescriptor
    ) -> None:
        if (
            descriptor.adapter_id != registration.adapter_id
            or descriptor.adapter_version != registration.adapter_version
            or descriptor.contract_version != registration.contract_version
            or descriptor.health != "healthy"
            or not registration.formats <= descriptor.formats
            or not registration.tasks <= descriptor.tasks
            or not registration.platforms <= descriptor.platforms
            or not registration.architectures <= descriptor.architectures
            or not registration.execution_providers <= descriptor.execution_providers
        ):
            raise RuntimeFailure(
                "runtime_unhealthy", "Runtime adapter identity or capability changed"
            )

    def _prepare_artifacts(
        self,
        scratch: Path,
        artifacts: Mapping[str, Path],
        *,
        maximum_artifact_bytes: int,
    ) -> tuple[dict[str, str], str]:
        if not artifacts or len(artifacts) > 1000:
            raise RuntimeFailure("artifact_invalid", "Runtime artifact set is invalid")
        root = scratch / "artifacts"
        root.mkdir(parents=True)
        digests: dict[str, str] = {}
        total = 0
        for raw_key, source in artifacts.items():
            key = _artifact_key(str(raw_key))
            origin = Path(source).resolve()
            if not origin.is_file() or origin.is_symlink():
                raise RuntimeFailure(
                    "artifact_missing", "Runtime artifact is unavailable"
                )
            total += origin.stat().st_size
            if total > maximum_artifact_bytes:
                raise RuntimeFailure(
                    "resource_rejected", "Runtime artifacts exceed limit"
                )
            target = root.joinpath(*key.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(origin, target)
            target.chmod(stat.S_IREAD)
            digests[key.as_posix()] = _sha256(target)
        for directory in sorted(
            (item for item in root.rglob("*") if item.is_dir()),
            key=lambda item: len(item.parts),
            reverse=True,
        ):
            directory.chmod(stat.S_IREAD | stat.S_IEXEC)
        root.chmod(stat.S_IREAD | stat.S_IEXEC)
        return dict(sorted(digests.items())), canonical_digest(
            dict(sorted(digests.items()))
        )

    async def start_session(
        self,
        *,
        adapter_id: str,
        installation_id: str,
        artifacts: Mapping[str, Path],
        model_format: str,
        task_id: str,
        platform: str,
        architecture: str,
        execution_provider: str,
        health_fault_profile: str | None = None,
        startup_timeout: float = 2.0,
        maximum_artifact_bytes: int = 1024 * 1024 * 1024,
        required_ram_bytes: int = 0,
        required_disk_bytes: int = 0,
        trace_id: str = "no-active-span",
    ) -> RuntimeSession:
        registration = self.registry.get(adapter_id)
        self._validate_request(
            registration,
            model_format=model_format,
            task_id=task_id,
            platform=platform,
            architecture=architecture,
            execution_provider=execution_provider,
        )
        if not _IDENTITY.fullmatch(installation_id):
            raise RuntimeFailure("artifact_invalid", "Installation identity is invalid")
        if (
            not math.isfinite(startup_timeout)
            or startup_timeout <= 0
            or startup_timeout > 30
        ):
            raise RuntimeFailure(
                "resource_rejected", "Runtime startup timeout is invalid"
            )
        if not 1 <= maximum_artifact_bytes <= 1024 * 1024 * 1024 * 1024:
            raise RuntimeFailure(
                "resource_rejected", "Runtime artifact limit is invalid"
            )
        self._reserve(required_ram_bytes, required_disk_bytes)
        reservation_active = True
        scratch = self.scratch_root / ("runtime-" + uuid.uuid4().hex)
        scratch.mkdir(parents=True)
        process: asyncio.subprocess.Process | None = None
        session: RuntimeSession | None = None
        try:
            digest_map, artifact_set_digest = self._prepare_artifacts(
                scratch,
                artifacts,
                maximum_artifact_bytes=maximum_artifact_bytes,
            )
            environment = self._clean_environment()
            self.last_environment_keys = frozenset(environment)
            kwargs: dict[str, Any] = {
                "stdin": asyncio.subprocess.PIPE,
                "stdout": asyncio.subprocess.PIPE,
                "stderr": asyncio.subprocess.PIPE,
                "cwd": str(scratch),
                "env": environment,
                "limit": registration.maximum_control_bytes,
            }
            if os.name == "nt":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            process = await asyncio.create_subprocess_exec(
                *registration.command,
                "--artifact-root",
                str(scratch / "artifacts"),
                **kwargs,
            )
            placeholder = AdapterDescriptor(
                registration.adapter_id,
                registration.adapter_version,
                registration.contract_version,
                registration.formats,
                registration.tasks,
                registration.platforms,
                registration.architectures,
                registration.execution_providers,
                registration.maximum_control_bytes,
                1,
                True,
                True,
                "healthy",
                {},
            )
            session = RuntimeSession(
                registration=registration,
                process=process,
                scratch=scratch,
                artifacts=digest_map,
                artifact_set_digest=artifact_set_digest,
                model_format=model_format,
                task_id=task_id,
                descriptor=placeholder,
                observer=self.observer,
                trace_id=trace_id,
                on_close=lambda value: self._close_session(
                    value, required_ram_bytes, required_disk_bytes
                ),
            )
            self._sessions.add(session)
            health = await session._exchange(
                "health",
                {},
                timeout=startup_timeout,
                fault_profile=health_fault_profile,
            )
            descriptor = AdapterDescriptor.parse(health)
            self._check_descriptor(registration, descriptor)
            session.descriptor = descriptor
            reservation_active = False
            return session
        except Exception:
            if session is not None:
                await session.shutdown()
                reservation_active = False
            elif process is not None and process.returncode is None:
                process.kill()
                await process.wait()
            try:
                _remove_tree(scratch)
            except OSError:
                pass
            if reservation_active:
                self._release(required_ram_bytes, required_disk_bytes)
            raise

    async def shutdown(self) -> tuple[str, ...]:
        return tuple(
            await asyncio.gather(
                *(session.shutdown() for session in tuple(self._sessions))
            )
        )


def current_runtime_platform() -> tuple[str, str]:
    import platform as platform_module

    systems = {"darwin": "macos", "linux": "linux", "windows": "windows"}
    machines = {
        "amd64": "x86_64",
        "x86_64": "x86_64",
        "aarch64": "aarch64",
        "arm64": "aarch64",
    }
    return (
        systems.get(platform_module.system().lower(), "unknown"),
        machines.get(platform_module.machine().lower(), "unknown"),
    )


def built_in_runtime_registry() -> RuntimeAdapterRegistry:
    system, architecture = current_runtime_platform()
    child = Path(__file__).with_name("affine_runtime.py")
    registrations = [
        AdapterRegistration(
            adapter_id="wright-deterministic",
            adapter_version="1.0.0",
            contract_version="1.0",
            command=(sys.executable, "-I", str(child)),
            formats=frozenset({"wright-affine-json"}),
            tasks=frozenset({"predict"}),
            platforms=frozenset({system}),
            architectures=frozenset({architecture}),
            execution_providers=frozenset({"cpu"}),
        )
    ]
    if importlib.util.find_spec("numpy") is not None:
        registrations.append(
            AdapterRegistration(
                adapter_id="wright-neuralfoil-numpy",
                adapter_version="1.0.0",
                contract_version="1.0",
                command=(
                    sys.executable,
                    "-I",
                    str(Path(__file__).with_name("neuralfoil_runtime.py")),
                ),
                formats=frozenset({"numpy-npz"}),
                tasks=frozenset({"airfoil_aerodynamics"}),
                platforms=frozenset({system}),
                architectures=frozenset({architecture}),
                execution_providers=frozenset({"cpu"}),
            )
        )
        registrations.append(
            AdapterRegistration(
                adapter_id="wright-chatter-forest-numpy",
                adapter_version="1.0.0",
                contract_version="1.0",
                command=(
                    sys.executable,
                    "-I",
                    str(Path(__file__).with_name("chatter_runtime.py")),
                ),
                formats=frozenset({"wright-chatter-forest-npz-1.0"}),
                tasks=frozenset({"screen_chatter_candidates"}),
                platforms=frozenset({system}),
                architectures=frozenset({architecture}),
                execution_providers=frozenset({"cpu"}),
            )
        )
    return RuntimeAdapterRegistry(registrations)


__all__ = [
    "AdapterDescriptor",
    "AdapterRegistration",
    "RuntimeAdapterRegistry",
    "RuntimeFailure",
    "RuntimeProgress",
    "RuntimeSession",
    "RuntimeSupervisor",
    "built_in_runtime_registry",
    "current_runtime_platform",
]
