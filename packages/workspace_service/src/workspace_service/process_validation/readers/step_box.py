"""Bounded STEP solid-envelope measurements from referenced vertices."""

from __future__ import annotations

import re

from core.process_validation import Measurement, ReaderIdentity, canonical_digest

from .base import ValidationIssue
from .geometry import _REFERENCE, _entities, _vector


_SELECTOR = re.compile(r"^box/(x|y|z)_span_mm$")


def _defect(code: str, message: str):
    return ValidationIssue(
        code, message, state="fail", category="output_defect", action="revise_output"
    )


class StepBoundingBoxReader:
    identity = ReaderIdentity(
        id="step-bounding-box",
        version="1",
        config_digest=canonical_digest(
            {
                "format": "ISO-10303-21",
                "evidence": "VERTEX_POINT coordinates",
                "version": 1,
            }
        ),
        method="native_inspection",
        tool_identity="wright bounded STEP vertex-envelope reader v1",
        formats=("step", "stp"),
    )

    def measure(self, snapshot, check, context):
        match = _SELECTOR.fullmatch(check.selector)
        if not match:
            raise ValidationIssue(
                "profile.step_box_selector",
                "STEP envelope selector must name an x, y or z span in millimetres.",
                category="source_conflict",
            )
        # AP214 files may declare a different length unit. This reader only makes
        # millimetre claims when the exchange context declares millimetres.
        compact = re.sub(rb"\s+", b"", snapshot.content.upper())
        if b"SI_UNIT(.MILLI.,.METRE.)" not in compact:
            raise _defect(
                "geometry.step_unit",
                "STEP geometry must declare millimetres for an envelope check.",
            )
        entities = _entities(snapshot.content, context)
        points = []
        try:
            for name, arguments in entities.values():
                if name != "VERTEX_POINT":
                    continue
                refs = [int(item) for item in _REFERENCE.findall(arguments)]
                if len(refs) != 1:
                    raise ValueError("vertex reference")
                point = _vector(entities[refs[0]], "CARTESIAN_POINT")
                points.append(point)
                context.checkpoint(entities=len(points))
        except (KeyError, ValueError) as exc:
            raise _defect(
                "geometry.invalid_vertex",
                "STEP solid vertices could not be read safely.",
            ) from exc
        if len(set(points)) < 4:
            raise _defect(
                "geometry.insufficient_vertices",
                "STEP geometry does not contain a measurable solid vertex envelope.",
            )
        axis = {"x": 0, "y": 1, "z": 2}[match.group(1)]
        observed = max(point[axis] for point in points) - min(
            point[axis] for point in points
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
            uncertainty=0.0,
            reader=self.identity,
            evidence_refs=(
                f"subject:{snapshot.subject.id}@{snapshot.subject.sha256}#solid-vertex-envelope",
            ),
        )
