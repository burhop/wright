"""Queued operations may be observed; completed/uncertain mutations stay guarded."""

import asyncio
import json
from dataclasses import replace

import pytest

from tool_registry.gateway_models import GatewayToolResult
from workspace_service.workflow_mcp_reconciliation import (
    ReconciliationTracker,
    validate_reconciliation_contracts,
)
from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    compile_prompt_workflow,
    execute_prompt_workflow,
)
from .test_workflow_ai_task import call, done, source
from .test_workflow_mcp_execution import TOOL, runtime
from .test_workflow_source_execution import service, task


CONTRACT = {
    "search": {
        "pending_status_path": ["job", "state"],
        "pending_status_values": ["queued", "running"],
        "terminal_status_values": ["completed", "failed"],
        "receipt_path": ["job", "id"],
        "argument_bindings": {"query": ["query"]},
        "fixed_arguments": {},
        "max_polls": 2,
    }
}


def observation(state="queued", identity="existing-job", query="bracket"):
    return {"query": query, "job": {"id": identity, "state": state}}


def test_only_pending_exact_operation_is_repeatable_until_terminal():
    tracker = ReconciliationTracker(CONTRACT)
    assert not tracker.permit_repeat("request", "search")
    assert tracker.observe("request", "search", {"query": "bracket"}, observation())[
        "pending"
    ]
    assert tracker.permit_repeat("request", "search")
    assert not tracker.permit_repeat("changed-request", "search")
    tracker.observe("request", "search", {"query": "bracket"}, observation("completed"))
    assert not tracker.permit_repeat("request", "search")


def test_poll_budget_is_not_reset_by_another_pending_observation():
    tracker = ReconciliationTracker(CONTRACT)
    for _ in range(2):
        tracker.observe("request", "search", {"query": "bracket"}, observation())
        assert tracker.permit_repeat("request", "search")
    tracker.observe("request", "search", {"query": "bracket"}, observation())
    with pytest.raises(WorkflowSourceExecutionError, match="budget"):
        tracker.permit_repeat("request", "search")


@pytest.mark.parametrize(
    "result",
    [
        observation(query="different"),
        observation(identity=""),
        {"query": "bracket", "job": {"state": "queued"}},
    ],
)
def test_pending_without_bound_request_and_receipt_is_rejected(result):
    with pytest.raises(WorkflowSourceExecutionError, match="identity"):
        ReconciliationTracker(CONTRACT).observe(
            "request", "search", {"query": "bracket"}, result
        )


def test_changed_identity_on_terminal_response_is_rejected():
    tracker = ReconciliationTracker(CONTRACT)
    tracker.observe("request", "search", {"query": "bracket"}, observation())
    with pytest.raises(WorkflowSourceExecutionError, match="identity"):
        tracker.observe(
            "request",
            "search",
            {"query": "bracket"},
            observation("completed", "other-job"),
        )


def test_missing_or_unknown_state_does_not_turn_pending_work_into_completion():
    tracker = ReconciliationTracker(CONTRACT)
    tracker.observe("request", "search", {"query": "bracket"}, observation())
    with pytest.raises(WorkflowSourceExecutionError, match="state"):
        tracker.observe(
            "request", "search", {"query": "bracket"}, observation("unknown")
        )


def test_fixed_arguments_compare_types_not_boolean_numeric_equivalence():
    config = json.loads(json.dumps(CONTRACT))
    config["search"]["fixed_arguments"] = {"route": False}
    with pytest.raises(WorkflowSourceExecutionError, match="identity"):
        ReconciliationTracker(config).observe(
            "request", "search", {"query": "bracket", "route": 0}, observation()
        )


@pytest.mark.parametrize(
    "patch",
    [
        {"max_polls": 0},
        {"max_polls": True},
        {"max_polls": 9},
        {"receipt_path": []},
        {"pending_status_values": []},
        {"argument_bindings": {}},
        {"unexpected": True},
    ],
)
def test_invalid_contracts_fail_before_dispatch(patch):
    config = {"search": {**CONTRACT["search"], **patch}}
    with pytest.raises(WorkflowSourceExecutionError):
        validate_reconciliation_contracts(
            config, agent_task=True, allowed_tools=["search"]
        )


def test_contract_must_name_an_allowed_task_tool():
    with pytest.raises(WorkflowSourceExecutionError):
        validate_reconciliation_contracts(
            CONTRACT, agent_task=True, allowed_tools=["other"]
        )
    with pytest.raises(WorkflowSourceExecutionError):
        validate_reconciliation_contracts(
            CONTRACT, agent_task=False, allowed_tools=["search"]
        )


@pytest.mark.parametrize("strict_intent", [False, True])
@pytest.mark.parametrize("repeat_after_completion", [False, True])
def test_executor_joins_pending_job_and_preserves_completed_guard(
    tmp_path, repeat_after_completion, strict_intent
):
    graph = source(
        task(
            "research",
            fmt="text",
            authoring_template="mcp-task",
            mcp_server="docs",
            mcp_task_tools=["search"],
            mcp_reconciliation_contracts=json.dumps(CONTRACT),
        )
    )
    workflow = compile_prompt_workflow(graph)
    if strict_intent:
        from agent_adapters.workflow_instructions import (
            load_default_workflow_instructions,
        )

        profile = load_default_workflow_instructions().model_dump(mode="json")
        workflow = replace(
            workflow, steps=(replace(workflow.steps[0], instruction_set=profile),)
        )
    gateway, runner = runtime()
    gateway.list_tools = lambda *args: (replace(TOOL, annotations={}),)
    responses = iter([observation(), observation("completed")])
    dispatched = []

    async def invoke(*args, **kwargs):
        dispatched.append(args)
        return GatewayToolResult(structured_content=next(responses), content=())

    gateway.call_tool = invoke

    def proposed_call():
        result = call()
        if strict_intent:
            result["tool_calls"][0]["function"]["arguments"] = json.dumps(
                {
                    "schema_version": "wright.workflow-action-intent/1",
                    "arguments": {"query": "bracket"},
                    "assumptions": [],
                    "unresolved_required_information": [],
                }
            )
        return result

    actions = iter(
        [
            proposed_call(),
            proposed_call(),
            proposed_call()
            if repeat_after_completion
            else done("Observed completion", (1, 2)),
        ]
    )
    events = []

    async def decide(*args, **kwargs):
        return next(actions)

    async def emit(event):
        events.append(event)

    execute = execute_prompt_workflow(
        service=service(tmp_path),
        workspace_dir=str(tmp_path),
        plan=workflow,
        input_values={},
        response_generator=None,
        action_generator=decide,
        tool_runtime=runner,
        on_event=emit,
    )
    if repeat_after_completion:
        with pytest.raises(WorkflowSourceExecutionError, match="completed operation"):
            asyncio.run(execute)
    else:
        result = asyncio.run(execute)
        assert (tmp_path / result["output_path"]).read_text() == "Observed completion"
    assert len(dispatched) == 2
    receipts = [e for e in events if e["kind"] == "operation_reconciled"]
    assert [e["pending"] for e in receipts] == [True, False]
    assert {e["receipt"] for e in receipts} == {"existing-job"}
