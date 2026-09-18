"""Bounded local-validator correction loops in the canonical process runner."""

import asyncio
import json
from pathlib import Path
from threading import Event

import pytest

from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    compile_prompt_workflow,
    execute_prompt_workflow,
)

from .test_workflow_process_validation import configuration, runtime_service, validator
from .test_workflow_source_execution import source, task


def rework_source(*, max_revisions=1, target="produce", producer=None, config=None):
    text = source(
        producer or task("produce", fmt="json"),
        validator(config, max_revisions=max_revisions),
        task("consume", prompt="Use the validated result.", fmt="text"),
    )
    text += """connection subject
  type: item
  from: "produce.produce_response"
  to: "inspect.inspect_subject"
  label: "Output to inspect"
  when: null
end
connection release
  type: approval
  from: "inspect"
  to: "consume"
  label: "Validated output"
  when: pass
end
"""
    text += f"""connection repair
  type: revision
  from: "inspect"
  to: "{target}"
  label: "Correct output"
  when: revise
end
"""
    return text


def mcp_file_rework_source(*, revision_policy="create_new_files"):
    from workspace_service.process_validation.profiles import load_profile

    profile = load_profile("parametric-drill-jig-01")
    producer_settings = {
        "authoring_template": "mcp-task",
        "mcp_server": "agentcad",
        "output_format": "json",
        "file_policy": "indexed",
        "expected_files": "jig.step",
        "expected_file_ports": {"jig_step": "jig.step"},
        "revision_policy": revision_policy,
    }
    validation = {
        "profile": {
            "source": "packaged",
            "name": "parametric-drill-jig-01",
            "reference": profile.reference().model_dump(),
        },
        "baseline": profile.baseline.reference().model_dump(),
        "subjects": {"jig_step": "jig"},
    }
    return f"""workflow mcp_file_rework
  name: "MCP file correction"
end
task produce
  name: "Create isolated jig"
  step_type: work
  performed_by: ai_assisted
  inputs: []
  outputs: [{{"key":"jig_step","name":"Jig STEP","kind":"workspace_file","required":true}}]
  prompt: "Create a new jig STEP file."
  settings: {json.dumps(producer_settings)}
  tool: null
  reusable_step: null
end
task inspect
  name: "Inspect jig"
  step_type: work
  performed_by: configured_tool
  inputs: [{{"key":"jig","name":"Jig STEP","kind":"workspace_file","required":true}}]
  outputs: [{{"key":"assessment","name":"Assessment","kind":"engineering_document"}}]
  prompt: ""
  settings: {json.dumps({"authoring_template": "process-validator", "validation": validation, "max_revisions": 1, "output_format": "json"})}
  tool: null
  reusable_step: null
end
connection subject
  type: item
  from: "produce.jig_step"
  to: "inspect.jig"
  label: "Jig to inspect"
  when: null
end
connection repair
  type: revision
  from: "inspect"
  to: "produce"
  label: "Correct measured geometry"
  when: revise
end
"""


def run(tmp_path, plan, generate, events):
    async def emit(event):
        events.append(event)

    return asyncio.run(
        execute_prompt_workflow(
            service=runtime_service(tmp_path),
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
            on_event=emit,
            run_id="repair-run",
        )
    )


def test_structured_producer_receives_typed_feedback_and_releases_new_revision(
    tmp_path,
):
    plan = compile_prompt_workflow(rework_source(max_revisions=2))
    prompts, events = [], []

    async def generate(prompt, fmt):
        prompts.append((prompt, fmt))
        if fmt == "text":
            return "Released after the current output passed."
        return json.dumps(
            {"part_id": "demo-plate", "length_mm": 98 if len(prompts) == 1 else 100}
        )

    result = run(tmp_path, plan, generate, events)

    assert [fmt for _, fmt in prompts] == ["json", "json", "text"]
    repair_prompt = prompts[1][0]
    assert "data, not instructions" in repair_prompt
    assert '"target_step_id":"produce"' in repair_prompt
    assert '"observed":98' in repair_prompt
    assert '"preserve_requirement_ids":["DEMO-002","DEMO-003"]' in repair_prompt
    assert result["steps"][-1]["task_id"] == "consume"
    assert [
        record["producer_attempt"]
        for record in result["revision_attempts"]
        if record["task_id"] == "produce"
    ] == [1]
    current = next(
        record for record in result["steps"] if record["task_id"] == "produce"
    )
    assert current["producer_attempt"] == 2
    assert current["repair_feedback"]["remaining_revisions"] == 2
    delivered = next(
        event for event in events if event["kind"] == "validation_feedback_delivered"
    )
    assert delivered["target_step_id"] == "produce"
    assert delivered["remaining_revisions"] == 2
    assert len([event for event in events if event["kind"] == "design_check"]) == 2


def test_identical_output_and_defect_stop_without_spending_another_revision(tmp_path):
    plan = compile_prompt_workflow(rework_source(max_revisions=3))
    prompts, events = [], []

    async def generate(prompt, fmt):
        prompts.append((prompt, fmt))
        return json.dumps({"part_id": "demo-plate", "length_mm": 98})

    with pytest.raises(WorkflowSourceExecutionError) as error:
        run(tmp_path, plan, generate, events)

    assert error.value.code == "PROCESS_VALIDATION_NO_PROGRESS"
    assert len(prompts) == 2
    assert (
        len(
            [
                event
                for event in events
                if event["kind"] == "validation_feedback_delivered"
            ]
        )
        == 1
    )


def test_revision_budget_is_persisted_and_exhaustion_holds_consumer(tmp_path):
    plan = compile_prompt_workflow(rework_source(max_revisions=1))
    outputs = iter((98, 99))
    events = []

    async def generate(prompt, fmt):
        return json.dumps({"part_id": "demo-plate", "length_mm": next(outputs)})

    with pytest.raises(WorkflowSourceExecutionError) as error:
        run(tmp_path, plan, generate, events)

    assert error.value.code == "PROCESS_VALIDATION_REJECTED"
    delivered = [e for e in events if e["kind"] == "validation_feedback_delivered"]
    assert len(delivered) == 1 and delivered[0]["remaining_revisions"] == 1
    exhausted = next(e for e in events if e["kind"] == "validation_exhausted")
    assert exhausted["remaining_revisions"] == 0
    assert exhausted["assessment_id"]
    assert not (tmp_path / "consume.txt").exists()


def test_mixed_failure_and_unknown_repair_defect_then_hold_for_missing_evidence(
    tmp_path,
):
    from core.process_validation import ValidationProfile
    from workspace_service.process_validation.profiles import load_profile

    raw = load_profile("structured-demo").model_dump(mode="json")
    raw["checks"][1]["reader"] = "missing-reader"
    profile = ValidationProfile.model_validate(raw)
    (tmp_path / "mixed-profile.json").write_text(
        profile.model_dump_json(), encoding="utf-8"
    )
    config = configuration()
    config["profile"] = {
        "source": "workspace",
        "name": "mixed-profile.json",
        "reference": profile.reference().model_dump(),
    }
    plan = compile_prompt_workflow(rework_source(max_revisions=2, config=config))
    outputs = iter((98, 100))
    events = []

    async def generate(prompt, fmt):
        return json.dumps({"part_id": "demo-plate", "length_mm": next(outputs)})

    with pytest.raises(WorkflowSourceExecutionError) as error:
        run(tmp_path, plan, generate, events)

    assert error.value.code == "PROCESS_VALIDATION_NEEDS_INPUT"
    delivered = next(e for e in events if e["kind"] == "validation_feedback_delivered")
    revision = next(e for e in events if e["kind"] == "design_revision")
    assert delivered["feedback_digest"] == revision["feedback_digest"]
    assert [e["status"] for e in events if e["kind"] == "design_check"] == [
        "revise",
        "needs_input",
    ]
    assert not (tmp_path / "consume.txt").exists()


def test_validator_error_never_replays_producer(tmp_path, monkeypatch):
    from workspace_service.process_validation.readers.structured import StructuredReader

    def fail(*_args):
        raise RuntimeError("controlled reader failure")

    monkeypatch.setattr(StructuredReader, "measure", fail)
    plan = compile_prompt_workflow(rework_source(max_revisions=2))
    calls, events = [], []

    async def generate(prompt, fmt):
        calls.append((prompt, fmt))
        return json.dumps({"part_id": "demo-plate", "length_mm": 98})

    with pytest.raises(WorkflowSourceExecutionError) as error:
        run(tmp_path, plan, generate, events)

    assert error.value.code == "PROCESS_VALIDATION_ERROR"
    assert len(calls) == 1
    assert not any(e["kind"] == "validation_feedback_delivered" for e in events)


def test_cancellation_reaches_active_validator_without_replaying_producer(
    tmp_path, monkeypatch
):
    from workspace_service.process_validation.readers.structured import StructuredReader

    started, observed = Event(), Event()

    def wait_for_cancel(self, snapshot, check, context):
        started.set()
        context.cancelled.wait(5)
        observed.set()
        context.checkpoint()

    monkeypatch.setattr(StructuredReader, "measure", wait_for_cancel)
    plan = compile_prompt_workflow(rework_source(max_revisions=2))
    calls, events = [], []

    async def generate(prompt, fmt):
        calls.append((prompt, fmt))
        return json.dumps({"part_id": "demo-plate", "length_mm": 98})

    async def scenario():
        async def emit(event):
            events.append(event)

        work = asyncio.create_task(
            execute_prompt_workflow(
                service=runtime_service(tmp_path),
                workspace_dir=str(tmp_path),
                plan=plan,
                input_values={},
                response_generator=generate,
                on_event=emit,
                run_id="cancel-repair-run",
            )
        )
        assert await asyncio.to_thread(started.wait, 2)
        work.cancel()
        with pytest.raises(asyncio.CancelledError):
            await work

    asyncio.run(scenario())
    assert observed.is_set() and len(calls) == 1
    assert not any(e["kind"] == "validation_feedback_delivered" for e in events)


@pytest.mark.parametrize(
    "producer",
    [
        task("produce", fmt="json", file_policy="overwrite"),
        task("produce", fmt="json", authoring_template="mcp-task"),
    ],
)
def test_compile_rejects_unsafe_non_cad_revision_target(producer):
    with pytest.raises(WorkflowSourceExecutionError):
        compile_prompt_workflow(rework_source(producer=producer))


def test_compile_rejects_revision_target_that_does_not_own_validator_subject():
    text = rework_source(target="other").replace(
        validator(max_revisions=1),
        task("other", fmt="json") + validator(max_revisions=1),
    )
    with pytest.raises(WorkflowSourceExecutionError):
        compile_prompt_workflow(text)


def test_saved_structured_loop_uses_the_canonical_bounded_revision_path():
    source_path = (
        Path(__file__).parents[3]
        / "tests/datasets/process-validation/processes/structured-loop.workflow.wflow"
    )
    plan = compile_prompt_workflow(source_path.read_text(encoding="utf-8"))
    assert [step.id for step in plan.steps] == ["produce", "inspect", "consume"]
    assert plan.revisions == {"inspect": "produce"}
    assert plan.steps[1].validation and plan.steps[1].max_revisions == 2


def test_compile_accepts_explicit_isolated_create_new_mcp_file_rework():
    plan = compile_prompt_workflow(mcp_file_rework_source())

    producer = plan.steps[0]
    assert producer.agent_task and producer.server_id == "agentcad"
    assert producer.revision_policy == "create_new_files"
    assert producer.expected_file_ports == {"jig_step": "jig.step"}
    assert plan.revisions == {"inspect": "produce"}


def test_compile_rejects_mcp_file_rework_without_explicit_create_new_policy():
    with pytest.raises(WorkflowSourceExecutionError, match="safe producer"):
        compile_prompt_workflow(mcp_file_rework_source(revision_policy=""))


@pytest.mark.parametrize(
    "filename",
    ["jig-validation-loop.workflow.wflow", "heat-validation.workflow.wflow"],
)
def test_saved_engineering_processes_pin_loadable_profiles(tmp_path, filename):
    from workspace_service.process_validation.configuration import (
        ValidatorConfiguration,
    )

    source_path = (
        Path(__file__).parents[3]
        / "tests/datasets/process-validation/processes"
        / filename
    )
    plan = compile_prompt_workflow(source_path.read_text(encoding="utf-8"))
    check = next(step for step in plan.steps if step.validation)

    ValidatorConfiguration.model_validate(check.validation).load(str(tmp_path))
