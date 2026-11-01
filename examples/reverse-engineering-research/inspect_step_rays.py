"""Read-only STEP visibility measurements at explicit original-image pixels.

Uses the existing projection camera contract and independent CadQuery/OCCT.
No vendor protocol, model call, executor, engineering verdict or camera fitting.
"""

import argparse
import hashlib
import json
from pathlib import Path

import cadquery as cq
import numpy as np
from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
from OCP.gp import gp_Dir, gp_Lin, gp_Pnt

from compare_native_faces import runtime_info
from project_mesh_to_photo import numeric_array, require, validate_camera


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inspect(
    step,
    expected_sha256,
    camera,
    pixels,
    *,
    unit_label,
    unit_basis,
    far_depth=1e7,
    numerical_tolerance=1e-7,
):
    """Return every exact trimmed-face hit, retaining edge/tangent multiplicity.

    Face indices refer only to this exact imported STEP. Ray parameters are
    distances from the near plane along a unit world ray; camera_depth uses
    the projection contract's camera Z coordinate. Neither means recess depth
    without an explicit engineering measurement definition.
    """
    step = Path(step)
    require(
        isinstance(unit_label, str) and bool(unit_label.strip()), "unit label required"
    )
    require(
        isinstance(unit_basis, str) and bool(unit_basis.strip()), "unit basis required"
    )
    require(step.stat().st_size <= 100_000_000, "STEP exceeds 100 MB inspection limit")
    source_hash = digest(step)
    require(source_hash == expected_sha256, "STEP SHA256 mismatch")
    rotation, translation = validate_camera(camera)
    pixels = numeric_array(pixels, "pixels")
    require(
        pixels.ndim == 2 and pixels.shape[1] == 2 and 0 < len(pixels) <= 10000,
        "pixels must be nonempty Nx2, at most 10000 rays",
    )
    require(
        np.all(pixels >= 0)
        and np.all(pixels[:, 0] <= camera["width_px"] - 1)
        and np.all(pixels[:, 1] <= camera["height_px"] - 1),
        "pixel outside original image",
    )
    require(
        type(far_depth) in (int, float)
        and np.isfinite(far_depth)
        and far_depth > camera["near_mm"],
        "far depth must exceed near plane",
    )
    require(
        type(numerical_tolerance) in (int, float)
        and np.isfinite(numerical_tolerance)
        and 0 < numerical_tolerance <= 1e-3,
        "invalid numerical tolerance",
    )
    roots = cq.importers.importStep(str(step)).vals()
    require(bool(roots), "STEP has no imported roots")
    shape = roots[0] if len(roots) == 1 else cq.Compound.makeCompound(roots)
    faces = shape.Faces()
    require(0 < len(faces) <= 100000, "STEP face count outside inspection bounds")
    # OCCT's hash only narrows lookup. IsSame below establishes actual identity.
    face_buckets = {}
    for index, face in enumerate(faces):
        face_buckets.setdefault(hash(face.wrapped), []).append(index)
    intersector = IntCurvesFace_ShapeIntersector()
    intersector.Load(shape.wrapped, numerical_tolerance)
    rows = []
    for u, v in pixels:
        x, y = (
            (u - camera["cx_px"]) / camera["fx"],
            (v - camera["cy_px"]) / camera["fy"],
        )
        if camera["projection"] == "perspective":
            direction_camera = np.array([x, y, 1.0])
            direction_camera /= np.linalg.norm(direction_camera)
            near_camera = np.array([x, y, 1.0]) * camera["near_mm"]
        else:
            direction_camera = np.array([0.0, 0.0, 1.0])
            near_camera = np.array([x, y, camera["near_mm"]])
        origin = rotation.T @ (near_camera - translation)
        direction = rotation.T @ direction_camera
        distance_limit = (far_depth - camera["near_mm"]) / direction_camera[2]
        require(
            np.isfinite(origin).all()
            and np.isfinite(direction).all()
            and np.isfinite(distance_limit),
            "nonfinite ray construction",
        )
        intersector.Perform(
            gp_Lin(gp_Pnt(*origin), gp_Dir(*direction)), 0.0, float(distance_limit)
        )
        require(intersector.IsDone(), "OCCT intersection did not complete")
        hits = []
        for i in range(1, intersector.NbPnt() + 1):
            face = intersector.Face(i)
            candidates = face_buckets.get(hash(face), [])
            matched = [
                index for index in candidates if faces[index].wrapped.IsSame(face)
            ]
            require(
                len(matched) == 1,
                "intersection face does not map uniquely to exact STEP inventory",
            )
            point = np.array(intersector.Pnt(i).Coord())
            camera_point = rotation @ point + translation
            hits.append(
                dict(
                    native_face_index=matched[0],
                    ray_distance_from_near_plane=float(intersector.WParameter(i)),
                    camera_depth=float(camera_point[2]),
                    point=point.tolist(),
                )
            )
        hits.sort(
            key=lambda h: (h["ray_distance_from_near_plane"], h["native_face_index"])
        )
        nearest = (
            [
                h["native_face_index"]
                for h in hits
                if h["ray_distance_from_near_plane"]
                - hits[0]["ray_distance_from_near_plane"]
                <= numerical_tolerance
            ]
            if hits
            else []
        )
        rows.append(
            dict(
                source_pixel=[float(u), float(v)],
                origin=origin.tolist(),
                direction=direction.tolist(),
                hits=hits,
                nearest_face_indices=nearest,
            )
        )
    require(digest(step) == source_hash, "STEP changed during inspection")
    return dict(
        schema="wright.step-ray-inspection/1",
        status="measured",
        step=dict(
            path=str(step.resolve()),
            sha256=source_hash,
            bytes=step.stat().st_size,
            imported_roots=len(roots),
            faces=len(faces),
            solids=len(shape.Solids()),
            occt_valid=shape.isValid(),
        ),
        camera=camera,
        model_unit=unit_label,
        unit_basis=unit_basis,
        far_camera_depth=far_depth,
        numerical_tolerance=numerical_tolerance,
        tolerance_role="OCCT intersection and nearest-depth tie guard; not engineering acceptance tolerance.",
        runtime=runtime_info(),
        rows=rows,
        limits=[
            "Conditional recorded camera, no fitting or distortion correction.",
            "Finite rays do not prove full-feature visibility, shell closure, dimensional fidelity or human acceptance.",
            "STEP face indices are revision/import specific; semantic feature identity must be bound separately.",
            "Edge/tangent/coincident hits are retained; multiple nearest faces are not arbitrarily resolved.",
            "The existing camera keys contain mm; unit_basis must state whether that gauge has verified physical scale.",
        ],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", type=Path, required=True)
    parser.add_argument("--expected-step-sha256", required=True)
    parser.add_argument("--camera", type=Path, required=True)
    parser.add_argument(
        "--pixels",
        type=Path,
        required=True,
        help="JSON array of explicit [u,v] source pixels",
    )
    parser.add_argument("--unit-label", required=True)
    parser.add_argument("--unit-basis", required=True)
    parser.add_argument("--far-depth", type=float, default=1e7)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    # Refuse overwriting evidence. CLI input bytes are bound and checked again.
    require(not args.output.exists(), "output already exists")
    camera_bytes, pixel_bytes = args.camera.read_bytes(), args.pixels.read_bytes()
    result = inspect(
        args.step,
        args.expected_step_sha256,
        json.loads(camera_bytes),
        json.loads(pixel_bytes),
        unit_label=args.unit_label,
        unit_basis=args.unit_basis,
        far_depth=args.far_depth,
    )
    require(
        args.camera.read_bytes() == camera_bytes
        and args.pixels.read_bytes() == pixel_bytes,
        "camera or pixels changed during inspection",
    )
    result["input_files"] = {
        name: dict(path=str(path.resolve()), sha256=hashlib.sha256(data).hexdigest())
        for name, path, data in [
            ("camera", args.camera, camera_bytes),
            ("pixels", args.pixels, pixel_bytes),
        ]
    }
    result["inspector_sha256"] = digest(Path(__file__))
    result["dependency_sha256"] = {
        name: digest(Path(__file__).with_name(name))
        for name in ["project_mesh_to_photo.py", "compare_native_faces.py"]
    }
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(
        json.dumps(
            dict(
                status=result["status"],
                rays=len(result["rows"]),
                step_sha256=result["step"]["sha256"],
            )
        )
    )


if __name__ == "__main__":
    main()
