"""Recorded provider facts feed the same bounded process projection."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json

import pytest

from core.process_interactions import Action
from workspace_service.process_interfaces.projection import (
    project_interactions,
    project_operation_observations,
)
from workspace_service.workflow_run_record import _execution_snapshot
from packages.workspace_service.tests.test_process_interaction_projection import (
    facts,
    run,
    scope,
)
from packages.workspace_service.tests.test_process_interaction_owners import (
    application,
    reference,
    scope as owner_scope,
)
from packages.workspace_service.tests.test_workflow_approval_execution import setup_case

STAMP = "2026-09-30T12:00:00Z"
CURRENT = "2026-09-30T12:00:01Z"
EXPIRED = "2026-09-30T12:01:00Z"


def event(state="working", **changes):
    return {
        "kind": "operation_progress",
        "task_id": "analysis",
        "provider_binding": "independent-solver",
        "operation_id": "job-123",
        "provider_schema_digest": "a" * 64,
        "state": state,
        "observed_at": STAMP,
        "stale_after": "2026-09-30T12:00:30Z",
        "observation_source": "provider_status",
        "progress_percent": 45,
        "estimated_remaining_seconds": 20,
        "metrics": {"iteration": 4},
        "message": "Solving",
        "limitations": [],
        **changes,
    }


def projected(*events, at=CURRENT, status="running", **record):
    execution, _, _ = _execution_snapshot({"events": events, **record}, status)
    observations = project_operation_observations(execution, at)
    action = Action(
        action_id="submit",
        title="Submit operation",
        operation="action",
        subject_digest="b" * 64,
        enabled=True,
    )
    snapshot = project_interactions(
        replace(
            facts(run=run(status), observations=observations, actions=(action,)),
            generated_at=at,
        ),
        scope(),
    )
    return execution, snapshot


def test_latest_identity_bound_observation_retains_timestamp_and_nulls():
    execution, view = projected(
        event(), event(progress_percent=None, estimated_remaining_seconds=None)
    )
    assert len(execution["operations"]) == 1
    assert view.state == "running"
    observed = view.observations[0]
    assert observed.operation_id == "job-123"
    assert observed.provider_binding == "independent-solver"
    assert observed.observed_at == STAMP
    assert observed.progress_percent is None
    assert observed.estimated_remaining_seconds is None
    assert observed.metrics["iteration"] == 4
    assert observed.metrics["provider_schema_digest"] == "a" * 64


def test_stale_active_observation_requires_reconciliation_and_disables_submission():
    _, view = projected(event(), at=EXPIRED)
    assert view.state == "reconciliation_required"
    assert view.observations[0].observed_at == STAMP
    assert view.observations[0].progress_percent is None
    assert view.observations[0].estimated_remaining_seconds is None
    assert view.observations[0].limitations
    assert not view.actions[0].enabled
    assert view.actions[0].reasons[0].code == "OUTCOME_UNKNOWN"


@pytest.mark.parametrize(
    "state,expected",
    [
        ("submitted", "waiting_external"),
        ("cancellation_requested", "cancellation_requested"),
        ("cancelled", "cancelled"),
        ("completed", "completed"),
        ("cancellation_unconfirmed", "reconciliation_required"),
        ("input_required", "reconciliation_required"),
    ],
)
def test_request_and_observed_outcome_have_different_meanings(state, expected):
    _, view = projected(event(state))
    assert view.observations[0].state == expected
    if state == "input_required":
        assert (
            not view.interactions
        )  # Never invent a human question from provider status.


def test_completed_fact_remains_historical_without_refreshing_its_time():
    _, view = projected(event("completed"), at=EXPIRED, status="completed")
    assert view.state == "completed"
    assert view.observations[0].observed_at == STAMP
    assert view.observations[0].progress_percent == 45  # No manufactured 100%.


@pytest.mark.parametrize(
    "change",
    [
        {"operation_id": None},
        {"provider_schema_digest": "unknown"},
        {"observed_at": None},
        {"observed_at": "2099-01-01T00:00:00Z"},
        {"stale_after": STAMP},
        {"observed_at": "invalid"},
    ],
)
def test_unverifiable_history_never_becomes_fresh_provider_success(change):
    _, view = projected(event("completed", **change), status="completed")
    assert view.state == "reconciliation_required"
    assert view.observations[-1].observation_id == "unverified-provider-history"
    assert view.observations[-1].operation_id is None


def test_run_ended_but_provider_still_working_requires_reconciliation():
    _, view = projected(event(), status="cancelled")
    assert view.state == "reconciliation_required"
    assert view.observations[0].state == "running"
    assert not view.actions[0].enabled


def test_operation_fold_is_bounded_and_never_exposes_raw_tool_payload():
    execution, view = projected(
        *[
            event(
                operation_id=f"job-{i}",
                metrics={"detail": "x" * 4096},
                arguments={"secret": "private"},
                result="private",
            )
            for i in range(300)
        ]
    )
    assert execution["operations_truncated"]
    assert len(json.dumps(execution).encode()) <= 65_536
    assert view.state == "reconciliation_required"
    assert "private" not in view.model_dump_json()
    assert view.observations[-1].observation_id == "unverified-provider-history"


@pytest.mark.asyncio
async def test_real_run_owner_reopen_reads_same_provider_facts_without_poll_or_mutation(
    tmp_path,
):
    case = await setup_case(tmp_path)
    app = application(case.services, tmp_path)
    path = tmp_path / case.result["run_log_path"]
    record = json.loads(path.read_bytes())
    now = datetime.now(timezone.utc)
    recorded = event(
        "completed",
        observed_at=(now - timedelta(seconds=1)).isoformat(),
        stale_after=(now + timedelta(seconds=60)).isoformat(),
    )
    record["events"].append(recorded)
    path.write_text(json.dumps(record), encoding="utf-8")
    original = path.read_bytes()
    calls = list(case.calls)
    first = await app.get_snapshot(
        owner_scope(),
        reference(tmp_path, case.checkpoint.workflow_id),
        run_id=case.result["run_id"],
    )
    reopened = application(case.services, tmp_path)
    second = await reopened.get_snapshot(
        owner_scope(),
        reference(tmp_path, case.checkpoint.workflow_id),
        run_id=case.result["run_id"],
    )
    assert first.observations[1] == second.observations[1]
    assert first.observations[1].observed_at == recorded["observed_at"]
    assert first.observations[1].operation_id == "job-123"
    assert path.read_bytes() == original
    assert case.calls == calls
