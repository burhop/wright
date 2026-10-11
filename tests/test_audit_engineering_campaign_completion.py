from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "campaign_completion",
    ROOT / "scripts/audit_engineering_campaign_completion.py",
)
completion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(completion)


def complete_documents():
    profile_ref = {"id": "profile", "version": "1", "sha256": "a" * 64}
    baseline_ref = {"id": "baseline", "version": "1", "sha256": "b" * 64}
    assessment = {
        "schema_version": "wright.process-validation/1",
        "assessment_id": "assessment-1",
        "assessment_digest": "c" * 64,
        "assessment_artifact": "_validation/assessment.json",
        "is_current": True,
        "full_scope": True,
        "release_eligible": True,
    }
    attempt = {
        "attempt_id": "attempt-001",
        "run_id": "run-1",
        "status": "completed",
        "dataset_digest": "d" * 64,
        "template_digest": "e" * 64,
        "accepted_by_runtime": True,
        "execution_kind": "integration",
        "required_step_ids": ["produce", "validate"],
        "completed_step_ids": ["produce", "validate"],
        "produced_files": [
            {
                "artifact_id": "artifact-1",
                "path": "result.json",
                "sha256": "f" * 64,
                "run_id": "run-1",
                "size_bytes": 10,
            }
        ],
        "completed_with_outputs": True,
        "output_check": {
            "passed": True,
            "missing_roles": [],
            "output_errors": [],
            "content_validated": True,
            "validation": {
                "status": "pass",
                "release_eligible": True,
                "assessments": [assessment],
            },
        },
        "integrity_check": {"mode": "full_audit", "last_hashed_at": "now"},
    }
    status = {
        "campaign_id": "campaign",
        "target": 1,
        "metrics": {name: 1 for name in completion.METRICS},
        "current_metrics": {
            "combinations_run": 1,
            "processes_with_outputs": 1,
            "valid_data": 1,
        },
        "validation_coverage": {"qualified": 1, "full_scope": 1, "unsupported": 0},
        "reconciliation": {"state": "current", "integrity_mode": "full_audit", "error": None},
        "issues": [],
        "datasets": [
            {
                "scenario_id": "case-01",
                "digest": "d" * 64,
                "template_digest": "e" * 64,
                "completed_current_revision": True,
                "latest_attempt": attempt,
            }
        ],
    }
    coverage = {
        "scenarios": [
            {
                "scenario_id": "case-01",
                "support_status": "qualified",
                "profile": {"profile_ref": profile_ref, "baseline_ref": baseline_ref},
                "campaign_credit": {
                    "full_scope": True,
                    "requirement_ids": ["REQ-1"],
                    "subject_roles": ["result"],
                },
            }
        ]
    }
    return status, coverage


def test_complete_audit_requires_every_current_identity_and_gate():
    status, coverage = complete_documents()

    report = completion.audit(status, coverage, target=1)

    assert report["status"] == "complete"
    assert report["summary"] == {
        "rows": 1,
        "passed": 1,
        "incomplete": 0,
        "global_blockers": [],
    }
    assert report["rows"][0]["status"] == "pass"
    assert "| case-01 | attempt-001 | run-1 | yes | yes | yes | pass |" in completion.markdown(report)


def test_missing_current_attempt_stays_explicitly_incomplete():
    status, coverage = complete_documents()
    status["datasets"][0]["latest_attempt"] = None
    status["datasets"][0]["completed_current_revision"] = False
    status["current_metrics"] = {
        "combinations_run": 0,
        "processes_with_outputs": 0,
        "valid_data": 0,
    }

    report = completion.audit(status, coverage, target=1)

    assert report["status"] == "incomplete"
    assert "current_metrics_not_complete" in report["summary"]["global_blockers"]
    assert report["rows"][0]["blockers"] == [
        "no_current_attempt",
        "attempt_not_current",
        "current_process_not_run",
        "current_outputs_incomplete",
        "required_process_steps_incomplete",
        "produced_file_identity_incomplete",
        "current_full_scope_assessment_not_passing",
        "current_output_bytes_not_full_audited",
    ]


def test_incremental_scan_or_failed_assessment_cannot_claim_completion():
    status, coverage = complete_documents()
    status["reconciliation"]["integrity_mode"] = "incremental"
    status["datasets"][0]["latest_attempt"]["output_check"]["validation"][
        "release_eligible"
    ] = False

    report = completion.audit(status, coverage, target=1)

    assert report["status"] == "incomplete"
    assert "campaign_full_audit_not_current" in report["summary"]["global_blockers"]
    assert "current_full_scope_assessment_not_passing" in report["rows"][0]["blockers"]


def test_attempt_from_an_old_dataset_revision_cannot_pass():
    status, coverage = complete_documents()
    changed = copy.deepcopy(status)
    changed["datasets"][0]["latest_attempt"]["dataset_digest"] = "9" * 64

    report = completion.audit(changed, coverage, target=1)

    assert report["status"] == "incomplete"
    assert "attempt_not_current" in report["rows"][0]["blockers"]
