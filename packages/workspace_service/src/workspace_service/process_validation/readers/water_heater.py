"""Independent validation of water-heater simulation trajectories."""

from __future__ import annotations

import csv
import json
import io
import math
import re

from core.process_validation import Measurement, ReaderIdentity, canonical_digest

from .base import ValidationIssue


_COLUMNS = (
    "request_id",
    "time_s",
    "temperature_C",
    "electrical_power_W",
    "electrical_energy_J",
    "thermal_power_W",
    "thermal_energy_J",
)


def _defect(code, message):
    return ValidationIssue(
        code, message, state="fail", category="output_defect", action="revise_output"
    )


def _trajectories(snapshot, context):
    try:
        reader = csv.DictReader(
            io.StringIO(snapshot.content.decode("utf-8-sig")), strict=True
        )
        if tuple(reader.fieldnames or ()) != _COLUMNS:
            raise ValueError("columns")
        groups = {}
        for count, raw in enumerate(reader, start=1):
            context.checkpoint(entities=count * len(_COLUMNS))
            if None in raw or any(
                value is None or value == "" for value in raw.values()
            ):
                raise ValueError("row")
            row = {name: float(raw[name]) for name in _COLUMNS[1:]}
            if any(not math.isfinite(value) for value in row.values()):
                raise ValueError("nonfinite")
            groups.setdefault(raw["request_id"], []).append(row)
    except (UnicodeError, csv.Error, ValueError) as exc:
        raise _defect(
            "water.invalid_timeline",
            "Water-heater timeline must contain finite rows in the frozen schema.",
        ) from exc
    if not groups:
        raise _defect("water.empty_timeline", "Water-heater timeline has no runs.")
    for rows in groups.values():
        if rows[0]["time_s"] != 0 or any(
            right["time_s"] < left["time_s"] for left, right in zip(rows, rows[1:])
        ):
            raise _defect(
                "water.invalid_time",
                "Every trajectory must start at zero and increase in time.",
            )
    return groups


def _crossing(rows, target):
    for left, right in zip(rows, rows[1:]):
        if left["temperature_C"] < target <= right["temperature_C"]:
            fraction = (target - left["temperature_C"]) / (
                right["temperature_C"] - left["temperature_C"]
            )
            return left["time_s"] + fraction * (right["time_s"] - left["time_s"])
    return 0.0 if rows[0]["temperature_C"] >= target else None


def _finite_number(value, *, positive=False):
    if isinstance(value, bool):
        raise ValueError("Boolean is not a measurement")
    number = float(value)
    if not math.isfinite(number) or (positive and number <= 0):
        raise ValueError("Measurement must be finite and positive")
    return number


def _same_number(actual, expected):
    # Serialization/solver roundoff only; engineering limits are compared exactly.
    return math.isclose(_finite_number(actual), expected, rel_tol=1e-7, abs_tol=1e-5)


def _package_numbers(document, measurements, field, parameters, context):
    """Recompute the declared 1-D screen, not a substitute for native CAD review."""
    try:
        fixed = parameters["fixed_requirements"]
        power = _finite_number(parameters["selected_power_w"], positive=True)
        efficiency = _finite_number(parameters["heater_efficiency"], positive=True)
        target = _finite_number(parameters["target_temperature_c"])
        ambient = _finite_number(parameters["ambient_temperature_c"])
        carrier_k = _finite_number(fixed["carrier_thermal_conductivity_w_mk"], positive=True)
        insulation_k = _finite_number(fixed["insulation_thermal_conductivity_w_mk"], positive=True)
        film = _finite_number(fixed["external_film_coefficient_w_m2k"], positive=True)
        contact_max = _finite_number(fixed["maximum_heater_contact_diameter_mm"], positive=True)
        insulation_min, insulation_max = (
            _finite_number(v, positive=True) for v in fixed["insulation_thickness_range_mm"]
        )
        envelope_max = [_finite_number(v, positive=True) for v in fixed["maximum_envelope_mm"]]
        mass_max = _finite_number(fixed["maximum_dry_package_mass_kg"], positive=True)
        carrier_max = _finite_number(fixed["maximum_carrier_temperature_c"])
        shell_key = ("maximum_accessible_shell_temperature_c" if "maximum_accessible_shell_temperature_c" in fixed
                     else "maximum_other_accessible_shell_temperature_c")
        shell_max = _finite_number(fixed[shell_key])
        if len(envelope_max) != 3 or insulation_min > insulation_max or efficiency > 1 or target <= ambient:
            raise ValueError("Invalid fixed screening parameters")
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationIssue("profile.water_package_parameters",
            "Package checks require the approved fixed numeric limits and thermal conditions.",
            category="source_conflict") from exc

    diameter = _finite_number(measurements["heater_contact_diameter_mm"], positive=True)
    carrier_thickness = _finite_number(measurements["carrier_thickness_mm"], positive=True) / 1000
    insulation_mm = _finite_number(measurements["insulation_thickness_mm"], positive=True)
    insulation_thickness = insulation_mm / 1000
    mass = _finite_number(measurements["dry_mass_kg"], positive=True)
    envelope = [_finite_number(v, positive=True) for v in measurements["envelope_mm"]]
    if (diameter > contact_max or not insulation_min <= insulation_mm <= insulation_max
            or len(envelope) != 3 or any(a > b for a, b in zip(envelope, envelope_max)) or mass > mass_max):
        raise _defect("water.package_numeric_limit", "Package measurements exceed an approved geometry or mass limit.")
    heat = power * efficiency
    if not _same_number(document["heater_efficiency"], efficiency) or not _same_number(document["thermal_power_w"], heat):
        raise _defect("water.package_heat_input", "Package heat input differs from the selected power and frozen efficiency.")
    area = math.pi * (diameter / 1000)**2 / 4
    carrier_peak = target + heat / area * carrier_thickness / carrier_k
    shell_surface = (insulation_k / insulation_thickness * target + film * ambient) / (insulation_k / insulation_thickness + film)
    models = {"carrier": [], "insulation": []}
    reader = csv.DictReader(io.StringIO(field.content.decode("utf-8-sig")), strict=True)
    if tuple(reader.fieldnames or ()) != ("model", "x_m", "temperature_c"):
        raise ValueError("Thermal field must use the frozen SI column schema")
    for count, row in enumerate(reader, start=1):
        context.checkpoint(entities=count * 3)
        if None in row or row["model"] not in models:
            raise ValueError("Unexpected thermal field model or columns")
        models[row["model"]].append((_finite_number(row["x_m"]), _finite_number(row["temperature_c"])))
    for name, thickness, end_temperature in (
        ("carrier", carrier_thickness, carrier_peak),
        ("insulation", insulation_thickness, shell_surface),
    ):
        rows = models[name]
        if (len(rows) < 2 or abs(rows[0][0]) > 1e-12 or not math.isclose(rows[-1][0], thickness, rel_tol=1e-8, abs_tol=1e-12)
                or any(right[0] <= left[0] for left, right in zip(rows, rows[1:]))):
            raise _defect("water.package_field_domain", "Both thermal fields must span their exact measured thicknesses.")
        if any(not _same_number(t, target + x / thickness * (end_temperature - target)) for x, t in rows):
            raise _defect("water.package_field_physics", "The field differs from the independently recomputed declared one-dimensional thermal case.")
    actual_carrier = max(t for _, t in models["carrier"])
    actual_shell = models["insulation"][-1][1]
    if actual_carrier > carrier_max or actual_shell > shell_max:
        raise _defect("water.package_temperature_limit", "The actual field exceeds an approved temperature limit.")
    checks = document["checks"]
    for name, observed_key, observed, limit_key, limit in (
        ("carrier_temperature", "observed_c", actual_carrier, "limit_c", carrier_max),
        ("accessible_shell_temperature", "observed_c", actual_shell, "limit_c", shell_max),
        ("dry_mass", "observed_kg", mass, "limit_kg", mass_max),
    ):
        item = checks[name]
        if not _same_number(item[observed_key], observed) or _finite_number(item[limit_key]) != limit:
            raise _defect("water.package_report_numbers", "Reported observations or limits differ from the bound field, measurements or fixed requirements.")
    item = checks["envelope"]
    reported = [_finite_number(v) for v in item["observed_mm"]]
    limits = [_finite_number(v) for v in item["limit_mm"]]
    if len(reported) != 3 or limits != envelope_max or not all(_same_number(a, b) for a, b in zip(reported, envelope)):
        raise _defect("water.package_report_numbers", "Reported envelope values differ from the bound measurements or fixed limits.")


class WaterHeaterTimelineReader:
    identity = ReaderIdentity(
        id="water-heater-timeline",
        version="1",
        config_digest=canonical_digest(
            {"schema": _COLUMNS, "crossing": "linear", "package": "hash-bound-numeric-1d-v2", "version": 3}
        ),
        method="independent_measurement",
        tool_identity="wright bounded water-heater trajectory reader v1",
        formats=("csv", "json"),
    )

    def measure(self, snapshot, check, context):
        if check.parameters.get("operation") == "package_verification":
            return self._measure_package(snapshot, check, context)
        groups = _trajectories(snapshot, context)
        parameters = check.parameters
        try:
            powers = [float(value) for value in parameters["powers_w"]]
            losses = [str(value) for value in parameters["loss_labels"]]
            efficiency = float(parameters["efficiency"])
            initial = float(parameters["initial_temperature_c"])
            target = float(parameters["target_temperature_c"])
            limit = float(parameters["time_limit_s"])
            horizon = float(parameters["horizon_s"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValidationIssue(
                "profile.water_parameters",
                "Water-heater checks require frozen numeric parameters.",
                category="source_conflict",
            ) from exc
        baselines = {
            name: rows for name, rows in groups.items() if name.endswith("-baseline")
        }
        expected = {(power, loss) for power in powers for loss in losses}
        observed = {}
        for name, rows in baselines.items():
            match = re.search(r"-p([0-9]+)-(low|nominal|high)-baseline$", name)
            if not match:
                raise _defect(
                    "water.run_identity",
                    "Baseline run identity does not encode its candidate and loss case.",
                )
            key = (float(match.group(1)), match.group(2))
            if key in observed:
                raise _defect(
                    "water.duplicate_run", "Candidate/loss baseline is duplicated."
                )
            observed[key] = rows
        if set(observed) != expected:
            raise _defect(
                "water.candidate_grid",
                "Timeline does not contain exactly the frozen candidate/loss grid.",
            )
        crossings = {}
        for key, rows in observed.items():
            power = key[0]
            if abs(rows[0]["temperature_C"] - initial) > 1e-9:
                raise _defect(
                    "water.initial_condition",
                    "A baseline run changed the frozen initial temperature.",
                )
            if rows[-1]["time_s"] > horizon + 1e-9:
                raise _defect(
                    "water.horizon", "A baseline run exceeds the frozen horizon."
                )
            crossing = _crossing(rows, target)
            heating_rows = [
                row for row in rows if crossing is None or row["time_s"] <= crossing
            ]
            if any(
                abs(row["electrical_power_W"] - power) > 1e-9 for row in heating_rows
            ):
                raise _defect(
                    "water.power",
                    "A baseline run changed its declared electrical power.",
                )
            if any(
                abs(row["thermal_power_W"] - efficiency * power) > 1e-6
                for row in heating_rows
            ):
                raise _defect(
                    "water.efficiency",
                    "Thermal power does not match the frozen heater efficiency.",
                )
            integer_times = {
                row["time_s"] for row in rows if row["time_s"].is_integer()
            }
            if integer_times != {float(value) for value in range(int(horizon) + 1)}:
                raise _defect(
                    "water.output_grid",
                    "Baseline output does not retain the complete one-second grid.",
                )
            if crossing is None and abs(rows[-1]["time_s"] - horizon) > 1e-6:
                raise _defect(
                    "water.unreached_horizon",
                    "An unreached candidate stopped before the frozen horizon.",
                )
            crossings[key] = crossing
        feasible = [
            power
            for power in powers
            if all(
                crossings[(power, loss)] is not None
                and crossings[(power, loss)] <= limit + 1e-9
                for loss in losses
            )
        ]
        selected = min(feasible) if feasible else None
        operation = parameters.get("operation")
        value, unit = (
            (len(observed), "1")
            if operation == "grid_count"
            else (selected, "W")
            if operation == "selection"
            else (None, None)
        )
        if value is None and operation not in {"selection"}:
            raise ValidationIssue(
                "profile.water_operation",
                "Water-heater check requests an unsupported operation.",
                category="source_conflict",
            )
        identity = canonical_digest(
            {"subject": snapshot.subject, "check": check, "reader": self.identity}
        )
        return Measurement(
            id="m-" + identity,
            subject_id=snapshot.subject.id,
            subject_sha256=snapshot.subject.sha256,
            selector=check.selector,
            value=value,
            unit=unit,
            frame=check.frame,
            uncertainty=0.0,
            reader=self.identity,
            evidence_refs=(
                f"subject:{snapshot.subject.id}@{snapshot.subject.sha256}#trajectories",
            ),
        )

    def _measure_package(self, snapshot, check, context):
        if snapshot.subject.format != "json":
            raise _defect(
                "water.package_format", "Thermal-package verification must be JSON."
            )
        related = {item.subject.role: item for item in context.related_snapshots}
        try:
            document = json.loads(snapshot.content)
            if document.get("schema") != "wright-water-thermal-package-verification-v1":
                raise ValueError("schema")
            geometry = related[check.parameters["geometry_role"]]
            field = related[check.parameters["field_role"]]
            comparison = related[check.parameters["comparison_role"]]
            measurements = related[check.parameters["measurements_role"]]
            measured = json.loads(measurements.content)
            if not isinstance(document, dict) or not isinstance(measured, dict):
                raise ValueError("Package evidence must be structured objects")
            if document["geometry"]["sha256"] != geometry.subject.sha256:
                raise _defect(
                    "water.package_geometry_identity",
                    "Package verification does not bind the current CAD STEP.",
                )
            if document["geometry"]["measurements_sha256"] != measurements.subject.sha256:
                raise _defect(
                    "water.package_measurement_identity",
                    "Package verification does not bind the current CAD measurements.",
                )
            if measured.get("step_sha256") != geometry.subject.sha256:
                raise _defect("water.package_measurement_geometry_identity",
                    "CAD measurements do not identify the current package STEP.")
            if document["field"]["sha256"] != field.subject.sha256:
                raise _defect(
                    "water.package_field_identity",
                    "Package verification does not bind the current thermal field.",
                )
            if document["modelica_selection_sha256"] != comparison.subject.sha256:
                raise _defect(
                    "water.package_selection_identity",
                    "Package verification does not bind the current Modelica selection.",
                )
            if float(document["selected_electrical_power_w"]) != float(
                check.parameters["selected_power_w"]
            ):
                raise _defect(
                    "water.package_selected_power",
                    "Package screen did not use the independently selected power.",
                )
            checks = document["checks"]
            required = {
                "carrier_temperature",
                "accessible_shell_temperature",
                "envelope",
                "dry_mass",
            }
            if set(checks) != required or any(
                item.get("pass") is not True for item in checks.values()
            ):
                raise _defect(
                    "water.package_requirement_failure",
                    "The final package does not pass every approved digital screen.",
                )
            if document.get("status") != "pass":
                raise _defect(
                    "water.package_status", "Thermal-package status is not pass."
                )
            _package_numbers(document, measured, field, check.parameters, context)
        except ValidationIssue:
            raise
        except (KeyError, TypeError, ValueError, AttributeError, csv.Error, UnicodeError, ArithmeticError) as exc:
            raise _defect(
                "water.invalid_package_verification",
                "Thermal-package verification is incomplete or malformed.",
            ) from exc
        evidence = [f"subject:{snapshot.subject.id}@{snapshot.subject.sha256}#package"]
        evidence.extend(
            f"subject:{item.subject.id}@{item.subject.sha256}#bound"
            for item in (geometry, measurements, field, comparison)
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
            value=True,
            unit=None,
            frame=check.frame,
            uncertainty=0.0,
            reader=self.identity,
            evidence_refs=tuple(evidence),
        )
