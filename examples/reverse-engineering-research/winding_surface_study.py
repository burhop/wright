"""Bounded local print-representation study using an external geometry library.

Not a workflow executor, mesh-repair acceptance gate, or CAD replacement. Input
triangle soup and inferred material interpretation stay explicit. The caller
must bound wall time and independently validate the exact resulting bytes.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path
import time


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def binary_stl(path: Path, expected: str, maximum_zero_faces: int):
    import numpy as np

    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("Input artifact changed.")
    count = int.from_bytes(raw[80:84], "little")
    if len(raw) != 84 + 50 * count:
        raise ValueError("Expected a complete binary STL.")
    dtype = np.dtype(
        [("normal", "<f4", (3,)), ("vertices", "<f4", (3, 3)), ("attribute", "<u2")]
    )
    triangles = np.frombuffer(raw, dtype=dtype, offset=84, count=count)[
        "vertices"
    ].astype(np.float64)
    if not np.isfinite(triangles).all():
        raise ValueError("Non-finite input coordinates.")
    cross = np.cross(
        triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
    )
    zero = np.linalg.norm(cross, axis=1) == 0
    removed = int(zero.sum())
    if removed > maximum_zero_faces:
        raise ValueError("Exact-zero triangle removal exceeds the declared bound.")
    # Exact identity only: do not round or move positive-area source vertices.
    vertices, inverse = np.unique(
        triangles[~zero].reshape(-1, 3), axis=0, return_inverse=True
    )
    return vertices, inverse.reshape(-1, 3).astype(np.int64), removed


def reconstruct(
    path: Path,
    expected_sha256: str,
    output: Path,
    *,
    units: str,
    longest_side_cells: int,
    maximum_grid_nodes: int,
    maximum_output_triangles: int,
    maximum_zero_faces: int,
    interpretation: str,
    contourer: str = "libigl",
    offset_mm: float = 0.0,
) -> dict:
    import igl
    import numpy as np
    import trimesh

    helper_digest = sha256(Path(__file__))
    if units != "mm" or interpretation != "positive_oriented_winding_material":
        raise ValueError(
            "Declare millimetres and the material interpretation explicitly."
        )
    if not 16 <= longest_side_cells <= 1024 or maximum_grid_nodes <= 0:
        raise ValueError("Invalid bounded grid configuration.")
    if maximum_zero_faces < 0 or maximum_output_triangles <= 0:
        raise ValueError("Invalid face bounds.")
    if contourer not in {"libigl", "lewiner"}:
        raise ValueError("Select an explicit supported contouring algorithm.")
    if not np.isfinite(offset_mm) or abs(offset_mm) > 0.01:
        raise ValueError("This study supports only an explicit offset within0.01mm.")
    if output.exists():
        raise FileExistsError("Preserve an existing study.")
    vertices, faces, removed = binary_stl(path, expected_sha256, maximum_zero_faces)
    extent = np.ptp(vertices, axis=0)
    if np.any(extent <= 0):
        raise ValueError("Expected a nonzero three-dimensional extent.")
    # Conservative preflight for the documented regular grid and padding.
    side_bound = (
        np.ceil((longest_side_cells + 10) * extent / extent.max()).astype(int) + 10
    )
    node_bound = int(np.prod(side_bound))
    if node_bound > maximum_grid_nodes:
        raise ValueError(
            "Conservative grid estimate exceeds the declared memory bound."
        )
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    sv, sf, gv, side, distance = igl.offset_surface(
        vertices,
        faces,
        offset_mm,
        longest_side_cells,
        igl.SIGNED_DISTANCE_TYPE_FAST_WINDING_NUMBER,
    )
    if contourer == "lewiner":
        from skimage.measure import marching_cubes

        axes = [np.unique(gv[:, i]) for i in range(3)]
        if tuple(map(len, axes)) != tuple(side) or not np.isfinite(distance).all():
            raise ValueError("Unexpected or incomplete scalar grid.")
        spacing = [float(a[1] - a[0]) for a in axes]
        expected_grid = np.stack(np.meshgrid(*axes, indexing="ij"), axis=-1).reshape(
            -1, 3, order="F"
        )
        if not np.allclose(gv, expected_grid, rtol=0, atol=1e-10):
            raise ValueError("Scalar-grid ordering is unqualified.")
        field = np.asarray(distance).reshape(tuple(side), order="F")
        sv, sf, _, _ = marching_cubes(
            field,
            level=offset_mm,
            spacing=tuple(spacing),
            gradient_direction="descent",
            allow_degenerate=False,
            method="lewiner",
        )
        sv = sv.astype(np.float64) + np.array([a[0] for a in axes])
    if len(gv) > maximum_grid_nodes or len(sf) > maximum_output_triangles:
        raise ValueError(
            "Actual output exceeds the declared resource bound; do not accept it."
        )
    if not len(sf) or not np.isfinite(sv).all():
        raise ValueError("No finite output surface.")
    mesh = trimesh.Trimesh(vertices=sv, faces=sf, process=False)
    target = output / "candidate.stl"
    target.write_bytes(trimesh.exchange.stl.export_stl(mesh))
    np.savez_compressed(output / "candidate.npz", vertices=sv, faces=sf)
    if sha256(path) != expected_sha256:
        raise ValueError("Input changed during reconstruction.")
    report = dict(
        schema="wright.local_winding_surface_study/1",
        state="produced_unaccepted",
        source=dict(path=str(path), sha256=expected_sha256),
        units=units,
        interpretation=interpretation,
        contourer=contourer,
        offset_mm=offset_mm,
        longest_side_cells=longest_side_cells,
        conservative_grid_node_bound=node_bound,
        actual_grid_nodes=len(gv),
        actual_side=side.tolist(),
        removed_exact_zero_area_triangles=removed,
        positive_area_triangles_deleted=0,
        source_triangles=len(faces),
        output_triangles=len(sf),
        elapsed_seconds=time.monotonic() - started,
        artifact=dict(path=str(target), sha256=sha256(target)),
        runtime=dict(
            libigl=importlib.metadata.version("libigl"),
            numpy=np.__version__,
            trimesh=trimesh.__version__,
            contourer_version=importlib.metadata.version("scikit-image")
            if contourer == "lewiner"
            else importlib.metadata.version("libigl"),
            helper_sha256=helper_digest,
        ),
        limitations=[
            "Infers material by positive oriented winding. Not measured hidden geometry.",
            "No component selection or largest-component deletion.",
            "Sampling changes representation; it does not certify CAD fidelity or printable detail.",
            "Exact output, source deviation, current-master binding and printer qualification remain required.",
        ],
    )
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
