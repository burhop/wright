"""Revalidate the same pinned, expanded requirements that were shown for review."""
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace

import pytest

from workspace_service import workflow_approval_execution as approvals
from workspace_service.process_validation.profiles import load_profile
from workspace_service.workflow_external_actions import WorkflowExternalActionError
from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    _approval_settings,
    compile_prompt_workflow,
)
from .test_workflow_approval_execution import setup_case


@pytest.mark.asyncio
@pytest.mark.parametrize("mutation", [None, "text", "sources", "missing", "profile", "input"])
async def test_preparation_recomputes_exact_expanded_review_settings(
    tmp_path, monkeypatch, mutation
):
    case = await setup_case(tmp_path, integration=False)
    plan = compile_prompt_workflow(
        (tmp_path / "workflows/example.workflow.wflow").read_text(encoding="utf-8")
    )
    cursor = case.checkpoint.continuation["next_step_index"]
    profile = load_profile("heat-spreader-sizing-01-full")
    required = [r.id for r in profile.baseline.requirements if r.review_required]
    action = deepcopy(plan.steps[cursor].external_action)
    action["settings"]["validation_review"] = {
        "profile_ref": profile.reference().model_dump(mode="json"),
        "requirement_ids": required,
    }
    review = replace(plan.steps[cursor], external_action=action)
    roles = {check.subject_role for check in profile.checks}
    for check in profile.checks:
        roles.update(check.parameters.get("related_roles", []))
    validator = SimpleNamespace(validation={
        "profile": {"source": "packaged", "name": "heat-spreader-sizing-01-full",
                    "reference": profile.reference().model_dump(mode="json")},
        "baseline": profile.baseline.reference().model_dump(mode="json"),
        "subjects": {role: role for role in roles},
    })
    plan = replace(plan, steps=tuple(
        review if index == cursor else step for index, step in enumerate(plan.steps)
    ) + (validator,))
    subject = deepcopy(case.checkpoint.subject)
    subject["settings"] = _approval_settings(
        pending_action=review, plan=plan, workspace_dir=str(tmp_path)
    )
    assert subject["settings"] != action["settings"]
    continuation = deepcopy(case.checkpoint.continuation)
    if mutation == "text":
        subject["settings"]["validation_review_requirements"][0]["text"] = "Changed"
    elif mutation == "sources":
        subject["settings"]["validation_review_requirements"][0]["sources"][0]["sha256"] = "0" * 64
    elif mutation == "missing":
        subject["settings"].pop("validation_review_requirements")
    elif mutation == "profile":
        validator.validation["profile"]["reference"]["sha256"] = "0" * 64
    elif mutation == "input":
        continuation["input_identities"] = {"unexpected": "0" * 64}
    checkpoint = replace(case.checkpoint, subject=subject, continuation=continuation)

    async def prepared(**kwargs):
        # Isolate decision-time comparison; setup_case exercises real initial
        # preparation/storage, and _approval_settings loads the real pinned profile.
        return plan, {}

    monkeypatch.setattr(approvals, "prepare_prompt_workflow", prepared)
    args = dict(service=case.services, workspace_id="ws", workspace_dir=str(tmp_path),
                checkpoint=checkpoint, gateway=None, session_id="session")
    if mutation:
        with pytest.raises((WorkflowExternalActionError, WorkflowSourceExecutionError)):
            await approvals._prepare(**args)
    else:
        actual_plan, inputs, runtime, context = await approvals._prepare(**args)
        assert actual_plan is plan and inputs == {} and runtime is None and context is None
    assert case.services.workflow_external_actions.lookup(case.checkpoint.checkpoint_id).state == "pending"
