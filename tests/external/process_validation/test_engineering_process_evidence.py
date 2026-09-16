"""Independent checks for the retained engineering validation demonstrations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from core.process_validation import Assessment, RepairFeedback, canonical_digest


REPOSITORY = Path(__file__).parents[3]
EVIDENCE_ROOT = (
    REPOSITORY
    / "artifacts/process-validation/engineering/20260916T213859Z"
)
PROCESS_ROOT = REPOSITORY / "tests/datasets/process-validation/processes"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assessment(process: str, record: dict) -> Assessment:
    path = EVIDENCE_ROOT / process / "workspace" / record["path"]
    assessment = Assessment.model_validate_json(path.read_bytes())
    assert assessment.id == record["id"]
    assert canonical_digest(assessment) == record["digest"]
    return assessment


def _measurement_values(assessment: Assessment) -> dict[str, object]:
    return {item.selector: item.value for item in assessment.measurements}


def test_retained_engineering_evidence_is_complete_and_untampered():
    manifest = _json(EVIDENCE_ROOT / "manifest.json")
    listed = {item["path"]: item for item in manifest["files"]}
    actual = {
        path.relative_to(EVIDENCE_ROOT).as_posix(): path
        for path in EVIDENCE_ROOT.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }

    assert manifest["schema_version"] == 1
    assert set(actual) == set(listed)
    for relative, path in actual.items():
        assert listed[relative]["bytes"] == path.stat().st_size
        assert listed[relative]["sha256"] == _sha256(path)

    assert not list(EVIDENCE_ROOT.rglob("*.sqlite3*"))
    assert not list(EVIDENCE_ROOT.rglob(".git"))


def test_jig_run_proves_real_ai_mcp_correction_and_current_revision_release():
    root = _json(EVIDENCE_ROOT / "evidence.json")
    evidence = root["jig"]
    source = PROCESS_ROOT / "jig-validation-loop.workflow.wflow"
    retained_source = EVIDENCE_ROOT / "jig/workspace" / source.name

    assert root["demonstration"] == "process-output-validation-engineering"
    assert root["assertions"] == {
        "jig": True,
        "heat": True,
        "generation_campaign_unchanged": True,
    }
    assert evidence["demonstration"] == "real-ai-mcp-jig-correction"
    assert evidence["workflow_sha256"] == _sha256(source) == _sha256(retained_source)
    assert evidence["model_runtime"]["health"]["status"] == "ok"
    assert evidence["model_usage"]
    assert any(item["status"] == "reported" for item in evidence["model_usage"])
    assert all(evidence["assertions"].values())

    records = evidence["assessments"]
    assessments = [_assessment("jig", record) for record in records]
    assert [item.summary.release_eligible for item in assessments] == [False, True]
    assert [item.request.subjects[0].producer.attempt for item in assessments] == [1, 2]
    old_subject = assessments[0].request.subjects[0]
    new_subject = assessments[1].request.subjects[0]
    assert old_subject.id != new_subject.id
    assert old_subject.sha256 != new_subject.sha256

    assert {finding.check_id for finding in assessments[0].findings} == {
        "h1-seat-center-x",
        "h2-seat-center-x",
    }
    first_values = _measurement_values(assessments[0])
    final_values = _measurement_values(assessments[1])
    assert first_values["seat/H1/center_x_mm"] == 31
    assert first_values["seat/H2/center_x_mm"] == 171
    assert final_values == {
        "seat/H1/center_x_mm": 30.0,
        "seat/H1/center_y_mm": 30.0,
        "seat/H1/diameter_mm": 10.2,
        "seat/H2/center_x_mm": 170.0,
        "seat/H2/center_y_mm": 30.0,
        "seat/H2/diameter_mm": 10.2,
    }
    assert not assessments[1].findings

    attempts = evidence["producer_attempts"]
    assert [item["attempt"] for item in attempts] == [1, 2]
    assert [item["tool_calls"][0]["status"] for item in attempts] == [
        "succeeded",
        "succeeded",
    ]
    assert [item["tool_calls"][0]["arguments"] for item in attempts] == [
        {"h1_x_mm": 31, "h2_x_mm": 171, "output_path": "jig.step"},
        {"h1_x_mm": 30, "h2_x_mm": 170, "output_path": "jig.step"},
    ]
    feedback = RepairFeedback.model_validate(attempts[1]["repair_feedback"])
    assert feedback.assessment_id == assessments[0].id
    assert feedback.target_step_id == "produce"
    assert {finding.observed for finding in feedback.findings} == {31.0, 171.0}
    assert all(
        finding.correction.target_step_id == "produce"
        for finding in feedback.findings
    )

    snapshots = evidence["snapshots"]
    assert [item["attempt"] for item in snapshots] == [1, 2]
    assert [item["sha256"] for item in snapshots] == [
        old_subject.sha256,
        new_subject.sha256,
    ]
    for snapshot in snapshots:
        path = EVIDENCE_ROOT / "jig" / snapshot["path"]
        assert snapshot["bytes"] == path.stat().st_size
        assert snapshot["sha256"] == _sha256(path)

    result = _json(EVIDENCE_ROOT / "jig/result.json")
    assert result["status"] == "completed"
    assert result["steps"][-1]["task_id"] == "consume"
    assert evidence["feedback_delivery"][0]["assessment_id"] == assessments[0].id
    assert evidence["feedback_delivery"][0]["target_step_id"] == "produce"


def test_heat_run_proves_real_bound_artifacts_and_independent_measurements():
    evidence = _json(EVIDENCE_ROOT / "evidence.json")["heat"]
    source = PROCESS_ROOT / "heat-validation.workflow.wflow"
    retained_source = EVIDENCE_ROOT / "heat/workspace" / source.name

    assert evidence["demonstration"] == "mcp-heat-output-validation"
    assert evidence["workflow_sha256"] == _sha256(source) == _sha256(retained_source)
    assert evidence["model_runtime"]["health"]["status"] == "ok"
    assert evidence["model_usage"]
    assert all(evidence["assertions"].values())

    assert len(evidence["staged_inputs"]) == 5
    for item in evidence["staged_inputs"]:
        staged = EVIDENCE_ROOT / "heat/workspace" / item["workspace_path"]
        retained = REPOSITORY / item["retained_path"]
        assert item["bytes"] == staged.stat().st_size
        assert item["sha256"] == _sha256(staged)
        assert item["sha256"] == _sha256(retained)

    record = evidence["assessments"][0]
    assessment = _assessment("heat", record)
    assert assessment.summary.release_eligible
    assert assessment.summary.counts == {
        "pass": 15,
        "fail": 0,
        "blocked": 0,
        "inconclusive": 0,
        "error": 0,
        "not_applicable": 0,
    }
    assert not assessment.findings
    assert len(assessment.request.subjects) == 5
    assert len(assessment.measurements) == 15
    assert {item.reader.id for item in assessment.measurements} == {"thermal-field"}
    assert {item.reader.method for item in assessment.measurements} == {
        "independent_measurement"
    }
    values = _measurement_values(assessment)
    assert values["decision/selected_case_id"] == "revision_60"
    assert values["field/maximum_temperature_c"] < 45

    result = _json(EVIDENCE_ROOT / "heat/result.json")
    assert result["status"] == "completed"
    assert result["steps"][-1]["task_id"] == "consume"
    assert not evidence["feedback_delivery"]
