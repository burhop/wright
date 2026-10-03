"""Declare external slicing and passive evidence stages; never run a provider.

The operator supplies exact registered tools, arguments, mounted paths and pinned
profiles. This file contains no slicer executable, profile derivation, device
protocol or fallback implementation. Existing source/runtime contracts execute
the resulting stages and retain their evidence.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "external_slice_declarations", ROOT / "scripts/engineering_campaign_binding_helpers.py"
)
helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(helpers)


def _resolve(value, replacements):
    if isinstance(value, str):
        if value in replacements:
            return replacements[value]
        if "{source}" in value or "{package}" in value:
            raise ValueError("Use complete explicit path placeholders")
        return value
    if isinstance(value, dict):
        return {key: _resolve(item, replacements) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve(item, replacements) for item in value]
    return value


def preflight(binding_path, scenario, tools, expected_process):
    try:
        return _preflight(binding_path, scenario, tools, expected_process)
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError("Complete the explicit external slicer, retention, inspection and profile binding before preparation") from error


def _preflight(binding_path, scenario, tools, expected_process):
    """Resolve required choices before any staging or native initialization."""
    if not binding_path:
        raise ValueError("Supply --slicer-binding for an independent offline provider; embedded slicers are retired")
    raw = Path(binding_path).read_bytes()
    if len(raw) > 65536:
        raise ValueError("External slicer binding exceeds its input bound")
    binding = json.loads(raw)
    if binding.get("schema_version") != 1 or binding.get("scenario_id") != scenario:
        raise ValueError("External slicer binding must identify this exact scenario")
    rows = list(tools.values()) if isinstance(tools, dict) else tools
    selected = {}
    for role in ("slicer", "files", "inspection"):
        choice = binding[role]
        matches = [row for row in rows if row.get("server_id") == choice["server"]
                   and row.get("tool_name") == choice["tool"]
                   and row.get("schema_digest") == choice["schema_digest"]]
        if len(matches) != 1 or not choice["schema_digest"]:
            raise ValueError("Required external binding missing, ambiguous or changed: " + role)
        if choice["server"] in {"wright-printed-part-slicer", "wright-drill-jig-slicer"}:
            raise ValueError("Select an independently installed slicer provider")
        selected[role] = matches[0]
    if binding["files"]["tool"] != "write_text_document" or binding["inspection"]["tool"] != "run_simulation":
        raise ValueError("Select the existing file-retention and engineering inspection contracts")
    if not isinstance(binding["inspection"]["backend"], str) or not binding["inspection"]["backend"].strip():
        raise ValueError("Declare the qualified inspection backend")
    mount = binding["inspection"]["workspace_mount"]
    if not isinstance(mount, str) or not mount.startswith("/") or "\\" in mount or ".." in mount.split("/"):
        raise ValueError("Declare the inspection provider's absolute workspace mount")
    for field in ("success_field", "success_contract", "gcode_entry"):
        if not isinstance(binding.get(field), str) or not binding[field].strip():
            raise ValueError("Declare the qualified provider's " + field)
    arguments = binding["slicer"]["arguments"]
    if not isinstance(arguments, dict) or "{source}" not in arguments.values() or "{package}" not in arguments.values():
        raise ValueError("Bind the actual source and package arguments explicitly")
    expected = binding["expected_response_fields"]
    if not isinstance(expected, dict) or "{source}" not in expected.values() or "{package}" not in expected.values():
        raise ValueError("Qualified success must identify the actual source and package")
    _resolve(arguments, {"{source}": "preflight-source", "{package}": "preflight-package"})
    _resolve(expected, {"{source}": "preflight-source", "{package}": "preflight-package"})
    json.dumps(arguments, allow_nan=False)
    if "nominal_layer_section" in binding and binding["nominal_layer_section"] is not None:
        # The existing reader remains the authority for actual section semantics;
        # readiness checks the explicit object shape, never invents boundaries.
        section = binding["nominal_layer_section"]
        if not isinstance(section, dict) or set(section) != {"start_marker", "end_marker"} or any(
            not isinstance(marker, str) or not marker.startswith(";") or len(marker) > 256
            or "\n" in marker or "\r" in marker for marker in section.values()
        ):
            raise ValueError("Declare the existing reader's explicit nominal section object")
    profiles = binding["profiles"]
    if set(profiles) != {"machine", "filament", "process"}:
        raise ValueError("Pin exactly the three actually configured profiles")
    profile_bytes = {}
    for role, reference in profiles.items():
        path = Path(reference["path"])
        if not path.is_file() or not 0 < path.stat().st_size <= 1024 * 1024:
            raise ValueError("Configured profile must be a bounded regular file: " + role)
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != reference["sha256"]:
            raise ValueError("Configured profile changed: " + role)
        value = json.loads(data)
        if not isinstance(value, dict):
            raise ValueError("Configured profile must be a JSON object")
        if role == "process" and any(value.get(key) != expected_value for key, expected_value in expected_process.items() if key != "base"):
            raise ValueError("Configured process changes the original engineering assignment")
        profile_bytes[role] = data
    return binding, selected, profile_bytes, hashlib.sha256(raw).hexdigest()


def bind(sections, step, upstream, *, workspace, input_root, output_root, source,
         prepared, staged, operation_label):
    """Keep the original evidence stage, inserting external slice/retention first."""
    binding, selected, profile_bytes, binding_digest = prepared
    root = Path(workspace).resolve()
    # The source's concrete path belongs to the slicer's configured host. The
    # separate inspection mount is supplied explicitly; it is never inferred.
    package = output_root + "/slice_package.gcode.3mf"
    replacements = {"{source}": str(helpers.confined(root, source)),
                    "{package}": str(helpers.confined(root, package))}

    def resolve(value):
        return _resolve(value, replacements)

    def stage(prefix, title):
        item = {"kind": "task", "id": prefix + "_" + step["id"],
                "fields": {"name": title, "purpose": title, "group": None, "inputs": [],
                           "outputs": [], "settings": {}}}
        sections.append(item)
        return item

    def exact(item, choice, arguments, filename, outputs):
        item["fields"].update(step_type="work", performed_by="configured_tool", prompt="",
            tool=None, reusable_step=None,
            outputs=[helpers.port(item["id"] + "_result"),
                     *[helpers.port(role, "workspace_file") for role in outputs]])
        item["fields"]["settings"] = {
            "authoring_template": "mcp-tool", "mcp_server": choice["server_id"],
            "mcp_tool": choice["name"], "mcp_schema_digest": choice["schema_digest"],
            "mcp_arguments": json.dumps(arguments, separators=(",", ":")),
            "timeout_seconds": 600, "output_format": "json", "save_output": True,
            "output_filename": output_root + "/" + filename, "file_policy": "overwrite",
            "expected_files": "\n".join(outputs.values()), "expected_file_ports": outputs,
        }

    def input_file(name, data):
        relative = input_root + "/" + name
        helpers.write_once(helpers.confined(root, relative), data)
        staged.append({"path": relative, "sha256": helpers.digest(data),
                       "size_bytes": len(data), "role": "external_slice_inspection_input"})
        reference = helpers.add_file_input(sections, step["id"], name.replace(".", "_").replace("-", "_"), relative)
        sections[-1]["fields"]["outputs"][0]["kind"] = "workspace_file"
        return reference, relative

    helpers.confined(root, output_root).mkdir(parents=True, exist_ok=True)
    slice_step = stage("invoke_external_slice", "Slice the actual upstream geometry with the selected independent provider")
    exact(slice_step, selected["slicer"], resolve(binding["slicer"]["arguments"]),
          "slicer-execution.json", {"external_slice_package": package})
    source_port = "selected_geometry"
    slice_step["fields"]["inputs"].append(helpers.port(source_port, "workspace_file"))
    slice_step["fields"]["settings"]["mcp_file_dependencies"] = {source_port: source}
    sections.append({"kind": "connection", "id": "slice_geometry_" + step["id"],
                     "fields": {"type": "item", "from": upstream, "to": slice_step["id"] + "." + source_port,
                                "label": "actual same-attempt geometry", "when": None}})
    response = stage("retain_slice_response", "Retain the actual external provider response")
    response_path = output_root + "/slice-provider-response.json"
    exact(response, selected["files"], {"relativePath": response_path, "mediaType": "application/json", "overwrite": False},
          "response-retention-receipt.json", {"provider_response": response_path})
    helpers.add_reference(sections, slice_step["id"] + "." + slice_step["id"] + "_result", response, "actual_response")
    response["fields"]["settings"].update(mcp_arguments_source="fields", mcp_argument_ports=json.dumps({response["id"] + "_actual_response": "content"}))
    profile_paths = {}
    references = []
    for role, data in profile_bytes.items():
        reference, relative = input_file(role + "-profile.json", data)
        references.append((role + "_profile_input", reference, relative))
        profile_paths[role] = relative
        key = role + "_profile_input"
        helpers.add_reference(sections, reference, slice_step, key, "workspace_file")
        slice_step["fields"]["settings"]["mcp_file_dependencies"][slice_step["id"] + "_" + key] = relative
    reader_path = ROOT / "packages/workspace_service/src/workspace_service/process_interfaces/representations.py"
    operation_path = ROOT / "scripts/engineering/inspect_manufacturing_package.py"
    reader, operation = reader_path.read_bytes(), operation_path.read_bytes()
    reader_ref, reader_relative = input_file("passive-representations.py", reader)
    operation_ref, operation_relative = input_file("inspect_manufacturing_package.py", operation)
    references.extend((("reader", reader_ref, reader_relative), ("operation", operation_ref, operation_relative)))
    mount = binding["inspection"]["workspace_mount"].rstrip("/")
    config = {"workspace_root": mount, "source_mesh": source, "slice_package": package,
              "provider_response": response_path, "output_root": output_root,
              "profiles": profile_paths, "gcode_entry": binding["gcode_entry"],
              "success_field": binding["success_field"], "success_contract": binding["success_contract"],
              "expected_response_fields": resolve(binding["expected_response_fields"]),
              "operation_label": operation_label, "legacy_previews": True,
              "nominal_layer_section": binding.get("nominal_layer_section")}
    input_content = (
        "import hashlib\nfrom pathlib import Path\n"
        f"reader=Path({str(PurePosixPath(mount) / reader_relative)!r}).read_bytes()\n"
        f"assert hashlib.sha256(reader).hexdigest()=={helpers.digest(reader)!r}\n"
        f"operation=Path({str(PurePosixPath(mount) / operation_relative)!r}).read_bytes()\n"
        f"assert hashlib.sha256(operation).hexdigest()=={helpers.digest(operation)!r}\n"
        "reader_namespace={'__name__':'passive_reader'}\noperation_namespace={'__name__':'package_inspection'}\n"
        "exec(compile(reader,'passive-representations.py','exec'),reader_namespace)\n"
        "exec(compile(operation,'inspect_manufacturing_package.py','exec'),operation_namespace)\n"
        f"print(operation_namespace['run']({config!r},reader_namespace['read_3mf_toolpaths']))\n"
    )
    outputs = {"slice_package": package, "slice_evidence": output_root + "/slice-evidence.json",
               "support_preview": output_root + "/support-preview.svg",
               **{role + "_profile": output_root + "/" + role + "-profile.json" for role in profile_bytes},
               "toolpath_preview": output_root + "/support-preview.json",
               "toolpath_summary": output_root + "/toolpath-summary.json",
               "slice_preview": output_root + "/slice-preview.png"}
    exact(step, selected["inspection"], {"solver": binding["inspection"]["backend"],
          "input_content": input_content, "job_name": output_root + "/package-inspection", "critic_approved": False},
          "package-inspection-result.json", outputs)
    dependencies = [("actual_package", slice_step["id"] + ".external_slice_package", package),
                    ("actual_response", response["id"] + ".provider_response", response_path),
                    ("actual_source", upstream, source), *references]
    step["fields"]["settings"]["mcp_file_dependencies"] = {}
    for key, reference, relative in dependencies:
        helpers.add_reference(sections, reference, step, key, "workspace_file")
        step["fields"]["settings"]["mcp_file_dependencies"][step["id"] + "_" + key] = relative
    for before, after in ((upstream.split(".")[0], slice_step["id"]), (slice_step["id"], response["id"]), (response["id"], step["id"])):
        sections.append({"kind": "connection", "id": "external_sequence_" + after,
                         "fields": {"type": "order", "from": before, "to": after,
                                    "label": "actual slice and retained passive inspection", "when": None}})
    return {"binding_sha256": binding_digest, "selected_tools": selected,
            "profile_sha256": {role: helpers.digest(data) for role, data in profile_bytes.items()},
            "vendor_implementation": "independent_provider",
            "inspection": "passive_actual_package", "engineering_acceptance": False}
