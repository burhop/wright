"""Simulated remote service contracts. These are not live FEA results."""

import asyncio
from dataclasses import replace
import pytest
from tool_registry.gateway_models import GatewayTool, GatewayToolResult
from workspace_service.workflow_mcp_execution import WorkflowMcpRuntime, schema_digest
from workspace_service.workflow_source_execution import (
    PromptStep,
    WorkflowSourceExecutionError,
)
from packages.workspace_service.tests.test_workflow_mcp_execution import Gateway


def remote(states=("working", "completed")):
    profile = {
        "version": 1,
        "status_tool": "status",
        "cancel_tool": "cancel",
        "poll_seconds": 0.05,
    }
    tools = [
        GatewayTool(
            name="fea__submit",
            server_id="fea",
            tool_name="submit",
            description="Submit analysis",
            input_schema={"type": "object"},
            upstream_meta={"wright/operation": profile},
        )
    ]
    tools.extend(
        GatewayTool(
            name="fea__" + name,
            server_id="fea",
            tool_name=name,
            description=name,
            input_schema={
                "type": "object",
                "properties": {"operation_id": {"type": "string"}},
                "required": ["operation_id"],
                "additionalProperties": False,
            },
            annotations={"readOnlyHint": name == "status"},
        )
        for name in ("status", "cancel")
    )
    g = Gateway()
    g.list_tools = lambda *a: tuple(tools)
    sequence = iter(states)
    last = "working"

    async def call(session, request, name, args, **kw):
        nonlocal last
        g.calls.append((name, args))
        if name == "fea__submit":
            value = {"operation_id": "job-123"}
        elif name == "fea__status":
            last = next(sequence, last)
            value = {"status": last, "result": {"stress": 12, "units": "MPa"}}
        else:
            value = {"accepted": True}
        return GatewayToolResult(content=(), structured_content=value)

    g.call_tool = call
    runtime = WorkflowMcpRuntime(g, workspace_id="w", session_id="s")
    step = PromptStep(
        "analysis",
        "Analysis",
        "",
        None,
        (),
        "json",
        "",
        False,
        "indexed",
        tool_name=tools[0].name,
        server_id="fea",
        schema_digest=schema_digest(tools[0]),
        timeout_seconds=2,
    )
    return g, runtime, step, tools


def test_submission_is_polled_to_completion_once():
    g, r, s, _ = remote()
    events = []

    async def emit(kind, **kw):
        events.append((kind, kw))

    result = asyncio.run(r.call(s, {}, on_event=emit))
    assert result[0] == {"stress": 12, "units": "MPa"}
    assert [n for n, a in g.calls] == ["fea__submit", "fea__status", "fea__status"]
    assert [e[1]["state"] for e in events] == [
        "submitted",
        "working",
        "completed",
        "results_collected",
    ]
    assert all(a["operation_id"] == "job-123" for n, a in g.calls if n != "fea__submit")


def test_timeout_requests_cancel_without_resubmission_or_false_completion():
    g, r, s, _ = remote(("working",))
    events = []

    async def emit(kind, **kw):
        events.append(kw)

    with pytest.raises(TimeoutError):
        asyncio.run(r.call(replace(s, timeout_seconds=0.07), {}, on_event=emit))
    assert [n for n, a in g.calls].count("fea__submit") == 1
    assert [n for n, _ in g.calls].count("fea__cancel") == 1
    assert events[-1]["state"] == "cancellation_unconfirmed"


def test_missing_status_capability_rejected_before_submission():
    g, r, s, tools = remote()
    g.list_tools = lambda *a: (tools[0],)
    with pytest.raises(WorkflowSourceExecutionError, match="status_tool"):
        asyncio.run(r.call(s, {}))
    assert not g.calls


@pytest.mark.parametrize("state", ["failed", "cancelled", "input_required", "mystery"])
def test_unfinished_or_unknown_job_is_never_success(state):
    g, r, s, _ = remote((state,))
    with pytest.raises(WorkflowSourceExecutionError):
        asyncio.run(r.call(s, {}))
    assert [n for n, a in g.calls].count("fea__submit") == 1


@pytest.mark.asyncio
async def test_progress_is_provider_observed_and_only_configured_metrics_are_used():
    g, runtime, step, tools = remote(("completed",))
    tools[0].upstream_meta["wright/operation"].update(
        progress_field="percent",
        remaining_seconds_field="seconds",
        metrics_fields={"iteration": "iteration"},
        freshness_seconds=3,
    )
    step = replace(step, schema_digest=schema_digest(tools[0]))
    original = g.call_tool

    async def call(*args, **kwargs):
        result = await original(*args, **kwargs)
        if args[2] == "fea__status":
            return GatewayToolResult(
                content=(),
                structured_content={
                    "operation_id": "job-123",
                    "status": "completed",
                    "percent": 87,
                    "seconds": 12,
                    "iteration": 4,
                    "secret": "not a UI metric",
                    "result": {"stress": 12},
                },
            )
        return result

    g.call_tool = call
    events = []

    async def emit(kind, **payload):
        events.append(payload)

    await runtime.call(step, {}, on_event=emit)
    observed = next(e for e in events if e["state"] == "completed")
    assert observed["provider_binding"] == "fea"
    assert observed["provider_schema_digest"] == step.schema_digest
    assert observed["observation_source"] == "provider_status"
    assert observed["progress_percent"] == 87
    assert observed["estimated_remaining_seconds"] == 12
    assert observed["metrics"] == {"iteration": 4}
    assert observed["observed_at"] < observed["stale_after"]
    assert events[-1]["observed_at"] == observed["observed_at"]


@pytest.mark.parametrize("value", [True, "50", -1, 101, float("nan"), float("inf")])
@pytest.mark.asyncio
async def test_invalid_progress_is_unavailable_never_guessed_or_clamped(value):
    g, runtime, step, tools = remote(("completed",))
    tools[0].upstream_meta["wright/operation"]["progress_field"] = "percent"
    step = replace(step, schema_digest=schema_digest(tools[0]))
    original = g.call_tool

    async def call(*args, **kwargs):
        result = await original(*args, **kwargs)
        if args[2] == "fea__status":
            result.structured_content["percent"] = value
        return result

    g.call_tool = call
    events = []

    async def emit(kind, **payload):
        events.append(payload)

    await runtime.call(step, {}, on_event=emit)
    observed = next(e for e in events if e["state"] == "completed")
    assert observed["progress_percent"] is None
    assert observed["estimated_remaining_seconds"] is None
    assert observed["limitations"]


@pytest.mark.asyncio
async def test_another_operation_status_never_becomes_this_operations_progress():
    g, runtime, step, _ = remote(("completed",))
    original = g.call_tool

    async def call(*args, **kwargs):
        result = await original(*args, **kwargs)
        if args[2] == "fea__status":
            result.structured_content["operation_id"] = "other-job"
        return result

    g.call_tool = call
    events = []

    async def emit(kind, **payload):
        events.append(payload)

    with pytest.raises(WorkflowSourceExecutionError, match="identity"):
        await runtime.call(step, {}, on_event=emit)
    assert events[-1]["state"] == "reconciliation_required"
    assert not any(e["state"] == "completed" for e in events)


@pytest.mark.asyncio
async def test_interrupting_monitor_does_not_send_a_remote_cancellation():
    g, runtime, step, _ = remote(("working",))
    started = asyncio.Event()
    events = []

    async def emit(kind, **payload):
        events.append(payload)
        if payload["state"] == "working":
            started.set()

    task = asyncio.create_task(runtime.call(step, {}, on_event=emit))
    await asyncio.wait_for(started.wait(), 2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert [n for n, _ in g.calls].count("fea__cancel") == 0
    assert events[-1]["state"] == "monitor_interrupted"


@pytest.mark.asyncio
async def test_timeout_cancellation_reads_actual_terminal_outcome_without_resubmission():
    g, runtime, step, tools = remote(("working",))
    tools[0].upstream_meta["wright/operation"]["cancel_confirm_seconds"] = 0.2
    step = replace(step, schema_digest=schema_digest(tools[0]), timeout_seconds=0.06)
    original = g.call_tool
    cancelled = False

    async def call(*args, **kwargs):
        nonlocal cancelled
        result = await original(*args, **kwargs)
        if args[2] == "fea__cancel":
            cancelled = True
        if args[2] == "fea__status" and cancelled:
            result.structured_content["status"] = "cancelled"
        return result

    g.call_tool = call
    events = []

    async def emit(kind, **payload):
        events.append(payload)

    with pytest.raises(TimeoutError):
        await runtime.call(step, {}, on_event=emit)
    assert [n for n, _ in g.calls].count("fea__submit") == 1
    assert [e["state"] for e in events][-2:] == ["cancellation_requested", "cancelled"]
    assert events[-1]["observation_source"] == "provider_status"


@pytest.mark.asyncio
async def test_status_binding_changed_during_submission_is_not_adopted():
    g, runtime, step, tools = remote()
    original = g.call_tool

    async def call(*args, **kwargs):
        result = await original(*args, **kwargs)
        if args[2] == "fea__submit":
            tools[1].input_schema["properties"]["operation_id"]["description"] = (
                "Changed schema"
            )
        return result

    g.call_tool = call
    events = []

    async def emit(kind, **payload):
        events.append(payload)

    with pytest.raises(WorkflowSourceExecutionError, match="binding has changed"):
        await runtime.call(step, {}, on_event=emit)
    assert [n for n, _ in g.calls] == ["fea__submit"]
    assert events[-1]["state"] == "reconciliation_required"


@pytest.mark.parametrize(
    "change",
    [
        {"progress_field": []},
        {"states": {"done": []}},
        {"metrics_fields": []},
        {"poll_seconds": float("nan")},
        {"freshness_seconds": True},
        {"cancel_confirm_seconds": 11},
    ],
)
def test_invalid_observation_profile_rejected_before_submission(change):
    g, runtime, step, tools = remote()
    tools[0].upstream_meta["wright/operation"].update(change)
    step = replace(step, schema_digest=schema_digest(tools[0]))
    with pytest.raises(WorkflowSourceExecutionError):
        asyncio.run(runtime.call(step, {}))
    assert not g.calls


@pytest.mark.asyncio
async def test_missing_cancel_authority_is_unavailable_without_a_runtime_question():
    from workspace_service.workflow_async_operations import operation_cancellation

    g, runtime, step, tools = remote(("working",))
    tools[2] = replace(tools[2], required_approvals=("separate-authority",))
    entered = asyncio.Event()

    async def emit(kind, **payload):
        if payload["state"] == "working":
            entered.set()

    task = asyncio.create_task(runtime.call(step, {}, on_event=emit))
    await asyncio.wait_for(entered.wait(), 2)
    assert operation_cancellation(runtime, reserve=True) is None
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert not any(n == "fea__cancel" for n, _ in g.calls)
    assert not runtime._active_operations


def test_status_authority_is_required_before_submission():
    g, runtime, step, tools = remote()
    tools[1] = replace(tools[1], required_approvals=("status-authority",))
    with pytest.raises(WorkflowSourceExecutionError, match="before submission"):
        asyncio.run(runtime.call(step, {}))
    assert not g.calls


@pytest.mark.asyncio
async def test_missing_submission_identity_is_unknown_without_resubmission():
    g, runtime, step, _ = remote()

    async def call(*args, **kwargs):
        g.calls.append((args[2], args[3]))
        return GatewayToolResult(
            content=(), structured_content={"receipt": "No stable job identity"}
        )

    g.call_tool = call
    events = []

    async def emit(kind, **payload):
        events.append(payload)

    with pytest.raises(WorkflowSourceExecutionError) as error:
        await runtime.call(step, {}, on_event=emit)
    assert error.value.code == "APPLICATION_OUTCOME_UNKNOWN"
    assert [n for n, _ in g.calls] == ["fea__submit"]
    assert events[-1]["state"] == "reconciliation_required"
    assert events[-1]["operation_id"] is None
