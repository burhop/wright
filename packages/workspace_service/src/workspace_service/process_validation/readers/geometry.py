"""Bounded actual-file STEP circle measurements for datum-controlled jig seats."""

from __future__ import annotations

import math
import re

from core.process_validation import Measurement, ReaderIdentity, canonical_digest

from .base import ValidationIssue


_ENTITY = re.compile(rb"#([0-9]+)\s*=\s*([A-Z0-9_]+)\s*\((.*?)\)\s*;", re.DOTALL)
_REFERENCE = re.compile(rb"#([0-9]+)")
_NUMBER = re.compile(
    rb"(?<![A-Z0-9_])[-+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[ED][-+]?[0-9]+)?",
    re.IGNORECASE,
)
_SELECTOR = re.compile(r"^seat/([A-Za-z0-9_.-]+)/(?:(center)_(x|y)_mm|(diameter)_mm)$")


def _defect(code: str, message: str):
    return ValidationIssue(
        code,
        message,
        state="fail",
        category="output_defect",
        action="revise_output",
    )


def _finite_number(raw: bytes) -> float:
    value = float(raw.decode("ascii").replace("D", "E").replace("d", "e"))
    if not math.isfinite(value):
        raise ValueError("nonfinite STEP number")
    return value


def _entities(content: bytes, context):
    if not content.lstrip().startswith(b"ISO-10303-21;"):
        raise _defect(
            "geometry.invalid_step", "Output is not an ISO-10303-21 STEP file."
        )
    entities = {}
    for count, match in enumerate(_ENTITY.finditer(content), start=1):
        context.checkpoint(entities=count)
        identifier = int(match.group(1))
        if identifier in entities:
            raise _defect(
                "geometry.duplicate_entity", "STEP entity IDs must be unique."
            )
        entities[identifier] = (match.group(2).decode("ascii"), match.group(3))
    if not entities or b"END-ISO-10303-21;" not in content:
        raise _defect("geometry.invalid_step", "STEP exchange structure is incomplete.")
    return entities


def _vector(entity, expected: str):
    name, arguments = entity
    if name != expected:
        raise ValueError(f"expected {expected}")
    vectors = re.findall(rb"\(([^()]*)\)", arguments)
    if not vectors:
        raise ValueError("missing coordinate tuple")
    values = [_finite_number(item) for item in _NUMBER.findall(vectors[-1])]
    if len(values) not in {2, 3}:
        raise ValueError("invalid coordinate count")
    return tuple([*values, 0.0][:3])


def _matrix(value):
    if (
        not isinstance(value, list)
        or len(value) != 4
        or any(not isinstance(row, list) or len(row) != 4 for row in value)
    ):
        raise ValidationIssue(
            "profile.datum_transform",
            "Geometry checks require a finite 4x4 model-to-workpiece transform.",
            category="source_conflict",
        )
    try:
        result = tuple(tuple(float(item) for item in row) for row in value)
    except (TypeError, ValueError) as exc:
        raise ValidationIssue(
            "profile.datum_transform",
            "Geometry datum transform contains a nonnumeric value.",
            category="source_conflict",
        ) from exc
    if not all(math.isfinite(item) for row in result for item in row) or result[3] != (
        0.0,
        0.0,
        0.0,
        1.0,
    ):
        raise ValidationIssue(
            "profile.datum_transform",
            "Geometry datum transform must be finite and affine.",
            category="source_conflict",
        )
    return result


def _point(matrix, point):
    return tuple(
        sum(matrix[row][column] * (*point, 1.0)[column] for column in range(4))
        for row in range(3)
    )


def _direction(matrix, direction):
    transformed = tuple(
        sum(matrix[row][column] * direction[column] for column in range(3))
        for row in range(3)
    )
    length = math.sqrt(sum(item * item for item in transformed))
    if length <= 0:
        raise ValueError("zero direction")
    return tuple(item / length for item in transformed)


class StepSeatGeometryReader:
    identity = ReaderIdentity(
        id="step-seat-geometry",
        version="1",
        config_digest=canonical_digest(
            {
                "format": "ISO-10303-21",
                "entities": [
                    "CIRCLE",
                    "AXIS2_PLACEMENT_3D",
                    "CARTESIAN_POINT",
                    "DIRECTION",
                ],
                "center": "axis-placement-origin",
                "version": 1,
            }
        ),
        method="native_inspection",
        tool_identity="wright bounded STEP circle-placement reader v1",
        formats=("step", "stp"),
    )

    def measure(self, snapshot, check, context):
        match = _SELECTOR.fullmatch(check.selector)
        if not match:
            raise ValidationIssue(
                "profile.geometry_selector",
                "STEP seat selector must name a seat center axis or diameter.",
                category="source_conflict",
            )
        parameters = check.parameters
        try:
            nominal = tuple(float(item) for item in parameters["nominal_center_mm"])
            nominal_diameter = float(parameters["nominal_diameter_mm"])
            capture = float(parameters["capture_radius_mm"])
            radius_tolerance = float(parameters.get("radius_match_tolerance_mm", 0.05))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValidationIssue(
                "profile.geometry_parameters",
                "STEP seat checks require finite nominal center, diameter and capture parameters.",
                category="source_conflict",
            ) from exc
        if (
            len(nominal) != 2
            or not all(
                math.isfinite(item)
                for item in (*nominal, nominal_diameter, capture, radius_tolerance)
            )
            or nominal_diameter <= 0
            or capture <= 0
            or radius_tolerance < 0
        ):
            raise ValidationIssue(
                "profile.geometry_parameters",
                "STEP seat geometry parameters are invalid.",
                category="source_conflict",
            )
        transform = _matrix(parameters.get("datum_transform_model_to_workpiece"))
        entities = _entities(snapshot.content, context)
        circles = []
        try:
            for identifier, (name, arguments) in entities.items():
                if name != "CIRCLE":
                    continue
                refs = [int(item) for item in _REFERENCE.findall(arguments)]
                numbers = [_finite_number(item) for item in _NUMBER.findall(arguments)]
                if not refs or not numbers:
                    raise ValueError("invalid circle")
                placement = entities[refs[0]]
                # STEP surface parameterizations also contain 2-D circles. They
                # are not model-space edge evidence and are deliberately ignored.
                if placement[0] == "AXIS2_PLACEMENT_2D":
                    continue
                placement_refs = [
                    int(item) for item in _REFERENCE.findall(placement[1])
                ]
                if placement[0] != "AXIS2_PLACEMENT_3D" or len(placement_refs) < 2:
                    raise ValueError("invalid circle placement")
                center = _point(
                    transform, _vector(entities[placement_refs[0]], "CARTESIAN_POINT")
                )
                axis = _direction(
                    transform, _vector(entities[placement_refs[1]], "DIRECTION")
                )
                circles.append((identifier, center, axis, numbers[-1]))
                context.checkpoint(entities=len(circles))
        except (KeyError, ValueError, UnicodeError) as exc:
            raise _defect(
                "geometry.invalid_circle",
                "STEP circle placement, axis or radius could not be read safely.",
            ) from exc
        unique = {}
        for identifier, center, axis, radius in circles:
            key = tuple(round(item, 8) for item in (*center, *axis, radius))
            unique.setdefault(key, (identifier, center, axis, radius))
        expected_radius = nominal_diameter / 2.0
        candidates = [
            item
            for item in unique.values()
            if abs(item[3] - expected_radius) <= radius_tolerance
            and abs(item[2][2]) >= 1.0 - 1e-6
            and math.dist(item[1][:2], nominal) <= capture
        ]
        groups = {}
        for item in candidates:
            key = tuple(round(value, 6) for value in item[1][:2])
            groups.setdefault(key, []).append(item)
        if not groups:
            raise _defect(
                "geometry.required_feature_missing",
                f"Required seat '{match.group(1)}' was not found in its frozen datum region.",
            )
        if len(groups) != 1:
            raise _defect(
                "geometry.feature_ambiguous",
                f"Seat '{match.group(1)}' has multiple candidate circle centers.",
            )
        group = next(iter(groups.values()))
        center = group[0][1]
        if any(math.dist(item[1][:2], center[:2]) > 1e-6 for item in group):
            raise _defect(
                "geometry.feature_inconsistent",
                f"Seat '{match.group(1)}' circular edges do not share one axis.",
            )
        radii = {round(item[3], 8) for item in group}
        if len(radii) != 1:
            raise _defect(
                "geometry.feature_inconsistent",
                f"Seat '{match.group(1)}' circular edges do not share one diameter.",
            )
        observed = (
            center[0]
            if match.group(3) == "x"
            else center[1]
            if match.group(3) == "y"
            else 2.0 * group[0][3]
        )
        identity = canonical_digest(
            {"subject": snapshot.subject, "check": check, "reader": self.identity}
        )
        return Measurement(
            id="m-" + identity,
            subject_id=snapshot.subject.id,
            subject_sha256=snapshot.subject.sha256,
            selector=check.selector,
            value=observed,
            unit="mm",
            frame=check.frame,
            # Decimal STEP coordinates and radii are read directly.  Do not
            # invent physical measurement uncertainty: profile tolerances carry
            # the acceptance allowance, including exact inclusive boundaries.
            uncertainty=0.0,
            reader=self.identity,
            evidence_refs=(
                f"subject:{snapshot.subject.id}@{snapshot.subject.sha256}#step-circle/{match.group(1)}",
            ),
        )
