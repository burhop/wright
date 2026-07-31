"""POSIX process-group adapter for owned live applications."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import signal
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime
from pathlib import Path

import psutil

from workspace_service.surfaces.process_supervisor import (
    PlatformProcessIdentity,
    ProcessLaunchRequest,
    ProcessStopResult,
    ProcessSupervisorError,
)


def _command_digest(argv: tuple[str, ...]) -> str:
    encoded = json.dumps(argv, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _resolve_executable(value: str) -> str | None:
    candidate = shutil.which(value)
    if candidate is None:
        return None
    return str(Path(candidate).resolve())


def _remaining_seconds(deadline: datetime) -> float:
    normalized = deadline if deadline.tzinfo else deadline.replace(tzinfo=UTC)
    return max(0.0, (normalized - datetime.now(UTC)).total_seconds())


class PosixManagedProcess:
    def __init__(
        self,
        *,
        process: asyncio.subprocess.Process,
        request: ProcessLaunchRequest,
        creation_time: float,
        executable: str | None,
        graceful_seconds: float,
        poll_seconds: float,
    ) -> None:
        self._process = process
        self._request = request
        self._creation_time = creation_time
        self._executable = executable
        self._graceful_seconds = graceful_seconds
        self._poll_seconds = poll_seconds
        self._owned: dict[int, float] = {process.pid: creation_time}
        self._monitor_task = asyncio.create_task(
            self._monitor_descendants(),
            name=f"surface-posix-{process.pid}-descendants",
        )
        self.identity = PlatformProcessIdentity(
            adapter="posix-process-group",
            pid=process.pid,
            creation_time=creation_time,
            containment_id=f"pgid:{process.pid}",
            containment_mode="process-group-with-psutil-reconciliation",
            executable=executable,
            command_digest=_command_digest(request.argv),
        )

    async def _read_stream(
        self, reader: asyncio.StreamReader | None
    ) -> AsyncIterator[bytes]:
        if reader is None:
            return
        while payload := await reader.read(64 * 1024):
            yield payload

    def stdout(self) -> AsyncIterator[bytes]:
        return self._read_stream(self._process.stdout)

    def stderr(self) -> AsyncIterator[bytes]:
        return self._read_stream(self._process.stderr)

    async def wait(self) -> int:
        return await self._process.wait()

    def owned_processes(self) -> tuple[tuple[int, float], ...]:
        return tuple(sorted(self._owned.items()))

    @staticmethod
    def _same_process(pid: int, creation_time: float) -> bool:
        try:
            process = psutil.Process(pid)
            return abs(process.create_time() - creation_time) < 0.001
        except (psutil.Error, OSError):
            return False

    async def _monitor_descendants(self) -> None:
        try:
            while self._process.returncode is None:
                try:
                    root = psutil.Process(self._process.pid)
                    if abs(root.create_time() - self._creation_time) >= 0.001:
                        return
                    for child in root.children(recursive=True):
                        try:
                            self._owned.setdefault(child.pid, child.create_time())
                        except psutil.Error:
                            continue
                except psutil.Error:
                    return
                await asyncio.sleep(self._poll_seconds)
        except asyncio.CancelledError:
            raise

    def _root_identity_valid(self) -> bool:
        if not self._same_process(self._process.pid, self._creation_time):
            return False
        if self._executable is None:
            return True
        try:
            actual = str(Path(psutil.Process(self._process.pid).exe()).resolve())
        except (psutil.Error, OSError):
            return False
        return os.path.normcase(actual) == os.path.normcase(self._executable)

    @staticmethod
    def _signal_group(group_id: int, value: signal.Signals) -> None:
        try:
            os.killpg(group_id, value)
        except ProcessLookupError:
            return

    async def _wait_for_exit(self, seconds: float) -> bool:
        if self._process.returncode is not None:
            return True
        if seconds <= 0:
            return False
        try:
            await asyncio.wait_for(
                asyncio.shield(self._process.wait()), timeout=seconds
            )
            return True
        except TimeoutError:
            return False

    def _kill_tracked_outside_group(self, group_id: int) -> None:
        for pid, created in tuple(self._owned.items()):
            if pid == self._process.pid or not self._same_process(pid, created):
                continue
            try:
                if os.getpgid(pid) == group_id:
                    continue
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                continue

    def _remaining_owned(self) -> tuple[str, ...]:
        return tuple(
            f"{pid}:{created:.6f}"
            for pid, created in sorted(self._owned.items())
            if self._same_process(pid, created)
        )

    def _remaining_listeners(self) -> tuple[str, ...]:
        owned_pids = {
            pid
            for pid, created in self._owned.items()
            if self._same_process(pid, created)
        }
        listeners: list[str] = []
        try:
            connections = psutil.net_connections(kind="tcp")
        except (psutil.Error, OSError):
            return ()
        for connection in connections:
            if (
                connection.pid in owned_pids
                and connection.status == psutil.CONN_LISTEN
                and connection.laddr
            ):
                listeners.append(f"{connection.laddr.ip}:{connection.laddr.port}")
        return tuple(sorted(set(listeners)))

    async def _stop_impl(self, *, deadline: datetime) -> ProcessStopResult:
        root_alive = self._process.returncode is None
        if root_alive and not self._root_identity_valid():
            return ProcessStopResult(
                exit_code=self._process.returncode,
                graceful=False,
                forced=False,
                descendants_remaining=self._remaining_owned(),
                listeners_remaining=self._remaining_listeners(),
                degraded_reason="PID, creation time, or executable identity changed; no signal sent",
            )
        group_id = self._process.pid
        graceful = self._process.returncode is not None
        forced = False
        if root_alive:
            try:
                if os.getpgid(self._process.pid) != group_id:
                    return ProcessStopResult(
                        exit_code=self._process.returncode,
                        graceful=False,
                        forced=False,
                        descendants_remaining=self._remaining_owned(),
                        listeners_remaining=self._remaining_listeners(),
                        degraded_reason="Root process is no longer in its owned process group",
                    )
            except (ProcessLookupError, PermissionError, OSError):
                root_alive = False
            if root_alive:
                self._signal_group(group_id, signal.SIGTERM)
                graceful = await self._wait_for_exit(
                    min(self._graceful_seconds, _remaining_seconds(deadline))
                )
        if not graceful:
            forced = True
            self._signal_group(group_id, signal.SIGKILL)
        self._kill_tracked_outside_group(group_id)
        await self._wait_for_exit(_remaining_seconds(deadline))
        while _remaining_seconds(deadline) > 0:
            descendants = self._remaining_owned()
            listeners = self._remaining_listeners()
            if not descendants and not listeners:
                break
            self._kill_tracked_outside_group(group_id)
            await asyncio.sleep(min(self._poll_seconds, _remaining_seconds(deadline)))
        else:
            descendants = self._remaining_owned()
            listeners = self._remaining_listeners()
        self._monitor_task.cancel()
        await asyncio.gather(self._monitor_task, return_exceptions=True)
        return ProcessStopResult(
            exit_code=self._process.returncode,
            graceful=graceful,
            forced=forced,
            descendants_remaining=descendants,
            listeners_remaining=listeners,
        )

    async def stop(self, *, deadline: datetime) -> ProcessStopResult:
        cleanup = asyncio.create_task(self._stop_impl(deadline=deadline))
        try:
            return await asyncio.shield(cleanup)
        except asyncio.CancelledError:
            await asyncio.shield(cleanup)
            raise


class PosixProcessAdapter:
    def __init__(
        self,
        *,
        graceful_seconds: float = 5.0,
        descendant_poll_seconds: float = 0.1,
        platform_name: Callable[[], str] | None = None,
    ) -> None:
        if graceful_seconds <= 0 or descendant_poll_seconds <= 0:
            raise ValueError("POSIX process timing bounds must be positive")
        self._graceful_seconds = graceful_seconds
        self._poll_seconds = descendant_poll_seconds
        self._platform_name = platform_name or (lambda: os.name)

    async def launch(self, request: ProcessLaunchRequest) -> PosixManagedProcess:
        if self._platform_name() != "posix":
            raise ProcessSupervisorError(
                "SURFACE_PROCESS_ADAPTER_UNAVAILABLE",
                "POSIX process-group containment is unavailable on this host",
            )
        pass_fds = () if request.listener_handle is None else (request.listener_handle,)
        process = await asyncio.create_subprocess_exec(
            *request.argv,
            cwd=request.cwd,
            env=dict(request.environment),
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
            pass_fds=pass_fds,
        )
        try:
            creation_time = psutil.Process(process.pid).create_time()
        except psutil.Error as error:
            process.kill()
            await process.wait()
            raise ProcessSupervisorError(
                "SURFACE_PROCESS_IDENTITY_UNAVAILABLE",
                "Could not capture POSIX process creation identity",
            ) from error
        return PosixManagedProcess(
            process=process,
            request=request,
            creation_time=creation_time,
            executable=_resolve_executable(request.argv[0]),
            graceful_seconds=min(
                self._graceful_seconds,
                float(request.limits.get("graceful_shutdown_seconds", 5)),
            ),
            poll_seconds=self._poll_seconds,
        )


__all__ = ["PosixManagedProcess", "PosixProcessAdapter"]
