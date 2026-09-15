"""Canonical same-run resumption across independently persisted approvals."""

import asyncio
import copy
import json
from dataclasses import asdict, replace

import pytest

from workspace_service.workflow_source_execution import (
    compile_prompt_workflow,
    execute_prompt_workflow,
    WorkflowSourceExecutionError,
)
from packages.workspace_service.tests.test_workflow_external_action_execution import (
    source,
    service,
)
from packages.workspace_service.tests.test_workflow_source_execution import task


def order(key, before, after):
    return f'''connection {key}
  type: order
  from: "{before}"
  to: "{after}"
  label: "next"
  when: null
end
'''


def graph():
    text = source()
    approval = text[
        text.index("task approve") : text.index("connection package_to_approval")
    ]
    return (
        text
        + task("after_first", fmt="text", save_output=True)
        + approval.replace("task approve", "task approve_second")
        + task("final", fmt="text", save_output=True)
        + order("first_continue", "approve", "after_first")
        + order("second_gate", "after_first", "approve_second")
        + order("final_continue", "approve_second", "final")
    )


def authorize(services, result, outcome="dispatched"):
    request = result["_approval_request"]
    checkpoint = services.workflow_external_actions.request(
        workspace_id="ws",
        workflow_id="workflows/example.workflow.wflow",
        run_id=result["run_id"],
        step_id=request["step_id"],
        action_kind=request["action_kind"],
        subject=request["subject"],
        continuation=request["continuation"],
    )
    services.workflow_external_actions.decide(
        checkpoint.checkpoint_id,
        workspace_id="ws",
        expected_subject_digest=checkpoint.subject_digest,
        actor="test-actor",
        approved=True,
    )
    services.workflow_external_actions.consume_for_dispatch(
        checkpoint.checkpoint_id,
        workspace_id="ws",
        current_subject=checkpoint.subject,
        action_id=f"action-{request['step_id']}",
    )
    return asdict(
        services.workflow_external_actions.reconcile(
            checkpoint.checkpoint_id,
            workspace_id="ws",
            run_id=result["run_id"],
            expected_subject_digest=checkpoint.subject_digest,
            outcome=outcome,
            evidence={"test": "No physical or supplier operation"},
        )
    )


def test_two_sequential_checkpoints_resume_same_run_and_execute_true_final_step(
    tmp_path,
):
    plan = replace(compile_prompt_workflow(graph()), definition_digest="a" * 64)
    calls, events = [], []

    async def generate(prompt, fmt):
        calls.append(prompt)
        return '{"package":"ready"}' if fmt == "json" else f"Generated {len(calls)}"

    async def emit(event):
        events.append(event)

    async def execute(services, **kwargs):
        return await execute_prompt_workflow(
            service=services,
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
            on_event=emit,
            **kwargs,
        )

    # Recreate the service each time to prove restore consumes durable JSON,
    # not a live process closure or in-memory model result.
    first = asyncio.run(
        execute(service(tmp_path), execution_context={"campaign_id": "test"})
    )
    first_checkpoint = authorize(service(tmp_path), first)
    assert len(calls) == 1
    state = json.loads(json.dumps(first_checkpoint["continuation"]))
    second = asyncio.run(
        execute(
            service(tmp_path), continuation=state, completed_checkpoint=first_checkpoint
        )
    )
    assert len(calls) == 2
    assert second["run_id"] == first["run_id"]
    assert second["_approval_request"]["step_id"] == "approve_second"
    assert second["_approval_request"]["continuation"]["execution_context"] == {
        "campaign_id": "test"
    }
    assert len(state["records"]) == 1  # Restoring cannot mutate sealed state.
    assert not (tmp_path / "final.txt").exists()
    second_checkpoint = authorize(service(tmp_path), second)
    final = asyncio.run(
        execute(
            service(tmp_path),
            continuation=second_checkpoint["continuation"],
            completed_checkpoint=second_checkpoint,
        )
    )
    assert len(calls) == 3
    assert final["run_id"] == first["run_id"]
    assert "_approval_request" not in final
    assert [item["task_id"] for item in final["steps"]] == [
        "package",
        "approve",
        "after_first",
        "approve_second",
        "final",
    ]
    assert {item["output_path"] for item in final["outputs"]} == {
        "package.json",
        "after_first.txt",
        "final.txt",
    }
    assert (tmp_path / "final.txt").read_text() == "Generated 3"
    assert [
        event["task_id"] for event in events if event["kind"] == "step_completed"
    ] == [
        "package",
        "approve",
        "after_first",
        "approve_second",
        "final",
    ]
    assert all(
        item["provenance"]["run_id"] == first["run_id"] for item in final["results"]
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "definition",
        "input",
        "artifact",
        "unknown",
        "not_dispatched",
        "cursor",
        "completed",
        "binding",
    ],
)
def test_stale_or_uncertain_continuations_never_execute_later_steps(tmp_path, mutation):
    plan = replace(compile_prompt_workflow(graph()), definition_digest="a" * 64)
    services = service(tmp_path)
    calls = []

    async def generate(prompt, fmt):
        calls.append(prompt)
        return '{"package":"ready"}'

    async def execute(**kwargs):
        return await execute_prompt_workflow(
            service=services,
            workspace_dir=str(tmp_path),
            response_generator=generate,
            **kwargs,
        )

    result = asyncio.run(execute(plan=plan, input_values={"brief": "Original"}))
    checkpoint = authorize(
        services,
        result,
        "outcome_unknown"
        if mutation == "unknown"
        else "not_dispatched"
        if mutation == "not_dispatched"
        else "dispatched",
    )
    state = copy.deepcopy(checkpoint["continuation"])
    inputs = {"brief": "Original"}
    if mutation == "definition":
        plan = replace(plan, definition_digest="b" * 64)
    elif mutation == "input":
        inputs["brief"] = "Changed"
    elif mutation == "artifact":
        (tmp_path / "package.json").write_text("Changed")
    elif mutation == "cursor":
        state["next_step_index"] += 1
    elif mutation == "completed":
        state["completed_step_ids"] = []
    elif mutation == "binding":
        changed = {**plan.steps[1].external_action, "binding": {"tool": "changed"}}
        plan = replace(
            plan,
            steps=(
                plan.steps[0],
                replace(plan.steps[1], external_action=changed),
                *plan.steps[2:],
            ),
        )
    with pytest.raises(WorkflowSourceExecutionError) as error:
        asyncio.run(
            execute(
                plan=plan,
                input_values=inputs,
                continuation=state,
                completed_checkpoint=checkpoint,
            )
        )
    assert error.value.code == "WORKFLOW_CONTINUATION_STALE"
    assert len(calls) == 1
    assert not (tmp_path / "after_first.txt").exists()


def test_nonterminal_manual_review_keeps_connected_artifact_for_later_task(tmp_path):
    from packages.workspace_service.tests.test_workflow_artifact_review import (
        source as reviewed_source,
        section,
        port,
    )

    text = reviewed_source()
    text += section(
        "task",
        "after",
        name="After review",
        step_type="work",
        performed_by="ai_assisted",
        tool=None,
        reusable_step=None,
        inputs=[port("in", True)],
        outputs=[port("out")],
        prompt="Use the approved design",
        settings={
            "output_format": "text",
            "output_filename": "final.txt",
            "save_output": True,
        },
    )
    text += section(
        "connection",
        "after_review",
        type="item",
        **{"from": "review.review_out", "to": "after.in"},
        label="approved",
        when=None,
    )
    plan = replace(compile_prompt_workflow(text), definition_digest="a" * 64)
    assert plan.steps[2].external_action["action_kind"] == "local_review"
    calls = []

    async def generate(prompt, fmt):
        calls.append(prompt)
        return (
            '{"facts":"input"}'
            if fmt == "json"
            else "<html><body>approved draft</body></html>"
            if fmt == "html"
            else "Final design"
        )

    services = service(tmp_path)

    async def execute(**kwargs):
        return await execute_prompt_workflow(
            service=services,
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={"context": "Context"},
            response_generator=generate,
            **kwargs,
        )

    first = asyncio.run(execute())
    checkpoint = authorize(services, first)
    final = asyncio.run(
        execute(
            continuation=checkpoint["continuation"], completed_checkpoint=checkpoint
        )
    )
    assert len(calls) == 3
    assert "approved draft" in calls[-1]
    assert final["steps"][-1]["task_id"] == "after"


@pytest.mark.parametrize("changed", [False, True])
def test_handoff_receipt_is_verified_and_attached_to_original_run(tmp_path, changed):
    import hashlib

    plan = replace(compile_prompt_workflow(source()), definition_digest="a" * 64)
    services = service(tmp_path)

    async def generate(*args):
        return '{"package":"ready"}'

    async def execute(**kwargs):
        return await execute_prompt_workflow(
            service=services,
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
            **kwargs,
        )

    first = asyncio.run(execute())
    checkpoint = authorize(services, first)
    raw = b'{"integration_test":true,"destination":"disposable-test"}'
    (tmp_path / "receipt.json").write_bytes(raw)
    checkpoint["external_action"]["evidence"]["produced_files"] = [
        {
            "output_path": "receipt.json",
            "sha256": hashlib.sha256(raw).hexdigest(),
            "output_bytes": len(raw),
            "output_format": "json",
            "output_port": "receipt",
        }
    ]
    if changed:
        (tmp_path / "receipt.json").write_bytes(b"changed")
        with pytest.raises(WorkflowSourceExecutionError, match="receipt changed"):
            asyncio.run(
                execute(
                    continuation=checkpoint["continuation"],
                    completed_checkpoint=checkpoint,
                )
            )
        return
    final = asyncio.run(
        execute(
            continuation=checkpoint["continuation"], completed_checkpoint=checkpoint
        )
    )
    receipt = next(
        item
        for item in final["results"]
        if item["artifact_role"] == "external_action_receipt"
    )
    assert receipt["provenance"] == {
        "run_id": first["run_id"],
        "task_id": "approve",
        "output_port": "receipt",
        "input_revisions": (),
        "definition_digest": None,
        "binding_digest": None,
    }
    assert final["outputs"][-1]["output_path"] == "receipt.json"
