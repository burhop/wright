"""Deterministic report projections from one immutable assessment."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from html import escape as html_escape
import io
import json

from core.process_validation import (
    Assessment,
    AssessmentCurrentness,
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
    requirements = {
        item.id: item for item in assessment.profile.baseline.requirements
    }
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
    text = html_escape(_text(value), quote=True)
    for character in ("\\", "`", "*", "_", "{", "}", "[", "]", "<", ">", "#", "|", "~"):
        text = text.replace(character, "\\" + character)
    return text.replace("\r", " ").replace("\n", "<br>")


def render_markdown(report: ValidationReport) -> str:
    assessment = report.assessment
    verdict = "PASS" if report.currentness.is_current and assessment.summary.release_eligible else "HOLD"
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
            "| Requirement | Check | Expected | Observed | Status | Evidence | Action |",
            "|---|---|---|---|---|---|---|",
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
            "| {} — {} | {} | {} | {} | {} | {} | {} |".format(
                _markdown(row.requirement_id),
                _markdown(row.requirement_text),
                _markdown(row.check_id),
                _markdown(expected),
                _markdown(observed),
                _markdown(row.check_state),
                _markdown(list(row.evidence_refs)),
                _markdown(row.action),
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


def render_rtm_csv(report: ValidationReport) -> str:
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
                _csv_safe(row.producer.model_dump(mode="json") if row.producer else None),
                row.action or "",
                report.assessment.id,
                report.assessment_digest,
                str(report.currentness.is_current).lower(),
            ]
        )
    return stream.getvalue()


def export_report(report: ValidationReport, format: str) -> ReportExport:
    stem = f"wright-validation-{report.assessment.id}"
    if format == "json":
        content = (json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        return ReportExport(format, "application/json", stem + ".json", content)
    if format == "markdown":
        return ReportExport(format, "text/markdown; charset=utf-8", stem + ".md", render_markdown(report).encode("utf-8"))
    if format in {"csv", "rtm"}:
        return ReportExport("csv", "text/csv; charset=utf-8", stem + "-rtm.csv", render_rtm_csv(report).encode("utf-8"))
    raise ValueError("Report format must be json, markdown or csv")
