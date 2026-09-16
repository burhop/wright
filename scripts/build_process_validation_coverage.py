"""Rebuild the source inventory; this does not evaluate any generated output."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


CAPABILITIES = {
    "printed-replacement-part": ["geometry", "manufacturing.slice"],
    "raspberry-pi-enclosure": ["geometry", "source.authority", "thermal.cfd"],
    "sheet-metal-supplier-handoff": ["geometry", "manufacturing.sheet_metal", "bundle"],
    "lightweight-equipment-bracket": ["geometry", "structural.fields"],
    "parametric-drill-jig": ["geometry", "fit.datum"],
    "robot-tracking-diagnosis": ["structured", "timeseries.frames"],
    "heat-spreader-sizing": ["thermal.conduction", "numerical.refinement"],
    "sensor-fan-harness": ["structured", "electrical.network"],
    "sensor-interface-pcb": ["electrical.netlist", "manufacturing.ecad"],
    "water-heater-sizing": ["numerical.timeseries", "modelica.model"],
}


def build(root: Path) -> dict:
    source = root / "tests/datasets/engineering-workflows/scenarios"
    seeds = (
        root
        / "specs/081-engineering-workflow-templates/content-validation/acceptance-cases.md"
    )
    seed_rows = {}
    for line in seeds.read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) == 5 and cells[1].endswith(("-01", "-02", "-03")):
            seed_rows[cells[1]] = cells[2:4]
    entries = []
    for manifest_path in sorted(source.glob("*/*/scenario.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        family, case_id = manifest["template_id"], manifest["scenario_id"]
        requirements, defect = seed_rows[case_id]
        sources = []
        for path in sorted(manifest_path.parent.rglob("*")):
            if not path.is_file():
                continue
            if path.is_symlink() or not path.resolve().is_relative_to(source.resolve()):
                raise ValueError(f"Source leaves inventory root: {path}")
            if path.stat().st_size > 16 * 1024 * 1024:
                raise ValueError(f"Source exceeds inventory bound: {path}")
            content = path.read_bytes()
            sources.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "size_bytes": len(content),
                }
            )
        entries.append(
            {
                "scenario_id": case_id,
                "family": family,
                "source_requirements_seed": requirements,
                "targeted_defect_seed": defect,
                "requirements_frozen": False,
                "sources": sources,
                "capabilities": [
                    {"id": item, "support": "planned"} for item in CAPABILITIES[family]
                ],
                "initial_slice": case_id
                in {"parametric-drill-jig-01", "heat-spreader-sizing-01"},
            }
        )
    ids = {entry["scenario_id"] for entry in entries}
    if (
        len(entries) != 30
        or len(ids) != 30
        or set(CAPABILITIES) != {entry["family"] for entry in entries}
    ):
        raise ValueError("Expected 30 unique scenarios in the ten known families")
    return {
        "schema_version": "wright.process-validation-coverage/1",
        "kind": "source_inventory",
        "scope": "Requirement seeds and planned reader support; no measured output verdicts.",
        "seed_source": {
            "path": seeds.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(seeds.read_bytes()).hexdigest(),
        },
        "scenarios": entries,
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    target = (
        root
        / "packages/workspace_service/src/workspace_service/process_validation/profiles/coverage.json"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(build(root), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote 30 source inventory entries: {target.relative_to(root)}")
