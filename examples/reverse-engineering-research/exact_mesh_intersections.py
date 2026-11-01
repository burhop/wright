"""Read-only cross-check of saved triangles using two exact-predicate kernels.

No tolerance-based welding, remeshing, component selection or acceptance authority.
External libigl/CGAL and predicates bindings must be provisioned independently.
"""

from pathlib import Path
import hashlib
import importlib.metadata
import time


def detect(vertices, faces):
    import igl.copyleft.cgal as cgal
    import igl.predicates as predicates
    import numpy as np

    vertices = np.ascontiguousarray(vertices, dtype=np.float64)
    faces = np.ascontiguousarray(faces, dtype=np.int64)
    found, pairs, coplanar = predicates.find_self_intersections(
        vertices, faces, first_only=False
    )
    _, _, other_pairs, _, _ = cgal.remesh_self_intersections(
        vertices, faces, detect_only=True, first_only=False
    )
    return dict(
        predicate_found=bool(found),
        predicate_pairs=pairs.tolist(),
        coplanar=coplanar.tolist(),
        CGAL_pairs=other_pairs.tolist(),
    )


def measure(path: Path, expected_sha256: str):
    import numpy as np
    import trimesh
    import igl

    started = time.monotonic()
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    if before != expected_sha256:
        raise ValueError("Input changed; inspect the declared saved artifact.")
    raw = trimesh.load_mesh(path, process=False)
    if not isinstance(raw, trimesh.Trimesh) or not np.isfinite(raw.vertices).all():
        raise ValueError("Expected one finite triangle mesh.")
    triangles = raw.triangles
    vertices, inverse = np.unique(triangles.reshape(-1, 3), axis=0, return_inverse=True)
    faces = inverse.reshape(-1, 3).astype(np.int64)
    if not np.array_equal(vertices[faces], triangles):
        raise ValueError("Exact vertex association changed coordinates.")
    sorted_faces = np.sort(faces, axis=1)
    duplicates = len(faces) - len(np.unique(sorted_faces, axis=0))
    zero = int(
        (
            np.linalg.norm(
                np.cross(
                    triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
                ),
                axis=1,
            )
            == 0
        ).sum()
    )
    result = detect(vertices, faces)
    if hashlib.sha256(path.read_bytes()).hexdigest() != before:
        raise ValueError("Input changed during inspection.")
    binaries = [
        p
        for p in Path(igl.__file__).parent.rglob("*.pyd")
        if "cgal" in p.name or "predicates" in p.name
    ]
    if len(binaries) != 2:
        raise ValueError("Could not identify both native intersection bindings.")
    return dict(
        schema="wright.exact_mesh_intersection_observation/1",
        source=dict(path=str(path), sha256=before),
        triangles=len(faces),
        exact_unique_vertices=len(vertices),
        exact_zero_area_triangles=zero,
        duplicate_coordinate_faces=duplicates,
        exact_coordinate_identity=True,
        predicate_pair_count=len(result["predicate_pairs"]),
        CGAL_pair_count=len(result["CGAL_pairs"]),
        **result,
        elapsed_seconds=time.monotonic() - started,
        runtime=dict(
            libigl=importlib.metadata.version("libigl"),
            numpy=np.__version__,
            trimesh=trimesh.__version__,
            helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            binaries={
                p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in binaries
            },
        ),
        scope="Complete saved-mesh pair detection, excluding legitimate shared simplices per library contracts. Degeneracy and duplicate counts are separate. No geometry changes, physical fidelity or print acceptance.",
    )
