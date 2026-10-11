"""Declare independent geometry operations and passive inspection; never execute them.

Arguments are pinned supplied inputs, not native code generated or interpreted
by this helper. Existing canonical source/runtime/gateway mechanisms own work.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "mesh_binding_helpers", ROOT / "scripts/engineering_campaign_binding_helpers.py"
)
helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(helpers)


def _object(raw):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("Duplicate mesh binding field")
            value[key] = item
        return value

    def finite(_value):
        raise ValueError("Mesh bindings must contain finite JSON")

    value = json.loads(raw, object_pairs_hook=unique, parse_constant=finite)
    if not isinstance(value, dict):
        raise ValueError("Mesh binding and arguments must be JSON objects")
    return value


def preflight(binding_path, scenario, tools, *, workspace, output_root, policy, machine_profile_sha256):
    """Resolve known requirements before staging; caller still needs acceptance."""
    if not binding_path:
        raise ValueError("Supply --repair-binding for an independent provider; bundled mesh wrappers are retired")
    try:
        path = Path(binding_path)
        if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= 65536:
            raise ValueError("Mesh binding must be a bounded regular JSON file")
        raw = path.read_bytes()
        binding = _object(raw)
        if type(binding["schema_version"]) is not int or binding["schema_version"] != 1 or binding["scenario_id"] != scenario:
            raise ValueError("Mesh binding must identify this exact scenario")
        if binding["workspace_root"] != str(Path(workspace).resolve()) or binding["output_root"] != output_root:
            raise ValueError("Mesh binding must identify the exact fresh workspace/attempt")
        # JSON identities retain numeric/boolean types; Python equality aliases
        # False with 0 and would otherwise accept a changed native policy.
        pinned_policy = json.dumps(policy, sort_keys=True, allow_nan=False, separators=(",", ":"))
        supplied_policy = json.dumps(binding["policy"], sort_keys=True, allow_nan=False, separators=(",", ":"))
        if supplied_policy != pinned_policy or binding["machine_profile_sha256"] != machine_profile_sha256:
            raise ValueError("Mesh binding changes the original policy or selected machine profile")
        choice = binding["provider"]
        if choice["server"] == "wright-printed-part-mesh-repair":
            raise ValueError("Select an independently installed geometry provider")
        rows = list(tools.values()) if isinstance(tools, dict) else tools
        matches = [row for row in rows if row.get("server_id") == choice["server"]
                   and row.get("tool_name") == choice["tool"]
                   and row.get("schema_digest") == choice["schema_digest"]]
        if len(matches) != 1 or not choice["schema_digest"]:
            raise ValueError("Required independent mesh capability is missing, ambiguous or changed")
        reference = binding["arguments"]
        argument_path = Path(reference["path"])
        if argument_path.is_symlink() or not argument_path.is_file() or not 0 < argument_path.stat().st_size <= 65536:
            raise ValueError("Supply bounded pinned provider arguments")
        arguments = argument_path.read_bytes()
        if helpers.digest(arguments) != reference["sha256"]:
            raise ValueError("Supplied provider arguments changed")
        _object(arguments)
        return {"binding": binding, "binding_sha256": helpers.digest(raw),
                "selected_tool": matches[0], "arguments": arguments,
                "arguments_source": str(argument_path)}
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError("Complete the exact provider, argument, attempt, policy and machine binding before preparation") from error


def validation_profile(policy, *, policy_path, policy_sha256, operation_path, operation_sha256, handle=False):
    """Configure the existing 082 validator; producer success never grants slicing."""
    from core.process_validation import ValidationProfile

    sources = [{"artifact_ref": policy_path, "sha256": policy_sha256,
                "locator": "Retained original geometry preparation policy"},
               {"artifact_ref": operation_path, "sha256": operation_sha256,
                "locator": "Pinned passive exact-byte inspection and original handle measurements"}]
    requirements, checks = [], []

    def check(name, text, role, reader, selector, constraint, *, unit=None, parameters=None):
        requirements.append({"id": name, "text": text, "scope": "design", "sources": sources})
        checks.append({"id": name, "requirement_ids": [name], "subject_role": role,
                       "reader": reader, "selector": selector, "constraint": constraint,
                       "unit": unit, "evidence_method": "independent_measurement" if reader == "printing" else "structured_value",
                       "parameters": parameters or {}})

    exact = {"unit_convention": "mm"}
    check("actual-mesh-integrity", "The actual repaired binary STL has closed nondegenerate manifold edges.",
          "repaired_mesh", "printing", "mesh/integrity", {"operator": "equals", "expected": True},
          parameters={"operation": "mesh_integrity", **exact})
    for metric, constraint, unit in (
        ("connected_components", {"operator": "equals", "expected": 1}, "1"),
        ("signed_volume_mm3", {"operator": "range", "minimum": 0.0, "inclusive": False}, "mm3"),
        ("triangle_count", {"operator": "range", "maximum": policy["triangle_limit"]}, "1"),
    ):
        check("actual-" + metric, "Retain the original repaired-mesh requirement for " + metric + ".",
              "repaired_mesh", "printing", "mesh/" + metric, constraint, unit=unit,
              parameters={"operation": "mesh_metric", **exact})
    for axis, limit in zip("xyz", policy["build_volume_mm"]):
        check("actual-envelope-" + axis, "The actual repaired extent fits the declared original build envelope.",
              "repaired_mesh", "printing", "mesh/" + axis + "_span_mm",
              {"operator": "range", "maximum": limit + policy["build_volume_tolerance_mm"]}, unit="mm",
              parameters={"operation": "stl_dimension", **exact})
    for name in ("closed_manifold", "outward_normals", "single_component", "no_degenerate_faces",
                 "within_triangle_limit", "fits_declared_build_volume"):
        check("inspection-" + name, "The pinned passive measurement report also records this retained check passing: " + name + ".",
              "mesh_evidence", "structured", "/checks/" + name, {"operator": "equals", "expected": True})
    if handle:
        check("original-handle-clearance", "The original exact triangle clipping measurement retains at least 25 mm central handle clearance.",
              "mesh_evidence", "structured", "/final_feature_measurements/minimum_clearance_mm",
              {"operator": "range", "minimum": 25.0}, unit="mm")
    return ValidationProfile.model_validate({
        "id": "repaired-mesh-integrity", "version": "1", "supported_kinds": ["file"],
        "baseline": {"id": "original-repaired-mesh-policy", "version": "1", "requirements": requirements},
        "checks": checks,
        "limitations": ["This pre-slice gate reuses the 082 validator over exact current output subjects; the original full profile and human reviews still govern engineering acceptance.",
                        "Signed volume is the retained global orientation diagnostic, not verification of every facet winding.",
                        "Passive report checks and handle clearance are structured measurements from the pinned inspection operation, not a trustworthy solver attestation or human acceptance."]})


def bind(sections, step, upstream, *, workspace, input_root, output_root, prepared, inspection, staged):
    """Reuse connected JSON arguments and explicit file dependencies on the original block."""
    root = Path(workspace).resolve()
    source = output_root + "/source_mesh.stl"
    repaired = output_root + "/repaired_mesh.stl"
    preview = output_root + "/mesh-preview.png"
    policy = prepared["binding"]["policy"]

    def stage_input(name, raw, role):
        relative = input_root + "/" + name
        helpers.write_once(helpers.confined(root, relative), raw)
        staged.append({"path": relative, "sha256": helpers.digest(raw), "size_bytes": len(raw), "kind": role})
        reference = helpers.add_file_input(sections, step["id"], name.replace(".", "_").replace("-", "_"), relative)
        if role != "pinned_external_operation_arguments":
            sections[-1]["fields"]["outputs"][0]["kind"] = "workspace_file"
        return reference, relative

    arguments_ref, arguments_relative = stage_input("mesh-provider-arguments.json", prepared["arguments"], "pinned_external_operation_arguments")
    policy_bytes = (json.dumps(policy, indent=2, allow_nan=False) + "\n").encode()
    policy_ref, policy_relative = stage_input("mesh-inspection-policy.json", policy_bytes, "original_geometry_policy")
    choice = prepared["selected_tool"]
    result_key = step["id"] + "_result"
    step["fields"].update(step_type="work", performed_by="configured_tool", prompt="", inputs=[],
        outputs=[helpers.port(result_key), helpers.port("repaired_mesh", "workspace_file"), helpers.port("geometry_preview", "workspace_file")], tool=None, reusable_step=None)
    argument_key = step["id"] + "_qualified_operation"
    step["fields"]["settings"] = {
        "authoring_template": "mcp-tool", "mcp_server": choice["server_id"], "mcp_tool": choice["name"],
        "mcp_schema_digest": choice["schema_digest"], "mcp_arguments": "{}", "mcp_arguments_source": "connection",
        "mcp_arguments_input": argument_key, "timeout_seconds": 600, "output_format": "json", "save_output": True,
        "output_filename": output_root + "/repair-model-report.json", "file_policy": "overwrite",
        "expected_files": repaired + "\n" + preview, "expected_file_ports": {"repaired_mesh": repaired, "geometry_preview": preview},
        "mcp_file_dependencies": {step["id"] + "_actual_source": source,
                                  step["id"] + "_original_policy": policy_relative},
    }
    helpers.add_reference(sections, arguments_ref, step, "qualified_operation")
    helpers.add_reference(sections, upstream, step, "actual_source", "workspace_file")
    helpers.add_reference(sections, policy_ref, step, "original_policy", "workspace_file")
    operation_path = ROOT / "scripts/engineering/inspect_repaired_mesh.py"
    operation = operation_path.read_bytes()
    inspection_step = {"kind": "task", "id": "inspect_repaired_mesh_" + step["id"],
        "fields": {"name": "Measure the exact repaired STL against the original policy",
                   "purpose": "Independent final-byte mesh and requested feature measurements",
                   "group": None, "inputs": [], "outputs": [], "settings": {}, "instructions": "Keep original mandatory geometry checks; this is digital evidence, not human acceptance."}}
    sections.append(inspection_step)
    operation_ref, operation_relative = stage_input("inspect_repaired_mesh.py", operation, "passive_exact_mesh_inspection")
    mount = inspection["configuration"]["workspace_mount"].rstrip("/")
    output = output_root + "/mesh-inspection-evidence.json"
    config = {"workspace_root": mount, "source": source, "repaired": repaired, "preview": preview,
              "output": output, "policy": policy,
              "measure_handle_features": prepared["binding"]["scenario_id"] == "printed-replacement-part-02"}
    code = ("import hashlib\nfrom pathlib import Path\n"
            f"raw=Path({str(PurePosixPath(mount) / operation_relative)!r}).read_bytes()\n"
            f"assert hashlib.sha256(raw).hexdigest()=={helpers.digest(operation)!r}\n"
            "namespace={'__name__':'passive_mesh_inspection'}\n"
            "exec(compile(raw,'inspect_repaired_mesh.py','exec'),namespace)\n"
            f"print(namespace['run']({config!r}))\n")
    inspector = inspection["tool"]
    inspection_step["fields"].update(step_type="work", performed_by="configured_tool", prompt="", tool=None, reusable_step=None,
        outputs=[helpers.port(inspection_step["id"] + "_result"), helpers.port("mesh_evidence", "workspace_file")])
    inspection_step["fields"]["settings"] = {
        "authoring_template": "mcp-tool", "mcp_server": inspector["server_id"], "mcp_tool": inspector["name"],
        "mcp_schema_digest": inspector["schema_digest"],
        "mcp_arguments": json.dumps({"solver": inspection["configuration"]["backend"], "input_content": code,
                                      "job_name": str(PurePosixPath(mount) / output_root / "mesh-inspection"), "critic_approved": False}),
        "timeout_seconds": 600, "output_format": "json", "save_output": True,
        "output_filename": output_root + "/mesh-inspection-provider-result.json", "file_policy": "overwrite",
        "expected_files": output, "expected_file_ports": {"mesh_evidence": output}, "mcp_file_dependencies": {},
    }
    for name, ref, relative in (("source", upstream, source), ("repaired", step["id"] + ".repaired_mesh", repaired),
                                ("preview", step["id"] + ".geometry_preview", preview),
                                ("operation", operation_ref, operation_relative), ("policy", policy_ref, policy_relative)):
        helpers.add_reference(sections, ref, inspection_step, name, "workspace_file")
        inspection_step["fields"]["settings"]["mcp_file_dependencies"][inspection_step["id"] + "_" + name] = relative
    sections.append({"kind": "connection", "id": "mesh_inspection_order_" + step["id"],
                     "fields": {"type": "order", "from": step["id"], "to": inspection_step["id"], "when": None, "label": "verify actual geometry before slicing"}})
    profile = validation_profile(policy, policy_path=policy_relative, policy_sha256=helpers.digest(policy_bytes),
                                 operation_path=operation_relative, operation_sha256=helpers.digest(operation),
                                 handle=config["measure_handle_features"])
    profile_bytes = (profile.model_dump_json(indent=2) + "\n").encode()
    profile_path = input_root + "/mesh-validation-profile.json"
    helpers.write_once(helpers.confined(root, profile_path), profile_bytes)
    staged.append({"path": profile_path, "sha256": helpers.digest(profile_bytes), "size_bytes": len(profile_bytes), "kind": "original_policy_validator_configuration"})
    gate_id = "validate_repaired_mesh_" + step["id"]
    gate = {"kind": "task", "id": gate_id,
            "fields": {"name": "Validate exact repaired geometry before slicing",
                       "purpose": "Existing 082 validator enforces original geometry requirements on exact native STL and inspection subjects",
                       "step_type": "work", "performed_by": "configured_tool", "group": None,
                       "inputs": [], "outputs": [helpers.port(gate_id + "_assessment")], "prompt": "", "tool": None, "reusable_step": None,
                       "settings": {"authoring_template": "process-validator", "output_format": "json", "max_revisions": 0,
                                    "validation": {"profile": {"source": "workspace", "name": profile_path,
                                                               "reference": profile.reference().model_dump(mode="json")},
                                                   "baseline": profile.baseline.reference().model_dump(mode="json"),
                                                   "subjects": {"repaired_mesh": gate_id + "_repaired_mesh", "mesh_evidence": gate_id + "_mesh_evidence"},
                                                   "budget": {"max_entities": 240000, "max_bytes": 16*1024*1024, "timeout_seconds": 120, "memory_limit_mb": 512}}}}}
    sections.append(gate)
    helpers.add_reference(sections, step["id"] + ".repaired_mesh", gate, "repaired_mesh", "workspace_file")
    helpers.add_reference(sections, inspection_step["id"] + ".mesh_evidence", gate, "mesh_evidence", "workspace_file")
    sections.append({"kind": "connection", "id": "mesh_validator_order_" + step["id"],
                     "fields": {"type": "order", "from": inspection_step["id"], "to": gate["id"], "when": None,
                                "label": "backend validation controls downstream permission"}})
    return {"binding_sha256": prepared["binding_sha256"], "selected_tool": choice,
            "arguments_sha256": helpers.digest(prepared["arguments"]), "arguments_source": prepared["arguments_source"],
            "arguments_staged": arguments_relative, "policy_sha256": helpers.digest(policy_bytes),
            "inspection_source_sha256": hashlib.sha256(operation).hexdigest(), "inspection_step": inspection_step,
            "validation_step_id": gate["id"], "validation_profile": profile.reference().model_dump(mode="json"),
            "feature_reference": inspection_step["id"] + ".mesh_evidence", "vendor_implementation": "independent_provider",
            "engineering_acceptance": False}
