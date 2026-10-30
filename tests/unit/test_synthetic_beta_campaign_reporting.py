"""Accounting boundaries; artificial events are not product evidence."""

import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
metrics = importlib.import_module("synthetic_beta_testing.campaign_reporting")


def event(task, status, minute, stage="implementation"):
    return {
        "id": task + "-" + status,
        "at": f"2026-10-25T12:{minute:02}:00Z",
        "kind": "activity",
        "feature": "fixture",
        "subject": "fixture-working-tree",
        "data": {
            "task": task,
            "stage": stage,
            "status": status,
            "summary": "Fixture task window",
        },
    }


def snapshot(events):
    return {"availability": "available", "truncated": False, "events": events}


def test_only_closed_windows_count_and_concurrent_lanes_stay_separate():
    records = [
        event("main", "started", 0),
        event("customer", "started", 0, "review"),
        event("main", "completed", 2),
        event("customer", "completed", 3, "review"),
        event("open", "started", 4),
    ]
    bindings = {
        "main": {"phase": "implementation", "lane": "implementer-main"},
        "customer": {"phase": "customer_validation", "lane": "customer-process"},
        "open": {"phase": "implementation", "lane": "implementer-main"},
    }
    result = metrics.project_activity(snapshot(records), bindings)
    assert {(x["lane"], x["seconds"]) for x in result["totals"]} == {
        ("implementer-main", 120),
        ("customer-process", 180),
    }
    assert len(result["open_windows"]) == 1
    assert "seconds" not in result["open_windows"][0]


def test_overlapping_work_cannot_be_counted_twice_in_one_lane():
    records = [
        event("a", "started", 0),
        event("b", "started", 1),
        event("a", "completed", 2),
        event("b", "completed", 3),
    ]
    bindings = {key: {"phase": "implementation", "lane": "main"} for key in ["a", "b"]}
    with pytest.raises(metrics.ReportError, match="overlapping activity"):
        metrics.project_activity(snapshot(records), bindings)


@pytest.mark.parametrize(
    "change", ["duplicate", "mislabeled", "unbound", "terminal-only", "truncated"]
)
def test_inconsistent_accounting_is_rejected(change):
    records = [event("a", "started", 0), event("a", "completed", 1)]
    data = snapshot(records)
    bindings = {"a": {"phase": "implementation", "lane": "main"}}
    if change == "duplicate":
        records.append(dict(records[0]))
    if change == "mislabeled":
        bindings["a"]["phase"] = "focused_validation"
    if change == "unbound":
        bindings = {}
    if change == "terminal-only":
        records.pop(0)
    if change == "truncated":
        data["truncated"] = True
    with pytest.raises(metrics.ReportError):
        metrics.project_activity(data, bindings)


def test_external_work_retains_problem_links_without_double_counting_categories():
    records = [event("a", "started", 0), event("a", "completed", 2)]
    binding = {
        "a": {
            "phase": "diagnosis",
            "lane": "main",
            "origin": "outside_loop",
            "issue_ids": ["browser-chat"],
            "categories": ["setup_access", "unclear_progress"],
        }
    }
    result = metrics.project_activity(snapshot(records), binding)
    assert result["totals"][0]["seconds"] == 120
    assert result["intervals"][0]["origin"] == "outside_loop"
    assert result["intervals"][0]["issue_ids"] == ["browser-chat"]
    binding["a"]["origin"] = "guess"
    with pytest.raises(metrics.ReportError):
        metrics.project_activity(snapshot(records), binding)
