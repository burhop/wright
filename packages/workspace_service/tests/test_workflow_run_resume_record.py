"""Durable run resume must retain one identity and never replay a begun segment."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from data_vault.workflow_continuation_repository import WorkflowContinuationRepository
from workspace_service.workflow_external_actions import WorkflowExternalActionService
from workspace_service.workflow_run_record import (
    record_workflow_run,
    record_workflow_resume,
    record_workflow_approval_transition,
)
from workspace_service.workflow_source_execution import WorkflowSourceExecutionError


class Files:
    async def write_generated(self, root, path, content, policy):
        target = Path(root) / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return path

    async def read_reference(self, root, path):
        return (Path(root) / path).read_bytes()


async def waiting_run(tmp_path):
    service = SimpleNamespace(
        files=Files(),
        workflow_external_actions=WorkflowExternalActionService(
            WorkflowContinuationRepository(str(tmp_path / "state.db"))
        ),
    )
    subject = {
        "definition_digest": "a" * 64,
        "input_digests": [],
        "artifact_digests": [],
        "binding": {"server": "wright", "tool": "review_artifacts", "schema": "b" * 64},
        "destination": {"kind": "local_review", "id": "workspace"},
        "settings": {},
        "action": {"kind": "local_review", "mode": "review_only"},
    }

    async def execute(emit):
        await emit({"kind": "step_completed", "task_id": "before"})
        return {
            "run_id": "original-run",
            "steps": [{"task_id": "before"}],
            "_approval_request": {
                "step_id": "review",
                "step_title": "Review",
                "instructions": "Review",
                "action_kind": "local_review",
                "subject": subject,
                "continuation": {"schema_version": 2},
            },
        }

    result = await record_workflow_run(
        service=service,
        workspace_dir=str(tmp_path),
        workspace_id="ws",
        source_path="workflows/example.workflow.wflow",
        source_digest="a" * 64,
        execute=execute,
        run_id="original-run",
        required_step_ids=["before", "review", "after"],
    )
    checkpoint_id = result["approval"]["checkpoint_id"]
    actions = service.workflow_external_actions
    actions.decide(
        checkpoint_id,
        workspace_id="ws",
        expected_subject_digest=result["approval"]["subject_digest"],
        actor="test",
        approved=True,
    )
    actions.consume_for_dispatch(
        checkpoint_id, workspace_id="ws", current_subject=subject, action_id="one"
    )
    checkpoint = actions.reconcile(
        checkpoint_id,
        workspace_id="ws",
        run_id="original-run",
        expected_subject_digest=result["approval"]["subject_digest"],
        outcome="dispatched",
        evidence={"kind": "local_review"},
    )
    await record_workflow_approval_transition(
        service=service,
        workspace_dir=str(tmp_path),
        checkpoint=checkpoint,
        kind="external_action_reconciled",
    )
    return service, checkpoint, result["run_log_path"]


@pytest.mark.asyncio
async def test_resume_retains_original_run_and_cached_segment_is_not_reexecuted(
    tmp_path,
):
    service, checkpoint, log = await waiting_run(tmp_path)
    before = json.loads((tmp_path / log).read_text())
    assert before["status"] == "continuation_ready"
    assert "completed_at" not in before
    calls = []

    async def execute(emit):
        calls.append("after")
        await emit({"kind": "step_completed", "task_id": "after"})
        return {
            "run_id": "original-run",
            "steps": [{"task_id": s} for s in ("before", "review", "after")],
        }

    arguments = dict(
        service=service,
        workspace_dir=str(tmp_path),
        workspace_id="ws",
        checkpoint=checkpoint,
        execute=execute,
    )
    first = await record_workflow_resume(**arguments)
    repeated = await record_workflow_resume(**arguments)
    assert first == repeated
    assert calls == ["after"]
    persisted = json.loads((tmp_path / log).read_text())
    assert first["run_log_path"] == log
    assert persisted["status"] == "completed"
    kinds = [event["kind"] for event in persisted["events"]]
    assert (
        kinds.count("run_started")
        == kinds.count("run_resumed")
        == kinds.count("run_completed")
        == 1
    )
    assert persisted["run_id"] == "original-run"


@pytest.mark.asyncio
async def test_missing_later_step_cannot_report_terminal_or_replay_claim(tmp_path):
    service, checkpoint, log = await waiting_run(tmp_path)
    calls = []

    async def execute(emit):
        calls.append("begun")
        return {"run_id": "original-run", "steps": [{"task_id": "before"}]}

    arguments = dict(
        service=service,
        workspace_dir=str(tmp_path),
        workspace_id="ws",
        checkpoint=checkpoint,
        execute=execute,
    )
    with pytest.raises(ValueError, match="missing required"):
        await record_workflow_resume(**arguments)
    with pytest.raises(WorkflowSourceExecutionError, match="already began"):
        await record_workflow_resume(**arguments)
    assert calls == ["begun"]
    persisted = json.loads((tmp_path / log).read_text())
    assert persisted["status"] == "failed"
    assert (
        persisted["resume_segments"][checkpoint.checkpoint_id]["state"]
        == "outcome_unknown"
    )
    assert not any(e["kind"] == "run_completed" for e in persisted["events"])
