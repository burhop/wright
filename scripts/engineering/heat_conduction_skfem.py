"""Actual 3D steady conduction FE operation for the bounded heat-link inputs.

Execute inside the selected OASiS/scikit-fem environment. OASiS input_content
sets HEAT_CONFIG before this source; standalone use accepts a JSON config path.
Temperature DOFs come from assembled linear systems, never the analytical bar
formula. Analytical and mesh comparisons are original workflow outputs.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import sys

import meshio
import numpy as np
from skfem import Basis, BilinearForm, ElementTetP1, FacetBasis, LinearForm, MeshTet, asm, condense, solve
from skfem.helpers import dot, grad


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(config):
    output = Path(config["output_root"]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    rows = config.get("cases")
    if rows is None:
        with Path(config["alternatives_csv"]).open(newline="") as stream:
            rows = list(csv.DictReader(stream))
    summary = []
    for row in rows:
        name = str(row["case_id"])
        if not name.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Unsafe case identifier")
        length, width, thick = (float(row[key]) / 1000 for key in ("length_mm", "width_mm", "thickness_mm"))
        k = float(row["conductivity_w_mk"])
        heat = float(row["heat_input_w"])
        cold = float(row.get("cold_face_temperature_c", row.get("rail_temperature_c")))
        resistance = float(row.get("total_contact_resistance_k_per_w", 0))
        if min(length, width, thick, k) <= 0 or heat < 0 or resistance < 0:
            raise ValueError("Invalid physical dimensions or constants")
        area = width * thick
        geometry = None
        if config.get("geometry_root"):
            step = Path(config["geometry_root"]) / (name + ".step")
            if not step.is_file() or not step.stat().st_size:
                raise ValueError("Missing same-run CAD: " + str(step))
            geometry = {"path": str(step), "sha256": digest(step)}
            measurements_document = json.loads(
                Path(config["geometry_measurements"]).read_text()
            )
            # AgentCAD authors may include provenance beside the case map. Both
            # accepted shapes retain the same exact per-case dimensions/hash.
            measurements = measurements_document.get("cases", measurements_document)
            if not isinstance(measurements, dict) or name not in measurements:
                raise ValueError("Geometry measurements omit exact case: " + name)
            measurements = measurements[name]
            if measurements["step_sha256"] != geometry["sha256"]:
                raise ValueError("CAD measurement identity differs from actual STEP")
            measured = tuple(float(measurements["dimensions_mm"][axis]) / 1000 for axis in ("x", "y", "z"))
            if not np.allclose(measured, (length, width, thick), rtol=0, atol=1e-8):
                raise ValueError("Actual measured rectangular CAD differs from the approved thermal model")
            length, width, thick = measured
            area = width * thick
        levels = []
        for refinement, divisions in (("coarse", (8, 4, 2)), ("fine", (16, 8, 4))):
            mesh = MeshTet.init_tensor(*(np.linspace(0, extent, count + 1)
                                        for extent, count in zip((length, width, thick), divisions)))
            element = ElementTetP1()
            basis = Basis(mesh, element)
            cold_facets = mesh.facets_satisfying(lambda x: np.isclose(x[0], 0, atol=1e-12))
            hot_facets = mesh.facets_satisfying(lambda x: np.isclose(x[0], length, atol=1e-12))
            cold_basis = FacetBasis(mesh, element, facets=cold_facets)
            hot_basis = FacetBasis(mesh, element, facets=hot_facets)

            @BilinearForm
            def conduction(u, v, w):
                return k * dot(grad(u), grad(v))

            @LinearForm
            def surface(v, w):
                return v

            @BilinearForm
            def robin(u, v, w):
                return u * v

            matrix = asm(conduction, basis)
            source = (heat / area) * asm(surface, hot_basis)
            cold_weights = asm(surface, cold_basis)
            if resistance:
                coefficient = 1 / (resistance * area)
                matrix = matrix + coefficient * asm(robin, cold_basis)
                rhs = source + coefficient * cold * cold_weights
                temperature = solve(matrix, rhs)
                removed = coefficient * float(cold_weights @ (temperature - cold))
            else:
                coefficient = None
                fixed = basis.get_dofs(facets=cold_facets).all()
                initial = np.full(basis.N, cold)
                temperature = solve(*condense(matrix, source, x=initial, D=fixed))
                reaction = matrix @ temperature - source
                removed = -float(reaction[fixed].sum())
            target = output / (name + "-" + refinement + "-temperature.vtu")
            meshio.write_points_cells(target, mesh.p.T, [("tetra", mesh.t.T)],
                                      point_data={"temperature_c": temperature})
            csv_path = output / (name + "-" + refinement + "-temperature.csv")
            np.savetxt(csv_path, np.column_stack((mesh.p.T, temperature)), delimiter=",",
                       header="x_m,y_m,z_m,temperature_c", comments="")
            maximum = float(temperature.max())
            analytical = cold + heat * (length / (k * area) + resistance)
            levels.append({"mesh": refinement, "divisions": divisions, "nodes": int(basis.N),
                           "elements": int(mesh.t.shape[1]), "maximum_temperature_c": maximum,
                           "minimum_temperature_c": float(temperature.min()),
                           "heat_input_w": float(source.sum()), "heat_removed_w": removed,
                           "relative_heat_imbalance": abs(float(source.sum()) - removed) / max(abs(heat), 1e-15),
                           "analytical_hot_end_c": analytical,
                           "relative_analytical_rise_error": abs(maximum - analytical) / max(abs(analytical - cold), 1e-15),
                           "cold_boundary": "total-resistance Robin" if resistance else "Dirichlet",
                           "interface_coefficient_w_m2k": coefficient,
                           "field": {"path": str(target), "sha256": digest(target), "bytes": target.stat().st_size}})
        fine = levels[-1]
        sensitivity = abs(levels[0]["maximum_temperature_c"] - fine["maximum_temperature_c"]) / max(abs(fine["maximum_temperature_c"] - cold), 1e-15)
        result = {"case_id": name, "geometry": geometry, "input": row, "mesh_levels": levels,
                  "relative_mesh_sensitivity": sensitivity,
                  "mass_kg": length * width * thick * float(row["density_kg_m3"]),
                  "maximum_temperature_c": fine["maximum_temperature_c"],
                  "within_declared_limit": fine["maximum_temperature_c"] <= float(row["limit_c"]),
                  "original_workflow_checks": {"analytical_2_percent": fine["relative_analytical_rise_error"] <= .02,
                                                "mesh_2_percent": sensitivity <= .02,
                                                "heat_balance_1_percent": fine["relative_heat_imbalance"] <= .01}}
        summary.append(result)
    eligible = [r for r in summary if r["within_declared_limit"] and all(r["original_workflow_checks"].values())]
    selected = min(eligible, key=lambda r: (r["mass_kg"], r["maximum_temperature_c"])) if eligible else None
    decision = {"operation": "3D P1 tetrahedral scikit-fem conduction", "cases": summary,
                "selected_case_id": selected["case_id"] if selected else None,
                "status": "candidate_selected" if selected else "no_candidate_meets_original_checks",
                "limitations": ["Synthetic constant-property conduction model only; no physical qualification.",
                                "Uniform end loading gives a linear field exactly representable by P1 elements; mesh stability does not independently validate the physics.",
                                "Campaign correctness-validation count remains zero."]}
    (output / "sizing-decision.json").write_text(json.dumps(decision, indent=2) + "\n")
    (output / "heat-balance.json").write_text(json.dumps({r["case_id"]: r["mesh_levels"] for r in summary}, indent=2) + "\n")
    (output / "mesh-comparison.json").write_text(json.dumps({r["case_id"]: r["relative_mesh_sensitivity"] for r in summary}, indent=2) + "\n")
    print(json.dumps({"status": decision["status"], "case_count": len(summary), "output_root": str(output)}))
    return decision


if __name__ == "__main__":
    configuration = globals().get("HEAT_CONFIG")
    if configuration is None:
        configuration = json.loads(Path(sys.argv[1]).read_text())
    run(configuration)
