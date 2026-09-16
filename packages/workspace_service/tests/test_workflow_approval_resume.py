from __future__ import annotations

import pytest
from data_vault import WorkflowContinuationRepository
from workspace_service.workflow_external_actions import (
    WorkflowExternalActionError,
    WorkflowExternalActionService,
    approval_subject_digest,
)


def subject(**changes):
    value = {
        "definition_digest": "a" * 64,
        "input_digests": ["b" * 64],
        "artifact_digests": ["c" * 64],
        "binding": {"server": "slicer", "tool": "slice", "schema": "d" * 64},
        "destination": {"kind": "printer", "id": "bambu-p1s-01"},
        "settings": {"material": "PLA", "profile": "0.20-standard"},
        "action": {"kind": "printer_transfer", "package": "c" * 64},
    }
    value.update(changes)
    return value


def service(tmp_path):
    return WorkflowExternalActionService(
        WorkflowContinuationRepository(str(tmp_path / "state.db"))
    )


def request(service):
    return service.request(
        workspace_id="workspace-1",
        workflow_id="workflow-1",
        run_id="run-1",
        step_id="transfer",
        action_kind="printer_transfer",
        subject=subject(),
        continuation={"next_step": "transfer"},
    )


def test_approval_is_bound_to_every_exact_subject_component(tmp_path):
    baseline = approval_subject_digest(subject())
    mutations = [
        subject(definition_digest="0" * 64),
        subject(input_digests=["0" * 64]),
        subject(artifact_digests=["0" * 64]),
        subject(binding={"server": "other", "tool": "slice", "schema": "d" * 64}),
        subject(destination={"kind": "printer", "id": "another"}),
        subject(settings={"material": "PETG", "profile": "0.20-standard"}),
        subject(action={"kind": "printer_transfer", "package": "0" * 64}),
    ]
    assert all(approval_subject_digest(value) != baseline for value in mutations)


def test_approved_subject_is_consumed_once_and_records_no_dispatch_yet(tmp_path):
    actions = service(tmp_path)
    pending = request(actions)
    approved = actions.decide(
        pending.checkpoint_id,
        workspace_id="workspace-1",
        expected_subject_digest=pending.subject_digest,
        actor="local-user",
        approved=True,
    )
    consumed = actions.consume_for_dispatch(
        approved.checkpoint_id,
        workspace_id="workspace-1",
        current_subject=subject(),
        action_id="action-1",
    )
    assert consumed.state == "consumed"
    assert consumed.external_action["outcome"] == "not_dispatched"
    assert (
        actions.consume_for_dispatch(
            approved.checkpoint_id,
            workspace_id="workspace-1",
            current_subject=subject(),
            action_id="action-1",
        )
        == consumed
    )
    with pytest.raises(WorkflowExternalActionError) as replay:
        actions.consume_for_dispatch(
            approved.checkpoint_id,
            workspace_id="workspace-1",
            current_subject=subject(),
            action_id="action-2",
        )
    assert replay.value.code == "approval_required"


def test_identical_decision_retry_is_idempotent_and_sensitive_subject_is_rejected(
    tmp_path,
):
    actions = service(tmp_path)
    pending = request(actions)
    approved = actions.decide(
        pending.checkpoint_id,
        workspace_id="workspace-1",
        expected_subject_digest=pending.subject_digest,
        actor="local-user",
        approved=True,
        reason="Checked",
    )
    assert (
        actions.decide(
            pending.checkpoint_id,
            workspace_id="workspace-1",
            expected_subject_digest=pending.subject_digest,
            actor="local-user",
            approved=True,
            reason="Checked",
        )
        == approved
    )
    with pytest.raises(WorkflowExternalActionError) as sensitive:
        approval_subject_digest(
            subject(destination={"kind": "printer", "api_token": "do-not-store"})
        )
    assert sensitive.value.code == "approval_subject_sensitive"


def test_changed_subject_becomes_stale_and_wrong_workspace_cannot_decide(tmp_path):
    actions = service(tmp_path)
    pending = request(actions)
    with pytest.raises(WorkflowExternalActionError) as unauthorized:
        actions.decide(
            pending.checkpoint_id,
            workspace_id="workspace-2",
            expected_subject_digest=pending.subject_digest,
            actor="local-user",
            approved=True,
        )
    assert unauthorized.value.code == "approval_not_found"
    actions.decide(
        pending.checkpoint_id,
        workspace_id="workspace-1",
        expected_subject_digest=pending.subject_digest,
        actor="local-user",
        approved=True,
    )
    with pytest.raises(WorkflowExternalActionError) as stale:
        actions.consume_for_dispatch(
            pending.checkpoint_id,
            workspace_id="workspace-1",
            current_subject=subject(
                settings={"material": "PETG", "profile": "0.20-standard"}
            ),
            action_id="action-1",
        )
    assert stale.value.code == "approval_stale"
    assert actions._repository.get(pending.checkpoint_id).state == "stale"


def test_denied_and_unsupported_actions_never_create_dispatch_authority(tmp_path):
    actions = service(tmp_path)
    pending = request(actions)
    actions.decide(
        pending.checkpoint_id,
        workspace_id="workspace-1",
        expected_subject_digest=pending.subject_digest,
        actor="local-user",
        approved=False,
    )
    with pytest.raises(WorkflowExternalActionError):
        actions.consume_for_dispatch(
            pending.checkpoint_id,
            workspace_id="workspace-1",
            current_subject=subject(),
            action_id="action-1",
        )
    with pytest.raises(WorkflowExternalActionError) as unsupported:
        actions.request(
            workspace_id="workspace-1",
            workflow_id="workflow-1",
            run_id="run-2",
            step_id="order",
            action_kind="purchase",
            subject=subject(),
            continuation={},
        )
    assert unsupported.value.code == "external_action_unsupported"


def test_expired_checkpoint_cannot_be_approved_after_restart(tmp_path):
    repository = WorkflowContinuationRepository(str(tmp_path / "state.db"))
    actions = WorkflowExternalActionService(repository)
    pending = actions.request(
        workspace_id="workspace-1",
        workflow_id="workflow-1",
        run_id="run-1",
        step_id="transfer",
        action_kind="printer_transfer",
        subject=subject(),
        continuation={"next_step": "transfer"},
        expires_at=1,
    )
    restarted = WorkflowExternalActionService(
        WorkflowContinuationRepository(str(tmp_path / "state.db"))
    )
    with pytest.raises(WorkflowExternalActionError) as expired:
        restarted.decide(
            pending.checkpoint_id,
            workspace_id="workspace-1",
            expected_subject_digest=pending.subject_digest,
            actor="local-user",
            approved=True,
        )
    assert expired.value.code == "approval_expired"
    assert restarted.lookup(pending.checkpoint_id).state == "expired"
