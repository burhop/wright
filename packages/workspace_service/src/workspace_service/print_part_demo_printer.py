"""Workspace-scoped P1S MCP operations for the print demo.

The printer MCP server owns LAN credentials. Wright exposes only a small fixed
read/print surface and verifies the exact workflow-created sliced package.
"""

from __future__ import annotations

import base64
import asyncio
import hashlib
import json
import ipaddress
import os
import re
import socket
import ssl
import struct
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
from zipfile import ZipFile, BadZipFile
from data_vault.lifecycle_lock import lifecycle_lock

from .workflow_run_record import recent_workflow_runs
from .workspace_path import WorkspacePath


class PrintDemoError(ValueError):
    pass


class PrintDispatchRejected(PrintDemoError):
    """The trusted adapter confirms failure before any start command was sent."""


class PrinterStatusMonitor:
    """Share bounded read polling between tabs; dispatch still checks fresh state."""

    def __init__(self):
        self._cache = {}
        self._pending = {}

    async def get(self, key, load, *, fresh=False):
        pending = self._pending.get(key)
        if pending is not None:
            task, requested_fresh = pending
            value = await asyncio.shield(task)
            if fresh and not requested_fresh:
                return await self.get(key, load, fresh=True)
            return value
        cached = self._cache.get(key)
        if not fresh and cached is not None and time.monotonic() - cached[0] < 5:
            return cached[1]

        async def read():
            try:
                value = await load()
                self._cache[key] = (time.monotonic(), value)
                return value
            except Exception:
                self._cache.pop(key, None)
                raise
            finally:
                self._pending.pop(key, None)

        task = asyncio.create_task(read())
        self._pending[key] = (task, fresh)
        return await asyncio.shield(task)


def _printer_tool(runtime, name: str):
    aliases = {
        "get_printer_status": ("printer_status", "get_printer_status"),
        "print_3mf": ("printer_print", "print_3mf"),
        "get_printer_ams": ("printer_ams",),
        "stop_print": ("printer_stop",),
    }
    names = aliases.get(name, (name,))
    preferred_server = os.environ.get(
        "WRIGHT_PRINT_DEMO_PRINTER_SERVER", "bambu-p1s-mcp-marctheshark3"
    )
    matches = [
        tool for tool in runtime.tools()
        if tool.server_id == preferred_server and tool.tool_name in names
    ]
    if len(matches) != 1:
        raise PrintDemoError(
            f"Enable one P1S printer MCP server with the {name} tool in this workspace."
        )
    return matches[0]


async def call_printer(runtime, name: str, arguments: dict | None = None) -> dict:
    tool = _printer_tool(runtime, name)
    if tool.server_id == "wright":
        raise PrintDemoError("A printer MCP server is required.")
    if tool.tool_name == "printer_status":
        arguments = {"fresh": bool((arguments or {}).get("fresh", False))}
    if tool.tool_name == "printer_print":
        arguments = {
            "path": arguments["three_mf_path"], "plate": 1,
            "use_ams": True, "bed_levelling": True,
            "ams_slot": arguments["ams_slot"],
            "filament_type": arguments["filament_type"],
            "remote_name": arguments["remote_name"],
            "confirm": True,
        }
    if tool.tool_name == "printer_stop":
        arguments = {"expected_job_name": arguments["expected_job_name"], "confirm": True}
    try:
        result = await runtime.gateway.call_tool(
            runtime.session_id, uuid4().hex, tool.name,
            arguments or {},
            workspace_approvals=runtime.gateway.workspace_approvals_for_model_call(
                runtime.session_id, tool.name
            ),
            timeout=120 if name == "print_3mf" else 20,
        )
    except Exception as error:
        raise PrintDemoError(
            f"The {name} printer MCP call failed. Check the server and P1S LAN connection."
        ) from error
    value = result.structured_content
    if value is None:
        texts = [
            item.get("text", "") for item in result.content
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        try:
            value = json.loads("\n".join(texts))
        except (ValueError, TypeError):
            value = {"message": "\n".join(texts)[:1000]}
    if result.is_error:
        raise PrintDemoError(f"The {name} printer MCP tool reported an error.")
    if not isinstance(value, dict):
        raise PrintDemoError(f"The {name} printer MCP tool returned an invalid result.")
    if value.get("ok") is False:
        detail = value.get("error")
        if isinstance(detail, str) and 0 < len(detail) <= 300 and tool.server_id == "bambu-p1s-mcp-marctheshark3":
            if name == "print_3mf" and value.get("start_command_sent") is False and value.get("phase") in {"validation", "upload", "final_printer_check"}:
                phase = str(value["phase"]).replace("_", " ")
                raise PrintDispatchRejected(f"P1S {phase} failed: {detail}. No print was started; you can retry.")
            raise PrintDemoError(f"The P1S printer MCP reported: {detail}")
        raise PrintDemoError(f"The {name} printer MCP tool reported failure. Check its LAN connection and server log.")
    if name == "get_printer_status" and value.get("connected") is False:
        raise PrintDemoError("The printer MCP server is not connected to the P1S.")
    if name == "print_3mf":
        accepted = value.get("ok") is True or str(value.get("status", "")).lower() in {
            "started", "printing", "success", "submitted", "accepted"
        }
        if not accepted:
            raise PrintDemoError(
                "The printer MCP tool did not positively confirm print dispatch. Check the printer before another attempt."
            )
    return value


SUPPORTED_FILAMENTS = {"PLA", "PETG", "ABS", "ASA"}


def sliced_filament_type(facts: dict) -> str:
    filament = facts.get("filament")
    name = filament.get("name") if isinstance(filament, dict) else None
    if not isinstance(name, str) or not name.startswith("Generic "):
        raise PrintDemoError("The slice does not identify a supported generic filament.")
    material = name.removeprefix("Generic ").upper()
    if material not in SUPPORTED_FILAMENTS:
        raise PrintDemoError("The sliced filament is not supported by this P1S demo.")
    return material


def printer_ams_summary(value: dict) -> dict:
    """Expose only loaded AMS slots with stable absolute slot IDs."""
    if isinstance(value.get("result"), dict) and "trays" not in value:
        value = value["result"]
    trays = value.get("trays")
    if not isinstance(trays, list):
        raise PrintDemoError("The P1S did not report its AMS slots.")
    result = []
    for tray in trays:
        if not isinstance(tray, dict) or str(tray.get("ams_id")) == "external":
            continue
        try:
            unit = int(tray.get("ams_id"))
            position = int(tray.get("slot"))
        except (TypeError, ValueError):
            continue
        if not 0 <= unit <= 25 or not 0 <= position <= 3:
            continue
        raw_type = tray.get("type")
        material = raw_type.strip().upper() if isinstance(raw_type, str) else ""
        color = tray.get("color")
        result.append({
            "slot": unit * 4 + position,
            "label": f"AMS {unit + 1} · slot {position + 1}",
            "type": material or None,
            "color": color if isinstance(color, str) and re.fullmatch(r"[0-9A-Fa-f]{6,8}", color) else None,
            "empty": bool(tray.get("empty", not material)),
            "supported": material in SUPPORTED_FILAMENTS,
        })
    return {"trays": sorted(result, key=lambda tray: tray["slot"])}


def require_ams_slot(ams: dict, slot: int, material: str) -> dict:
    if material not in SUPPORTED_FILAMENTS or not isinstance(slot, int) or isinstance(slot, bool):
        raise PrintDemoError("Select a supported filament and AMS slot.")
    matches = [tray for tray in ams.get("trays", []) if tray.get("slot") == slot]
    if len(matches) != 1 or matches[0]["empty"]:
        raise PrintDemoError("The selected AMS slot is empty or no longer reported. Refresh printer status.")
    if matches[0]["type"] != material:
        raise PrintDemoError(f"The selected AMS slot no longer contains {material}. Create a matching slice or choose another slot.")
    return matches[0]


def current_package(
    workspace_dir: str, workflow_path: str, run_id: str, expected_sha256: str
) -> tuple[Path, str, dict]:
    if not re.fullmatch(r"workflows/prompt-to-print-[0-9a-f]{12}\.workflow\.wflow", workflow_path):
        raise PrintDemoError("Choose a saved print-demo workflow.")
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise PrintDemoError("The selected package digest is invalid.")
    runs = recent_workflow_runs(workspace_dir, workflow_path, latest_only=True)
    if len(runs) != 1 or runs[0].get("status") != "completed":
        raise PrintDemoError("The latest workflow run has not completed successfully.")
    run = runs[0]
    if run.get("run_id") != run_id or not run.get("source_matches_current"):
        raise PrintDemoError("The reviewed run is no longer current. Generate a fresh package.")
    representations = [
        rep for item in run.get("results", [])
        if isinstance(item, dict)
        for rep in item.get("representations", [])
        if isinstance(rep, dict)
        and rep.get("kind") == "workspace_file"
        and str(rep.get("location", "")).endswith("slice_package.gcode.3mf")
    ]
    if len(representations) != 1:
        raise PrintDemoError("The run did not publish one sliced 3MF package.")
    rep = representations[0]
    relative = rep["location"]
    paths = WorkspacePath(workspace_dir)
    package = paths.resolve(relative, must_exist=True)
    if not 1000 <= package.stat().st_size <= 500 * 1024 * 1024:
        raise PrintDemoError("The sliced 3MF package has an invalid size.")
    with package.open("rb") as stream:
        package_hash = hashlib.file_digest(stream, "sha256").hexdigest()
    if package_hash != expected_sha256 or rep.get("sha256") != expected_sha256:
        raise PrintDemoError("The sliced package changed after the workflow run.")
    previews = [
        rep for item in run.get("results", [])
        if isinstance(item, dict)
        for rep in item.get("representations", [])
        if isinstance(rep, dict)
        and rep.get("kind") == "workspace_file"
        and str(rep.get("location", "")).endswith("support-preview.svg")
    ]
    if len(previews) != 1 or not isinstance(previews[0].get("sha256"), str):
        raise PrintDemoError("The run did not publish one support preview.")
    with paths.resolve(previews[0]["location"], must_exist=True).open("rb") as stream:
        preview_hash = hashlib.file_digest(stream, "sha256").hexdigest()
    if preview_hash != previews[0]["sha256"]:
        raise PrintDemoError("The support preview changed after the workflow run.")
    evidence_representations = [
        rep for item in run.get("results", [])
        if isinstance(item, dict)
        for rep in item.get("representations", [])
        if isinstance(rep, dict)
        and rep.get("kind") == "workspace_file"
        and str(rep.get("location", "")).endswith("slice-evidence.json")
    ]
    if len(evidence_representations) != 1 or not isinstance(evidence_representations[0].get("sha256"), str):
        raise PrintDemoError("The run did not publish one slice evidence file.")
    evidence_relative = str(Path(relative).parent / "slice-evidence.json").replace("\\", "/")
    if evidence_representations[0].get("location") != evidence_relative:
        raise PrintDemoError("The slice evidence does not belong to this package.")
    evidence = paths.resolve(evidence_relative, must_exist=True)
    with evidence.open("rb") as stream:
        evidence_hash = hashlib.file_digest(stream, "sha256").hexdigest()
    if evidence_hash != evidence_representations[0]["sha256"]:
        raise PrintDemoError("The slice evidence changed after the workflow run.")
    facts = json.loads(evidence.read_text(encoding="utf-8"))
    if (
        facts.get("operation") != "actual_local_bambu_slice"
        or facts.get("simulation") is not False
        or facts.get("exit_code") != 0
        or facts.get("package_sha256") != expected_sha256
        or facts.get("supports_enabled") is not True
        or not isinstance(facts.get("extrusion_moves"), int)
        or facts["extrusion_moves"] <= 0
    ):
        raise PrintDemoError("The current Bambu slice evidence is incomplete.")
    material = sliced_filament_type(facts)
    try:
        with ZipFile(package) as archive:
            if "Metadata/plate_1.gcode" not in archive.namelist():
                raise PrintDemoError("The 3MF has no sliced plate 1 G-code.")
            slice_info = ET.fromstring(archive.read("Metadata/slice_info.config"))
            filaments = slice_info.findall(".//filament")
            if len(filaments) != 1 or filaments[0].get("type", "").upper() != material:
                raise PrintDemoError("The package filament does not match its slice evidence.")
    except (BadZipFile, KeyError, ET.ParseError) as error:
        raise PrintDemoError("The 3MF package is invalid.") from error
    return package, relative, facts


def printer_status_summary(value: dict) -> dict:
    """Project the two supported printer MCP response shapes to UI fields."""
    if isinstance(value.get("result"), dict) and not any(
        key in value for key in ("status", "state", "print", "progress")
    ):
        value = value["result"]
    current = value.get("print") if isinstance(value.get("print"), dict) else {}
    def first(*items):
        return next((item for item in items if item is not None), None)
    def number(*items):
        item = first(*items)
        return item if isinstance(item, (int, float)) and not isinstance(item, bool) else None
    state = first(value.get("gcode_state"), value.get("status"), value.get("state"), current.get("status"))
    state = state.strip().upper() if isinstance(state, str) else "UNKNOWN"
    connected = value.get("connected") is True
    fault = number(value.get("print_error"), current.get("print_error"))
    # P1S keeps FAILED after cancellation. Bambu Studio treats that as a
    # finished job, not an active print. Require explicit clear error telemetry
    # before accepting that terminal state; unknown/error states stay blocked.
    hms = first(value.get("hms"), current.get("hms"))
    cancelled_or_finished = state == "FAILED" and fault == 0 and hms == []
    stale = value.get("telemetry_stale") is True
    ready = connected and not stale and fault in (None, 0) and not hms and (
        state in {"IDLE", "FINISH"} or cancelled_or_finished
    )
    reason = (
        "Printer is ready. The previous job has ended." if ready and state == "FAILED" else
        "Printer is ready." if ready else
        "Printer connection is unavailable." if not connected else
        "Printer telemetry is out of date. Waiting for a fresh report." if stale else
        "Printer reported an error." if fault not in (None, 0) else
        "Printer reports a diagnostic alert; check the details below." if hms else
        "Printer needs attention before another job." if state == "FAILED" else
        "Printer is busy with another job." if state in {"RUNNING", "PREPARE", "SLICING", "PAUSE"} else
        "Printer state is unknown; refresh before printing."
    )
    return {
        "status": state,
        "connected": connected,
        "ready": ready,
        "readiness_reason": reason,
        "telemetry_at": value.get("telemetry_at"),
        "telemetry_age_seconds": number(value.get("telemetry_age_seconds")),
        "telemetry_stale": stale,
        "print_error": fault,
        "hms": hms if isinstance(hms, list) else [],
        "stage": number(value.get("stage")),
        "nozzle_c": number(value.get("nozzle_c")),
        "nozzle_target_c": number(value.get("nozzle_target_c")),
        "bed_c": number(value.get("bed_c")),
        "bed_target_c": number(value.get("bed_target_c")),
        "job_name": first(value.get("job_name"), current.get("job_name")),
        "gcode_file": first(value.get("gcode_file"), current.get("gcode_file")),
        "progress": number(current.get("progress"), value.get("progress"), value.get("progress_percent"), value.get("mc_percent")),
        "time_remaining_minutes": number(current.get("timeRemaining"), value.get("remaining_minutes"), value.get("mc_remaining_time")),
        "current_layer": number(current.get("currentLayer"), value.get("current_layer"), value.get("layer"), value.get("layer_num")),
        "total_layers": number(current.get("totalLayers"), value.get("total_layers"), value.get("total_layer_num")),
    }


def reserve_print_dispatch(package: Path, *, run_id: str, digest: str, ams_slot: int, remote_name: str) -> Path:
    receipt = package.parent / "print-dispatch.json"
    payload = {
        "schema_version": 1,
        "run_id": run_id,
        "package_sha256": digest,
        "ams_slot": ams_slot,
        "remote_name": remote_name,
        "state": "dispatch_started_outcome_unknown",
        "replay_permitted": False,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
    with lifecycle_lock(receipt):
        if receipt.exists():
            previous = current_dispatch(package, run_id=run_id, digest=digest)
            if previous.get("state") not in {"dispatch_failed_before_start", "retry_authorized_by_user"} or previous.get("replay_permitted") is not True:
                raise PrintDemoError(
                    "This package already has a print dispatch attempt. Check the printer before creating another job."
                )
            receipt.rename(receipt.with_name(f"print-dispatch-attempt-{uuid4().hex}.json"))
        with receipt.open("x", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2)
    return receipt


def fail_print_dispatch_before_start(receipt: Path, error: PrintDispatchRejected) -> None:
    with lifecycle_lock(receipt):
        payload = json.loads(receipt.read_text(encoding="utf-8"))
        payload.update(state="dispatch_failed_before_start", replay_permitted=True, error=str(error))
        temporary = receipt.with_name(f".print-dispatch-{uuid4().hex}.json")
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temporary.replace(receipt)


def finish_print_dispatch(receipt: Path, response: dict) -> str:
    # MQTT delivery, printer acknowledgment and observed printing are distinct.
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    payload["state"] = (
        "printer_rejected" if response.get("status") == "rejected" else
        "printer_acknowledged" if response.get("status") == "accepted" else
        "command_sent_awaiting_confirmation"
    )
    payload["printer_response"] = {
        key: value for key, value in response.items()
        if key in {"status", "message", "filename", "job_id", "print_id", "remote", "command_response"}
    }
    receipt.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload["state"]


def current_dispatch(package: Path, *, run_id: str, digest: str) -> dict | None:
    receipt = package.parent / "print-dispatch.json"
    if not receipt.is_file():
        return None
    try:
        value = json.loads(receipt.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise PrintDemoError("The print dispatch record is invalid.") from error
    if value.get("run_id") != run_id or value.get("package_sha256") != digest:
        raise PrintDemoError("The print dispatch record does not match this package.")
    return value


def authorize_print_retry(package: Path, *, run_id: str, digest: str, status: dict) -> None:
    """Record an explicit operator check; retain uncertainty in the prior receipt."""
    receipt = package.parent / "print-dispatch.json"
    with lifecycle_lock(receipt):
        dispatch = current_dispatch(package, run_id=run_id, digest=digest)
        if not dispatch or dispatch.get("state") not in {
            "dispatch_started_outcome_unknown", "printer_tool_accepted",
            "command_sent_awaiting_confirmation", "printer_acknowledged", "printer_rejected",
        }:
            raise PrintDemoError("This attempt is not awaiting a checked retry.")
        if time.time() - receipt.stat().st_mtime < 60:
            raise PrintDemoError("Allow at least one minute for the printer to respond before checking a retry.")
        if not status.get("ready") or status.get("telemetry_stale") or job_matches_dispatch(status, dispatch):
            raise PrintDemoError("The printer must be freshly idle with no matching Wright job before retrying.")
        # Preserve the original outcome; an operator check is not evidence that
        # the earlier command failed before transmission.
        dispatch["previous_attempt"] = {key: dispatch.get(key) for key in ("state", "printer_response", "submitted_at")}
        dispatch.update(state="retry_authorized_by_user", replay_permitted=True,
                        operator_checked_at=datetime.now(timezone.utc).isoformat())
        temporary = receipt.with_name(f".print-dispatch-{uuid4().hex}.json")
        temporary.write_text(json.dumps(dispatch, indent=2) + "\n", encoding="utf-8")
        temporary.replace(receipt)


def job_matches_dispatch(status: dict, dispatch: dict) -> bool:
    expected = dispatch.get("remote_name")
    if not isinstance(expected, str) or not re.fullmatch(r"wright_[0-9a-f]{12}\.gcode\.3mf", expected):
        return False
    return any(
        isinstance(name, str) and Path(name).name == expected
        for name in (status.get("job_name"), status.get("gcode_file"))
    )


def jpeg_frame(value: dict) -> bytes:
    encoded = value.get("base64")
    if not isinstance(encoded, str) or len(encoded) > 8 * 1024 * 1024:
        raise PrintDemoError("The camera MCP tool did not return a JPEG frame.")
    try:
        data = base64.b64decode(encoded, validate=True)
    except ValueError as error:
        raise PrintDemoError("The camera frame is invalid.") from error
    if len(data) < 100 or not data.startswith(b"\xff\xd8") or not data.endswith(b"\xff\xd9"):
        raise PrintDemoError("The camera MCP tool did not return a valid JPEG.")
    return data


def p1s_camera_config() -> tuple[str, str] | None:
    """Use API-host or local MCP credentials; never send them to the browser."""
    host = os.environ.get("WRIGHT_P1S_IP", "").strip()
    code = os.environ.get("WRIGHT_P1S_ACCESS_CODE", "").strip()
    if bool(host) != bool(code):
        raise PrintDemoError("Set both P1S camera LAN settings, or use the saved printer MCP credentials.")
    if not host:
        from tool_registry.secrets import read_secrets

        try:
            saved = read_secrets(os.environ.get(
                "WRIGHT_PRINT_DEMO_PRINTER_SERVER", "bambu-p1s-mcp-marctheshark3"
            ))
        except RuntimeError:
            return None
        if saved.get("BAMBU_MODEL", "").upper() != "P1S" or not saved.get("BAMBU_SERIAL"):
            return None
        host = saved.get("BAMBU_IP", "").strip()
        code = saved.get("BAMBU_ACCESS_CODE", "").strip()
        if not host or not code:
            return None
    try:
        address = ipaddress.ip_address(host)
        if address.version != 4 or not address.is_private:
            raise ValueError("P1S camera IP must be a private IPv4 address.")
        encoded = code.encode("ascii")
        if not 1 <= len(encoded) <= 32:
            raise ValueError("P1S LAN access code must be 1–32 ASCII bytes.")
    except (ValueError, UnicodeError) as error:
        raise PrintDemoError("The API host has invalid P1S camera LAN settings.") from error
    return host, code


def p1s_camera_frames(host: str, code: str):
    """Read P1S port-6000 TLS JPEG frames and yield browser MJPEG chunks."""
    context = ssl._create_unverified_context()  # P1S presents a local self-signed certificate.
    with socket.create_connection((host, 6000), timeout=10) as raw:
        with context.wrap_socket(raw, server_hostname=host) as stream:
            stream.settimeout(15)
            authentication = (
                struct.pack("<IIII", 0x40, 0x3000, 0, 0)
                + b"bblp".ljust(32, b"\x00")
                + code.encode("ascii").ljust(32, b"\x00")
            )
            stream.sendall(authentication)
            while True:
                header = _recv_exact(stream, 16)
                length, _track, flags, _reserved = struct.unpack("<IIII", header)
                if not 100 <= length <= 8 * 1024 * 1024 or flags != 1:
                    raise PrintDemoError("The P1S camera sent an invalid frame header.")
                frame = _recv_exact(stream, length)
                if not frame.startswith(b"\xff\xd8") or not frame.endswith(b"\xff\xd9"):
                    raise PrintDemoError("The P1S camera sent an invalid JPEG frame.")
                yield (
                    b"--wright-frame\r\nContent-Type: image/jpeg\r\nContent-Length: "
                    + str(len(frame)).encode() + b"\r\n\r\n" + frame + b"\r\n"
                )


def _recv_exact(stream, length: int) -> bytes:
    parts = bytearray()
    while len(parts) < length:
        chunk = stream.recv(length - len(parts))
        if not chunk:
            raise PrintDemoError("The P1S camera connection closed.")
        parts.extend(chunk)
    return bytes(parts)
