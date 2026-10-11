"""Optional exact CAD/drawing handoff using existing MCP and validation stages.

These are example declarations, never another executor. The independent provider
does the native work; Wright freezes and checks its actual output dependencies.
"""

import hashlib
import json
from pathlib import Path

from core.process_validation import ValidationProfile


OUTPUTS = {
    "measurements": "engineering-measurements.json",
    "drawing_native": "inspection-drawing.FCStd",
    "drawing_svg": "inspection-drawing.svg",
    "drawing_pdf": "inspection-drawing.pdf",
    "drawing_preview": "inspection-drawing.png",
    "matrix": "requirements-matrix.md",
}
INPUT_ROLES = ("native_cad", "neutral_cad", "source_mesh")


def qualify(binding, construction, *, configured, retained):
    if retained or not configured or not set(INPUT_ROLES) <= construction["outputs"].keys():
        raise ValueError("Native inspection requires the declared current native CAD, STEP and mesh producer")
    if (
        not isinstance(binding, dict)
        or set(binding) != {"server", "tool", "arguments_file"}
        or any(not isinstance(binding[key], str) or not binding[key].strip()
               for key in ("server", "tool"))
    ):
        raise ValueError("Declare the independent native-inspection server, tool and pinned arguments")
    reference = binding["arguments_file"]
    if not isinstance(reference, dict) or set(reference) != {"path", "sha256"}:
        raise ValueError("Pin native-inspection arguments by path and SHA256")
    path = Path(reference["path"])
    if not path.is_file() or path.stat().st_size > 65536:
        raise ValueError("Native-inspection arguments must be a bounded regular file")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != reference["sha256"]:
        raise ValueError("Native-inspection arguments changed")
    if not isinstance(json.loads(raw), dict):
        raise ValueError("Supply the selected native-inspection tool arguments")
    profile_raw = Path(__file__).with_name("native-inspection-profile.json").read_bytes()
    profile = ValidationProfile.model_validate_json(profile_raw)
    return binding, raw, profile_raw, profile


def add(flow, definition, qualified, create, construction):
    binding, raw, profile_raw, profile = qualified
    arguments = flow.input_bytes(
        "native-inspection-arguments.json", raw,
        original=binding["arguments_file"]["path"],
        run_paths=bool(flow.run_path_template),
    )
    inspect = flow.stage("inspect_native_and_draw", "Measure native CAD and prepare the wheel inspection drawing")
    argument_port = flow.reference(arguments, inspect, "exact_arguments")
    flow.exact_mcp(
        inspect, flow.select(binding["server"], binding["tool"]),
        argument_port, tuple(OUTPUTS.values()), "native-inspection-provider-response.json",
    )
    dependencies = {}
    for role in INPUT_ROLES:
        key = flow.reference(create["id"] + "." + role, inspect, role, "workspace_file")
        dependencies[key] = flow.output + "/" + construction["outputs"][role]
    inspect["fields"]["settings"]["mcp_file_dependencies"] = dependencies
    flow.file_outputs(inspect, {role: flow.output + "/" + name for role, name in OUTPUTS.items()})

    profile_name = "native-inspection-profile.json"
    profile_ref = flow.input_bytes(profile_name, profile_raw, kind="workspace_file")
    gate = flow.stage("validate_native_inspection", "Check measured CAD, mesh correspondence and linked drawing dimensions")
    subject = flow.reference(inspect["id"] + ".measurements", gate, "inspection", "workspace_file")
    gate["fields"]["prompt"] = ""
    gate["fields"]["outputs"] = [definition.port("native_inspection_assessment")]
    gate["fields"]["settings"] = {
        "authoring_template": "process-validator", "max_revisions": 0,
        "validation": {
            "profile": {"source": "workspace", "name": flow.input_root + "/" + profile_name,
                        "reference": profile.reference().model_dump()},
            "baseline": profile.baseline.reference().model_dump(),
            "subjects": {"inspection": subject},
        },
    }
    review_refs = [(inspect["id"] + "." + role, "native_" + role, "workspace_file")
                   for role in OUTPUTS]
    review_refs.extend([(gate["id"] + ".native_inspection_assessment", "native_assessment", "engineering_document"),
                        (profile_ref, "native_inspection_criteria", "workspace_file")])
    return [inspect, gate], review_refs
