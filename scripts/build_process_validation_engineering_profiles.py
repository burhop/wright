"""Freeze the initial jig and heat process-validation profiles from source packs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from core.process_validation import (
    Baseline,
    CheckDefinition,
    Constraint,
    Requirement,
    SourceReference,
    ValidationProfile,
)


ROOT = Path(__file__).resolve().parents[1]
TARGET = (
    ROOT
    / "packages/workspace_service/src/workspace_service/process_validation/profiles"
)


def _source(path: str, locator: str) -> SourceReference:
    content = (ROOT / path).read_bytes()
    return SourceReference(
        artifact_ref=path,
        sha256=hashlib.sha256(content).hexdigest(),
        locator=locator,
    )


def _write(name: str, profile: ValidationProfile) -> None:
    (TARGET / name).write_text(
        json.dumps(profile.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )


def jig_profile() -> ValidationProfile:
    holes = "tests/datasets/engineering-workflows/scenarios/parametric-drill-jig/01-furniture-rail-insert-jig/holes.csv"
    bushings = "tests/datasets/engineering-workflows/scenarios/parametric-drill-jig/01-furniture-rail-insert-jig/bushings.csv"
    context = "tests/datasets/engineering-workflows/scenarios/parametric-drill-jig/01-furniture-rail-insert-jig/context.md"
    requirements = []
    for hole, x in (("H1", 30.0), ("H2", 170.0)):
        requirements.extend(
            [
                Requirement(
                    id=f"JIG-{hole}-X",
                    text=f"{hole} bushing-seat center X is {x:g} +/- 0.20 mm in the workpiece datum.",
                    scope="design",
                    sources=(_source(holes, f"row:{hole}:x_mm"), _source(context, "Shop purpose and coordinates")),
                ),
                Requirement(
                    id=f"JIG-{hole}-Y",
                    text=f"{hole} bushing-seat center Y is 30 +/- 0.20 mm in the workpiece datum.",
                    scope="design",
                    sources=(_source(holes, f"row:{hole}:y_mm"), _source(context, "Shop purpose and coordinates")),
                ),
                Requirement(
                    id=f"JIG-{hole}-SEAT-DIAMETER",
                    text=f"{hole} body seat is 10.20 +/- 0.10 mm from 10.0 mm body OD plus 0.20 mm diametral clearance.",
                    scope="design",
                    sources=(_source(bushings, "row:B5:body_od_mm+body_diametral_clearance_mm"), _source(context, "Jig and bushing intent")),
                ),
            ]
        )
    transform = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
    checks = []
    for hole, x in (("H1", 30.0), ("H2", 170.0)):
        parameters = {
            "nominal_center_mm": [x, 30.0],
            "nominal_diameter_mm": 10.2,
            "capture_radius_mm": 5.0,
            "radius_match_tolerance_mm": 0.15,
            "datum_transform_model_to_workpiece": transform,
        }
        for axis, target in (("x", x), ("y", 30.0)):
            checks.append(
                CheckDefinition(
                    id=f"{hole.lower()}-seat-center-{axis}",
                    requirement_ids=(f"JIG-{hole}-{axis.upper()}",),
                    subject_role="jig_step",
                    reader="step-seat-geometry",
                    selector=f"seat/{hole}/center_{axis}_mm",
                    constraint=Constraint(operator="within", target=target, tolerance=0.2),
                    unit="mm",
                    frame="workpiece_datum",
                    evidence_method="native_inspection",
                    parameters=parameters,
                )
            )
        checks.append(
            CheckDefinition(
                id=f"{hole.lower()}-seat-diameter",
                requirement_ids=(f"JIG-{hole}-SEAT-DIAMETER",),
                subject_role="jig_step",
                reader="step-seat-geometry",
                selector=f"seat/{hole}/diameter_mm",
                constraint=Constraint(operator="within", target=10.2, tolerance=0.1),
                unit="mm",
                frame="workpiece_datum",
                evidence_method="native_inspection",
                parameters=parameters,
            )
        )
    return ValidationProfile(
        id="parametric-drill-jig-01-seat-geometry",
        version="1",
        baseline=Baseline(
            id="parametric-drill-jig-01-seat-basis",
            version="1",
            requirements=tuple(requirements),
        ),
        checks=tuple(checks),
        excluded_scope=(
            "Flange-pocket applicability and bushing body-length stackup remain unresolved and are not acceptance checks.",
            "Clamp access, datum-fence engagement, markings, DXF/STL correspondence and drilling-depth control are outside this bounded profile.",
            "Manufacturing process capability, physical fit, retention, wear, strength and machining safety are not assessed.",
        ),
        limitations=(
            "The bounded STEP reader qualifies circular body-seat axes and diameters only; it does not establish full topology correspondence.",
            "Synthetic bushing data are prototype inputs rather than supplier-certified dimensions.",
        ),
        supported_kinds=("file",),
    )


def heat_profile() -> ValidationProfile:
    alternatives = "tests/datasets/engineering-workflows/scenarios/heat-spreader-sizing/01-eink-sign-controller-strap/alternatives.csv"
    context = "tests/datasets/engineering-workflows/scenarios/heat-spreader-sizing/01-eink-sign-controller-strap/context.md"
    common_sources = (_source(alternatives, "rows:baseline_40,revision_60"), _source(context, "Geometry and boundary definitions"))
    requirements = (
        Requirement(id="HEAT-FIELDS", text="Both 40 mm and 60 mm candidates retain actual coarse and refined numerical temperature fields with the declared dimensions.", scope="content", sources=common_sources),
        Requirement(id="HEAT-ANALYTICAL", text="Each field's numerical temperature rise agrees within 2% of Q*L/(k*W*t) using 4 W, 100 mm, 2 mm, k=200 W/(m K), and a 25 C cold face.", scope="design", sources=common_sources),
        Requirement(id="HEAT-BALANCE", text="Each refined field implies heat removal within 1% of the 4 W source under the declared one-dimensional model.", scope="design", sources=common_sources),
        Requirement(id="HEAT-REFINEMENT", text="Coarse-to-refined hot-end temperature-rise sensitivity is at most 2% for each candidate.", scope="design", sources=(_source(context, "Reporting policy"),)),
        Requirement(id="HEAT-BASELINE-OUTCOME", text="The 40 mm candidate exceeds the 45 C limit in the declared model, so it is not selected.", scope="design", sources=common_sources),
        Requirement(id="HEAT-REVISION-OUTCOME", text="The 60 mm candidate is at or below the inclusive 45 C limit in the declared model.", scope="design", sources=common_sources),
        Requirement(id="HEAT-SELECTION", text="The sizing decision selects the narrowest bound candidate at or below 45 C: revision_60.", scope="design", sources=(_source(context, "Engineering objective and shop capability"), _source(alternatives, "width_mm,limit_c"))),
    )
    cases = {
        "baseline": {"case": "baseline_40", "width": 40.0, "dimensions": [100.0, 40.0, 2.0]},
        "revision": {"case": "revision_60", "width": 60.0, "dimensions": [100.0, 60.0, 2.0]},
    }
    checks = []
    for prefix, case in cases.items():
        base = {
            "dimensions_mm": case["dimensions"],
            "length_mm": 100.0,
            "width_mm": case["width"],
            "thickness_mm": 2.0,
            "conductivity_w_mk": 200.0,
            "heat_input_w": 4.0,
            "cold_temperature_c": 25.0,
        }
        for mesh in ("coarse", "fine"):
            role = f"{prefix}_{mesh}"
            checks.extend(
                [
                    CheckDefinition(id=f"{role}-field", requirement_ids=("HEAT-FIELDS",), subject_role=role, reader="thermal-field", selector="field/node_count", constraint=Constraint(operator="range", minimum=2.0), unit="1", evidence_method="independent_measurement", parameters={**base, "operation": "field_nodes"}),
                    CheckDefinition(id=f"{role}-analytical", requirement_ids=("HEAT-ANALYTICAL",), subject_role=role, reader="thermal-field", selector="field/analytical_relative_rise_error", constraint=Constraint(operator="range", maximum=0.02), unit="1", evidence_method="independent_measurement", parameters={**base, "operation": "analytical_relative_error"}),
                ]
            )
        checks.extend(
            [
                CheckDefinition(id=f"{prefix}-fine-balance", requirement_ids=("HEAT-BALANCE",), subject_role=f"{prefix}_fine", reader="thermal-field", selector="field/relative_heat_imbalance", constraint=Constraint(operator="range", maximum=0.01), unit="1", evidence_method="independent_measurement", parameters={**base, "operation": "heat_balance_relative"}),
                CheckDefinition(id=f"{prefix}-refinement", requirement_ids=("HEAT-REFINEMENT",), subject_role=f"{prefix}_fine", reader="thermal-field", selector="field/refinement_relative_sensitivity", constraint=Constraint(operator="range", maximum=0.02), unit="1", evidence_method="independent_measurement", parameters={**base, "operation": "refinement_relative", "coarse_role": f"{prefix}_coarse", "related_roles": [f"{prefix}_coarse"]}),
                CheckDefinition(id=f"{prefix}-maximum", requirement_ids=(("HEAT-BASELINE-OUTCOME",) if prefix == "baseline" else ("HEAT-REVISION-OUTCOME",)), subject_role=f"{prefix}_fine", reader="thermal-field", selector="field/maximum_temperature_c", constraint=Constraint(operator="range", minimum=45.0, inclusive=False) if prefix == "baseline" else Constraint(operator="range", maximum=45.0), unit="degC", evidence_method="independent_measurement", parameters={**base, "operation": "maximum_temperature"}),
            ]
        )
    selection_cases = [
        {"id": value["case"], "role": f"{key}_fine", "width_mm": value["width"], "dimensions_mm": value["dimensions"]}
        for key, value in cases.items()
    ]
    checks.append(
        CheckDefinition(
            id="candidate-selection",
            requirement_ids=("HEAT-SELECTION",),
            subject_role="decision",
            reader="thermal-field",
            selector="decision/selected_case_id",
            constraint=Constraint(operator="equals", expected="revision_60"),
            evidence_method="independent_measurement",
            parameters={
                "operation": "selection",
                "temperature_limit_c": 45.0,
                "cases": selection_cases,
                "related_roles": ["baseline_fine", "revision_fine"],
            },
        )
    )
    return ValidationProfile(
        id="heat-spreader-sizing-01-fields",
        version="1",
        baseline=Baseline(id="heat-spreader-sizing-01-basis", version="1", requirements=requirements),
        checks=tuple(checks),
        excluded_scope=(
            "Convection, radiation, interfaces, fasteners, local chip footprint, temperature-dependent properties and transient behavior are outside the source model.",
            "STEP geometry topology, manufacturing details and material procurement are not acceptance checks in this profile.",
        ),
        limitations=(
            "The source is a synthetic constant-property one-dimensional conduction case; passing does not establish physical thermal qualification.",
            "Uniform end loading yields a linear field, so refinement agreement is a data-lineage check rather than independent validation of model physics.",
        ),
        supported_kinds=("file",),
    )


def build() -> None:
    _write("parametric-drill-jig-01.json", jig_profile())
    _write("heat-spreader-sizing-01.json", heat_profile())


if __name__ == "__main__":
    build()
