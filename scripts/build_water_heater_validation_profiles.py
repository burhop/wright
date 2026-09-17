"""Build full-scope water-heater profiles from frozen baselines."""

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
    baseline = load_baseline(scenario_id)
    prefix = "WATER" + scenario_id[-2:]
    known = {item.id for item in baseline.requirements}

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
    ]
    for role in ("timeline", "comparison", "energy", "curve", "report", "parameters"):
        checks.append(check("deliverable-" + role, [rid("DELIVERABLES")], role))
    review_ids = {
        requirement_id
        for item in checks
        if item["constraint"]["operator"] == "review"
        for requirement_id in item["requirement_ids"]
    }
    baseline = baseline.model_dump(mode="json")
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
