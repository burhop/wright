"""Build full-scope robot tracking profiles from frozen baselines."""

from __future__ import annotations

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
    "robot-tracking-diagnosis-01": dict(
        position=0.014113165506822019,
        lateral=0.014113165506822019,
        velocity=0.012187389343759947,
        samples=61,
        gap=0.5,
        gaps=[],
        alignment=["map", "map", 0.0, 0.0, 0.0, 0.0],
        event_time=15.0,
    ),
    "robot-tracking-diagnosis-02": dict(
        position=0.10613942977788116,
        lateral=0.006411903944762738,
        velocity=0.02067094046493575,
        samples=61,
        gap=0.5,
        gaps=[],
        alignment=["tracker", "map", -1.0, 2.0, 0.0, 0.15],
        event_time=12.0,
    ),
    "robot-tracking-diagnosis-03": dict(
        position=0.008614542537186748,
        lateral=0.006423582096768288,
        velocity=0.0,
        samples=56,
        gap=3.0,
        gaps=[[13.5, 16.5]],
        alignment=["map", "map", 0.0, 0.0, 0.0, 0.0],
        event_time=14.0,
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
    return dict(
        id=identifier,
        version="1",
        requirement_ids=requirement_ids,
        subject_role=role,
        reader=reader,
        selector=selector,
        constraint=constraint or {"operator": "exists"},
        unit=unit,
        frame=None,
        evidence_method=method,
        parameters=parameters or {},
        applicability_reason=None,
    )


def build(scenario_id, config):
    baseline = load_baseline(scenario_id).model_dump(mode="json")
    prefix = "ROBOT" + scenario_id[-2:]
    approved_path = (
        ROOT
        / "specs/082-output-content-validation/campaign-example-renewal-engineering-input-proposal.json"
    )
    source = {
        "artifact_ref": approved_path.relative_to(ROOT).as_posix(),
        "locator": "cases/" + scenario_id + "/new_fixed_requirements",
        "sha256": hashlib.sha256(approved_path.read_bytes()).hexdigest(),
    }
    additions = {
        "DESIGN-CONTRACT": "Corrective hardware preserves every independently approved site, interface, material, load, envelope and mass requirement and changes only the permitted design choices; tracking correlation is not treated as causal proof.",
        "CORRECTIVE-CAD": "The final corrective-hardware CAD is an inspectable same-attempt STEP with reopened measurements bound to the approved interfaces.",
        "CORRECTIVE-FEA": "The exact final STEP is checked with coarse/fine CalculiX fields, reaction equilibrium, approved stress and deflection limits, and explicit limitations.",
        "COMMISSIONING": "The final package includes a bounded installation and commissioning plan that preserves unperformed physical, causal and authority-dependent checks.",
    }
    baseline["requirements"].extend(
        {
            "id": prefix + "-" + suffix,
            "text": text,
            "mandatory": True,
            "scope": "design" if suffix != "COMMISSIONING" else "content",
            "sources": [source],
            "review_required": False,
        }
        for suffix, text in additions.items()
    )
    baseline["amendments"].append(source)
    ids = {item["id"] for item in baseline["requirements"]}

    def rid(suffix):
        value = prefix + "-" + suffix
        if value not in ids:
            raise ValueError(value)
        return value

    checks = [
        check(
            "conversion-format",
            [rid("INPUT-LINEAGE")],
            "conversion_manifest",
            selector="/format",
            constraint={"operator": "equals", "expected": "ROS2 sqlite3 CDR"},
        ),
        check(
            "conversion-frame",
            [rid("INPUT-LINEAGE")],
            "conversion_manifest",
            selector="/frame_transform_applied",
            constraint={"operator": "equals", "expected": False},
        ),
        check(
            "conversion-clock",
            [rid("INPUT-LINEAGE")],
            "conversion_manifest",
            selector="/header_clock_corrected",
            constraint={"operator": "equals", "expected": False},
        ),
    ]

    def alignment_requirement(key):
        if scenario_id.endswith("02"):
            return "TIME-ALIGNMENT" if key == "header_offset_s" else "SPATIAL-ALIGNMENT"
        if scenario_id.endswith("03"):
            return "INPUT-LINEAGE"
        return "ALIGNMENT"

    for key, expected in zip(
        (
            "external_frame",
            "map_frame",
            "translation_x_m",
            "translation_y_m",
            "rotation_rad",
            "header_offset_s",
        ),
        config["alignment"],
        strict=True,
    ):
        checks.append(
            check(
                "alignment-" + key.replace("_", "-"),
                [rid(alignment_requirement(key))],
                "metrics",
                selector="/alignment/" + key,
                constraint={"operator": "equals", "expected": expected},
            )
        )
    metric_req = rid("METRICS")
    for operation, target, unit in (
        ("position_rmse", config["position"], "m"),
        ("lateral_rmse", config["lateral"], "m"),
        ("retained_samples", config["samples"], "1"),
        ("start_time", 0, "s"),
        ("end_time", 30, "s"),
        ("largest_gap", config["gap"], "s"),
    ):
        requirement_ids = [metric_req]
        if scenario_id.endswith("03") and operation in {
            "retained_samples",
            "start_time",
            "end_time",
        }:
            requirement_ids.append(rid("SAMPLE-SCOPE"))
        checks.append(
            check(
                "timeline-" + operation.replace("_", "-"),
                requirement_ids,
                "timeline",
                reader="tracking-timeline",
                selector="timeline/" + operation,
                constraint={"operator": "within", "target": target, "tolerance": 1e-9},
                unit=unit,
                method="independent_measurement",
                parameters={"operation": operation},
            )
        )
    checks.extend(
        [
            check(
                "velocity-rmse",
                [metric_req],
                "metrics",
                selector="/velocity_disagreement_rmse_mps",
                constraint={
                    "operator": "within",
                    "target": config["velocity"],
                    "tolerance": 1e-9,
                },
                unit="m/s",
            ),
            check(
                "gap-record",
                [
                    rid("OCCLUSION")
                    if scenario_id.endswith("03")
                    else rid("TIME-ALIGNMENT")
                    if scenario_id.endswith("02")
                    else rid("ALIGNMENT")
                ],
                "metrics",
                selector="/external_gaps_not_interpolated",
                constraint={"operator": "equals", "expected": config["gaps"]},
            ),
            check(
                "event-id",
                [rid("EVENT")],
                "metrics",
                selector="/events/0/event_id",
                constraint={"operator": "equals", "expected": "E01"},
            ),
            check(
                "event-time",
                [rid("EVENT")],
                "metrics",
                selector="/events/0/bag_elapsed_s",
                constraint={
                    "operator": "within",
                    "target": config["event_time"],
                    "tolerance": 1e-9,
                },
                unit="s",
            ),
            check(
                "event-correlation",
                [rid("EVENT")],
                "metrics",
                selector="/events/0/difference_s",
                constraint={
                    "operator": "range",
                    "minimum": -0.5,
                    "maximum": 0.5,
                    "inclusive": True,
                },
                unit="s",
            ),
            check(
                "plot-review", [rid("PLOTS")], "plot", constraint={"operator": "review"}
            ),
            check(
                "diagnosis-review",
                [rid("DIAGNOSIS"), rid("ACTION-SCOPE")],
                "diagnosis",
                constraint={"operator": "review"},
            ),
            check(
                "corrective-cad-native",
                [rid("CORRECTIVE-CAD")],
                "corrective_step",
                reader="step-bounding-box",
                selector="box/x_span_mm",
                constraint={"operator": "range", "minimum": 0.1},
                unit="mm",
                method="native_inspection",
            ),
            check(
                "corrective-design-review",
                [rid("DESIGN-CONTRACT"), rid("CORRECTIVE-CAD")],
                "corrective_measurements",
                constraint={"operator": "review"},
                method="human_review",
            ),
            check(
                "corrective-fea-status",
                [rid("CORRECTIVE-FEA")],
                "corrective_fea",
                selector="/status",
                constraint={"operator": "equals", "expected": "pass"},
            ),
            check(
                "corrective-fea-review",
                [rid("CORRECTIVE-FEA")],
                "corrective_fea",
                constraint={"operator": "review"},
                method="human_review",
            ),
            check(
                "commissioning-review",
                [rid("COMMISSIONING")],
                "commissioning",
                constraint={"operator": "review"},
                method="human_review",
            ),
        ]
    )
    if scenario_id.endswith("03"):
        checks.append(
            check(
                "yaw-wrapping",
                [metric_req],
                "timeline",
                reader="tracking-timeline",
                selector="timeline/max_yaw_residual",
                constraint={"operator": "range", "maximum": 3.141592653589793},
                unit="rad",
                method="independent_measurement",
                parameters={"operation": "max_yaw_residual"},
            )
        )
    for role in ("timeline", "metrics", "diagnosis", "plot", "conversion_manifest"):
        checks.append(
            check("deliverable-" + role.replace("_", "-"), [rid("DELIVERABLES")], role)
        )
    for role in ("corrective_measurements", "corrective_fea", "commissioning"):
        checks.append(
            check(
                "deliverable-" + role.replace("_", "-"),
                [rid("CORRECTIVE-CAD") if role == "corrective_measurements" else rid("CORRECTIVE-FEA") if role == "corrective_fea" else rid("COMMISSIONING")],
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
                "Physical robot operation and causal proof remain outside this digital validation gate."
            ],
            # Canonical runs bind native artifacts as files and the AI-authored
            # diagnosis as its exact immutable response value.  Retained
            # campaign qualification continues to exercise the file form.
            "supported_kinds": ["file", "value"],
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
    print(json.dumps({"profiles": len(CONFIG)}))
