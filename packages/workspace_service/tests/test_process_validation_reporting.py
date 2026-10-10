"""Report, paging, currentness and authenticated-review behavior."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from core.process_validation import (
    Baseline,
    CheckDefinition,
    Constraint,
    ProducerIdentity,
    Requirement,
    SourceReference,
    SubjectBinding,
    ValidationProfile,
    ValidationReport,
    ValidationRequest,
    canonical_digest,
)
from data_vault.process_validation_repository import ProcessValidationRepository
from workspace_service.process_validation.reporting import export_report
from workspace_service.process_validation.service import ProcessValidationService
from workspace_service.process_validation.subjects import SubjectResolver


REPOSITORY = Path(__file__).parents[3]


def _profile(*, review: bool = False, requirement_text: str = "Length is 100 mm"):
    requirements = [
        Requirement(
            id="REQ-LENGTH",
            text=requirement_text,
            scope="design",
            sources=(
                SourceReference(
                    artifact_ref="requirements.json",
                    sha256="a" * 64,
                    locator="REQ-LENGTH",
                ),
            ),
        )
    ]
    checks = [
        CheckDefinition(
            id="length",
            requirement_ids=("REQ-LENGTH",),
            subject_role="result",
            reader="structured",
            selector="/length_mm",
            constraint=Constraint(operator="within", target=100.0, tolerance=0.2),
            unit="mm",
        )
    ]
    if review:
        requirements.append(
            Requirement(
                id="REQ-REVIEW",
                text="Drawing has been reviewed",
                scope="design",
                sources=(
                    SourceReference(
                        artifact_ref="requirements.json",
                        sha256="a" * 64,
                        locator="REQ-REVIEW",
                    ),
                ),
                review_required=True,
            )
        )
        checks.append(
            CheckDefinition(
                id="drawing-review",
                requirement_ids=("REQ-REVIEW",),
                subject_role="result",
                reader="review",
                selector="/drawing",
                constraint=Constraint(operator="review"),
                evidence_method="human_review",
            )
        )
    return ValidationProfile(
        id="report-demo",
        version="1",
        baseline=Baseline(id="report-basis", version="1", requirements=requirements),
        checks=checks,
        excluded_scope=("Manufacturing inspection is outside this check.",),
        limitations=("Physical validation is not assessed.",),
    )


def _request(profile, *, length=98, key="one", workspace="workspace"):
    value = {"length_mm": length}
    return ValidationRequest(
        trace_id="trace",
        workspace_id=workspace,
        invocation_id="report-check",
        subjects=(
            SubjectBinding(
                id=f"subject-{key}",
                role="result",
                result_id=f"import:{key}:result",
                producer=ProducerIdentity(
                    run_id="report-check",
                    step_id="import",
                    attempt=1,
                    output_port="result",
                ),
                kind="value",
                value=value,
                sha256=canonical_digest(value),
            ),
        ),
        profile_ref=profile.reference(),
        baseline_ref=profile.baseline.reference(),
        idempotency_key=key,
    )


def _service(tmp_path):
    repository = ProcessValidationRepository(tmp_path / "validation.sqlite3")
    return ProcessValidationService(
        repository, SubjectResolver("workspace", str(tmp_path))
    )


def test_json_markdown_and_rtm_share_one_assessment_verdict(tmp_path):
    service = _service(tmp_path)
    outcome = service.evaluate(_request(_profile(), length=98), _profile())
    report = service.get_result(outcome.assessment.id)

    assert isinstance(report, ValidationReport)
    assert report.currentness.is_current
    assert report.traceability[0].check_state == "fail"
    assert report.traceability[0].observed == (98,)

    exported_json = json.loads(export_report(report, "json").content)
    markdown = export_report(report, "markdown").content.decode()
    csv_rows = list(
        csv.DictReader(io.StringIO(export_report(report, "csv").content.decode()))
    )
    assert exported_json["assessment"]["summary"]["release_eligible"] is False
    assert "**Verdict:** HOLD" in markdown
    assert csv_rows[0]["status"] == "fail"
    assert csv_rows[0]["assessment_digest"] == report.assessment_digest


def test_reports_escape_markdown_and_neutralize_csv_formulas(tmp_path):
    malicious = '=HYPERLINK("https://invalid") | <script>alert(1)</script>'
    profile = _profile(requirement_text=malicious)
    service = _service(tmp_path)
    assessment = service.evaluate(_request(profile), profile).assessment
    report = service.get_result(assessment.id)

    markdown = export_report(report, "markdown").content.decode()
    row = next(
        csv.DictReader(io.StringIO(export_report(report, "csv").content.decode()))
    )
    assert "<script>" not in markdown
    assert "\\|" in markdown
    assert row["requirement_text"].startswith("'=")


@pytest.mark.parametrize(
    ("text", "escaped"),
    [
        (
            "Required reader 'probe' is unavailable.",
            "Required reader &#x27;probe&#x27; is unavailable.",
        ),
        (
            '"P2" & <raw> [link](https://invalid) #tag_1',
            "&quot;P2&quot; &amp; &lt;raw&gt; \\[link\\](https://invalid) \\#tag\\_1",
        ),
        ("Literal &#x27; and &lt;", "Literal &amp;\\#x27; and &amp;lt;"),
    ],
)
def test_report_escaping_keeps_generated_entities_intact(text, escaped):
    from workspace_service.process_validation.reporting import _markdown

    assert _markdown(text) == escaped


def test_currentness_and_finding_pages_use_latest_authoritative_attempt(tmp_path):
    profile = _profile()
    service = _service(tmp_path)
    first = service.evaluate(_request(profile, key="first"), profile).assessment
    page = service.list_findings(first.id, limit=1)
    assert page.is_current and page.next_cursor is None
    assert page.findings[0].observed == 98

    second = service.evaluate(
        _request(profile, length=100, key="second"), profile
    ).assessment
    assert service.get_result(second.id).currentness.is_current
    stale = service.get_result(first.id).currentness
    assert not stale.is_current
    assert stale.stale_reason == "newer_validation_attempt"
    assert stale.latest_attempt_id == second.attempt_id


def test_late_review_appends_new_assessment_and_preserves_original(tmp_path):
    profile = _profile(review=True)
    service = _service(tmp_path)
    original = service.evaluate(_request(profile, length=100), profile).assessment
    assert not original.summary.release_eligible

    revised = service.record_review(
        original.id,
        requirement_id="REQ-REVIEW",
        actor_id="engineer-1",
        authority_ref="authenticated-request-1",
        decision="approved",
        rationale="Reviewed the attached drawing against the requirement.",
        evidence_refs=("wright://workspace/workspace/drawing.pdf#page=1",),
    )

    assert revised.supersedes == original.id
    assert revised.summary.release_eligible
    assert revised.review_ids and revised.id != original.id
    assert service.repository.assessment("workspace", original.id) == original
    stale = service.get_result(original.id).currentness
    assert stale.stale_reason == "superseded_by_review"
    assert stale.superseded_by == (revised.id,)
    assert service.get_result(revised.id).currentness.is_current
    with pytest.raises(ValueError, match="current"):
        service.record_review(
            original.id,
            requirement_id="REQ-REVIEW",
            actor_id="engineer-1",
            authority_ref="authenticated-request-2",
            decision="approved",
            rationale="Replay must not rewrite history.",
            evidence_refs=("wright://workspace/workspace/drawing.pdf#page=1",),
        )


def test_authenticated_changes_requested_remains_a_failed_review(tmp_path):
    profile = _profile(review=True)
    service = _service(tmp_path)
    original = service.evaluate(_request(profile, length=100), profile).assessment
    revised = service.record_review(
        original.id,
        requirement_id="REQ-REVIEW",
        actor_id="engineer-2",
        authority_ref="authenticated-request-3",
        decision="changes_requested",
        rationale="Add the missing revision annotation before approval.",
        evidence_refs=("wright://workspace/workspace/review-note#finding-1",),
    )
    review_check = next(
        item for item in revised.checks if item.check_id == "drawing-review"
    )
    finding = next(
        item for item in revised.findings if item.check_id == "drawing-review"
    )
    assert review_check.state == "fail"
    assert finding.code == "review.changes_requested"
    assert finding.explanation == "Add the missing revision annotation before approval."
    assert not revised.summary.release_eligible


def test_report_reads_do_not_cross_workspace_boundary(tmp_path):
    profile = _profile()
    service = _service(tmp_path)
    assessment = service.evaluate(_request(profile), profile).assessment
    foreign = ProcessValidationService(
        service.repository, SubjectResolver("other", str(tmp_path))
    )
    with pytest.raises(KeyError):
        foreign.get_result(assessment.id)


def test_schema_only_consumer_accepts_examples_and_reconciles_exports():
    contract = REPOSITORY / "specs/082-output-content-validation/contracts"
    schema = json.loads(
        (contract / "schemas/ValidationReport.schema.json").read_text(encoding="utf-8")
    )
    validator = Draft202012Validator(schema)
    expected = {
        "pass": (True, True),
        "fail": (False, True),
        "mixed": (False, True),
        "blocked": (False, True),
        "error": (False, True),
        "stale": (True, False),
        "repair": (False, True),
    }
    reports = {}
    for name, (release_eligible, is_current) in expected.items():
        report = json.loads(
            (contract / f"examples/{name}.report.json").read_text(encoding="utf-8")
        )
        validator.validate(report)
        assert report["assessment"]["summary"]["release_eligible"] is release_eligible
        assert report["currentness"]["is_current"] is is_current
        reports[name] = report

    repair = reports["repair"]
    markdown = (contract / "examples/repair.report.md").read_text(encoding="utf-8")
    csv_rows = list(
        csv.DictReader(
            io.StringIO(
                (contract / "examples/repair.rtm.csv").read_text(encoding="utf-8")
            )
        )
    )
    assert "**Verdict:** HOLD" in markdown
    assert {row["status"] for row in csv_rows} == {
        row["check_state"] for row in repair["traceability"]
    }
    assert {row["assessment_digest"] for row in csv_rows} == {
        repair["assessment_digest"]
    }
