"""Bounded JSON, CSV and text observations; never trust producer verdict flags."""

from __future__ import annotations

import csv
import io
import json
import math
import re

from core.process_validation import (
    Measurement,
    ReaderIdentity,
    canonical_digest,
    canonical_json,
)

from .base import ValidationIssue


def _invalid(message, code="output.invalid_content"):
    return ValidationIssue(
        code, message, state="fail", category="output_defect", action="revise_output"
    )


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON member")
        result[key] = value
    return result


def _constant(_):
    raise ValueError("Nonfinite JSON number")


def _pointer(value, pointer):
    if not pointer:
        return value
    if not pointer.startswith("/"):
        raise ValidationIssue(
            "profile.selector",
            "The profile requires a JSON pointer selector.",
            category="source_conflict",
        )
    current = value
    for encoded in pointer[1:].split("/"):
        if re.search(r"~(?![01])", encoded):
            raise ValidationIssue(
                "profile.selector",
                "The profile selector contains an invalid escape.",
                category="source_conflict",
            )
        key = encoded.replace("~1", "/").replace("~0", "~")
        try:
            if isinstance(current, dict):
                current = current[key]
            elif isinstance(current, list) and re.fullmatch(r"0|[1-9][0-9]*", key):
                current = current[int(key)]
            else:
                raise KeyError(key)
        except (KeyError, IndexError, ValueError) as exc:
            raise _invalid(
                "The required field or table cell is absent from the output.",
                "output.required_value_missing",
            ) from exc
    return current


def _check_structure(value, context):
    stack, count = [(value, 0)], 0
    while stack:
        current, depth = stack.pop()
        count += 1
        context.checkpoint(entities=count)
        if depth > 64:
            raise ValidationIssue(
                "reader.depth_limit",
                "Structured output exceeds the supported nesting depth.",
                category="capability_unavailable",
                action="restore_capability",
            )
        if isinstance(current, float) and not math.isfinite(current):
            raise _invalid(
                "Output contains a nonfinite numeric value.", "output.nonfinite"
            )
        children = (
            current.values()
            if isinstance(current, dict)
            else current
            if isinstance(current, list)
            else ()
        )
        context.checkpoint(entities=count + len(stack) + len(children))
        stack.extend((child, depth + 1) for child in children)


class StructuredReader:
    identity = ReaderIdentity(
        id="structured",
        version="1",
        config_digest=canonical_digest({"parser": "json-csv-text", "version": 1}),
        method="structured_value",
        formats=("json", "csv", "text", "markdown", "html", "svg"),
    )

    def measure(self, snapshot, check, context):
        context.checkpoint()
        try:
            text = snapshot.content.decode("utf-8-sig")
        except UnicodeError as exc:
            raise _invalid(
                "Output is not valid UTF-8 text.", "output.encoding"
            ) from exc
        fmt = snapshot.subject.format
        if snapshot.subject.kind == "value" and fmt in {"text", "markdown", "html"}:
            # Inline text is hashed as canonical JSON, but its observation is
            # the original string, not the serialized quotes/escapes.
            text = snapshot.subject.value
            if not isinstance(text, str):
                raise _invalid(
                    "Inline text output must be a string.", "output.text_type"
                )
        if fmt == "json":
            try:
                value = json.loads(
                    text, object_pairs_hook=_pairs, parse_constant=_constant
                )
            except (ValueError, RecursionError) as exc:
                raise _invalid(
                    "Output must be unambiguous finite JSON.", "output.invalid_json"
                ) from exc
        elif fmt == "csv":
            try:
                reader = csv.DictReader(io.StringIO(text), strict=True)
                headers = reader.fieldnames
                if (
                    not headers
                    or any(not header for header in headers)
                    or len(set(headers)) != len(headers)
                ):
                    raise ValueError("Invalid columns")
                rows = []
                for row in reader:
                    context.checkpoint(entities=(len(rows) + 1) * (len(headers) + 1))
                    if None in row or any(item is None for item in row.values()):
                        raise ValueError("Inconsistent column count")
                    rows.append(row)
                value = {"columns": headers, "rows": rows, "row_count": len(rows)}
            except ValidationIssue:
                raise
            except (ValueError, csv.Error) as exc:
                raise _invalid(
                    "CSV output requires unique columns and consistent rows.",
                    "output.invalid_csv",
                ) from exc
        else:
            value = (
                {"text": text, "lines": text.splitlines()} if check.selector else text
            )
        _check_structure(value, context)
        observed = _pointer(value, check.selector)
        if not check.selector and check.constraint.operator in {"exists", "review"}:
            # Presence and review checks bind the complete artifact by its subject
            # digest. Keep the inline observation bounded so large reports and SVGs
            # remain reviewable without duplicating their content into the result.
            observed = {
                "present": True,
                "bytes": len(snapshot.content),
                "sha256": snapshot.subject.sha256,
            }
        if len(canonical_json(observed).encode("utf-8")) > 64 * 1024:
            raise ValidationIssue(
                "reader.observation_limit",
                "Select a smaller field or table region; inline observations are limited to 64 KiB.",
                category="capability_unavailable",
                action="restore_capability",
            )
        if fmt == "csv" and check.constraint.operator in {"within", "range"}:
            try:
                converted = float(observed)
                if math.isfinite(converted):
                    observed = converted
            except (TypeError, ValueError):
                pass  # Evaluator returns a typed output defect with the raw cell.
        unit, frame, uncertainty = check.unit, check.frame, 0.0
        if "unit_pointer" in check.parameters:
            unit = _pointer(value, check.parameters["unit_pointer"])
        if "frame_pointer" in check.parameters:
            frame = _pointer(value, check.parameters["frame_pointer"])
        if "uncertainty_pointer" in check.parameters:
            uncertainty = _pointer(value, check.parameters["uncertainty_pointer"])
            if (
                type(uncertainty) not in {int, float}
                or not math.isfinite(uncertainty)
                or uncertainty < 0
            ):
                raise _invalid(
                    "Measurement uncertainty must be a finite nonnegative number.",
                    "output.uncertainty",
                )
        if (unit is not None and not isinstance(unit, str)) or (
            frame is not None and not isinstance(frame, str)
        ):
            raise _invalid(
                "Unit and frame declarations must be strings.", "output.unit_frame"
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
            unit=unit,
            frame=frame,
            uncertainty=uncertainty,
            reader=self.identity,
            evidence_refs=(
                f"subject:{snapshot.subject.id}@{snapshot.subject.sha256}#{check.selector}",
            ),
        )
