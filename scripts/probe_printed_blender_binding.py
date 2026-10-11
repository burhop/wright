"""Probe guarded owned-Blender geometry and an independent offline slicer.

This is a diagnostic only. It creates a generic disposable mesh, never uses a
dataset recipe, never dispatches a workflow, and never contacts a printer.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.util
import json
import socket
import struct
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

from core.native_application import utc_now
from data_vault.migrations import upgrade_database
from data_vault.native_application_repository import NativeApplicationRepository
from tool_registry.native_application_blender import (
    BlenderNativeApplicationAdapter,
    process_identity,
)
from tool_registry.native_application_lifecycle import NativeApplicationLifecycle
from tool_registry.runners.stdio import StdioRunner


ROOT = Path(__file__).resolve().parents[1]
BLENDER_SERVER_REVISION = "5f8ddaf6e987c4aa0c3467fcc548838b28f64477"


def external_slice_definition(path):
    """Resolve explicit qualification inputs before creating any native owner."""
    raw = Path(path).read_bytes()
    if len(raw) > 65536:
        raise ValueError("Diagnostic provider definition exceeds its bound")
    value = json.loads(raw)
    if value.get("schema_version") != 1 or value.get("offline_only") is not True:
        raise ValueError("Select an explicit independently configured offline diagnostic provider")
    command = value.get("command")
    if not isinstance(command, list) or not command or any(not isinstance(item, str) or not item for item in command):
        raise ValueError("Declare the independent provider's installed command as an argument array")
    if any("engineering_dataset_slice" in item or "engineering_jig_slice_mcp" in item for item in command):
        raise ValueError("Embedded slicing implementations are retired")
    for field in ("tool", "input_schema_sha256", "success_field", "success_contract", "gcode_entry"):
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise ValueError("Declare the qualified diagnostic provider's " + field)
    for field in ("arguments", "expected_response_fields"):
        arguments = value.get(field)
        if not isinstance(arguments, dict) or "{source}" not in arguments.values() or "{package}" not in arguments.values():
            raise ValueError("Bind the actual diagnostic geometry and package paths")
        if any(isinstance(item, str) and item not in {"{source}", "{package}"}
               and ("{source}" in item or "{package}" in item) for item in arguments.values()):
            raise ValueError("Use complete diagnostic path placeholders")
    if not isinstance(value.get("env", {}), dict) or any(not isinstance(key, str) or not isinstance(item, str)
                                                        for key, item in value.get("env", {}).items()):
        raise ValueError("Diagnostic provider environment must contain explicit string values")
    profiles = value.get("profiles")
    if not isinstance(profiles, dict) or set(profiles) != {"machine", "process", "filament"}:
        raise ValueError("Pin the three actual configured diagnostic profiles")
    retained = {}
    for role, reference in profiles.items():
        source = Path(reference["path"])
        if not source.is_file() or not 0 < source.stat().st_size <= 1024 * 1024:
            raise ValueError("Diagnostic profile must be a bounded regular file")
        data = source.read_bytes()
        if hashlib.sha256(data).hexdigest() != reference["sha256"]:
            raise ValueError("Diagnostic configured profile changed: " + role)
        if not isinstance(json.loads(data), dict):
            raise ValueError("Diagnostic profile must be a JSON object")
        retained[role] = data
    return value, retained, hashlib.sha256(raw).hexdigest()


async def external_slice_probe(definition, workspace, runner_factory=StdioRunner):
    """One tool call; passive readback never retries an uncertain slice."""
    value, profiles, definition_digest = definition
    source = workspace / "diagnostic/artifacts/repaired_mesh.stl"
    package = workspace / "diagnostic/artifacts/slice_package.gcode.3mf"
    response_path = workspace / "diagnostic/artifacts/slice-provider-response.json"
    attempt_path = workspace / "diagnostic/artifacts/external-slice-attempt.json"
    if not source.is_file() or not 0 < source.stat().st_size <= 32 * 1024 * 1024:
        raise ValueError("The bounded actual diagnostic geometry is required")
    if any(path.exists() for path in (package, response_path, attempt_path)):
        raise ValueError("Preserve the existing diagnostic slice attempt; do not replay")
    substitutions = {"{source}": str(source), "{package}": str(package)}

    def arguments(field):
        return {key: substitutions.get(item, item) if isinstance(item, str) else item
                for key, item in value[field].items()}

    runner = runner_factory(value["command"], env=value.get("env"), cwd=value.get("cwd"), operation_timeout=600)
    attempt = {"definition_sha256": definition_digest, "source_sha256": sha(source),
               "state": "not_called", "engineering_acceptance": False}
    with attempt_path.open("x", encoding="utf-8") as stream:
        json.dump(attempt, stream)
    try:
        await runner.start()
        selected = [tool for tool in await runner.list_tools() if tool["name"] == value["tool"]]
        if len(selected) != 1 or hashlib.sha256(json.dumps(selected[0]["inputSchema"], sort_keys=True, separators=(",", ":")).encode()).hexdigest() != value["input_schema_sha256"]:
            raise ValueError("Diagnostic provider schema is missing, ambiguous or changed")
        attempt["state"] = "outcome_unknown"
        write_json(attempt_path, attempt)
        sliced = await runner.call_tool(value["tool"], arguments("arguments"))
        attempt["state"] = "response_received"
        write_json(attempt_path, attempt)
    finally:
        await runner.stop()
    with response_path.open("x", encoding="utf-8") as stream:
        json.dump(sliced, stream, ensure_ascii=False)
    input_paths = {}
    for role, data in profiles.items():
        relative = "diagnostic/inputs/" + role + "-profile.json"
        with (workspace / relative).open("xb") as stream:
            stream.write(data)
        input_paths[role] = relative
    config = {"workspace_root": str(workspace), "source_mesh": "diagnostic/artifacts/repaired_mesh.stl",
              "slice_package": "diagnostic/artifacts/slice_package.gcode.3mf",
              "provider_response": "diagnostic/artifacts/slice-provider-response.json",
              "output_root": "diagnostic/artifacts", "profiles": input_paths,
              "gcode_entry": value["gcode_entry"], "success_field": value["success_field"],
              "success_contract": value["success_contract"], "expected_response_fields": arguments("expected_response_fields"),
              "operation_label": "independent_offline_slice_diagnostic", "legacy_previews": True,
              "nominal_layer_section": value.get("nominal_layer_section")}
    spec = importlib.util.spec_from_file_location("diagnostic_package_inspection", ROOT / "scripts/engineering/inspect_manufacturing_package.py")
    inspector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inspector)
    from workspace_service.process_interfaces.representations import read_3mf_toolpaths

    observed = inspector.run(config, read_3mf_toolpaths)
    return {"definition_sha256": definition_digest, "inspection": observed,
            "package_sha256": sha(package), "response_sha256": sha(response_path),
            "engineering_acceptance": False, "protocol_scope": "direct MCP diagnostic; not fresh production-gateway qualification"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def response_text(result: dict) -> str:
    return "\n".join(
        str(item.get("text", ""))
        for item in result.get("content", [])
        if item.get("type") == "text"
    )


def stl_bounds(path: Path) -> dict:
    data = path.read_bytes()
    vertices = []
    if len(data) >= 84 and 84 + struct.unpack_from("<I", data, 80)[0] * 50 == len(data):
        triangles = struct.unpack_from("<I", data, 80)[0]
        for index in range(triangles):
            offset = 84 + index * 50 + 12
            vertices.extend(struct.unpack_from("<fff", data, offset + vertex * 12) for vertex in range(3))
    else:
        for line in data.decode("ascii", errors="strict").splitlines():
            fields = line.strip().split()
            if len(fields) == 4 and fields[0] == "vertex":
                vertices.append(tuple(float(value) for value in fields[1:]))
        triangles = len(vertices) // 3
    if not vertices or triangles < 12:
        raise ValueError("Blender did not emit a bounded triangulated STL")
    lower = [min(vertex[index] for vertex in vertices) for index in range(3)]
    upper = [max(vertex[index] for vertex in vertices) for index in range(3)]
    return {
        "triangles": triangles,
        "bounds_min_mm": lower,
        "bounds_max_mm": upper,
        "dimensions_mm": [upper[index] - lower[index] for index in range(3)],
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def guarded_mesh_code(source_stl: Path, repaired_stl: Path) -> str:
    """Return the generic diagnostic mesh code sent through the pinned guard."""

    return "\n".join(
        [
            "import bpy",
            "bpy.ops.object.select_all(action='DESELECT')",
            "bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=10.0, depth=10.0, location=(0.0, 0.0, 5.0))",
            "part = bpy.context.active_object",
            "part.name = 'wright_generic_print_seam_mesh'",
            "bevel = part.modifiers.new(name='edge_radius', type='BEVEL')",
            "bevel.width = 1.0",
            "bevel.segments = 3",
            "bpy.context.view_layer.objects.active = part",
            "part.select_set(True)",
            "bpy.ops.object.modifier_apply(modifier=bevel.name)",
            f"bpy.ops.wm.stl_export(filepath={json.dumps(str(source_stl))}, export_selected_objects=True)",
            f"bpy.ops.wm.stl_export(filepath={json.dumps(str(repaired_stl))}, export_selected_objects=True)",
            "print('WRIGHT_GUARDED_MESH_EXPORTED')",
        ]
    )


async def run(args) -> dict:
    external_definition = external_slice_definition(args.slicer_provider)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    workspace = output / "workspace"
    inputs = workspace / "diagnostic" / "inputs"
    artifacts = workspace / "diagnostic" / "artifacts"
    inputs.mkdir(parents=True)
    artifacts.mkdir()
    port = free_loopback_port()
    blender_source = args.blender_server_source.resolve()
    addon_source = args.addon_source.resolve()
    safe_mode_source = blender_source / "src" / "blender_mcp" / "safe_mode.py"
    if not safe_mode_source.is_file() or not addon_source.is_file():
        raise ValueError("Pinned Blender MCP server/add-on source is incomplete")
    revision = subprocess.run(
        ["git", "-C", str(blender_source), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if revision != BLENDER_SERVER_REVISION:
        raise ValueError("Blender MCP source revision changed")
    result = {
        "kind": "printed-binding-diagnostic",
        "output": str(output),
        "campaign_credit": False,
        "workflow_dispatched": False,
        "printer_connected": False,
        "started_at": utc_now(),
        "pins": {
            "blender_version": "4.5.10 LTS",
            "blender_mcp_revision": revision,
            "addon_sha256": sha(addon_source),
            "safe_mode_sha256": sha(safe_mode_source),
            "external_slicer_definition_sha256": external_definition[2],
        },
        "repairs": [],
    }
    write_json(output / "acceptance.json", result)

    server_command = [sys.executable, "-m", "blender_mcp.server"]
    server_env = {
        "PYTHONPATH": str(blender_source / "src"),
        "BLENDER_HOST": "127.0.0.1",
        "BLENDER_PORT": str(port),
        "BLENDER_MCP_SAFE_MODE": "true",
        "BLENDER_MCP_DISABLE_TELEMETRY": "true",
    }
    blender_runner = StdioRunner(server_command, env=server_env, operation_timeout=120)
    session = None
    lifecycle = None
    active_operation = None
    await blender_runner.start()
    try:
        tools = await blender_runner.list_tools()
        execute = next(tool for tool in tools if tool["name"] == "execute_blender_code")
        result["pins"]["execute_blender_code_input_schema_sha256"] = hashlib.sha256(
            json.dumps(execute["inputSchema"], sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        rejected = []
        for code in ("open('blocked.txt', 'w')", "import runpy\nrunpy.run_path('blocked.py')"):
            response = await blender_runner.call_tool(
                "execute_blender_code", {"code": code, "user_prompt": "guard rejection diagnostic"}
            )
            text = response_text(response)
            if "Rejected by safe mode" not in text or "Could not connect to Blender" in text:
                raise AssertionError(f"Guard did not reject before socket access: {text}")
            rejected.append({"code_sha256": hashlib.sha256(code.encode()).hexdigest(), "response": text})
        result["guard_rejections_before_socket"] = rejected

        upgrade_database(args.database)
        repository = NativeApplicationRepository(str(args.database))
        adapter = BlenderNativeApplicationAdapter(allowed_roots=(output,))
        lifecycle = NativeApplicationLifecycle(repository, adapter)
        trace = "printed-binding-proof-" + uuid4().hex
        launched = adapter.launch(
            args.executable,
            output / "owned-blender",
            addon_source=addon_source,
            addon_port=port,
            addon_sha256=result["pins"]["addon_sha256"],
        )
        session = lifecycle.register_session(launched, trace_id=trace)
        lease = lifecycle.acquire(
            session["session_id"],
            owner_id=trace,
            case_id="printed-binding-diagnostic",
            attempt="seam-001",
            trace_id=trace,
        )
        active_operation = "guarded-mesh-export"
        lifecycle.begin_operation(session["session_id"], lease["lease_id"], active_operation, trace_id=trace)
        created = adapter.create_document(session, "generic-print-seam-mesh")
        creation = output / "owned-blender" / "creation.json"
        write_json(creation, created)
        lifecycle.register_document(
            session["session_id"],
            lease["lease_id"],
            {
                "native_id": created["native_id"],
                "path": None,
                "dirty": True,
                "ownership": "owned",
                "preexisted": False,
                "creation_evidence": str(creation),
                "case_id": "printed-binding-diagnostic",
                "attempt": "seam-001",
                "recovery_path": str(output / "owned-blender" / "recovery.blend"),
            },
            trace_id=trace,
        )
        source_stl = artifacts / "source_mesh.stl"
        repaired_stl = artifacts / "repaired_mesh.stl"
        code = guarded_mesh_code(source_stl, repaired_stl)
        response = await blender_runner.call_tool(
            "execute_blender_code", {"code": code, "user_prompt": "generic guarded printing seam diagnostic"}
        )
        text = response_text(response)
        if "Code executed successfully" not in text or "WRIGHT_GUARDED_MESH_EXPORTED" not in text:
            raise RuntimeError(f"Guarded Blender mesh operation failed: {text}")
        source_mesh = stl_bounds(source_stl)
        repaired_mesh = stl_bounds(repaired_stl)
        identity_after_mesh = process_identity(session["identity"]["pid"])
        if identity_after_mesh != session["identity"]:
            raise AssertionError("Owned Blender process identity changed during mesh execution")
        lineage = {
            "operation": "guarded_execute_blender_code",
            "code": code,
            "code_sha256": hashlib.sha256(code.encode()).hexdigest(),
            "input_hashes": {
                "addon": result["pins"]["addon_sha256"],
                "safe_mode": result["pins"]["safe_mode_sha256"],
            },
            "output_hashes": {
                "source_mesh.stl": source_mesh["sha256"],
                "repaired_mesh.stl": repaired_mesh["sha256"],
            },
            "mcp_response": text,
        }
        write_json(artifacts / "blender-call-lineage.json", lineage)
        lifecycle.finish_operation(
            session["session_id"],
            active_operation,
            outcome="succeeded",
            evidence_reference=str(artifacts / "blender-call-lineage.json"),
            trace_id=trace,
        )
        active_operation = None
        result["owned_blender"] = {
            "session_id": session["session_id"],
            "identity": session["identity"],
            "identity_after_mesh": identity_after_mesh,
            "mesh_endpoint": session["mesh_endpoint"],
            "source_mesh": source_mesh,
            "repaired_mesh": repaired_mesh,
            "lineage_sha256": sha(artifacts / "blender-call-lineage.json"),
        }

        result["external_slice"] = await external_slice_probe(external_definition, workspace)
    except Exception as error:
        result["error"] = f"{type(error).__name__}: {error}"
        if session is not None and lifecycle is not None and active_operation is not None:
            lifecycle.finish_operation(
                session["session_id"],
                active_operation,
                outcome="unknown",
                evidence_reference=str(output / "owned-blender" / "control"),
                trace_id=trace,
            )
        raise
    finally:
        await blender_runner.stop()
        if session is not None and lifecycle is not None:
            result["cleanup"] = lifecycle.cleanup(
                session["session_id"],
                "printed-binding-diagnostic-cleanup",
                reason="diagnostic_finished",
                trace_id=trace,
            )
            result["post_cleanup_identity"] = process_identity(session["identity"]["pid"])
        result["finished_at"] = utc_now()
        write_json(output / "acceptance.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--blender-server-source", required=True, type=Path)
    parser.add_argument("--addon-source", required=True, type=Path)
    parser.add_argument("--slicer-provider", required=True, type=Path,
                        help="Explicit independently installed offline MCP command, schema, arguments and pinned configured profiles")
    args = parser.parse_args()
    result = asyncio.run(run(args))
    print(
        json.dumps(
            {
                "output": result["output"],
                "guard_rejections": len(result["guard_rejections_before_socket"]),
                "cleanup": result.get("cleanup", {}).get("status"),
                "error": result.get("error"),
            }
        )
    )


if __name__ == "__main__":
    main()
