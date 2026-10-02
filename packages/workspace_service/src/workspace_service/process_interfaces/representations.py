"""Bounded passive engineering readers; no provider, tool, or effect authority.

Views describe recorded nominal data. They are not a machine interpreter,
manufacturing approval, solver verification, or provider attestation. Unsupported
motion semantics fail explicitly instead of yielding an incomplete green view.
"""

from __future__ import annotations

import csv
import hashlib
import io
import math
from pathlib import PurePosixPath
import re
import zipfile


PARSER_VERSION = "wright.passive-representations/1"
MAX_SOURCE_BYTES = 32 * 1024 * 1024
MAX_GCODE_BYTES = 20 * 1024 * 1024
MAX_SEGMENTS = 1_000_000
MAX_LAYERS = 10_000
MAX_COORDINATE = 1_000_000
ARC_CHORD_ERROR_MM = 0.02


class RepresentationUnavailable(ValueError):
    """The complete passive view cannot be established within supported bounds."""


def _digest(content):
    return hashlib.sha256(content).hexdigest()


def _source(content, expected_digest, maximum):
    if not isinstance(content, bytes) or not 0 < len(content) <= maximum:
        raise RepresentationUnavailable(
            "The representation exceeds its passive reader bound."
        )
    if (
        not isinstance(expected_digest, str)
        or not re.fullmatch(r"[0-9a-f]{64}", expected_digest)
        or _digest(content) != expected_digest
    ):
        raise RepresentationUnavailable(
            "The reader input does not match the exact recorded artifact."
        )


def _finite(number):
    try:
        value = float(number)
    except (TypeError, ValueError) as error:
        raise RepresentationUnavailable(
            "A coordinate or value is not numeric."
        ) from error
    if not math.isfinite(value) or abs(value) > MAX_COORDINATE:
        raise RepresentationUnavailable(
            "A coordinate or value exceeds its finite view bound."
        )
    return value


_WORD = re.compile(r"([A-Za-z])([+-]?(?:\d+(?:\.\d*)?|\.\d+))")
_COMMAND = re.compile(r"^([GMT])\s*(\d+(?:\.\d+)?)", re.I)
_FEATURES = {
    "outer wall": "model",
    "inner wall": "model",
    "overhang wall": "model",
    "wall-outer": "model",
    "wall-inner": "model",
    "external perimeter": "model",
    "perimeter": "model",
    "overhang perimeter": "model",
    "bottom surface": "model",
    "top surface": "model",
    "top/bottom": "model",
    "solid infill": "model",
    "internal solid infill": "model",
    "sparse infill": "model",
    "infill": "model",
    "fill": "model",
    "bridge": "model",
    "bridge infill": "model",
    "support": "support",
    "support interface": "support",
    "support material": "support",
    "support material interface": "support",
    "support-interface": "support",
}


def _words(text):
    words, previous = {}, 0
    for match in _WORD.finditer(text):
        if text[previous : match.start()].strip():
            raise RepresentationUnavailable("The motion word syntax is unsupported.")
        key = match[1].upper()
        if key in words:
            raise RepresentationUnavailable("Repeated motion words are ambiguous.")
        words[key] = _finite(match[2])
        previous = match.end()
    if text[previous:].strip():
        raise RepresentationUnavailable("The motion word syntax is unsupported.")
    return words


def _arc(start, end, words, clockwise, units, absolute_center):
    """Tessellate an actual single planar arc with a declared chord error."""
    x, y, z = start
    ex, ey, ez = end
    if not math.isclose(z, ez, abs_tol=1e-7) or words.get("P", 1) != 1:
        raise RepresentationUnavailable(
            "Extruding helical or multiple-turn arcs have no supported view."
        )
    if "R" in words:
        if "I" in words or "J" in words:
            raise RepresentationUnavailable(
                "Mixed arc center and radius definitions are ambiguous."
            )
        signed_radius = words["R"] * units
        radius = abs(signed_radius)
        chord = math.hypot(ex - x, ey - y)
        if not chord or radius < chord / 2:
            raise RepresentationUnavailable(
                "The arc radius cannot establish its center."
            )
        distance = math.sqrt(max(0, radius * radius - chord * chord / 4))
        candidates = [
            (
                (x + ex) / 2 + direction * (y - ey) / chord * distance,
                (y + ey) / 2 + direction * (ex - x) / chord * distance,
            )
            for direction in (1, -1)
        ]
    elif "I" in words or "J" in words:
        if absolute_center and not {"I", "J"}.issubset(words):
            raise RepresentationUnavailable(
                "Absolute arc centers need both planar coordinates."
            )
        candidates = [
            (
                words.get("I", 0) * units + (0 if absolute_center else x),
                words.get("J", 0) * units + (0 if absolute_center else y),
            )
        ]
        radius = math.hypot(x - candidates[0][0], y - candidates[0][1])
        if not radius:
            raise RepresentationUnavailable("The arc has a zero radius.")
    else:
        raise RepresentationUnavailable("The arc has no supported center or radius.")
    selected = None
    for cx, cy in candidates:
        if not math.isclose(
            math.hypot(ex - cx, ey - cy), radius, rel_tol=1e-4, abs_tol=0.02
        ):
            raise RepresentationUnavailable(
                "The arc endpoints do not lie on its declared circle."
            )
        first = math.atan2(y - cy, x - cx)
        last = math.atan2(ey - cy, ex - cx)
        sweep = (
            -((first - last) % math.tau or math.tau)
            if clockwise
            else ((last - first) % math.tau or math.tau)
        )
        if "R" not in words or (abs(sweep) <= math.pi + 1e-7) == (signed_radius >= 0):
            selected = cx, cy, first, sweep
            break
    if selected is None:
        raise RepresentationUnavailable("The radius arc could not be resolved.")
    cx, cy, first, sweep = selected
    angle = 2 * math.acos(max(-1, 1 - min(ARC_CHORD_ERROR_MM, radius) / radius))
    count = max(1, math.ceil(abs(sweep) / min(angle, math.pi / 12)))
    if count > 10_000:
        raise RepresentationUnavailable(
            "The arc tessellation exceeds its segment bound."
        )
    points = [(x, y)]
    for index in range(1, count):
        a = first + sweep * index / count
        points.append(
            (_finite(cx + radius * math.cos(a)), _finite(cy + radius * math.sin(a)))
        )
    points.append((ex, ey))
    return [[*a, *b] for a, b in zip(points, points[1:])]


def read_gcode_toolpaths(
    content: bytes,
    expected_digest: str,
    *,
    package_digest: str | None = None,
    entry: str | None = None,
):
    """Read true layer comments and extrusion moves; never execute G-code.

    Supports mm/inch, absolute/relative axes and extrusion, planar IJ/R arcs,
    common layer/feature comments and G92 resets. Missing layers, unknown motion
    transforms and unsupported extruding arcs are explicit download fallbacks.
    """
    _source(content, expected_digest, MAX_GCODE_BYTES)
    if package_digest is not None and not re.fullmatch(r"[0-9a-f]{64}", package_digest):
        raise RepresentationUnavailable("The package identity is invalid.")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeError as error:
        raise RepresentationUnavailable(
            "The G-code is not supported UTF-8 text."
        ) from error
    layers, layer = [], None
    position = {axis: None for axis in "XYZ"}
    units, axes_absolute, extrusion_absolute, center_absolute = 1.0, True, True, False
    extrusions, tool, plane = {0: 0.0}, 0, "G17"
    feature, known_features, unknown_features = "unclassified", set(), set()
    total, arc_count, unlayered = 0, 0, 0
    for line_number, original in enumerate(text.splitlines(), 1):
        if line_number > 2_000_000 or len(original) > 65_536:
            raise RepresentationUnavailable("The G-code line bound is exceeded.")
        command_text, _, comment = original.partition(";")
        if len(command_text) > 4096:
            raise RepresentationUnavailable("The G-code command bound is exceeded.")
        comment = comment.strip()
        feature_match = re.fullmatch(r"(?:FEATURE|TYPE)\s*:\s*(.+)", comment, re.I)
        if feature_match:
            label = feature_match[1].strip().lower()
            if len(label) > 256:
                raise RepresentationUnavailable(
                    "A feature label exceeds its passive bound."
                )
            feature = _FEATURES.get(label, "unclassified")
            (known_features if feature != "unclassified" else unknown_features).add(
                label
            )
            if len(unknown_features) > 256:
                raise RepresentationUnavailable(
                    "The feature evidence exceeds its passive bound."
                )
        if comment.upper() in {"CHANGE_LAYER", "LAYER_CHANGE"}:
            marker = len(layers)
            layer = {
                "index": marker,
                "z": None,
                "model": [],
                "support": [],
                "unclassified": [],
            }
            layers.append(layer)
        elif match := re.fullmatch(r"LAYER\s*:\s*(-?\d+)", comment, re.I):
            source_index = int(match[1])
            if layers and source_index <= layers[-1].get("source_index", -10_001):
                raise RepresentationUnavailable(
                    "The source layer indices are not ordered."
                )
            marker = len(layers)
            layer = {
                "index": marker,
                "source_index": source_index,
                "z": None,
                "model": [],
                "support": [],
                "unclassified": [],
            }
            layers.append(layer)
        if len(layers) > MAX_LAYERS:
            raise RepresentationUnavailable(
                "The layer count exceeds the passive view bound."
            )
        if match := re.fullmatch(
            r"(?:Z_HEIGHT|Z)\s*:\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))", comment, re.I
        ):
            if layer is not None:
                layer["z"] = _finite(_finite(match[1]) * units)
        # Parenthesized comments do not contribute executable words to a passive view.
        command_text = re.sub(r"\([^()]*\)", "", command_text).strip()
        command_text = re.sub(r"^N\d+\s*", "", command_text, flags=re.I)
        if not command_text:
            continue
        match = _COMMAND.match(command_text)
        if not match:
            raise RepresentationUnavailable(
                f"Unsupported command syntax at line {line_number}."
            )
        letter, code = match[1].upper(), match[2]
        command = letter + code
        if letter == "M" and command not in {"M82", "M83", "M200", "M206", "M218"}:
            continue  # Nonmotion firmware commands are not simulated or attested.
        if command in {"M200", "M206", "M218"}:
            raise RepresentationUnavailable(
                "Volumetric extrusion or firmware coordinate offsets are unsupported."
            )
        words = _words(command_text[match.end() :])
        if letter == "T":
            if not code.isdigit() or not 0 <= int(code) < 64 or words:
                raise RepresentationUnavailable(
                    "The tool-selection syntax is unsupported."
                )
            tool = int(code)
            extrusions.setdefault(tool, 0.0)
        elif command in {"G90", "G91"}:
            axes_absolute = command == "G90"
            extrusion_absolute = axes_absolute
        elif command in {"G90.1", "G91.1"}:
            center_absolute = command == "G90.1"
        elif command in {"M82", "M83"}:
            extrusion_absolute = command == "M82"
        elif command in {"G20", "G21"}:
            units = 25.4 if command == "G20" else 1.0
        elif command in {"G17", "G18", "G19"}:
            plane = command
        elif command == "G28":
            for axis in "XYZ":
                if not any(a in words for a in "XYZ") or axis in words:
                    position[axis] = None
        elif command == "G92":
            for axis in "XYZ":
                if axis in words:
                    position[axis] = words[axis] * units
            if "E" in words:
                extrusions[tool] = words["E"] * units
        elif command in {"G0", "G1", "G2", "G3"}:
            if set(words) - set("XYZEFIJRP"):
                raise RepresentationUnavailable(
                    "The motion uses unsupported axes or words."
                )
            before = dict(position)
            for axis in "XYZ":
                if axis in words:
                    if not axes_absolute and position[axis] is None:
                        raise RepresentationUnavailable(
                            "Relative motion begins without a known axis position."
                        )
                    position[axis] = _finite(
                        words[axis] * units + (0 if axes_absolute else position[axis])
                    )
            amount = words.get("E", 0) * units
            delta = (
                amount - extrusions[tool]
                if extrusion_absolute and "E" in words
                else amount
            )
            if "E" in words:
                extrusions[tool] = (
                    amount if extrusion_absolute else extrusions[tool] + amount
                )
            moving = command in {"G2", "G3"} or any(axis in words for axis in "XY")
            if delta <= 1e-9 or not moving:
                continue
            if layer is None:
                unlayered += 1
                continue
            if any(value is None for value in (*before.values(), *position.values())):
                raise RepresentationUnavailable(
                    "An extrusion move lacks a known XYZ start or end."
                )
            z = position["Z"]
            if layer["z"] is None:
                layer["z"] = z
            if not math.isclose(before["Z"], z, abs_tol=1e-7) or not math.isclose(
                layer["z"], z, abs_tol=1e-5
            ):
                raise RepresentationUnavailable(
                    "Extrusion leaves the declared planar layer."
                )
            if command in {"G2", "G3"}:
                if plane != "G17":
                    raise RepresentationUnavailable(
                        "Only planar XY extrusion arcs are supported."
                    )
                segments = _arc(
                    tuple(before.values()),
                    tuple(position.values()),
                    words,
                    command == "G2",
                    units,
                    center_absolute,
                )
                arc_count += 1
            else:
                segments = [[before["X"], before["Y"], position["X"], position["Y"]]]
            total += len(segments)
            if total > MAX_SEGMENTS:
                raise RepresentationUnavailable(
                    "The toolpath segment bound is exceeded."
                )
            layer[feature].extend(segments)
        elif command != "G4":
            raise RepresentationUnavailable(
                f"Unsupported motion or coordinate semantics: {command}."
            )
    if not total or any(item["z"] is None for item in layers):
        raise RepresentationUnavailable(
            "True finite layer/extrusion data is unavailable."
        )
    return {
        "format": "wright.gcode.toolpaths.v1",
        "package_sha256": package_digest or expected_digest,
        "classification_source": "gcode_feature_comments"
        if known_features
        else "unknown",
        "layers": layers,
        "provenance": {
            "reader": PARSER_VERSION,
            "source_sha256": expected_digest,
            "archive_entry": entry,
            "method": "recorded planar extrusion commands and explicit layer/feature comments",
            "units": "mm",
            "segments": total,
            "extruding_arcs": arc_count,
            "arc_maximum_chord_error_mm": ARC_CHORD_ERROR_MM,
            "unlayered_extrusion_commands_excluded": unlayered,
            "recognized_features": sorted(known_features),
            "unclassified_features": sorted(unknown_features),
            "limits": "Nominal paths; firmware commands are not executed, and machine/material acceptance is not established.",
            "engineering_acceptance": False,
        },
    }


def read_3mf_toolpaths(
    content: bytes, expected_digest: str, *, entry: str | None = None
):
    """Read one explicit plate, never merge or select an ambiguous package."""
    _source(content, expected_digest, MAX_SOURCE_BYTES)
    # Bound ZipFile's materialized directory before it allocates entry objects.
    # A coincidental signature in compressed data may conservatively refuse a view.
    if content.count(b"PK\x01\x02") > 2048:
        raise RepresentationUnavailable(
            "The package directory exceeds its passive read bound."
        )
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            entries = archive.infolist()
            if (
                len(entries) > 2048
                or sum(item.file_size for item in entries) > 100 * 1024 * 1024
            ):
                raise RepresentationUnavailable(
                    "The package archive exceeds its passive read bound."
                )
            names = [item.filename for item in entries]
            if len(set(names)) != len(names):
                raise RepresentationUnavailable(
                    "The archive contains ambiguous duplicate entries."
                )
            for item in entries:
                # ZipInfo normalizes host separators and truncates NUL names;
                # validate the original archive spelling, not only its safe-looking result.
                original_name = item.orig_filename
                path = PurePosixPath(original_name)
                if (
                    original_name != item.filename
                    or path.is_absolute()
                    or ".." in path.parts
                    or "\\" in original_name
                    or ":" in original_name
                ):
                    raise RepresentationUnavailable(
                        "The archive entry names are unsupported."
                    )
                if item.flag_bits & 1 or item.compress_type not in {
                    zipfile.ZIP_STORED,
                    zipfile.ZIP_DEFLATED,
                }:
                    raise RepresentationUnavailable(
                        "Encrypted or unsupported archive compression is unavailable."
                    )
            candidates = [
                item for item in entries if item.filename.lower().endswith(".gcode")
            ]
            if entry is None:
                if len(candidates) != 1:
                    raise RepresentationUnavailable(
                        "Select an exact G-code plate; this package has none or several."
                    )
                selected = candidates[0]
            else:
                selected = next(
                    (item for item in candidates if item.filename == entry), None
                )
                if selected is None:
                    raise RepresentationUnavailable(
                        "The selected plate is not an exact package entry."
                    )
            if selected.file_size > MAX_GCODE_BYTES:
                raise RepresentationUnavailable(
                    "The selected G-code exceeds its passive read bound."
                )
            with archive.open(selected) as stream:
                gcode = stream.read(MAX_GCODE_BYTES + 1)
            return read_gcode_toolpaths(
                gcode,
                _digest(gcode),
                package_digest=expected_digest,
                entry=selected.filename,
            )
    except (zipfile.BadZipFile, RuntimeError, EOFError, OSError) as error:
        raise RepresentationUnavailable(
            "The package could not be read as supported passive data."
        ) from error


def read_scalar_csv(
    content: bytes, expected_digest: str, *, x: str, y: str, z: str, value: str
):
    """Read exact configured columns as samples; do not infer units or geometry."""
    _source(content, expected_digest, 2 * 1024 * 1024)
    columns = (x, y, z, value)
    if len(set(columns)) != 4 or any(
        not isinstance(name, str) or not 0 < len(name) <= 128 for name in columns
    ):
        raise RepresentationUnavailable("Select four distinct bounded field columns.")
    try:
        rows = csv.reader(
            io.StringIO(content.decode("utf-8-sig"), newline=""), strict=True
        )
        headers = next(rows)
        if (
            len(headers) > 50
            or len(set(headers)) != len(headers)
            or not set(columns).issubset(headers)
        ):
            raise RepresentationUnavailable(
                "The exact field columns are absent or ambiguous."
            )
        positions = [headers.index(name) for name in columns]
        points = []
        for row in rows:
            if (
                len(row) != len(headers)
                or any(len(cell) > 8192 for cell in row)
                or len(points) >= 10_000
            ):
                raise RepresentationUnavailable(
                    "The field rows exceed their supported shape or bound."
                )
            points.append([_finite(row[index]) for index in positions])
        if not points:
            raise RepresentationUnavailable(
                "No actual numeric field samples were supplied."
            )
    except (csv.Error, UnicodeError, StopIteration) as error:
        raise RepresentationUnavailable(
            "The numerical CSV is not supported finite tabular data."
        ) from error
    return {
        "format": "wright.scalar-field.v1",
        "source_sha256": expected_digest,
        "columns": {"x": x, "y": y, "z": z, "value": value},
        "points": points,
        "provenance": {
            "reader": PARSER_VERSION,
            "method": "exact configured CSV columns; raw XYZ/value samples",
            "units": "as declared by source columns",
            "interpolated_geometry": False,
            "engineering_acceptance": False,
        },
    }
