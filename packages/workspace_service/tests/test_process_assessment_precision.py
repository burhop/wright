"""Readable numbers cannot change assessments, exports or borderline findings."""

import pytest

from core.process_validation import Constraint, RequirementTraceRow
from workspace_service.process_validation.reporting import (
    _markdown,
    _readable_measurement,
    export_report,
    render_readable_markdown,
)
from .test_process_validation_reporting import _profile, _request, _service


def row(rule=None, state="pass", unit="mm", frame=None):
    return RequirementTraceRow(
        requirement_id="dimension",
        requirement_text="Recorded dimension",
        requirement_scope="design",
        mandatory=True,
        review_required=False,
        source_refs=_profile().baseline.requirements[0].sources,
        check_id="dimension",
        check_version="1",
        check_state=state,
        reader="structured",
        evidence_method="independent_measurement",
        selector="/value",
        expected=Constraint(**(rule or {"operator": "range", "maximum": 100})),
        expected_unit=unit,
        expected_frame=frame,
        observed=(),
        observed_units=(),
        observed_frames=(),
        evidence_refs=(),
        finding_ids=(),
    )


@pytest.mark.parametrize(
    "value,expected",
    [
        (41.6666666665829, "≈ 41.6667"),
        (5.600000000000236, "≈ 5.6"),
        (4.890807758808503e-12, "≈ 4.89081e-12"),
        (-1.234567891e-220, "≈ -1.23457e-220"),
        (-1.234567891e290, "≈ -1.23457e+290"),
        (1.234567891e-310, "≈ 1.23457e-310"),
        (0.0, "0.0"),
        (-0.0, "-0.0"),
        (100.0, "100.0"),
        (123456789012345678901234567890, "123456789012345678901234567890"),
        (True, "Yes"),
        (False, "No"),
        (None, ""),
        ("41.6666666665829", "41.6666666665829"),
        ([1.23456789], "[1.23456789]"),
        (float("inf"), "Infinity"),
        (float("-inf"), "-Infinity"),
        (float("nan"), "NaN"),
    ],
)
def test_compact_display_preserves_types_sign_and_scale(value, expected):
    assert _readable_measurement(value, row(), "mm", None) == expected


@pytest.mark.parametrize(
    "state", ["fail", "blocked", "error", "inconclusive", "not_applicable"]
)
def test_nonpassing_findings_keep_full_observation(state):
    assert (
        _readable_measurement(5.200000000000176, row(state=state), "mm", None)
        == "5.200000000000176"
    )


@pytest.mark.parametrize(
    "rule,value",
    [
        ({"operator": "range", "maximum": 45, "inclusive": True}, 44.9999999),
        ({"operator": "range", "maximum": 45, "inclusive": False}, 44.9999999),
        ({"operator": "range", "minimum": 45, "inclusive": False}, 45.0000001),
        ({"operator": "range", "maximum": 1.234567895}, 1.234567891),
        ({"operator": "within", "target": 100, "tolerance": 0.2}, 100.199999999),
        ({"operator": "within", "target": 100, "tolerance": 0.2}, 99.800000001),
        (
            {"operator": "range", "minimum": 1e-300, "inclusive": False},
            1.000000000099e-300,
        ),
        ({"operator": "equals", "expected": 5.600000000000236}, 5.600000000000236),
        ({"operator": "exists"}, 5.600000000000236),
    ],
)
def test_limits_and_exact_comparisons_keep_full_precision(rule, value):
    assert _readable_measurement(value, row(rule), "mm", None) == str(value)


@pytest.mark.parametrize(
    "unit,frame", [("m", None), (None, None), ("mm", "other-frame")]
)
def test_different_measurement_units_or_frames_are_not_rounded(unit, frame):
    assert (
        _readable_measurement(5.600000000000236, row(), unit, frame)
        == "5.600000000000236"
    )


@pytest.mark.parametrize(
    "value,state,display",
    [
        (99.999999999123, "pass", "≈ 100"),
        (100.199999999, "pass", "100.199999999"),
        (100.200000001, "fail", "100.200000001"),
    ],
)
def test_display_does_not_mutate_assessment_or_any_export(
    tmp_path, value, state, display
):
    profile = _profile()
    service = _service(tmp_path)
    assessment = service.evaluate(_request(profile, length=value), profile).assessment
    report = service.get_result(assessment.id)
    original = assessment.model_dump_json()
    exports = {
        kind: export_report(report, kind).content
        for kind in ("json", "markdown", "csv")
    }
    assert report.traceability[0].check_state == state
    text = render_readable_markdown(report)
    assert f"**Observed:** {_markdown(display)} mm" in text
    assert "**Required:** 100.0 ± 0.2 mm" in text
    assert f"Recorded outcome: {'PASS' if state == 'pass' else 'HOLD'}" in text
    assert "six significant digits" in text
    assert (
        report.assessment.model_dump_json() == assessment.model_dump_json() == original
    )
    assert service.get_result(assessment.id).assessment.model_dump_json() == original
    assert {kind: export_report(report, kind).content for kind in exports} == exports
