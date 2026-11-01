"""Read-only projected control-hull containment against a source front contour.

A positive-basis patch or geometry contained by these controls is contained by
the projected hull when every control depth is positive. Binding that geometric
condition to an actual artifact remains the caller's responsibility. This is
not camera calibration, physical metrology, workflow execution or acceptance.
"""

from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

_missing_dependency = None
try:
    import numpy as np
    from project_mesh_to_photo import project_points
except ImportError as error:
    _missing_dependency = error.name


def convex_hull_2d(points):
    points = sorted(set(tuple(float(v) for v in p) for p in points))
    if len(points) < 3:
        raise ValueError("At least three distinct projected controls are required")

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = np.array(lower[:-1] + upper[:-1])
    if len(hull) < 3:
        raise ValueError("Projected controls are collinear")
    return hull


def certify(points, camera, front_outline):
    if _missing_dependency is not None:
        raise ModuleNotFoundError(
            "Projection capability unavailable", name=_missing_dependency
        )
    outline = np.asarray(front_outline, dtype=float)
    if (
        outline.ndim != 2
        or outline.shape[1] != 2
        or len(outline) < 2
        or not np.isfinite(outline).all()
    ):
        raise ValueError("Expected finite source [u,v] polyline points")
    if not np.all(np.diff(outline[:, 1]) > 0):
        raise ValueError("Source front contour must have strictly increasing v")
    uv, depth = project_points(points, camera)
    hull = convex_hull_2d(uv)
    vmin, vmax = float(hull[:, 1].min()), float(hull[:, 1].max())
    domain = [float(outline[0, 1]), float(outline[-1, 1])]
    report = dict(
        schema="wright.projected_control_hull_measurement/1",
        state="calculated",
        projection=camera["projection"],
        minimum_control_depth=float(depth.min()),
        projected_controls=uv.tolist(),
        projected_hull=hull.tolist(),
        projected_v_domain=[vmin, vmax],
        source_v_domain=domain,
        hull_contained=False,
        limits=[
            "Conditional on this camera and supplied source front contour; no camera/source authenticity or physical accuracy proof.",
            "Controls must contain the bound geometry, or come from a nonnegative partition-of-unity representation with positive rational weights. This utility does not verify that artifact binding.",
            "Positive perspective control depths make projected geometry a convex combination of projected controls; a failed hull check is not proof the actual surface protrudes.",
            "Piecewise-linear contour and hull are checked at every common segment break in floating point. This is not interval arithmetic or an invented observation tolerance.",
            "Read-only calculation; existing workflow validation/review owners retain authority.",
        ],
    )
    if vmin < domain[0] or vmax > domain[1]:
        report["diagnosis"] = "outside_source_domain"
        return report
    breaks = np.unique(
        np.r_[hull[:, 1], outline[(outline[:, 1] > vmin) & (outline[:, 1] < vmax), 1]]
    )
    samples = []
    for v in breaks:
        intersections = []
        for a, b in zip(hull, np.roll(hull, -1, axis=0)):
            if not min(a[1], b[1]) - 1e-10 <= v <= max(a[1], b[1]) + 1e-10:
                continue
            if abs(b[1] - a[1]) <= 1e-14:
                if abs(v - a[1]) <= 1e-10:
                    intersections.append(float(min(a[0], b[0])))
            else:
                intersections.append(
                    float(a[0] + (v - a[1]) * (b[0] - a[0]) / (b[1] - a[1]))
                )
        if not intersections:
            raise ValueError("No control-hull intersection at a declared break")
        u = min(intersections)
        bound = float(np.interp(v, outline[:, 1], outline[:, 0]))
        samples.append(
            dict(
                v=float(v),
                minimum_hull_u=u,
                source_front_u=bound,
                clearance_px=u - bound,
            )
        )
    worst = min(samples, key=lambda r: r["clearance_px"])
    report.update(
        diagnosis="hull_inside_front_bound"
        if worst["clearance_px"] >= 0
        else "control_hull_not_contained",
        hull_contained=worst["clearance_px"] >= 0,
        minimum_clearance_px=worst["clearance_px"],
        worst_break=worst,
        breaks_checked=len(samples),
        breaks=samples,
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != args.expected_sha256.lower():
        raise ValueError("Input digest changed")
    if args.report.exists():
        raise ValueError("Preserve the existing report; choose a fresh path")
    data = json.loads(raw)
    if _missing_dependency is not None:
        result = dict(
            schema="wright.projected_control_hull_measurement/1",
            state="capability_unavailable",
            diagnosis="missing_dependency",
            missing_dependency=_missing_dependency,
            hull_contained=None,
        )
    else:
        result = certify(data["control_points"], data["camera"], data["front_outline"])
    if hashlib.sha256(args.input.read_bytes()).hexdigest() != digest:
        raise ValueError("Input changed during calculation")
    result["input_sha256"] = digest
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps({k: result[k] for k in ["state", "diagnosis", "hull_contained"]}))
    return 0 if result["state"] == "calculated" else 2


if __name__ == "__main__":
    raise SystemExit(main())
