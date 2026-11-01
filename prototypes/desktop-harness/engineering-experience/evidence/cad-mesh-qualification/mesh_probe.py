# Provider input script: actual retained STEP -> Gmsh mesh. No load/strength claim.
import hashlib
import json
import subprocess
from pathlib import Path
import meshio
import numpy as np

source = Path("/inputs/design.step")
source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
proc = subprocess.run(
    [
        "gmsh",
        str(source),
        "-3",
        "-format",
        "msh2",
        "-o",
        "cad-mesh.msh",
        "-clmax",
        "5",
        "-clmin",
        "1",
        "-order",
        "1",
        "-v",
        "3",
    ],
    capture_output=True,
    text=True,
    timeout=90,
)
Path("gmsh.stdout").write_text(proc.stdout)
Path("gmsh.stderr").write_text(proc.stderr)
if proc.returncode:
    raise RuntimeError(f"Gmsh exited {proc.returncode}; inspect retained stderr")
mesh = meshio.read("cad-mesh.msh")
tetra = mesh.get_cells_type("tetra")
if not len(tetra):
    raise ValueError("No volume elements produced")
points = mesh.points
if not np.isfinite(points).all():
    raise ValueError("Nonfinite mesh coordinates")
a, b, c, d = [points[tetra[:, i]] for i in range(4)]
volumes = np.abs(np.einsum("ij,ij->i", b - a, np.cross(c - a, d - a))) / 6
if np.any(volumes <= 1e-12):
    raise ValueError("Degenerate tetrahedron")
meshio.write("cad-volume-mesh.vtu", meshio.Mesh(points, [("tetra", tetra)]))
report = {
    "scope": "CAD-derived volume meshing prerequisite; not strength or dimensional acceptance",
    "source_sha256": source_digest,
    "nodes": len(points),
    "tetrahedra": len(tetra),
    "minimum_tetra_volume": float(volumes.min()),
    "mesh_volume_coordinate_units_cubed": float(volumes.sum()),
    "bounds_coordinate_units": [
        points.min(axis=0).tolist(),
        points.max(axis=0).tolist(),
    ],
    "gmsh_exit": proc.returncode,
    "files": {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [Path("cad-mesh.msh"), Path("cad-volume-mesh.vtu")]
    },
}
Path("mesh-check.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report))
