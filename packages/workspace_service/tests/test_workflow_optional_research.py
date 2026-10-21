"""Optional research reuses supplied inputs; engineering tool evidence stays required."""

import asyncio
import json
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from core.process_validation import canonical_digest
from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    compile_prompt_workflow,
    execute_prompt_workflow,
    _parse,
)
from .test_workflow_ai_task import call, done, plan, source
from .test_workflow_mcp_execution import TOOL, runtime
from .test_workflow_source_execution import service, task


POLICY = "supplied_inputs_or_tools"


@pytest.mark.parametrize(
    "template,stage,supplied_facts",
    [
        (
            "raspberry-pi-enclosure",
            "design_basis",
            {
                "board": "Pi 5",
                "dimension_source": "supplied manufacturer drawing",
                "thermal_load_w": 5,
            },
        ),
        (
            "robot-tracking-diagnosis",
            "evidence_diagnosis",
            {"time_range_s": [0, 30], "rmse_m": 0.025, "cause": "unproven"},
        ),
    ],
)
@pytest.mark.parametrize("research_needed", [False, True])
def test_existing_design_basis_and_tracking_diagnosis_analysis_stages(
    tmp_path, template, stage, supplied_facts, research_needed
):
    # Controlled stage-level qualification, not a claim of live CAD/robot evidence.
    path = (
        Path(__file__).parents[1]
        / "src/workspace_service/engineering_workflow_templates/templates"
        / f"{template}.workflow.wflow"
    )
    original = path.read_bytes()
    fields = next(
        b["fields"]
        for b in _parse(original.decode().replace("__instance__", "fixture"))
        if b["id"] == stage + "_fixture"
    )
    original_prompt = fields["prompt"]
    workflow = compile_prompt_workflow(
        source(
            task(
                stage,
                prompt=original_prompt
                + "\n\nSupplied fixture evidence:\n"
                + json.dumps(supplied_facts),
                fmt="text",
                authoring_template="mcp-task",
                mcp_server="docs",
                mcp_completion_policy=POLICY,
            )
        )
    )
    replies = (
        [call(), done("Analysis of observed fixture evidence.")]
        if research_needed
        else [supplied()]
    )
    execution, gateway, events, requests = run(tmp_path, workflow, replies)
    asyncio.run(execution)
    delivered = next(m["content"] for m in requests[0][0] if m["role"] == "user")
    assert original_prompt in delivered and json.dumps(supplied_facts) in delivered
    assert len(gateway.calls) == int(research_needed)
    evidence = next(e for e in events if e["kind"] == "task_completion_evidence")
    assert evidence["basis"] == ("tool_calls" if research_needed else "supplied_inputs")
    assert path.read_bytes() == original


def supplied(response="Analysis from the supplied dimensions."):
    result = done(response, ())
    body = json.loads(result["content"])
    body["completion_basis"] = "supplied_inputs"
    result["content"] = json.dumps(body)
    return result


def run(tmp_path, workflow, replies, *, annotations=None, result=None):
    gateway, runner = runtime()
    tool = replace(
        TOOL, annotations={"readOnlyHint": True} if annotations is None else annotations
    )
    gateway.list_tools = lambda *_: (tool,)
    if result is not None:
        gateway.result = result
    events, requests = [], []
    sequence = iter(replies)

    async def decide(messages, tools, **kwargs):
        requests.append((list(messages), tools, kwargs))
        return next(sequence)

    async def emit(event):
        events.append(event)

    execution = execute_prompt_workflow(
        service=service(tmp_path),
        workspace_dir=str(tmp_path),
        plan=workflow,
        input_values={},
        response_generator=None,
        action_generator=decide,
        tool_runtime=runner,
        on_event=emit,
    )
    return execution, gateway, events, requests


def test_supplied_analysis_completes_without_call_and_retains_input_identity(tmp_path):
    workflow = plan(mcp_completion_policy=POLICY)
    execution, gateway, events, requests = run(tmp_path, workflow, [supplied()])
    result = asyncio.run(execution)
    assert gateway.calls == []
    assert result["steps"][0]["tool_calls"] == []
    assert "supplied dimensions" in (tmp_path / result["output_path"]).read_text()
    evidence = next(e for e in events if e["kind"] == "task_completion_evidence")
    user = next(m["content"] for m in requests[0][0] if m["role"] == "user")
    actual_input, context = user.rsplit("\n\n", 1)
    assert evidence["input_digest"] == canonical_digest(
        {"prompt": actual_input, "images": []}
    )
    assert evidence["basis"] == "supplied_inputs"
    assert evidence["tool_call_numbers"] == []
    assert (
        json.loads(context)["wright_step_context"]["completion_evidence_policy"]
        == POLICY
    )
    resolved = next(e for e in events if e["kind"] == "instructions_resolved")[
        "instructions"
    ]
    assert "context.mcp-input-completion" in resolved["asset_ids"]
    assert "optional read-only research" in requests[0][0][0]["content"]
    # The typed setting is part of the same serialized step used for continuation.
    assert asdict(workflow.steps[0])["mcp_completion_policy"] == POLICY


def test_optional_research_cites_actual_tool_evidence_when_used(tmp_path):
    execution, gateway, events, _ = run(
        tmp_path, plan(mcp_completion_policy=POLICY), [call(), done("Research result")]
    )
    asyncio.run(execution)
    assert len(gateway.calls) == 1
    evidence = next(e for e in events if e["kind"] == "task_completion_evidence")
    assert evidence["basis"] == "tool_calls"
    assert evidence["tool_call_numbers"] == [1]


@pytest.mark.parametrize(
    "workflow,replies",
    [
        (plan(), [supplied()]),
        (plan(mcp_completion_policy=POLICY), [done("Missing explicit basis", ())]),
        (plan(mcp_completion_policy=POLICY), [done("Invented tool evidence", (1,))]),
        (plan(mcp_completion_policy=POLICY), [call(), supplied()]),
        (
            plan(mcp_completion_policy=POLICY),
            [call(), done("Invalid evidence", (True,))],
        ),
    ],
)
def test_completion_cannot_waive_or_fabricate_evidence(tmp_path, workflow, replies):
    execution, _, events, _ = run(tmp_path, workflow, replies)
    with pytest.raises(
        WorkflowSourceExecutionError, match="no valid execution evidence"
    ):
        asyncio.run(execution)
    assert not any(e["kind"] == "task_completion_evidence" for e in events)


@pytest.mark.parametrize(
    "annotations", [{}, {"idempotentHint": True}, {"readOnlyHint": False}]
)
def test_optional_research_rejects_unclassified_or_changing_tools_before_model(
    tmp_path, annotations
):
    execution, gateway, _, requests = run(
        tmp_path,
        plan(mcp_completion_policy=POLICY),
        [supplied()],
        annotations=annotations,
    )
    with pytest.raises(WorkflowSourceExecutionError, match="explicitly read-only"):
        asyncio.run(execution)
    assert gateway.calls == [] and requests == []


@pytest.mark.parametrize("missing", ["collection", "helper"])
def test_saved_helper_is_required_without_silent_default_substitution(
    tmp_path, missing
):
    workflow = plan(mcp_completion_policy=POLICY)
    profile = json.loads(json.dumps(workflow.instruction_set))
    if missing == "helper":
        profile["assets"] = [
            a for a in profile["assets"] if a["id"] != "context.mcp-input-completion"
        ]
    else:
        profile = None
    workflow = replace(
        workflow, steps=(replace(workflow.steps[0], instruction_set=profile),)
    )
    execution, gateway, _, requests = run(tmp_path, workflow, [supplied()])
    with pytest.raises(
        WorkflowSourceExecutionError, match="saved task instructions are invalid"
    ):
        asyncio.run(execution)
    assert gateway.calls == [] and requests == []


@pytest.mark.parametrize("policy", [None, True, [], "allow_any"])
def test_invalid_completion_policy_rejected_during_compilation(policy):
    with pytest.raises(WorkflowSourceExecutionError, match="completion policy"):
        plan(mcp_completion_policy=policy)


@pytest.mark.parametrize(
    "patch",
    [
        {"authoring_template": "ai-prompt"},
        {"expected_files": "output.step"},
    ],
)
def test_supplied_completion_cannot_replace_declared_engineering_work(patch):
    settings = {
        "authoring_template": "mcp-task",
        "mcp_server": "docs",
        "mcp_completion_policy": POLICY,
        **patch,
    }
    with pytest.raises(WorkflowSourceExecutionError, match="read-only analysis"):
        compile_prompt_workflow(source(task("research", fmt="text", **settings)))


def test_format_repair_retains_supplied_basis_without_research(tmp_path):
    workflow = compile_prompt_workflow(
        source(
            task(
                "research",
                fmt="json",
                authoring_template="mcp-task",
                mcp_server="docs",
                mcp_completion_policy=POLICY,
            )
        )
    )
    execution, gateway, events, requests = run(
        tmp_path,
        workflow,
        [
            supplied("Unformatted analysis"),
            done('{"summary":"Unformatted analysis"}', ()),
        ],
    )
    asyncio.run(execution)
    assert gateway.calls == []
    assert len(requests) == 2 and requests[1][1] == []
    assert any(e["kind"] == "task_response_format_repair" for e in events)
    assert (
        next(e for e in events if e["kind"] == "task_completion_evidence")["basis"]
        == "supplied_inputs"
    )


def test_failed_research_cannot_be_hidden_as_supplied_input_completion(tmp_path):
    from tool_registry.gateway_models import GatewayToolResult

    execution, gateway, events, _ = run(
        tmp_path,
        plan(mcp_completion_policy=POLICY),
        [call(), supplied()],
        result=GatewayToolResult(
            content=({"type": "text", "text": "Unavailable"},), is_error=True
        ),
    )
    with pytest.raises(
        WorkflowSourceExecutionError, match="no valid execution evidence"
    ):
        asyncio.run(execution)
    assert len(gateway.calls) == 1
    assert not any(e["kind"] == "task_completion_evidence" for e in events)


def test_readonly_hint_drift_is_rejected_before_dispatch(tmp_path):
    gateway, runner = runtime()
    current = replace(TOOL, annotations={"readOnlyHint": True})
    gateway.list_tools = lambda *_: (current,)

    async def decide(*args, **kwargs):
        nonlocal current
        current = replace(current, annotations={})
        return call()

    async def emit(*args, **kwargs):
        pass

    with pytest.raises(WorkflowSourceExecutionError):
        asyncio.run(
            execute_prompt_workflow(
                service=service(tmp_path),
                workspace_dir=str(tmp_path),
                plan=plan(mcp_completion_policy=POLICY),
                input_values={},
                response_generator=None,
                action_generator=decide,
                tool_runtime=runner,
                on_event=emit,
            )
        )
    assert gateway.calls == []


def test_same_run_resume_keeps_analysis_and_rejects_changed_policy(tmp_path):
    from .test_workflow_execution_continuation import authorize, order
    from .test_workflow_external_action_execution import (
        service as durable_service,
        source as approval_source,
    )

    original = approval_source()
    approval = original[
        original.index("task approve") : original.index(
            "connection package_to_approval"
        )
    ]
    text = (
        source(
            task(
                "research",
                fmt="text",
                save_output=True,
                authoring_template="mcp-task",
                mcp_server="docs",
                mcp_completion_policy=POLICY,
            ),
            approval,
            task("final", fmt="text"),
        )
        + order("wait", "research", "approve")
        + order("continue", "approve", "final")
    )
    workflow = replace(
        compile_prompt_workflow(text), definition_digest=canonical_digest(text)
    )
    gateway, runner = runtime()
    gateway.list_tools = lambda *_: (replace(TOOL, annotations={"readOnlyHint": True}),)
    decisions = []

    async def decide(*args, **kwargs):
        decisions.append(1)
        return supplied()

    async def generate(*args, **kwargs):
        return "Post-review report"

    async def execute(selected, **kwargs):
        return await execute_prompt_workflow(
            service=durable_service(tmp_path),
            workspace_dir=str(tmp_path),
            plan=selected,
            input_values={},
            response_generator=generate,
            action_generator=decide,
            tool_runtime=runner,
            **kwargs,
        )

    first = asyncio.run(execute(workflow))
    checkpoint = authorize(durable_service(tmp_path), first)
    frozen = json.loads(json.dumps(checkpoint["continuation"]))
    changed_text = text.replace(POLICY, "tool_evidence_required")
    changed = replace(
        compile_prompt_workflow(changed_text),
        definition_digest=canonical_digest(changed_text),
    )
    with pytest.raises(
        WorkflowSourceExecutionError, match="definition or inputs changed"
    ):
        asyncio.run(
            execute(changed, continuation=frozen, completed_checkpoint=checkpoint)
        )
    final = asyncio.run(
        execute(workflow, continuation=frozen, completed_checkpoint=checkpoint)
    )
    assert final["run_id"] == first["run_id"]
    assert len(decisions) == 1 and gateway.calls == []
    assert final["steps"][0]["tool_calls"] == []
