"""Stage real retained CAD exports for an isolated CFD interface diagnostic."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

from pi_cfd_operations import validate


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(source: Path, output: Path, *, steady_profile=False):
    source, output = source.resolve(), output.resolve()
    if output.exists():
        raise ValueError("Choose a fresh diagnostic directory; retained attempts are immutable")
    output.mkdir(parents=True)
    staged = []
    for alternative in ("a", "b"):
        original = source / f"cfd-contract-{alternative}.json"
        contract = json.loads(original.read_bytes())
        if steady_profile:
            shutil.copyfile(original, output/f"source-contract-{alternative}.json")
            contract.pop("duration_s", None)
            contract.pop("delta_t_s", None)
            contract.update(schema_version=2,
                            numerics={"mode": "steady", "iterations": 300, "write_interval": 50},
                            mesh_grading={"far_size_mm": 10, "distance_min_mm": 2, "distance_max_mm": 25})
            contract["assumptions"].append("Diagnostic versioned steady comparison proposal matching the supplied steady heating brief; 300 SIMPLE iterations are not physical seconds or validated convergence. Geometry, domain, materials, heat loads and locations unchanged.")
        paths = []
        for region in contract["regions"]:
            exported = source / Path(region["step"]).name
            if sha(exported) != region["sha256"]:
                raise ValueError("Retained native export hash does not match the authored contract")
            destination = output / "geometry" / exported.name
            destination.parent.mkdir(exist_ok=True)
            if not destination.exists():
                shutil.copyfile(exported, destination)
            elif sha(destination) != sha(exported):
                raise ValueError("Ambiguous retained export filename")
            paths.append({"original_path": region["step"], "probe_path": destination.relative_to(output).as_posix(),
                          "sha256": sha(exported)})
            region["step"] = destination.relative_to(output).as_posix()
        target = output / f"contract-{alternative}.json"
        target.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
        row = {"alternative": alternative, "original_contract": str(original), "original_sha256": sha(original),
               "probe_contract_sha256": sha(target), "path_remapping": paths}
        try:
            regions = validate(contract, output)
            row.update(schema_status="passed", region_count=len(regions))
        except (ValueError, KeyError, TypeError) as error:
            row.update(schema_status="failed", error_type=type(error).__name__, error=str(error))
        staged.append(row)
    compiler = Path(__file__).with_name("pi_cfd_operations.py")
    shutil.copyfile(compiler, output / compiler.name)
    report = {"schema_version": 1, "observed_at": datetime.now(timezone.utc).isoformat(),
              "kind": "retained_native_exports_cfd_interface_probe", "compiler_sha256": sha(compiler),
              "alternatives": staged, "changes": ("Versioned steady 300-iteration profile, writes every50, CAD-surface mesh grading2-to10mm at2-to25mm distance; open boundaries use ambient on incoming flow. Original contracts retained; geometry/domain/materials/heat loads/locations unchanged. Diagnostic proposal only, fresh workflow review required."
                                                   if steady_profile else "Only workspace-relative paths remapped; geometry and engineering parameters unchanged."),
              "solver_executed": False, "workflow_completion_credit": False, "content_validated": False}
    (output / "preflight.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steady-profile", action="store_true")
    args = parser.parse_args()
    result = prepare(args.source, args.output, steady_profile=args.steady_profile)
    print(json.dumps({"alternatives": [{key: row.get(key) for key in ("alternative", "schema_status", "region_count", "error")}
                                      for row in result["alternatives"]]}))
