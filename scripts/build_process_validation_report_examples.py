"""Build deterministic v1 report examples from contract-valid assessments."""

from __future__ import annotations

import json
from pathlib import Path

from core.process_validation import (
    Assessment,
    AssessmentCurrentness,
    CheckResult,
    Correction,
    Finding,
    summarize,
)
from workspace_service.process_validation.reporting import (
    build_report,
    render_markdown,
    render_rtm_csv,
)


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "artifacts/process-validation/structured-loop/20260916T202647Z"
TARGET = ROOT / "specs/082-output-content-validation/contracts/examples"


def _load(name: str) -> Assessment:
    return Assessment.model_validate_json(
        (EVIDENCE / "workspace/validation" / name).read_bytes()
    )


def _currentness(
    assessment: Assessment, *, stale_reason: str | None = None
) -> AssessmentCurrentness:
    return AssessmentCurrentness(
        as_of="2026-09-16T21:00:00Z",
        selected_assessment_id=assessment.id,
        selected_attempt_id=assessment.attempt_id,
        selected_subject_ids=tuple(item.id for item in assessment.request.subjects),
        latest_attempt_id=(
            "attempt-example-newer"
            if stale_reason == "newer_validation_attempt"
            else assessment.attempt_id
        ),
        latest_assessment_id=(
            "assessment-example-newer"
            if stale_reason == "newer_validation_attempt"
            else assessment.id
        ),
        is_current=stale_reason is None,
        stale_reason=stale_reason,
    )


def _replace_finding(
    source: Assessment,
    *,
    identifier: str,
    state: str,
    category: str,
    action: str,
    code: str,
) -> Assessment:
    original = source.findings[0]
    correction = Correction(
        action=action,
        target=(
            "Provide the missing evidence and run validation again."
            if action == "supply_input"
            else "Repair the validator capability and retry the same output."
        ),
        recheck_ids=tuple(item.id for item in source.profile.checks),
    )
    finding = Finding(
        **{
            **original.model_dump(),
            "id": "finding-example-" + identifier,
            "code": code,
            "state": state,
            "category": category,
            "observed": None if state != "fail" else original.observed,
            "observed_unit": None if state != "fail" else original.observed_unit,
            "observed_frame": None if state != "fail" else original.observed_frame,
            "evidence_refs": () if state != "fail" else original.evidence_refs,
            "summary": correction.target,
            "explanation": correction.target,
            "correction": correction,
        }
    )
    checks = tuple(
        CheckResult(
            **{
                **item.model_dump(),
                "state": state,
                "measurement_ids": item.measurement_ids if state == "fail" else (),
                "evidence_refs": item.evidence_refs if state == "fail" else (),
                "finding_ids": (finding.id,),
            }
        )
        if item.check_id == original.check_id
        else item
        for item in source.checks
    )
    return Assessment(
        **{
            **source.model_dump(),
            "id": "assessment-example-" + identifier,
            "checks": checks,
            "findings": (finding,),
            "summary": summarize(source.profile, checks),
        }
    )


def _mixed(source: Assessment) -> Assessment:
    definition = next(item for item in source.profile.checks if item.id == "part-identity")
    requirement_ids = definition.requirement_ids
    source_refs = tuple(
        ref
        for requirement in source.profile.baseline.requirements
        if requirement.id in requirement_ids
        for ref in requirement.sources
    )
    finding = Finding(
        id="finding-example-mixed-missing",
        code="subject.role_missing",
        check_id=definition.id,
        requirement_ids=requirement_ids,
        state="blocked",
        category="missing_evidence",
        expected=definition.constraint,
        source_refs=source_refs,
        summary="The required identity evidence is missing.",
        explanation="Bind the required identity output and run validation again.",
        correction=Correction(
            action="supply_input",
            target="Bind the required identity output and run validation again.",
            recheck_ids=tuple(item.id for item in source.profile.checks),
        ),
    )
    checks = tuple(
        CheckResult(
            check_id=item.check_id,
            requirement_ids=item.requirement_ids,
            state="blocked",
            finding_ids=(finding.id,),
        )
        if item.check_id == definition.id
        else item
        for item in source.checks
    )
    return Assessment(
        **{
            **source.model_dump(),
            "id": "assessment-example-mixed",
            "checks": checks,
            "findings": (*source.findings, finding),
            "summary": summarize(source.profile, checks),
        }
    )


def build() -> None:
    failed = _load("assessment-c15a88754bb042aeb37a84d3dfaad2bf.json")
    passed = _load("assessment-a867edfeee654ea9a2e196ea3ff740a2.json")
    examples = {
        "pass": (passed, None),
        "fail": (
            _replace_finding(
                failed,
                identifier="fail",
                state="fail",
                category="output_defect",
                action="supply_input",
                code="requirement.failed_no_safe_repair",
            ),
            None,
        ),
        "mixed": (_mixed(failed), None),
        "blocked": (
            _replace_finding(
                failed,
                identifier="blocked",
                state="blocked",
                category="missing_evidence",
                action="supply_input",
                code="subject.required_evidence_missing",
            ),
            None,
        ),
        "error": (
            _replace_finding(
                failed,
                identifier="error",
                state="error",
                category="validator_error",
                action="retry_validation",
                code="validator.reader_error",
            ),
            None,
        ),
        "stale": (passed, "newer_validation_attempt"),
        "repair": (failed, None),
    }
    TARGET.mkdir(parents=True, exist_ok=True)
    for name, (assessment, stale_reason) in examples.items():
        report = build_report(
            assessment, _currentness(assessment, stale_reason=stale_reason)
        )
        (TARGET / f"{name}.report.json").write_text(
            json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
        if name == "repair":
            (TARGET / "repair.report.md").write_text(
                render_markdown(report), encoding="utf-8"
            )
            (TARGET / "repair.rtm.csv").write_text(
                render_rtm_csv(report), encoding="utf-8", newline=""
            )


if __name__ == "__main__":
    build()
