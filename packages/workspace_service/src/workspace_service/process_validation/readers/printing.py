"""Bounded independent inspection of printable meshes and slicer evidence."""

from __future__ import annotations

from collections import Counter
import io
import json
import math
import re
import struct
from zipfile import BadZipFile, ZipFile

from core.process_validation import Measurement, ReaderIdentity, canonical_digest

from .base import ValidationIssue


_STL_SELECTOR = re.compile(r"^mesh/(x|y|z)_(min|max|span)_mm$")
_MAX_ARCHIVE_ENTRIES = 256
_MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
_MAX_COMPRESSION_RATIO = 200


def _defect(code: str, message: str) -> ValidationIssue:
    return ValidationIssue(
        code,
        message,
        state="fail",
        category="output_defect",
        action="revise_output",
    )


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate member")
        value[key] = item
    return value


def _constant(_):
    raise ValueError("nonfinite number")


def _json_object(content: bytes, name: str) -> dict:
    try:
        value = json.loads(
            content.decode("utf-8-sig"),
            object_pairs_hook=_pairs,
            parse_constant=_constant,
        )
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise _defect(
            "printing.invalid_json", f"{name} must be unambiguous finite JSON."
        ) from exc
    if not isinstance(value, dict):
        raise _defect("printing.invalid_json", f"{name} must be a JSON object.")
    return value


def _stl(content: bytes, context) -> dict:
    if len(content) < 84:
        raise _defect("printing.invalid_stl", "The printable mesh is not a binary STL.")
    count = struct.unpack_from("<I", content, 80)[0]
    if count < 4 or len(content) != 84 + count * 50:
        raise _defect(
            "printing.invalid_stl",
            "The binary STL triangle count does not match its exact byte length.",
        )
    context.checkpoint(entities=count * 4)
    minimum = [math.inf, math.inf, math.inf]
    maximum = [-math.inf, -math.inf, -math.inf]
    edges: Counter[tuple[tuple[float, float, float], tuple[float, float, float]]] = (
        Counter()
    )
    degenerate = 0
    for index in range(count):
        values = struct.unpack_from("<12fH", content, 84 + index * 50)
        if not all(math.isfinite(item) for item in values[:12]):
            raise _defect(
                "printing.nonfinite_stl",
                "The printable mesh contains nonfinite coordinates.",
            )
        vertices = tuple(
            tuple(float(item) for item in values[offset : offset + 3])
            for offset in (3, 6, 9)
        )
        for vertex in vertices:
            for axis, coordinate in enumerate(vertex):
                minimum[axis] = min(minimum[axis], coordinate)
                maximum[axis] = max(maximum[axis], coordinate)
        ab = tuple(vertices[1][axis] - vertices[0][axis] for axis in range(3))
        ac = tuple(vertices[2][axis] - vertices[0][axis] for axis in range(3))
        cross = (
            ab[1] * ac[2] - ab[2] * ac[1],
            ab[2] * ac[0] - ab[0] * ac[2],
            ab[0] * ac[1] - ab[1] * ac[0],
        )
        if sum(item * item for item in cross) <= 1e-20:
            degenerate += 1
        for left, right in (
            (vertices[0], vertices[1]),
            (vertices[1], vertices[2]),
            (vertices[2], vertices[0]),
        ):
            edges[tuple(sorted((left, right)))] += 1
        if index % 1024 == 0:
            context.checkpoint(entities=count + len(edges))
    context.checkpoint(entities=count + len(edges))
    return {
        "triangle_count": count,
        "minimum": tuple(minimum),
        "maximum": tuple(maximum),
        "span": tuple(maximum[i] - minimum[i] for i in range(3)),
        "degenerate_triangles": degenerate,
        "boundary_edges": sum(value == 1 for value in edges.values()),
        "nonmanifold_edges": sum(value > 2 for value in edges.values()),
    }


def _archive(content: bytes, context) -> set[str]:
    try:
        with ZipFile(io.BytesIO(content)) as archive:
            entries = archive.infolist()
            context.checkpoint(entities=len(entries))
            if not entries or len(entries) > _MAX_ARCHIVE_ENTRIES:
                raise _defect(
                    "printing.package_entries",
                    "The slice package has an unsupported number of members.",
                )
            names = [entry.filename.replace("\\", "/") for entry in entries]
            if len(names) != len(set(names)):
                raise _defect(
                    "printing.package_duplicates",
                    "The slice package contains duplicate member names.",
                )
            total = 0
            for entry, name in zip(entries, names, strict=True):
                parts = name.split("/")
                if (
                    not name
                    or name.startswith("/")
                    or re.match(r"^[A-Za-z]:", name)
                    or ".." in parts
                    or entry.flag_bits & 0x1
                ):
                    raise _defect(
                        "printing.package_member",
                        "The slice package contains an unsafe or encrypted member.",
                    )
                total += entry.file_size
                if total > _MAX_ARCHIVE_BYTES:
                    raise _defect(
                        "printing.package_size",
                        "The expanded slice package exceeds the inspection limit.",
                    )
                if entry.file_size and entry.compress_size == 0:
                    raise _defect(
                        "printing.package_ratio",
                        "The slice package contains an invalid compressed member.",
                    )
                if (
                    entry.compress_size
                    and entry.file_size / entry.compress_size > _MAX_COMPRESSION_RATIO
                ):
                    raise _defect(
                        "printing.package_ratio",
                        "The slice package exceeds the allowed compression ratio.",
                    )
            if archive.testzip() is not None:
                raise _defect(
                    "printing.package_crc", "The slice package contains corrupt data."
                )
            return set(names)
    except ValidationIssue:
        raise
    except (BadZipFile, OSError, RuntimeError) as exc:
        raise _defect(
            "printing.invalid_package", "The slice package is not a valid 3MF ZIP."
        ) from exc


def _related(context, *roles):
    snapshots = {item.subject.role: item for item in context.related_snapshots}
    missing = [role for role in roles if role not in snapshots]
    if missing:
        raise ValidationIssue(
            "subject.related_role_missing",
            f"Bind the required related output role '{missing[0]}'.",
        )
    return tuple(snapshots[role] for role in roles)


class PrintingArtifactReader:
    identity = ReaderIdentity(
        id="printing",
        version="1",
        config_digest=canonical_digest(
            {
                "formats": ["binary-stl", "json-evidence", "3mf-zip"],
                "checks": [
                    "mesh-envelope-and-integrity",
                    "distinct-mesh-lineage",
                    "slice-hash-binding",
                    "safe-package-inventory",
                    "simulator-transfer-binding",
                ],
                "version": 1,
            }
        ),
        method="independent_measurement",
        tool_identity="wright bounded print artifact reader v1",
        formats=("stl", "json", "3mf"),
    )

    def measure(self, snapshot, check, context):
        operation = check.parameters.get("operation")
        evidence = [
            f"subject:{snapshot.subject.id}@{snapshot.subject.sha256}#{check.selector}"
        ]
        unit = None
        if operation in {"stl_dimension", "mesh_integrity"}:
            if snapshot.subject.format != "stl":
                raise _defect(
                    "printing.mesh_format", "Mesh checks require a binary STL."
                )
            if check.parameters.get("unit_convention") != "mm":
                raise ValidationIssue(
                    "profile.printing_unit",
                    "STL checks require a source-backed millimetre unit convention.",
                    category="source_conflict",
                )
            mesh = _stl(snapshot.content, context)
            if operation == "mesh_integrity":
                if any(
                    mesh[key]
                    for key in (
                        "degenerate_triangles",
                        "boundary_edges",
                        "nonmanifold_edges",
                    )
                ):
                    raise _defect(
                        "printing.mesh_integrity",
                        "The repaired mesh is not a closed nondegenerate two-manifold.",
                    )
                observed = True
            else:
                match = _STL_SELECTOR.fullmatch(check.selector)
                if not match:
                    raise ValidationIssue(
                        "profile.printing_selector",
                        "STL dimension checks require a mesh axis minimum, maximum or span selector.",
                        category="source_conflict",
                    )
                axis = {"x": 0, "y": 1, "z": 2}[match.group(1)]
                observed = mesh[match.group(2)][axis]
                unit = "mm"
        elif operation == "mesh_lineage":
            (source,) = _related(context, "source_mesh")
            if snapshot.subject.format != "stl" or source.subject.format != "stl":
                raise _defect(
                    "printing.mesh_format",
                    "Mesh lineage requires two binary STL files.",
                )
            if snapshot.subject.sha256 == source.subject.sha256:
                raise _defect(
                    "printing.mesh_not_distinct",
                    "Source and repaired meshes are byte-identical; provide a distinct repaired revision.",
                )
            repaired_mesh = _stl(snapshot.content, context)
            source_mesh = _stl(source.content, context)
            tolerance = check.parameters.get("span_tolerance_mm", 0.01)
            if type(tolerance) not in {int, float} or not math.isfinite(tolerance):
                raise ValidationIssue(
                    "profile.printing_tolerance",
                    "Mesh lineage tolerance must be finite.",
                    category="source_conflict",
                )
            if any(
                abs(left - right) > tolerance
                for left, right in zip(
                    repaired_mesh["span"], source_mesh["span"], strict=True
                )
            ):
                raise _defect(
                    "printing.mesh_geometry_changed",
                    "The repaired mesh envelope no longer matches the source geometry.",
                )
            observed = True
            evidence.append(
                f"subject:{source.subject.id}@{source.subject.sha256}#mesh-lineage"
            )
        elif operation == "slice_binding":
            repaired, package = _related(context, "repaired_mesh", "slice_package")
            value = _json_object(snapshot.content, "Slice evidence")
            valid = (
                value.get("operation")
                == check.parameters.get(
                    "expected_operation", "actual_local_bambu_slice"
                )
                and value.get("simulation") is False
                and value.get("exit_code") == 0
                and value.get("source_sha256") == repaired.subject.sha256
                and value.get("package_sha256") == package.subject.sha256
            )
            if not valid:
                raise _defect(
                    "printing.slice_binding",
                    "Slice evidence must record a successful real local slice bound to the exact repaired mesh and 3MF bytes.",
                )
            observed = True
            evidence.extend(
                (
                    f"subject:{repaired.subject.id}@{repaired.subject.sha256}#slice-input",
                    f"subject:{package.subject.id}@{package.subject.sha256}#slice-output",
                )
            )
        elif operation == "package_inventory":
            members = _archive(snapshot.content, context)
            required = check.parameters.get("required_members")
            if (
                not isinstance(required, list)
                or not required
                or any(not isinstance(item, str) or not item for item in required)
            ):
                raise ValidationIssue(
                    "profile.printing_members",
                    "Slice-package checks require explicit member names.",
                    category="source_conflict",
                )
            missing = sorted(set(required) - members)
            if missing:
                raise _defect(
                    "printing.package_missing",
                    "The slice package is missing required members: "
                    + ", ".join(missing),
                )
            observed = len(set(required))
            unit = "1"
        elif operation == "transfer_binding":
            (package,) = _related(context, "slice_package")
            value = _json_object(snapshot.content, "Transfer receipt")
            destination = value.get("destination")
            digests = value.get("artifact_digests")
            valid = (
                value.get("integration_test") is True
                and value.get("simulated_handoff") is True
                and value.get("network_dispatch") is False
                and isinstance(destination, dict)
                and destination.get("kind") == "integration_test"
                and isinstance(digests, list)
                and package.subject.sha256 in digests
            )
            if not valid:
                raise _defect(
                    "printing.transfer_binding",
                    "Transfer evidence must be simulator-only, non-networked and bound to the exact 3MF digest.",
                )
            observed = True
            evidence.append(
                f"subject:{package.subject.id}@{package.subject.sha256}#simulated-transfer"
            )
        else:
            raise ValidationIssue(
                "profile.printing_operation",
                "Print-artifact check requests an unsupported operation.",
                category="source_conflict",
            )
        identity = canonical_digest(
            {
                "subject": snapshot.subject,
                "check": check,
                "reader": self.identity,
                "related": tuple(item.subject for item in context.related_snapshots),
            }
        )
        return Measurement(
            id="m-" + identity,
            subject_id=snapshot.subject.id,
            subject_sha256=snapshot.subject.sha256,
            selector=check.selector,
            value=observed,
            unit=unit,
            frame=check.frame,
            uncertainty=0.0,
            reader=self.identity,
            evidence_refs=tuple(evidence),
        )
