"""Independent bounded observations over actual thermal field tables."""

from __future__ import annotations

import csv
import io
import json
import math

from core.process_validation import Measurement, ReaderIdentity, canonical_digest

from .base import ValidationIssue


def _defect(code: str, message: str):
    return ValidationIssue(
        code,
        message,
        state="fail",
        category="output_defect",
        action="revise_output",
    )


def _number(value, name):
    if type(value) not in {int, float}:
        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise _defect("thermal.invalid_value", f"Thermal {name} must be numeric.") from exc
    value = float(value)
    if not math.isfinite(value):
        raise _defect("thermal.nonfinite", f"Thermal {name} must be finite.")
    return value


def _field(snapshot, context, parameters):
    try:
        text = snapshot.content.decode("utf-8-sig")
        rows = csv.DictReader(io.StringIO(text), strict=True)
        if rows.fieldnames != ["x_m", "y_m", "z_m", "temperature_c"]:
            raise ValueError("columns")
        values = []
        for count, row in enumerate(rows, start=1):
            context.checkpoint(entities=count * 4)
            if None in row or any(value is None for value in row.values()):
                raise ValueError("row")
            values.append(tuple(_number(row[name], name) for name in rows.fieldnames))
    except ValidationIssue:
        raise
    except (UnicodeError, csv.Error, ValueError) as exc:
        raise _defect(
            "thermal.invalid_field",
            "Thermal field must be a finite CSV with x_m,y_m,z_m,temperature_c columns.",
        ) from exc
    if len(values) < 2:
        raise _defect("thermal.field_empty", "Thermal field has insufficient points.")
    try:
        dimensions = tuple(float(item) / 1000.0 for item in parameters["dimensions_mm"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationIssue(
            "profile.thermal_dimensions",
            "Thermal field checks require three source-derived dimensions in mm.",
            category="source_conflict",
        ) from exc
    if len(dimensions) != 3 or any(not math.isfinite(item) or item <= 0 for item in dimensions):
        raise ValidationIssue(
            "profile.thermal_dimensions",
            "Thermal dimensions must be three finite positive values.",
            category="source_conflict",
        )
    axes = tuple(tuple(row[index] for row in values) for index in range(3))
    tolerance = 1e-9
    for axis, extent in zip(axes, dimensions, strict=True):
        if abs(min(axis)) > tolerance or abs(max(axis) - extent) > tolerance:
            raise _defect(
                "thermal.field_extent",
                "Thermal field coordinates do not match the frozen candidate geometry.",
            )
    temperatures = tuple(row[3] for row in values)
    return {
        "count": len(values),
        "minimum": min(temperatures),
        "maximum": max(temperatures),
        "dimensions_m": dimensions,
    }


class ThermalFieldReader:
    identity = ReaderIdentity(
        id="thermal-field",
        version="1",
        config_digest=canonical_digest(
            {
                "field": "finite x/y/z/temperature CSV",
                "checks": ["analytical-rise", "heat-balance", "refinement", "selection"],
                "version": 1,
            }
        ),
        method="independent_measurement",
        tool_identity="wright bounded thermal field reader v1",
        formats=("csv", "json"),
    )

    def measure(self, snapshot, check, context):
        operation = check.parameters.get("operation")
        related = {item.subject.role: item for item in context.related_snapshots}
        evidence = [
            f"subject:{snapshot.subject.id}@{snapshot.subject.sha256}#{check.selector}"
        ]
        if operation == "selection":
            observed = self._selection(snapshot, check, context, related, evidence)
            unit = None
        else:
            if snapshot.subject.format != "csv":
                raise _defect(
                    "thermal.field_format", "Thermal numerical checks require a field CSV."
                )
            field = _field(snapshot, context, check.parameters)
            unit = "1"
            if operation == "field_nodes":
                observed, unit = field["count"], "1"
            elif operation == "maximum_temperature":
                observed, unit = field["maximum"], "degC"
            elif operation == "analytical_relative_error":
                analytical = self._analytical_hot(check.parameters)
                cold = _number(check.parameters.get("cold_temperature_c"), "cold temperature")
                rise = analytical - cold
                if rise <= 0:
                    raise ValidationIssue(
                        "profile.thermal_analytical",
                        "Analytical temperature rise must be positive.",
                        category="source_conflict",
                    )
                observed = abs((field["maximum"] - cold) - rise) / rise
            elif operation == "heat_balance_relative":
                length, width, thickness = field["dimensions_m"]
                conductivity = _number(check.parameters.get("conductivity_w_mk"), "conductivity")
                heat = _number(check.parameters.get("heat_input_w"), "heat input")
                removed = conductivity * width * thickness * (
                    field["maximum"] - field["minimum"]
                ) / length
                observed = abs(removed - heat) / abs(heat)
            elif operation == "refinement_relative":
                role = check.parameters.get("coarse_role")
                coarse_snapshot = related.get(role)
                if coarse_snapshot is None or coarse_snapshot.subject.format != "csv":
                    raise ValidationIssue(
                        "subject.related_role_missing",
                        "Refinement check requires the bound coarse field.",
                    )
                coarse = _field(coarse_snapshot, context, check.parameters)
                if field["count"] <= coarse["count"]:
                    raise _defect(
                        "thermal.refinement_lineage",
                        "Refined field must contain more points than its bound coarse field.",
                    )
                cold = _number(check.parameters.get("cold_temperature_c"), "cold temperature")
                fine_rise = field["maximum"] - cold
                if fine_rise <= 0:
                    raise _defect(
                        "thermal.invalid_rise", "Refined field has no positive temperature rise."
                    )
                observed = abs(field["maximum"] - coarse["maximum"]) / fine_rise
                evidence.append(
                    f"subject:{coarse_snapshot.subject.id}@{coarse_snapshot.subject.sha256}#field"
                )
            else:
                raise ValidationIssue(
                    "profile.thermal_operation",
                    "Thermal check requests an unsupported operation.",
                    category="source_conflict",
                )
        identity = canonical_digest(
            {"subject": snapshot.subject, "check": check, "reader": self.identity, "related": tuple(item.subject for item in context.related_snapshots)}
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

    @staticmethod
    def _analytical_hot(parameters):
        length = _number(parameters.get("length_mm"), "length") / 1000.0
        width = _number(parameters.get("width_mm"), "width") / 1000.0
        thickness = _number(parameters.get("thickness_mm"), "thickness") / 1000.0
        conductivity = _number(parameters.get("conductivity_w_mk"), "conductivity")
        heat = _number(parameters.get("heat_input_w"), "heat input")
        cold = _number(parameters.get("cold_temperature_c"), "cold temperature")
        if min(length, width, thickness, conductivity, heat) <= 0:
            raise ValidationIssue(
                "profile.thermal_analytical",
                "Analytical parameters must be positive.",
                category="source_conflict",
            )
        return cold + heat * length / (conductivity * width * thickness)

    def _selection(self, snapshot, check, context, related, evidence):
        if snapshot.subject.format != "json":
            raise _defect("thermal.decision_format", "Sizing decision must be JSON.")
        try:
            decision = json.loads(snapshot.content)
            selected = decision["selected_case_id"]
        except (UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
            raise _defect(
                "thermal.invalid_decision", "Sizing decision does not name a selected case."
            ) from exc
        cases = check.parameters.get("cases")
        limit = _number(check.parameters.get("temperature_limit_c"), "temperature limit")
        if not isinstance(cases, list) or not cases:
            raise ValidationIssue(
                "profile.thermal_cases",
                "Selection check requires source-derived candidate roles and widths.",
                category="source_conflict",
            )
        observed = []
        for case in cases:
            if not isinstance(case, dict):
                raise ValidationIssue(
                    "profile.thermal_cases", "Thermal candidate definition is invalid.", category="source_conflict"
                )
            role = case.get("role")
            related_snapshot = related.get(role)
            if related_snapshot is None:
                raise ValidationIssue(
                    "subject.related_role_missing",
                    f"Selection requires the bound field role '{role}'.",
                )
            parameters = {**check.parameters, "dimensions_mm": case.get("dimensions_mm")}
            field = _field(related_snapshot, context, parameters)
            observed.append(
                (
                    str(case.get("id")),
                    _number(case.get("width_mm"), "candidate width"),
                    field["maximum"],
                )
            )
            evidence.append(
                f"subject:{related_snapshot.subject.id}@{related_snapshot.subject.sha256}#field"
            )
        passing = sorted((width, identifier) for identifier, width, maximum in observed if maximum <= limit)
        derived = passing[0][1] if passing else None
        if not isinstance(selected, str) or selected != derived:
            raise _defect(
                "thermal.selection_mismatch",
                "Sizing decision does not select the narrowest bound candidate meeting the source limit.",
            )
        return selected
