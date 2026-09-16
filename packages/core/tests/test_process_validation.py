"""Behavioral contracts: unknown evidence must never become an accepted design."""

import math

import pytest
from pydantic import ValidationError

from core.process_validation import (
    Baseline,
    CheckDefinition,
    CheckResult,
    Constraint,
    ProducerIdentity,
    Requirement,
    SourceReference,
    SubjectBinding,
    ValidationProfile,
    canonical_digest,
    summarize,
)


def profile():
    source = SourceReference(
        artifact_ref="requirements.md", sha256="a" * 64, locator="DEMO-001"
    )
    baseline = Baseline(
        id="demo",
        version="1",
        requirements=(
            Requirement(
                id="identity",
                text="Identity is demo-plate",
                scope="content",
                sources=(source,),
            ),
            Requirement(
                id="length",
                text="Length is 100 +/- 0.2 mm",
                scope="design",
                sources=(source,),
            ),
        ),
    )
    return ValidationProfile(
        id="demo",
        version="1",
        baseline=baseline,
        checks=(
            CheckDefinition(
                id="identity",
                requirement_ids=("identity",),
                subject_role="result",
                reader="structured",
                selector="/part_id",
                constraint=Constraint(operator="equals", expected="demo-plate"),
            ),
            CheckDefinition(
                id="length",
                requirement_ids=("length",),
                subject_role="result",
                reader="structured",
                selector="/length_mm",
                unit="mm",
                constraint=Constraint(operator="within", target=100, tolerance=0.2),
            ),
        ),
    )


def result(check_id, state):
    return CheckResult(
        check_id=check_id,
        requirement_ids=(check_id,),
        state=state,
        evidence_refs=("observation-1",) if state in {"pass", "fail"} else (),
        finding_ids=("finding-1",) if state not in {"pass", "not_applicable"} else (),
    )


def test_canonical_identity_is_order_independent_and_rejects_nonfinite():
    assert canonical_digest({"a": 1, "b": [2]}) == canonical_digest({"b": [2], "a": 1})
    for value in [math.nan, math.inf, -math.inf, {"nested": [math.nan]}]:
        with pytest.raises(ValueError):
            canonical_digest(value)


def test_value_subject_requires_exact_content_and_producer_revision():
    args = dict(
        id="subject-1",
        role="result",
        result_id="run:producer:result",
        kind="value",
        producer=ProducerIdentity(
            run_id="run", step_id="producer", attempt=1, output_port="result"
        ),
        value={"length_mm": 98},
        sha256=canonical_digest({"length_mm": 98}),
    )
    subject = SubjectBinding(**args)
    with pytest.raises(ValidationError, match="digest"):
        SubjectBinding(**{**args, "value": {"length_mm": 100}})
    revised = SubjectBinding(
        **{**args, "producer": {**subject.producer.model_dump(), "attempt": 2}}
    )
    assert canonical_digest(subject) != canonical_digest(revised)
    with pytest.raises(ValidationError):
        ProducerIdentity(
            run_id="run", step_id="producer", attempt=0, output_port="result"
        )


@pytest.mark.parametrize(
    "path",
    ["../secret", "C:/secret", "/secret", "a/../secret", "a\\secret", "a//secret"],
)
def test_file_subject_rejects_unconfined_locators(path):
    with pytest.raises(ValidationError):
        SubjectBinding(
            id="s",
            role="file",
            result_id="r",
            kind="file",
            locator=path,
            sha256="a" * 64,
            producer=ProducerIdentity(
                run_id="r", step_id="s", attempt=1, output_port="file"
            ),
        )


@pytest.mark.parametrize(
    "constraint",
    [
        {"operator": "within", "target": 10, "tolerance": -1},
        {"operator": "within", "target": math.nan, "tolerance": 1},
        {"operator": "within", "target": True, "tolerance": 1},
        {"operator": "range", "minimum": 20, "maximum": 10},
        {"operator": "range"},
        {"operator": "python", "expected": "return True"},
    ],
)
def test_invalid_acceptance_limits_are_rejected(constraint):
    with pytest.raises(ValidationError):
        Constraint(**constraint)


def test_profile_rejects_uncovered_or_unknown_requirement_and_duplicate_check():
    raw = profile().model_dump()
    with pytest.raises(ValidationError, match="coverage"):
        ValidationProfile(**{**raw, "checks": raw["checks"][:1]})
    with pytest.raises(ValidationError, match="unique"):
        ValidationProfile(**{**raw, "checks": raw["checks"] + raw["checks"][:1]})
    raw["checks"][0]["requirement_ids"] = ("invented",)
    with pytest.raises(ValidationError, match="unknown"):
        ValidationProfile(**raw)


def test_profile_identity_includes_source_and_acceptance_limits():
    original = profile()
    raw = original.model_dump()
    raw["checks"][1]["constraint"]["tolerance"] = 0.3
    assert canonical_digest(original) != canonical_digest(ValidationProfile(**raw))


def test_known_failure_survives_an_unavailable_content_check():
    summary = summarize(
        profile(), (result("identity", "blocked"), result("length", "fail"))
    )
    assert summary.requirements_compliant is False
    assert summary.content_verified is None
    assert not summary.evaluation_complete
    assert not summary.release_eligible


def test_an_accurate_analysis_can_describe_a_noncompliant_design():
    summary = summarize(
        profile(), (result("identity", "pass"), result("length", "fail"))
    )
    assert summary.content_verified is True
    assert summary.requirements_compliant is False
    assert summary.evaluation_complete
    assert not summary.release_eligible


def test_no_older_or_partial_pass_can_release_current_work():
    checks = (result("identity", "pass"), result("length", "pass"))
    assert summarize(profile(), checks).release_eligible
    assert not summarize(profile(), checks, subject_current=False).release_eligible
    assert not summarize(profile(), checks[:1]).release_eligible
    assert not summarize(profile(), ()).release_eligible


def test_false_pass_without_evidence_and_unjustified_na_are_invalid():
    with pytest.raises(ValidationError, match="evidence"):
        CheckResult(check_id="length", requirement_ids=("length",), state="pass")
    with pytest.raises(ValidationError, match="applicability"):
        CheckResult(
            check_id="length", requirement_ids=("length",), state="not_applicable"
        )


def test_unknown_contract_version_is_not_accepted():
    with pytest.raises(ValidationError):
        ValidationProfile(
            **{
                **profile().model_dump(),
                "schema_version": "wright.process-validation/99",
            }
        )


def test_result_cannot_reassign_check_to_a_different_requirement():
    forged = CheckResult(
        check_id="identity",
        requirement_ids=("length",),
        state="pass",
        evidence_refs=("e",),
    )
    with pytest.raises(ValueError, match="requirements"):
        summarize(profile(), (forged,))
