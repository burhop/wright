"""Bounded numerical camera checks on the existing asymmetric-box fixture.

Uses VTK's actual camera transform and an independent pinhole calculation.
Not CAD production, raster visibility, photo calibration or MCP qualification.
"""

from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import sys

import numpy as np
from vtkmodules.vtkRenderingCore import vtkCamera
from vtkmodules.vtkCommonCore import vtkVersion


def pinhole(points, focal_px=800.0, depth_mm=100.0, cx=512.0, cy=384.0):
    points = np.asarray(points, dtype=float)
    z = points[:, 2] + depth_mm
    if not np.isfinite(points).all() or not np.isfinite(z).all() or (z <= 0).any():
        raise ValueError("Points must be finite and in front of camera")
    return points[:, :2] / z[:, None] * focal_px + [cx, cy]


def vtk_project(points):
    camera = vtkCamera()
    camera.SetPosition(0, 0, -100)
    camera.SetFocalPoint(0, 0, 0)
    camera.SetViewUp(0, -1, 0)
    camera.SetViewAngle(math.degrees(2 * math.atan(768 / (2 * 800))))
    camera.SetClippingRange(1, 1000)
    transform = camera.GetCompositeProjectionTransformMatrix(1024 / 768, -1, 1)
    result = []
    for point in points:
        clip = transform.MultiplyPoint((*point, 1))
        ndc = np.array(clip[:3]) / clip[3]
        result.append([(ndc[0] + 1) * 512, (1 - ndc[1]) * 384])
    return np.array(result)


def bounds(uv):
    return np.concatenate([uv.min(axis=0), uv.max(axis=0)])


def qualify(points):
    expected = pinhole(points)
    actual = vtk_project(points)
    tests = []

    def add(name, passed, value, scope):
        tests.append(
            {"id": name, "passed": bool(passed), "observation": value, "scope": scope}
        )

    residual = float(np.abs(actual - expected).max())
    add(
        "vtk_matches_independent_pinhole",
        residual < 1e-9,
        residual,
        "maximum coordinate residual in pixels; exact synthetic camera only",
    )
    scaled = pinhole(points * 1.1)
    residual = float(np.linalg.norm(scaled - expected, axis=1).max())
    add(
        "wrong_scale_detected_at_fixed_camera",
        residual > 1,
        residual,
        "10 percent scale change; synthetic diagnostic threshold 1 px",
    )
    shifted = points.copy()
    shifted[:, 0] += 20
    residual = float(np.linalg.norm(pinhole(shifted) - expected, axis=1).max())
    add(
        "wrong_camera_translation_detected",
        residual > 100,
        residual,
        "camera-relative 20 mm translation; do not correct CAD to compensate",
    )
    mirrored = points.copy()
    mirrored[:, 0] *= -1
    residual = float(np.linalg.norm(pinhole(mirrored) - expected, axis=1).max())
    add(
        "mirrored_frame_detected",
        residual > 100,
        residual,
        "labelled corner correspondences",
    )
    residual = float(np.abs(pinhole(points * 1.1, depth_mm=110) - expected).max())
    add(
        "joint_scale_camera_ambiguity_exposed",
        residual < 1e-9,
        residual,
        "metric scale is unobservable when object and camera translation scale together",
    )
    deep = points.copy()
    deep[:, 2] *= 2
    residual = float(np.abs(bounds(pinhole(deep)) - bounds(expected)).max())
    add(
        "outer_outline_cannot_accept_hidden_depth",
        residual < 1e-9,
        {
            "outline_residual_px": residual,
            "reference_depth_mm": float(np.ptp(points[:, 2])),
            "changed_depth_mm": float(np.ptp(deep[:, 2])),
        },
        "axis-aligned box outline only; hidden depth requires a separate observation",
    )
    cropped = expected - [100, 50]
    restored = cropped + [100, 50]
    add(
        "crop_offset_must_be_restored",
        np.allclose(restored, expected) and not np.allclose(cropped, expected),
        {"crop_origin_px": [100, 50]},
        "coordinate transform, not a new independent image",
    )
    rejected = False
    try:
        pinhole(np.array([[0.0, 0.0, -100.0]]))
    except ValueError:
        rejected = True
    add(
        "nonpositive_depth_rejected",
        rejected,
        None,
        "singular projection must not yield a pass",
    )
    return tests


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.fixture_directory.resolve()))
    from synthetic_fixtures import asymmetric_box

    fixture = asymmetric_box()
    args.output.mkdir(parents=True, exist_ok=False)
    mesh = {
        "points": fixture.points.tolist(),
        "triangles": fixture.triangles.tolist(),
        "units": "mm",
        "basis": "existing synthetic 30 x 17 x 9 mm asymmetric box",
    }
    mesh_path = args.output / "fixture.json"
    mesh_path.write_text(json.dumps(mesh, indent=2), encoding="utf-8")
    tests = qualify(fixture.points)
    report = {
        "status": "pass" if all(t["passed"] for t in tests) else "fail",
        "scope": "numerical camera/observability controls only",
        "cases": tests,
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "vtk": vtkVersion.GetVTKVersion(),
        },
        "fixture_sha256": hashlib.sha256(mesh_path.read_bytes()).hexdigest(),
        "source_hashes": {
            name: hashlib.sha256(
                (args.fixture_directory / name).read_bytes()
            ).hexdigest()
            for name in ["synthetic_fixtures.py", "re_geometry.py"]
        },
        "method_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "camera": {
            "resolution_px": [1024, 768],
            "focal_px": 800,
            "position_mm": [0, 0, -100],
            "vtk_view_up": [0, -1, 0],
            "distortion": "synthetic zero",
            "image_origin": "top left",
        },
        "unqualified": [
            "lens distortion",
            "raster masks and occlusion",
            "real-photo calibration",
            "uncertainty budget",
            "mesh surface accuracy",
            "provider integration",
            "Roadster reconstruction",
        ],
    }
    (args.output / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "passed": sum(t["passed"] for t in tests),
                "total": len(tests),
            }
        )
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
