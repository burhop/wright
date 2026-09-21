"""Fail-closed native cleanup classification for a single campaign attempt.

Runner summaries contain additional validation fields. Compare their identity
and phase, not the entire dictionary, and require durable terminal state before
letting a wrapper shut down a native resource.
"""

from __future__ import annotations


def single_attempt_outcome(summary, state, scenario_id, attempt_id):
    """Return lifecycle outcome/cleanup permission without awarding validation credit."""
    result = {"outcome": "unknown", "cleanup_allowed": False, "workflow_completed": False}
    rows = summary.get("cases") if isinstance(summary, dict) else None
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        return result
    row = rows[0]
    if row.get("scenario_id") != scenario_id or row.get("attempt_id") != attempt_id:
        return result
    if not isinstance(state, dict) or row.get("phase") != state.get("phase"):
        return result
    if state.get("active_operation") is not None or not state.get("run_id"):
        return result
    runtime_status = state.get("runtime_status")
    if runtime_status not in {
        "completed", "failed", "blocked", "changes_requested",
        "external_action_not_dispatched",
    }:
        return result
    if row.get("phase") not in {
        "completed", "failed", "blocked", "changes_requested",
        "external_action_not_dispatched", "evidence_rejected",
    }:
        return result
    if row["phase"] != runtime_status and row["phase"] != "evidence_rejected":
        return result
    completed = row["phase"] == runtime_status == "completed"
    return {
        "outcome": "succeeded" if completed else "failed",
        "cleanup_allowed": True,
        "workflow_completed": completed,
    }
