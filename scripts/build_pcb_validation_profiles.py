"""Build full-scope sensor-interface PCB profiles from frozen source packs."""

from __future__ import annotations

import csv
from pathlib import Path

from core.process_validation import ValidationProfile, canonical_json
from workspace_service.process_validation.baselines import load_baseline


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = (
    ROOT
    / "packages/workspace_service/src/workspace_service/process_validation/profiles"
)
SOURCE = ROOT / "tests/datasets/engineering-workflows/scenarios/sensor-interface-pcb"
PACKS = {
    "sensor-interface-pcb-01": "01-thermistor-interface",
    "sensor-interface-pcb-02": "02-dual-pressure-filter",
    "sensor-interface-pcb-03": "03-fan-tach-service-board",
}
FOOTPRINTS = {
    "1x02_2.54mm_vertical_THT": "PinHeader_1x02_P2.54mm_Vertical",
    "1x03_2.54mm_vertical_THT": "PinHeader_1x03_P2.54mm_Vertical",
    "1x04_2.54mm_vertical_THT": "PinHeader_1x04_P2.54mm_Vertical",
    "1x02_3.5mm_THT_terminal": "TerminalBlock_4Ucon_1x02_P3.50mm_Vertical",
    "R_0603_1608Metric": "R_0603_1608Metric",
    "C_0603_1608Metric": "C_0603_1608Metric",
    "C_0805_2012Metric": "C_0805_2012Metric",
    "1.5mm_min_exposed_pad": "TestPoint_Pad_D1.5mm",
    "1.5mm_exposed_pad": "TestPoint_Pad_D1.5mm",
}
PLACEMENTS = {
    "sensor-interface-pcb-01": {
        "J1": {"xy_mm": [7, 15], "point": "pad_centroid"},
        "J2": {"xy_mm": [33, 15], "point": "pad_centroid"},
    },
    "sensor-interface-pcb-02": {
        "J2": {"xy_mm": [34, 19.5], "point": "pad_centroid"},
        "J3": {"xy_mm": [34, 10.5], "point": "pad_centroid"},
        "J1": {"xy_mm": [4.5, 18.81], "rotation_deg": 180},
        "C2": {"xy_mm": [23, 18.5], "rotation_deg": 0},
        "C3": {"xy_mm": [8, 23], "rotation_deg": 0},
        "C4": {"xy_mm": [12, 23], "rotation_deg": 0},
        "TP1": {"xy_mm": [10, 14]},
    },
    "sensor-interface-pcb-03": {
        "J3": {"xy_mm": [36, 16.46], "point": "pad_centroid"},
        "J4": {"xy_mm": [20, 25.5], "point": "pad_centroid"},
        "J2": {"xy_mm": [5, 19]},
        "TP1": {"xy_mm": [10, 14]},
        "TP3": {"xy_mm": [32, 14]},
    },
}


def check(
    identifier,
    requirement_ids,
    role,
    *,
    operation=None,
    constraint=None,
    reader="kicad",
    method="independent_measurement",
    parameters=None,
):
    values = dict(parameters or {})
    if operation:
        values["operation"] = operation
    return {
        "id": identifier,
        "version": "1",
        "requirement_ids": requirement_ids,
        "subject_role": role,
        "reader": reader,
        "selector": f"pcb/{operation}" if operation else "",
        "constraint": constraint or {"operator": "exists"},
        "unit": "1" if reader == "kicad" else None,
        "frame": "board_coordinates"
        if operation in {"placement", "board_geometry"}
        else None,
        "evidence_method": method,
        "parameters": values,
        "applicability_reason": None,
    }


def _sources(pack):
    with (pack / "netlist.csv").open(newline="", encoding="utf-8-sig") as stream:
        connections = list(csv.DictReader(stream))
    components = {}
    with (pack / "component-library.csv").open(
        newline="", encoding="utf-8-sig"
    ) as stream:
        for row in csv.DictReader(stream):
            for reference in row["reference"].split(";"):
                components[reference] = {
                    "value": row["value"],
                    "footprint_contains": FOOTPRINTS[row["footprint_requirement"]],
                }
    return connections, components


def build(scenario_id, pack_name):
    baseline = load_baseline(scenario_id)
    prefix = "PCB" + scenario_id[-2:]
    known = {item.id for item in baseline.requirements}

    def ids(*suffixes):
        result = [prefix + "-" + suffix for suffix in suffixes]
        if not set(result) <= known:
            raise ValueError(set(result) - known)
        return result

    connections, components = _sources(SOURCE / pack_name)
    checks = [
        check(
            "native-netlist",
            ids("CONNECTIVITY", "CONNECTORS")
            if scenario_id.endswith("01")
            else ids("CONNECTIVITY"),
            "board",
            operation="netlist",
            constraint={"operator": "equals", "expected": len(connections)},
            parameters={"expected_connections": connections},
        ),
        check(
            "native-components",
            ids("PARTS"),
            "board",
            operation="components",
            constraint={"operator": "equals", "expected": len(components)},
            parameters={"expected_components": components},
        ),
        check(
            "bom-components",
            ids("PARTS", "CORRESPONDENCE"),
            "bom",
            operation="bom",
            constraint={"operator": "equals", "expected": len(components)},
            parameters={"expected_components": components},
        ),
        check(
            "required-placement",
            ids("CONNECTORS")
            if scenario_id.endswith("01")
            else ids("CONNECTORS", "TEST-PADS", "QUALIFIED-PLACEMENT")
            if scenario_id.endswith("02")
            else ids("PLACEMENT"),
            "board",
            operation="placement",
            constraint={"operator": "equals", "expected": len(PLACEMENTS[scenario_id])},
            parameters={
                "expected_placements": PLACEMENTS[scenario_id],
                "tolerance_mm": 0.02,
            },
        ),
        check(
            "board-outline-holes",
            ids("BOARD") if scenario_id.endswith("01") else ids("BOARD-RULES"),
            "board",
            operation="board_geometry",
            constraint={"operator": "equals", "expected": 1},
            parameters={
                "size_mm": [40, 30],
                "tolerance_mm": 0.02,
                "holes": {"H1": [3, 3], "H2": [37, 3], "H3": [3, 27], "H4": [37, 27]},
            },
        ),
        check(
            "erc-errors",
            ids("CHECKS"),
            "erc",
            operation="report",
            constraint={"operator": "equals", "expected": 0},
        ),
        check(
            "drc-errors",
            ids("CHECKS"),
            "drc",
            operation="report",
            constraint={"operator": "equals", "expected": 0},
        ),
        check(
            "fabrication-members",
            ids("DELIVERABLES", "CORRESPONDENCE"),
            "fabrication",
            operation="fabrication_bundle",
            constraint={"operator": "equals", "expected": 5},
            parameters={
                "required_members": [
                    "design-F_Cu.gtl",
                    "design-B_Cu.gbl",
                    "design-Edge_Cuts.gm1",
                    "design.drl",
                    "design-job.gbrjob",
                ]
            },
        ),
        check(
            "deliverable-schematic",
            ids("DELIVERABLES"),
            "schematic",
            reader="structured",
            method="structured_value",
        ),
        check(
            "deliverable-basis",
            ids("DELIVERABLES"),
            "basis",
            reader="structured",
            method="structured_value",
        ),
    ]
    if scenario_id.endswith("03"):
        checks.append(
            check(
                "power-track-widths",
                ids("POWER-ROUTING"),
                "board",
                operation="track_widths",
                constraint={"operator": "equals", "expected": 2},
                parameters={"minimum_by_net_mm": {"24V": 1.5, "GND": 1.5}},
            )
        )
    automated = {rid for item in checks for rid in item["requirement_ids"]}
    review_ids = [item.id for item in baseline.requirements if item.id not in automated]
    if review_ids:
        checks.append(
            check(
                "engineering-review",
                review_ids,
                "basis",
                constraint={"operator": "review"},
                reader="structured",
                method="human_review",
            )
        )
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
                "Warning disposition, production-source compatibility, full native-to-fabrication correspondence, physical performance and release authorization require authenticated engineering review."
            ],
            "supported_kinds": ["file"],
        }
    )


def render():
    return {
        DESTINATION / f"{scenario_id}.json": (
            canonical_json(build(scenario_id, pack)) + "\n"
        ).encode()
        for scenario_id, pack in PACKS.items()
    }


if __name__ == "__main__":
    for path, data in render().items():
        path.write_bytes(data)
    print(f"Wrote {len(PACKS)} PCB profiles")
