"""Explicit tiny OCC-derived CHT prerequisite; never a Pi workflow or campaign result."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import gmsh

from pi_cfd_operations import prepare, solve_and_extract


def run(root, attempt, fan=False):
    root = Path(root).resolve()
    directory = root/attempt
    directory.mkdir()
    cad = directory/"cad"
    cad.mkdir()
    shutil.copyfile(__file__, cad/"qualification-geometry-source.py")
    rows = []
    for identity in ("air", "shell", "heater"):
        gmsh.initialize()
        try:
            gmsh.model.add(identity)
            if identity == "air":
                air = gmsh.model.occ.addBox(0, 0, 2, 20, 16, 8)
                heater = gmsh.model.occ.addBox(8, 6, 2, 4, 4, 2)
                gmsh.model.occ.cut([(3, air)], [(3, heater)])
            elif identity == "shell":
                gmsh.model.occ.addBox(0, 0, 0, 20, 16, 2)
            else:
                gmsh.model.occ.addBox(8, 6, 2, 4, 4, 2)
            gmsh.model.occ.synchronize()
            path = cad/(identity+".step")
            gmsh.write(str(path))
            material = {"rho": 1.18, "cp": 1005, "kappa": .026} if identity == "air" else {"rho": 1270, "cp": 1200, "kappa": .2} if identity == "shell" else {"rho": 2700, "cp": 900, "kappa": 120}
            rows.append({"name": identity, "kind": "fluid" if identity == "air" else "solid", "step": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "material": material, "heat_w": .2 if identity == "heater" else 0})
        finally:
            gmsh.finalize()
    contract = {"schema_version": 1, "units": "mm", "ambient_k": 298.15, "gravity_m_s2": [0, 0, -9.81],
                "mesh_size_mm": 2, "duration_s": .02, "delta_t_s": .001, "regions": rows,
                "boundaries": [{"name": label, "region": "air", "axis": 0, "coordinate_mm": coordinate, "tolerance_mm": .001, "role": "ambient"} for label, coordinate in (("left_ambient", 0), ("right_ambient", 20))],
                "assumptions": ["Tiny independent prerequisite CAD, not a supplied Pi model", "Laminar ideal gas; transient demonstration only; no steady-state claim", "Exterior solid surfaces prescribed ambient; radiation omitted"]}
    if fan:
        contract["boundaries"][0]["role"] = "fan"
        contract["fan_curve"] = {"points": [[0,45],[.0003,38],[.0006,27],[.0009,12],[.0011,0]], "provenance": "synthetic_customer_curve"}
        contract["delta_t_s"] = .00001
        contract["duration_s"] = .001
    path = directory/"contract.json"
    path.write_text(json.dumps(contract, indent=2))
    prep = prepare(root, path.relative_to(root).as_posix(), attempt+"/case")
    result = solve_and_extract(directory/"case")
    report = {"scope": "Independent actual OCC CAD to conformal mesh to CHT fields prerequisite; not Pi campaign", "preparation": prep, "result": result, "campaign_credit": 0}
    (directory/"evidence.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"status": "actual_prerequisite_executed", "evidence": str(directory/"evidence.json")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--attempt", required=True)
    parser.add_argument("--fan", action="store_true")
    args = parser.parse_args()
    run(args.root, args.attempt, args.fan)
