"""Build full-scope lightweight-equipment-bracket validation profiles."""

from __future__ import annotations

from pathlib import Path

from core.process_validation import ValidationProfile, canonical_json
from workspace_service.process_validation.baselines import load_baseline


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "packages/workspace_service/src/workspace_service/process_validation/profiles"
CASES = {
    "lightweight-equipment-bracket-01": {
        "force_n": [0, 0, -100],
        "load_centroid_mm": [72.5, 0, 60],
        "mass_reduction": 0.20,
    },
    "lightweight-equipment-bracket-02": {
        "force_n": [60, 0, -80],
        "load_centroid_mm": [86, 0, 72],
        "mass_reduction": 0.15,
    },
    "lightweight-equipment-bracket-03": {
        "force_n": [0, 100, 0],
        "load_centroid_mm": [0, -22, 80],
        "mass_reduction": 0.25,
    },
}


def check(
    identifier,
    requirements,
    role,
    *,
    constraint=None,
    reader="structural-evidence",
    method="independent_measurement",
    selector="",
    parameters=None,
    unit=None,
    frame=None,
):
    return {
        "id": identifier,
        "version": "1",
        "requirement_ids": requirements,
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


def build(scenario_id: str, values: dict) -> ValidationProfile:
    prefix = "BRACKET" + scenario_id[-2:]
    baseline = load_baseline(scenario_id).model_dump(mode="json")
    known = {item["id"] for item in baseline["requirements"]}

    def ids(*suffixes):
        result = [prefix + "-" + suffix for suffix in suffixes]
        if not set(result) <= known:
            raise ValueError(set(result) - known)
        return result

    reviews = set(
        ids(
            "GEOMETRY",
            "MANUFACTURING",
            "LOAD",
            "MATERIAL",
            "RESPONSES",
            "REACTIONS",
            "REFINEMENT",
            "CLAIM-SCOPE",
        )
    )
    for requirement in baseline["requirements"]:
        requirement["review_required"] = requirement["id"] in reviews

    checks = [
        check(
            "baseline-step-present",
            ids("GEOMETRY", "DELIVERABLES"),
            "baseline_step",
            reader="step-bounding-box",
            method="native_inspection",
            selector="box/x_span_mm",
            constraint={"operator": "range", "minimum": 0.001},
            unit="mm",
            frame="model_axes",
        ),
        check(
            "revised-step-present",
            ids("GEOMETRY", "DELIVERABLES"),
            "revised_step",
            reader="step-bounding-box",
            method="native_inspection",
            selector="box/x_span_mm",
            constraint={"operator": "range", "minimum": 0.001},
            unit="mm",
            frame="model_axes",
        ),
        check(
            "request-contract",
            ids("LOAD", "MATERIAL", "DELIVERABLES"),
            "fea_requests",
            constraint={"operator": "equals", "expected": True},
            selector="structural/request-contract",
            parameters={
                "operation": "request_contract",
                "force_n": values["force_n"],
                "related_roles": ["baseline_step", "revised_step"],
            },
        ),
        check(
            "mass-reduction",
            ids("MASS"),
            "mass_comparison",
            constraint={"operator": "range", "minimum": values["mass_reduction"]},
            selector="structural/mass-reduction",
            parameters={
                "operation": "mass_reduction",
                "density_kg_m3": 2700,
                "related_roles": ["baseline_step", "revised_step"],
            },
            unit="1",
        ),
    ]
    for variant in ("baseline", "revised"):
        geometry_role = f"{variant}_step"
        for mesh in ("coarse", "fine"):
            label = f"{variant}_{mesh}"
            displacement = f"{label}_displacement"
            stress = f"{label}_stress"
            reaction = f"{label}_reaction"
            checks.extend(
                [
                    check(
                        f"{label}-receipt",
                        ids("DELIVERABLES"),
                        f"{label}_receipt",
                        constraint={"operator": "equals", "expected": True},
                        selector=f"structural/{label}/receipt",
                        parameters={
                            "operation": "receipt_binding",
                            "geometry_role": geometry_role,
                            "related_roles": [geometry_role, displacement, stress, reaction],
                            "expected_paths": {
                                displacement: "native-field-expansion/displacement-field.csv",
                                stress: "native-field-expansion/stress-field.csv",
                                reaction: "reaction-forces.json",
                            },
                        },
                    ),
                    check(
                        f"{label}-displacement",
                        ids("RESPONSES", "DELIVERABLES"),
                        displacement,
                        constraint={"operator": "range", "maximum": 0.5},
                        selector=f"structural/{label}/maximum-displacement",
                        parameters={"operation": "displacement_maximum"},
                        unit="mm",
                        frame="global",
                    ),
                    check(
                        f"{label}-stress-field",
                        ids("RESPONSES", "DELIVERABLES"),
                        stress,
                        constraint={"operator": "range", "minimum": 0},
                        selector=f"structural/{label}/unfiltered-maximum-von-mises",
                        parameters={"operation": "stress_maximum"},
                        unit="MPa",
                        frame="global",
                    ),
                    check(
                        f"{label}-equilibrium",
                        ids("REACTIONS"),
                        reaction,
                        constraint={"operator": "range", "maximum": 0.01},
                        selector=f"structural/{label}/equilibrium-relative-error",
                        parameters={
                            "operation": "reaction_equilibrium",
                            "force_n": values["force_n"],
                            "load_centroid_mm": values["load_centroid_mm"],
                        },
                        unit="1",
                        frame="global_origin",
                    ),
                ]
            )
        for field in ("displacement", "stress"):
            checks.append(
                check(
                    f"{variant}-{field}-refinement",
                    ids("REFINEMENT"),
                    f"{variant}_fine_{field}",
                    constraint={"operator": "range", "maximum": 0.05, "inclusive": False},
                    selector=f"structural/{variant}/{field}-refinement",
                    parameters={
                        "operation": "refinement",
                        "field": field,
                        "coarse_role": f"{variant}_coarse_{field}",
                        "related_roles": [f"{variant}_coarse_{field}"],
                    },
                    unit="1",
                )
            )
    checks.extend(
        [
            check(
                "mechanical-basis-review",
                ids("GEOMETRY", "MANUFACTURING", "LOAD", "MATERIAL"),
                "mechanical_basis",
                constraint={"operator": "review"},
                reader="structured",
                method="human_review",
            ),
            check(
                "analysis-review",
                ids("RESPONSES", "REACTIONS", "REFINEMENT", "CLAIM-SCOPE"),
                "analysis_report",
                constraint={"operator": "review"},
                reader="structured",
                method="human_review",
            ),
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
                "The validator checks static linear-elastic digital evidence only; fatigue, impact, joint compliance, material certification and physical qualification remain outside scope.",
                "Detailed protected-feature topology, machining feasibility and non-singular stress-region interpretation require authenticated engineering review.",
            ],
            "supported_kinds": ["file", "value"],
        }
    )


def render():
    return {
        DESTINATION / f"{scenario_id}.json": (
            canonical_json(build(scenario_id, values)) + "\n"
        ).encode("utf-8")
        for scenario_id, values in CASES.items()
    }


def main():
    for path, content in render().items():
        path.write_bytes(content)
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
