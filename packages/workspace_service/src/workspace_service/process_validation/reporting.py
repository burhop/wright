"""Deterministic report projections from one immutable assessment."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal, localcontext
from html import escape as html_escape
import io
import json
import math

from core.process_validation import (
    Assessment,
    AssessmentCurrentness,
    Measurement,
    ReportScope,
    RequirementTraceRow,
    ValidationReport,
    canonical_digest,
)


@dataclass(frozen=True)
class ReportExport:
    format: str
    media_type: str
    filename: str
    content: bytes


def build_report(
    assessment: Assessment, currentness: AssessmentCurrentness
) -> ValidationReport:
    requirements = {item.id: item for item in assessment.profile.baseline.requirements}
    results = {item.check_id: item for item in assessment.checks}
    measurements = {item.id: item for item in assessment.measurements}
    findings = {item.id: item for item in assessment.findings}
    subjects = {item.role: item for item in assessment.request.subjects}
    rows: list[RequirementTraceRow] = []
    for definition in assessment.profile.checks:
        result = results.get(definition.id)
        state = result.state if result else "blocked"
        measurement_items = (
            tuple(measurements[item] for item in result.measurement_ids)
            if result
            else ()
        )
        finding_items = (
            tuple(findings[item] for item in result.finding_ids) if result else ()
        )
        subject = subjects.get(definition.subject_role)
        evidence_refs = tuple(
            dict.fromkeys(
                [*(result.evidence_refs if result else ())]
                + [ref for item in measurement_items for ref in item.evidence_refs]
                + [ref for item in finding_items for ref in item.evidence_refs]
            )
        )
        action = finding_items[0].correction.action if finding_items else None
        for requirement_id in definition.requirement_ids:
            requirement = requirements[requirement_id]
            rows.append(
                RequirementTraceRow(
                    requirement_id=requirement.id,
                    requirement_text=requirement.text,
                    requirement_scope=requirement.scope,
                    mandatory=requirement.mandatory,
                    review_required=requirement.review_required,
                    source_refs=requirement.sources,
                    check_id=definition.id,
                    check_version=definition.version,
                    check_state=state,
                    reader=definition.reader,
                    evidence_method=definition.evidence_method,
                    selector=definition.selector,
                    expected=definition.constraint,
                    expected_unit=definition.unit,
                    expected_frame=definition.frame,
                    observed=tuple(item.value for item in measurement_items),
                    observed_units=tuple(item.unit for item in measurement_items),
                    observed_frames=tuple(item.frame for item in measurement_items),
                    evidence_refs=evidence_refs,
                    subject_id=subject.id if subject else None,
                    subject_sha256=subject.sha256 if subject else None,
                    producer=subject.producer if subject else None,
                    finding_ids=tuple(item.id for item in finding_items),
                    action=action,
                )
            )
    readers = tuple(
        {
            (
                item.reader.id,
                item.reader.version,
                item.reader.config_digest,
                item.reader.method,
                item.reader.tool_identity,
                item.reader.formats,
            ): item.reader
            for item in assessment.measurements
        }.values()
    )
    return ValidationReport(
        assessment_digest=canonical_digest(assessment),
        currentness=currentness,
        scope=ReportScope(
            requirement_ids=tuple(requirements),
            excluded_scope=assessment.profile.excluded_scope,
            limitations=assessment.profile.limitations,
            physical_validation=assessment.summary.physical_validation,
        ),
        reader_identities=readers,
        traceability=tuple(rows),
        assessment=assessment,
    )


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _markdown(value: object) -> str:
    text = _text(value)
    for character in ("\\", "`", "*", "_", "{", "}", "[", "]", "#", "|", "~"):
        text = text.replace(character, "\\" + character)
    # Escape HTML last so Markdown escaping cannot break generated entities.
    text = html_escape(text, quote=True)
    return text.replace("\r", " ").replace("\n", "<br>")


_UNCERTAINTY_NOTE = (
    "Allowances are copied from recorded measurements. Zero can be a default; "
    "it does not prove zero measurement error or physical accuracy. "
    "Uncertainty applies to numeric observations only."
)


def _measurements_by_check(
    assessment: Assessment,
) -> dict[str, tuple[Measurement, ...]]:
    measurements = {item.id: item for item in assessment.measurements}
    return {
        check.check_id: tuple(measurements[key] for key in check.measurement_ids)
        for check in assessment.checks
    }


def _uncertainty_text(measurements: tuple[Measurement, ...]) -> str:
    def label(item: Measurement) -> str:
        if type(item.value) not in {int, float}:
            return "Not applicable (non-numeric observation)"
        return (
            _text(item.uncertainty)
            + (f" {item.unit}" if item.unit else " (unit not recorded)")
            + (f" (frame: {item.frame})" if item.frame else "")
        )

    return "; ".join(label(item) for item in measurements) or "No measurement recorded"


def render_markdown(report: ValidationReport) -> str:
    assessment = report.assessment
    measurements = _measurements_by_check(assessment)
    verdict = (
        "PASS"
        if report.currentness.is_current and assessment.summary.release_eligible
        else "HOLD"
    )
    lines = [
        "# Process validation report",
        "",
        f"**Verdict:** {verdict}",
        f"**Assessment:** `{_markdown(assessment.id)}`",
        f"**Assessment digest:** `{report.assessment_digest}`",
        f"**Profile:** `{_markdown(assessment.profile.id)}@{_markdown(assessment.profile.version)}`",
        f"**Current as of:** `{_markdown(report.currentness.as_of)}` — {'yes' if report.currentness.is_current else 'no'}",
    ]
    if report.currentness.stale_reason:
        lines.append(f"**Stale reason:** `{report.currentness.stale_reason}`")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            "| Content verified | Requirements compliant | Complete | Release eligible |",
            "|---|---|---|---|",
            "| {} | {} | {} | {} |".format(
                _text(assessment.summary.content_verified),
                _text(assessment.summary.requirements_compliant),
                _text(assessment.summary.evaluation_complete),
                _text(
                    report.currentness.is_current
                    and assessment.summary.release_eligible
                ),
            ),
            "",
            "## Requirements traceability",
            "",
            _UNCERTAINTY_NOTE,
            "",
            "| Requirement | Check | Expected | Observed | Status | Evidence | Action | Review required | Uncertainty allowance |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for row in report.traceability:
        expected = row.expected.model_dump(mode="json", exclude_none=True)
        observed = [
            {"value": value, "unit": unit, "frame": frame}
            for value, unit, frame in zip(
                row.observed, row.observed_units, row.observed_frames, strict=True
            )
        ]
        lines.append(
            "| {} — {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
                _markdown(row.requirement_id),
                _markdown(row.requirement_text),
                _markdown(row.check_id),
                _markdown(expected),
                _markdown(observed),
                _markdown(row.check_state),
                _markdown(list(row.evidence_refs)),
                _markdown(row.action),
                "Yes" if row.review_required else "No",
                _markdown(_uncertainty_text(measurements.get(row.check_id, ()))),
            )
        )
    if report.scope.excluded_scope or report.scope.limitations:
        lines.extend(["", "## Scope and limitations", ""])
        for item in (*report.scope.excluded_scope, *report.scope.limitations):
            lines.append(f"- {_markdown(item)}")
    return "\n".join(lines) + "\n"


def _csv_safe(value: object) -> str:
    text = _text(value).replace("\x00", "")
    formula = text.lstrip(" \t\r\n")
    if formula and formula[0] in ("=", "+", "-", "@"):
        return "'" + text
    return text


def _readable_measurement(
    item: object, row: RequirementTraceRow, unit: str | None, frame: str | None
) -> str:
    """Compact passed numeric observations only; never determine check state."""
    exact = "Yes" if item is True else "No" if item is False else _text(item)
    rule = row.expected
    if (
        type(item) is not float
        or not math.isfinite(item)
        or row.check_state != "pass"
        or rule.operator not in {"within", "range"}
        or unit != row.expected_unit
        or frame != row.expected_frame
    ):
        return exact
    compact = format(item, ".6g")
    original, displayed = Decimal(str(item)), Decimal(compact)
    if displayed == original:
        return exact
    # Keep the recorded side of each limit visible. This guard controls display,
    # not compliance; the stored check result remains the sole verdict.
    with localcontext() as context:
        context.prec = 700  # Covers sums/differences across finite float exponents.
        if rule.operator == "within":
            target, tolerance = Decimal(str(rule.target)), Decimal(str(rule.tolerance))
            limits = (target - tolerance, target + tolerance)
        else:
            limits = tuple(
                Decimal(str(limit))
                for limit in (rule.minimum, rule.maximum)
                if limit is not None
            )
        low, high = sorted((original, displayed))
        if any(low <= limit <= high for limit in limits):
            return exact
    return f"≈ {compact}"


def render_readable_markdown(report: ValidationReport) -> str:
    """Compact working-view presentation of the same report; no new evaluation."""
    assessment = report.assessment
    eligible = report.currentness.is_current and assessment.summary.release_eligible
    subjects = {item.id: item for item in assessment.request.subjects}
    findings = {item.id: item for item in assessment.findings}
    measurements = _measurements_by_check(assessment)

    def value(item):
        return "Yes" if item is True else "No" if item is False else _text(item)

    def quantity(item, unit=None, frame=None):
        return (
            value(item)
            + (f" {unit}" if unit else "")
            + (f" (frame: {frame})" if frame else "")
        )

    def expected(row):
        rule = row.expected
        if rule.operator == "within":
            text = f"{rule.target} ± {rule.tolerance}"
        elif rule.operator == "range":
            bounds = []
            if rule.minimum is not None:
                bounds.append(f"{'≥' if rule.inclusive else '>'} {rule.minimum}")
            if rule.maximum is not None:
                bounds.append(f"{'≤' if rule.inclusive else '<'} {rule.maximum}")
            text = " and ".join(bounds)
        elif rule.operator == "review":
            text = "Authenticated review of this exact result"
        elif rule.operator == "exists":
            text = "Evidence exists"
        elif rule.operator == "type":
            text = f"Value type: {rule.expected}"
        else:
            text = f"Equals {value(rule.expected)}"
        return quantity(text, row.expected_unit, row.expected_frame)

    def observed_values(row):
        return (
            "; ".join(
                quantity(_readable_measurement(item, row, unit, frame), unit, frame)
                for item, unit, frame in zip(
                    row.observed, row.observed_units, row.observed_frames, strict=True
                )
            )
            or "No measurement recorded"
        )

    def correction_text(finding):
        if (
            finding.code == "requirement.out_of_bounds"
            and finding.correction.action == "revise_output"
        ):
            return "Revise the assessed output and rerun the required checks."
        return finding.correction.target

    lines = [
        "# Engineering assessment",
        "",
        f"**Recorded outcome: {'PASS' if eligible else 'HOLD'}**",
        "",
        "Release is eligible under these recorded checks."
        if eligible
        else "Release remains held. Inspect the recorded findings and required review below.",
        "",
        f"- **Evidence current:** {'Yes' if report.currentness.is_current else 'No'}",
        f"- **Checked as of:** {_markdown(report.currentness.as_of)}",
        f"- **Physical validation:** {_markdown(report.scope.physical_validation.replace('_', ' '))}",
        "",
        "## Check summary",
        "",
    ]
    if report.currentness.stale_reason:
        lines.extend(
            [
                f"**Currentness limitation:** {_markdown(report.currentness.stale_reason)}",
                "",
            ]
        )
    for state, count in assessment.summary.counts.items():
        if count:
            lines.append(f"- {_markdown(state.replace('_', ' '))}: {count}")
    pending = [row for row in report.traceability if row.check_state != "pass"]
    if pending:
        lines.extend(["", "## Findings requiring attention", ""])
        for finding in assessment.findings:
            row = next(
                (
                    item
                    for item in report.traceability
                    if finding.id in item.finding_ids
                ),
                None,
            )
            lines.append(f"- **{_markdown(finding.summary.rstrip('.:'))}**")
            if finding.code == "requirement.out_of_bounds" and row is not None:
                lines.append(f"  - **Required:** {_markdown(expected(row))}")
                lines.append(f"  - **Observed:** {_markdown(observed_values(row))}")
                lines.append(
                    f"  - **Recorded uncertainty allowance:** {_markdown(_uncertainty_text(measurements.get(row.check_id, ())))}"
                )
            lines.append(f"  - **Next action:** {_markdown(correction_text(finding))}")
            lines.append(
                f"  - **Requirements:** {_markdown(', '.join(finding.requirement_ids))}"
            )
    lines.extend(
        [
            "",
            "## Requirements and observations",
            "",
            "A check may provide evidence for several requirements.",
            "",
            "Observations marked ≈ use six significant digits for display. Exact values remain in the recorded assessment. "
            "Failed or unresolved checks, and values that would round onto or across a limit, are shown in full. "
            "Required bounds, tolerances and recorded outcomes are unchanged.",
            "",
            _UNCERTAINTY_NOTE,
            "",
        ]
    )
    for row in (
        *pending,
        *(row for row in report.traceability if row.check_state == "pass"),
    ):
        observed = observed_values(row)
        lines.extend(
            [
                f"### {_markdown(row.requirement_id)} · {_markdown(row.check_state.upper())}",
                "",
                _markdown(row.requirement_text),
                "",
                f"- **Required:** {_markdown(expected(row))}",
                f"- **Observed:** {_markdown(observed)}",
                f"- **Recorded uncertainty allowance:** {_markdown(_uncertainty_text(measurements.get(row.check_id, ())))}",
                f"- **Method:** {_markdown(row.evidence_method.replace('_', ' '))}",
                f"- **Mandatory:** {'Yes' if row.mandatory else 'No'}",
                f"- **Review required by requirement:** {'Yes' if row.review_required else 'No'}",
                f"- **Check:** {_markdown(row.check_id)}",
            ]
        )
        subject = subjects.get(row.subject_id)
        if subject:
            label = (
                subject.locator.replace("\\", "/").rsplit("/", 1)[-1]
                if subject.locator
                else subject.role
            )
            lines.append(f"- **Assessed output:** {_markdown(label)}")
        if row.action:
            targets = [
                correction_text(findings[key])
                for key in row.finding_ids
                if key in findings
            ]
            lines.append(
                f"- **Next action:** {_markdown('; '.join(dict.fromkeys(targets)) or row.action.replace('_', ' '))}"
            )
        if row.source_refs:
            lines.append(
                "- **Requirement source:** "
                + "; ".join(
                    _markdown(
                        ref.artifact_ref.replace("\\", "/").rsplit("/", 1)[-1]
                        + (f" · {ref.locator}" if ref.locator else "")
                    )
                    for ref in row.source_refs
                )
            )
        lines.append("")
    lines.extend(["## Scope and limitations", ""])
    for item in (*report.scope.excluded_scope, *report.scope.limitations):
        lines.append(f"- {_markdown(item)}")
    lines.extend(
        [
            "",
            "## Record identity",
            "",
            f"- Assessment: {_markdown(assessment.id)}",
            f"- Profile: {_markdown(assessment.profile.id)} · {_markdown(assessment.profile.version)}",
            f"- Assessment digest: {report.assessment_digest}",
            "",
            "The exact downloaded assessment retains all measurements, source identities and check definitions.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_rtm_csv(report: ValidationReport) -> str:
    measurements = _measurements_by_check(report.assessment)
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\r\n")
    writer.writerow(
        [
            "requirement_id",
            "requirement_text",
            "requirement_scope",
            "mandatory",
            "source_refs",
            "check_id",
            "method",
            "reader",
            "selector",
            "expected",
            "expected_unit",
            "expected_frame",
            "observed",
            "observed_units",
            "observed_frames",
            "status",
            "evidence_refs",
            "subject_id",
            "subject_sha256",
            "producer",
            "action",
            "assessment_id",
            "assessment_digest",
            "is_current",
            "review_required",
            "measurement_uncertainties",
            "uncertainty_note",
        ]
    )
    for row in report.traceability:
        writer.writerow(
            [
                _csv_safe(row.requirement_id),
                _csv_safe(row.requirement_text),
                row.requirement_scope,
                str(row.mandatory).lower(),
                _csv_safe([item.model_dump(mode="json") for item in row.source_refs]),
                _csv_safe(row.check_id),
                row.evidence_method,
                _csv_safe(row.reader),
                _csv_safe(row.selector),
                _csv_safe(row.expected.model_dump(mode="json", exclude_none=True)),
                _csv_safe(row.expected_unit),
                _csv_safe(row.expected_frame),
                _csv_safe(list(row.observed)),
                _csv_safe(list(row.observed_units)),
                _csv_safe(list(row.observed_frames)),
                row.check_state,
                _csv_safe(list(row.evidence_refs)),
                _csv_safe(row.subject_id),
                row.subject_sha256 or "",
                _csv_safe(
                    row.producer.model_dump(mode="json") if row.producer else None
                ),
                row.action or "",
                report.assessment.id,
                report.assessment_digest,
                str(report.currentness.is_current).lower(),
                str(row.review_required).lower(),
                _csv_safe(
                    [
                        {
                            "measurement_id": item.id,
                            "uncertainty": item.uncertainty,
                            "unit": item.unit,
                            "frame": item.frame,
                            "numeric": type(item.value) in {int, float},
                        }
                        for item in measurements.get(row.check_id, ())
                    ]
                ),
                _csv_safe(_UNCERTAINTY_NOTE),
            ]
        )
    return stream.getvalue()


def export_report(report: ValidationReport, format: str) -> ReportExport:
    stem = f"wright-validation-{report.assessment.id}"
    if format == "json":
        content = (
            json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2)
            + "\n"
        ).encode("utf-8")
        return ReportExport(format, "application/json", stem + ".json", content)
    if format == "markdown":
        return ReportExport(
            format,
            "text/markdown; charset=utf-8",
            stem + ".md",
            render_markdown(report).encode("utf-8"),
        )
    if format in {"csv", "rtm"}:
        return ReportExport(
            "csv",
            "text/csv; charset=utf-8",
            stem + "-rtm.csv",
            render_rtm_csv(report).encode("utf-8"),
        )
    raise ValueError("Report format must be json, markdown or csv")
