import argparse
import hashlib
import io
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

MAX_PIXELS = 20_000_000
MAX_TRIANGLES = 100_000
MAX_TESTS = 150_000_000
ROT_ATOL = 1e-9  # Numerical rotation-validation tolerance, not engineering tolerance.


def require(condition, message):
    if not condition:
        raise ValueError(message)


def numeric_array(value, name):
    a = np.asarray(value)
    require(a.dtype.kind in "iuf", name + ": numeric values required")
    a = a.astype(np.float64)
    require(np.isfinite(a).all(), name + ": nonfinite values")
    return a


def validate_camera(c):
    require(isinstance(c, dict), "camera must be an object")
    require(c["projection"] in ("perspective", "orthographic"), "invalid projection")
    require(c["distortion"] == "none_assumed", "distortion must be none_assumed")
    require(
        isinstance(c["provenance"], str) and c["provenance"].strip(),
        "nonempty camera hypothesis provenance required",
    )
    for key in ("width_px", "height_px"):
        require(type(c[key]) is int and c[key] > 0, key + ": positive integer required")
    require(c["width_px"] * c["height_px"] <= MAX_PIXELS, "image pixel limit exceeded")
    for key in ("fx", "fy", "cx_px", "cy_px", "near_mm"):
        require(
            type(c[key]) in (int, float) and math.isfinite(c[key]),
            key + ": finite number required",
        )
    require(
        c["fx"] > 0 and c["fy"] > 0 and c["near_mm"] > 0,
        "fx, fy and near_mm must be positive",
    )
    r = numeric_array(c["R_world_to_camera"], "R_world_to_camera")
    t = numeric_array(c["t_world_to_camera_mm"], "t_world_to_camera_mm")
    require(r.shape == (3, 3) and t.shape == (3,), "invalid rotation/translation shape")
    require(
        np.allclose(r @ r.T, np.eye(3), atol=ROT_ATOL, rtol=0)
        and abs(np.linalg.det(r) - 1) <= ROT_ATOL,
        "R must be orthonormal with det +1",
    )
    return r, t


def project_points(points, camera):
    # Returns (N, 2) original-raster pixel centers and (N,) camera-space z in mm.
    r, t = validate_camera(camera)
    p = numeric_array(points, "points")
    require(
        p.ndim == 2 and p.shape[1] == 3 and len(p) > 0, "points must be nonempty Nx3"
    )
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        q = p @ r.T + t
        require(np.isfinite(q).all(), "nonfinite transformed coordinates")
        bad = int(np.count_nonzero(q[:, 2] < camera["near_mm"]))
        require(
            bad == 0,
            f"near-plane rejection: {bad} vertices below near_mm; no clipping implemented",
        )
        xy = q[:, :2].copy()
        if camera["projection"] == "perspective":
            xy /= q[:, 2, None]
        xy = xy * [camera["fx"], camera["fy"]] + [camera["cx_px"], camera["cy_px"]]
        require(np.isfinite(xy).all(), "nonfinite projected coordinates")
    return xy, q[:, 2].copy()


def rasterize(points, triangles, camera):
    # Returns mask uint8 (0/255), depth float64 (mm, NaN background), gray shade, stats.
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        return _rasterize(points, triangles, camera)


def _rasterize(points, triangles, c):
    p = numeric_array(points, "points")
    uv, z = project_points(p, c)
    tri = np.asarray(triangles)
    require(
        tri.ndim == 2 and tri.shape[1] == 3 and len(tri) > 0,
        "triangles must be nonempty Mx3",
    )
    require(len(tri) <= MAX_TRIANGLES, "triangle count limit exceeded")
    require(
        tri.dtype.kind in "iu", "triangle indices must be integers, not booleans/floats"
    )
    require(np.all(tri >= 0) and np.all(tri < len(p)), "triangle index out of range")
    tri = tri.astype(np.int64)
    normals = np.cross(p[tri[:, 1]] - p[tri[:, 0]], p[tri[:, 2]] - p[tri[:, 0]])
    lengths = np.hypot(np.hypot(normals[:, 0], normals[:, 1]), normals[:, 2])
    degenerate = int(np.count_nonzero(lengths == 0))
    require(
        degenerate == 0,
        f"degenerate triangles: {degenerate} of {len(tri)}; rendering rejected",
    )
    require(np.isfinite(lengths).all(), "triangle normal overflow")
    r = np.asarray(c["R_world_to_camera"], dtype=np.float64)
    nz = (normals / lengths[:, None]) @ r[2]
    intensities = np.rint(60 + 195 * np.clip(np.abs(nz), 0, 1)).astype(np.uint8)
    w, h = c["width_px"], c["height_px"]
    jobs, work, screen_degenerate, outside = [], 0, 0, 0
    for k, ids in enumerate(tri):
        a, b, d = uv[ids]
        den = (b[1] - d[1]) * (a[0] - d[0]) + (d[0] - b[0]) * (a[1] - d[1])
        if den == 0:
            screen_degenerate += 1
            continue
        lo, hi = uv[ids].min(axis=0), uv[ids].max(axis=0)
        if hi[0] < 0 or hi[1] < 0 or lo[0] > w - 1 or lo[1] > h - 1:
            outside += 1
            continue
        x0, y0 = math.ceil(max(0, lo[0])), math.ceil(max(0, lo[1]))
        x1, y1 = math.floor(min(w - 1, hi[0])), math.floor(min(h - 1, hi[1]))
        if x0 > x1 or y0 > y1:
            outside += 1
            continue
        work += (x1 - x0 + 1) * (y1 - y0 + 1)
        require(
            work <= MAX_TESTS,
            f"projected bbox workload exceeds {MAX_TESTS} pixel tests",
        )
        jobs.append((k, x0, y0, x1, y1, den))
    depth = np.full((h, w), np.inf, dtype=np.float64)
    shade = np.zeros((h, w), dtype=np.uint8)
    updated_triangles, updates = 0, 0
    for k, x0, y0, x1, y1, den in jobs:
        ids = tri[k]
        a, b, d = uv[ids]
        zz = z[ids]
        xs = np.arange(x0, x1 + 1, dtype=np.float64)[None, :]
        rows = max(1, 65536 // (x1 - x0 + 1))
        touched = False
        for first in range(y0, y1 + 1, rows):
            last = min(y1 + 1, first + rows)
            ys = np.arange(first, last, dtype=np.float64)[:, None]
            b0 = ((b[1] - d[1]) * (xs - d[0]) + (d[0] - b[0]) * (ys - d[1])) / den
            b1 = ((d[1] - a[1]) * (xs - d[0]) + (a[0] - d[0]) * (ys - d[1])) / den
            b2 = 1 - b0 - b1
            covered = (b0 >= 0) & (b1 >= 0) & (b2 >= 0)
            iy, ix = np.nonzero(covered)
            if not len(iy):
                continue
            weights = np.stack((b0[iy, ix], b1[iy, ix], b2[iy, ix]), axis=1)
            if c["projection"] == "perspective":
                candidate = 1 / np.sum(weights / zz, axis=1)
            else:
                candidate = np.sum(weights * zz, axis=1)
            require(
                np.isfinite(candidate).all() and np.all(candidate > 0),
                "nonfinite/nonpositive interpolated depth",
            )
            view = depth[first:last, x0 : x1 + 1]
            win = (
                candidate < view[iy, ix]
            )  # Equal-depth ties keep earlier input triangle.
            if np.any(win):
                yy, xx = iy[win], ix[win]
                view[yy, xx] = candidate[win]
                shade[first:last, x0 : x1 + 1][yy, xx] = intensities[k]
                updates += int(np.count_nonzero(win))
                touched = True
        updated_triangles += int(touched)
    foreground = np.isfinite(depth)
    depth[~foreground] = np.nan
    mask = foreground.astype(np.uint8) * 255
    stats = {
        "input_vertices": len(p),
        "input_triangles": len(tri),
        "degenerate_world_triangles": degenerate,
        "screen_degenerate_triangles": screen_degenerate,
        "triangles_without_viewport_pixel_bbox": outside,
        "triangles_rasterized": len(jobs),
        "triangles_with_depth_updates": updated_triangles,
        "depth_update_fragments": updates,
        "rendered_foreground_pixels": int(np.count_nonzero(foreground)),
        "bbox_pixel_tests": work,
        "projected_bounds_px": {
            "min_uv": uv.min(axis=0).tolist(),
            "max_uv": uv.max(axis=0).tolist(),
        },
    }
    return mask, depth, shade, stats


LIMITATIONS = [
    "Fixed supplied camera hypothesis only: no calibration, registration, autofit or optimization. Mathematical validity does not establish photo calibration or physical accuracy; object/camera scale ambiguity remains.",
    "Input tessellation only; STEP identity is checked but STEP geometry is not read or compared. No CAD production, solid inference, watertightness claim or volume calculation. Open surfaces render double-sided.",
    "No distortion correction, EXIF orientation transform, resize or crop. Reference and outputs use decoded original raster coordinates. Overlay is RGB; other pixels preserve decoded RGB values, not original compressed bytes or metadata.",
    "CPU float64, pixel-center single samples, inclusive floating barycentric edges, no antialiasing. Extremely small/large or ill-conditioned inputs can fail numerically; edge rounding can affect individual pixels. Exact depth ties keep first triangle.",
    "All vertices, including unused ones, must be at or beyond near_mm. No near clipping or far plane; viewport bounding boxes are clipped without discarding spanning triangles.",
    "Only nearest tessellated surface depth is retained; hidden layers and real-photo occluders are not modeled. Shading is double-sided normal contrast for visibility, not photometry.",
    "Triangle depth-update counts include triangles later occluded and are not final visible-triangle counts. Projected bounds include all input vertices and are not clipped to the raster.",
    "No observed foreground inference, target-mask comparison, similarity score, engineering threshold or approval verdict. Computational limits and rotation validation tolerance are not engineering tolerances.",
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_json(data):
    def invalid(value):
        raise ValueError("nonstandard JSON constant: " + value)

    return json.loads(data.decode("utf-8-sig"), parse_constant=invalid)


def save_image(path, array):
    with path.open("xb") as f:
        Image.fromarray(array).save(f, format="PNG")


def main():
    parser = argparse.ArgumentParser(
        description="Fixed-camera mesh projection; no photo calibration."
    )
    for option in ("mesh", "camera", "reference", "output"):
        parser.add_argument("--" + option, required=True, type=Path)
    args = parser.parse_args()
    try:
        require(
            not args.output.exists(), "output must be a NEW directory; no overwriting"
        )
        paths = {
            name: getattr(args, name).resolve(strict=True)
            for name in ("mesh", "camera", "reference")
        }
        data = {name: path.read_bytes() for name, path in paths.items()}
        mesh, camera = load_json(data["mesh"]), load_json(data["camera"])
        require(mesh["units"] == "mm", "mesh units must be mm")
        tess = mesh["tessellation"]
        require(
            isinstance(tess, (str, dict))
            and bool(tess)
            and (not isinstance(tess, str) or bool(tess.strip())),
            "descriptive tessellation settings required",
        )
        artifact = mesh["source_artifact"]
        require(
            isinstance(artifact["path"], str), "source artifact path must be a string"
        )
        source = Path(artifact["path"])
        require(
            source.is_absolute() and source.is_file(),
            "source STEP path must be absolute and exist",
        )
        require(
            source.suffix.lower() in (".step", ".stp"),
            "source artifact must be a STEP file",
        )
        expected = artifact["sha256"]
        require(
            isinstance(expected, str)
            and len(expected) == 64
            and all(ch in "0123456789abcdefABCDEF" for ch in expected),
            "invalid STEP SHA256",
        )
        with source.open("rb") as f:
            actual = hashlib.file_digest(f, "sha256").hexdigest()
        require(actual == expected.lower(), "source STEP SHA256 mismatch")
        validate_camera(camera)
        with Image.open(io.BytesIO(data["reference"])) as image:
            require(
                image.size == (camera["width_px"], camera["height_px"]),
                "reference raster size mismatch",
            )
            require(
                getattr(image, "n_frames", 1) == 1,
                "reference must be a single-frame raster",
            )
            photo = np.array(image.convert("RGB"))  # Deliberately no EXIF transpose.
        mask, depth, shade, stats = rasterize(mesh["points"], mesh["triangles"], camera)
        eroded = cv2.erode(
            mask,
            np.ones((3, 3), np.uint8),
            borderType=cv2.BORDER_CONSTANT,
            borderValue=0,
        )
        photo[(mask != 0) & (eroded == 0)] = (255, 40, 0)
        report = {
            "schema_version": "wright.fixed-camera-mesh-projection/1",
            "inputs": {
                n: {"path": str(paths[n]), "sha256": digest(data[n])} for n in paths
            },
            "pixel_frame": {
                "schema_version": "wright.image-coordinate-frame/1",
                "image_sha256": digest(data["reference"]),
                "width_px": camera["width_px"],
                "height_px": camera["height_px"],
                "axes": "x-right-y-down",
                "origin": "top-left",
                "pixel_reference": "centers",
            },
            "camera": camera,
            "camera_axes": "x-right-y-down-z-forward",
            "camera_hypothesis_provenance": camera["provenance"],
            "focal_parameter_units": "pixels"
            if camera["projection"] == "perspective"
            else "px/mm",
            "depth_units": "camera mm",
            "source_artifact": artifact,
            "verified_step_sha256": actual,
            "tessellation": tess,
            "render": stats,
            "computational_policy": {
                "max_image_pixels": MAX_PIXELS,
                "max_triangles": MAX_TRIANGLES,
                "max_bbox_pixel_tests": MAX_TESTS,
                "rotation_absolute_tolerance": ROT_ATOL,
                "backface_culling": False,
                "sampling": "integer pixel centers",
            },
            "outputs": [
                "mask.png",
                "depth.npy",
                "shaded.png",
                "overlay.png",
                "report.json",
            ],
            "limitations": LIMITATIONS,
        }
        encoded = json.dumps(
            report, indent=2, ensure_ascii=True, allow_nan=False
        ).encode("utf-8")
        args.output.mkdir(
            exist_ok=False
        )  # Existing parent required; exclusive directory creation.
        save_image(args.output / "mask.png", mask)
        with (args.output / "depth.npy").open("xb") as f:
            np.save(f, depth, allow_pickle=False)
        save_image(args.output / "shaded.png", shade)
        save_image(args.output / "overlay.png", photo)
        with (args.output / "report.json").open("xb") as f:
            f.write(
                encoded
            )  # Written last; successful exit is required for completion.
        return 0
    except Exception as exc:
        print(
            f"ERROR {type(exc).__name__}: {exc}. No successful result; any newly created output directory may contain partial files. Inputs were not modified.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
