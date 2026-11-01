"""Actual-output evaluation and actionable failure behavior, independent of UI."""

import hashlib
import json

import pytest

from core.process_validation import (
    ProducerIdentity,
    SubjectBinding,
    ValidationRequest,
    canonical_digest,
)
from data_vault.process_validation_repository import ProcessValidationRepository
from workspace_service.process_validation.profiles import load_profile
from workspace_service.process_validation.readers.base import ReaderRegistry
from workspace_service.process_validation.readers.structured import StructuredReader
from workspace_service.process_validation.service import ProcessValidationService
from workspace_service.process_validation.subjects import SubjectResolver


def evaluate(
    tmp_path,
    value,
    *,
    profile=None,
    registry=None,
    key="evaluate",
    file_bytes=None,
    file_format="json",
    related_subjects=(),
):
    profile = profile or load_profile("structured-demo")
    args = dict(
        id="subject",
        role="result",
        result_id="run:producer:result",
        producer=ProducerIdentity(
            run_id="run", step_id="producer", attempt=1, output_port="result"
        ),
    )
    if file_bytes is None:
        subject = SubjectBinding(
            **args, kind="value", value=value, sha256=canonical_digest(value)
        )
    else:
        (tmp_path / "result.json").write_bytes(file_bytes)
        subject = SubjectBinding(
            **args,
            kind="file",
            format=file_format,
            locator="result.json",
            encoding="raw-bytes",
            sha256=hashlib.sha256(file_bytes).hexdigest(),
        )
    request = ValidationRequest(
        trace_id="trace",
        workspace_id="workspace",
        invocation_id="check",
        subjects=(subject, *related_subjects),
        profile_ref=profile.reference(),
        baseline_ref=profile.baseline.reference(),
        idempotency_key=key,
    )
    service = ProcessValidationService(
        ProcessValidationRepository(tmp_path / "state.sqlite3"),
        SubjectResolver("workspace", str(tmp_path)),
        registry=registry,
    )
    return service.evaluate(request, profile), service, request


@pytest.mark.parametrize("length", [99.8, 100, 100.2])
def test_valid_and_boundary_alternatives_pass(tmp_path, length):
    outcome, _, _ = evaluate(tmp_path, {"length_mm": length, "part_id": "demo-plate"})
    assert outcome.release_eligible
    assert outcome.assessment.summary.evaluation_complete
    assert len(outcome.assessment.measurements) == 4


def test_defect_has_precise_values_source_location_and_repair_target(tmp_path):
    outcome, _, _ = evaluate(tmp_path, {"length_mm": 98, "part_id": "demo-plate"})
    assert not outcome.release_eligible
    finding = outcome.assessment.findings[0]
    assert finding.state == "fail" and finding.observed == 98
    assert finding.expected.target == 100 and finding.expected.tolerance == 0.2
    assert finding.unit == "mm" and finding.selector == "/length_mm"
    assert finding.owner.step_id == finding.correction.target_step_id == "producer"
    assert finding.correction.action == "revise_output"
    assert finding.evidence_refs and finding.source_refs
    assert outcome.assessment.summary.content_verified is True
    assert outcome.assessment.summary.requirements_compliant is False


def test_finding_describes_the_requirement_without_instructing_evidence_edits(tmp_path):
    outcome, _, _ = evaluate(tmp_path, {"length_mm": 98, "part_id": "demo-plate"})
    finding = outcome.assessment.findings[0]
    assert finding.correction.target == "Required at /length_mm: 100 mm, within 0.2 mm."
    assert finding.explanation.startswith("Observed 98 mm. Required at /length_mm:")
    # A structured subject can be an inspection record. Its selector is an
    # evidence locator, not authorization to replace a measurement with a target.
    assert finding.correction.action == "revise_output"
    assert finding.correction.target_step_id == finding.owner.step_id == "producer"
    assert finding.observed == 98 and finding.expected.target == 100
    assert finding.correction.recheck_ids


@pytest.mark.parametrize("value", [True, "100", None])
def test_invalid_numeric_value_is_an_output_defect_not_a_reader_crash(tmp_path, value):
    outcome, _, _ = evaluate(tmp_path, {"length_mm": value, "part_id": "demo-plate"})
    assert not outcome.release_eligible
    assert outcome.assessment.findings[0].category == "output_defect"


def test_missing_required_field_identifies_the_field(tmp_path):
    outcome, _, _ = evaluate(tmp_path, {"part_id": "demo-plate"})
    finding = outcome.assessment.findings[0]
    assert finding.state == "fail" and finding.selector == "/length_mm"
    assert finding.code == "output.required_value_missing"
    assert outcome.assessment.summary.content_verified is False


@pytest.mark.parametrize(
    "raw", [b'{"length_mm":NaN}', b'{"length_mm":100,"length_mm":98}', b"not json"]
)
def test_malformed_content_cannot_be_accepted_as_a_summary(tmp_path, raw):
    outcome, _, _ = evaluate(tmp_path, None, file_bytes=raw)
    assert not outcome.release_eligible
    assert all(check.state == "fail" for check in outcome.assessment.checks)
    assert all(f.category == "output_defect" for f in outcome.assessment.findings)


def test_unavailable_reader_is_blocked_with_named_next_action(tmp_path):
    outcome, _, _ = evaluate(tmp_path, {"length_mm": 100}, registry=ReaderRegistry())
    assert not outcome.release_eligible
    assert all(
        f.category == "capability_unavailable"
        and f.correction.action == "restore_capability"
        for f in outcome.assessment.findings
    )


def test_evaluator_fault_stays_error_not_design_failure(tmp_path):
    class BrokenReader(StructuredReader):
        def measure(self, *_):
            raise ArithmeticError("internal fault with private details")

    registry = ReaderRegistry()
    registry.register(BrokenReader())
    outcome, _, _ = evaluate(tmp_path, {"length_mm": 100}, registry=registry)
    assert outcome.attempt.state == "error"
    assert outcome.assessment.summary.requirements_compliant is None
    assert all(f.category == "validator_error" for f in outcome.assessment.findings)
    assert "private details" not in outcome.assessment.model_dump_json()


def test_same_request_is_idempotent_but_new_attempt_does_not_reuse_old_pass(tmp_path):
    first, service, request = evaluate(
        tmp_path, {"length_mm": 100, "part_id": "demo-plate"}
    )
    duplicate = service.evaluate(request, load_profile("structured-demo"))
    assert duplicate.assessment.id == first.assessment.id
    second, _, _ = evaluate(
        tmp_path, {"length_mm": 98, "part_id": "demo-plate"}, key="second"
    )
    assert not second.release_eligible
    old = service.evaluate(request, load_profile("structured-demo"))
    assert old.assessment.summary.release_eligible  # historical evidence is retained
    assert not old.is_current and not old.release_eligible


def test_file_mutation_during_measurement_prevents_release(tmp_path):
    class MutatingReader(StructuredReader):
        def measure(self, *args):
            measured = super().measure(*args)
            (tmp_path / "result.json").write_text('{"length_mm":98}', encoding="utf-8")
            return measured

    registry = ReaderRegistry()
    registry.register(MutatingReader())
    raw = json.dumps({"length_mm": 100, "part_id": "demo-plate"}).encode()
    outcome, _, _ = evaluate(tmp_path, None, registry=registry, file_bytes=raw)
    assert not outcome.release_eligible
    assert any(f.category == "stale_subject" for f in outcome.assessment.findings)


def numeric_profile(*, parameters=None, reader="structured"):
    from core.process_validation import ValidationProfile

    raw = load_profile("structured-demo").model_dump()
    raw["version"] = "numeric-test"
    raw["checks"][0]["parameters"] = parameters or {}
    raw["checks"][0]["reader"] = reader
    return ValidationProfile(**raw)


def test_unit_conversion_compares_the_same_physical_quantity(tmp_path):
    profile = numeric_profile(parameters={"unit_pointer": "/unit"})
    outcome, _, _ = evaluate(
        tmp_path,
        {"length_mm": 0.100, "unit": "m", "part_id": "demo-plate"},
        profile=profile,
    )
    assert outcome.release_eligible
    assert outcome.assessment.measurements[0].unit == "m"


def test_unknown_dimension_stays_inconclusive(tmp_path):
    profile = numeric_profile(parameters={"unit_pointer": "/unit"})
    outcome, _, _ = evaluate(
        tmp_path,
        {"length_mm": 100, "unit": "kg", "part_id": "demo-plate"},
        profile=profile,
    )
    assert not outcome.release_eligible
    assert outcome.assessment.checks[0].state == "inconclusive"
    assert outcome.assessment.findings[0].correction.action == "supply_input"


@pytest.mark.parametrize(
    "length,uncertainty,state",
    [(100, 0.1, "pass"), (100.2, 0.01, "inconclusive"), (101, 0.01, "fail")],
)
def test_uncertainty_interval_has_three_distinct_outcomes(
    tmp_path, length, uncertainty, state
):
    profile = numeric_profile(parameters={"uncertainty_pointer": "/uncertainty"})
    outcome, _, _ = evaluate(
        tmp_path,
        {"length_mm": length, "uncertainty": uncertainty, "part_id": "demo-plate"},
        profile=profile,
    )
    assert outcome.assessment.checks[0].state == state
    assert outcome.release_eligible == (state == "pass")


def test_failure_survives_a_different_blocked_check(tmp_path):
    from core.process_validation import ValidationProfile

    raw = numeric_profile().model_dump()
    raw["checks"][1]["reader"] = "missing-reader"
    outcome, _, _ = evaluate(
        tmp_path,
        {"length_mm": 98, "part_id": "demo-plate"},
        profile=ValidationProfile(**raw),
    )
    assert outcome.assessment.summary.requirements_compliant is False
    assert not outcome.assessment.summary.evaluation_complete
    assert {f.state for f in outcome.assessment.findings} == {"fail", "blocked"}


def test_csv_reader_identifies_actual_row_and_column(tmp_path):
    from core.process_validation import ValidationProfile

    raw = load_profile("structured-demo").model_dump()
    raw["version"] = "csv-test"
    raw["checks"][0]["selector"] = "/rows/0/length_mm"
    raw["checks"][1]["selector"] = "/rows/0/part_id"
    raw["checks"][3]["selector"] = "/rows/0/length_mm"
    outcome, _, _ = evaluate(
        tmp_path,
        None,
        file_bytes=b"length_mm,part_id\n98,demo-plate\n",
        file_format="csv",
        profile=ValidationProfile(**raw),
    )
    finding = outcome.assessment.findings[0]
    assert finding.observed == 98 and finding.selector == "/rows/0/length_mm"
    assert finding.state == "fail"


def test_frozen_fixture_files_reach_the_intended_check(tmp_path):
    from pathlib import Path

    fixture_root = (
        Path(__file__).resolve().parents[3]
        / "tests/datasets/process-validation/structured"
    )
    good, _, _ = evaluate(
        tmp_path, None, file_bytes=(fixture_root / "valid.json").read_bytes()
    )
    assert good.release_eligible
    bad, _, _ = evaluate(
        tmp_path,
        None,
        key="bad",
        file_bytes=(fixture_root / "wrong-length.json").read_bytes(),
    )
    assert bad.assessment.findings[0].check_id == "length"
    assert bad.assessment.findings[0].observed == 98


def test_failure_preserves_observed_and_expected_units_separately(tmp_path):
    profile = numeric_profile(parameters={"unit_pointer": "/unit"})
    outcome, _, _ = evaluate(
        tmp_path,
        {"length_mm": 0.098, "unit": "m", "part_id": "demo-plate"},
        profile=profile,
    )
    finding = outcome.assessment.findings[0]
    assert finding.unit == "mm" and finding.observed_unit == "m"
    assert finding.expected.target == 100 and finding.observed == 0.098
    assert finding.explanation.startswith(
        "Observed 0.098 m. Required at /length_mm: 100 mm"
    )
    assert "Observed 0.098 mm" not in finding.explanation


def test_inline_text_observation_does_not_include_serialization_quotes():
    from core.process_validation import (
        CheckDefinition,
        Constraint,
        ResourceBudget,
        canonical_json,
    )
    from workspace_service.process_validation.readers.base import (
        ReaderContext,
        SubjectSnapshot,
    )

    subject = SubjectBinding(
        id="s",
        role="result",
        result_id="r",
        kind="value",
        format="text",
        value="Part report\nAccepted scope",
        sha256=canonical_digest("Part report\nAccepted scope"),
        producer=ProducerIdentity(
            run_id="r", step_id="p", attempt=1, output_port="text"
        ),
    )
    check = CheckDefinition(
        id="title",
        requirement_ids=("title",),
        subject_role="result",
        reader="structured",
        selector="/lines/0",
        constraint=Constraint(operator="equals", expected="Part report"),
    )
    observed = StructuredReader().measure(
        SubjectSnapshot(subject, canonical_json(subject.value).encode()),
        check,
        ReaderContext.create(ResourceBudget(), "trace"),
    )
    assert observed.value == "Part report"


def test_cancelled_invocation_keeps_an_explicit_terminal_result(tmp_path):
    from threading import Event

    _, service, request = evaluate(
        tmp_path, {"length_mm": 100, "part_id": "demo-plate"}
    )
    cancel = Event()
    cancel.set()
    request = ValidationRequest(
        **{**request.model_dump(), "idempotency_key": "cancelled-request"}
    )
    outcome = service.evaluate(
        request, load_profile("structured-demo"), cancelled=cancel
    )
    assert outcome.attempt.state == "cancelled" and not outcome.release_eligible
    assert outcome.assessment.findings[0].code == "validation.cancelled"
