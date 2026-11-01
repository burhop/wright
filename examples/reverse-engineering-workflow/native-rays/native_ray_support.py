#!/usr/bin/env python3
"""Read-only, bounded native point-intersection diagnostic.
CLI: --input manifest.json --output NEWdirectory
     --self-test --output NEWdirectory
Only report.json is written. No STEP export, healing, Boolean edit, image I/O,
network, subprocess, plugin loading, or retry. Import this module and call
query_shape(shape, manifest) for an already guarded shared-reader shape.
That function does not establish file provenance; the caller must do so.

Implementation assumptions are recorded in report.policy. These are numerical
validation/resource conventions, NOT physical accuracy or engineering limits.
The supplied camera matrices are never fitted or orthogonalized.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import sys
from importlib import metadata

DEPENDENCY_ERROR = None
try:
    import numpy as np
    import cadquery as cq
    from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
    from OCP.gp import gp_Lin, gp_Pnt, gp_Dir
    from OCP.TopAbs import TopAbs_IN, TopAbs_ON
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.GeomAbs import GeomAbs_Plane
except Exception as exc:
    DEPENDENCY_ERROR = type(exc).__name__

POLICY = {
    "assumptions_not_engineering_requirements": True,
    "rotation_max_abs_RtR_minus_I": 1e-10,
    "rotation_abs_det_minus_one": 1e-10,
    "parallel_plane_dot_bound": 1e-12,
    "max_queries": 128,
    "max_faces": 2048,
    "max_query_face_pairs": 65536,
    "max_comparison_cameras": 8,
    "max_hits_per_query": 1024,
    "max_manifest_bytes": 2097152,
    "max_artifact_bytes": 1073741824,
    "max_runtime_file_bytes": 536870912,
    "max_abs_ray_parameter_mm": 10000000.0,
    "max_ray_span_mm": 10000000.0,
    "max_abs_world_origin_or_endpoint_mm": 10000000.0,
    "max_abs_input_pixel_coordinate": 10000000.0,
    "frame_convention": "0 <= u < width_px and 0 <= v < height_px; no half-pixel shift",
    "face_indices": "zero-based indices in this loaded shape.Faces(); not persistent names",
    "tie_policy": "all eligible hits whose distance minus minimum distance <= supplied tie_distance_mm; not transitive chaining",
    "artifact_relative_path_base": "manifest parent directory",
    "intersection_tolerance": "exactly manifest value; never enlarged",
    "planar_overlap_screen": "reject a ray parallel within the stated dot bound and within supplied intersection tolerance of a supporting plane; conservative even outside its trim",
    "kernel_query": "one bounded Perform per loaded face per query, not retries; preserves shared-edge face incidences",
    "self_test_intersection_tolerance_mm": 1e-7,
    "self_test_tie_distance_mm": 1e-7,
    "self_test_assertion_abs_bound": 1e-8,
}
LIMITS = [
    "Diagnostics completed is not physical acceptance, edit approval, or continuous pixel-region visibility certification.",
    "All reported intersections are native kernel discrete IN/ON point incidences, not tessellated depth samples.",
    "Positive-dimensional ray/surface overlaps are outside the point-intersector contract. Near-coplanar planar cases are conservatively rejected; general curved-surface overlaps are not certified by this API.",
    "Nearest means nearest within the supplied interval and mapped near plane only; a truncated interval can omit a closer support.",
    "Geometric opacity does not represent translucent glass, lighting, reflections, or photographic occluders.",
    "Uncalibrated cameras and nominal model scale do not establish physical 3D truth.",
    "Comparison-camera reprojection is not a second visibility test.",
    "Pre/post SHA256 checks detect content differences at those observations, not an atomic snapshot against an adversarial concurrent replace-and-restore. The host must keep source files immutable during reading.",
    "Runtime hashes fingerprint recorded interpreter/package files and metadata, not every transitive binary or the entire host.",
    "The single-process native kernel call has no hard wall-clock cancellation mechanism here. Counts, input sizes and ray ranges are bounded; no retries are performed.",
    "Opaque provenance is preserved as supplied. Do not place credentials in provenance.",
]


class DiagnosticError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.safe_message = message
        super().__init__(message)


def require(condition, code, message):
    if not condition:
        raise DiagnosticError(code, message)


def safe_error(exc, stage):
    if isinstance(exc, DiagnosticError):
        return {
            "category": "DiagnosticError",
            "code": exc.code,
            "message": exc.safe_message,
            "stage": stage,
        }
    allowed = {
        "ValueError",
        "TypeError",
        "RuntimeError",
        "OSError",
        "FileNotFoundError",
        "PermissionError",
        "MemoryError",
        "OverflowError",
        "RecursionError",
        "ImportError",
        "ModuleNotFoundError",
        "UnicodeDecodeError",
    }
    category = type(exc).__name__
    return {
        "category": category if category in allowed else "NativeOrRuntimeError",
        "code": "OPERATION_FAILED",
        "stage": stage,
        "message": "Operation failed. Raw exception text is withheld because it may contain paths, input data, or credentials.",
    }


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def file_hash(path, cap):
    with open(path, "rb") as stream:
        info = os.fstat(stream.fileno())
        require(
            stat.S_ISREG(info.st_mode),
            "NOT_REGULAR_FILE",
            "A regular local file is required.",
        )
        require(
            0 <= info.st_size <= cap,
            "FILE_LIMIT",
            "File exceeds the declared byte limit.",
        )
        h = hashlib.sha256()
        count = 0
        for _ in range(cap // 1048576 + 2):
            block = stream.read(min(1048576, cap - count + 1))
            if not block:
                return h.hexdigest()
            count += len(block)
            require(
                count <= cap, "FILE_LIMIT", "File grew beyond the declared byte limit."
            )
            h.update(block)
    raise DiagnosticError("FILE_LIMIT", "Bounded hashing did not reach end of file.")


def numeric(value):
    return type(value) in (int, float) and math.isfinite(value)


def vector(value, length):
    require(
        isinstance(value, list)
        and len(value) == length
        and all(numeric(x) for x in value),
        "BAD_VECTOR",
        "Expected a finite numeric vector of the declared length.",
    )
    return np.array(value, dtype=float)


def keys(value, required, optional=()):
    require(
        isinstance(value, dict)
        and set(required) <= set(value)
        and set(value) <= set(required) | set(optional),
        "SCHEMA",
        "Object keys do not match the declared schema.",
    )


def validate_camera(c):
    keys(
        c,
        (
            "projection",
            "R_world_to_camera",
            "t_world_to_camera_mm",
            "fx",
            "fy",
            "cx_px",
            "cy_px",
            "width_px",
            "height_px",
            "near_mm",
            "distortion",
        ),
        ("provenance",),
    )
    require(
        c["projection"] == "orthographic",
        "UNSUPPORTED_PROJECTION",
        "Only orthographic projection is supported.",
    )
    require(
        c["distortion"] == "none_assumed",
        "UNSUPPORTED_DISTORTION",
        "Only none_assumed distortion is supported.",
    )
    raw = c["R_world_to_camera"]
    require(
        isinstance(raw, list) and len(raw) == 3,
        "BAD_ROTATION",
        "Rotation must be a finite 3 by 3 matrix.",
    )
    R = np.stack([vector(row, 3) for row in raw])
    require(
        float(np.max(np.abs(R.T @ R - np.eye(3))))
        <= POLICY["rotation_max_abs_RtR_minus_I"]
        and abs(float(np.linalg.det(R)) - 1.0) <= POLICY["rotation_abs_det_minus_one"],
        "BAD_ROTATION",
        "Rotation violates stated orthonormal/proper numerical validation bounds.",
    )
    vector(c["t_world_to_camera_mm"], 3)
    for field in ("fx", "fy", "near_mm"):
        require(
            numeric(c[field]) and c[field] > 0,
            "BAD_CAMERA",
            "Camera scale and near distance must be positive and finite.",
        )
    for field in ("cx_px", "cy_px"):
        require(
            numeric(c[field]), "BAD_CAMERA", "Camera principal point must be finite."
        )
    for field in ("width_px", "height_px"):
        require(
            type(c[field]) is int and c[field] > 0,
            "BAD_CAMERA",
            "Frame dimensions must be positive integers.",
        )


def make_ray(c, uv, interval):
    R = np.array(c["R_world_to_camera"], dtype=float)
    t = np.array(c["t_world_to_camera_mm"], dtype=float)
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        origin = R.T @ (
            np.array(
                [(uv[0] - c["cx_px"]) / c["fx"], (uv[1] - c["cy_px"]) / c["fy"], 0.0]
            )
            - t
        )
        direction = R.T @ np.array([0.0, 0.0, 1.0])
        norm = float(np.linalg.norm(direction))
        z0 = float((R @ origin + t)[2])
        dz = float((R @ direction)[2])
        require(
            norm > 0 and dz > 0,
            "BAD_RAY",
            "Ray must advance toward increasing camera depth.",
        )
        near_parameter = (c["near_mm"] - z0) / dz
        endpoints = np.stack(
            [origin, origin + interval[0] * direction, origin + interval[1] * direction]
        )
    require(
        np.isfinite(endpoints).all()
        and np.isfinite(direction).all()
        and math.isfinite(near_parameter),
        "BAD_RAY",
        "Derived ray is nonfinite.",
    )
    require(
        float(np.max(np.abs(endpoints)))
        <= POLICY["max_abs_world_origin_or_endpoint_mm"],
        "RAY_LIMIT",
        "Derived ray exceeds the declared coordinate resource bound.",
    )
    return origin, direction, norm, near_parameter


def validate_manifest(m):
    keys(
        m,
        (
            "artifact",
            "camera",
            "queries",
            "ray_interval_mm",
            "intersection_tolerance_mm",
            "tie_distance_mm",
            "comparison_cameras",
        ),
        ("provenance",),
    )
    keys(m["artifact"], ("path", "sha256"))
    a = m["artifact"]
    require(
        isinstance(a["path"], str)
        and a["path"]
        and "\x00" not in a["path"]
        and "://" not in a["path"],
        "BAD_ARTIFACT",
        "Artifact path must be a local path.",
    )
    require(
        isinstance(a["sha256"], str)
        and len(a["sha256"]) == 64
        and all(ch in "0123456789abcdefABCDEF" for ch in a["sha256"]),
        "BAD_SHA256",
        "Artifact SHA256 must contain exactly 64 hexadecimal digits.",
    )
    validate_camera(m["camera"])
    interval = vector(m["ray_interval_mm"], 2)
    require(
        interval[0] < interval[1],
        "BAD_INTERVAL",
        "Ray interval must be strictly increasing.",
    )
    require(
        float(np.max(np.abs(interval))) <= POLICY["max_abs_ray_parameter_mm"]
        and float(interval[1] - interval[0]) <= POLICY["max_ray_span_mm"],
        "RAY_LIMIT",
        "Ray interval exceeds the declared resource bounds.",
    )
    require(
        numeric(m["intersection_tolerance_mm"]) and m["intersection_tolerance_mm"] > 0,
        "BAD_TOLERANCE",
        "Intersection tolerance must be positive and finite.",
    )
    require(
        numeric(m["tie_distance_mm"]) and m["tie_distance_mm"] >= 0,
        "BAD_TIE_DISTANCE",
        "Tie distance must be nonnegative and finite.",
    )
    cameras = m["comparison_cameras"]
    require(
        isinstance(cameras, dict) and len(cameras) <= POLICY["max_comparison_cameras"],
        "CAMERA_LIMIT",
        "Comparison camera collection exceeds its limit or is malformed.",
    )
    for label, c in cameras.items():
        require(
            isinstance(label, str) and 0 < len(label) <= 128,
            "BAD_LABEL",
            "Camera label must be a short nonempty string.",
        )
        validate_camera(c)
    qs = m["queries"]
    require(
        isinstance(qs, list) and 1 <= len(qs) <= POLICY["max_queries"],
        "QUERY_LIMIT",
        "Query count is outside the declared bounds.",
    )
    seen = set()
    for q in qs:
        keys(q, ("id", "uv_px"))
        require(
            isinstance(q["id"], str)
            and 0 < len(q["id"]) <= 128
            and q["id"] not in seen,
            "BAD_QUERY_ID",
            "Query IDs must be unique short nonempty strings.",
        )
        seen.add(q["id"])
        uv = vector(q["uv_px"], 2)
        require(
            float(np.max(np.abs(uv))) <= POLICY["max_abs_input_pixel_coordinate"],
            "PIXEL_LIMIT",
            "Input pixel coordinate exceeds the declared resource bound.",
        )
        make_ray(m["camera"], uv, interval)


def project(c, point):
    with np.errstate(over="raise", invalid="raise"):
        p = np.array(c["R_world_to_camera"]) @ point + np.array(
            c["t_world_to_camera_mm"]
        )
        uv = [float(c["fx"] * p[0] + c["cx_px"]), float(c["fy"] * p[1] + c["cy_px"])]
    require(
        np.isfinite(p).all() and all(math.isfinite(x) for x in uv),
        "NONFINITE_REPROJECTION",
        "Reprojection produced nonfinite coordinates.",
    )
    return {
        "uv_px": uv,
        "depth_mm": float(p[2]),
        "frame": "in"
        if 0 <= uv[0] < c["width_px"] and 0 <= uv[1] < c["height_px"]
        else "out",
        "near_plane": "at_or_after" if p[2] >= c["near_mm"] else "before",
    }


def inventory(shape):
    require(
        isinstance(shape, cq.Shape) and not shape.wrapped.IsNull(),
        "INVALID_ARTIFACT",
        "Imported native shape is null or unsupported.",
    )
    faces = shape.Faces()
    require(
        1 <= len(faces) <= POLICY["max_faces"],
        "FACE_LIMIT",
        "Face inventory is empty or exceeds its resource limit.",
    )
    rows = [
        {"index": i, "valid": bool(face.isValid()), "surface_type": face.geomType()}
        for i, face in enumerate(faces)
    ]
    require(
        shape.isValid() and all(row["valid"] for row in rows),
        "INVALID_ARTIFACT",
        "Native shape or a native face is invalid.",
    )
    return faces, rows


def query_shape(shape, manifest):
    """Reusable geometry-only API. Does not mutate shape or establish its file hash.
    Returns every eligible discrete hit, plus excluded kernel observations and
    per-query failures. Native identity association uses IsSame against Faces().
    """
    require(
        DEPENDENCY_ERROR is None,
        "DEPENDENCY_UNAVAILABLE",
        "Required installed CAD/numerical dependencies are unavailable.",
    )
    validate_manifest(manifest)
    faces, rows = inventory(shape)
    require(
        len(faces) * len(manifest["queries"]) <= POLICY["max_query_face_pairs"],
        "WORK_LIMIT",
        "Query-face product exceeds its declared resource bound.",
    )
    out = {
        "status": "diagnostics_completed",
        "face_count": len(faces),
        "face_inventory": rows,
        "provenance": manifest.get("provenance"),
        "queries": [],
        "interpretation": "Nearest eligible discrete native support only; no feature ownership or edit permission.",
    }
    for q in manifest["queries"]:
        row = {
            "id": q["id"],
            "uv_px": q["uv_px"],
            "status": "pending",
            "hits": [],
            "excluded_hits": [],
            "completed_face_indices": [],
        }
        out["queries"].append(row)
        try:
            o, d, norm, near = make_ray(
                manifest["camera"], q["uv_px"], manifest["ray_interval_mm"]
            )
            lo, hi = manifest["ray_interval_mm"]
            unit = d / norm
            line = gp_Lin(gp_Pnt(*map(float, o)), gp_Dir(*map(float, d)))
            row["ray"] = {
                "origin_world_mm": o.tolist(),
                "direction_world": d.tolist(),
                "kernel_unit_direction_world": unit.tolist(),
                "direction_norm": norm,
                "interval_parameter_mm": [lo, hi],
                "mapped_near_parameter_mm": near,
                "parameter_convention": "P(lambda)=origin+lambda*direction; kernel distance=lambda*direction_norm",
            }
            row["source_input_frame"] = (
                "in"
                if 0 <= q["uv_px"][0] < manifest["camera"]["width_px"]
                and 0 <= q["uv_px"][1] < manifest["camera"]["height_px"]
                else "out"
            )
            observed = 0
            for face_index, face in enumerate(faces):
                row["active_face_index"] = face_index
                adaptor = BRepAdaptor_Surface(face.wrapped)
                if adaptor.GetType() == GeomAbs_Plane:
                    plane = adaptor.Plane()
                    n = plane.Axis().Direction()
                    dot = abs(float(np.dot(unit, [n.X(), n.Y(), n.Z()])))
                    if (
                        dot <= POLICY["parallel_plane_dot_bound"]
                        and plane.Distance(line.Location())
                        <= manifest["intersection_tolerance_mm"]
                    ):
                        raise DiagnosticError(
                            "UNSUPPORTED_PLANAR_OVERLAP",
                            "Ray is conservatively classified as parallel and coincident with a face supporting plane; discrete hits are not a complete representation.",
                        )
                intersector = IntCurvesFace_ShapeIntersector()
                intersector.Load(
                    face.wrapped, float(manifest["intersection_tolerance_mm"])
                )
                intersector.Perform(line, float(lo * norm), float(hi * norm))
                require(
                    intersector.IsDone(),
                    "INTERSECTOR_NOT_DONE",
                    "Native intersector IsDone returned false.",
                )
                count = intersector.NbPnt()
                require(
                    0 <= count <= POLICY["max_hits_per_query"] - observed,
                    "HIT_LIMIT",
                    "Native hit count exceeds the per-query resource limit; this query is incomplete.",
                )
                observed += count
                for i in range(1, count + 1):
                    native_face = intersector.Face(i)
                    indices = [
                        j
                        for j, candidate in enumerate(faces)
                        if candidate.wrapped.IsSame(native_face)
                    ]
                    p = intersector.Pnt(i)
                    xyz = np.array([p.X(), p.Y(), p.Z()], dtype=float)
                    distance = float(intersector.WParameter(i))
                    parameter = distance / norm
                    surface_uv = [
                        float(intersector.UParameter(i)),
                        float(intersector.VParameter(i)),
                    ]
                    state = intersector.State(i)
                    require(
                        np.isfinite(xyz).all()
                        and all(
                            math.isfinite(x) for x in [distance, parameter] + surface_uv
                        ),
                        "NONFINITE_NATIVE_HIT",
                        "Native intersector returned a nonfinite point or parameter.",
                    )
                    require(
                        state in (TopAbs_IN, TopAbs_ON),
                        "UNSUPPORTED_HIT_STATE",
                        "Native intersector returned a state other than IN or ON.",
                    )
                    source = project(manifest["camera"], xyz)
                    residual = np.array(source["uv_px"]) - np.array(q["uv_px"])
                    source["input_residual_px"] = residual.tolist()
                    source["input_residual_norm_px"] = float(np.linalg.norm(residual))
                    hit = {
                        "point_world_mm": xyz.tolist(),
                        "ray_parameter_mm": parameter,
                        "ray_distance_mm": distance,
                        "uv_on_surface": surface_uv,
                        "state": "IN" if state == TopAbs_IN else "ON",
                        "source_face_indices": indices,
                        "face_association": "unique"
                        if len(indices) == 1
                        else ("ambiguous" if indices else "unmatched"),
                        "queried_face_index": face_index,
                        "native_hit_index_1based": i,
                        "distance_from_reconstructed_raypoint_mm": float(
                            np.linalg.norm(xyz - (o + parameter * d))
                        ),
                        "source_camera_reprojection": source,
                        "comparison_reprojections": {
                            label: project(c, xyz)
                            for label, c in manifest["comparison_cameras"].items()
                        },
                    }
                    exclusions = []
                    if not lo <= parameter <= hi:
                        exclusions.append("outside_supplied_interval")
                    if parameter < near:
                        exclusions.append("before_mapped_near_plane")
                    if exclusions:
                        hit["exclusion_reasons"] = exclusions
                        row["excluded_hits"].append(hit)
                    else:
                        row["hits"].append(hit)
                    require(
                        indices,
                        "UNMATCHED_NATIVE_FACE",
                        "Returned native face has no IsSame association in the loaded inventory.",
                    )
                row["completed_face_indices"].append(face_index)
            row.pop("active_face_index", None)
            row["hits"].sort(key=lambda h: h["ray_distance_mm"])
            row["excluded_hits"].sort(key=lambda h: h["ray_distance_mm"])
            hits = row["hits"]
            tied = (
                [
                    i
                    for i, h in enumerate(hits)
                    if h["ray_distance_mm"] - hits[0]["ray_distance_mm"]
                    <= manifest["tie_distance_mm"]
                ]
                if hits
                else []
            )
            identities = sorted(
                {j for i in tied for j in hits[i]["source_face_indices"]}
            )
            association_ambiguity = any(
                len(hits[i]["source_face_indices"]) != 1 for i in tied
            )
            status = (
                "no_hits"
                if not tied
                else (
                    "ambiguous_face_identity"
                    if association_ambiguity
                    else ("nearest_tie" if len(tied) > 1 else "unique_nearest_support")
                )
            )
            row["nearest"] = {
                "status": status,
                "hit_indices_0based": tied,
                "source_face_indices": identities,
                "tie_distance_mm": manifest["tie_distance_mm"],
                "minimum_distance_mm": hits[0]["ray_distance_mm"] if hits else None,
            }
            row["status"] = "diagnostics_completed"
        except Exception as exc:
            row["status"] = "diagnostics_failed"
            row["error"] = safe_error(exc, "native_query")
            row["hits"].sort(key=lambda h: h["ray_distance_mm"])
            row["excluded_hits"].sort(key=lambda h: h["ray_distance_mm"])
            out["status"] = "diagnostics_failed"
    return out


def load_guarded(path, expected, audit, tracked):
    audit["cad_import_attempted"] = False
    audit["expected_sha256"] = expected.lower()
    actual = file_hash(path, POLICY["max_artifact_bytes"])
    audit["observed_sha256_before"] = actual
    tracked.append(("artifact", path, actual, POLICY["max_artifact_bytes"]))
    require(
        actual == expected.lower(),
        "SHA256_MISMATCH",
        "Artifact SHA256 mismatch; CAD import was not attempted.",
    )
    audit["sha256_guard_passed"] = True
    audit["cad_import_attempted"] = True
    imported = cq.importers.importStep(str(path))
    roots = imported.vals()
    require(
        roots and all(isinstance(s, cq.Shape) for s in roots),
        "INVALID_ARTIFACT",
        "STEP import did not return native shapes.",
    )
    audit["imported_root_count"] = len(roots)
    require(
        len(roots) <= POLICY["max_faces"],
        "ROOT_LIMIT",
        "Imported root count exceeds the declared resource limit.",
    )
    # A read-only in-memory grouping, not a fuse, heal, sew, or file edit.
    return roots[0] if len(roots) == 1 else cq.Compound.makeCompound(roots)


def duplicate_checked(pairs):
    result = {}
    for key, value in pairs:
        require(
            key not in result,
            "DUPLICATE_JSON_KEY",
            "Duplicate JSON object key is not allowed.",
        )
        result[key] = value
    return result


def reject_constant(_):
    raise DiagnosticError("NONFINITE_JSON", "Nonfinite JSON constants are not allowed.")


def finite_float(text):
    value = float(text)
    require(
        math.isfinite(value),
        "NONFINITE_JSON",
        "Nonfinite JSON numbers are not allowed.",
    )
    return value


def read_manifest(path, report, tracked):
    cap = POLICY["max_manifest_bytes"]
    before = file_hash(path, cap)
    tracked.append(("manifest", path, before, cap))
    with open(path, "rb") as stream:
        data = stream.read(cap + 1)
    require(
        len(data) <= cap and digest_bytes(data) == before,
        "MANIFEST_CHANGED",
        "Manifest changed during bounded reading.",
    )
    report["input_sha256"] = before
    m = json.loads(
        data.decode("utf-8"),
        object_pairs_hook=duplicate_checked,
        parse_constant=reject_constant,
        parse_float=finite_float,
    )
    report["input_canonical_sha256"] = digest_bytes(canonical(m))
    if isinstance(m, dict) and "provenance" in m:
        report["provenance"] = m["provenance"]
    validate_manifest(m)
    report["manifest"] = m
    return m


def runtime_fingerprint():
    result = {
        "python_version": sys.version,
        "implementation": sys.implementation.name,
        "platform": sys.platform,
        "packages": {},
        "files": [],
    }
    for name in ("numpy", "cadquery", "cadquery-ocp"):
        try:
            result["packages"][name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            result["packages"][name] = None
    paths = [("python_executable", Path(sys.executable))]
    for name in ("numpy", "cadquery", "OCP", "OCP.OCP"):
        module = sys.modules.get(name)
        filename = getattr(module, "__file__", None)
        if filename:
            paths.append((name, Path(filename)))
    for label, path in paths:
        result["files"].append(
            {
                "label": label,
                "basename": path.name,
                "sha256": file_hash(path, POLICY["max_runtime_file_bytes"]),
            }
        )
    return {"details": result, "sha256": digest_bytes(canonical(result))}


def self_test(report, tracked, script_path):
    # Artificial fixtures only; these coordinates are not input-artifact dimensions.
    camera = {
        "projection": "orthographic",
        "R_world_to_camera": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        "t_world_to_camera_mm": [0, 0, 0],
        "fx": 10,
        "fy": 10,
        "cx_px": 50,
        "cy_px": 50,
        "width_px": 100,
        "height_px": 100,
        "near_mm": 1,
        "distortion": "none_assumed",
    }
    base = {
        "artifact": {"path": "in_memory_fixture_not_imported", "sha256": "0" * 64},
        "camera": camera,
        "queries": [{"id": "fixture", "uv_px": [50.25, 49.5]}],
        "ray_interval_mm": [0, 12],
        "intersection_tolerance_mm": 1e-7,
        "tie_distance_mm": 1e-7,
        "comparison_cameras": {},
        "provenance": {"kind": "constructed_self_test", "not_vehicle_evidence": True},
    }
    report["self_test_specification"] = base
    report["input_sha256"] = digest_bytes(canonical(base))
    report["input_hash_kind"] = (
        "canonical synthetic self-test specification; fixture definitions also bound by script hash"
    )
    cases = report.setdefault("cases", [])

    def clone(value):
        return json.loads(json.dumps(value))

    def case(name, expected, operation, check):
        row = {"id": name, "expected": expected, "status": "failed"}
        cases.append(row)
        try:
            row["observed"] = operation()
            row["status"] = "passed" if check(row["observed"]) else "failed"
            if row["status"] == "failed":
                row["error"] = {
                    "category": "ControlFailure",
                    "message": "Observation did not satisfy the independent fixture expectation.",
                }
        except Exception as exc:
            row["error"] = safe_error(exc, "self_test_case")

    def rectangle(x0, x1, y0, y1, z, hole=False):
        wire = cq.Wire.makePolygon(
            [
                cq.Vector(x0, y0, z),
                cq.Vector(x1, y0, z),
                cq.Vector(x1, y1, z),
                cq.Vector(x0, y1, z),
            ],
            close=True,
        )
        inner = []
        if hole:
            inner = [
                cq.Wire.makePolygon(
                    [
                        cq.Vector(-0.5, -0.5, z),
                        cq.Vector(-0.5, 0.5, z),
                        cq.Vector(0.5, 0.5, z),
                        cq.Vector(0.5, -0.5, z),
                    ],
                    close=True,
                )
            ]
        return cq.Face.makeFromWires(wire, inner)

    def run_faces(face_list, m=None):
        return query_shape(cq.Compound.makeCompound(face_list), m or base)

    def points_match(observation, expected, nearest=None):
        if observation["status"] != "diagnostics_completed":
            return False
        q = observation["queries"][0]
        if len(q["hits"]) != len(expected):
            return False
        for h, point in zip(q["hits"], expected):
            if not np.allclose(h["point_world_mm"], point, rtol=0, atol=1e-8):
                return False
            if not abs(h["ray_parameter_mm"] - point[2]) <= 1e-8:
                return False
            if h["distance_from_reconstructed_raypoint_mm"] > 1e-8:
                return False
        return nearest is None or q["nearest"]["status"] == nearest

    def parallel(reverse):
        f = [rectangle(-2, 2, -2, 2, 5), rectangle(-2, 2, -2, 2, 9)]
        return run_faces(list(reversed(f)) if reverse else f)

    expected = [[0.025, -0.05, 5], [0.025, -0.05, 9]]
    for reverse in (False, True):
        case(
            "parallel_reversed" if reverse else "parallel_original",
            {"points_mm": expected, "nearest_z_mm": 5, "interval_mm": [0, 12]},
            lambda reverse=reverse: parallel(reverse),
            lambda o: (
                points_match(o, expected, "unique_nearest_support")
                and o["queries"][0]["nearest"]["hit_indices_0based"] == [0]
            ),
        )

    def miss():
        m = clone(base)
        m["queries"][0]["uv_px"] = [80, 50]
        return run_faces([rectangle(-2, 2, -2, 2, 5)], m)

    case(
        "outside_finite_face",
        {"ray_xy_mm": [3, 0], "hits": 0},
        miss,
        lambda o: points_match(o, [], "no_hits"),
    )

    def hole_test(uv):
        m = clone(base)
        m["queries"][0]["uv_px"] = uv
        face = rectangle(-2, 2, -2, 2, 5, True)
        o = run_faces([face], m)
        o["fixture_face_area_mm2"] = face.Area()
        return o

    case(
        "hole_miss",
        {"plane_z_mm": 5, "hole_xy_mm": [-0.5, 0.5], "hits": 0, "face_area_mm2": 15},
        lambda: hole_test([50, 50]),
        lambda o: (
            points_match(o, [], "no_hits")
            and abs(o["fixture_face_area_mm2"] - 15) <= 1e-8
        ),
    )
    case(
        "hole_material_control",
        {"point_mm": [1.5, 0, 5]},
        lambda: hole_test([65, 50]),
        lambda o: points_match(o, [[1.5, 0, 5]], "unique_nearest_support"),
    )

    def shared_edge():
        def edge(a, b):
            return cq.Edge.makeLine(cq.Vector(*a), cq.Vector(*b))

        shared = edge((0, -2, 5), (0, 2, 5))
        left = cq.Face.makeFromWires(
            cq.Wire.assembleEdges(
                [
                    edge((-2, -2, 5), (0, -2, 5)),
                    shared,
                    edge((0, 2, 5), (-2, 2, 5)),
                    edge((-2, 2, 5), (-2, -2, 5)),
                ]
            )
        )
        right = cq.Face.makeFromWires(
            cq.Wire.assembleEdges(
                [
                    cq.Edge(shared.wrapped.Reversed()),
                    edge((0, -2, 5), (2, -2, 5)),
                    edge((2, -2, 5), (2, 2, 5)),
                    edge((2, 2, 5), (0, 2, 5)),
                ]
            )
        )
        # Sewing is confined to this artificial fixture, never an input artifact.
        from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing

        sewing = BRepBuilderAPI_Sewing(1e-7, True, True, True, False)
        sewing.Add(left.wrapped)
        sewing.Add(right.wrapped)
        sewing.Perform()
        native_sewed = sewing.SewedShape()
        require(
            not native_sewed.IsNull(), "SELF_TEST_FIXTURE", "Sewed fixture is null."
        )
        sewed_shape = cq.Shape.cast(native_sewed)
        require(sewed_shape.isValid(), "SELF_TEST_FIXTURE", "Sewed fixture is invalid.")
        sewed_faces = sewed_shape.Faces()
        require(
            len(sewed_faces) == 2 and all(f.isValid() for f in sewed_faces),
            "SELF_TEST_FIXTURE",
            "Sewing must preserve exactly two valid faces.",
        )

        def bounds(face):
            b = face.BoundingBox()
            return [b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax]

        # Sorting is for fixture auditing only; query inventory order is untouched.
        ordered = sorted(sewed_faces, key=lambda f: f.BoundingBox().xmin)
        face_bounds = [bounds(f) for f in ordered]
        face_areas = [f.Area() for f in ordered]
        total_area = sewed_shape.Area()
        face_normals = [list(f.normalAt().toTuple()) for f in ordered]
        original_normals = [list(f.normalAt().toTuple()) for f in (left, right)]
        require(
            np.allclose(
                face_bounds,
                [[-2, 0, -2, 2, 5, 5], [0, 2, -2, 2, 5, 5]],
                rtol=0,
                atol=1e-8,
            ),
            "SELF_TEST_FIXTURE",
            "Sewing changed the original rectangle bounds.",
        )
        require(
            np.allclose(face_areas, [8, 8], rtol=0, atol=1e-8)
            and abs(total_area - 16) <= 1e-8,
            "SELF_TEST_FIXTURE",
            "Sewing changed the rectangle areas or total area of 16.",
        )
        require(
            np.allclose(face_normals, original_normals, rtol=0, atol=1e-8),
            "SELF_TEST_FIXTURE",
            "Sewing changed the original face normals.",
        )
        shared_edge_count = sum(
            a.wrapped.IsSame(b.wrapped)
            for a in sewed_faces[0].Edges()
            for b in sewed_faces[1].Edges()
        )
        require(
            shared_edge_count == 1,
            "SELF_TEST_FIXTURE",
            "Sewed fixture must have exactly one shared native edge by IsSame.",
        )
        m = clone(base)
        m["queries"][0]["uv_px"] = [50, 50]
        o = run_faces(sewed_faces, m)
        o["fixture_has_shared_native_edge"] = shared_edge_count == 1
        o["fixture_sewing_audit"] = {
            "tolerance_mm": 1e-7,
            "nonnull": True,
            "valid": True,
            "face_count": len(sewed_faces),
            "bounds_order": ["xmin", "xmax", "ymin", "ymax", "zmin", "zmax"],
            "face_bounds_mm": face_bounds,
            "face_areas_mm2": face_areas,
            "total_area_mm2": total_area,
            "face_normals": face_normals,
            "original_face_normals": original_normals,
            "shared_native_edge_count": shared_edge_count,
        }
        return o

    case(
        "shared_edge_tie",
        {"points_mm": [[0, 0, 5], [0, 0, 5]], "distinct_faces": 2, "state": "ON"},
        shared_edge,
        lambda o: (
            points_match(o, [[0, 0, 5], [0, 0, 5]], "nearest_tie")
            and o["fixture_has_shared_native_edge"]
            and len(o["queries"][0]["nearest"]["source_face_indices"]) == 2
            and all(h["state"] == "ON" for h in o["queries"][0]["hits"])
            and o["queries"][0]["nearest"]["hit_indices_0based"] == [0, 1]
            and o["queries"][0]["nearest"]["source_face_indices"] == [0, 1]
            and sorted(h["source_face_indices"] for h in o["queries"][0]["hits"])
            == [[0], [1]]
            and abs(o["queries"][0]["nearest"]["minimum_distance_mm"] - 5) <= 1e-8
        ),
    )

    def near_test():
        m = clone(base)
        m["camera"]["near_mm"] = 6
        return run_faces([rectangle(-2, 2, -2, 2, 5), rectangle(-2, 2, -2, 2, 9)], m)

    case(
        "near_plane_reporting",
        {"eligible_z_mm": 9, "excluded_z_mm": 5},
        near_test,
        lambda o: (
            points_match(o, [expected[1]], "unique_nearest_support")
            and len(o["queries"][0]["excluded_hits"]) == 1
            and o["queries"][0]["excluded_hits"][0]["source_camera_reprojection"][
                "near_plane"
            ]
            == "before"
        ),
    )

    def crossview():
        m = clone(base)
        c = clone(camera)
        c.update(t_world_to_camera_mm=[1, -2, -3], fx=20, fy=30, cx_px=10, cy_px=20)
        m["comparison_cameras"] = {"translated": c}
        return run_faces([rectangle(-2, 2, -2, 2, 5)], m)

    def cross_check(o):
        if not points_match(o, [expected[0]], "unique_nearest_support"):
            return False
        p = o["queries"][0]["hits"][0]["comparison_reprojections"]["translated"]
        return (
            np.allclose(p["uv_px"], [30.5, -41.5], rtol=0, atol=1e-8)
            and abs(p["depth_mm"] - 2) <= 1e-8
            and p["frame"] == "out"
        )

    case(
        "comparison_reprojection",
        {"uv_px": [30.5, -41.5], "depth_mm": 2, "frame": "out"},
        crossview,
        cross_check,
    )

    def rejected(m):
        try:
            validate_manifest(m)
            return {"rejected": False}
        except DiagnosticError as exc:
            return {"rejected": True, "error": safe_error(exc, "validation_control")}

    def camera_provenance_control():
        m = clone(base)
        m["comparison_cameras"] = {"same": clone(camera)}
        faces = [rectangle(-2, 2, -2, 2, 5), rectangle(-2, 2, -2, 2, 9)]
        plain = run_faces(faces, m)
        plain_digest = digest_bytes(canonical(m))
        # Assumption: synthetic opaque marker and unknown-key name are test-only choices.
        marker = "synthetic camera provenance"
        m["camera"]["provenance"] = marker
        m["comparison_cameras"]["same"]["provenance"] = marker
        annotated = run_faces(faces, m)
        unknown = clone(m)
        unknown["camera"]["unexpected_camera_key"] = True
        unknown_comparison = clone(m)
        unknown_comparison["comparison_cameras"]["same"]["unexpected_camera_key"] = True
        return {
            "without_provenance": plain,
            "with_provenance": annotated,
            "camera_inputs": {
                "source": m["camera"],
                "comparison": m["comparison_cameras"]["same"],
            },
            "provenance_preserved": m["camera"]["provenance"] == marker
            and m["comparison_cameras"]["same"]["provenance"] == marker,
            "input_digest_changed": digest_bytes(canonical(m)) != plain_digest,
            "unknown_key_rejections": [rejected(unknown), rejected(unknown_comparison)],
        }

    case(
        "camera_provenance_schema",
        {
            "points_mm": expected,
            "geometric_results_unchanged": True,
            "unknown_key_code": "SCHEMA",
        },
        camera_provenance_control,
        lambda o: (
            points_match(o["without_provenance"], expected, "unique_nearest_support")
            and points_match(o["with_provenance"], expected, "unique_nearest_support")
            and canonical(o["without_provenance"]) == canonical(o["with_provenance"])
            and o["provenance_preserved"]
            and o["input_digest_changed"]
            and all(
                r.get("rejected") and r["error"]["code"] == "SCHEMA"
                for r in o["unknown_key_rejections"]
            )
        ),
    )
    bad = []
    m = clone(base)
    m["camera"]["projection"] = "perspective"
    bad.append(("perspective", m, "UNSUPPORTED_PROJECTION"))
    m = clone(base)
    m["camera"]["distortion"] = "radial"
    bad.append(("distortion", m, "UNSUPPORTED_DISTORTION"))
    m = clone(base)
    m["camera"]["R_world_to_camera"] = [[1, 0], [0, 1]]
    bad.append(("malformed_rotation", m, "BAD_ROTATION"))
    m = clone(base)
    m["camera"]["fx"] = float("nan")
    bad.append(("nonfinite_camera", m, "BAD_CAMERA"))
    m = clone(base)
    m["camera"]["R_world_to_camera"][0][0] = -1
    bad.append(("improper_rotation", m, "BAD_ROTATION"))
    m = clone(base)
    m["ray_interval_mm"] = [0, float("inf")]
    bad.append(("nonfinite_interval", m, "BAD_VECTOR"))
    m = clone(base)
    m["ray_interval_mm"] = [12, 0]
    bad.append(("reversed_interval", m, "BAD_INTERVAL"))
    m = clone(base)
    m["queries"][0]["uv_px"] = [50]
    bad.append(("malformed_query_ray", m, "BAD_VECTOR"))
    m = clone(base)
    m["queries"][0]["uv_px"] = [float("nan"), 50]
    bad.append(("nonfinite_query_ray", m, "BAD_VECTOR"))
    for name, m, code in bad:
        case(
            name,
            {"rejection_code": code},
            lambda m=m: rejected(m),
            lambda o, code=code: o.get("rejected") and o["error"]["code"] == code,
        )

    def mismatch():
        # The script is a known non-STEP regular file; no extra fixture file is written.
        actual = file_hash(script_path, POLICY["max_manifest_bytes"])
        wrong = ("0" if actual[0] != "0" else "1") + actual[1:]
        audit = {}
        try:
            load_guarded(script_path, wrong, audit, tracked)
            return {"audit": audit, "rejected": False}
        except DiagnosticError as exc:
            return {
                "audit": audit,
                "rejected": True,
                "error": safe_error(exc, "sha_control"),
            }

    case(
        "sha_mismatch_before_cad_import",
        {"rejection_code": "SHA256_MISMATCH", "cad_import_attempted": False},
        mismatch,
        lambda o: (
            o.get("rejected")
            and o["error"]["code"] == "SHA256_MISMATCH"
            and o["audit"]["cad_import_attempted"] is False
        ),
    )
    report["status"] = (
        "self_tests_passed"
        if all(c["status"] == "passed" for c in cases)
        else "self_tests_failed"
    )


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise DiagnosticError(
            "CLI_INVALID",
            "Invalid command-line options; use --input or --self-test, and --output NEWdirectory.",
        )


def main(argv=None):
    output = None
    report = {
        "status": "diagnostics_failed",
        "policy": POLICY,
        "limits": LIMITS,
        "authority": "read-only diagnostics; no physical acceptance or native-edit authorization",
        "integrity_after": [],
    }
    tracked = []
    stage = "arguments"
    try:
        parser = Parser(description=__doc__)
        mode = parser.add_mutually_exclusive_group(required=True)
        mode.add_argument("--input")
        mode.add_argument("--self-test", action="store_true")
        parser.add_argument("--output", required=True)
        args = parser.parse_args(argv)
        stage = "create_output_directory"
        candidate = Path(args.output)
        require(
            not candidate.exists() and not candidate.is_symlink(),
            "OUTPUT_EXISTS",
            "Output path already exists; refusing any write there.",
        )
        candidate.mkdir(parents=False, exist_ok=False)
        output = candidate
        stage = "script_provenance"
        script_path = Path(__file__).resolve(strict=True)
        script_sha = file_hash(script_path, POLICY["max_manifest_bytes"])
        report["script_sha256"] = script_sha
        tracked.append(
            ("script", script_path, script_sha, POLICY["max_manifest_bytes"])
        )
        stage = "runtime_provenance"
        report["runtime"] = runtime_fingerprint()
        require(
            DEPENDENCY_ERROR is None,
            "DEPENDENCY_UNAVAILABLE",
            "Required installed numpy/CadQuery/OCP dependencies could not be imported.",
        )
        if args.self_test:
            stage = "self_tests"
            self_test(report, tracked, script_path)
        else:
            stage = "manifest"
            manifest_path = Path(args.input).resolve(strict=True)
            m = read_manifest(manifest_path, report, tracked)
            path = Path(m["artifact"]["path"])
            if not path.is_absolute():
                path = manifest_path.parent / path
            path = path.resolve(strict=True)
            stage = "guarded_native_import"
            report["source"] = {}
            shape = load_guarded(
                path, m["artifact"]["sha256"], report["source"], tracked
            )
            stage = "native_queries"
            report["diagnostics"] = query_shape(shape, m)
            report["status"] = report["diagnostics"]["status"]
    except Exception as exc:
        report["status"] = "diagnostics_failed"
        report.setdefault("errors", []).append(safe_error(exc, stage))
    finally:
        for label, path, before, cap in tracked:
            row = {"source": label, "sha256_before": before}
            report["integrity_after"].append(row)
            try:
                after = file_hash(path, cap)
                row.update(sha256_after=after, unchanged=(after == before))
                if after != before:
                    report["status"] = "diagnostics_failed"
                    row["error"] = {
                        "category": "IntegrityFailure",
                        "message": "Source content differs after processing; results must not be accepted.",
                    }
            except Exception as exc:
                row["unchanged"] = False
                row["error"] = safe_error(exc, "integrity_recheck")
                report["status"] = "diagnostics_failed"
    success = report["status"] in ("diagnostics_completed", "self_tests_passed")
    if output is None:
        # No report can be written without violating the new-directory rule.
        sys.stderr.write(
            json.dumps(
                {"status": "diagnostics_failed", "errors": report.get("errors", [])},
                allow_nan=False,
            )
            + "\n"
        )
        return 2
    try:
        # Exclusive creation; on failure leave any partial report in place. No retry.
        payload = (
            json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
        )
        with open(output / "report.json", "x", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception as exc:
        sys.stderr.write(
            json.dumps(
                {
                    "status": "diagnostics_failed",
                    "error": safe_error(exc, "write_report"),
                }
            )
            + "\n"
        )
        return 2
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
