from __future__ import annotations

import asyncio
import os
import sys
from datetime import UTC, datetime, timedelta

import psutil
import pytest

from workspace_service.surfaces.process_supervisor import (
    ProcessLaunchRequest,
    ProcessSupervisorError,
)
from workspace_service.surfaces.process_windows import WindowsProcessAdapter


pytestmark = [pytest.mark.workspace_surfaces, pytest.mark.asyncio]


def _request(tmp_path, code: str) -> ProcessLaunchRequest:
    environment = {
        name: value
        for name, value in os.environ.items()
        if name.upper()
        in {
            "PATH",
            "SYSTEMROOT",
            "WINDIR",
            "COMSPEC",
            "TEMP",
            "TMP",
            "PATHEXT",
            "PYTHONPATH",
        }
    }
    environment["PYTHONUNBUFFERED"] = "1"
    return ProcessLaunchRequest(
        workspace_id="workspace-1",
        instance_id="instance-1",
        generation=1,
        argv=(sys.executable, "-c", code),
        cwd=str(tmp_path.resolve()),
        environment=environment,
        limits={
            "graceful_shutdown_seconds": 0.1,
            "processes_per_owned_tree": 8,
            "memory_mib_per_owned_app": 256,
            "cpu_cores_per_owned_app": 1.0,
        },
        listener_handle=None,
    )


async def test_windows_adapter_reports_unavailable_off_windows(tmp_path) -> None:
    adapter = WindowsProcessAdapter(platform_name=lambda: "posix")
    with pytest.raises(ProcessSupervisorError) as raised:
        await adapter.launch(_request(tmp_path, "pass"))
    assert raised.value.code == "SURFACE_PROCESS_ADAPTER_UNAVAILABLE"


@pytest.mark.skipif(os.name != "nt", reason="requires Windows Job Objects")
async def test_hidden_suspended_launch_assigns_root_and_descendants_before_resume(
    tmp_path,
) -> None:
    code = (
        "import subprocess,sys,time; "
        "subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
        "print('ready', flush=True); time.sleep(60)"
    )
    process = await WindowsProcessAdapter(descendant_poll_seconds=0.02).launch(
        _request(tmp_path, code)
    )
    await asyncio.sleep(0.25)

    assert process.identity.adapter == "windows-job-object"
    assert process.identity.executable
    assert process._job.contains(process.identity.pid)  # noqa: SLF001
    children = psutil.Process(process.identity.pid).children(recursive=True)
    assert children and all(process._job.contains(child.pid) for child in children)  # noqa: SLF001

    report = await process.stop(deadline=datetime.now(UTC) + timedelta(seconds=2))
    assert report.descendants_remaining == ()
    assert report.listeners_remaining == ()


@pytest.mark.skipif(os.name != "nt", reason="requires Windows Job Objects")
async def test_job_handle_close_kills_entire_tree(tmp_path) -> None:
    process = await WindowsProcessAdapter().launch(
        _request(tmp_path, "import time; time.sleep(60)")
    )
    pid = process.identity.pid
    process._job.close()  # noqa: SLF001 - verifies kill-on-close contract
    await asyncio.wait_for(process.wait(), timeout=2)
    assert not psutil.pid_exists(pid)
    process._monitor_task.cancel()  # noqa: SLF001
    await asyncio.gather(process._monitor_task, return_exceptions=True)  # noqa: SLF001


@pytest.mark.skipif(os.name != "nt", reason="requires Windows Job Objects")
async def test_pid_reuse_or_executable_mismatch_does_not_terminate_job(
    tmp_path, monkeypatch
) -> None:
    process = await WindowsProcessAdapter().launch(
        _request(tmp_path, "import time; time.sleep(60)")
    )
    pid = process.identity.pid
    monkeypatch.setattr(process, "_root_identity_valid", lambda: False)
    report = await process.stop(deadline=datetime.now(UTC) + timedelta(seconds=0.2))
    assert report.degraded_reason and "identity changed" in report.degraded_reason
    assert psutil.pid_exists(pid)

    process._job.terminate()  # noqa: SLF001
    process._job.close()  # noqa: SLF001
    await process.wait()
    process._monitor_task.cancel()  # noqa: SLF001
    await asyncio.gather(process._monitor_task, return_exceptions=True)  # noqa: SLF001


@pytest.mark.skipif(os.name != "nt", reason="requires Windows Job Objects")
async def test_listener_and_breakaway_evidence_are_reconciled(
    tmp_path, monkeypatch
) -> None:
    code = (
        "import socket,time; s=socket.socket(); s.bind(('127.0.0.1',0)); "
        "s.listen(); print(s.getsockname()[1], flush=True); time.sleep(60)"
    )
    process = await WindowsProcessAdapter(descendant_poll_seconds=0.01).launch(
        _request(tmp_path, code)
    )
    listeners: tuple[str, ...] = ()
    for _ in range(100):
        listeners = process._remaining_listeners()  # noqa: SLF001
        if listeners:
            break
        await asyncio.sleep(0.02)
    assert listeners
    real_contains = process._job.contains  # noqa: SLF001
    monkeypatch.setattr(
        process._job,  # noqa: SLF001
        "contains",
        lambda pid: False if pid == process.identity.pid else real_contains(pid),
    )
    report = await process.stop(deadline=datetime.now(UTC) + timedelta(seconds=2))
    assert report.degraded_reason and "break away" in report.degraded_reason
    assert report.listeners_remaining == ()


@pytest.mark.skipif(os.name != "nt", reason="requires Windows Job Objects")
async def test_assignment_failure_terminates_suspended_process_and_reports_error(
    tmp_path,
) -> None:
    class FailingJob:
        def __init__(self, **_kwargs) -> None:
            self.pid = None

        def assign(self, pid: int) -> None:
            self.pid = pid
            raise OSError("assignment denied")

        def terminate(self) -> None:
            if self.pid is not None:
                psutil.Process(self.pid).kill()

        def close(self) -> None:
            return None

    adapter = WindowsProcessAdapter(job_factory=FailingJob)
    with pytest.raises(ProcessSupervisorError) as raised:
        await adapter.launch(_request(tmp_path, "import time; time.sleep(60)"))
    assert raised.value.code == "SURFACE_PROCESS_CONTAINMENT_FAILED"


@pytest.mark.skipif(os.name != "nt", reason="requires Windows Job Objects")
async def test_stop_cancellation_waits_for_job_cleanup(tmp_path) -> None:
    process = await WindowsProcessAdapter(graceful_seconds=0.1).launch(
        _request(tmp_path, "import time; time.sleep(60)")
    )
    pid = process.identity.pid
    task = asyncio.create_task(
        process.stop(deadline=datetime.now(UTC) + timedelta(seconds=2))
    )
    await asyncio.sleep(0.02)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert not psutil.pid_exists(pid)
