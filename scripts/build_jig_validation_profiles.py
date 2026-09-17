"""Build full-scope drill-jig profiles from frozen baselines."""

from pathlib import Path

from core.process_validation import ValidationProfile, canonical_json
from workspace_service.process_validation.baselines import load_baseline


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = (
    ROOT
    / "packages/workspace_service/src/workspace_service/process_validation/profiles"
)
IDENTITY = [
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, 1.0, 0.0],
    [0.0, 0.0, 0.0, 1.0],
]
CONFIG = {
    "parametric-drill-jig-01": dict(
        centers={"H1": (30, 30), "H2": (170, 30)},
        tolerance=0.2,
        body=10.2,
        body_tol=0.1,
        flange=14.3,
    ),
    "parametric-drill-jig-02": dict(
        centers={"H1": (30, 20), "H2": (30, 60), "H3": (150, 20), "H4": (150, 60)},
        tolerance=0.15,
        body=12.15,
        body_tol=0.1,
        flange=18.3,
    ),
    "parametric-drill-jig-03": dict(
        centers={
            "H1": (50, 0),
            "H2": (25, 43.301),
            "H3": (-25, 43.301),
            "H4": (-50, 0),
            "H5": (-25, -43.301),
            "H6": (25, -43.301),
        },
        tolerance=0.1,
        body=12.2,
        body_tol=0.1,
        flange=18.3,
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
    frame=None,
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
        "frame": frame,
        "evidence_method": method,
        "parameters": parameters or {},
        "applicability_reason": None,
    }


def build(scenario_id, config):
    baseline = load_baseline(scenario_id)
    prefix = "JIG" + scenario_id[-2:]
    known = {r.id for r in baseline.requirements}

    def rid(suffix):
        value = prefix + "-" + suffix
        if value not in known:
            raise ValueError(value)
        return value

    checks = []
    for hole, (x, y) in config["centers"].items():
        coordinate_requirements = (
            [rid(hole + "-X"), rid(hole + "-Y")]
            if scenario_id.endswith("01")
            else [rid(hole)]
        )
        parameters = {
            "nominal_center_mm": [float(x), float(y)],
            "nominal_diameter_mm": config["body"],
            "capture_radius_mm": 4.0,
            "radius_match_tolerance_mm": 0.08,
            "datum_transform_model_to_workpiece": IDENTITY,
        }
        for axis, target in (("x", x), ("y", y)):
            requirement = (
                [rid(hole + "-" + axis.upper())]
                if scenario_id.endswith("01")
                else coordinate_requirements
            )
            checks.append(
                check(
                    f"{hole.lower()}-{axis}",
                    requirement,
                    "jig_step",
                    reader="step-seat-geometry",
                    selector=f"seat/{hole}/center_{axis}_mm",
                    constraint={
                        "operator": "within",
                        "target": target,
                        "tolerance": config["tolerance"],
                    },
                    unit="mm",
                    frame="workpiece_datum",
                    method="native_inspection",
                    parameters=parameters,
                )
            )
        body_req = rid("BODY-SEATS") if scenario_id.endswith("01") else rid("SEATS")
        checks.append(
            check(
                f"{hole.lower()}-body",
                [body_req],
                "jig_step",
                reader="step-seat-geometry",
                selector=f"seat/{hole}/diameter_mm",
                constraint={
                    "operator": "within",
                    "target": config["body"],
                    "tolerance": config["body_tol"],
                },
                unit="mm",
                frame="workpiece_datum",
                method="native_inspection",
                parameters=parameters,
            )
        )
        flange_req = rid("FLANGE-SEATS") if scenario_id.endswith("01") else rid("SEATS")
        flange_parameters = {**parameters, "nominal_diameter_mm": config["flange"]}
        checks.append(
            check(
                f"{hole.lower()}-flange",
                [flange_req],
                "jig_step",
                reader="step-seat-geometry",
                selector=f"seat/{hole}-flange/diameter_mm",
                constraint={
                    "operator": "within",
                    "target": config["flange"],
                    "tolerance": 0.1,
                },
                unit="mm",
                frame="workpiece_datum",
                method="native_inspection",
                parameters=flange_parameters,
            )
        )
    covered = {r for c in checks for r in c["requirement_ids"]}
    review_ids = [
        r.id
        for r in baseline.requirements
        if r.id not in covered and not r.id.endswith("-DELIVERABLES")
    ]
    checks.extend(
        [
            check(
                "design-review",
                review_ids,
                "report",
                constraint={"operator": "review"},
                method="human_review",
            ),
            check("deliverable-dxf", [rid("DELIVERABLES")], "dxf"),
            check("deliverable-report", [rid("DELIVERABLES")], "report"),
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
                "Physical fit, machining, drilling, guarding and supplier qualification remain outside this digital validation gate."
            ],
            "supported_kinds": ["file"],
        }
    )


def render():
    return {
        DESTINATION
        / (scenario_id + ("-full" if scenario_id.endswith("01") else "") + ".json"): (
            canonical_json(build(scenario_id, config)) + "\n"
        ).encode()
        for scenario_id, config in CONFIG.items()
    }


if __name__ == "__main__":
    for path, data in render().items():
        path.write_bytes(data)
    print(f"Wrote {len(CONFIG)} jig profiles")
