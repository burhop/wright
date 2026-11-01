"""Read-only mesh measurements for an exact artifact; acceptance stays with Wright.

Requires an independently provisioned environment with NumPy, Trimesh and
PyMeshLab. This utility does not install dependencies, execute a workflow,
repair geometry, select a printer or grant review/dispatch authority.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def measure(path: Path, expected_sha256: str, declared_units: str) -> dict:
    import numpy as np
    import pymeshlab
    import trimesh

    before = digest(path)
    if before != expected_sha256:
        raise ValueError("The artifact digest changed; measure the declared output.")
    mesh = trimesh.load_mesh(path, process=True)
    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError("Expected one mesh, not an implicitly combined scene.")
    if not len(mesh.vertices) or not len(mesh.faces):
        raise ValueError("The artifact contains no measurable triangles.")
    if not np.isfinite(mesh.vertices).all():
        raise ValueError("The artifact contains non-finite coordinates.")
    session = pymeshlab.MeshSet()
    session.add_mesh(
        pymeshlab.Mesh(
            vertex_matrix=np.asarray(mesh.vertices, dtype=np.float64),
            face_matrix=np.asarray(mesh.faces, dtype=np.int32),
        )
    )
    session.compute_selection_by_self_intersections_per_face()
    intersecting = session.current_mesh().face_selection_array()
    incidence = np.bincount(mesh.edges_unique_inverse)
    measurements = {
        "vertices": len(mesh.vertices),
        "triangles": len(mesh.faces),
        "components": len(mesh.split(only_watertight=False)),
        "watertight": bool(mesh.is_watertight),
        "consistent_winding": bool(mesh.is_winding_consistent),
        "positive_volume": bool(mesh.is_volume and mesh.volume > 0),
        "volume_in_declared_units_cubed": float(mesh.volume),
        "extents_in_declared_units": mesh.extents.tolist(),
        "minimum_triangle_area_in_declared_units_squared": float(mesh.area_faces.min()),
        "exact_zero_area_triangles": int((mesh.area_faces == 0).sum()),
        "boundary_edges": int((incidence == 1).sum()),
        "nonmanifold_edges": int((incidence > 2).sum()),
        "intersecting_faces": int(intersecting.sum()),
    }
    if digest(path) != before:
        raise ValueError("The input changed during measurement; the result is stale.")
    return {
        "schema": "wright.mesh_geometry_measurement/1",
        "state": "measured",
        "measured_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifact": {"path": str(path), "sha256": before},
        "declared_units": declared_units,
        "units_independently_verified": False,
        "measurements": measurements,
        "runtime": {
            "python": sys.version,
            "numpy": np.__version__,
            "trimesh": trimesh.__version__,
            "pymeshlab": importlib.metadata.version("pymeshlab"),
        },
        "scope": {
            "source_file_modified": False,
            "geometry_repair_performed": False,
            "vertex_import": "Ordinary Trimesh vertex merging only.",
            "intersection_count_kind": "Selected faces, not intersection pairs.",
            "acceptance_authority": "Existing workflow validation and review owners.",
            "not_established": [
                "authenticated physical dimensions",
                "complete CAD-to-mesh deviation bound",
                "minimum printable feature suitability",
                "printer/material/support settings",
                "assembly fit or human acceptance",
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mesh", type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument(
        "--declared-units", choices=("mm", "m", "unverified"), default="unverified"
    )
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    expected = args.expected_sha256.lower()
    if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
        parser.error("--expected-sha256 must contain 64 hexadecimal characters")
    if args.report.exists():
        parser.error(
            "The report already exists; preserve it and use a fresh evidence path"
        )
    try:
        result = measure(args.mesh.resolve(strict=True), expected, args.declared_units)
    except ImportError as error:
        result = {
            "schema": "wright.mesh_geometry_measurement/1",
            "state": "capability_unavailable",
            "missing_dependency": error.name,
            "measurements": None,
        }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"state": result["state"], "report": str(args.report)}))
    return 0 if result["state"] == "measured" else 2


if __name__ == "__main__":
    raise SystemExit(main())
