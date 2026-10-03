"""Passive measurements of actual STL bytes; no native application implementation."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import struct


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def _clip_x(points, boundary, keep_above):
    """Clip a triangle polygon; extrema include edge/plane intersections."""
    result = []
    for a, b in zip(points, points[1:] + points[:1]):
        inside_a = a[0] >= boundary if keep_above else a[0] <= boundary
        inside_b = b[0] >= boundary if keep_above else b[0] <= boundary
        if inside_a:
            result.append(a)
        if inside_a != inside_b:
            fraction = (boundary - a[0]) / (b[0] - a[0])
            result.append(tuple(a[i] + fraction * (b[i] - a[i]) for i in range(3)))
    return result

def measure_handle_features(path: Path) -> dict:
    """Read actual STL bytes in the supplied mounting frame, independently of CAD claims.

    Circle sections are measurements for human review, not new acceptance
    tolerances. The clearance minimum is exact for the linear triangle surface.
    """
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError("Handle measurement needs a binary STL")
    count = struct.unpack_from("<I", data, 80)[0]
    if not 0 < count <= 80000 or len(data) != 84 + 50 * count:
        raise ValueError("Handle measurement requires a bounded binary STL")
    triangles = []
    for offset in range(84, len(data), 50):
        values = struct.unpack_from("<12fH", data, offset)
        points = [tuple(values[i:i + 3]) for i in (3, 6, 9)]
        if not all(math.isfinite(v) for p in points for v in p):
            raise ValueError("Handle mesh contains nonfinite coordinates")
        a, b, c = points
        u = [b[i] - a[i] for i in range(3)]
        v = [c[i] - a[i] for i in range(3)]
        cross = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
        if all(value == 0 for value in cross):
            raise ValueError("Final handle STL contains a zero-area triangle")
        triangles.append(points)
    bounds = [[min(p[i] for t in triangles for p in t) for i in range(3)],
              [max(p[i] for t in triangles for p in t) for i in range(3)]]
    minimum = None
    for triangle in triangles:
        polygon = _clip_x(_clip_x(triangle, 15.5, True), 80.5, False)
        for point in polygon:
            if minimum is None or point[2] < minimum[2]:
                minimum = point
    if minimum is None:
        raise ValueError("Handle has no surface in the required central span")

    sections = []
    # Three planes through the straight part of each 5 mm mounting pad.
    # Segment distances also expose the inscribed (faceted) bore clearance.
    for z in (1.5, 2.5, 3.5):
        holes = []
        for nominal_x in (0.0, 96.0):
            segments = []
            for triangle in triangles:
                hits = []
                for a, b in zip(triangle, triangle[1:] + triangle[:1]):
                    if (a[2] <= z < b[2]) or (b[2] <= z < a[2]):
                        fraction = (z - a[2]) / (b[2] - a[2])
                        hits.append(tuple(a[i] + fraction * (b[i] - a[i]) for i in (0, 1)))
                if len(hits) == 2 and all(math.hypot(p[0] - nominal_x, p[1]) < 4.0 for p in hits):
                    segments.append(hits)
            if not segments:
                raise ValueError(f"No bore section found at X={nominal_x}, Z={z}")
            points = [p for segment in segments for p in segment]
            # The midpoint of opposite extrema does not assume that voxelized
            # holes remain circular. Report anisotropy and radius range explicitly.
            low = [min(p[i] for p in points) for i in (0, 1)]
            high = [max(p[i] for p in points) for i in (0, 1)]
            center = [(a + b) / 2 for a, b in zip(low, high)]
            distances = []
            for a, b in segments:
                dx, dy = b[0] - a[0], b[1] - a[1]
                length2 = dx * dx + dy * dy
                fraction = 0 if length2 == 0 else max(0, min(1, ((center[0] - a[0]) * dx + (center[1] - a[1]) * dy) / length2))
                distances.append(math.hypot(a[0] + fraction * dx - center[0], a[1] + fraction * dy - center[1]))
            holes.append({'center_xy_mm': center, 'diameter_xy_mm': [high[i] - low[i] for i in (0, 1)],
                          'minimum_centered_clearance_diameter_mm': 2 * min(distances),
                          'maximum_centered_diameter_mm': 2 * max(math.dist(p, center) for p in points),
                          'section_segments': len(segments)})
        sections.append({'z_mm': z, 'holes': holes,
                         'center_spacing_mm': math.dist(holes[0]['center_xy_mm'], holes[1]['center_xy_mm'])})

    orientations = []
    for name, axis, sign in (('pads_down', 2, 1), ('side', 1, -1)):
        bed = min(sign * p[axis] for t in triangles for p in t)
        contact_area = overhang_area = 0.0
        for triangle in triangles:
            a, b, c = triangle
            u = [b[i] - a[i] for i in range(3)]
            v = [c[i] - a[i] for i in range(3)]
            cross = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
            length = math.sqrt(sum(value * value for value in cross))
            if length == 0:
                continue
            at_bed = all(abs(sign * p[axis] - bed) <= 1e-6 for p in triangle)
            if at_bed:
                contact_area += length / 2
            elif sign * cross[axis] / length < -math.sqrt(0.5):
                overhang_area += length / 2
        orientations.append({'orientation': name, 'build_height_mm': bounds[1][axis] - bounds[0][axis],
                             'flat_bed_contact_area_mm2': contact_area,
                             'downward_surface_area_beyond_45_degrees_mm2': overhang_area})
    return {'source_sha256': hashlib.sha256(data).hexdigest(), 'triangles': count,
            'method': 'Actual binary-STL triangles: exact X-slab clipping, bore plane sections, and oriented surface areas.',
            'bounds_mm': bounds, 'central_span_x_mm': [15.5, 80.5],
            'minimum_clearance_mm': minimum[2], 'minimum_at_mm': minimum,
            'required_clearance_mm': 25.0, 'clearance_pass': minimum[2] >= 25.0,
            'bore_sections': sections, 'orientation_comparison': orientations,
            'orientation_selection': 'pads_down',
            'orientation_reason': 'Pads-down keeps both mounting faces on the bed and bolt bores vertical; supports may contact the rear/underside of the raised bow. Side orientation makes the bores horizontal and places the grip flank/edges at support or bed contact. Inspect the actual selected slice support preview before acceptance.',
            'limitations': 'The 45-degree surface-area measure is a geometric comparison indicator, not a slicer support prediction or acceptance threshold. Bore sections do not replace full engineering review. No physical fit, strength or printing claim.'}


def mesh_metrics(path: Path, *, maximum_triangles: int) -> dict:
    """Inspect bounded final bytes without native application reports or repairs."""
    if type(maximum_triangles) is not int or not 4 <= maximum_triangles <= 1_000_000:
        raise ValueError("Declare a bounded triangle inspection limit")
    if path.stat().st_size > 84 + 50 * maximum_triangles:
        raise ValueError("Mesh exceeds the declared triangle inspection limit")
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError("Mesh inspection needs a binary STL")
    count = struct.unpack_from("<I", data, 80)[0]
    if not 4 <= count <= maximum_triangles or len(data) != 84 + 50 * count:
        raise ValueError("Mesh inspection requires a bounded binary STL")
    minimum = [math.inf] * 3
    maximum = [-math.inf] * 3
    edges = {}
    neighbors = {}
    volumes = []
    degenerate = 0
    for offset in range(84, len(data), 50):
        values = struct.unpack_from("<12fH", data, offset)
        if not all(math.isfinite(value) for value in values[:12]):
            raise ValueError("Mesh contains nonfinite coordinates")
        a, b, c = [tuple(values[index:index + 3]) for index in (3, 6, 9)]
        for point in (a, b, c):
            for axis in range(3):
                minimum[axis] = min(minimum[axis], point[axis])
                maximum[axis] = max(maximum[axis], point[axis])
        u = [b[index] - a[index] for index in range(3)]
        v = [c[index] - a[index] for index in range(3)]
        cross = [u[1]*v[2] - u[2]*v[1], u[2]*v[0] - u[0]*v[2], u[0]*v[1] - u[1]*v[0]]
        degenerate += sum(value * value for value in cross) <= 4e-20
        volumes.append((a[0]*(b[1]*c[2] - b[2]*c[1]) + a[1]*(b[2]*c[0] - b[0]*c[2]) + a[2]*(b[0]*c[1] - b[1]*c[0])) / 6)
        for left, right in ((a,b), (b,c), (c,a)):
            edge = tuple(sorted((left, right)))
            edges[edge] = edges.get(edge, 0) + 1
            neighbors.setdefault(left, set()).add(right)
            neighbors.setdefault(right, set()).add(left)
    remaining = set(neighbors)
    components = 0
    while remaining:
        components += 1
        stack = [remaining.pop()]
        while stack:
            current = stack.pop()
            for neighbor in neighbors[current]:
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return {
        "source_sha256": hashlib.sha256(data).hexdigest(), "triangles": count,
        "minimum_mm": minimum, "maximum_mm": maximum,
        "dimensions_mm": [maximum[index] - minimum[index] for index in range(3)],
        "boundary_edges": sum(value == 1 for value in edges.values()),
        "nonmanifold_edges": sum(value > 2 for value in edges.values()),
        "degenerate_faces": degenerate, "connected_components": components,
        "signed_volume_mm3": math.fsum(volumes),
        "method": "Actual binary-STL triangle coordinates, exact shared edges, components and signed volume",
    }


def run(configuration: dict) -> dict:
    """Emit passive evidence; mandatory measurement failures stop the declared step."""
    root = Path(configuration["workspace_root"]).resolve(strict=True)

    def path(key):
        relative = Path(configuration[key])
        value = (root / relative).resolve()
        if relative.is_absolute() or value == root or not value.is_relative_to(root):
            raise ValueError("Mesh-inspection path escapes its declared workspace")
        return value

    source, repaired, preview, output = [path(key) for key in ("source", "repaired", "preview", "output")]
    if len({source, repaired, preview, output}) != 4 or output.exists():
        raise ValueError("Mesh inspection requires distinct files and a new evidence output")
    if not all(item.is_file() for item in (source, repaired, preview)):
        raise ValueError("Actual source, repaired STL and preview are required")
    if not 24 <= preview.stat().st_size <= 16 * 1024 * 1024:
        raise ValueError("Native geometry preview exceeds the bounded 16 MiB inspection size")
    with preview.open("rb") as stream:
        header = stream.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError("The native geometry preview must have a PNG header")
    if not all(0 < value <= 16384 for value in struct.unpack(">II", header[16:24])):
        raise ValueError("Native geometry preview dimensions exceed the inspection bounds")
    policy = configuration["policy"]
    volume = policy["build_volume_mm"]
    if (not isinstance(volume, list) or len(volume) != 3
            or any(isinstance(value, bool) or not isinstance(value, (int, float))
                   or not math.isfinite(value) or value <= 0 for value in volume)):
        raise ValueError("Declare the selected build envelope explicitly")
    tolerance = policy["build_volume_tolerance_mm"]
    if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance) or not 0 <= tolerance <= 0.01:
        raise ValueError("Declare the original bounded envelope tolerance")
    before = mesh_metrics(source, maximum_triangles=1_000_000)
    after = mesh_metrics(repaired, maximum_triangles=policy["triangle_limit"])
    checks = {
        "closed_manifold": after["boundary_edges"] == after["nonmanifold_edges"] == 0,
        "outward_normals": after["signed_volume_mm3"] > 0,
        "single_component": after["connected_components"] == 1,
        "no_degenerate_faces": after["degenerate_faces"] == 0,
        "within_triangle_limit": after["triangles"] <= policy["triangle_limit"],
        "fits_declared_build_volume": all(value <= limit + tolerance for value, limit in zip(after["dimensions_mm"], volume)),
    }
    report = {"operation": "passive_exact_repaired_mesh_inspection", "before": before,
              "after": after, "checks": checks, "policy": policy,
              "artifacts": [{"path": str(item.relative_to(root)), "sha256": _sha256(item), "size_bytes": item.stat().st_size} for item in (source, repaired, preview)],
              "preview_scope": "Header and bytes verified; geometry-only native preview, not support prediction or image-content acceptance",
              "engineering_acceptance": False, "physical_verification": False}
    if configuration["measure_handle_features"]:
        report["final_feature_measurements"] = measure_handle_features(repaired)
        checks["original_25mm_clearance"] = report["final_feature_measurements"]["clearance_pass"]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
    if not all(checks.values()):
        raise ValueError("Actual repaired mesh fails retained mandatory checks: " + json.dumps(checks))
    return report
