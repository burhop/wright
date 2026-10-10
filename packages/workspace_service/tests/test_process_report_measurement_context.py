"""Reports expose recorded uncertainty and review obligations without evaluation."""

import csv
import io
import json

import pytest

from core.process_validation import Constraint, canonical_digest
from workspace_service.process_validation.reporting import (
    export_report,
    render_readable_markdown,
)
from .test_process_validation_reporting import _profile, _request, _service


def measured_report(
    tmp_path,
    value,
    uncertainty,
    *,
    operator="within",
    reader="structured",
    unit=None,
    frame=None,
):
    profile = _profile(review=True)
    check = profile.checks[0].model_copy(
        update={
            "reader": reader,
            "parameters": {
                "uncertainty_pointer": "/allowance",
                **({"unit_pointer": "/unit"} if unit else {}),
                **({"frame_pointer": "/frame"} if frame else {}),
            },
            "frame": frame,
            **(
                {"constraint": Constraint(operator="equals", expected=True)}
                if operator == "equals"
                else {}
            ),
        }
    )
    profile = profile.model_copy(update={"checks": (check, profile.checks[1])})
    request = _request(profile, length=value)
    data = {"length_mm": value, "allowance": uncertainty, "unit": unit, "frame": frame}
    subject = request.subjects[0].model_copy(
        update={"value": data, "sha256": canonical_digest(data)}
    )
    request = request.model_copy(update={"subjects": (subject,)})
    service = _service(tmp_path)
    assessment = service.evaluate(request, profile).assessment
    return service, service.get_result(assessment.id)


@pytest.mark.parametrize(
    "value,uncertainty,state",
    [
        (100, 0.0, "pass"),
        (100, 0.1, "pass"),
        (100.2, 0.01, "inconclusive"),
        (101, 0.01, "fail"),
    ],
)
def test_readable_and_exported_reports_keep_actual_allowances_and_review(
    tmp_path, value, uncertainty, state
):
    service, report = measured_report(tmp_path, value, uncertainty)
    original = report.assessment.model_dump_json()
    json_before = export_report(report, "json").content
    assert report.traceability[0].check_state == state
    readable = render_readable_markdown(report)
    assert f"**Recorded uncertainty allowance:** {uncertainty} mm" in readable
    assert "**Review required by requirement:** Yes" in readable
    assert "**Review required by requirement:** No" in readable
    assert "Zero can be a default" in readable
    assert "Recorded outcome: HOLD" in readable
    exported = export_report(report, "markdown").content.decode()
    assert "Uncertainty allowance" in exported and "Review required" in exported
    rows = list(
        csv.DictReader(io.StringIO(export_report(report, "csv").content.decode()))
    )
    assert rows[0]["review_required"] == "false"
    assert rows[1]["review_required"] == "true"
    measurements = {m.id: m for m in report.assessment.measurements}
    check = report.assessment.checks[0]
    entries = json.loads(rows[0]["measurement_uncertainties"])
    assert entries == [
        dict(
            measurement_id=m.id,
            uncertainty=m.uncertainty,
            unit=m.unit,
            frame=m.frame,
            numeric=type(m.value) in {int, float},
        )
        for m in (measurements[key] for key in check.measurement_ids)
    ]
    assert entries[0]["uncertainty"] == uncertainty
    assert rows[0]["status"] == state
    assert "Zero can be a default" in rows[0]["uncertainty_note"]
    assert json.loads(rows[1]["measurement_uncertainties"]) == []
    assert export_report(report, "json").content == json_before
    assert (
        service.get_result(report.assessment.id).assessment.model_dump_json()
        == original
    )


def test_missing_measurement_does_not_invent_zero_allowance(tmp_path):
    _, report = measured_report(tmp_path, 100, 0.1, reader="missing-reader")
    text = render_readable_markdown(report)
    assert "**Recorded uncertainty allowance:** No measurement recorded" in text
    rows = list(
        csv.DictReader(io.StringIO(export_report(report, "csv").content.decode()))
    )
    assert json.loads(rows[0]["measurement_uncertainties"]) == []
    assert rows[0]["status"] == "blocked"


def test_nonnumeric_observation_is_not_presented_as_zero_accuracy(tmp_path):
    _, report = measured_report(tmp_path, True, 0.0, operator="equals")
    text = render_readable_markdown(report)
    assert (
        "**Recorded uncertainty allowance:** Not applicable (non-numeric observation)"
        in text
    )
    rows = list(
        csv.DictReader(io.StringIO(export_report(report, "csv").content.decode()))
    )
    entry = json.loads(rows[0]["measurement_uncertainties"])[0]
    assert entry["numeric"] is False and entry["uncertainty"] == 0.0


def test_allowance_keeps_observed_units_and_datum_not_requirement_units(tmp_path):
    _, report = measured_report(tmp_path, 10.0, 0.01, unit="cm", frame="part-datum")
    assert report.traceability[0].check_state == "pass"
    text = render_readable_markdown(report)
    assert "**Required:** 100.0 ± 0.2 mm (frame: part-datum)" in text
    assert "**Observed:** 10.0 cm (frame: part-datum)" in text
    assert "**Recorded uncertainty allowance:** 0.01 cm (frame: part-datum)" in text
    rows = list(
        csv.DictReader(io.StringIO(export_report(report, "csv").content.decode()))
    )
    entry = json.loads(rows[0]["measurement_uncertainties"])[0]
    assert (
        entry["uncertainty"] == 0.01
        and entry["unit"] == "cm"
        and entry["frame"] == "part-datum"
    )
