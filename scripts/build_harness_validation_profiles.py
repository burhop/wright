"""Build full-scope sensor-fan harness profiles from frozen source schedules."""

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
SOURCES = {
    "sensor-fan-harness-01": "01-desktop-incubator",
    "sensor-fan-harness-02": "02-growth-rack-long-run",
    "sensor-fan-harness-03": "03-dual-zone-air-sampler",
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


def expected_connections(directory):
    path = (
        ROOT
        / "tests/datasets/engineering-workflows/scenarios/sensor-fan-harness"
        / directory
        / "wiring-schedule.csv"
    )
    with path.open(encoding="utf-8", newline="") as handle:
        return [
            {
                "from": f"{row['from_connector']}:{row['from_pin']}",
                "to": f"{row['to_connector']}:{row['to_pin']}",
                "net": row["net"],
            }
            for row in csv.DictReader(handle)
        ]


def build(scenario_id, directory):
    baseline = load_baseline(scenario_id)
    prefix = "HARNESS" + scenario_id[-2:]
    known = {item.id for item in baseline.requirements}

    def rid(suffix):
        value = prefix + "-" + suffix
        if value not in known:
            raise ValueError(value)
        return value

    topology_requirements = [rid("TOPOLOGY")]
    if scenario_id.endswith("02"):
        topology_requirements.append(rid("SIGNALS"))
    checks = [
        check(
            "net-topology",
            topology_requirements,
            "netlist",
            reader="harness",
            selector="harness/topology",
            constraint={
                "operator": "equals",
                "expected": len(expected_connections(directory)),
            },
            unit="1",
            method="independent_measurement",
            parameters={
                "operation": "topology",
                "expected_connections": expected_connections(directory),
            },
        ),
        check(
            "cut-lengths",
            [rid("CUT-LENGTHS")],
            "cut_list",
            reader="harness",
            selector="harness/cut_lengths",
            constraint={"operator": "range", "minimum": 1},
            unit="1",
            method="independent_measurement",
            parameters={"operation": "cut_lengths"},
        ),
        check(
            "voltage-drop",
            [rid("DROP")],
            "voltage_drop",
            reader="harness",
            selector="harness/maximum_total_drop",
            constraint={"operator": "range", "maximum": 0.72},
            unit="V",
            method="independent_measurement",
            parameters={"operation": "voltage_drop"},
        ),
    ]
    if scenario_id.endswith("03"):
        checks.extend(
            [
                check(
                    "reserve-pins",
                    [rid("RESERVE")],
                    "netlist",
                    reader="harness",
                    selector="harness/reserve",
                    constraint={"operator": "equals", "expected": 2},
                    unit="1",
                    method="independent_measurement",
                    parameters={
                        "operation": "reserve_unconnected",
                        "reserved_endpoints": ["ZX:6", "ZY:6"],
                    },
                ),
                check(
                    "shield-review",
                    [rid("SHIELDS")],
                    "shield",
                    constraint={"operator": "review"},
                    method="human_review",
                ),
            ]
        )
    automated = {
        requirement for item in checks for requirement in item["requirement_ids"]
    }
    review_roles = {"basis": [], "plan": [], "assembly": [], "bom": [], "handoff": []}
    preferred = {
        "CURRENTS": "basis",
        "CONNECTORS": "basis",
        "PACKAGING": "plan",
        "INTERFACES": "basis",
        "VIEWS": "plan",
        "SERVICE": "plan",
        "SPLICES": "plan",
        "TEST-INSTRUCTIONS": "assembly",
        "ACTION-SCOPE": "handoff",
    }
    for requirement in baseline.requirements:
        if requirement.id in automated or requirement.id.endswith("-DELIVERABLES"):
            continue
        suffix = requirement.id.removeprefix(prefix + "-")
        review_roles[preferred.get(suffix, "basis")].append(requirement.id)
    for role, requirement_ids in review_roles.items():
        if requirement_ids:
            checks.append(
                check(
                    role + "-review",
                    requirement_ids,
                    role,
                    constraint={"operator": "review"},
                    method="human_review",
                )
            )
    for role in ("plan", "pin_schedule", "cut_list", "bom", "assembly", "voltage_drop"):
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
                "Physical fabrication, energizing, purchasing and production certification remain outside this digital validation gate."
            ],
            "supported_kinds": ["file", "value"],
        }
    )


def render():
    return {
        DESTINATION / (scenario_id + ".json"): (
            canonical_json(build(scenario_id, directory)) + "\n"
        ).encode()
        for scenario_id, directory in SOURCES.items()
    }


if __name__ == "__main__":
    for path, data in render().items():
        path.write_bytes(data)
    print(f"Wrote {len(SOURCES)} harness profiles")
