"""Build full-scope Raspberry Pi enclosure and CFD validation profiles."""

from __future__ import annotations

import csv
from pathlib import Path

from core.process_validation import ValidationProfile, canonical_json
from workspace_service.process_validation.baselines import load_baseline


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "packages/workspace_service/src/workspace_service/process_validation/profiles"
SOURCE = ROOT / "tests/datasets/engineering-workflows/scenarios/raspberry-pi-enclosure"
CASES = {
    "raspberry-pi-enclosure-01": {
        "source": "01-riverstone-desktop-computer",
        "envelope": {"x": (None, 112), "y": (None, 86), "z": (None, 39)},
        "ambient_k": 298.15,
        "target_c": 65,
        "regions": {
            "air": {"heat_w": 0, "kappa": 0.026},
            "petg_shell": {"heat_w": 0, "kappa": 0.2},
            "board_hot_patch": {"heat_w": 6, "kappa": 120},
        },
        "roles": {
            "air": "fluid_domain_{variant}",
            "petg_shell": "enclosure_{variant}",
            "board_hot_patch": "source_primary_{variant}",
        },
        "patch_region": "board_hot_patch",
        "review": ["SOURCE", "ENCLOSURE", "THERMAL", "VENT-A", "VENT-B", "SCOPE"],
        "archive_records": 22,
    },
    "raspberry-pi-enclosure-02": {
        "source": "02-greenhouse-sensor-gateway",
        "envelope": {"z": (None, 60)},
        "ambient_k": 308.15,
        "target_c": 70,
        "regions": {
            "air": {"heat_w": 0, "kappa": 0.0267},
            "shell": {"heat_w": 0, "kappa": 0.2},
            "pi_source": {"heat_w": 6, "kappa": 120},
            "sensor_source": {"heat_w": 2, "kappa": 120},
        },
        "roles": {
            "air": "fluid_domain_{variant}",
            "shell": "enclosure_{variant}",
            "pi_source": "source_primary_{variant}",
            "sensor_source": "source_secondary_{variant}",
        },
        "patch_region": "pi_source",
        "review": ["SOURCE", "ENCLOSURE", "LOADS", "VARIANTS", "SCREEN", "SCOPE"],
        "archive_records": 24,
    },
    "raspberry-pi-enclosure-03": {
        "source": "03-edge-vision-instrument",
        "envelope": {"x": (145, 145), "y": (110, 110), "z": (48, 48)},
        "ambient_k": 303.15,
        "target_c": 68,
        "regions": {
            "air": {"heat_w": 0, "kappa": 0.026},
            "petg_shell": {"heat_w": 0, "kappa": 0.2},
            "board_hot_patch": {"heat_w": 9, "kappa": 120},
            "power_interface": {"heat_w": 2, "kappa": 120},
        },
        "roles": {
            "air": "fluid_domain_{variant}",
            "petg_shell": "enclosure_{variant}",
            "board_hot_patch": "source_primary_{variant}",
            "power_interface": "source_secondary_{variant}",
        },
        "patch_region": "board_hot_patch",
        "review": ["SOURCE", "ENCLOSURE", "LOADS", "FAN", "VARIANTS", "SCOPE"],
        "archive_records": 18,
    },
}


def check(identifier, requirements, role, *, constraint=None, reader="cfd-evidence", method="independent_measurement", selector="", parameters=None, unit=None, frame=None):
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


def build(scenario_id, values):
    original = load_baseline(scenario_id)
    prefix = "PI" + scenario_id[-2:]
    known = {item.id for item in original.requirements}

    def ids(*suffixes):
        result = [prefix + "-" + suffix for suffix in suffixes]
        if not set(result) <= known:
            raise ValueError(set(result) - known)
        return result

    checks = []
    for variant in ("a", "b"):
        for axis, (minimum, maximum) in values["envelope"].items():
            constraint = (
                {"operator": "within", "target": minimum, "tolerance": 0.01}
                if minimum is not None and minimum == maximum
                else {"operator": "range", "minimum": minimum, "maximum": maximum}
            )
            checks.append(
                check(
                    f"enclosure-{variant}-{axis}",
                    ids("ENCLOSURE"),
                    f"enclosure_{variant}",
                    constraint=constraint,
                    reader="step-bounding-box",
                    method="native_inspection",
                    selector=f"box/{axis}_span_mm",
                    unit="mm",
                    frame="enclosure_axes",
                )
            )
        related_roles = {
            region: role.format(variant=variant) for region, role in values["roles"].items()
        }
        checks.append(
            check(
                f"contract-{variant}",
                ids("THERMAL" if scenario_id.endswith("01") else "LOADS", "CFD"),
                f"contract_{variant}",
                constraint={"operator": "equals", "expected": True},
                selector="cfd/contract",
                parameters={
                    "operation": "contract",
                    "related_roles": sorted(set(related_roles.values())),
                    "region_roles": related_roles,
                    "expected": {
                        "ambient_k": values["ambient_k"],
                        "gravity_m_s2": [0, 0, -9.81],
                        "regions": values["regions"],
                    },
                },
            )
        )
        checks.extend(
            [
                check(
                    f"patch-temperature-{variant}",
                    ids("CFD"),
                    "field_archive",
                    constraint={"operator": "range", "maximum": values["target_c"]},
                    selector=f"cfd/{variant}/maximum_temperature_c",
                    parameters={
                        "operation": "maximum_temperature",
                        "member": f"variant-{variant}/{values['patch_region']}.vtk",
                    },
                    unit="degC",
                ),
                check(
                    f"mass-balance-{variant}",
                    ids("CFD"),
                    "comparison",
                    constraint={"operator": "range", "maximum": 0.001},
                    selector=f"cfd/{variant}/mass_balance_relative",
                    parameters={
                        "operation": "mass_balance_relative",
                        "variant": f"variant-{variant}",
                    },
                    unit="1",
                ),
                check(
                    f"fluid-domain-{variant}",
                    ids("DELIVERABLES"),
                    f"fluid_domain_{variant}",
                    constraint={"operator": "range", "minimum": 1},
                    reader="step-bounding-box",
                    method="native_inspection",
                    selector="box/x_span_mm",
                    unit="mm",
                    frame="model_axes",
                ),
            ]
        )
    checks.extend(
        [
            check(
                "field-archive-binding",
                ids("CFD", "DELIVERABLES"),
                "comparison",
                constraint={"operator": "equals", "expected": values["archive_records"]},
                selector="cfd/archive_records",
                parameters={"operation": "archive_binding", "related_roles": ["field_archive"]},
                unit="1",
            ),
            check(
                "convergence-evidence",
                ids("CFD"),
                "comparison",
                constraint={"operator": "equals", "expected": True},
                selector="cfd/convergence",
                parameters={"operation": "convergence"},
            ),
            check(
                "heat-balance-evidence",
                ids("CFD"),
                "comparison",
                constraint={"operator": "range", "maximum": 0.01},
                selector="cfd/heat_balance_relative",
                parameters={"operation": "heat_balance"},
                unit="1",
            ),
            check(
                "design-basis-present",
                ids("DELIVERABLES"),
                "design_basis",
                reader="structured",
                method="structured_value",
            ),
            check(
                "manufacturer-research-present",
                ids("DELIVERABLES"),
                "manufacturer_research",
                reader="structured",
                method="structured_value",
            ),
            check(
                "editable-source-present",
                ids("DELIVERABLES"),
                "cad_source",
                reader="structured",
                method="structured_value",
            ),
        ]
    )
    if scenario_id.endswith("03"):
        with (SOURCE / values["source"] / "fan-curve.csv").open(
            newline="", encoding="utf-8-sig"
        ) as stream:
            points = [
                [float(row["volume_flow_m3_s"]), float(row["static_pressure_pa"])]
                for row in csv.DictReader(stream)
            ]
        for variant in ("a", "b"):
            checks.append(
                check(
                    f"fan-curve-{variant}",
                    ids("FAN"),
                    f"contract_{variant}",
                    constraint={"operator": "equals", "expected": points},
                    reader="structured",
                    method="structured_value",
                    selector="/fan_curve/points",
                )
            )
    review_ids = ids(*values["review"])
    checks.append(
        check(
            "engineering-review",
            review_ids,
            "design_basis",
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
                "Manufacturer-source authority, detailed CAD features and physical thermal, ingress, electrical, EMC, material and release claims require authenticated engineering review. Mesh-refinement evidence is not present in the retained output."
            ],
            "supported_kinds": ["file"],
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
    for path, content in render().items():
        path.write_bytes(content)
    print(f"Wrote {len(CASES)} Raspberry Pi enclosure profiles")
