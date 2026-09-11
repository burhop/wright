"""Bounded, dependency-free inspection of the actual exported flat DXF.

This verifies file/contour integrity, not conformity to a particular design.
Unsupported DXF constructs are reported instead of silently dropping geometry.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path


MAX_BYTES = 20 * 1024 * 1024
MAX_ENTITIES = 20_000
MAX_SEGMENTS = 10_000
TAU = 2 * math.pi
UNITS = {1: ("in", 25.4), 2: ("ft", 304.8), 4: ("mm", 1.0),
         5: ("cm", 10.0), 6: ("m", 1000.0)}
BEND_LAYERS = {"UP_CENTERLINES", "DOWN_CENTERLINES"}


@dataclass(frozen=True)
class Segment:
    layer: str
    start: tuple[float, float]
    end: tuple[float, float]
    center: tuple[float, float] | None = None
    radius: float = 0.0
    angle: float = 0.0
    sweep: float = 0.0

    def bounds_points(self):
        points = [self.start, self.end]
        if self.center:
            for angle in (0.0, math.pi / 2, math.pi, 3 * math.pi / 2):
                distance = ((angle - self.angle) if self.sweep > 0 else (self.angle - angle)) % TAU
                if distance <= abs(self.sweep) + 1e-12:
                    points.append((self.center[0] + self.radius * math.cos(angle),
                                   self.center[1] + self.radius * math.sin(angle)))
        return points

    @property
    def length(self):
        return self.radius * abs(self.sweep) if self.center else math.dist(self.start, self.end)


def _first(fields, code, default=None):
    values = [value for key, value in fields if key == code]
    if not values:
        if default is None:
            raise ValueError(f"Missing required DXF group code {code}.")
        return default
    if len(values) != 1:
        raise ValueError(f"Repeated singleton DXF group code {code}.")
    return values[0]


def _number(fields, code, default=None):
    number = float(_first(fields, code, default))
    if not math.isfinite(number):
        raise ValueError(f"Non-finite geometry at DXF group code {code}.")
    return number


def _pairs(data):
    if data.startswith(b"AutoCAD Binary DXF"):
        raise NotImplementedError("Binary DXF is not supported by this verifier.")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("cp1252")
    lines = text.splitlines()
    if len(lines) % 2:
        raise ValueError("DXF has an unmatched group-code/value line.")
    pairs = []
    for index in range(0, len(lines), 2):
        code = int(lines[index].strip())
        if not 0 <= code <= 1071:
            raise ValueError("DXF has an out-of-range group code.")
        pairs.append((code, lines[index + 1].strip()))
    return pairs


def _sections(pairs):
    sections, current, buffer, ended = {}, None, [], False
    index = 0
    while index < len(pairs):
        code, value = pairs[index]
        if ended:
            raise ValueError("DXF contains data after EOF.")
        if (code, value) == (0, "SECTION"):
            if current is not None or index + 1 >= len(pairs) or pairs[index + 1][0] != 2:
                raise ValueError("Malformed DXF section declaration.")
            current = pairs[index + 1][1]
            if current in sections:
                raise ValueError("Duplicate DXF section.")
            buffer = []
            index += 2
            continue
        if (code, value) == (0, "ENDSEC"):
            if current is None:
                raise ValueError("DXF ENDSEC has no matching section.")
            sections[current] = buffer
            current, buffer = None, []
        elif (code, value) == (0, "EOF"):
            if current is not None:
                raise ValueError("DXF ended inside a section.")
            ended = True
        elif current is not None:
            buffer.append((code, value))
        elif code != 999:
            raise ValueError("Unexpected DXF data outside a section.")
        index += 1
    if not ended or current is not None or "ENTITIES" not in sections:
        raise ValueError("DXF needs a complete ENTITIES section and EOF.")
    return sections


def _header_value(header, name):
    matches = []
    for index, pair in enumerate(header):
        if pair == (9, name):
            if index + 1 >= len(header) or header[index + 1][0] != 70:
                raise ValueError(f"Invalid {name} header value.")
            matches.append(int(header[index + 1][1]))
    if len(matches) > 1:
        raise ValueError(f"Duplicate {name} header value.")
    return matches[0] if matches else None


def _groups(pairs):
    groups, name, fields = [], None, []
    for code, value in pairs:
        if code == 0:
            if name is not None:
                groups.append((name, fields))
            name, fields = value, []
        elif name is not None:
            fields.append((code, value))
        elif code != 999:
            raise ValueError("DXF entity data has no entity type.")
    if name is not None:
        groups.append((name, fields))
    if len(groups) > MAX_ENTITIES:
        raise NotImplementedError("DXF exceeds the bounded entity inspection limit.")
    return groups


def _planar(fields):
    # Reject nonfinite values even in optional geometry fields that a supported
    # entity does not otherwise need for its two-dimensional contour.
    for code, value in fields:
        if 10 <= code <= 59 or 110 <= code <= 149 or 210 <= code <= 239:
            if not math.isfinite(float(value)):
                raise ValueError(f"Non-finite geometry at DXF group code {code}.")
    for code in (30, 31, 38, 39):
        if _number(fields, code, "0") != 0:
            raise NotImplementedError("Nonzero elevation/thickness requires explicit plane normalization.")
    if tuple(_number(fields, code, default) for code, default in ((210, "0"), (220, "0"), (230, "1"))) != (0, 0, 1):
        raise NotImplementedError("Non-default extrusion axes require explicit coordinate transformation.")
    if int(_first(fields, 67, "0")) != 0:
        raise NotImplementedError("Paper-space geometry is not a flat-pattern cutting contour.")


def _arc(layer, center, radius, angle, sweep):
    if radius <= 0 or not math.isfinite(radius) or not 0 < abs(sweep) < TAU:
        raise ValueError("Arc needs positive radius and a nonzero sweep below 360 degrees.")
    start = (center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle))
    end = (center[0] + radius * math.cos(angle + sweep), center[1] + radius * math.sin(angle + sweep))
    return Segment(layer, start, end, center, radius, angle, sweep)


def _polyline(layer, vertices, closed):
    if len(vertices) < 2:
        raise ValueError("Polyline needs at least two vertices.")
    segments = []
    for index in range(len(vertices) if closed else len(vertices) - 1):
        x, y, bulge = vertices[index]
        start, end = (x, y), vertices[(index + 1) % len(vertices)][:2]
        chord = math.dist(start, end)
        if chord == 0:
            raise ValueError("Polyline has a zero-length segment.")
        if bulge == 0:
            segments.append(Segment(layer, start, end))
        else:
            offset = chord * (1 - bulge * bulge) / (4 * bulge)
            center = ((start[0] + end[0]) / 2 - (end[1] - start[1]) / chord * offset,
                      (start[1] + end[1]) / 2 + (end[0] - start[0]) / chord * offset)
            segment = _arc(layer, center, chord * (1 + bulge * bulge) / (4 * abs(bulge)),
                           math.atan2(start[1] - center[1], start[0] - center[0]), 4 * math.atan(bulge))
            # Preserve exact vertex identities rather than rounded trig results.
            segments.append(Segment(layer, start, end, segment.center, segment.radius, segment.angle, segment.sweep))
    return segments


def _vertices(fields):
    vertices, current = [], []
    for pair in fields:
        if pair[0] == 10:
            if current:
                vertices.append(current)
            current = [pair]
        elif current and pair[0] in (20, 40, 41, 42, 91):
            current.append(pair)
    if current:
        vertices.append(current)
    result = []
    for vertex in vertices:
        if _number(vertex, 40, "0") != 0 or _number(vertex, 41, "0") != 0:
            raise NotImplementedError("Variable-width polylines are not unambiguous cut paths.")
        result.append((_number(vertex, 10), _number(vertex, 20), _number(vertex, 42, "0")))
    return result


def _geometry(groups, report):
    segments, circles = [], []
    index = 0
    while index < len(groups):
        name, fields = groups[index]
        layer = str(_first(fields, 8, "0"))
        try:
            _planar(fields)
            if name == "LINE":
                segment = Segment(layer, (_number(fields, 10), _number(fields, 20)),
                                  (_number(fields, 11), _number(fields, 21)))
                if segment.length == 0:
                    raise ValueError("Zero-length LINE entity.")
                segments.append(segment)
            elif name in {"ARC", "CIRCLE"}:
                center, radius = (_number(fields, 10), _number(fields, 20)), _number(fields, 40)
                if radius <= 0:
                    raise ValueError("Circle/arc radius must be positive.")
                if name == "CIRCLE":
                    circles.append({"layer": layer, "center": list(center), "radius": radius})
                else:
                    angle, end = math.radians(_number(fields, 50)), math.radians(_number(fields, 51))
                    segments.append(_arc(layer, center, radius, angle, (end - angle) % TAU))
            elif name in {"LWPOLYLINE", "POLYLINE"}:
                flags = int(_first(fields, 70, "0"))
                if flags & ~129:
                    raise NotImplementedError("Fitted, three-dimensional or mesh polylines are unsupported.")
                if any(float(value) != 0 for code, value in fields if code in (40, 41, 43)):
                    raise NotImplementedError("Wide polylines are not unambiguous cut paths.")
                if name == "LWPOLYLINE":
                    vertices = _vertices(fields)
                    if len(vertices) != int(_first(fields, 90)):
                        raise ValueError("LWPOLYLINE vertex count does not match its declaration.")
                else:
                    vertices = []
                    index += 1
                    while index < len(groups) and groups[index][0] == "VERTEX":
                        vertex_fields = groups[index][1]
                        _planar(vertex_fields)
                        if int(_first(vertex_fields, 70, "0")) != 0:
                            raise NotImplementedError("Fitted or mesh VERTEX records are unsupported.")
                        vertices.extend(_vertices(vertex_fields))
                        index += 1
                    if index >= len(groups) or groups[index][0] != "SEQEND":
                        raise ValueError("POLYLINE has no matching SEQEND.")
                segments.extend(_polyline(layer, vertices, bool(flags & 1)))
            else:
                raise NotImplementedError(f"Unsupported entity type {name}; its geometry was not verified.")
        except NotImplementedError as error:
            report["unverified"].append({"code": "unsupported_geometry", "entity": name, "layer": layer, "message": str(error)})
        except (ValueError, OverflowError) as error:
            report["errors"].append({"code": "invalid_geometry", "entity": name, "layer": layer, "message": str(error)})
        index += 1
        if len(segments) > MAX_SEGMENTS:
            raise NotImplementedError("DXF exceeds the bounded contour inspection limit.")
    return segments, circles


def _topology(segments, tolerance):
    # Spatial buckets only find candidates; actual Euclidean distance decides
    # closure, avoiding the old parser's rounding-boundary false mismatches.
    points, buckets, edges = [], defaultdict(list), []
    def node(point):
        bucket = tuple(math.floor(value / tolerance) for value in point)
        candidates = [n for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                      for n in buckets[(bucket[0] + dx, bucket[1] + dy)]
                      if math.dist(points[n], point) <= tolerance]
        if len(candidates) > 1:
            raise NotImplementedError("Multiple contour vertices fall within the closure tolerance.")
        if candidates:
            return candidates[0]
        result = len(points)
        points.append(point)
        buckets[bucket].append(result)
        return result
    adjacency = defaultdict(list)
    for segment in segments:
        a, b = node(segment.start), node(segment.end)
        if a == b:
            raise ValueError("Contour segment is shorter than the verification tolerance.")
        edges.append((a, b))
        adjacency[a].append(b)
        adjacency[b].append(a)
    visited, closed, opened = set(), 0, 0
    for start in adjacency:
        if start in visited:
            continue
        pending, component = [start], set()
        while pending:
            current = pending.pop()
            if current in component:
                continue
            component.add(current)
            pending.extend(adjacency[current])
        visited.update(component)
        if all(len(adjacency[n]) == 2 for n in component):
            closed += 1
        else:
            opened += 1
    duplicate_edges = len(edges) - len(set(tuple(sorted(edge)) for edge in edges))
    # Two arcs with common endpoints can legitimately form a closed loop. Their
    # endpoints alone cannot establish duplicates; do not use duplicate_edges as
    # a geometry failure. Exact duplicate entities are checked independently.
    return {"closed_components": closed, "open_or_branched_components": opened,
            "vertex_count": len(points), "edge_count": len(edges),
            "degree_counts": dict(Counter(len(v) for v in adjacency.values())),
            "shared_endpoint_pairs": duplicate_edges}


def _cut_integrity(segments, circles, tolerance, report):
    def issue(kind, code, message):
        report[kind].append({"code": code, "message": message})
    layers = {s.layer.upper() for s in segments} | {c["layer"].upper() for c in circles}
    if layers - {"OUTER_LOOP", "INTERIOR_LOOPS"}:
        issue("unverified", "unknown_cut_layer", "Unrecognized cut-layer roles: " + ", ".join(sorted(layers - {"OUTER_LOOP", "INTERIOR_LOOPS"})))
    if any(s.center for s in segments):
        issue("unverified", "curved_contour_intersections", "ARC/bulged-polyline metrics were read, but their intersections and nesting are not supported by this bounded verifier.")
        return
    if len(segments) + len(circles) > 1000:
        issue("unverified", "intersection_limit", "The contour exceeds the bounded pairwise intersection check limit.")
        return
    def cross(a, b):
        return a[0] * b[1] - a[1] * b[0]
    def sub(a, b):
        return a[0] - b[0], a[1] - b[1]
    for i, a in enumerate(segments):
        r = sub(a.end, a.start)
        for b in segments[i + 1:]:
            s, delta = sub(b.end, b.start), sub(b.start, a.start)
            denominator = cross(r, s)
            epsilon = tolerance * max(a.length, b.length)
            if abs(denominator) <= epsilon:
                if abs(cross(delta, r)) > tolerance * a.length:
                    continue
                axis = 0 if abs(r[0]) >= abs(r[1]) else 1
                amin, amax = sorted((a.start[axis], a.end[axis]))
                bmin, bmax = sorted((b.start[axis], b.end[axis]))
                if min(amax, bmax) - max(amin, bmin) > tolerance:
                    issue("errors", "overlapping_cuts", "Cutting LINE segments overlap or duplicate one another.")
                    return
                continue
            t, u = cross(delta, s) / denominator, cross(delta, r) / denominator
            if -tolerance / a.length <= t <= 1 + tolerance / a.length and -tolerance / b.length <= u <= 1 + tolerance / b.length:
                if not any(math.dist(x, y) <= tolerance for x in (a.start, a.end) for y in (b.start, b.end)):
                    issue("errors", "intersecting_cuts", "Cutting LINE segments intersect away from a shared contour endpoint.")
                    return
    for i, circle in enumerate(circles):
        center, radius = circle["center"], circle["radius"]
        for segment in segments:
            delta = sub(segment.end, segment.start)
            t = max(0, min(1, sum((center[j] - segment.start[j]) * delta[j] for j in (0, 1)) / segment.length ** 2))
            closest = tuple(segment.start[j] + t * delta[j] for j in (0, 1))
            if math.dist(center, closest) <= radius + tolerance and max(math.dist(center, segment.start), math.dist(center, segment.end)) >= radius - tolerance:
                issue("errors", "intersecting_hole", "A circular cut touches or intersects another cut contour.")
                return
        for other in circles[i + 1:]:
            distance = math.dist(center, other["center"])
            if distance <= radius + other["radius"] + tolerance:
                if distance >= abs(radius - other["radius"]) - tolerance:
                    issue("errors", "intersecting_holes", "Circular cuts overlap or touch.")
                    return
                issue("unverified", "nested_circular_cuts", "Nested circular cuts need an explicit material-region check.")
    outer = [s for s in segments if s.layer.upper() == "OUTER_LOOP"]
    if not outer or any(c["layer"].upper() == "OUTER_LOOP" for c in circles):
        issue("unverified", "outer_region", "This bounded verifier requires a straight-segment OUTER_LOOP for region containment.")
        return
    if _topology(outer, tolerance)["closed_components"] != 1:
        issue("unverified", "outer_region", "Exactly one closed outer region has not been established.")
        return
    def inside(point, boundary):
        x, y = point
        crossings = 0
        for line in boundary:
            a, b = line.start, line.end
            if (a[1] > y) != (b[1] > y) and x < a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]):
                crossings += 1
        return crossings % 2 == 1
    interior = [s for s in segments if s.layer.upper() == "INTERIOR_LOOPS"]
    if any(not inside(c["center"], outer) for c in circles) or any(not inside(s.start, outer) for s in interior):
        issue("errors", "cut_outside_outer", "An interior cut contour lies outside the outer boundary.")
    if interior:
        issue("unverified", "interior_region_nesting", "Noncircular interior contour nesting needs an explicit material-region check.")


def _region_metrics(segments, circles, tolerance):
    outer = [s for s in segments if s.layer.upper() == "OUTER_LOOP"]
    remaining = outer[1:]
    polygon = [outer[0].start, outer[0].end]
    while remaining:
        matches = [(i, s.end if math.dist(polygon[-1], s.start) <= tolerance else s.start)
                   for i, s in enumerate(remaining)
                   if min(math.dist(polygon[-1], s.start), math.dist(polygon[-1], s.end)) <= tolerance]
        if len(matches) != 1:
            raise ValueError("Outer region cannot be traversed unambiguously.")
        index, point = matches[0]
        remaining.pop(index)
        polygon.append(point)
    area = abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(polygon, polygon[1:]))) / 2
    net_area = area - sum(math.pi * c["radius"] ** 2 for c in circles)
    result = {"net_area": net_area, "outer_perimeter": sum(s.length for s in outer),
              "inner_perimeter": sum(TAU * c["radius"] for c in circles), "inner_loop_count": len(circles)}
    if net_area <= 0 or not all(math.isfinite(value) for value in result.values()):
        raise ValueError("Flat region has nonpositive or nonfinite area/perimeter.")
    return result


def _native_scale(report, evidence, path, provider_id, document_id, metrics):
    """Compare actual provider measurements, bound to this exact exported file."""
    # Keep malformed/nonfinite provider measurements diagnosable without making
    # the verification report itself impossible to serialize as strict JSON.
    try:
        report_evidence = json.loads(json.dumps(evidence, allow_nan=False))
    except (TypeError, ValueError):
        report_evidence = {"invalid": "Provider evidence is not finite JSON."}
    comparison = {"status": "inconclusive", "evidence": report_evidence,
                  "tolerances": {"length_abs_mm": 1e-4, "area_abs_mm2": 1e-3, "relative": 1e-6}}
    report["native_geometry"] = comparison
    def reject(code, message, *, inconclusive=False):
        comparison["status"] = "inconclusive" if inconclusive else "fail"
        report["unverified" if inconclusive else "errors"].append({"code": code, "message": message})
        return None
    if not isinstance(evidence, dict):
        return reject("invalid_native_evidence", "Native flat measurement evidence is not a structured provider report.")
    status = evidence.get("evidenceStatus")
    if not isinstance(status, dict) or status.get("provenance") != "observed" or status.get("disposition") != "not_evaluated":
        return reject("native_evidence_unavailable", "The CAD provider did not return observed native flat measurements.", inconclusive=True)
    if evidence.get("nativeFlatUpToDate") is not True or evidence.get("unit") != "mm":
        return reject("native_evidence_unavailable", "Native flat measurements require an up-to-date model and explicit millimeter units.", inconclusive=True)
    if not provider_id or not document_id or evidence.get("providerId") != provider_id or evidence.get("documentId") != document_id:
        return reject("native_document_mismatch", "Native flat evidence does not match the bound CAD provider and document.")
    output_path = evidence.get("outputPath")
    if (not isinstance(output_path, str)
            or os.path.normcase(os.path.realpath(output_path)) != os.path.normcase(os.path.realpath(path))
            or evidence.get("outputSha256") != report["file"].get("sha256")):
        return reject("native_export_mismatch", "Native flat evidence does not match the exact exported DXF path and SHA-256.")
    names = ("netAreaMm2", "outerPerimeterMm", "innerPerimeterMm")
    if any(type(evidence.get(key)) not in (int, float) or not math.isfinite(evidence[key]) for key in names):
        return reject("invalid_native_measurement", "Native area and perimeter measurements must be finite numbers.")
    if (evidence["netAreaMm2"] <= 0 or evidence["outerPerimeterMm"] <= 0 or evidence["innerPerimeterMm"] < 0
            or type(evidence.get("innerLoopCount")) is not int or evidence["innerLoopCount"] < 0):
        return reject("invalid_native_measurement", "Native flat area, perimeter or loop count is invalid.")
    if metrics is None:
        return reject("native_comparison_unsupported", "The exported contour is not supported for native area/perimeter comparison.", inconclusive=True)
    if evidence["innerLoopCount"] != metrics["inner_loop_count"]:
        return reject("native_loop_mismatch", "Exported inner-loop count disagrees with the native flat model.")
    # Missing DXF units may be resolved only by a unique mm/in interpretation
    # matching all independent native metrics. Explicit other header units are
    # checked at their declared scale, never silently converted or overwritten.
    header_scale = report["units"]["scale_to_mm"]
    candidates = sorted({1.0, 25.4, *([header_scale] if header_scale else [])})
    comparisons, matches = [], []
    for scale in candidates:
        observed = {"netAreaMm2": metrics["net_area"] * scale ** 2,
                    "outerPerimeterMm": metrics["outer_perimeter"] * scale,
                    "innerPerimeterMm": metrics["inner_perimeter"] * scale}
        if not all(math.isfinite(value) for value in observed.values()):
            return reject("native_comparison_range", "Scaled DXF area/perimeters exceed the supported numeric range.")
        delta = {name: abs(observed[name] - evidence[name]) for name in names}
        passed = all(delta[name] <= max(1e-3 if name == "netAreaMm2" else 1e-4, abs(evidence[name]) * 1e-6) for name in names)
        comparisons.append({"scale_to_mm": scale, "matches": passed, "absolute_deltas": delta})
        if passed:
            matches.append(scale)
    comparison["candidates"] = comparisons
    if len(matches) != 1:
        return reject("native_geometry_mismatch", "No unique millimeter/inch scale matches the native flat area and both perimeters.", inconclusive=len(matches) > 1)
    scale = matches[0]
    if header_scale is not None and scale != header_scale:
        return reject("native_unit_conflict", "The DXF $INSUNITS header contradicts the measured native flat geometry.")
    if report["units"]["insunits"] not in (None, 0) and header_scale is None:
        return reject("unsupported_explicit_units", "An unsupported explicit DXF unit cannot be overridden by inferred scale.", inconclusive=True)
    comparison.update(status="pass", scale_to_mm=scale, source="provider_export_report")
    report["not_checked"].remove("Native flat-model geometry equivalence")
    if header_scale is None:
        report["units"].update(name="mm" if scale == 1 else "in", scale_to_mm=scale,
                              source="hash_bound_native_flat_geometry")
        report["unverified"] = [item for item in report["unverified"] if item["code"] != "units_unverified"]
    return scale


def verify_flat_dxf(path: str | Path, *, relative_path: str | None = None,
                    native_evidence: dict | None = None, provider_id: str | None = None,
                    document_id: str | None = None) -> dict:
    """Return evidence for this file; pass never means design acceptance."""
    path = Path(path)
    report = {"schema_version": 1, "verification": "flat_dxf_export_integrity",
              "status": "inconclusive", "file": {"path": relative_path or path.name},
              "units": {}, "entity_counts": {}, "contours": {}, "holes": {}, "bends": {},
              "geometry_raw": None, "native_geometry": {"status": "not_checked"},
              "bounds_raw": None, "bounds_mm": None, "errors": [], "unverified": [],
              "not_checked": ["Design-dependent dimensions and feature counts", "Material and bend allowance", "Native flat-model geometry equivalence",
                              "Supplier acceptance and manufacturing suitability"]}
    try:
        if path.stat().st_size > MAX_BYTES:
            raise NotImplementedError("DXF exceeds the 20 MiB bounded inspection limit.")
        data = path.read_bytes()
        report["file"].update(sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))
        sections = _sections(_pairs(data))
        header = sections.get("HEADER", [])
        code = _header_value(header, "$INSUNITS")
        measurement = _header_value(header, "$MEASUREMENT")
        unit, scale = UNITS.get(code, (None, None))
        report["units"] = {"insunits": code, "measurement": measurement, "name": unit,
                           "scale_to_mm": scale, "source": "$INSUNITS" if unit else None}
        if unit is None:
            report["unverified"].append({"code": "units_unverified", "message":
                "DXF has no supported explicit $INSUNITS length unit. $MEASUREMENT does not establish millimeters."})
        groups = _groups(sections["ENTITIES"])
        report["entity_counts"] = dict(Counter(f'{_first(fields, 8, "0")}:{name}' for name, fields in groups))
        segments, circles = _geometry(groups, report)
        if any(not math.isfinite(segment.length) for segment in segments):
            raise ValueError("Geometry contains a nonfinite calculated segment length.")
        cuts = [segment for segment in segments if segment.layer.upper() not in BEND_LAYERS]
        bends = [segment for segment in segments if segment.layer.upper() in BEND_LAYERS]
        if any(s.center for s in bends) or any(c["layer"].upper() in BEND_LAYERS for c in circles):
            report["unverified"].append({"code": "curved_bend_annotation", "message": "A bend-centerline layer contains curved entities."})
        cut_circles = [c for c in circles if c["layer"].upper() not in BEND_LAYERS]
        if not cuts and not cut_circles:
            report["errors"].append({"code": "no_cut_contours", "message": "DXF contains no supported cutting contours."})
        # Keep the tolerance explicit, and never label raw unknown-unit values mm.
        tolerance = 1e-5 / scale if scale else 1e-8
        report["contours"] = {**_topology(cuts, tolerance), "circle_count": len(cut_circles),
                              "closure_tolerance_raw": tolerance,
                              "closure_tolerance_mm": 1e-5 if scale else None}
        if report["contours"]["open_or_branched_components"]:
            report["errors"].append({"code": "open_contour", "message": "Cutting geometry contains an open or branched contour."})
        _cut_integrity(cuts, cut_circles, tolerance, report)
        signatures = [(s.layer, s.start, s.end, s.center, s.radius, s.angle, s.sweep) for s in cuts]
        if len(signatures) != len(set(signatures)):
            report["errors"].append({"code": "duplicate_entity", "message": "DXF contains duplicate cutting entities."})
        circle_signatures = [(c["layer"], *c["center"], c["radius"]) for c in cut_circles]
        if len(circle_signatures) != len(set(circle_signatures)):
            report["errors"].append({"code": "duplicate_entity", "message": "DXF contains duplicate circles."})
        if not report["errors"] and all(item["code"] == "units_unverified" for item in report["unverified"]):
            report["geometry_raw"] = _region_metrics(cuts, cut_circles, tolerance)
        if native_evidence is not None:
            verified_scale = _native_scale(report, native_evidence, path, provider_id, document_id, report["geometry_raw"])
            if verified_scale is not None:
                scale = verified_scale
                report["contours"]["closure_tolerance_mm"] = tolerance * scale
        points = [p for s in cuts for p in s.bounds_points()]
        for circle in cut_circles:
            x, y = circle["center"]
            radius = circle["radius"]
            points.extend(((x - radius, y - radius), (x + radius, y + radius)))
        if points:
            minimum = [min(p[axis] for p in points) for axis in (0, 1)]
            maximum = [max(p[axis] for p in points) for axis in (0, 1)]
            bounds = {"minimum": minimum, "maximum": maximum,
                      "size": [maximum[i] - minimum[i] for i in (0, 1)]}
            if not all(math.isfinite(v) for values in bounds.values() for v in values):
                raise ValueError("Geometry bounds are not finite.")
            report["bounds_raw"] = bounds
            scaled_bounds = {key: [v * scale for v in values] for key, values in bounds.items()} if scale else None
            if scaled_bounds and not all(math.isfinite(v) for values in scaled_bounds.values() for v in values):
                raise ValueError("Scaled geometry bounds exceed the supported numeric range.")
            report["bounds_mm"] = scaled_bounds
        diameters = [2 * c["radius"] * scale for c in cut_circles] if scale else None
        bend_lengths = [s.length * scale for s in bends] if scale else None
        if not all(math.isfinite(v) for v in (diameters or []) + (bend_lengths or [])):
            raise ValueError("Scaled geometry lengths exceed the supported numeric range.")
        report["holes"] = {"circular_contour_count": len(cut_circles), "circles_raw": cut_circles,
                           "diameters_mm": diameters,
                           "interpretation": "Circular cut contours; design role and nesting not verified."}
        report["bends"] = {"centerline_count": len(bends), "layers": dict(Counter(s.layer for s in bends)),
                           "lengths_mm": bend_lengths}
    except NotImplementedError as error:
        report["unverified"].append({"code": "unsupported_dxf", "message": str(error)})
    except (OSError, ValueError, UnicodeError, OverflowError) as error:
        report["errors"].append({"code": "invalid_dxf", "message": str(error)})
    report["status"] = "fail" if report["errors"] else "inconclusive" if report["unverified"] else "pass"
    return report
