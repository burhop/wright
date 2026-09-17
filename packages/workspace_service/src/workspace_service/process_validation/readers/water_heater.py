"""Independent validation of water-heater simulation trajectories."""

from __future__ import annotations

import csv
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


class WaterHeaterTimelineReader:
    identity = ReaderIdentity(
        id="water-heater-timeline",
        version="1",
        config_digest=canonical_digest(
            {"schema": _COLUMNS, "crossing": "linear", "version": 1}
        ),
        method="independent_measurement",
        tool_identity="wright bounded water-heater trajectory reader v1",
        formats=("csv",),
    )

    def measure(self, snapshot, check, context):
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
