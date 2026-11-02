"""Derived-view fixture checks, not observations of a real customer."""

import base64
import hashlib
import json

import pytest

from scripts.synthetic_beta_testing.reports import STAGES, ReportError, audit_report
from scripts.synthetic_beta_testing.storyboard import export_storyboard


@pytest.fixture
def recorded_session(tmp_path):
    root = tmp_path / "session"
    root.mkdir()
    (root / "captures").mkdir()
    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a9N8AAAAASUVORK5CYII="
    )
    (root / "captures/screen.png").write_bytes(png)
    event = {
        "id": "e1",
        "session_id": "customer-1",
        "time": "2026-10-25T12:00:00Z",
        "action": {"tool": "desktop", "action": "screenshot"},
        "observed_result": "Fixture visible screen",
        "captures": [
            {"path": "captures/screen.png", "sha256": hashlib.sha256(png).hexdigest()}
        ],
    }
    (root / "events.jsonl").write_text(json.dumps(event) + "\n")
    stages = [
        {"id": stage, "status": "not_reached", "evidence_refs": []} for stage in STAGES
    ]
    report = {
        "schema_version": 1,
        "session_id": "customer-1",
        "outcome": "justified_stop",
        "expectation": "Expected setup guidance",
        "task": "Try the handle example",
        "accomplishment": "Reached fixture screen",
        "stopping_reason": "Could not continue",
        "positives": [],
        "uncertainties": [{"text": "Was setup complete?", "evidence_refs": ["e1"]}],
        "help": [],
        "stages": stages,
        "friction": [
            {
                "id": "f1",
                "stage": "setup",
                "impact": "blocked_progress",
                "observation": "No visible next action",
                "expected": "Setup guidance",
                "consequence": "Stopped",
                "interpretation": "I may need help",
                "suggestion": "Explain the next step",
                "evidence_refs": ["e1"],
            }
        ],
        "priorities": [{"finding_id": "f1", "recommendation": "Explain the next step"}],
    }
    verification = {
        "schema_version": 1,
        "session_id": "customer-1",
        "evaluator_session_id": "review-1",
        "events_sha256": hashlib.sha256(
            (root / "events.jsonl").read_bytes()
        ).hexdigest(),
        "stages": stages,
        "findings": [
            {
                "finding_id": "f1",
                "disposition": "supported",
                "evidence_refs": ["e1"],
                "reason": "Fixture support",
            }
        ],
    }
    (root / "report.json").write_text(json.dumps(report, indent=3) + "\n\n")
    (root / "verification.json").write_text(json.dumps(verification))
    (root / "audit.json").write_text(
        json.dumps(audit_report(report, root, verification=verification))
    )
    return root, report, verification


def test_storyboard_is_deterministic_and_preserves_all_source_bytes(
    recorded_session, tmp_path
):
    root, _, _ = recorded_session
    original = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}
    first = export_storyboard(root, tmp_path / "storyboard-a")
    second = export_storyboard(root, tmp_path / "storyboard-b")
    assert first == second
    assert first["frames"] == 5
    assert len(first["captures"]) == 1
    assert (tmp_path / "storyboard-a/storyboard.html").read_bytes() == (
        tmp_path / "storyboard-b/storyboard.html"
    ).read_bytes()
    assert all(path.read_bytes() == content for path, content in original.items())
    asset = first["captures"][0]
    assert (
        hashlib.sha256(
            (tmp_path / "storyboard-a" / asset["path"]).read_bytes()
        ).hexdigest()
        == asset["sha256"]
    )


def test_customer_feedback_is_escaped_not_executed(recorded_session, tmp_path):
    root, report, verification = recorded_session
    report["expectation"] = (
        '<script>alert("unsafe")</script><img src="https://private.invalid/">'
    )
    report["priorities"][0]["recommendation"] = (
        '<iframe src="file:///etc/passwd"></iframe>'
    )
    (root / "report.json").write_text(json.dumps(report))
    (root / "audit.json").write_text(
        json.dumps(audit_report(report, root, verification=verification))
    )
    export_storyboard(root, tmp_path / "output")
    html = (tmp_path / "output/storyboard.html").read_text()
    assert "<script>" not in html
    assert '<img src="https:' not in html
    assert "<iframe" not in html
    assert "&lt;script&gt;" in html


def test_tampered_capture_cannot_be_exported(recorded_session, tmp_path):
    root, _, _ = recorded_session
    (root / "captures/screen.png").write_bytes(b"tampered")
    with pytest.raises(ReportError, match="digest mismatch"):
        export_storyboard(root, tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_cross_session_path_cannot_become_a_storyboard_asset(
    recorded_session, tmp_path
):
    root, _, _ = recorded_session
    event = json.loads((root / "events.jsonl").read_text())
    event["captures"][0]["path"] = "../other-session/screen.png"
    (root / "events.jsonl").write_text(json.dumps(event) + "\n")
    with pytest.raises(ReportError, match="unsafe capture"):
        export_storyboard(root, tmp_path / "output")


def test_stale_audit_cannot_support_a_storyboard(recorded_session, tmp_path):
    root, _, _ = recorded_session
    stale = json.loads((root / "audit.json").read_text())
    stale["disposition"] = "invented pass"
    (root / "audit.json").write_text(json.dumps(stale))
    with pytest.raises(ReportError, match="stale"):
        export_storyboard(root, tmp_path / "output")


def test_export_refuses_overwriting_existing_views(recorded_session, tmp_path):
    root, _, _ = recorded_session
    export_storyboard(root, tmp_path / "output")
    with pytest.raises(ReportError, match="fresh"):
        export_storyboard(root, tmp_path / "output")


def test_v2_storyboard_distinguishes_task_accomplishment_from_target_progress(
    recorded_session, tmp_path
):
    root, report, verification = recorded_session
    report["outcome"] = "independent_completion"
    report["accomplishment"] = (
        "The lost choice was restored; final guidance was reached."
    )
    verification["checkpoint_accomplishment"] = {
        "claim_disposition": "supported",
        "final_state_reached": True,
        "evidence_refs": ["e1"],
        "reason": "Disclosed restoration and final state are supported by fixture capture.",
    }
    verification["target_observation"] = {
        "issue_key": "registered-target",
        "present": True,
        "progressed": False,
        "evidence_refs": ["e1"],
    }
    (root / "customer-session.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "session_id": "customer-1",
                "observation_scope": "calibration_checkpoint_v2",
                "assistance": "none",
            }
        )
    )
    (root / "report.json").write_text(json.dumps(report))
    original = (root / "report.json").read_bytes()
    (root / "verification.json").write_text(json.dumps(verification))
    audit = audit_report(
        report,
        root,
        verification=verification,
        observation_scope="calibration_checkpoint_v2",
    )
    (root / "audit.json").write_text(json.dumps(audit))
    export_storyboard(root, tmp_path / "output")
    assert (
        "Separate checkpoint accomplishment"
        in (tmp_path / "output/storyboard.html").read_text()
    )
    assert (root / "report.json").read_bytes() == original
    assert audit["target_observation"]["progressed"] is False
