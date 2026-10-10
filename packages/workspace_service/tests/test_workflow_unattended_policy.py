"""Undeclared model questions fail; they do not become runtime input barriers."""

import json
from dataclasses import replace

import pytest

from agent_adapters.report_generation import WorkflowGeneratedResponse
from core.workflow_step_outcomes import InvalidStepOutcomeError
from agent_adapters.workflow_instructions import (
    embedded_asset,
    embedded_instruction_set,
)

from packages.workspace_service.tests.test_workflow_mcp_integration_restriction import (
    Gateway,
    runtime,
    step,
    tool,
)
from packages.workspace_service.tests.test_workflow_source_execution import (
    service,
    source,
    task,
)
from packages.workspace_service.tests.test_process_run_supervisor import (
    prepared_case,
    start,
)
from packages.workspace_service.tests.test_process_preparation_service import scope
from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    compile_prompt_workflow,
    execute_prompt_workflow,
)


STRICT_POLICY_BODY = embedded_asset(
    embedded_instruction_set(), "policy.require-specified"
).body


def generated(response, *, status="completed", reason=None):
    return WorkflowGeneratedResponse(
        response,
        {"status": "reported", "model": "synthetic-model", "input_tokens": 1},
        outcome={
            "version": "wright.unattended-step/1",
            "status": status,
            "reason": reason,
            "response": response,
        },
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("format", ["text", "markdown", "html", "json"])
async def test_plain_step_question_fails_before_formatting_outputs_or_downstream(
    tmp_path, format
):
    plan = compile_prompt_workflow(
        source(
            task("first", fmt="text", save_output=True),
            task("second", fmt=format, save_output=True),
            task("third", fmt="text"),
            links=[("first", "second"), ("second", "third")],
        )
    )
    calls, events = [], []

    async def generate(prompt, fmt):
        calls.append((prompt, fmt))
        return (
            generated("Retained measured output")
            if len(calls) == 1
            else generated(
                "Choose the allowable load", status="blocked", reason="input_required"
            )
        )

    async def emit(event):
        events.append(event)

    with pytest.raises(WorkflowSourceExecutionError) as caught:
        await execute_prompt_workflow(
            service=service(tmp_path),
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
            on_event=emit,
        )
    assert caught.value.code == "INTERACTION_NOT_DECLARED"
    assert "second" in str(caught.value)
    assert "declare a human-input step" in caught.value.correction
    assert len(calls) == 2
    assert (tmp_path / "first.txt").read_text() == "Retained measured output"
    assert not list(tmp_path.glob("second.*")) and not list(tmp_path.glob("third.*"))
    assert not any(
        e["kind"] in {"input_requested", "approval_requested"} for e in events
    )
    diagnostic = next(e for e in events if e["kind"] == "step_diagnostic")
    assert diagnostic["task_id"] == "second"
    assert diagnostic["diagnostic"] == "Choose the allowable load"


@pytest.mark.asyncio
@pytest.mark.parametrize("when", ["before", "after", "mixed", "repair"])
async def test_mcp_question_has_no_new_form_default_retry_or_tool_dispatch(when):
    # Preserve strict legacy policy for a qualified read-only test operation.
    item = tool(annotations={"readOnlyHint": True})
    gateway = Gateway([item])
    runner = runtime(gateway)
    events, decisions = [], []

    async def emit(kind, **payload):
        events.append((kind, payload))

    async def decide(messages, schemas, **kwargs):
        decisions.append(schemas)
        assert STRICT_POLICY_BODY in messages[0]["content"]
        call = {
            "id": "operation-1",
            "function": {"name": "tool_0", "arguments": "{}"},
        }
        if when in {"after", "repair"} and len(decisions) == 1:
            return {"tool_calls": [call]}
        if when == "repair" and len(decisions) == 2:
            return {
                "content": json.dumps(
                    {
                        "status": "completed",
                        "response": "An observed result",
                        "evidence": [1],
                    }
                )
            }
        value = {
            "status": "blocked",
            "reason": "input_required",
            "response": "Specify the allowable load",
            "evidence": [],
        }
        return {
            "content": json.dumps(value),
            **({"tool_calls": [call]} if when == "mixed" else {}),
        }

    with pytest.raises(WorkflowSourceExecutionError) as caught:
        await runner.run_task(
            replace(step(item), agent_task=True), "Complete", decide, emit
        )
    assert caught.value.code == "INTERACTION_NOT_DECLARED"
    assert len(gateway.calls) == (when in {"after", "repair"})
    assert len(decisions) == {"before": 1, "after": 2, "mixed": 1, "repair": 3}[when]
    assert any(kind == "step_diagnostic" for kind, _ in events)
    assert not any(
        kind in {"input_requested", "approval_requested"} for kind, _ in events
    )
    if when == "repair":
        assert decisions[-1] == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status, reason, expected",
    [
        ("blocked", "capability_unavailable", "TASK_BLOCKED"),
        ("error", "execution_failed", "TASK_FAILED"),
    ],
)
async def test_other_structured_failures_remain_failures(
    tmp_path, status, reason, expected
):
    plan = compile_prompt_workflow(source(task(fmt="text")))

    async def generate(*args):
        return generated("Inspection unavailable", status=status, reason=reason)

    with pytest.raises(WorkflowSourceExecutionError) as caught:
        await execute_prompt_workflow(
            service=service(tmp_path),
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
        )
    assert caught.value.code == expected
    assert not (tmp_path / "report.txt").exists()


@pytest.mark.asyncio
async def test_document_questions_and_json_status_are_not_classified_as_interactions(
    tmp_path,
):
    plan = compile_prompt_workflow(source(task(fmt="json")))
    document = '{"status":"input_required","question":"A survey question?"}'

    async def generate(*args):
        return generated(document)

    result = await execute_prompt_workflow(
        service=service(tmp_path),
        workspace_dir=str(tmp_path),
        plan=plan,
        input_values={},
        response_generator=generate,
    )
    assert len(result["steps"]) == 1
    assert (tmp_path / "report.json").read_text() == document


@pytest.mark.asyncio
async def test_invalid_production_envelope_has_own_output_diagnostic(tmp_path):
    plan = compile_prompt_workflow(source(task(fmt="text")))

    async def generate(*args):
        raise InvalidStepOutcomeError("Invalid model envelope")

    with pytest.raises(WorkflowSourceExecutionError) as caught:
        await execute_prompt_workflow(
            service=service(tmp_path),
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
        )
    assert caught.value.code == "MODEL_OUTCOME_INVALID"
    assert "Model Setup" not in caught.value.correction


@pytest.mark.asyncio
async def test_supervised_failure_survives_reattach_without_invented_input(tmp_path):
    app, reference, frozen = await prepared_case(tmp_path, later=True)
    calls = []

    async def generate(prompt, fmt):
        calls.append(prompt)
        return (
            generated("Retained first result")
            if len(calls) == 1
            else generated(
                "Choose a missing constraint", status="blocked", reason="input_required"
            )
        )

    try:
        receipt = await start(app, reference, frozen, generate)
        view = await app.runs.wait(scope(), reference, receipt.run_id)
        assert view["status"] == "failed"
        assert view["code"] == "INTERACTION_NOT_DECLARED"
        assert "input_checkpoint" not in view
        assert (tmp_path / "first.txt").read_text() == "Retained first result"
        projection = await app.get_snapshot(scope(), reference, run_id=receipt.run_id)
        assert not projection.interactions
        assert not any(a.operation == "respond" for a in projection.actions)
        assert projection.diagnostics[0].code == "INTERACTION_NOT_DECLARED"
        assert projection.diagnostics[0].step_id == "later"
        assert "declare a human-input step" in projection.diagnostics[0].correction
        await app.runs.close()
        from workspace_service.process_interfaces.runs import ProcessRunSupervisor

        app.runs = ProcessRunSupervisor(app)
        retry = await start(app, reference, frozen, generate)
        assert retry == receipt
        attached = await app.runs.wait(scope(), reference, receipt.run_id)
        assert attached["code"] == "INTERACTION_NOT_DECLARED"
        assert len(calls) == 2
    finally:
        await app.close()


@pytest.mark.parametrize("during_repair", [False, True])
def test_declared_082_revision_budget_does_not_authorize_a_runtime_question(
    tmp_path, during_repair
):
    from packages.workspace_service.tests.test_workflow_process_validation_rework import (
        rework_source,
        run,
    )

    plan = compile_prompt_workflow(rework_source(max_revisions=3))
    prompts, events = [], []

    async def generate(prompt, fmt):
        prompts.append(prompt)
        if during_repair and len(prompts) == 1:
            return generated('{"part_id":"demo-plate","length_mm":98}')
        return generated(
            "Choose a different target length",
            status="blocked",
            reason="input_required",
        )

    with pytest.raises(WorkflowSourceExecutionError) as caught:
        run(tmp_path, plan, generate, events)
    assert caught.value.code == "INTERACTION_NOT_DECLARED"
    assert len(prompts) == (2 if during_repair else 1)
    assert len([e for e in events if e["kind"] == "design_check"]) == int(during_repair)
    assert not any(
        e["kind"] in {"input_requested", "approval_requested"} for e in events
    )
    assert not any(e.get("task_id") == "consume" for e in events)
