"""Prepare source-bound printing campaign drafts; never executes a workflow.

The declarative binding edits the original canonical graph. After the normal
template instance API creates provenance, pass its returned source through
--instance-source to preserve its semantic identities when preparing a save.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

from workspace_service.workflow_source_execution import (
    _parse, compile_prompt_workflow, validate_workspace_authoring_shape,
)

ROOT = Path(__file__).resolve().parents[1]
BINDING = ROOT / "tests/datasets/engineering-workflows/bindings/printed-replacement-part.json"
TEMPLATE = ROOT / "packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/printed-replacement-part.workflow.wflow"
SERVER = "blender-mcp-ahujasid"
SLICE_WRAPPER = ROOT / "scripts/engineering_dataset_slice_mcp.py"
REPAIR_WRAPPER = ROOT / "scripts/engineering_dataset_mesh_repair_mcp.py"
REPAIR_OPERATION = ROOT / "scripts/engineering_dataset_mesh_repair.py"


def _agentcad_guidance():
    import importlib.util
    spec = importlib.util.spec_from_file_location("agentcad_source_contract",ROOT/"scripts/agentcad_source_contract.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.GUIDANCE


AGENTCAD_ENTRYPOINT_GUIDANCE = _agentcad_guidance()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def confined(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise ValueError("A campaign path escapes its declared workspace")
    return candidate


def write_once(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != data:
        raise ValueError(f"Refusing to replace a different staged file: {path}")
    path.write_bytes(data)


def port(key: str, kind: str = "engineering_document") -> dict:
    return dict(key=key, name=key.replace("_", " "), kind=kind, item=None,
                required=True, quantity="one", description="Campaign input or same-run output")


def render(sections: list[dict]) -> str:
    return "\n\n".join(
        f"{s['kind']} {s['id']}\n" + "\n".join(
            f"  {k}: {json.dumps(v, ensure_ascii=False, separators=(',', ':'))}"
            for k, v in s["fields"].items()
        ) + "\nend" for s in sections
    ) + "\n"


def add_reference(sections, producer, target, key, kind="engineering_document"):
    key = f"{target['id']}_{key}"
    target["fields"]["inputs"].append(port(key, kind))
    sections.append(dict(kind="connection", id=f"bind_{target['id']}_{key}", fields={
        "type": "item", "from": producer, "to": f"{target['id']}.{key}",
        "label": "campaign input binding", "when": None,
    }))


def add_file_input(sections, suffix, name, path):
    identity = f"campaign_{name}_{suffix}"
    sections.append(dict(kind="input", id=identity, fields={
        "name": name.replace("_", " "), "purpose": "Human-submitted campaign context",
        "step_type": "work", "group": None, "provided_by": "engineer",
        "inputs": [], "outputs": [port(identity + "_document")],
        "instructions": "Use the original supplied document; do not invent measurements.",
        "settings": {"input_mode": "workspace-file", "workspace_file": path},
        "tool": None, "reusable_step": None,
    }))
    return identity + "." + identity + "_document"


def selected_tool(tools, server, name):
    matches = [
        value
        for value in tools.values()
        if value.get("server_id") == server and value.get("tool_name") == name
    ]
    if len(matches) != 1:
        raise ValueError(f"Required configured tool is missing or ambiguous: {server}/{name}")
    return matches[0]


def publish_input_binding_evidence(report, scenario_directory):
    """Future-only sidecar; never changes staged bytes or canonical source."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("engineering_dataset_input_bindings", ROOT/"scripts/engineering_dataset_input_bindings.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.emit_for_preparation(report,scenario_directory)


def prepare(args, scenario_dir: Path, tools: dict) -> dict:
    config = json.loads(BINDING.read_text(encoding="utf-8"))
    blender_server = getattr(args, "blender_server", None) or SERVER
    repair_server = getattr(args, "repair_server", None) or config["repair_server"]
    slicer_server = getattr(args, "slicer_server", None) or config["slicer_server"]
    manifest = json.loads((scenario_dir / "scenario.json").read_text(encoding="utf-8"))
    scenario_id = manifest["scenario_id"]
    suffix = scenario_id.replace("-", "_") + "_" + args.attempt.replace("-", "_")
    input_root = f"campaign/{scenario_id}/{args.attempt}/inputs"
    output_root = f"campaign/{scenario_id}/{args.attempt}/artifacts"
    workspace = Path(args.workspace_root).resolve()
    draft_root = Path(args.draft_root).resolve() / scenario_id / args.attempt
    if draft_root.exists():
        raise ValueError(f"Draft attempt already exists; inspect it or choose a new attempt: {draft_root}")
    draft_root.mkdir(parents=True)
    # Blender's confined exporter may write files but cannot create host
    # directories. Establish the fresh attempt output root during staging so
    # the native application never needs broader filesystem privileges.
    confined(workspace, output_root).mkdir(parents=True, exist_ok=False)
    inputs = []
    for source in sorted(scenario_dir.iterdir()):
        if source.is_file():
            relative = f"{input_root}/{source.name}"
            data = source.read_bytes()
            write_once(confined(workspace, relative), data)
            inputs.append({"path": relative, "sha256": digest(data), "size_bytes": len(data),
                           "original": source.relative_to(ROOT).as_posix()})
    brief = "\n\n".join((scenario_dir / name).read_text(encoding="utf-8")
                          for name in ["user-profile.md", "context.md"])
    brief_path = f"{input_root}/assembled-context.md"
    write_once(confined(workspace, brief_path), brief.encode())
    inputs.append({"path": brief_path, "sha256": digest(brief.encode()), "size_bytes": len(brief.encode()),
                   "derived_from": [f"{input_root}/user-profile.md", f"{input_root}/context.md"]})
    source = Path(args.instance_source).read_text(encoding="utf-8") if args.instance_source else TEMPLATE.read_text(encoding="utf-8").replace("__instance__", suffix)
    sections = _parse(source)
    def stage(prefix):
        matches = [s for s in sections if s["kind"] in {"input", "task"} and s["id"].startswith(prefix + "_")]
        if len(matches) != 1:
            raise ValueError(f"Original canonical stage missing/ambiguous: {prefix}")
        return matches[0]
    image = stage("image_and_scale")
    image["fields"]["settings"].update(workspace_file=f"{input_root}/concept.png", rights_file=f"{input_root}/scenario.json", reference_dimension_mm=config["scenarios"][scenario_id]["reference_dimension_mm"])
    prompt_ref = add_file_input(sections, suffix, "user_prompt", f"{input_root}/prompt.txt")
    context_ref = add_file_input(sections, suffix, "user_and_business_context", brief_path)
    source_task = stage("create_mesh")
    source_config = config["stages"]["create_mesh"]
    source_result_key = source_task["id"] + "_result"
    source_task["fields"].update(
        performed_by="ai_assisted",
        prompt=source_config["prompt"].replace("{output_root}", output_root),
    )
    source_task["fields"]["outputs"] = [port(source_result_key)]
    source_task["fields"]["settings"].update({
        "authoring_template": "mcp-task", "mcp_server": blender_server,
        "output_format": "json", "save_output": True,
        "output_filename": f"{output_root}/source-model-report.json", "file_policy": "overwrite",
        "expected_files": "\n".join(f"{output_root}/{name}" for name in source_config["expected_files"]),
        "max_tool_calls": 12,
        "timeout_seconds": 600,
        "task_guidance": "Use only execute_blender_code, get_scene_info, get_viewport_screenshot. Do not access external asset or inference services. Preserve the exact original user prompt in every tool call. Return a compact operation and measurement summary; Wright records exact submitted source and file hashes in canonical evidence outside Blender. Never request raw file, hash, runpy, subprocess, persistent callback or text-datablock mechanisms. Blender safe mode rejects user-defined callables passed as callbacks or invoked indirectly: do not pass lambda functions or helper-function parameters that are later called; compute vertices and values explicitly. Explicitly import mathutils before calling mathutils.Vector; do not import and call Vector directly. Construct and export in the first authoring call when possible. Call bpy.ops.wm.stl_export(...) directly; never inspect bpy.ops or its module namespaces with hasattr or use an operator namespace as a value. Verify actual world-space bounds plus boundary and non-manifold edge counts, correct discrepancies, re-export, then finish immediately without a viewport screenshot once the requested bounds and zero boundary/non-manifold edges are reported. Never rebuild already-watertight geometry merely to restate measurements. Never report a file that was not generated.",
    })
    add_reference(sections, prompt_ref, source_task, "natural_prompt")
    add_reference(sections, context_ref, source_task, "supplied_context")

    repair_config = {
        "workspace_root": str(workspace),
        "source": str(confined(workspace, f"{output_root}/source_mesh.stl")),
        "repaired": str(confined(workspace, f"{output_root}/repaired_mesh.stl")),
        "preview": str(confined(workspace, f"{output_root}/mesh-preview.png")),
        "object_name": f"wright_{scenario_id.replace('-', '_')}_{args.attempt.replace('-', '_')}_repaired",
        "triangle_limit": 80000,
        "merge_tolerance_mm": 0.001,
        "degenerate_tolerance_mm": 0.000001,
    }
    repair_recipe_path = f"{input_root}/mesh-repair-operation.json"
    repair_recipe_bytes = (json.dumps(repair_config, indent=2) + "\n").encode()
    write_once(confined(workspace, repair_recipe_path), repair_recipe_bytes)
    inputs.append({"path": repair_recipe_path, "sha256": digest(repair_recipe_bytes), "size_bytes": len(repair_recipe_bytes), "kind": "reviewed_operation_configuration"})
    repair_operation_path = f"{input_root}/mesh-repair-operation.py"
    repair_operation_source = REPAIR_OPERATION.read_bytes()
    write_once(confined(workspace, repair_operation_path), repair_operation_source)
    inputs.append({"path": repair_operation_path, "sha256": digest(repair_operation_source), "size_bytes": len(repair_operation_source), "kind": "reviewed_executed_source"})
    repair = stage("repair_measure_orient")
    repair_binding = selected_tool(tools, repair_server, config["repair_tool"])
    repair_result_key = repair["id"] + "_result"
    repair["fields"].update(
        step_type="work", performed_by="configured_tool", inputs=[],
        outputs=[port(repair_result_key)], prompt="",
        instructions=config["stages"]["repair_measure_orient"]["prompt"].replace("{output_root}", output_root),
        tool=None, reusable_step=None,
    )
    repair["fields"]["settings"] = {
        "authoring_template": "mcp-tool", "mcp_server": repair_server,
        "mcp_tool": repair_binding["name"],
        "mcp_schema_digest": repair_binding["schema_digest"],
        "mcp_arguments": json.dumps({"configuration_document": repair_recipe_path, "operation_source_document": repair_operation_path}, separators=(",", ":")),
        "output_format": "json", "save_output": True,
        "output_filename": f"{output_root}/repair-model-report.json",
        "file_policy": "overwrite",
        "expected_files": "\n".join(f"{output_root}/{name}" for name in config["stages"]["repair_measure_orient"]["expected_files"]),
        "timeout_seconds": 600,
    }
    sections.append({
        "kind": "connection",
        "id": f"order_{source_task['id']}_{repair['id']}",
        "fields": {
            "type": "order",
            "from": source_task["id"],
            "to": repair["id"],
            "label": "repair the completed source mesh",
            "when": None,
        },
    })
    profile = config["scenarios"][scenario_id]["process"]
    slicer_config = {
        "slicer": str((ROOT / config["slicer"]["executable"]).resolve()),
        "profiles_root": str((ROOT / config["slicer"]["profiles_root"]).resolve()),
        "machine": config["slicer"]["machine"], "filament": config["slicer"]["filament"],
        "process": profile, "workspace_root": str(workspace), "output_root": output_root,
        "source": f"{output_root}/repaired_mesh.stl",
    }
    recipe_path = f"{input_root}/slice-operation.json"
    write_once(confined(workspace, recipe_path), (json.dumps(slicer_config, indent=2) + "\n").encode())
    inputs.append({"path": recipe_path, "sha256": digest(confined(workspace, recipe_path).read_bytes()), "kind": "reviewed_operation_configuration"})
    operation_path = f"{input_root}/slice-operation.py"
    operation_source = (ROOT / "scripts/engineering_dataset_slice.py").read_bytes()
    write_once(confined(workspace, operation_path), operation_source)
    inputs.append({"path": operation_path, "sha256": digest(operation_source), "kind": "reviewed_executed_source"})
    slicer = stage("supports_and_slice")
    slicer_binding = selected_tool(
        tools,
        slicer_server,
        config["slicer_tool"],
    )
    slicer["fields"].update(
        step_type="work",
        performed_by="configured_tool",
        inputs=[],
        outputs=[port(slicer["id"] + "_result")],
        prompt="",
        instructions=config["stages"]["supports_and_slice"]["prompt"],
        tool=None,
        reusable_step=None,
    )
    slicer["fields"]["settings"] = {
        "authoring_template": "mcp-tool",
        "mcp_server": slicer_server,
        "mcp_tool": slicer_binding["name"],
        "mcp_schema_digest": slicer_binding["schema_digest"],
        "mcp_arguments": json.dumps(
            {
                "configuration_document": recipe_path,
                "operation_source_document": operation_path,
            },
            separators=(",", ":"),
        ),
        "output_format": "json",
        "save_output": True,
        "output_filename": f"{output_root}/slice-operation-report.json",
        "file_policy": "overwrite",
        "expected_files": "\n".join(
            f"{output_root}/{name}"
            for name in config["stages"]["supports_and_slice"]["expected_files"]
        ),
        "timeout_seconds": 600,
    }
    approval = stage("authorize_transfer")
    approval["fields"]["settings"].update({
        "approval_binding": {"server": "wright", "tool": "test_handoff", "schema": digest(b"wright.integration_test_handoff.v1")},
        "approval_destination": {"kind": "integration_test", "id": f"test://{args.campaign_id}/printer/{scenario_id}"},
        "approval_settings": {"material": "PETG HF", "nozzle_mm": "0.4", "process": profile, "package_path": f"{output_root}/slice_package.gcode.3mf", "receipt_path": f"{output_root}/printer-transfer-receipt.json", "simulation": True},
        "approval_action": {"kind": "printer_transfer", "mode": "transfer_only", "simulation": True},
    })
    result = render(sections)
    validate_workspace_authoring_shape(result)
    compiled = compile_prompt_workflow(result)
    target = draft_root / "bound.workflow.wflow"
    target.write_text(result, encoding="utf-8")
    report = {"schema_version": 1, "scenario_id": scenario_id, "attempt_id": args.attempt,
        "status": "prepared_not_dispatched", "template_id": manifest["template_id"],
        "template_source_sha256": digest(TEMPLATE.read_bytes()), "source_sha256": digest(result.encode()),
        "source": str(target), "workspace_root": str(workspace), "output_root": output_root,
        "requires_template_instance_api": not bool(args.instance_source), "preserved_original_stages": [s.id for s in compiled.steps],
        "input_manifest": inputs,
        "tool_allowlist": [selected_tool(tools, blender_server, name) for name in config["allowed_tools"]]
        + [repair_binding, slicer_binding],
        "fixed_mesh_repair_wrapper": {
            "path": str(REPAIR_WRAPPER),
            "sha256": digest(REPAIR_WRAPPER.read_bytes()),
            "operation_path": str(REPAIR_OPERATION),
            "operation_sha256": digest(REPAIR_OPERATION.read_bytes()),
        },
        "fixed_slicer_wrapper": {
            "path": str(SLICE_WRAPPER),
            "sha256": digest(SLICE_WRAPPER.read_bytes()),
        },
        "execution_lineage_authority": {
            "kind": "canonical_mcp_step_record",
            "model_reports_are_authoritative": False,
            "actual_code": "tool_calls[].arguments.code",
            "input_hashes": "references[].sha256",
            "output_hashes": "produced_files[].sha256",
            "persistence": "canonical run/step evidence written by Wright outside Blender",
        },
        "expected_outputs": manifest["expected_outputs"], "expected_tool_created_files": [p for s in compiled.steps for p in s.expected_files],
        "approval_policy_request": {"mode": "auto", "scope": "integration_test", "destination": f"test://{args.campaign_id}/printer/{scenario_id}"},
        "blockers": ["Exact integration enrollment and test destination binding must be supplied by authoritative runtime before dispatch"],
    }
    publish_input_binding_evidence(report, scenario_dir)
    (draft_root / "staging-manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return {"scenario_id": scenario_id, "draft": str(target), "stages": len(compiled.steps), "files": len(inputs)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", default=str(ROOT / ".local-run/feature-081-live/printed-campaign-workspace"))
    parser.add_argument("--draft-root", default=str(ROOT / ".local-run/feature-081-live/printed-campaign-drafts"))
    parser.add_argument("--attempt", default="attempt-001")
    parser.add_argument("--campaign-id", default="081-engineering-datasets-v1")
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--session", default="wright-local-e3dc0ef1-06da-45dd-83b9-290347814f8a")
    parser.add_argument("--scenario", help="Scenario ID; otherwise prepare all three")
    parser.add_argument("--instance-source", help="Source returned by original-template instance API; requires --scenario")
    parser.add_argument("--blender-server", help="Registered server ID for the lifecycle-owned guarded Blender endpoint")
    parser.add_argument("--repair-server", help="Registered server ID for the fixed same-attempt Blender repair endpoint")
    parser.add_argument("--slicer-server", help="Registered server ID for the fixed local slicer")
    args = parser.parse_args()
    if args.instance_source and not args.scenario:
        parser.error("--instance-source requires --scenario")
    with urllib.request.urlopen(f"{args.api}/api/workspace/workflow-sources/tools?session_id={args.session}", timeout=30) as response:
        available = json.load(response)["tools"]
    tools = {(t["server_id"], t["tool_name"]): t for t in available}
    required = json.loads(BINDING.read_text())["allowed_tools"]
    blender_server = args.blender_server or SERVER
    if any((blender_server, name) not in tools for name in required):
        raise RuntimeError("Required Blender tools are not workspace available")
    binding = json.loads(BINDING.read_text())
    repair_server = args.repair_server or binding["repair_server"]
    if (repair_server, binding["repair_tool"]) not in tools:
        raise RuntimeError("Required fixed mesh-repair tool is not workspace available")
    slicer_server = args.slicer_server or binding["slicer_server"]
    if (slicer_server, binding["slicer_tool"]) not in tools:
        raise RuntimeError("Required fixed slicer tool is not workspace available")
    rows = []
    for directory in sorted((ROOT / "tests/datasets/engineering-workflows/scenarios/printed-replacement-part").iterdir()):
        scenario = json.loads((directory / "scenario.json").read_text())["scenario_id"]
        if not args.scenario or args.scenario == scenario:
            rows.append(prepare(args, directory, tools))
    if not rows:
        raise ValueError("No matching scenario")
    print(json.dumps({"prepared": rows, "executed": False}, indent=2))


if __name__ == "__main__":
    main()
