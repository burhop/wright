from __future__ import annotations

import concurrent.futures

import pytest
from data_vault.workflow_continuation_repository import (
    WorkflowContinuationCheckpoint,
    WorkflowContinuationRepository,
    WorkflowContinuationStateConflict,
)


def checkpoint():
    return WorkflowContinuationCheckpoint(
        checkpoint_id="checkpoint-1",
        workspace_id="workspace-1",
        workflow_id="workflow-1",
        run_id="run-1",
        step_id="transfer",
        action_kind="printer_transfer",
        subject={"package": "a" * 64},
        subject_digest="b" * 64,
        state="pending",
        continuation={"next_step": "dispatch"},
        actor=None,
        reason=None,
        created_at=1,
        updated_at=1,
        expires_at=None,
        external_action=None,
    )


def test_checkpoint_round_trips_and_state_transition_is_compare_and_swap(tmp_path):
    repository = WorkflowContinuationRepository(str(tmp_path / "state.db"))
    repository.create(checkpoint())
    approved = repository.transition(
        "checkpoint-1",
        expected_state="pending",
        state="approved",
        updated_at=2,
        actor="local-user",
    )
    assert approved.state == "approved"
    assert repository.get("checkpoint-1") == approved
    with pytest.raises(WorkflowContinuationStateConflict):
        repository.transition(
            "checkpoint-1",
            expected_state="pending",
            state="changes_requested",
            updated_at=3,
        )


def test_only_one_concurrent_consumer_can_record_dispatch_authority(tmp_path):
    repository = WorkflowContinuationRepository(str(tmp_path / "state.db"))
    repository.create(checkpoint())
    repository.transition(
        "checkpoint-1", expected_state="pending", state="approved", updated_at=2
    )

    def consume(index):
        return repository.transition(
            "checkpoint-1",
            expected_state="approved",
            state="consumed",
            updated_at=3,
            external_action={"action_id": f"action-{index}"},
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(consume, index) for index in range(2)]
    outcomes = []
    for future in futures:
        try:
            outcomes.append(future.result().state)
        except WorkflowContinuationStateConflict:
            outcomes.append("conflict")
    assert sorted(outcomes) == ["conflict", "consumed"]
