"""Diagnostic projections use isolated evidence; they cannot award run credit."""

import json
import sqlite3
import threading
from types import SimpleNamespace

from scripts.engineering_dataset_diagnostics import build_diagnostics, native_diagnostics


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def campaign(tmp_path, receipts):
    path = tmp_path / "campaign.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE datasets(id TEXT,document TEXT)")
        db.execute("CREATE TABLE attempts(id TEXT,document TEXT)")
        db.execute("INSERT INTO datasets VALUES (?,?)", ("family-01", json.dumps({
            "scenario_id": "family-01", "template_id": "family", "digest": "current", "template_digest": "template",
        })))
        for index, receipt in enumerate(receipts):
            db.execute("INSERT INTO attempts VALUES (?,?)", (str(index), json.dumps(receipt)))
    return SimpleNamespace(db=path, lock=threading.RLock())


def receipt(**overrides):
    return {
        "scenario_id": "family-01", "attempt_id": "attempt-001", "run_id": "actual-run",
        "accepted_by_runtime": True, "execution_kind": "integration", "status": "failed",
        "dataset_digest": "current", "template_digest": "template",
        "started_at": "2026-09-13T00:00:00+00:00", **overrides,
    }


def test_only_unique_accepted_runtime_attempts_count_and_restart_is_read_only(tmp_path):
    ledger = campaign(tmp_path, [receipt(), receipt(), receipt(run_id=None),
                                 receipt(run_id="fixture", execution_kind="fixture"),
                                 receipt(run_id="unaccepted", accepted_by_runtime=False)])
    before = ledger.db.read_bytes()
    first = build_diagnostics(ledger, observed_at="2026-09-13T01:00:00+00:00")
    second = build_diagnostics(ledger, observed_at="2026-09-13T01:00:00+00:00")
    assert first == second
    assert ledger.db.read_bytes() == before
    assert first["accepted_attempts"] == 1
    assert first["scenarios"][0]["accepted_attempts"] == 1
    assert "metrics" not in first and "history" not in first
    assert first["scenarios"][0]["total_tokens"] is None
    assert first["scenarios"][0]["duration_seconds"] is None
    assert first["scenarios"][0]["attempts_since_fix"] is None
    assert not first["native"]["available"]


def test_stage_event_order_and_terminal_duration_observation(tmp_path):
    ledger = campaign(tmp_path, [receipt(error_code="TASK_BLOCKED", error="RoundedRectangle import failed", step_events=[
        {"kind": "step_started", "task_id": "cad", "at": "2026-09-13T00:05:01Z"},
        {"kind": "step_completed", "task_id": "author", "at": "2026-09-13T00:05:00Z"},
        {"kind": "step_started", "task_id": "author", "at": "2026-09-13T00:02:00Z"},
    ])])
    runners = tmp_path / "runner"
    write_json(runners / "family-01/attempt-001.json", {
        "phase": "blocked", "updated_at": "2026-09-13T00:06:00Z", "reason_code": "runtime_request_rejected",
    })
    row = build_diagnostics(ledger, runner_root=runners)["scenarios"][0]
    assert row["last_successful_stage"] == "author"
    assert row["current_or_failed_stage"] == "cad"
    assert row["stage_durations"] == [{"task_id": "author", "seconds": 180}]
    assert row["duration_seconds"] == 360
    assert "upper bound" in row["duration_source"]
    assert row["failure"]["category"] == "Source / SDK contract"
    assert row["failure"]["category_inferred"]


def test_historical_orphan_and_explicit_fixes_do_not_create_running_progress(tmp_path):
    ledger = campaign(tmp_path, [receipt(dataset_digest="old", status="running"),
                                 receipt(attempt_id="attempt-002", run_id="new-run", started_at="2026-09-13T02:00:00Z")])
    runners = tmp_path / "runner"
    write_json(runners / "family-01/attempt-001.json", {
        "phase": "outcome_unknown", "reason_code": "runtime_owner_missing",
    })
    runners.joinpath("pause-after-current").touch()
    journal = tmp_path / "recovery.json"
    write_json(journal, {"families": {"family": {
        "readiness": "failed probe", "queued_at": "2026-09-13T00:00:00Z",
        "fixes": [{"at": "2026-09-13T01:00:00Z", "evidence": "proof.json"},
                  {"at": "2026-09-13T02:30:00Z"}],
    }}})
    result = build_diagnostics(ledger, runner_root=runners, recovery_path=journal, observed_at="2026-09-13T03:00:00Z")
    assert result["accepted_attempts"] == 2
    assert result["runner"]["paused"]
    assert result["runner"]["worker_health"] == "unknown"
    assert len(result["unresolved_attempts"]) == 1
    assert result["unresolved_attempts"][0]["reason"] == "runtime_owner_missing"
    row = result["scenarios"][0]
    assert row["attempts_since_fix"] == 1
    assert row["fix_age_seconds"] == 7200
    assert row["queue_age_seconds"] == 10800
    assert row["readiness"] == "failed probe"


def test_completed_current_revision_and_last_completion_are_independent_of_cleanup(tmp_path):
    ledger = campaign(tmp_path, [receipt(status="completed", completed_with_outputs=True,
                                         finished_at="2026-09-13T00:10:00Z")])
    result = build_diagnostics(ledger, observed_at="2026-09-13T01:10:00Z")
    assert result["last_completion_at"] == "2026-09-13T00:10:00Z"
    assert result["since_last_completion_seconds"] == 3600
    assert result["families"][0]["completed"] == 1
    assert result["scenarios"][0]["readiness"] == "complete"
    assert result["scenarios"][0]["duration_seconds"] == 600
    assert result["native"]["available"] is False


def test_native_read_only_projection_filters_private_fields(tmp_path):
    path = tmp_path / "native.db"
    with sqlite3.connect(path) as db:
        for table in ("sessions", "leases", "cleanup"):
            db.execute(f"CREATE TABLE native_application_{table}(record TEXT)")
        db.execute("INSERT INTO native_application_sessions VALUES (?)", (json.dumps({
            "session_id": "owned-session", "app_kind": "blender", "ownership": "owned", "state": "idle",
            "identity": {"pid": 12, "creation_time": "2026-09-13T00:00:00Z", "executable": "/blender"},
            "launch_receipt": {"secret": "DO_NOT_EXPOSE"},
        }),))
        db.execute("INSERT INTO native_application_leases VALUES (?)", (json.dumps({
            "session_id": "owned-session", "lease_id": "lease", "state": "released", "case_id": "family-01",
        }),))
        db.execute("INSERT INTO native_application_cleanup VALUES (?)", (json.dumps({
            "session_id": "owned-session", "status": "cleanup_blocked", "reason": "owned work remains unsaved",
            "completed_at": "2026-09-13T01:00:00Z",
        }),))
    before = path.read_bytes()
    result = native_diagnostics(path, [])
    assert result["available"]
    assert result["sessions"][0]["cleanup"]["status"] == "cleanup_blocked"
    assert result["sessions"][0]["leases"][0]["state"] == "released"
    assert "DO_NOT_EXPOSE" not in json.dumps(result)
    assert path.read_bytes() == before


def test_torn_optional_json_does_not_break_ledger_projection(tmp_path):
    ledger = campaign(tmp_path, [receipt()])
    journal = tmp_path / "recovery.json"
    journal.write_text('{"families":', encoding="utf-8")
    result = build_diagnostics(ledger, recovery_path=journal)
    assert result["accepted_attempts"] == 1
    assert result["issues"]


def test_native_journal_path_updates_live_within_campaign_diagnostics(tmp_path, monkeypatch):
    ledger = campaign(tmp_path, [])
    journal = tmp_path / "recovery.json"
    observed = []
    monkeypatch.setattr("scripts.engineering_dataset_diagnostics.native_diagnostics",
                        lambda path, issues: observed.append(path) or {"available": False})
    for name in ("first.db", "second.db"):
        write_json(journal, {"native_database_path": "diagnostics/" + name})
        build_diagnostics(ledger, recovery_path=journal)
    assert observed == [(tmp_path / "diagnostics" / name).resolve() for name in ("first.db", "second.db")]
    write_json(journal, {"native_database_path": "../unrelated.db"})
    result = build_diagnostics(ledger, recovery_path=journal)
    assert observed[-1] is None
    assert result["issues"]
