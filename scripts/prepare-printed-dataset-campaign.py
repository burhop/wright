"""Prepare source-bound printing campaign drafts; never executes a workflow.

The declarative binding edits the original canonical graph. After the normal
template instance API creates provenance, pass its returned source through
--instance-source to preserve its semantic identities when preparing a save.
"""
from __future__ import annotations

import argparse
import importlib.util
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
REPAIR_POLICY = ROOT / "examples/process-interfaces/printed-replacement-part/original-repair-policy.json"
VALIDATION_COVERAGE = ROOT / "packages/workspace_service/src/workspace_service/process_validation/profiles/coverage.json"


_helper_spec = importlib.util.spec_from_file_location(
    "engineering_campaign_binding_helpers", ROOT / "scripts/engineering_campaign_binding_helpers.py"
)
_binding_helpers = importlib.util.module_from_spec(_helper_spec)
_helper_spec.loader.exec_module(_binding_helpers)
_renewal_module = _binding_helpers._renewal_module
_agentcad_guidance = _binding_helpers._agentcad_guidance
digest = _binding_helpers.digest
confined = _binding_helpers.confined
write_once = _binding_helpers.write_once
port = _binding_helpers.port
render = _binding_helpers.render
add_reference = _binding_helpers.add_reference
add_file_input = _binding_helpers.add_file_input
selected_tool = _binding_helpers.selected_tool
publish_input_binding_evidence = _binding_helpers.publish_input_binding_evidence
AGENTCAD_ENTRYPOINT_GUIDANCE = _binding_helpers.AGENTCAD_ENTRYPOINT_GUIDANCE


_slice_spec = importlib.util.spec_from_file_location(
    "external_campaign_slice_binding", ROOT / "scripts/engineering_external_slice_binding.py"
)
external_slice = importlib.util.module_from_spec(_slice_spec)
_slice_spec.loader.exec_module(external_slice)

_mesh_spec = importlib.util.spec_from_file_location(
    "external_campaign_mesh_binding", ROOT / "scripts/engineering_external_mesh_binding.py"
)
external_mesh = importlib.util.module_from_spec(_mesh_spec)
_mesh_spec.loader.exec_module(external_mesh)


def prepare(args, scenario_dir: Path, tools: dict) -> dict:
    renewal = _renewal_module()
    config = json.loads(BINDING.read_text(encoding="utf-8"))
    blender_server = getattr(args, "blender_server", None) or SERVER
    manifest = json.loads((scenario_dir / "scenario.json").read_text(encoding="utf-8"))
    scenario_id = manifest["scenario_id"]
    prepared_slice = external_slice.preflight(
        getattr(args, "slicer_binding", None), scenario_id, tools,
        config["scenarios"][scenario_id]["process"],
    )
    original_policy = json.loads(REPAIR_POLICY.read_bytes())
    repair_policy = {key: value for key, value in original_policy.items()
                     if key not in {"schema_version", "basis", "archived_operation_sha256", "handle_triangle_limit"}}
    if scenario_id == "printed-replacement-part-02":
        repair_policy["triangle_limit"] = original_policy["handle_triangle_limit"]
    repair_policy["planar_cleanup"] = scenario_id == "printed-replacement-part-02"
    input_root = f"campaign/{scenario_id}/{args.attempt}/inputs"
    output_root = f"campaign/{scenario_id}/{args.attempt}/artifacts"
    workspace = Path(args.workspace_root).resolve()
    if getattr(args, "repair_server", None):
        raise ValueError("The old --repair-server wrapper path is retired; supply --repair-binding")
    prepared_mesh = external_mesh.preflight(
        getattr(args, "repair_binding", None), scenario_id, tools,
        workspace=workspace, output_root=output_root, policy=repair_policy,
        machine_profile_sha256=digest(prepared_slice[2]["machine"]),
    )
    correction_source = getattr(args, "review_correction_source", None)
    correction_proof = getattr(args, "review_correction_proof", None)
    correction_files = {}
    if correction_source or correction_proof:
        if scenario_id != "printed-replacement-part-02" or not (correction_source and correction_proof):
            raise ValueError("Printed 02 review correction requires its paired source and qualification proof")
        source_bytes = Path(correction_source).read_bytes()
        proof_bytes = Path(correction_proof).read_bytes()
        proof = json.loads(proof_bytes)
        if (
            proof.get("status") != "qualified"
            or proof.get("source_code_after_sha256") != digest(source_bytes)
            or proof.get("operation_sha256") != original_policy["archived_operation_sha256"]
            or proof.get("cleanup", {}).get("status") != "cleaned"
            or proof.get("cleanup", {}).get("post_cleanup_identity") is not None
        ):
            raise ValueError("Printed 02 historical correction qualification identity is not current")
        correction_files = {
            "review-correction-source.py": source_bytes,
            "review-correction-qualification.json": proof_bytes,
        }
    coverage = json.loads(VALIDATION_COVERAGE.read_text(encoding="utf-8"))
    support = next(
        row for row in coverage["scenarios"] if row["scenario_id"] == scenario_id
    )
    validation_profile = support.get("full_profile")
    if not validation_profile:
        raise ValueError("The printed-part full validator profile is unavailable")
    profile_document = json.loads(
        (
            ROOT
            / "packages/workspace_service/src/workspace_service/process_validation/profiles"
            / (validation_profile["profile_resource"] + ".json")
        ).read_text(encoding="utf-8")
    )
    suffix = scenario_id.replace("-", "_") + "_" + args.attempt.replace("-", "_")
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
    renewal_data = renewal.contract_bytes(manifest)
    renewal_path = f"{input_root}/approved-engineering-brief.json"
    write_once(confined(workspace, renewal_path), renewal_data)
    inputs.append({"path": renewal_path, "sha256": digest(renewal_data),
                   "size_bytes": len(renewal_data), "role": "approved_engineering_brief"})
    brief = "\n\n".join((scenario_dir / name).read_text(encoding="utf-8")
                          for name in ["user-profile.md", "context.md"])
    brief_path = f"{input_root}/assembled-context.md"
    write_once(confined(workspace, brief_path), brief.encode())
    inputs.append({"path": brief_path, "sha256": digest(brief.encode()), "size_bytes": len(brief.encode()),
                   "derived_from": [f"{input_root}/user-profile.md", f"{input_root}/context.md"]})
    for name, data in correction_files.items():
        relative = f"{input_root}/{name}"
        write_once(confined(workspace, relative), data)
        inputs.append({"path": relative, "sha256": digest(data), "size_bytes": len(data),
                       "role": "same_case_review_correction"})
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
    engineering_brief_ref = add_file_input(
        sections, suffix, "approved_engineering_brief", renewal_path
    )
    source_task = stage("create_mesh")
    add_reference(
        sections, engineering_brief_ref, source_task, "approved_engineering_brief"
    )
    source_config = config["stages"]["create_mesh"]
    source_result_key = source_task["id"] + "_result"
    source_task["fields"].update(
        performed_by="ai_assisted",
        prompt=source_config["prompt"].replace("{output_root}", output_root),
    )
    source_task["fields"]["outputs"] = [
        port(source_result_key),
        port("source_mesh", "workspace_file"),
    ]
    source_task["fields"]["settings"].update({
        "authoring_template": "mcp-task", "mcp_server": blender_server,
        "output_format": "json", "save_output": True,
        "output_filename": f"{output_root}/source-model-report.json", "file_policy": "overwrite",
        "expected_files": "\n".join(f"{output_root}/{name}" for name in source_config["expected_files"]),
        "max_tool_calls": 12,
        "timeout_seconds": 600,
        "expected_file_ports": {"source_mesh": f"{output_root}/source_mesh.stl"},
        "task_guidance": "Use only execute_blender_code, get_scene_info, get_viewport_screenshot. Do not access external asset or inference services. Preserve the exact original user prompt in every tool call. Return a compact operation and measurement summary; Wright records exact submitted source and file hashes in canonical evidence outside Blender. Never request raw file, hash, runpy, subprocess, persistent callback or text-datablock mechanisms. Blender safe mode rejects user-defined callables passed as callbacks or invoked indirectly: do not pass lambda functions or helper-function parameters that are later called; compute vertices and values explicitly. Explicitly import mathutils before calling mathutils.Vector; do not import and call Vector directly. Construct and export in the first authoring call when possible. Call bpy.ops.wm.stl_export(...) directly; never inspect bpy.ops or its module namespaces with hasattr or use an operator namespace as a value. Verify actual world-space bounds plus boundary and non-manifold edge counts, correct discrepancies, re-export, then finish immediately without a viewport screenshot once the requested bounds and zero boundary/non-manifold edges are reported. Never rebuild already-watertight geometry merely to restate measurements. Never report a file that was not generated.",
    })
    if scenario_id == "printed-replacement-part-02":
        source_task["fields"]["prompt"] += (
            " Review correction: preserve the 96 mm mounting frame and every supplied dimension. "
            "The previous source's nominal 25 mm clearance measured only 24.8168 mm "
            "because a sweep segment crossed the central-span boundary. Explicitly include "
            "X=15.5 and X=80.5 in the construction and keep the complete triangulated "
            "underside at Z>=25 throughout that interval, with outer Z<=34. "
            "A nominal dimension in your report is not a measurement. Retain the oval "
            "12 by 9 mm section, 1.5 mm recess, required edge rounding and internal blends; "
            "explain any where-space-permits blend limitation. Preserve exact bores and "
            "flat mounting faces; the repair now cleans planar topology without forcing "
            "a voxel remesh of a valid solid. Save the actual editable Blender scene with "
            f"bpy.ops.wm.save_as_mainfile(filepath='{(workspace / output_root / 'native-design.blend').as_posix()}', copy=True) "
            "to save a native copy while preserving the owned lifecycle document path "
            "after authoring, as well as source_mesh.stl. Compare pads-down and side "
            "orientations in the source report, including bed contact, bore direction, "
            "grip surface support contact and why pads-down is selected for this process. "
            "Final mesh measurements and the actual support preview remain subject to review."
        )
        source_task["fields"]["outputs"].append(port("native_design", "workspace_file"))
        source_task["fields"]["settings"]["expected_files"] += f"\n{output_root}/native-design.blend"
        source_task["fields"]["settings"]["expected_file_ports"]["native_design"] = f"{output_root}/native-design.blend"
    if correction_files:
        for name in correction_files:
            key = name.replace(".", "_").replace("-", "_")
            reference = add_file_input(sections, suffix, key, f"{input_root}/{name}")
            add_reference(sections, reference, source_task, key)
        source_task["fields"]["prompt"] += (
            " The supplied review-correction-source.py is the audited correction of this exact "
            "case's rejected design. Reuse its construction through execute_blender_code, changing "
            "only the two export paths to this attempt's source_mesh.stl and native-design.blend "
            "paths above. Submit its source directly as the tool's code argument; do not use exec, "
            "runpy or file-reading code inside Blender. This preserves independently measured "
            "tangent root rounds, perpendicular oval shoulder sections and the full X=28..68 "
            "thumb recess. Do not replace it with a newly invented sweep or post-union bevel. "
            "Generate and inspect actual current-attempt files, then report the measurements "
            "and orientation comparison. Qualification evidence is not approval and does not "
            "substitute for the current native execution or final engineering review."
        )
    add_reference(sections, prompt_ref, source_task, "natural_prompt")
    add_reference(sections, context_ref, source_task, "supplied_context")

    repair = stage("repair_measure_orient")
    repair_binding = prepared_mesh["selected_tool"]
    repair["fields"]["instructions"] = config["stages"]["repair_measure_orient"]["prompt"].replace("{output_root}", output_root)
    mesh_binding_evidence = external_mesh.bind(
        sections, repair, source_task["id"] + ".source_mesh", workspace=workspace,
        input_root=input_root, output_root=output_root, prepared=prepared_mesh,
        inspection={"tool": prepared_slice[1]["inspection"], "configuration": prepared_slice[0]["inspection"]},
        staged=inputs,
    )
    # The original template already orders these stages. Retain that identity
    # rather than adding a duplicate that the diagram correctly rejects.
    if not any(
        section["kind"] == "connection"
        and section["fields"].get("type") == "order"
        and section["fields"].get("from") == source_task["id"]
        and section["fields"].get("to") == repair["id"]
        and section["fields"].get("when") is None
        for section in sections
    ):
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
    slicer = stage("supports_and_slice")
    slice_binding_evidence = external_slice.bind(
        sections, slicer, repair["id"] + ".repaired_mesh",
        workspace=workspace, input_root=input_root, output_root=output_root,
        source=f"{output_root}/repaired_mesh.stl", prepared=prepared_slice,
        staged=inputs, operation_label="actual_local_bambu_slice",
    )
    sections.append({"kind": "connection", "id": "verified_mesh_before_slice_" + suffix,
                     "fields": {"type": "order", "from": mesh_binding_evidence["validation_step_id"],
                                "to": slice_binding_evidence["package_reference"].split(".")[0],
                                "when": None, "label": "hold slicing until actual geometry checks pass"}})
    approval = stage("authorize_transfer")
    approval["fields"]["outputs"] = [port("receipt", "workspace_file")]
    approval["fields"]["settings"].update({
        "approval_binding": {"server": "wright", "tool": "test_handoff", "schema": digest(b"wright.integration_test_handoff.v1")},
        "approval_destination": {"kind": "integration_test", "id": f"test://{args.campaign_id}/printer/{scenario_id}"},
        "approval_settings": {"material": "PETG HF", "nozzle_mm": "0.4", "process": profile, "package_path": f"{output_root}/slice_package.gcode.3mf", "receipt_path": f"{output_root}/printer-transfer-receipt.json", "simulation": True},
        "approval_action": {"kind": "printer_transfer", "mode": "transfer_only", "simulation": True},
    })
    final_review = {
        "kind": "task",
        "id": "review_printed_outputs_" + suffix,
        "fields": {
            "name": "Review exact printed-part outputs",
            "purpose": "Review geometry, orientation and claim scope",
            "step_type": "review",
            "group": None,
            "performed_by": "engineer",
            "inputs": [],
            "outputs": [],
            "instructions": "Review the exact source-model report against every frozen geometry, tolerance, orientation, support and action-scope requirement. Approval does not establish physical fit, strength or print success.",
            "tool": None,
            "reusable_step": None,
            "settings": {
                "authoring_template": "external-action-approval",
                "action_kind": "local_review",
                "approval_binding": {"server": "wright", "tool": "review_artifacts", "schema": digest(b"wright.local_review.v1")},
                "approval_destination": {"kind": "local_review", "id": "workspace"},
                "approval_settings": {
                    "review_task_id": "review_printed_outputs_" + suffix,
                    "validation_review": {
                        "profile_ref": validation_profile["profile_ref"],
                        "requirement_ids": sorted(
                            requirement["id"]
                            for requirement in profile_document["baseline"]["requirements"]
                            if requirement["review_required"]
                        ),
                    },
                },
                "approval_action": {"kind": "local_review", "mode": "review_only"},
            },
        },
    }
    sections.append(final_review)
    add_reference(sections, source_task["id"] + "." + source_result_key, final_review, "source_report")
    add_reference(sections, mesh_binding_evidence["feature_reference"], final_review, "actual_mesh_inspection", "workspace_file")
    if scenario_id == "printed-replacement-part-02":
        add_reference(sections, source_task["id"] + ".native_design", final_review, "native_design")
        add_reference(sections, mesh_binding_evidence["feature_reference"], final_review, "final_feature_measurements", "workspace_file")
    validation_sources = {
        "source_mesh": (source_task, "source_mesh", "workspace_file"),
        "source_report": (source_task, source_result_key, "engineering_document"),
        "repaired_mesh": (repair, "repaired_mesh", "workspace_file"),
        "slice_package": (
            next(section for section in sections
                 if section["id"] == slice_binding_evidence["package_reference"].split(".")[0]),
            slice_binding_evidence["package_reference"].split(".")[1], "workspace_file"),
        **{
            role: (slicer, role, "workspace_file")
            for role in (
                "support_preview",
                "slice_evidence",
                "machine_profile",
                "filament_profile",
                "process_profile",
            )
        },
        "transfer_receipt": (approval, "receipt", "workspace_file"),
    }
    validator = {
        "kind": "task",
        "id": "validate_printed_content_" + suffix,
        "fields": {
            "name": "Validate current printed-part outputs",
            "purpose": "Check exact model, slice and simulated handoff evidence",
            "step_type": "work",
            "group": None,
            "performed_by": "configured_tool",
            "inputs": [port("validate_" + role, kind) for role, (_, _, kind) in validation_sources.items()],
            "outputs": [port("assessment")],
            "prompt": "",
            "tool": None,
            "reusable_step": None,
            "settings": {
                "authoring_template": "process-validator",
                "output_format": "json",
                "max_revisions": 0,
                "validation": {
                    "profile": {"source": "packaged", "name": validation_profile["profile_resource"], "reference": validation_profile["profile_ref"]},
                    "baseline": validation_profile["baseline_ref"],
                    "subjects": {role: "validate_" + role for role in validation_sources},
                },
            },
        },
    }
    sections.append(validator)
    for role, (producer, producer_port, _) in validation_sources.items():
        sections.append({"kind": "connection", "id": "bind_" + validator["id"] + "_" + role, "fields": {
            "type": "item", "from": producer["id"] + "." + producer_port,
            "to": validator["id"] + ".validate_" + role,
            "label": "current printed-part output to validate", "when": None,
        }})
    for left, right in ((approval, final_review), (final_review, validator)):
        sections.append({"kind": "connection", "id": "order_" + left["id"] + "_" + right["id"], "fields": {
            "type": "order", "from": left["id"], "to": right["id"],
            "label": "complete exact output review and validation", "when": None,
        }})
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
        + [repair_binding, *prepared_slice[1].values()],
        "external_mesh_binding": {key: value for key, value in mesh_binding_evidence.items() if key != "inspection_step"},
        "historical_correction_scope": "Retained source/legacy qualification is historical evidence only; current independent repair and exact-byte inspection must run afresh",
        "external_slicer_binding": slice_binding_evidence,
        "execution_lineage_authority": {
            "kind": "canonical_mcp_step_record",
            "model_reports_are_authoritative": False,
            "actual_code": "tool_calls[].arguments.code",
            "input_hashes": "references[].sha256",
            "output_hashes": "produced_files[].sha256",
            "persistence": "canonical run/step evidence written by Wright outside Blender",
        },
        "expected_outputs": renewal.expected_outputs(manifest), "expected_tool_created_files": [p for s in compiled.steps for p in s.expected_files],
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
    parser.add_argument("--repair-binding", required=True, help="Pinned arguments and original policy for an independently installed geometry provider")
    parser.add_argument("--slicer-binding", required=True, help="Explicit independent slicer/inspection binding and pinned profiles for the selected scenario")
    parser.add_argument("--review-correction-source", help="Audited same-case Printed 02 construction to reuse through MCP")
    parser.add_argument("--review-correction-proof", help="Current native qualification bound to the correction source and repair operation")
    args = parser.parse_args()
    if not args.scenario:
        parser.error("--scenario is required for an exact external slicer binding")
    with urllib.request.urlopen(f"{args.api}/api/workspace/workflow-sources/tools?session_id={args.session}", timeout=30) as response:
        available = json.load(response)["tools"]
    tools = {(t["server_id"], t["tool_name"]): t for t in available}
    required = json.loads(BINDING.read_text())["allowed_tools"]
    blender_server = args.blender_server or SERVER
    if any((blender_server, name) not in tools for name in required):
        raise RuntimeError("Required Blender tools are not workspace available")
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
