"""Correction summaries do not replace or mutate exact assessment findings."""

from types import SimpleNamespace

from workspace_service.process_validation.process import _correction_explanations


def test_repeated_cause_does_not_hide_a_later_distinct_correction():
    explanations = ["Cannot read inspection data."] * 25 + [
        "The drawing belongs to a different revision.",
        "Cannot read inspection data.",
    ]
    findings = [
        SimpleNamespace(explanation=text, check_id=str(i))
        for i, text in enumerate(explanations)
    ]
    assert _correction_explanations(findings) == [
        "Cannot read inspection data.",
        "The drawing belongs to a different revision.",
    ]
    assert [finding.explanation for finding in findings] == explanations
    assert [finding.check_id for finding in findings] == list(map(str, range(27)))


def test_distinct_corrections_keep_the_existing_limit_and_order():
    explanations = [f"Check {i} requires more evidence." for i in range(23)]
    findings = [SimpleNamespace(explanation=text) for text in explanations]
    assert _correction_explanations(findings) == explanations[:20]


def test_similar_wording_is_not_reinterpreted_or_normalized():
    explanations = ["Length is 10 mm.", "Length is 10 m.", "length is 10 mm."]
    assert (
        _correction_explanations(
            [SimpleNamespace(explanation=text) for text in explanations]
        )
        == explanations
    )


def test_no_findings_has_no_correction():
    assert _correction_explanations([]) == []
