import pytest

from core.workflow_runs import WorkflowRun, WorkflowRunEvent, WorkflowRunState


def test_workflow_run_requires_immutable_scope_identity():
    run = WorkflowRun(
        "run", "workspace", "session", "workflow", 1, 1, WorkflowRunState.QUEUED
    )
    assert run.generation == 1
    with pytest.raises(ValueError):
        WorkflowRun(
            "", "workspace", "session", "workflow", 1, 1, WorkflowRunState.QUEUED
        )
    with pytest.raises(ValueError):
        WorkflowRunEvent("run", 0, "start", {})
