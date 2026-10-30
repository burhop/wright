"""Explicit scenario selection and versioned authored instruction assets."""
import json
from pathlib import Path


WHEEL = "printed-replacement-part-01"
HANDLE = "printed-replacement-part-02"


def load(repo, bindings):
    identity = bindings.get("scenario_id", WHEEL)
    if identity not in (WHEEL, HANDLE):
        raise ValueError("Unsupported printed-part scenario_id")
    if identity == WHEEL:
        cases = json.loads((repo / "examples/process-interfaces/proof-bindings.json").read_bytes())
        return next(item for item in cases["cases"] if item["scenario_id"] == identity), None
    folder = Path(__file__).with_name("scenarios")
    manifest = json.loads((folder / (identity + ".json")).read_bytes())
    raw = (folder / manifest["instructions"]).read_bytes()
    instructions = json.loads(raw)
    if instructions["scenario_id"] != identity or instructions["version"] != "1":
        raise ValueError("Handle instruction identity changed")
    if bindings.get("orientation_comparison") is not True:
        raise ValueError("The handle requires orientation_comparison=true")
    if not bindings.get("run_path_template"):
        raise ValueError("The handle study requires explicit reusable run paths")
    if "native_inspection_operation" in bindings or "retained_geometry_source" in bindings:
        raise ValueError("Wheel-specific native inspection/retained source is not a handle binding")
    return manifest, (raw, instructions)


def apply(flow, frozen, asset, *, basis, basis_review, create, repair, report,
          final_review, qualified, configured_construction, configured_repair):
    """Write authored bodies into the proposal, not runtime policy literals."""
    raw, instructions = asset
    reference = flow.input_bytes(
        "scenario-instructions.json", raw,
        original=str(Path(__file__).with_name("scenarios") / frozen["instructions"]),
    )
    identity = flow.input_bytes(
        "scenario-binding.json", (json.dumps(frozen, indent=2) + "\n").encode(),
    )
    values = {key: str(flow.workspace / flow.output / name)
              for key, name in (("source_mesh", "source_mesh.stl"),
                                ("repaired_mesh", "repaired_mesh.stl"),
                                ("mesh_preview", "mesh-preview.png"))}
    for stage, title in ((basis, "Interpret the original drawer-handle requirements"),
                         (basis_review, "Review handle dimensions and proposed construction")):
        stage["fields"]["name"] = stage["fields"]["purpose"] = title
    for stage, key in ((basis, "basis"), (create, "create"), (repair, "repair"), (report, "report")):
        if stage["fields"]["performed_by"] == "ai_assisted":
            body = instructions[key].format(**values)
            if qualified:
                addition = {"basis": "qualified_basis", "create": "configured_construction",
                            "repair": "configured_repair"}.get(key)
                if addition:
                    body += "\n" + instructions[addition]
            stage["fields"]["prompt"] = body
            flow.reference(reference, stage, "authored_scenario_instructions")
    basis_review["fields"]["instructions"] = instructions["basis_review"]
    if configured_construction or configured_repair:
        basis_review["fields"]["instructions"] += "\n" + instructions["configured_review"]
    final_review["fields"]["instructions"] = instructions["final_review"]
    flow.reference(identity, basis_review, "scenario_origin")
    flow.reference(reference, basis_review, "authored_scenario_instructions")
    flow.reference(reference, final_review, "authored_scenario_instructions")
    return instructions
