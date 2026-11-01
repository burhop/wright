#!/usr/bin/env python3
"""Create an auditable visualization-only mesh derivative.

This is NOT CAD repair, a physical tolerance, STEP validity inspection,
manufacturing validation, or authorization to render without inspection.
The original mesh, STEP, renderer, and prior failed projection evidence are
not edited. Requires Python 3 and NumPy.
"""

import argparse
import copy
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

import numpy as np


MAX_TRIANGLES = 100_000
MAX_VERTICES = 1_000_000
LIMITATIONS = [
    "Visualization-only derivative; not CAD repair or manufacturing validation.",
    "No tolerance, welding, remeshing, hole filling, or near-zero filtering.",
    "STEP validity is supplied separately by an independent inspector; SHA-256 checks bytes only.",
    "Independent inspection of the derivative and audit remains required.",
    "JSON coordinate numbers are interpreted as IEEE-754 binary64 coordinates.",
    "A zero NumPy cross magnitude is only a candidate; exact rational confirmation is mandatory.",
    "Nonfinite floating detector arithmetic or an exact-nonzero candidate causes failure.",
    "Connectivity, watertightness, orientation, and manufacturing fitness are not certified.",
    "Integrity checks are before/after snapshots, not protection against concurrent modification.",
    "No network APIs are used; operators must provide local filesystem paths, not network mounts.",
    "Input count limits apply after JSON parsing; this is not a bounded-memory streaming parser.",
    "Failure evidence is retained when writable; abrupt termination can leave incomplete output.",
]
METHOD = {
    "detector": "numpy.linalg.norm(numpy.cross(b-a, c-a), axis=1) == 0.0, float64",
    "confirmation": "Fraction.from_float on each stored float64 coordinate, then exact subtraction and cross product",
    "removal_rule": "Remove only detector candidates whose three rational cross components are exactly zero.",
    "tolerance": None,
    "vertex_policy": "Preserve every input vertex in its original order, including unused vertices.",
    "metadata_policy": "Preserve every JSON field except the filtered triangles array; formatting is not preserved.",
    "triangle_policy": "Preserve retained triangle order and index values; no reindexing.",
    "audit_index_base": 0,
}


class MeshError(Exception):
    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = {} if details is None else details


def local_path(value, label):
    if not isinstance(value, str) or not value:
        raise MeshError(label + " must be a nonempty local path.")
    if "://" in value or value.startswith("//") or value.startswith(chr(92) * 2):
        raise MeshError(label + " must not be a URL or network-share path.")
    return Path(value)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def hash_file(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def reject_constant(value):
    raise MeshError("Nonfinite JSON number is forbidden.")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise MeshError("Duplicate JSON object keys are forbidden.")
        result[key] = value
    return result


def encode_json(value):
    return (
        json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + chr(10)
    ).encode("utf-8")


def write_exclusive(path, data):
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()


def validate_mesh(mesh):
    if not isinstance(mesh, dict):
        raise MeshError("Mesh must be a JSON object.")
    if mesh.get("units") != "mm":
        raise MeshError("Mesh units must be mm.")
    if not isinstance(mesh.get("tessellation"), dict):
        raise MeshError("Tessellation metadata must be an object.")
    points = mesh.get("points")
    triangles = mesh.get("triangles")
    if not isinstance(points, list) or not points:
        raise MeshError("Points must be a nonempty array.")
    if not isinstance(triangles, list) or not triangles:
        raise MeshError("Triangles must be a nonempty array.")
    if len(points) > MAX_VERTICES or len(triangles) > MAX_TRIANGLES:
        raise MeshError("Input exceeds the vertex or triangle count limit.")
    for index, point in enumerate(points):
        if not isinstance(point, list) or len(point) != 3:
            raise MeshError(
                "Each point must have three coordinates.", {"vertex_index": index}
            )
        if any(type(value) not in (int, float) for value in point):
            raise MeshError(
                "Coordinates must be numbers, not booleans or strings.",
                {"vertex_index": index},
            )
    try:
        coordinates = np.asarray(points, dtype=np.float64)
    except (ValueError, TypeError, OverflowError):
        raise MeshError("Coordinates cannot be represented as float64.") from None
    invalid = np.flatnonzero(~np.isfinite(coordinates).all(axis=1)).tolist()
    if invalid:
        raise MeshError(
            "Coordinates must be finite float64 values.", {"vertex_indices": invalid}
        )
    for index, triangle in enumerate(triangles):
        if not isinstance(triangle, list) or len(triangle) != 3:
            raise MeshError(
                "Each triangle must have three indices.", {"triangle_index": index}
            )
        if any(type(value) is not int for value in triangle):
            raise MeshError(
                "Triangle indices must be integers, not floats or booleans.",
                {"triangle_index": index},
            )
        if any(value < 0 or value >= len(points) for value in triangle):
            raise MeshError(
                "Triangle index is out of bounds.",
                {"triangle_index": index, "vertex_indices": triangle},
            )
    source = mesh.get("source_artifact")
    if not isinstance(source, dict):
        raise MeshError("source_artifact must be an object.")
    source_path = local_path(source.get("path"), "Source STEP")
    if not source_path.is_absolute():
        raise MeshError("Source STEP path must be absolute.")
    expected = source.get("sha256")
    if (
        not isinstance(expected, str)
        or re.fullmatch("[0-9a-fA-F]{64}", expected) is None
    ):
        raise MeshError(
            "Source SHA-256 must contain exactly 64 hexadecimal characters."
        )
    if not source_path.is_file():
        raise MeshError("Source STEP is missing or is not a regular file.")
    return (
        coordinates,
        np.asarray(triangles, dtype=np.int64),
        source_path,
        expected.lower(),
    )


def float_cross_magnitudes(points, triangles):
    a = points[triangles[:, 0]]
    b = points[triangles[:, 1]]
    c = points[triangles[:, 2]]
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        cross = np.cross(b - a, c - a)
        magnitudes = np.linalg.norm(cross, axis=1)
    invalid = np.flatnonzero(
        ~np.isfinite(cross).all(axis=1) | ~np.isfinite(magnitudes)
    ).tolist()
    if invalid:
        raise MeshError(
            "Floating detector arithmetic is nonfinite; no derivative accepted.",
            {"triangle_indices": invalid},
        )
    return magnitudes


def rational_cross(coordinates):
    a, b, c = [
        [Fraction.from_float(float(value)) for value in row] for row in coordinates
    ]
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    return [
        u[1] * v[2] - u[2] * v[1],
        u[2] * v[0] - u[0] * v[2],
        u[0] * v[1] - u[1] * v[0],
    ]


def candidate_audit(mesh, points, index):
    vertex_indices = mesh["triangles"][index]
    coordinates = points[vertex_indices]
    cross = rational_cross(coordinates)
    entry = {
        "triangle_index": index,
        "vertex_indices": copy.deepcopy(vertex_indices),
        "coordinates": copy.deepcopy([mesh["points"][i] for i in vertex_indices]),
        "float64_coordinate_hex": [
            [float(value).hex() for value in row] for row in coordinates
        ],
        "detector_cross_magnitude": 0.0,
        "exact_zero_proof": {
            "method": "Fraction.from_float coordinates; exact (b-a) cross (c-a)",
            "cross_components": [
                {
                    "numerator": str(value.numerator),
                    "denominator": str(value.denominator),
                }
                for value in cross
            ],
            "all_components_exactly_zero": all(value == 0 for value in cross),
        },
    }
    return entry, all(value == 0 for value in cross)


def public_error(exc):
    if isinstance(exc, MeshError):
        return str(exc), exc.details
    return "Local processing failed (" + type(
        exc
    ).__name__ + "); paths are omitted.", {}


def prepare(mesh_path, output_dir):
    start = time.perf_counter()
    mesh_path = local_path(str(mesh_path), "Input mesh")
    output_dir = local_path(str(output_dir), "Output directory")
    try:
        output_dir.mkdir(exist_ok=False)
    except FileExistsError:
        raise MeshError("Output already exists; nothing there was modified.") from None
    audit = {
        "schema": "visualization-mesh-preparation/1",
        "purpose": "Rendering preparation only; not physical tolerance, CAD repair, or manufacturing validation.",
        "inspection": "Not performed by this program; independent review remains required.",
        "method": METHOD,
        "limitations": LIMITATIONS,
        "runtime": {"python": sys.version.split()[0], "numpy": np.__version__},
        "removed_triangles": [],
    }
    try:
        if not mesh_path.is_file():
            raise MeshError("Input mesh is missing or is not a regular file.")
        original_bytes = mesh_path.read_bytes()
        input_hash = sha256_bytes(original_bytes)
        audit["input_mesh_sha256"] = input_hash
        mesh = json.loads(
            original_bytes,
            parse_constant=reject_constant,
            object_pairs_hook=unique_object,
        )
        points, triangles, source_path, expected_hash = validate_mesh(mesh)
        audit["source_artifact"] = copy.deepcopy(mesh["source_artifact"])
        source_before = hash_file(source_path)
        audit["source_sha256_before"] = source_before
        if source_before != expected_hash:
            raise MeshError("Source SHA-256 does not match source_artifact.sha256.")
        magnitudes = float_cross_magnitudes(points, triangles)
        candidates = np.flatnonzero(magnitudes == 0.0).tolist()
        audit["float_zero_candidate_count"] = len(candidates)
        offending = []
        removed_indices = []
        for index in candidates:
            entry, exact_zero = candidate_audit(mesh, points, index)
            if exact_zero:
                audit["removed_triangles"].append(entry)
                removed_indices.append(index)
            else:
                offending.append(entry)
        if offending:
            raise MeshError(
                "Floating zero disagrees with exact arithmetic; no derivative accepted. Offending original triangle indices: "
                + ", ".join(str(entry["triangle_index"]) for entry in offending),
                {"offending_triangles": offending},
            )
        if len(removed_indices) == len(triangles):
            raise MeshError("All triangles would be removed; empty derivative refused.")
        removed_set = set(removed_indices)
        prepared = copy.deepcopy(mesh)
        prepared["triangles"] = [
            triangle
            for index, triangle in enumerate(mesh["triangles"])
            if index not in removed_set
        ]
        audit["counts"] = {
            "input_vertices": len(points),
            "output_vertices": len(points),
            "preserved_vertices": len(points),
            "removed_vertices": 0,
            "input_triangles": len(triangles),
            "output_triangles": len(prepared["triangles"]),
            "preserved_triangles": len(prepared["triangles"]),
            "removed_triangles": len(removed_indices),
        }
        prepared_bytes = encode_json(prepared)
        prepared_path = output_dir / "prepared-mesh.json"
        write_exclusive(prepared_path, prepared_bytes)
        output_hash = hash_file(prepared_path)
        if output_hash != sha256_bytes(prepared_bytes):
            raise MeshError(
                "Written derivative bytes do not match the serialized derivative."
            )
        audit["output_mesh_sha256"] = output_hash
        audit["output_mesh_filename"] = "prepared-mesh.json"
        source_after = hash_file(source_path)
        input_after = hash_file(mesh_path)
        audit["source_sha256_after"] = source_after
        audit["input_mesh_sha256_after"] = input_after
        if source_after != source_before or input_after != input_hash:
            raise MeshError(
                "Input STEP or input mesh changed during processing; derivative is not accepted."
            )
        audit["integrity_checks"] = {
            "input_step_unchanged": True,
            "input_mesh_unchanged": True,
            "output_bytes_verified": True,
            "scope": "SHA-256 snapshots after derivative write and before final report write; not STEP validity.",
        }
        audit["runtime"]["elapsed_seconds_before_report_write"] = (
            time.perf_counter() - start
        )
        audit["recorded_at_utc"] = datetime.now(timezone.utc).isoformat()
        audit["status"] = (
            "visualization_derivative_created_pending_independent_inspection"
        )
        write_exclusive(output_dir / "report.json", encode_json(audit))
        return audit
    except Exception as exc:
        message, details = public_error(exc)
        audit["status"] = "failed_do_not_use_derivative"
        audit["error"] = {"message": message, "details": details}
        audit["removed_triangles_scope"] = (
            "Confirmed removal candidates only; this failed run authorizes no derivative."
        )
        audit["runtime"]["elapsed_seconds_to_failure"] = time.perf_counter() - start
        try:
            failure_path = output_dir / "report.json"
            if failure_path.exists():
                failure_path = output_dir / "failure.json"
            write_exclusive(failure_path, encode_json(audit))
        except Exception:
            # Never delete or overwrite partial evidence to manufacture success.
            pass
        raise MeshError(message, details) from None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mesh", required=True, help="Local input tessellation JSON")
    parser.add_argument(
        "--output",
        required=True,
        help="New local output directory; existing paths are refused",
    )
    args = parser.parse_args(argv)
    try:
        prepare(args.mesh, args.output)
    except Exception as exc:
        message, _ = public_error(exc)
        print("ERROR: " + message, file=sys.stderr)
        print(
            "No usable derivative verdict. Preserve any partial output; do not retry into it.",
            file=sys.stderr,
        )
        return 1
    print("Visualization derivative created; independent inspection is still required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
