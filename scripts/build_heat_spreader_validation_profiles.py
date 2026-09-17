"""Build full-scope heat-spreader profiles from frozen baselines."""

from __future__ import annotations

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
    "heat-spreader-sizing-01": {
        "length": 100.0,
        "thickness": 2.0,
        "conductivity": 200.0,
        "heat": 4.0,
        "cold": 25.0,
        "limit": 45.0,
        "contact": 0.0,
        "selected": "revision_60",
        "candidates": [("baseline_40", 40.0, False), ("revision_60", 60.0, True)],
    },
    "heat-spreader-sizing-02": {
        "length": 80.0,
        "thickness": 3.0,
        "conductivity": 167.0,
        "heat": 9.0,
        "cold": 30.0,
        "limit": 56.0,
        "contact": 0.0,
        "selected": "wide_60",
        "candidates": [
            ("narrow_30", 30.0, False),
            ("middle_45", 45.0, False),
            ("wide_60", 60.0, True),
        ],
    },
    "heat-spreader-sizing-03": {
        "length": 120.0,
        "thickness": 2.0,
        "conductivity": 385.0,
        "heat": 18.0,
        "cold": 35.0,
        "limit": 75.0,
        "contact": 0.15,
        "selected": "copper_80",
        "candidates": [
            ("copper_60", 60.0, False),
            ("copper_80", 80.0, True),
            ("copper_100", 100.0, True),
        ],
    },
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
    baseline = load_baseline(scenario_id)
    prefix = "HEAT" + scenario_id[-2:]
    ids = {item.id for item in baseline.requirements}

    def rid(suffix):
        value = prefix + "-" + suffix
        if value not in ids:
            raise ValueError(value)
        return value

    checks = []
    field_roles = []
    selection_cases = []
    for case_id, width, passes in config["candidates"]:
        dimensions = [config["length"], width, config["thickness"]]
        geometry_role = case_id + "_geometry"
        for axis, target in zip(("x", "y", "z"), dimensions, strict=True):
            checks.append(
                check(
                    f"{case_id}-geometry-{axis}",
                    [rid("GEOMETRY"), rid("DELIVERABLES")],
                    geometry_role,
                    reader="step-bounding-box",
                    selector=f"box/{axis}_span_mm",
                    constraint={
                        "operator": "within",
                        "target": target,
                        "tolerance": 1e-6,
                    },
                    unit="mm",
                    method="native_inspection",
                )
            )
        parameters = {
            "dimensions_mm": dimensions,
            "length_mm": config["length"],
            "width_mm": width,
            "thickness_mm": config["thickness"],
            "conductivity_w_mk": config["conductivity"],
            "heat_input_w": config["heat"],
            "cold_temperature_c": config["cold"],
            "contact_resistance_k_w": config["contact"],
        }
        coarse, fine = case_id + "_coarse", case_id + "_fine"
        field_roles.extend((coarse, fine))
        for role in (coarse, fine):
            checks.extend(
                [
                    check(
                        f"{role}-field",
                        [rid("FIELDS"), rid("DELIVERABLES")],
                        role,
                        reader="thermal-field",
                        selector="field/node_count",
                        constraint={"operator": "range", "minimum": 2},
                        unit="1",
                        method="independent_measurement",
                        parameters={**parameters, "operation": "field_nodes"},
                    ),
                    check(
                        f"{role}-analytical",
                        [rid("ANALYTICAL")],
                        role,
                        reader="thermal-field",
                        selector="field/analytical_relative_rise_error",
                        constraint={"operator": "range", "maximum": 0.02},
                        unit="1",
                        method="independent_measurement",
                        parameters={
                            **parameters,
                            "operation": "analytical_relative_error",
                        },
                    ),
                ]
            )
        checks.extend(
            [
                check(
                    f"{case_id}-balance",
                    [rid("BALANCE")],
                    fine,
                    reader="thermal-field",
                    selector="field/relative_heat_imbalance",
                    constraint={"operator": "range", "maximum": 0.01},
                    unit="1",
                    method="independent_measurement",
                    parameters={**parameters, "operation": "heat_balance_relative"},
                ),
                check(
                    f"{case_id}-refinement",
                    [rid("REFINEMENT")],
                    fine,
                    reader="thermal-field",
                    selector="field/refinement_relative_sensitivity",
                    constraint={"operator": "range", "maximum": 0.02},
                    unit="1",
                    method="independent_measurement",
                    parameters={
                        **parameters,
                        "operation": "refinement_relative",
                        "coarse_role": coarse,
                        "related_roles": [coarse],
                    },
                ),
            ]
        )
        outcome_requirement = (
            "OUTCOME-40"
            if scenario_id.endswith("01") and not passes
            else "OUTCOME-60"
            if scenario_id.endswith("01")
            else "OUTCOMES"
        )
        bound = (
            {"operator": "range", "maximum": config["limit"]}
            if passes
            else {"operator": "range", "minimum": config["limit"], "inclusive": False}
        )
        checks.append(
            check(
                f"{case_id}-outcome",
                [rid(outcome_requirement)],
                fine,
                reader="thermal-field",
                selector="field/maximum_temperature_c",
                constraint=bound,
                unit="degC",
                method="independent_measurement",
                parameters={**parameters, "operation": "maximum_temperature"},
            )
        )
        selection_cases.append(
            {
                "id": case_id,
                "role": fine,
                "width_mm": width,
                "dimensions_mm": dimensions,
            }
        )
    checks.append(
        check(
            "candidate-selection",
            [rid("SELECTION")],
            "decision",
            reader="thermal-field",
            selector="decision/selected_case_id",
            constraint={"operator": "equals", "expected": config["selected"]},
            method="independent_measurement",
            parameters={
                "operation": "selection",
                "temperature_limit_c": config["limit"],
                "cases": selection_cases,
                "related_roles": [item["role"] for item in selection_cases],
            },
        )
    )
    review_requirements = [rid("BOUNDARIES"), rid("MATERIAL"), rid("CLAIM-SCOPE")]
    if scenario_id.endswith("03"):
        review_requirements.extend([rid("CONTACT"), rid("REVIEW")])
        checks.append(
            check(
                "supported-contact-model",
                [rid("UNSUPPORTED-DISPOSITION")],
                "decision",
                selector="/status",
                constraint={"operator": "equals", "expected": "candidate_selected"},
            )
        )
    checks.extend(
        [
            check(
                "basis-review",
                review_requirements,
                "basis",
                constraint={"operator": "review"},
                method="human_review",
            ),
            check("deliverable-decision", [rid("DELIVERABLES")], "decision"),
            check("deliverable-basis", [rid("DELIVERABLES")], "basis"),
        ]
    )
    return ValidationProfile.model_validate(
        {
            "id": scenario_id + "-full",
            "version": "1",
            "baseline": baseline,
            "checks": checks,
            "excluded_scope": [],
            "limitations": [
                "Physical thermal qualification and certification remain outside this digital validation gate."
            ],
            "supported_kinds": ["file"],
        }
    )


def render():
    return {
        DESTINATION / (scenario_id + "-full.json"): (
            canonical_json(build(scenario_id, config)) + "\n"
        ).encode()
        for scenario_id, config in CONFIG.items()
    }


if __name__ == "__main__":
    for path, data in render().items():
        path.write_bytes(data)
    print(json.dumps({"profiles": len(CONFIG)}))
