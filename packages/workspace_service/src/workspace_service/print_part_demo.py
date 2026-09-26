"""Prepare an isolated prompt-to-print run from Wright's printed-part example.

The demo reuses the reviewed Blender, mesh-repair and Bambu Studio operations.
Every attempt gets its own source, inputs and outputs. Printer dispatch is a
separate, explicit user action after the sliced package has been inspected.
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from .workflow_source_execution import (
    _parse,
    compile_prompt_workflow,
    validate_workspace_authoring_shape,
)


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "scripts/engineering_dataset_slice.py").is_file():
            return parent
    raise ValueError(
        "The local printed-part operations are unavailable. Run this demo from a Wright source checkout."
    )


def _port(key: str, kind: str = "engineering_document") -> dict:
    return {
        "key": key,
        "name": key.replace("_", " "),
        "kind": kind,
        "item": None,
        "required": True,
        "quantity": "one",
        "description": "Current print-demo attempt artifact",
    }


def _render(sections: list[dict]) -> str:
    return "\n\n".join(
        f"{section['kind']} {section['id']}\n"
        + "\n".join(
            f"  {key}: {json.dumps(value, ensure_ascii=False, separators=(',', ':'))}"
            for key, value in section["fields"].items()
        )
        + "\nend"
        for section in sections
    ) + "\n"


def _tool(tools: list[dict], server: str, name: str) -> dict:
    matches = [
        item for item in tools
        if item.get("server_id") == server and item.get("tool_name") == name
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Enable the {server} MCP server and its {name} tool in this workspace."
        )
    return matches[0]


def _section(sections: list[dict], prefix: str) -> dict:
    matches = [
        section for section in sections
        if section["kind"] in {"input", "task"}
        and section["id"].startswith(prefix + "_")
    ]
    if len(matches) != 1:
        raise ValueError(f"The printed-part template lacks its {prefix} stage.")
    return matches[0]


def _reference(sections: list[dict], producer: str, task: dict, key: str, kind="engineering_document") -> None:
    task["fields"]["inputs"].append(_port(key, kind))
    sections.append({
        "kind": "connection", "id": f"bind_{task['id']}_{key}",
        "fields": {
            "type": "item", "from": producer,
            "to": f"{task['id']}.{key}", "label": "current attempt input",
            "when": None,
        },
    })


def prepare_print_part_demo(
    *, workspace_dir: str, prompt: str, image_path: str | None,
    target_mm: float, tools: list[dict],
) -> tuple[str, str, dict[str, bytes], str]:
    """Return (workflow path, source, staged files, artifact root)."""
    if not isinstance(prompt, str) or len(prompt) > 12000:
        raise ValueError("Keep the design prompt under 12,000 characters.")
    if not prompt.strip() and not image_path:
        raise ValueError("Provide a design prompt, a reference image, or both.")
    if not 5 <= target_mm <= 250:
        raise ValueError("The target dimension must be between 5 and 250 mm.")
    root = _repo_root()
    binding = json.loads((root / "tests/datasets/engineering-workflows/bindings/printed-replacement-part.json").read_text(encoding="utf-8"))
    blender_tools = tuple(binding["allowed_tools"])
    if blender_tools != ("execute_blender_code", "get_scene_info", "get_viewport_screenshot"):
        raise ValueError("The reviewed printed-part Blender tool binding changed.")
    for tool_name in blender_tools:
        _tool(tools, "blender-mcp-ahujasid", tool_name)
    blender = _tool(tools, "blender-mcp-ahujasid", "execute_blender_code")
    repair_tool = _tool(tools, "wright-printed-part-mesh-repair", "repair_model_file")
    slicer_tool = _tool(tools, "wright-printed-part-slicer", "slice_model_file")
    slicer_executable = (root / binding["slicer"]["executable"]).resolve()
    profiles_root = (root / binding["slicer"]["profiles_root"]).resolve()
    if not slicer_executable.is_file() or not profiles_root.is_dir():
        raise ValueError(
            "The reviewed Bambu Studio CLI and P1S profiles are unavailable on this host."
        )
    suffix = "demo_" + uuid4().hex[:12]
    attempt = "demo-" + suffix[5:]
    input_root = f"campaign/printed-replacement-part-01/{attempt}/inputs"
    output_root = f"campaign/printed-replacement-part-01/{attempt}/artifacts"
    path = f"workflows/prompt-to-print-{suffix[5:]}.workflow.wflow"
    template = (root / "packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/printed-replacement-part.workflow.wflow").read_text(encoding="utf-8")
    sections = _parse(template.replace("__instance__", suffix))
    workflow = next(section for section in sections if section["kind"] == "workflow")
    workflow["fields"]["name"] = "Prompt to 3D printed part"
    workflow["fields"]["purpose"] = "Create a dimensioned mesh from the supplied request, repair it, compare stable orientations using actual Bambu P1S slices, and select a lower-support print package."
    image = _section(sections, "image_and_scale")
    if image_path:
        image["fields"]["settings"] = {
            "input_mode": "workspace-file", "workspace_file": image_path,
            "target_largest_dimension_mm": target_mm, "units": "mm",
        }
        image["fields"]["instructions"] = "Use the supplied image as visual reference. It provides no measured scale; use the requested target dimension as a design goal."
    else:
        sections.remove(image)
        sections[:] = [
            section for section in sections
            if section["id"] != "image_to_mesh_" + suffix
        ]
    prompt_input = {
        "kind": "input", "id": "design_prompt_" + suffix,
        "fields": {
            "name": "Design prompt", "purpose": "Original user design request",
            "step_type": "work", "group": None, "provided_by": "engineer",
            "inputs": [], "outputs": [_port("request")],
            "instructions": "Preserve the original user request and declared target size.",
            "settings": {"input_text": (prompt.strip() or "Create the part shown in the reference image.") + f"\nTarget largest dimension: {target_mm:g} mm."},
            "tool": None, "reusable_step": None,
        },
    }
    sections.append(prompt_input)
    create = _section(sections, "create_mesh")
    if not image_path:
        create["fields"]["inputs"] = []
    geometry_prompt = binding["stages"]["create_mesh"]["prompt"].replace(
        "Use the attached original PNG and the user's exact prompt",
        "Use the supplied reference image when present and the user's exact prompt",
    )
    geometry_prompt += (
        " Construct the geometry and export the source STL in the first "
        "execute_blender_code call. Do not leave a constructed-only model "
        "for a later tool decision to export. "
        " Call bpy.ops.wm.stl_export(filepath=..., export_selected_objects=True, "
        "ascii_format=False, global_scale=1.0) directly. The guarded Blender "
        "server rejects introspection such as hasattr(bpy.ops.wm, 'stl_export'); "
        "do not test operator availability. "
        " Choose and record a sensible initial build-plate orientation for this geometry. "
        " Give rounded or sculptural parts a modest flat underside so they can "
        "stand on the build plate without unnecessary supports. "
        "Place the lowest point on the Z=0 build plane. The next MCP stage "
        "preserves these axes while checking mesh and P1S envelope."
    )
    create["fields"].update(
        performed_by="ai_assisted",
        prompt=geometry_prompt.replace("{output_root}", str((Path(workspace_dir) / output_root).resolve()).replace("\\", "/")),
        outputs=[_port("source_report"), _port("source_mesh", "workspace_file")],
    )
    create["fields"]["settings"] = {
        "authoring_template": "mcp-task", "mcp_server": blender["server_id"],
        "mcp_task_tools": list(blender_tools),
        "output_format": "json", "save_output": True,
        "output_filename": f"{output_root}/source-model-report.json",
        "file_policy": "overwrite",
        "expected_files": f"{output_root}/source_mesh.stl",
        "expected_file_ports": {"source_mesh": f"{output_root}/source_mesh.stl"},
        "max_tool_calls": 12, "timeout_seconds": 600,
        "task_guidance": "Use the guarded Blender MCP tools to construct the requested part and export its closed manifold STL in the first execute_blender_code call. Call bpy.ops.wm.stl_export directly without hasattr or operator introspection. Preserve the user prompt and image as source references. Work in millimetres. Do not defer export, invent measurements, silently substitute a canned shape, or claim an absent file exists.",
    }
    _reference(sections, f"{prompt_input['id']}.request", create, "natural_prompt")
    repair = _section(sections, "repair_measure_orient")
    repair_config = {
        "workspace_root": str(Path(workspace_dir).resolve()),
        "source": str((Path(workspace_dir) / output_root / "source_mesh.stl").resolve()),
        "repaired": str((Path(workspace_dir) / output_root / "repaired_mesh.stl").resolve()),
        "preview": str((Path(workspace_dir) / output_root / "mesh-preview.png").resolve()),
        "object_name": "wright_" + suffix + "_repaired",
        "triangle_limit": 80000, "merge_tolerance_mm": 0.001,
        "degenerate_tolerance_mm": 0.000001,
        "force_voxel_remesh": False, "envelope_margin_mm": 0.0,
        "planar_cleanup": False, "measure_handle_features": False,
        "ensure_printable_base": True,
    }
    repair["fields"].update(inputs=[], outputs=[_port("repair_report"), _port("repaired_mesh", "workspace_file")], prompt="")
    repair["fields"]["instructions"] = (
        "Consume the actual source mesh. Repair and measure manifold geometry, "
        "preserve the selected axes, place its lowest point on the build plate, "
        "and export the exact repaired STL and preview."
    )
    repair["fields"]["settings"] = {
        "authoring_template": "mcp-tool", "mcp_server": repair_tool["server_id"],
        "mcp_tool": repair_tool["name"],
        "mcp_schema_digest": repair_tool["schema_digest"],
        "mcp_arguments": json.dumps({"configuration_document": f"{input_root}/mesh-repair-operation.json", "operation_source_document": f"{input_root}/mesh-repair-operation.py"}, separators=(",", ":")),
        "output_format": "json", "save_output": True,
        "output_filename": f"{output_root}/repair-model-report.json",
        "file_policy": "overwrite", "timeout_seconds": 600,
        "expected_files": "\n".join(f"{output_root}/{name}" for name in ("repaired_mesh.stl", "mesh-preview.png")),
        "expected_file_ports": {"repaired_mesh": f"{output_root}/repaired_mesh.stl"},
        "mcp_file_dependencies": {"source_mesh_in": f"{output_root}/source_mesh.stl"},
    }
    _reference(sections, f"{create['id']}.source_mesh", repair, "source_mesh_in", "workspace_file")
    slicer = _section(sections, "supports_and_slice")
    slice_config = {
        "slicer": str(slicer_executable),
        "profiles_root": str(profiles_root),
        "machine": binding["slicer"]["machine"],
        "filament": "filament/Generic PETG.json",
        "process": binding["scenarios"]["printed-replacement-part-01"]["process"],
        "workspace_root": str(Path(workspace_dir).resolve()),
        "output_root": output_root,
        "source": f"{output_root}/repaired_mesh.stl",
        "optimize_orientation": True,
    }
    slicer_files = [*binding["stages"]["supports_and_slice"]["expected_files"], "oriented_mesh.stl", "toolpaths.json"]
    slicer["fields"].update(inputs=[], outputs=[
        _port("slice_report"), _port("support_preview", "workspace_file"),
        _port("oriented_mesh", "workspace_file"),
        _port("slice_package", "workspace_file"),
        _port("slice_evidence", "workspace_file"),
        _port("toolpaths", "workspace_file"),
        _port("machine_profile", "workspace_file"),
        _port("filament_profile", "workspace_file"),
        _port("process_profile", "workspace_file"),
    ], prompt="")
    slicer["fields"]["settings"] = {
        "authoring_template": "mcp-tool", "mcp_server": slicer_tool["server_id"],
        "mcp_tool": slicer_tool["name"],
        "mcp_schema_digest": slicer_tool["schema_digest"],
        "mcp_arguments": json.dumps({"configuration_document": f"{input_root}/slice-operation.json", "operation_source_document": f"{input_root}/slice-operation.py"}, separators=(",", ":")),
        "output_format": "json", "save_output": True,
        "output_filename": f"{output_root}/slice-operation-report.json",
        "file_policy": "overwrite", "timeout_seconds": 600,
        "expected_files": "\n".join(f"{output_root}/{name}" for name in slicer_files),
        "expected_file_ports": {
            "support_preview": f"{output_root}/support-preview.svg",
            "oriented_mesh": f"{output_root}/oriented_mesh.stl",
            "slice_package": f"{output_root}/slice_package.gcode.3mf",
            "slice_evidence": f"{output_root}/slice-evidence.json",
            "toolpaths": f"{output_root}/toolpaths.json",
            "machine_profile": f"{output_root}/machine-profile.json",
            "filament_profile": f"{output_root}/filament-profile.json",
            "process_profile": f"{output_root}/process-profile.json",
        },
        "mcp_file_dependencies": {"repaired_mesh_in": f"{output_root}/repaired_mesh.stl"},
    }
    _reference(sections, f"{repair['id']}.repaired_mesh", slicer, "repaired_mesh_in", "workspace_file")
    sections[:] = [
        section for section in sections
        if section["id"] not in {
            "mesh_to_repair_" + suffix, "repair_to_slice_" + suffix,
        }
    ]
    # The built-in transfer checkpoint is a setup-required reference. The demo
    # has its own exact-package Print action and does not claim a test receipt.
    approval = _section(sections, "authorize_transfer")
    sections.remove(approval)
    sections[:] = [
        section for section in sections
        if section["id"] != "slice_to_transfer_" + suffix
    ]
    source = _render(sections)
    validate_workspace_authoring_shape(source)
    compile_prompt_workflow(source)
    staged = {
        f"{input_root}/mesh-repair-operation.json": (json.dumps(repair_config, indent=2) + "\n").encode(),
        f"{input_root}/mesh-repair-operation.py": (root / "scripts/engineering_dataset_mesh_repair.py").read_bytes(),
        f"{input_root}/slice-operation.json": (json.dumps(slice_config, indent=2) + "\n").encode(),
        f"{input_root}/slice-operation.py": (root / "scripts/engineering_dataset_slice.py").read_bytes(),
    }
    return path, source, staged, output_root
