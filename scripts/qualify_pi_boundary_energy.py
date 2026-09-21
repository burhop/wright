"""Postprocess a copied native checkpoint; never execute a new CFD solve."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

from diagnose_pi_thermal_boundary import diagnose
from pi_cfd_operations import extract_boundary_energy, foam_command, sha


def qualify(source: Path, output: Path, time_name: str):
    import pyvista as pv

    source, output = source.resolve(), output.resolve()
    if output.exists() or source == output or source in output.parents or output in source.parents:
        raise ValueError("Use a fresh, isolated sibling diagnostic output")
    if not time_name.isdigit() or not (source / time_name).is_dir():
        raise ValueError("Choose an existing numeric retained checkpoint")
    output.mkdir(parents=True)
    source_files = [file for directory in ("constant", "system", time_name) for file in (source / directory).rglob("*") if file.is_file()]
    before = {str(file.relative_to(source)): sha(file) for file in source_files}
    for directory in ("constant", "system", time_name):
        shutil.copytree(source / directory, output / directory)
    shutil.copyfile(source / "contract.json", output / "contract.json")
    contract = json.loads((output / "contract.json").read_text())
    grids = {}
    for region in contract["regions"]:
        identity = region["name"]
        foam_command(output, ["chtMultiRegionFoam", "-postProcess", "-func", "grad(T)", "-latestTime", "-region", identity])
        foam_command(output, ["foamToVTK", "-region", identity, "-latestTime"])
        candidates = list((output / "VTK" / identity).glob("*.vtk"))
        if len(candidates) != 1:
            raise ValueError("Expected one actual internal VTK per region")
        grids[identity] = pv.read(candidates[0])
    results = output / "results"
    results.mkdir()
    energy = extract_boundary_energy(output, contract, grids, pv, results)
    if any(sha(source / name) != digest for name, digest in before.items()):
        raise ValueError("Retained source changed during read-only diagnostic")
    report = {
        "at": datetime.now(timezone.utc).isoformat(),
        "scope": "postprocess copied retained fields only; no solve or campaign dispatch",
        "source_case": str(source), "checkpoint": time_name,
        "compiler_sha256": sha(Path(__file__).with_name("pi_cfd_operations.py")),
        "retained_files_unchanged": len(before), "boundary_audit": diagnose(source),
        "energy": energy, "solver_executed": False, "campaign_credit": False,
    }
    (results / "qualification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--time", required=True)
    args = parser.parse_args()
    qualify(args.source, args.output, args.time)
