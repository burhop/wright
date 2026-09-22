"""Build full-scope water-heater profiles from frozen baselines."""

import hashlib
import json
from pathlib import Path

from core.process_validation import ValidationProfile, canonical_json
from workspace_service.process_validation.baselines import load_baseline


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = (
    ROOT
    / "packages/workspace_service/src/workspace_service/process_validation/profiles"
)
CONFIG = {
    "water-heater-sizing-01": dict(
        powers=[350, 500, 700],
        losses=["nominal"],
        efficiency=0.92,
        horizon=300,
        limit=180,
        selected=700,
    ),
    "water-heater-sizing-02": dict(
        powers=[400, 600, 800],
        losses=["nominal"],
        efficiency=0.93,
        horizon=600,
        limit=360,
        selected=600,
    ),
    "water-heater-sizing-03": dict(
        powers=[1200, 1500, 1800],
        losses=["low", "nominal", "high"],
        efficiency=0.94,
        horizon=700,
        limit=400,
        selected=1500,
    ),
}


def check(
    identifier,
    requirement_ids,
    role,
    reader="structured",
    selector="",
    constraint=None,
    unit=None,
    method="structured_value",
    parameters=None,
):
    return {
        "id": identifier,
        "version": "1",
        "requirement_ids": requirement_ids,
        "subject_role": role,
        "reader": reader,
        "selector": selector,
        "constraint": constraint or {"operator": "exists"},
        "unit": unit,
        "frame": None,
        "evidence_method": method,
        "parameters": parameters or {},
        "applicability_reason": None,
    }


def build(scenario_id, config):
    baseline = load_baseline(scenario_id).model_dump(mode="json")
    prefix = "WATER" + scenario_id[-2:]
    approved_path = (
        ROOT
        / "specs/082-output-content-validation/campaign-example-renewal-engineering-input-proposal.json"
    )
    approved_document = json.loads(approved_path.read_text(encoding="utf-8"))
    approved_case = next(
        item for item in approved_document["cases"] if item["scenario_id"] == scenario_id
    )
    fixed = approved_case["new_fixed_requirements"]
    source = {
        "artifact_ref": approved_path.relative_to(ROOT).as_posix(),
        "locator": "cases/" + scenario_id + "/new_fixed_requirements",
        "sha256": hashlib.sha256(approved_path.read_bytes()).hexdigest(),
    }
    additions = {
        "PACKAGE-CONTRACT": "The CAD package preserves every approved vessel, heater, insulation, envelope, mounting, keepout, material, temperature and mass requirement; only the explicitly permitted geometry choices may vary.",
        "PACKAGE-CORRESPONDENCE": "The final CAD STEP, its reopened measurements, the selected Modelica power and the downstream scikit-fem fields retain exact same-attempt identity correspondence.",
        "PACKAGE-THERMAL": "The selected package passes the approved maximum carrier and accessible-shell temperature limits using the selected demonstrated power and declared material/film inputs.",
        "PACKAGE-DELIVERABLES": "The final design package contains the exact CAD STEP, CAD measurements, thermal field and evidence-linked package verification.",
    }
    baseline["requirements"].extend(
        {
            "id": prefix + "-" + suffix,
            "text": text,
            "mandatory": True,
            "scope": "design" if suffix != "PACKAGE-DELIVERABLES" else "content",
            "sources": [source],
            "review_required": False,
        }
        for suffix, text in additions.items()
    )
    baseline["amendments"].append(source)
    known = {item["id"] for item in baseline["requirements"]}

    def rid(suffix):
        value = prefix + "-" + suffix
        if value not in known:
            raise ValueError(value)
        return value

    grid_requirement = "GRID" if scenario_id.endswith("03") else "CANDIDATES"
    parameters = {
        "powers_w": config["powers"],
        "loss_labels": config["losses"],
        "efficiency": config["efficiency"],
        "initial_temperature_c": 20.0,
        "target_temperature_c": 90.0,
        "time_limit_s": config["limit"],
        "horizon_s": config["horizon"],
    }
    checks = [
        check(
            "trajectory-grid",
            [
                rid(grid_requirement),
                rid("PHYSICS"),
                rid("CONTROL"),
                rid("HORIZON"),
                rid("TARGET"),
            ],
            "timeline",
            reader="water-heater-timeline",
            selector="water/grid_count",
            constraint={
                "operator": "equals",
                "expected": len(config["powers"]) * len(config["losses"]),
            },
            unit="1",
            method="independent_measurement",
            parameters={**parameters, "operation": "grid_count"},
        ),
        check(
            "candidate-selection",
            [rid("SELECTION")],
            "timeline",
            reader="water-heater-timeline",
            selector="water/selected_power",
            constraint={"operator": "equals", "expected": config["selected"]},
            unit="W",
            method="independent_measurement",
            parameters={**parameters, "operation": "selection"},
        ),
        check(
            "kit-id",
            [rid("MODEL")],
            "parameters",
            selector="/kit_id",
            constraint={"operator": "equals", "expected": "wright-water-heater-v1"},
        ),
        check(
            "kit-version",
            [rid("MODEL")],
            "parameters",
            selector="/kit_version",
            constraint={"operator": "equals", "expected": "0.1.0"},
        ),
        check(
            "energy-review",
            [
                rid("ENERGY")
                if scenario_id.endswith(("01", "03"))
                else rid("BATTERY-ENERGY")
            ],
            "energy",
            constraint={"operator": "review"},
            method="human_review",
        ),
        check(
            "refinement-review",
            [rid("REFINEMENT")],
            "comparison",
            constraint={"operator": "review"},
            method="human_review",
        ),
        check(
            "claim-review",
            [rid("CLAIM-SCOPE")],
            "report",
            constraint={"operator": "review"},
            method="human_review",
        ),
        check(
            "package-verification",
            [
                rid("PACKAGE-CORRESPONDENCE"),
                rid("PACKAGE-THERMAL"),
                rid("PACKAGE-CONTRACT"),
            ],
            "package_verification",
            reader="water-heater-timeline",
            selector="package/verified",
            constraint={"operator": "equals", "expected": True},
            method="independent_measurement",
            parameters={
                "operation": "package_verification",
                "selected_power_w": config["selected"],
                "geometry_role": "package_step",
                "measurements_role": "package_measurements",
                "field_role": "package_field",
                "comparison_role": "comparison",
                "related_roles": [
                    "package_step",
                    "package_measurements",
                    "package_field",
                    "comparison",
                ],
            },
        ),
        check(
            "package-contract-review",
            [rid("PACKAGE-CONTRACT")],
            "package_measurements",
            constraint={"operator": "review"},
            method="human_review",
        ),
    ]
    for axis, maximum in zip(("x", "y", "z"), fixed["maximum_envelope_mm"], strict=True):
        checks.append(
            check(
                "package-envelope-" + axis,
                [rid("PACKAGE-CONTRACT")],
                "package_step",
                reader="step-bounding-box",
                selector="box/" + axis + "_span_mm",
                constraint={"operator": "range", "maximum": maximum},
                unit="mm",
                method="native_inspection",
            )
        )
    for role in ("timeline", "comparison", "energy", "curve", "report", "parameters"):
        checks.append(check("deliverable-" + role, [rid("DELIVERABLES")], role))
    for role in (
        "package_measurements",
        "package_field",
        "package_verification",
    ):
        checks.append(
            check(
                "deliverable-" + role,
                [rid("PACKAGE-DELIVERABLES")],
                role,
            )
        )
    review_ids = {
        requirement_id
        for item in checks
        if item["constraint"]["operator"] == "review"
        for requirement_id in item["requirement_ids"]
    }
    for requirement in baseline["requirements"]:
        requirement["review_required"] = requirement["id"] in review_ids
    return ValidationProfile.model_validate(
        {
            "id": scenario_id + "-full",
            "version": "1",
            "baseline": baseline,
            "checks": checks,
            "excluded_scope": [],
            "limitations": [
                "Physical heater operation, safety, wiring, purchasing and certification remain outside this digital validation gate."
            ],
            "supported_kinds": ["file"],
        }
    )


def render():
    return {
        DESTINATION / (scenario_id + ".json"): (
            canonical_json(build(scenario_id, config)) + "\n"
        ).encode()
        for scenario_id, config in CONFIG.items()
    }


if __name__ == "__main__":
    for path, data in render().items():
        path.write_bytes(data)
    print(f"Wrote {len(CONFIG)} water-heater profiles")
