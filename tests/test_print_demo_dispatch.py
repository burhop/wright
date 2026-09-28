import asyncio
import importlib.util
import json
import sys
import types
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from workspace_service.print_part_demo_printer import (
    PrintDemoError, PrintDispatchRejected, PrinterStatusMonitor,
    call_printer, fail_print_dispatch_before_start, printer_status_summary, reserve_print_dispatch,
)


@pytest.mark.parametrize("changes,ready", [
    ({}, True),
    ({"print_error": 1}, False),
    ({"hms": [{"code": 1}]}, False),
    ({"hms": None}, False),
    ({"print_error": None}, False),
    ({"connected": False}, False),
    ({"gcode_state": "RUNNING"}, False),
    ({"gcode_state": "PAUSE"}, False),
    ({"gcode_state": "UNKNOWN"}, False),
])
def test_cancelled_job_requires_explicit_clear_telemetry(changes, ready):
    telemetry = dict(connected=True, gcode_state="FAILED", print_error=0, hms=[])
    assert printer_status_summary({**telemetry, **changes})["ready"] is ready


def test_only_confirmed_failure_before_start_can_retry(tmp_path):
    package = tmp_path / "part.gcode.3mf"
    arguments = dict(run_id="run", digest="digest", ams_slot=0, remote_name="wright_part.gcode.3mf")
    receipt = reserve_print_dispatch(package, **arguments)
    with pytest.raises(PrintDemoError):
        reserve_print_dispatch(package, **arguments)
    fail_print_dispatch_before_start(receipt, PrintDispatchRejected("Upload timed out before start"))

    def retry():
        try:
            reserve_print_dispatch(package, **arguments)
            return True
        except PrintDemoError:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: retry(), range(2))) == [False, True]
    archives = list(tmp_path.glob("print-dispatch-attempt-*.json"))
    assert len(archives) == 1
    assert json.loads(archives[0].read_text())["error"] == "Upload timed out before start"
    assert json.loads(receipt.read_text())["replay_permitted"] is False


@pytest.mark.parametrize("phase,sent,retryable", [
    ("upload", False, True),
    ("final_printer_check", False, True),
    ("start_command", True, False),
    ("unknown", False, False),
])
def test_uncertain_dispatch_errors_do_not_authorize_replay(phase, sent, retryable):
    async def call(*args, **kwargs):
        return types.SimpleNamespace(is_error=False, structured_content={
            "ok": False, "error": "TimeoutError: timed out", "phase": phase,
            "start_command_sent": sent,
        })
    tool = types.SimpleNamespace(server_id="bambu-p1s-mcp-marctheshark3", tool_name="printer_print", name="p1s_print")
    runtime = types.SimpleNamespace(session_id="session", tools=lambda: [tool], gateway=types.SimpleNamespace(
        call_tool=call, workspace_approvals_for_model_call=lambda *args: set(),
    ))
    with pytest.raises(PrintDemoError) as error:
        asyncio.run(call_printer(runtime, "print_3mf", {
            "three_mf_path": "part.gcode.3mf", "ams_slot": 0,
            "filament_type": "PLA", "remote_name": "part.gcode.3mf",
        }))
    assert isinstance(error.value, PrintDispatchRejected) is retryable


def test_polling_is_coalesced_and_fresh_bypasses_cache():
    async def scenario():
        monitor = PrinterStatusMonitor()
        calls = []
        started = asyncio.Event()
        release = asyncio.Event()

        async def load():
            calls.append(1)
            started.set()
            await release.wait()
            return {"ready": True}

        first = asyncio.create_task(monitor.get("workspace", load))
        await started.wait()
        second = asyncio.create_task(monitor.get("workspace", load))
        await asyncio.sleep(0)
        first.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first
        release.set()
        assert await second == {"ready": True}
        assert await monitor.get("workspace", load) == {"ready": True}
        assert len(calls) == 1
        await monitor.get("workspace", load, fresh=True)
        assert len(calls) == 2
    asyncio.run(scenario())


@pytest.mark.parametrize("stored_size,completion_error", [(148, None), (100, None), (148, TimeoutError("completion missing"))])
def test_p1s_upload_closes_data_and_requires_completion_and_size(monkeypatch, tmp_path, stored_size, completion_error):
    events = []

    class Data:
        def __enter__(self):
            return self
        def sendall(self, block):
            events.append(("bytes", len(block)))
        def unwrap(self):
            pytest.fail("P1S upload must not wait for SSL unwrap")
        def __exit__(self, *args):
            events.append("data_closed")

    class Ftp:
        def voidcmd(self, command):
            assert command == "TYPE I"
        def transfercmd(self, command):
            assert command == "STOR part.gcode.3mf"
            return Data()
        def voidresp(self):
            assert events[-1] == "data_closed"
            events.append("completion")
            if completion_error:
                raise completion_error
            return "226 Complete"
        def size(self, name):
            assert events[-1] == "completion"
            return stored_size
        def close(self):
            events.append("control_closed")

    ftp_module = types.ModuleType("bambu_p1s_mcp.ftp")
    ftp_module._connect = lambda settings: Ftp()
    monkeypatch.setitem(sys.modules, "bambu_p1s_mcp", types.ModuleType("bambu_p1s_mcp"))
    monkeypatch.setitem(sys.modules, "bambu_p1s_mcp.ftp", ftp_module)
    script = Path(__file__).parents[1] / "scripts/print_demo_p1s_transfer.py"
    spec = importlib.util.spec_from_file_location("p1s_transfer_under_test", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = tmp_path / "part.gcode.3mf"
    source.write_bytes(b"x" * 148)
    if stored_size != 148 or completion_error:
        with pytest.raises(OSError):
            module.upload_file(None, str(source), source.name)
    else:
        assert module.upload_file(None, str(source), source.name) == source.name
    assert events[-1] == "control_closed"
