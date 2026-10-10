"""Pure source fixtures for varied final UI/software proofs; no execution."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from packages.workspace_service.tests.test_process_first_human_input import first_input_source
from packages.workspace_service.tests.test_process_conditional_human_input import conditional_source
from packages.workspace_service.tests.test_workflow_artifact_review import section
from workspace_service.workflow_source_execution import _parse, compile_prompt_workflow


def generate(initial: bool):
    blocks = _parse(first_input_source() if initial else conditional_source())
    name = "Plate mass with declared thickness input" if initial else "Resolved plate mass without a question"
    for block in blocks:
        fields = block["fields"]
        if block["kind"] == "workflow":
            fields.update(name=name, purpose="Isolated software calculation proof. Dimensions and densities are supplied requirements; no strength, fit or manufacturing acceptance claim.")
        if block["kind"] == "input":
            fields["settings"]["interaction_input"]["default"] = "Compare identical 60 mm x 25 mm x 4 mm rectangular plates. Steel density 7850 kg/m3, aluminum density 2700 kg/m3. Explicit focus a=steel."
        if block["id"] == "first":
            fields.update(name="Confirm supplied material focus", prompt='Output only a requirements-resolution JSON object with version "wright.requirements-resolution/1", unresolved_fields [], resolved_values {"selection":"a"}. Selection a=steel is explicitly supplied. Preserve it, and do not ask questions.')
            fields["settings"].update(output_filename="resolved-material-focus.json")
        if block["id"] == "choice":
            declaration = fields["settings"]["human_interaction"]
            fields.update(name="Choose plate calculation inputs")
            declaration["instructions"] = "This software input supplies material focus and thickness only; it does not approve a design."
            if initial:
                declaration["response_schema"] = {
                    "type": "object", "additionalProperties": False,
                    "properties": {
                        "selection": {"type": "string", "enum": ["steel", "aluminum"], "title": "Material focus"},
                        "thickness_mm": {"type": "number", "minimum": 1, "maximum": 8, "title": "Thickness (mm)"},
                    },
                    "required": ["selection", "thickness_mm"],
                }
        if block["kind"] == "task" and fields.get("performed_by") == "ai_assisted" and block["id"] != "first":
            fields.update(name="Calculate comparative plate masses", prompt=(
                "Use the supplied structured answer. Calculate volume and mass only of identical rectangular solid plates, "
                + ("80 mm x 40 mm with the supplied thickness_mm in millimeters; selection is steel or aluminum. " if initial else "60 mm x 25 mm x 4 mm; selection a=steel or b=aluminum. ")
                + "Steel density is 7850 kg/m3; aluminum density is 2700 kg/m3. Preserve every supplied value. Show unit conversions, volume in m3, both masses in grams, and chosen focus. Do not ask questions or claim verified strength, fit or manufacturing feasibility."
            ))
            fields["settings"].update(output_format="text", output_filename="comparative-plate-masses.txt")
    source = "".join(section(block["kind"], block["id"], **block["fields"]) for block in blocks)
    compile_prompt_workflow(source)
    return source


if __name__ == "__main__":
    target = Path(sys.argv[1])
    target.mkdir(parents=True, exist_ok=True)
    for initial, slug in [(True, "first-input"), (False, "resolved-conditional")]:
        (target / (slug + ".workflow.wflow")).write_text(generate(initial), encoding="utf-8")
    (target / "expected-results.json").write_text(json.dumps({
        "first-input": {"answer": {"selection": "aluminum", "thickness_mm": 3}, "volume_m3": 0.0000096, "steel_mass_g": 75.36, "aluminum_mass_g": 25.92},
        "resolved-conditional": {"selection": "a", "volume_m3": 0.000006, "steel_mass_g": 47.1, "aluminum_mass_g": 16.2},
        "integration_test": True, "engineering_acceptance": False,
    }, indent=2), encoding="utf-8")
    print(json.dumps({"fixtures": str(target), "executions": 0}))
