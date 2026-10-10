"""Rejected model assumptions remain diagnostic evidence, never accepted outputs."""

import asyncio
import json

import pytest

from packages.workspace_service.tests.test_workflow_instruction_settings import profile
from packages.workspace_service.tests.test_workflow_source_execution import (
    service,
    source,
    task,
)
from workspace_service.workflow_instruction_settings import (
    materialize_new_workflow_instructions,
)
from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    compile_prompt_workflow,
    execute_prompt_workflow,
)


@pytest.mark.parametrize(
    "protected,outputs", [(True, ["report_response"]), (False, ["not_declared"])]
)
def test_rejected_assumptions_name_exact_violation_and_retain_redacted_evidence(
    tmp_path, protected, outputs
):
    instructions = profile().model_copy(
        update={
            "policy": profile().policy.model_copy(
                update={"protected_requirements": ("length",) if protected else ()}
            )
        }
    )
    plan = compile_prompt_workflow(
        materialize_new_workflow_instructions(source(task(fmt="text")), instructions)
    )
    events = []

    class Result(str):
        pass

    async def generate(
        prompt, fmt, *, instruction_set, instruction_override, invocation_observer
    ):
        context = json.loads(prompt.split("wright_step_context: ", 1)[1])
        assert context == {
            "step_id": "report",
            "outputs": [
                {"output_id": "report_response", "kind": "engineering_document"}
            ],
            "protected_requirement_identifiers": ["length"] if protected else [],
        }
        generated = Result(
            "A completed model response does not grant output acceptance."
        )
        generated.wright_instructions = instructions.resolve(
            "workflow-task"
        ).model_dump(mode="json")
        generated.wright_assumptions = [
            {
                "parameter": "length",
                "value": "10",
                "units": "mm",
                "rationale": "Unspecified illustrative choice. api_key=super-secret-test-token",
                "affected_outputs": outputs,
            }
        ]
        return generated

    async def emit(event):
        events.append(event)

    with pytest.raises(WorkflowSourceExecutionError) as failure:
        asyncio.run(
            execute_prompt_workflow(
                service=service(tmp_path),
                workspace_dir=str(tmp_path),
                plan=plan,
                input_values={},
                response_generator=generate,
                on_event=emit,
            )
        )
    assert failure.value.code == "WORKFLOW_ASSUMPTION_INVALID"
    assert "length" in str(failure.value)
    assert ("protected requirement" if protected else "not_declared") in str(
        failure.value
    )
    rejection = next(
        event for event in events if event["kind"] == "assumptions_rejected"
    )
    assert rejection["task_id"] == "report"
    assert rejection["diagnostic"]["violations"] == [
        {
            "parameter": "length",
            "protected_requirement": protected,
            "undeclared_outputs": [] if protected else ["not_declared"],
        }
    ]
    assert "super-secret-test-token" not in str(rejection)
    assert not any(
        event["kind"]
        in {"assumptions_recorded", "result_ready", "step_completed", "input_requested"}
        for event in events
    )
    assert not (tmp_path / "report.txt").exists()
