"""Presentation permission comes from the canonical approval application."""

import pytest

from workspace_service import workflow_approval_execution as owner
from workspace_service.workflow_source_execution import WorkflowSourceExecutionError
from packages.workspace_service.tests.test_workflow_approval_execution import setup_case


@pytest.mark.asyncio
async def test_inspection_checks_current_subject_without_deciding_or_dispatching(
    tmp_path,
):
    case = await setup_case(tmp_path)
    calls = list(case.calls)
    before = {
        p.relative_to(tmp_path).as_posix(): p.read_bytes()
        for p in (tmp_path / "runs").rglob("*.json")
    }
    inspected = await owner.inspect_workflow_approval(**case.args)
    assert inspected.checkpoint.checkpoint_id == case.checkpoint.checkpoint_id
    assert inspected.can_decide and not inspected.can_resume
    assert (
        case.services.workflow_external_actions.lookup(
            case.checkpoint.checkpoint_id
        ).state
        == "pending"
    )
    assert case.calls == calls
    assert {
        p.relative_to(tmp_path).as_posix(): p.read_bytes()
        for p in (tmp_path / "runs").rglob("*.json")
    } == before


@pytest.mark.asyncio
async def test_inspection_exposes_approved_supported_resume_without_consuming(tmp_path):
    case = await setup_case(tmp_path)
    calls = list(case.calls)
    await owner.decide_workflow_approval(
        **case.args, decision="approved", reason="Test review"
    )
    inspected = await owner.inspect_workflow_approval(**case.args)
    assert not inspected.can_decide and inspected.can_resume
    assert inspected.checkpoint.state == "approved"
    assert inspected.checkpoint.external_action is None
    assert case.calls == calls


@pytest.mark.asyncio
async def test_changed_input_is_owner_stale_not_an_enabled_review(tmp_path):
    case = await setup_case(tmp_path)
    calls = list(case.calls)
    (tmp_path / "brief.md").write_text("different input", encoding="utf-8")
    with pytest.raises(
        (owner.WorkflowExternalActionError, WorkflowSourceExecutionError)
    ):
        await owner.inspect_workflow_approval(**case.args)
    assert (
        case.services.workflow_external_actions.lookup(
            case.checkpoint.checkpoint_id
        ).state
        == "pending"
    )
    assert case.calls == calls


@pytest.mark.asyncio
async def test_consumed_action_is_never_resubmittable_by_reading(tmp_path):
    case = await setup_case(tmp_path)
    await owner.decide_workflow_approval(
        **case.args, decision="approved", reason="Test review"
    )
    await owner.resume_workflow_approval(
        **case.args,
        response_generator=case.generate,
        request_id="test-inspection-resume",
    )
    count = len(case.calls)
    inspected = await owner.inspect_workflow_approval(**case.args)
    assert not inspected.can_decide and not inspected.can_resume
    assert inspected.checkpoint.state == "consumed"
    assert len(case.calls) == count


@pytest.mark.asyncio
async def test_approval_does_not_imply_dispatcher_capability(tmp_path):
    case = await setup_case(tmp_path, integration=False, handoff=True)
    await owner.decide_workflow_approval(
        **case.args, decision="approved", reason="Test review"
    )
    inspected = await owner.inspect_workflow_approval(**case.args)
    assert not inspected.can_decide and not inspected.can_resume
    assert inspected.resume_error_code == "WORKFLOW_EXTERNAL_DISPATCH_UNSUPPORTED"
    assert inspected.resume_correction
    assert inspected.checkpoint.state == "approved"
    assert inspected.checkpoint.external_action is None
