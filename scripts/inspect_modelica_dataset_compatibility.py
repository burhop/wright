"""Record selected approved-kit source evidence without executing a simulation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess


def inspect(source: Path, datasets: Path, output: Path) -> dict:
    commit = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
    ).strip()
    paths = [
        "LICENSE", "deno.json", "src/kits/coffee-machine.ts",
        "src/tools/kit-input-schemas.ts", "models/CoffeeMachine.mo",
        "scenarios/heat-up-nominal.json", "docs/provider-and-runtime.md",
        "docs/contracts-and-evidence.md",
    ]
    snapshots = []
    for relative in paths:
        data = (source / relative).read_bytes()
        target = output / "source" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        snapshots.append({
            "path": relative, "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "source_url": f"https://github.com/Casys-AI/mcp-modelica/blob/{commit}/{relative}",
        })
    text = (source / "src/kits/coffee-machine.ts").read_text(encoding="utf-8")
    definitions = text.split("const parameters:", 1)[1].split("\n];", 1)[0]
    parameters = {}
    for match in re.finditer(
        r'id: "([^"]+)".*?unit: "([^"]+)".*?defaultValue: ([\d.-]+),'
        r'.*?minimum: ([\d.-]+),.*?maximum: ([\d.-]+),', definitions, re.S
    ):
        name, unit, default, minimum, maximum = match.groups()
        parameters[name] = dict(unit=unit, default=float(default), minimum=float(minimum), maximum=float(maximum))
    if len(parameters) != 8:
        raise ValueError("Approved kit parameter source changed; review parser and contract")
    scenario = json.loads((source / "scenarios/heat-up-nominal.json").read_text())
    cases = []
    for case in sorted(datasets.iterdir()):
        if not case.is_dir():
            continue
        with (case / "parameters.csv").open(newline="") as stream:
            values = {row["quantity"]: float(row["value"]) for row in csv.DictReader(stream)}
        with (case / "power-candidates.csv").open(newline="") as stream:
            powers = [float(row["electrical_power_W"]) for row in csv.DictReader(stream)]
        gaps = [{
            "code": "timestep_override_unavailable",
            "detail": "The approved scenario fixes stop time and output intervals; the public closed schema has no solver step/tolerance override for required tighter-timestep verification.",
            "requested_stop_time_s": values["requested_stop_time"],
            "approved_stop_time_s": scenario["stop_time_s"],
            "approved_intervals": scenario["number_of_intervals"],
        }, {
            "code": "efficiency_not_exposed",
            "requested_efficiency": values["electrical_to_thermal_efficiency"],
            "detail": "Kit heater power drives an ideal thermal source directly; no independent electrical efficiency parameter is exposed. A reviewed input/output conversion would be needed before calling energy electrical.",
        }]
        minimum = parameters["heater_power"]["minimum"]
        maximum = parameters["heater_power"]["maximum"]
        invalid = [power for power in powers if not minimum <= power <= maximum]
        if invalid:
            gaps.append({"code": "power_out_of_bounds", "requested_W": invalid, "minimum_W": minimum, "maximum_W": maximum})
        capacity = values["vessel_heat_capacity"]
        if not parameters["boiler_heat_capacity"]["minimum"] <= capacity <= parameters["boiler_heat_capacity"]["maximum"]:
            gaps.append({"code": "vessel_capacity_out_of_bounds", "requested_J_per_K": capacity, "bounds": parameters["boiler_heat_capacity"]})
        cases.append({"dataset_directory": case.name, "compatible": False, "gaps": gaps})
    report = {
        "schema_version": 1, "evidence_kind": "source_contract_inspection",
        "repository": "https://github.com/Casys-AI/mcp-modelica", "commit": commit,
        "package_version": json.loads((source / "deno.json").read_text())["version"],
        "selected_model": "coffee-machine-v1", "model_version": "0.1.0",
        "scenario": scenario, "parameters": parameters, "snapshots": snapshots,
        "cases": cases, "simulation_executed": False,
        "canonical_workflow_dispatched": False, "full_clean_container_qualification": False,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "contract-inspection.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--datasets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = inspect(args.source.resolve(), args.datasets.resolve(), args.output.resolve())
    print(json.dumps({"commit": result["commit"], "cases": result["cases"]}, indent=2))
