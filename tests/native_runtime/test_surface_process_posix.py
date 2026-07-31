from __future__ import annotations

import asyncio
import os
import signal
import sys
from datetime import UTC, datetime, timedelta

import psutil
import pytest

from workspace_service.surfaces.process_posix import PosixProcessAdapter
from workspace_service.surfaces.process_supervisor import (
    ProcessLaunchRequest,
    ProcessSupervisorError,
)


pytestmark = [pytest.mark.workspace_surfaces, pytest.mark.asyncio]


def _request(tmp_path, code: str) -> ProcessLaunchRequest:
    environment = {
        name: value
        for name, value in os.environ.items()
        if name in {"PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "PYTHONPATH"}
    }
    environment["PYTHONUNBUFFERED"] = "1"
    return ProcessLaunchRequest(
        workspace_id="workspace-1",
        instance_id="instance-1",
        generation=1,
        argv=(sys.executable, "-c", code),
        cwd=str(tmp_path.resolve()),
        environment=environment,
        limits={"graceful_shutdown_seconds": 0.2},
        listener_handle=None,
    )


async def test_posix_adapter_reports_unavailable_off_posix(tmp_path) -> None:
    adapter = PosixProcessAdapter(platform_name=lambda: "nt")
    with pytest.raises(ProcessSupervisorError) as raised:
        await adapter.launch(_request(tmp_path, "pass"))
    assert raised.value.code == "SURFACE_PROCESS_ADAPTER_UNAVAILABLE"


@pytest.mark.skipif(os.name != "posix", reason="requires POSIX process groups")
async def test_new_session_descendants_and_graceful_group_stop(tmp_path) -> None:
    code = (
        "import signal,subprocess,sys,time; "
        "subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
        "signal.signal(signal.SIGTERM, lambda *_: sys.exit(0)); "
        "print('ready', flush=True); time.sleep(60)"
    )
    process = await PosixProcessAdapter(descendant_poll_seconds=0.02).launch(
        _request(tmp_path, code)
    )
    await asyncio.sleep(0.15)

    assert process.identity.containment_id == f"pgid:{process.identity.pid}"
    assert process.identity.executable
    report = await process.stop(deadline=datetime.now(UTC) + timedelta(seconds=2))

    assert report.graceful is True
    assert report.descendants_remaining == ()
    assert report.listeners_remaining == ()


@pytest.mark.skipif(os.name != "posix", reason="requires POSIX process groups")
async def test_ignored_graceful_signal_escalates_entire_group(tmp_path) -> None:
    code = "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)"
    process = await PosixProcessAdapter(graceful_seconds=0.05).launch(
        _request(tmp_path, code)
    )
    await asyncio.sleep(0.05)
    report = await process.stop(deadline=datetime.now(UTC) + timedelta(seconds=2))
    assert report.forced is True
    assert report.descendants_remaining == ()


@pytest.mark.skipif(os.name != "posix", reason="requires POSIX process groups")
async def test_stop_cancellation_finishes_cleanup_before_propagating(tmp_path) -> None:
    code = "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)"
    process = await PosixProcessAdapter(graceful_seconds=0.1).launch(
        _request(tmp_path, code)
    )
    pid = process.identity.pid
    task = asyncio.create_task(
        process.stop(deadline=datetime.now(UTC) + timedelta(seconds=2))
    )
    await asyncio.sleep(0.02)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert pid is not None
    assert not psutil.pid_exists(pid)


@pytest.mark.skipif(os.name != "posix", reason="requires POSIX process groups")
async def test_pid_reuse_or_executable_mismatch_never_signals_unknown_process(
    tmp_path, monkeypatch
) -> None:
    process = await PosixProcessAdapter().launch(
        _request(tmp_path, "import time; time.sleep(60)")
    )
    pid = process.identity.pid
    monkeypatch.setattr(process, "_root_identity_valid", lambda: False)
    report = await process.stop(deadline=datetime.now(UTC) + timedelta(seconds=0.2))
    assert report.degraded_reason and "identity changed" in report.degraded_reason
    assert pid is not None and psutil.pid_exists(pid)

    os.killpg(pid, signal.SIGKILL)
    await process.wait()


@pytest.mark.skipif(os.name != "posix", reason="requires POSIX process groups")
async def test_breakaway_orphan_is_reconciled_by_recorded_creation_identity(tmp_path) -> None:
    child = (
        "import os,time; time.sleep(.15); os.setsid(); time.sleep(60)"
    )
    code = (
        "import subprocess,sys,time; "
        f"subprocess.Popen([sys.executable,'-c',{child!r}]); time.sleep(60)"
    )
    process = await PosixProcessAdapter(descendant_poll_seconds=0.01).launch(
        _request(tmp_path, code)
    )
    await asyncio.sleep(0.3)
    report = await process.stop(deadline=datetime.now(UTC) + timedelta(seconds=2))
    assert report.descendants_remaining == ()


@pytest.mark.skipif(os.name != "posix", reason="requires POSIX process groups")
async def test_owned_listener_is_identified_and_gone_after_stop(tmp_path) -> None:
    code = (
        "import socket,time; s=socket.socket(); s.bind(('127.0.0.1',0)); "
        "s.listen(); print(s.getsockname()[1], flush=True); time.sleep(60)"
    )
    process = await PosixProcessAdapter(descendant_poll_seconds=0.01).launch(
        _request(tmp_path, code)
    )
    await asyncio.sleep(0.15)
    assert process._remaining_listeners()  # noqa: SLF001 - native ownership evidence
    report = await process.stop(deadline=datetime.now(UTC) + timedelta(seconds=2))
    assert report.listeners_remaining == ()
