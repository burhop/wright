"""Workspace-scoped P1S MCP operations for the print demo.

The printer MCP server owns LAN credentials. Wright exposes only a small fixed
read/print surface and verifies the exact workflow-created sliced package.
"""

from __future__ import annotations

import base64
import hashlib
import json
import ipaddress
import os
import re
import socket
import ssl
import struct
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile, BadZipFile

from .workflow_run_record import recent_workflow_runs
from .workspace_path import WorkspacePath


class PrintDemoError(ValueError):
    pass


def _printer_tool(runtime, name: str):
    aliases = {
        "get_printer_status": ("printer_status", "get_printer_status"),
        "print_3mf": ("printer_print", "print_3mf"),
    }
    names = aliases.get(name, (name,))
    matches = [tool for tool in runtime.tools() if tool.tool_name in names]
    preferred_server = os.environ.get(
        "WRIGHT_PRINT_DEMO_PRINTER_SERVER", "bambu-p1s-mcp-marctheshark3"
    )
    preferred = [tool for tool in matches if tool.server_id == preferred_server]
    if preferred:
        matches = preferred
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
            "confirm": True,
        }
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
    evidence = paths.resolve(str(Path(relative).parent / "slice-evidence.json"), must_exist=True)
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
    try:
        with ZipFile(package) as archive:
            if not any(re.fullmatch(r"Metadata/plate_\d+\.gcode", name) for name in archive.namelist()):
                raise PrintDemoError("The 3MF has no sliced plate G-code.")
    except BadZipFile as error:
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
    state = first(value.get("status"), value.get("state"), value.get("gcode_state"), current.get("status"))
    return {
        "status": state if isinstance(state, str) else "unknown",
        "progress": number(current.get("progress"), value.get("progress"), value.get("progress_percent"), value.get("mc_percent")),
        "time_remaining_minutes": number(current.get("timeRemaining"), value.get("remaining_minutes"), value.get("mc_remaining_time")),
        "current_layer": number(current.get("currentLayer"), value.get("current_layer"), value.get("layer"), value.get("layer_num")),
        "total_layers": number(current.get("totalLayers"), value.get("total_layers"), value.get("total_layer_num")),
    }


def reserve_print_dispatch(package: Path, *, run_id: str, digest: str) -> Path:
    receipt = package.parent / "print-dispatch.json"
    payload = {
        "schema_version": 1,
        "run_id": run_id,
        "package_sha256": digest,
        "state": "dispatch_started_outcome_unknown",
        "replay_permitted": False,
    }
    try:
        with receipt.open("x", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2)
    except FileExistsError as error:
        raise PrintDemoError(
            "This package already has a print dispatch attempt. Check the printer before creating another job."
        ) from error
    return receipt


def finish_print_dispatch(receipt: Path, response: dict) -> None:
    # A successful tool response establishes accepted dispatch, not a physical print.
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    payload["state"] = "printer_tool_accepted"
    payload["printer_response"] = {
        key: value for key, value in response.items()
        if key in {"status", "message", "filename", "job_id", "print_id"}
    }
    receipt.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


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
