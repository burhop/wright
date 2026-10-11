"""Independent recomputation of tracking metrics from retained timeline rows."""

from __future__ import annotations

import csv
import io
import math

from core.process_validation import Measurement, ReaderIdentity, canonical_digest

from .base import ValidationIssue


_COLUMNS = (
    "time_s",
    "acquisition_time_s",
    "original_header_time_s",
    "raw_x_m",
    "raw_y_m",
    "aligned_x_m",
    "aligned_y_m",
    "planned_x_m",
    "planned_y_m",
    "dx_m",
    "dy_m",
    "lateral_error_m",
    "yaw_error_rad",
)


def _defect(code, message):
    return ValidationIssue(
        code, message, state="fail", category="output_defect", action="revise_output"
    )


def _timeline(snapshot, context):
    try:
        reader = csv.DictReader(
            io.StringIO(snapshot.content.decode("utf-8-sig")), strict=True
        )
        if tuple(reader.fieldnames or ()) != _COLUMNS:
            raise ValueError("columns")
        rows = []
        for count, raw in enumerate(reader, start=1):
            context.checkpoint(entities=count * len(_COLUMNS))
            if None in raw or any(
                value is None or value == "" for value in raw.values()
            ):
                raise ValueError("row")
            row = {name: float(raw[name]) for name in _COLUMNS}
            if any(not math.isfinite(value) for value in row.values()):
                raise ValueError("nonfinite")
            if rows and row["time_s"] <= rows[-1]["time_s"]:
                raise ValueError("time")
            if abs(row["dx_m"] - (row["aligned_x_m"] - row["planned_x_m"])) > 1e-9:
                raise ValueError("dx")
            if abs(row["dy_m"] - (row["aligned_y_m"] - row["planned_y_m"])) > 1e-9:
                raise ValueError("dy")
            if not -math.pi - 1e-12 <= row["yaw_error_rad"] <= math.pi + 1e-12:
                raise ValueError("yaw")
            rows.append(row)
    except (UnicodeError, csv.Error, ValueError) as exc:
        raise _defect(
            "tracking.invalid_timeline",
            "Tracking timeline must contain finite, ordered and internally consistent aligned rows.",
        ) from exc
    if not rows:
        raise _defect(
            "tracking.empty_timeline", "Tracking timeline has no retained samples."
        )
    return rows


class TrackingTimelineReader:
    identity = ReaderIdentity(
        id="tracking-timeline",
        version="1",
        config_digest=canonical_digest({"columns": _COLUMNS, "version": 1}),
        method="independent_measurement",
        tool_identity="wright bounded tracking timeline reader v1",
        formats=("csv",),
    )

    def measure(self, snapshot, check, context):
        rows = _timeline(snapshot, context)
        operation = check.parameters.get("operation")
        unit = "1"
        if operation == "retained_samples":
            value = len(rows)
        elif operation == "position_rmse":
            value = math.sqrt(
                math.fsum(row["dx_m"] ** 2 + row["dy_m"] ** 2 for row in rows)
                / len(rows)
            )
            unit = "m"
        elif operation == "lateral_rmse":
            value = math.sqrt(
                math.fsum(row["lateral_error_m"] ** 2 for row in rows) / len(rows)
            )
            unit = "m"
        elif operation == "start_time":
            value, unit = rows[0]["time_s"], "s"
        elif operation == "end_time":
            value, unit = rows[-1]["time_s"], "s"
        elif operation == "largest_gap":
            value = max(
                (
                    right["time_s"] - left["time_s"]
                    for left, right in zip(rows, rows[1:])
                ),
                default=0.0,
            )
            unit = "s"
        elif operation == "max_yaw_residual":
            value, unit = max(abs(row["yaw_error_rad"]) for row in rows), "rad"
        else:
            raise ValidationIssue(
                "profile.tracking_operation",
                "Tracking check requests an unsupported operation.",
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
                f"subject:{snapshot.subject.id}@{snapshot.subject.sha256}#timeline",
            ),
        )
