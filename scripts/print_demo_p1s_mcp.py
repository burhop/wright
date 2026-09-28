"""P1S MCP adapter with explicit single-filament AMS slot mapping.

Uses the pinned bambu-p1s-mcp library for LAN status, FTPS upload, MQTT and
safe error handling. The upstream printer_print tool has no AMS mapping input;
this adapter supplies one for Wright's single-filament sliced packages.
"""

from __future__ import annotations

import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from bambu_p1s_mcp.config import load_settings
from print_demo_p1s_transfer import upload_file
from bambu_p1s_mcp.guard import require_confirm
from bambu_p1s_mcp.payloads import project_file
from bambu_p1s_mcp.printer import get_session
from bambu_p1s_mcp.redact import public_error
from workspace_service.print_part_demo_printer import printer_status_summary


SERVER = FastMCP("wright-print-demo-p1s")
SUPPORTED = {"PLA", "PETG", "ABS", "ASA"}


def _error(error: Exception) -> dict:
    return {"ok": False, "error": public_error(error, load_settings().access_code)}


@SERVER.tool()
def printer_status(fresh: bool = False) -> dict:
    """Read the P1S state and current job; fresh requests full telemetry."""
    try:
        return {"ok": True, **get_session().snapshot(fresh=fresh)}
    except Exception as error:
        return _error(error)


@SERVER.tool()
def printer_ams() -> dict:
    """Read loaded AMS trays, material types and colors."""
    try:
        return {"ok": True, **get_session().ams()}
    except Exception as error:
        return _error(error)


@SERVER.tool()
def printer_stop(expected_job_name: str, confirm: bool = False) -> dict:
    """Stop only the named Wright job. Requires confirm=true."""
    refused = require_confirm(confirm, "stop")
    if refused:
        return {"ok": False, "error": refused}
    try:
        if not re.fullmatch(r"wright_[0-9a-f]{12}\.gcode\.3mf", expected_job_name):
            raise ValueError("A named Wright print is required")
        session = get_session()
        state = session.snapshot(fresh=True)
        reported = {Path(str(state.get(key) or "")).name for key in ("job_name", "gcode_file")}
        if state.get("gcode_state") not in {"RUNNING", "PREPARE", "SLICING", "PAUSE"} or expected_job_name not in reported:
            raise ValueError("The current P1S job does not match this Wright print")
        return {"ok": True, "sent": session.stop_print()}
    except Exception as error:
        return _error(error)


@SERVER.tool()
def printer_print(
    path: str, ams_slot: int, filament_type: str, remote_name: str,
    plate: int = 1, use_ams: bool = True, bed_levelling: bool = True,
    confirm: bool = False,
) -> dict:
    """Upload one sliced 3MF and start it with an explicit AMS slot mapping."""
    refused = require_confirm(confirm, "print")
    if refused:
        return {"ok": False, "error": refused, "phase": "validation", "start_command_sent": False}
    phase = "validation"
    start_command_sent = False
    try:
        if plate != 1 or use_ams is not True or bed_levelling is not True:
            raise ValueError("The demo requires plate 1, AMS and bed leveling")
        if not isinstance(ams_slot, int) or isinstance(ams_slot, bool) or not 0 <= ams_slot <= 103:
            raise ValueError("Select a valid AMS slot")
        if filament_type not in SUPPORTED:
            raise ValueError("Choose a supported filament type")
        if not re.fullmatch(r"wright_[0-9a-f]{12}\.gcode\.3mf", remote_name):
            raise ValueError("The print job name is invalid")
        source = Path(path).resolve()
        if not source.is_file() or not source.name.endswith(".gcode.3mf"):
            raise ValueError("A sliced G-code 3MF is required")
        session = get_session()
        state = session.snapshot(fresh=True)
        if not printer_status_summary(state)["ready"]:
            raise ValueError("The P1S is not ready to accept a print")
        trays = session.ams().get("trays", [])
        selected = [
            tray for tray in trays
            if str(tray.get("ams_id")) != "external"
            and str(tray.get("ams_id", "")).isdigit()
            and str(tray.get("slot", "")).isdigit()
            and int(tray["ams_id"]) * 4 + int(tray["slot"]) == ams_slot
        ]
        if len(selected) != 1 or selected[0].get("empty") or str(selected[0].get("type", "")).upper() != filament_type:
            raise ValueError("The selected AMS slot no longer has the sliced filament type")
        settings = load_settings()
        if settings.model.upper() != "P1S":
            raise ValueError("This demo is configured for a P1S printer only")
        phase = "upload"
        remote = upload_file(settings, str(source), remote_name=remote_name)
        phase = "final_printer_check"
        latest = session.snapshot(fresh=True)
        if not printer_status_summary(latest)["ready"]:
            raise ValueError("The P1S became busy during upload; print was not started")
        latest_trays = session.ams().get("trays", [])
        if not any(
            str(tray.get("ams_id")) != "external"
            and str(tray.get("ams_id", "")).isdigit()
            and str(tray.get("slot", "")).isdigit()
            and int(tray["ams_id"]) * 4 + int(tray["slot"]) == ams_slot
            and not tray.get("empty")
            and str(tray.get("type", "")).upper() == filament_type
            for tray in latest_trays
        ):
            raise ValueError("The selected AMS slot changed during upload; print was not started")
        command = project_file(session.next_seq(), remote, plate=1, use_ams=True, bed_levelling=True)
        command["print"]["ams_mapping"] = [ams_slot]
        command["print"]["ams_mapping2"] = [{"ams_id": ams_slot // 4, "slot_id": ams_slot % 4}]
        phase = "start_command"
        start_command_sent = True  # From here, a transport failure has an uncertain outcome.
        session.publish(command, qos=1)
        return {"ok": True, "status": "submitted", "remote": remote}
    except Exception as error:
        return {**_error(error), "phase": phase, "start_command_sent": start_command_sent}


if __name__ == "__main__":
    SERVER.run(transport="stdio")
