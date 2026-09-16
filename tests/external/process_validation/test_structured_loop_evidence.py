"""Independent checks for the retained real-model structured correction run."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from core.process_validation import Assessment, RepairFeedback, canonical_digest


REPOSITORY = Path(__file__).parents[3]
EVIDENCE_ROOT = (
    REPOSITORY
    / "artifacts/process-validation/structured-loop/20260916T202647Z"
)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_retained_structured_loop_evidence_is_complete_and_untampered():
    manifest = _json(EVIDENCE_ROOT / "manifest.json")
    listed = {item["path"]: item for item in manifest["files"]}
    actual = {
        path.relative_to(EVIDENCE_ROOT).as_posix(): path
        for path in EVIDENCE_ROOT.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }

    assert set(actual) == set(listed)
    for relative, path in actual.items():
        assert listed[relative]["bytes"] == path.stat().st_size
        assert listed[relative]["sha256"] == _sha256(path)

    assert not (EVIDENCE_ROOT / "runtime.sqlite3").exists()
    assert not (EVIDENCE_ROOT / "workspace/.git").exists()


def test_retained_structured_loop_proves_real_bounded_correction_and_release():
    evidence = _json(EVIDENCE_ROOT / "evidence.json")
    source = REPOSITORY / (
        "tests/datasets/process-validation/processes/structured-loop.workflow.wflow"
    )
    retained_source = EVIDENCE_ROOT / "workspace/structured-loop.workflow.wflow"

    assert evidence["demonstration"] == "ordinary-ai-structured-output-correction"
    assert evidence["workflow_sha256"] == _sha256(source) == _sha256(retained_source)
    assert evidence["model_runtime"]["health"]["status"] == "ok"
    assert evidence["model_runtime"]["models"] == ["hermes-agent"]
    assert len(evidence["model_usage"]) == 3
    assert all(item["status"] == "reported" for item in evidence["model_usage"])
    assert all(evidence["assertions"].values())

    assessment_records = evidence["assessments"]
    assessments = [
        Assessment.model_validate_json(
            (EVIDENCE_ROOT / "workspace" / record["path"]).read_bytes()
        )
        for record in assessment_records
    ]
    assert [item.summary.release_eligible for item in assessments] == [False, True]
    assert [item.request.subjects[0].producer.attempt for item in assessments] == [1, 2]
    assert assessments[0].request.subjects[0].id != assessments[1].request.subjects[0].id
    assert assessments[0].request.subjects[0].sha256 != assessments[1].request.subjects[0].sha256
    for record, assessment in zip(assessment_records, assessments, strict=True):
        assert record["id"] == assessment.id
        assert record["digest"] == canonical_digest(assessment)

    attempts = evidence["producer_attempts"]
    assert [item["response"]["length_mm"] for item in attempts] == [98, 100]
    feedback = RepairFeedback.model_validate(attempts[1]["repair_feedback"])
    assert feedback.assessment_id == assessments[0].id
    assert feedback.target_step_id == "produce"
    assert feedback.findings[0].observed == 98
    assert feedback.findings[0].correction.target_step_id == "produce"
    assert evidence["consumer"]["saved_response"]["output_path"] == "release-note.txt"

