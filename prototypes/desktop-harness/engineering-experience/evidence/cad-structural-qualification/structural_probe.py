"""Numerical handoff fixture, not an accepted handle design or material model."""

import csv
import hashlib
import json
from pathlib import Path
import meshio
import numpy as np
from skfem import Basis, ElementVector, ElementTetP1, MeshTet, asm, condense, solve
from skfem.models.elasticity import linear_elasticity

mesh_path = Path("/mesh/cad-mesh.msh")
step_path = Path("/inputs/design.step")
assert "SI_UNIT(.MILLI.,.METRE.)" in step_path.read_text()
mesh = meshio.read(mesh_path)
cells = mesh.get_cells_type("tetra")
model = MeshTet(mesh.points.T, cells.T)
basis = Basis(model, ElementVector(ElementTetP1()))
# Synthetic numerical-check conditions; not approved PETG/handle requirements.
E, nu = 1000.0, 0.3
lam, mu = E * nu / ((1 + nu) * (1 - 2 * nu)), E / (2 * (1 + nu))
stiffness = asm(linear_elasticity(lam, mu), basis)
fixed_nodes = np.flatnonzero(np.isclose(model.p[0], model.p[0].min()))
loaded_nodes = np.flatnonzero(np.isclose(model.p[0], model.p[0].max()))
assert len(fixed_nodes) > 2 and len(loaded_nodes) > 2
fixed = basis.get_dofs(nodes=fixed_nodes).all()
free = np.setdiff1d(np.arange(basis.N), fixed)
records = []
for force in (1.0, 2.0):
    prefix = f"force-{int(force)}n"
    load = np.zeros(basis.N)
    load[basis.nodal_dofs[2, loaded_nodes]] = -force / len(loaded_nodes)
    displacement = solve(*condense(stiffness, load, D=fixed))
    residual = stiffness @ displacement - load
    assert np.isfinite(displacement).all()
    assert np.max(np.abs(residual[free])) < 1e-8
    reaction = residual[basis.nodal_dofs].sum(axis=1)
    assert np.max(np.abs(reaction + [0, 0, -force])) < 1e-8
    gradient = basis.interpolate(displacement).grad
    strain = (gradient + gradient.swapaxes(0, 1)) / 2
    stress = (
        2 * mu * strain
        + lam
        * np.eye(3)[:, :, None, None]
        * np.trace(strain, axis1=0, axis2=1)[None, None, :, :]
    )
    nodal = displacement[basis.nodal_dofs].T
    with Path(prefix + "-displacement.csv").open("w") as file:
        writer = csv.writer(file)
        writer.writerow(["node_id", "ux_mm", "uy_mm", "uz_mm"])
        writer.writerows((i + 1, *row) for i, row in enumerate(nodal))
    with Path(prefix + "-stress.csv").open("w") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "element_id",
                "integration_point",
                "sxx_mpa",
                "syy_mpa",
                "szz_mpa",
                "sxy_mpa",
                "sxz_mpa",
                "syz_mpa",
            ]
        )
        for element in range(stress.shape[2]):
            for point in range(stress.shape[3]):
                tensor = stress[:, :, element, point]
                writer.writerow(
                    [
                        element + 1,
                        point + 1,
                        tensor[0, 0],
                        tensor[1, 1],
                        tensor[2, 2],
                        tensor[0, 1],
                        tensor[0, 2],
                        tensor[1, 2],
                    ]
                )
    with Path(prefix + "-balance.csv").open("w") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["node_id", "fixed", "fx_n", "fy_n", "fz_n", "rx_n", "ry_n", "rz_n"]
        )
        writer.writerows(
            (
                i + 1,
                int(i in fixed_nodes),
                *load[basis.nodal_dofs[:, i]],
                *residual[basis.nodal_dofs[:, i]],
            )
            for i in range(model.p.shape[1])
        )
    meshio.write(
        prefix + "-displacement.vtu",
        meshio.Mesh(
            model.p.T, [("tetra", model.t.T)], point_data={"displacement_mm": nodal}
        ),
    )
    records.append(
        {
            "force_n": force,
            "fixed_nodes": len(fixed_nodes),
            "loaded_nodes": len(loaded_nodes),
            "maximum_displacement_mm": float(np.linalg.norm(nodal, axis=1).max()),
            "reaction_n": reaction.tolist(),
            "strain_energy_n_mm": float(displacement @ (stiffness @ displacement) / 2),
            "free_residual_max_n": float(np.max(np.abs(residual[free]))),
        }
    )
report = {
    "scope": "synthetic linear-elastic numerical handoff on retained CAD-derived mesh; no strength acceptance",
    "material_fixture": {"youngs_modulus_mpa": E, "poisson_ratio": nu},
    "supports": "all translations fixed on x-min nodes",
    "load": "distributed negative z nodal load on x-max nodes",
    "source_sha256": hashlib.sha256(step_path.read_bytes()).hexdigest(),
    "mesh_sha256": hashlib.sha256(mesh_path.read_bytes()).hexdigest(),
    "nodes": model.p.shape[1],
    "tetrahedra": model.t.shape[1],
    "cases": records,
    "files": {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(Path(".").glob("force-*"))
    },
}
Path("structural-check.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report))
