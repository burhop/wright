"""Build full-scope printed-replacement-part validation profiles."""

from __future__ import annotations

from pathlib import Path

from core.process_validation import ValidationProfile, canonical_json
from workspace_service.process_validation.baselines import load_baseline


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = (
    ROOT
    / "packages/workspace_service/src/workspace_service/process_validation/profiles"
)
CASES = {
    "printed-replacement-part-01": {
        "envelope": {"x": (None, 38.0), "y": (None, 38.0), "z": (None, 18.0)},
        "layer_height": "0.20",
        "wall_loops": "4",
        "infill": "35%",
    },
    "printed-replacement-part-02": {
        "envelope": {"x": (None, 118.0), "y": (None, 28.0), "z": (None, 34.0)},
        "layer_height": "0.20",
        "wall_loops": "5",
        "infill": "40%",
    },
    "printed-replacement-part-03": {
        "envelope": {"x": (26.0, 26.0), "y": (38.0, 38.0), "z": (17.0, 17.0)},
        "layer_height": "0.16",
        "wall_loops": "5",
        "infill": "45%",
    },
}
PACKAGE_MEMBERS = [
    "3D/3dmodel.model",
    "3D/Objects/object_1.model",
    "Metadata/plate_1.gcode",
    "Metadata/project_settings.config",
    "Metadata/slice_info.config",
]


def check(
    identifier,
    requirement_ids,
    role,
    *,
    constraint=None,
    selector="",
    reader="printing",
    method="independent_measurement",
    parameters=None,
    unit=None,
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


def build(scenario_id: str, values: dict) -> ValidationProfile:
    original = load_baseline(scenario_id)
    prefix = "PRINT" + scenario_id[-2:]
    known = {item.id for item in original.requirements}

    def ids(*suffixes):
        result = [prefix + "-" + suffix for suffix in suffixes]
        if not set(result) <= known:
            raise ValueError(set(result) - known)
        return result

    geometry_requirement = ids("ENVELOPE") if scenario_id[-2:] != "03" else ids("BODY")
    checks = []
    for axis, (minimum, maximum) in values["envelope"].items():
        if minimum == maximum and minimum is not None:
            constraint = {
                "operator": "within",
                "target": minimum,
                "tolerance": 0.01,
            }
        else:
            constraint = {
                "operator": "range",
                "minimum": minimum,
                "maximum": maximum,
            }
        checks.append(
            check(
                f"repaired-envelope-{axis}",
                geometry_requirement,
                "repaired_mesh",
                selector=f"mesh/{axis}_span_mm",
                constraint=constraint,
                parameters={"operation": "stl_dimension", "unit_convention": "mm"},
                unit="mm",
                frame="model_axes",
            )
        )
    checks.extend(
        [
            check(
                "repaired-mesh-integrity",
                ids("MESH-LINEAGE", "DELIVERABLES"),
                "repaired_mesh",
                selector="mesh/integrity",
                constraint={"operator": "equals", "expected": True},
                parameters={"operation": "mesh_integrity", "unit_convention": "mm"},
            ),
            check(
                "distinct-mesh-lineage",
                ids("MESH-LINEAGE"),
                "repaired_mesh",
                selector="mesh/lineage",
                constraint={"operator": "equals", "expected": True},
                parameters={
                    "operation": "mesh_lineage",
                    "related_roles": ["source_mesh"],
                    "span_tolerance_mm": 0.01,
                },
            ),
            check(
                "machine-name",
                ids("SLICE"),
                "machine_profile",
                selector="/name",
                constraint={"operator": "equals", "expected": "Bambu Lab P1S 0.4 nozzle"},
                reader="structured",
                method="structured_value",
            ),
            check(
                "machine-nozzle",
                ids("SLICE"),
                "machine_profile",
                selector="/nozzle_diameter",
                constraint={"operator": "equals", "expected": ["0.4"]},
                reader="structured",
                method="structured_value",
            ),
            check(
                "filament-name",
                ids("SLICE"),
                "filament_profile",
                selector="/name",
                constraint={
                    "operator": "equals",
                    "expected": "Bambu PETG HF @BBL P1S 0.4 nozzle",
                },
                reader="structured",
                method="structured_value",
            ),
            check(
                "filament-type",
                ids("SLICE"),
                "filament_profile",
                selector="/filament_type",
                constraint={"operator": "equals", "expected": ["PETG"]},
                reader="structured",
                method="structured_value",
            ),
            check(
                "layer-height",
                ids("SLICE"),
                "process_profile",
                selector="/layer_height",
                constraint={"operator": "equals", "expected": values["layer_height"]},
                reader="structured",
                method="structured_value",
            ),
            check(
                "wall-loops",
                ids("SLICE"),
                "process_profile",
                selector="/wall_loops",
                constraint={"operator": "equals", "expected": values["wall_loops"]},
                reader="structured",
                method="structured_value",
            ),
            check(
                "infill-density",
                ids("SLICE"),
                "process_profile",
                selector="/sparse_infill_density",
                constraint={"operator": "equals", "expected": values["infill"]},
                reader="structured",
                method="structured_value",
            ),
            check(
                "slice-package-inventory",
                ids("SLICE", "DELIVERABLES"),
                "slice_package",
                selector="package/required_members",
                constraint={"operator": "equals", "expected": len(PACKAGE_MEMBERS)},
                parameters={
                    "operation": "package_inventory",
                    "required_members": PACKAGE_MEMBERS,
                },
                unit="1",
            ),
            check(
                "slice-lineage",
                ids("MESH-LINEAGE", "SLICE"),
                "slice_evidence",
                selector="slice/hash_binding",
                constraint={"operator": "equals", "expected": True},
                parameters={
                    "operation": "slice_binding",
                    "related_roles": ["repaired_mesh", "slice_package"],
                    "expected_operation": "actual_local_bambu_slice",
                },
            ),
            check(
                "simulated-transfer-binding",
                ids("DELIVERABLES"),
                "transfer_receipt",
                selector="transfer/package_binding",
                constraint={"operator": "equals", "expected": True},
                parameters={
                    "operation": "transfer_binding",
                    "related_roles": ["slice_package"],
                },
            ),
            check(
                "support-preview-present",
                ids("DELIVERABLES"),
                "support_preview",
                constraint={"operator": "exists"},
                reader="structured",
                method="structured_value",
            ),
            check(
                "source-report-present",
                ids("DELIVERABLES"),
                "source_report",
                constraint={"operator": "exists"},
                reader="structured",
                method="structured_value",
            ),
        ]
    )
    automated = {rid for item in checks for rid in item["requirement_ids"]}
    review_ids = sorted(known - automated)
    if review_ids:
        checks.append(
            check(
                "engineering-review",
                review_ids,
                "source_report",
                constraint={"operator": "review"},
                reader="structured",
                method="human_review",
            )
        )
    baseline = original.model_dump(mode="json")
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
                "Detailed mating features, grip geometry, orientation/support decisions, tolerance statements, physical fit/load/print performance and production release require authenticated engineering review."
            ],
            "supported_kinds": ["file", "value"],
        }
    )


def render():
    return {
        DESTINATION / f"{scenario_id}.json": (
            canonical_json(build(scenario_id, values)) + "\n"
        ).encode()
        for scenario_id, values in CASES.items()
    }


if __name__ == "__main__":
    for path, data in render().items():
        path.write_bytes(data)
    print(f"Wrote {len(CASES)} printed-part profiles")
