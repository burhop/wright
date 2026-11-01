"""Synthetic clock fixtures, not customer observations."""

import copy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from synthetic_beta_testing.journey import (
    JourneyRecorder,
    project,
    read_events,
    validate_plan,
)
from synthetic_beta_testing.reports import ReportError

PLAN = {
    "schema_version": 1,
    "id": "fixture",
    "label": "Fixture job",
    "target_seconds": 1200,
    "steps": [
        {"id": "install", "label": "Install", "target_seconds": 10},
        {"id": "result", "label": "Receive result"},
    ],
}


@pytest.fixture
def clock(tmp_path, monkeypatch):
    seconds = [1000.0]
    monkeypatch.setattr(
        "synthetic_beta_testing.journey.time.monotonic", lambda: seconds[0]
    )
    recorder = JourneyRecorder.begin(tmp_path, copy.deepcopy(PLAN))
    return recorder, seconds


def result(recorder):
    return project(recorder.plan, read_events(recorder.root))


def test_retries_gaps_and_blocked_time_are_preserved(clock):
    r, t = clock
    t[0] += 3
    r.step("install", "started")
    t[0] += 9
    r.step("install", "blocked", "No connection", ["setup_access"])
    t[0] += 2
    r.step("install", "started")
    t[0] += 6
    r.step("install", "completed")
    t[0] += 1
    r.finish()
    p = result(r)
    assert p["elapsed_seconds"] == 21
    assert p["unassigned_seconds"] == 6
    assert p["steps"][0]["seconds"] == 15
    assert p["steps"][0]["retry_count"] == 1
    assert p["steps"][0]["over_target"]
    assert [v["status"] for v in p["steps"][0]["visits"]] == ["blocked", "completed"]
    assert p["steps"][1]["seconds"] is None
    assert p["steps"][1]["status"] == "not_attempted"
    assert len(p["issues"]) == 1


def test_open_and_aborted_steps_cannot_become_success(clock):
    r, t = clock
    r.step("result", "started", actor="customer")
    assert result(r)["steps"][1]["seconds"] is None
    assert not result(r)["finished"]
    t[0] += 25
    r.finish()
    assert result(r)["steps"][1]["status"] == "interrupted"
    assert result(r)["steps"][1]["seconds"] == 25
    assert not result(r)["issues"]


@pytest.mark.parametrize(
    "operation", ["overlap", "wrong_finish", "unknown", "bad_category", "backwards"]
)
def test_invalid_recording_cannot_mutate_log(clock, operation):
    r, t = clock
    r.step("install", "started")
    before = r.path.read_bytes()
    with pytest.raises(ReportError):
        if operation == "overlap":
            r.step("result", "started")
        if operation == "wrong_finish":
            r.step("result", "completed")
        if operation == "unknown":
            r.step("unplanned", "completed")
        if operation == "bad_category":
            r.step("install", "blocked", categories=["invented"])
        if operation == "backwards":
            t[0] -= 1
            r.finish()
    assert r.path.read_bytes() == before


def test_frozen_plan_and_terminal_clock_cannot_be_replaced(clock):
    r, _ = clock
    with pytest.raises(ReportError):
        JourneyRecorder.begin(r.root, PLAN)
    changed = copy.deepcopy(PLAN)
    changed["steps"][0]["label"] = "Changed task"
    with pytest.raises(ReportError, match="frozen plan"):
        project(changed, read_events(r.root))
    r.finish()
    with pytest.raises(ReportError, match="follows its end"):
        r.step("result", "started")


def test_different_journeys_have_different_steps_and_targets():
    plan = {
        "schema_version": 1,
        "id": "reopen",
        "label": "Return to saved work",
        "steps": [{"id": "open", "label": "Open existing workspace"}],
    }
    assert validate_plan(plan) == plan
    plan["steps"].append(dict(plan["steps"][0]))
    with pytest.raises(ReportError):
        validate_plan(plan)
