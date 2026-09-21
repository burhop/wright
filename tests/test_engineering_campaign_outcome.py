"""Native cleanup must not turn a human-review boundary into a failed attempt."""

import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "campaign_outcome", Path(__file__).resolve().parents[1] / "scripts/engineering_campaign_outcome.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def evaluate(phase="completed", runtime="completed", **changes):
    row = {"scenario_id": "printed-replacement-part-01", "attempt_id": "attempt-017", "phase": phase,
           "content_validated": False, "validations": [{"verdict": "failed"}]}
    state = {"phase": phase, "runtime_status": runtime, "active_operation": None, "run_id": "actual-run"}
    state.update(changes)
    return MODULE.single_attempt_outcome({"cases": [row]}, state, row["scenario_id"], row["attempt_id"])


def test_additional_summary_fields_do_not_misclassify_completed_execution():
    assert evaluate() == {"outcome": "succeeded", "cleanup_allowed": True, "workflow_completed": True}
    # Workflow completion does not invent content-validation credit.
    assert "content_validated" not in evaluate()


@pytest.mark.parametrize("phase,runtime", [
    ("awaiting_manual_approval", "awaiting_approval"),
    ("outcome_unknown", "running"),
    ("runner_blocked", "running"),
    ("completed", "running"),
    ("observing", "completed"),
])
def test_nonterminal_or_conflicting_evidence_retains_native_resource(phase, runtime):
    assert evaluate(phase, runtime) == {"outcome": "unknown", "cleanup_allowed": False, "workflow_completed": False}


@pytest.mark.parametrize("phase", ["failed", "blocked", "changes_requested", "external_action_not_dispatched"])
def test_known_terminal_failure_allows_cleanup(phase):
    assert evaluate(phase, phase) == {"outcome": "failed", "cleanup_allowed": True, "workflow_completed": False}


def test_rejected_evidence_does_not_claim_success_but_terminal_runtime_can_be_cleaned():
    assert evaluate("evidence_rejected", "completed")["outcome"] == "failed"
    assert evaluate("evidence_rejected", "completed")["cleanup_allowed"] is True


@pytest.mark.parametrize("changes", [{"active_operation": "resume:checkpoint"}, {"run_id": None}, {"phase": "failed"}])
def test_unresolved_operation_or_mismatched_state_prevents_cleanup(changes):
    assert evaluate(**changes)["cleanup_allowed"] is False


@pytest.mark.parametrize("summary", [{}, {"cases": []}, {"cases": [None]}, {"cases": [{}, {}]}, {"cases": [{"scenario_id": "foreign", "attempt_id": "attempt-017", "phase": "completed"}]}])
def test_summary_identity_must_be_exact(summary):
    state = {"phase": "completed", "runtime_status": "completed", "run_id": "run"}
    assert MODULE.single_attempt_outcome(summary, state, "printed-replacement-part-01", "attempt-017")["cleanup_allowed"] is False
