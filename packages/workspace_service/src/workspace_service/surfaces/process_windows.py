"""Windows hidden-process and kill-on-close Job Object adapter."""

from __future__ import annotations

import asyncio
import ctypes
import hashlib
import json
import os
import signal
import subprocess
from collections.abc import AsyncIterator, Callable
from ctypes import wintypes
from datetime import UTC, datetime
from pathlib import Path

import psutil

from workspace_service.surfaces.process_supervisor import (
    PlatformProcessIdentity,
    ProcessLaunchRequest,
    ProcessStopResult,
    ProcessSupervisorError,
)


_KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True) if os.name == "nt" else None

_PROCESS_TERMINATE = 0x0001
_PROCESS_SET_QUOTA = 0x0100
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_THREAD_SUSPEND_RESUME = 0x0002
_JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 0x00000008
_JOB_OBJECT_LIMIT_JOB_MEMORY = 0x00000200
_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
_JOB_OBJECT_CPU_RATE_CONTROL_ENABLE = 0x1
_JOB_OBJECT_CPU_RATE_CONTROL_HARD_CAP = 0x4
_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
_JOB_OBJECT_CPU_RATE_CONTROL_INFORMATION = 15
_INVALID_RESUME_RESULT = 0xFFFFFFFF
_CREATE_SUSPENDED = 0x00000004


if _KERNEL32 is not None:
    _KERNEL32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    _KERNEL32.CreateJobObjectW.restype = wintypes.HANDLE
    _KERNEL32.SetInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    _KERNEL32.SetInformationJobObject.restype = wintypes.BOOL
    _KERNEL32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    _KERNEL32.OpenProcess.restype = wintypes.HANDLE
    _KERNEL32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    _KERNEL32.AssignProcessToJobObject.restype = wintypes.BOOL
    _KERNEL32.IsProcessInJob.argtypes = [
        wintypes.HANDLE,
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.BOOL),
    ]
    _KERNEL32.IsProcessInJob.restype = wintypes.BOOL
    _KERNEL32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    _KERNEL32.TerminateJobObject.restype = wintypes.BOOL
    _KERNEL32.OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    _KERNEL32.OpenThread.restype = wintypes.HANDLE
    _KERNEL32.ResumeThread.argtypes = [wintypes.HANDLE]
    _KERNEL32.ResumeThread.restype = wintypes.DWORD
    _KERNEL32.CloseHandle.argtypes = [wintypes.HANDLE]
    _KERNEL32.CloseHandle.restype = wintypes.BOOL


class _JobBasicLimitInformation(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class _IoCounters(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class _JobExtendedLimitInformation(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _JobBasicLimitInformation),
        ("IoInfo", _IoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class _JobCpuRateControlInformation(ctypes.Structure):
    _fields_ = [("ControlFlags", wintypes.DWORD), ("CpuRate", wintypes.DWORD)]


def _windows_error(message: str) -> OSError:
    return ctypes.WinError(ctypes.get_last_error(), message)


def _remaining_seconds(deadline: datetime) -> float:
    normalized = deadline if deadline.tzinfo else deadline.replace(tzinfo=UTC)
    return max(0.0, (normalized - datetime.now(UTC)).total_seconds())


class WindowsJob:
    """Minimal safe Job Object owner; closing it terminates all assigned members."""

    def __init__(
        self, *, max_processes: int, max_memory_mib: int, cpu_cores: float
    ) -> None:
        if _KERNEL32 is None:
            raise OSError("Windows Job Objects are unavailable")
        self._handle = _KERNEL32.CreateJobObjectW(None, None)
        if not self._handle:
            raise _windows_error("Could not create Windows Job Object")
        self._closed = False
        try:
            limits = _JobExtendedLimitInformation()
            limits.BasicLimitInformation.LimitFlags = (
                _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
                | _JOB_OBJECT_LIMIT_ACTIVE_PROCESS
                | _JOB_OBJECT_LIMIT_JOB_MEMORY
            )
            limits.BasicLimitInformation.ActiveProcessLimit = max_processes
            limits.JobMemoryLimit = max_memory_mib * 1024 * 1024
            self._set_information(_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION, limits)

            logical_cpus = max(1, os.cpu_count() or 1)
            rate = max(1, min(10_000, round(cpu_cores / logical_cpus * 10_000)))
            cpu = _JobCpuRateControlInformation(
                _JOB_OBJECT_CPU_RATE_CONTROL_ENABLE
                | _JOB_OBJECT_CPU_RATE_CONTROL_HARD_CAP,
                rate,
            )
            self._set_information(_JOB_OBJECT_CPU_RATE_CONTROL_INFORMATION, cpu)
        except BaseException:
            self.close()
            raise

    @property
    def handle(self) -> int:
        if self._closed:
            raise OSError("Windows Job Object is closed")
        return int(self._handle)

    def _set_information(self, information_class: int, value: ctypes.Structure) -> None:
        assert _KERNEL32 is not None
        if not _KERNEL32.SetInformationJobObject(
            self._handle,
            information_class,
            ctypes.byref(value),
            ctypes.sizeof(value),
        ):
            raise _windows_error("Could not configure Windows Job Object")

    @staticmethod
    def _open_process(pid: int, access: int) -> int:
        assert _KERNEL32 is not None
        handle = _KERNEL32.OpenProcess(access, False, pid)
        if not handle:
            raise _windows_error("Could not open managed Windows process")
        return int(handle)

    def assign(self, pid: int) -> None:
        assert _KERNEL32 is not None
        process_handle = self._open_process(
            pid,
            _PROCESS_SET_QUOTA
            | _PROCESS_TERMINATE
            | _PROCESS_QUERY_LIMITED_INFORMATION,
        )
        try:
            if not _KERNEL32.AssignProcessToJobObject(self._handle, process_handle):
                raise _windows_error("Could not assign process to Windows Job Object")
        finally:
            _KERNEL32.CloseHandle(process_handle)

    def contains(self, pid: int) -> bool:
        assert _KERNEL32 is not None
        try:
            process_handle = self._open_process(pid, _PROCESS_QUERY_LIMITED_INFORMATION)
        except OSError:
            return False
        result = wintypes.BOOL()
        try:
            if not _KERNEL32.IsProcessInJob(
                process_handle, self._handle, ctypes.byref(result)
            ):
                raise _windows_error("Could not query Windows Job Object membership")
            return bool(result.value)
        finally:
            _KERNEL32.CloseHandle(process_handle)

    def terminate(self, exit_code: int = 1) -> None:
        assert _KERNEL32 is not None
        if not self._closed and not _KERNEL32.TerminateJobObject(
            self._handle, exit_code
        ):
            error = ctypes.get_last_error()
            if error not in {0, 5, 87}:
                raise ctypes.WinError(error)

    def close(self) -> None:
        if not self._closed and _KERNEL32 is not None:
            _KERNEL32.CloseHandle(self._handle)
            self._closed = True


class WindowsManagedProcess:
    def __init__(
        self,
        *,
        process: asyncio.subprocess.Process,
        request: ProcessLaunchRequest,
        job: WindowsJob,
        creation_time: float,
        executable: str,
        graceful_seconds: float,
        poll_seconds: float,
    ) -> None:
        self._process = process
        self._request = request
        self._job = job
        self._creation_time = creation_time
        self._executable = executable
        self._graceful_seconds = graceful_seconds
        self._poll_seconds = poll_seconds
        self._owned: dict[int, float] = {process.pid: creation_time}
        self._monitor_task = asyncio.create_task(
            self._monitor_descendants(),
            name=f"surface-windows-{process.pid}-descendants",
        )
        digest = hashlib.sha256(
            json.dumps(request.argv, separators=(",", ":")).encode()
        ).hexdigest()
        self.identity = PlatformProcessIdentity(
            adapter="windows-job-object",
            pid=process.pid,
            creation_time=creation_time,
            containment_id=f"job:{job.handle:x}",
            containment_mode="kill-on-close-job-object",
            executable=executable,
            command_digest=digest,
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
            return abs(psutil.Process(pid).create_time() - creation_time) < 0.001
        except psutil.Error:
            return False

    def _root_identity_valid(self) -> bool:
        if not self._same_process(self._process.pid, self._creation_time):
            return False
        try:
            actual = str(Path(psutil.Process(self._process.pid).exe()).resolve())
        except (psutil.Error, OSError):
            return False
        return os.path.normcase(actual) == os.path.normcase(self._executable)

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

    def _remaining_owned(self) -> tuple[str, ...]:
        return tuple(
            f"{pid}:{created:.6f}"
            for pid, created in sorted(self._owned.items())
            if self._same_process(pid, created)
        )

    def _remaining_listeners(self) -> tuple[str, ...]:
        owned = {
            pid
            for pid, created in self._owned.items()
            if self._same_process(pid, created)
        }
        try:
            connections = psutil.net_connections(kind="tcp")
        except psutil.Error:
            return ()
        return tuple(
            sorted(
                {
                    f"{item.laddr.ip}:{item.laddr.port}"
                    for item in connections
                    if item.pid in owned
                    and item.status == psutil.CONN_LISTEN
                    and item.laddr
                }
            )
        )

    def _kill_recorded_breakaways(self) -> bool:
        breakaway = False
        for pid, created in tuple(self._owned.items()):
            if not self._same_process(pid, created):
                continue
            if self._job.contains(pid):
                continue
            breakaway = True
            try:
                psutil.Process(pid).kill()
            except psutil.Error:
                continue
        return breakaway

    async def _stop_impl(self, *, deadline: datetime) -> ProcessStopResult:
        if self._process.returncode is None and not self._root_identity_valid():
            return ProcessStopResult(
                exit_code=self._process.returncode,
                graceful=False,
                forced=False,
                descendants_remaining=self._remaining_owned(),
                listeners_remaining=self._remaining_listeners(),
                degraded_reason="PID, creation time, or executable identity changed; Job was not signalled",
            )
        graceful = self._process.returncode is not None
        if not graceful:
            try:
                self._process.send_signal(signal.CTRL_BREAK_EVENT)
            except (OSError, ProcessLookupError, ValueError):
                pass
            graceful = await self._wait_for_exit(
                min(self._graceful_seconds, _remaining_seconds(deadline))
            )
        forced = not graceful
        if forced:
            self._job.terminate()
        breakaway = self._kill_recorded_breakaways()
        await self._wait_for_exit(_remaining_seconds(deadline))
        while _remaining_seconds(deadline) > 0:
            descendants = self._remaining_owned()
            listeners = self._remaining_listeners()
            if not descendants and not listeners:
                break
            breakaway = self._kill_recorded_breakaways() or breakaway
            await asyncio.sleep(min(self._poll_seconds, _remaining_seconds(deadline)))
        else:
            descendants = self._remaining_owned()
            listeners = self._remaining_listeners()
        self._monitor_task.cancel()
        await asyncio.gather(self._monitor_task, return_exceptions=True)
        self._job.close()
        return ProcessStopResult(
            exit_code=self._process.returncode,
            graceful=graceful,
            forced=forced,
            descendants_remaining=descendants,
            listeners_remaining=listeners,
            degraded_reason=(
                "A recorded descendant attempted to break away from the Job Object"
                if breakaway
                else None
            ),
        )

    async def stop(self, *, deadline: datetime) -> ProcessStopResult:
        cleanup = asyncio.create_task(self._stop_impl(deadline=deadline))
        try:
            return await asyncio.shield(cleanup)
        except asyncio.CancelledError:
            await asyncio.shield(cleanup)
            raise


class WindowsProcessAdapter:
    def __init__(
        self,
        *,
        graceful_seconds: float = 5.0,
        descendant_poll_seconds: float = 0.1,
        platform_name: Callable[[], str] | None = None,
        job_factory: Callable[..., WindowsJob] = WindowsJob,
    ) -> None:
        if graceful_seconds <= 0 or descendant_poll_seconds <= 0:
            raise ValueError("Windows process timing bounds must be positive")
        self._graceful_seconds = graceful_seconds
        self._poll_seconds = descendant_poll_seconds
        self._platform_name = platform_name or (lambda: os.name)
        self._job_factory = job_factory

    @staticmethod
    def _resume_primary_thread(pid: int) -> None:
        assert _KERNEL32 is not None
        try:
            threads = psutil.Process(pid).threads()
        except psutil.Error as error:
            raise OSError("Could not enumerate suspended primary thread") from error
        if not threads:
            raise OSError("Suspended process has no primary thread")
        thread_id = min(item.id for item in threads)
        handle = _KERNEL32.OpenThread(_THREAD_SUSPEND_RESUME, False, thread_id)
        if not handle:
            raise _windows_error("Could not open suspended primary thread")
        try:
            if _KERNEL32.ResumeThread(handle) == _INVALID_RESUME_RESULT:
                raise _windows_error("Could not resume managed process")
        finally:
            _KERNEL32.CloseHandle(handle)

    async def launch(self, request: ProcessLaunchRequest) -> WindowsManagedProcess:
        if self._platform_name() != "nt" or _KERNEL32 is None:
            raise ProcessSupervisorError(
                "SURFACE_PROCESS_ADAPTER_UNAVAILABLE",
                "Windows Job Object containment is unavailable on this host",
            )
        try:
            job = self._job_factory(
                max_processes=int(request.limits.get("processes_per_owned_tree", 32)),
                max_memory_mib=int(
                    request.limits.get("memory_mib_per_owned_app", 2048)
                ),
                cpu_cores=float(request.limits.get("cpu_cores_per_owned_app", 2.0)),
            )
        except OSError as error:
            raise ProcessSupervisorError(
                "SURFACE_PROCESS_CONTAINMENT_DEGRADED",
                "Required Windows Job Object limits could not be configured",
            ) from error

        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = subprocess.SW_HIDE
        if request.listener_handle is not None:
            os.set_handle_inheritable(request.listener_handle, True)
            startup.lpAttributeList = {"handle_list": [request.listener_handle]}
        creation_flags = (
            _CREATE_SUSPENDED
            | subprocess.CREATE_NEW_PROCESS_GROUP
            | subprocess.CREATE_NO_WINDOW
        )
        process: asyncio.subprocess.Process | None = None
        try:
            process = await asyncio.create_subprocess_exec(
                *request.argv,
                cwd=request.cwd,
                env=dict(request.environment),
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=creation_flags,
                startupinfo=startup,
                close_fds=True,
            )
            identity = psutil.Process(process.pid)
            creation_time = identity.create_time()
            executable = str(Path(identity.exe()).resolve())
            job.assign(process.pid)
            self._resume_primary_thread(process.pid)
        except BaseException as error:
            if process is not None and process.returncode is None:
                try:
                    job.terminate()
                except OSError:
                    process.kill()
                await process.wait()
            job.close()
            if isinstance(error, asyncio.CancelledError):
                raise
            raise ProcessSupervisorError(
                "SURFACE_PROCESS_CONTAINMENT_FAILED",
                "Managed process could not be assigned to a Windows Job Object before resume",
            ) from error
        return WindowsManagedProcess(
            process=process,
            request=request,
            job=job,
            creation_time=creation_time,
            executable=executable,
            graceful_seconds=min(
                self._graceful_seconds,
                float(request.limits.get("graceful_shutdown_seconds", 5)),
            ),
            poll_seconds=self._poll_seconds,
        )


__all__ = ["WindowsJob", "WindowsManagedProcess", "WindowsProcessAdapter"]
