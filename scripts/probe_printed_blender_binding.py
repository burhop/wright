"""Prove the guarded owned-Blender to fixed-Bambu printing seam.

This is a diagnostic only. It creates a generic disposable mesh, never uses a
dataset recipe, never dispatches a workflow, and never contacts a printer.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
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
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    workspace = output / "workspace"
    inputs = workspace / "diagnostic" / "inputs"
    artifacts = workspace / "diagnostic" / "artifacts"
    inputs.mkdir(parents=True)
    artifacts.mkdir()
    operation_source = ROOT / "scripts" / "engineering_dataset_slice.py"
    staged_operation = inputs / "slice-operation.py"
    staged_operation.write_bytes(operation_source.read_bytes())
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
            "slicer_executable_sha256": sha(args.slicer.resolve()),
            "slice_operation_sha256": sha(operation_source),
            "slice_wrapper_sha256": sha(ROOT / "scripts" / "engineering_dataset_slice_mcp.py"),
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

        configuration = {
            "slicer": str(args.slicer.resolve()),
            "profiles_root": str(args.profiles_root.resolve()),
            "machine": "machine/Bambu Lab P1S 0.4 nozzle.json",
            "filament": "filament/Bambu PETG HF @BBL P1S 0.4 nozzle.json",
            "process": {
                "base": "process/0.20mm Standard @BBL X1C.json",
                "layer_height": "0.20",
                "wall_loops": "4",
                "sparse_infill_density": "35%",
                "enable_support": "1",
            },
            "workspace_root": str(workspace),
            "output_root": "diagnostic/artifacts",
            "source": "diagnostic/artifacts/repaired_mesh.stl",
        }
        configuration_path = inputs / "slice-operation.json"
        write_json(configuration_path, configuration)
        slicer_runner = StdioRunner(
            [sys.executable, str(ROOT / "scripts" / "engineering_dataset_slice_mcp.py")],
            env={"WRIGHT_PRINT_WORKSPACE": str(workspace)},
            cwd=str(ROOT),
            operation_timeout=600,
        )
        await slicer_runner.start()
        try:
            slicer_tools = await slicer_runner.list_tools()
            slicer_tool = next(tool for tool in slicer_tools if tool["name"] == "slice_model_file")
            result["pins"]["slice_model_file_input_schema_sha256"] = hashlib.sha256(
                json.dumps(slicer_tool["inputSchema"], sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            sliced = await slicer_runner.call_tool(
                "slice_model_file",
                {
                    "configuration_document": "diagnostic/inputs/slice-operation.json",
                    "operation_source_document": "diagnostic/inputs/slice-operation.py",
                },
            )
        finally:
            await slicer_runner.stop()
        if sliced.get("isError"):
            raise RuntimeError(f"Fixed Bambu slicer tool failed: {response_text(sliced)}")
        evidence = json.loads((artifacts / "slice-evidence.json").read_text(encoding="utf-8"))
        result["external_bambu_slice"] = {
            "tool_response": response_text(sliced),
            "evidence": evidence,
            "package_sha256": sha(artifacts / "slice_package.gcode.3mf"),
            "preview_sha256": sha(artifacts / "slice-preview.png"),
            "support_preview_sha256": sha(artifacts / "support-preview.svg"),
        }
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
    parser.add_argument("--slicer", required=True, type=Path)
    parser.add_argument("--profiles-root", required=True, type=Path)
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
