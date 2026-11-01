"""File correction preserves the measured failed attempt, not only its receipt."""

import asyncio
import hashlib
import json
from types import SimpleNamespace
from dataclasses import replace

import pytest

from workspace_service.workflow_run_paths import (
    bind_run_paths,
    bind_attempt_paths,
    reserve_run_paths,
    verify_prior_attempt_files,
)
from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    compile_prompt_workflow,
    execute_prompt_workflow,
)

from .test_workflow_process_validation import runtime_service
from .test_workflow_process_validation_rework import rework_source
from .test_workflow_source_execution import task


def file_rework_source(*, legacy=False, connected_consumer=False):
    output = (
        "measurement.json"
        if legacy
        else "outputs/{{wright.run_id}}/produce/{{wright.producer_attempt}}/measurement.json"
    )
    producer = task(
        "produce",
        prompt="Create the measured result in the declared output file.",
        fmt="json",
        authoring_template="mcp-task",
        mcp_server="measurement-tool",
        file_policy="indexed",
        revision_policy="create_new_files",
        expected_files=output,
        expected_file_ports={"produce_response": output},
        run_path_template="" if legacy else "wright.run-path/2",
    ).replace(
        '"kind":"engineering_document","name":"Response"',
        '"kind":"workspace_file","name":"Response"',
    )
    text = rework_source(producer=producer).replace(
        '"kind":"engineering_document","required":true',
        '"kind":"workspace_file","required":true',
    )
    if connected_consumer:
        consumer = task(
            "consume",
            prompt="Inspect the corrected file using the selected tool.",
            fmt="text",
            authoring_template="mcp-task",
            mcp_server="inspection-tool",
            mcp_file_dependencies={"consume_prompt": {"source": "connected_output"}},
        )
        consumer = consumer.replace(
            '"kind":"engineering_document"', '"kind":"workspace_file"', 1
        )
        text = text.replace(
            task("consume", prompt="Use the validated result.", fmt="text"), consumer
        )
        text += """connection checked_file
  type: item
  from: "produce.produce_response"
  to: "consume.consume_prompt"
  label: "Corrected measured file"
  when: null
end
"""
    return text


def run_files(
    tmp_path,
    *,
    lengths=(98, 100),
    tamper=False,
    events=None,
    writes=None,
    plan=None,
    app=None,
    **execution,
):
    plan = plan or bind_run_paths(
        compile_prompt_workflow(file_rework_source()), "file-repair-run"
    )
    events = [] if events is None else events
    writes = [] if writes is None else writes

    async def run_task(step, prompt, decide, emit, **kwargs):
        if step.id == "consume":
            assert len(writes) == 2
            assert writes[-1][0].relative_to(tmp_path).as_posix() in prompt
            assert hashlib.sha256(writes[-1][0].read_bytes()).hexdigest() in prompt
            assert writes[0][0].relative_to(tmp_path).as_posix() not in prompt
            return "Inspected the corrected file received on the connected port.", []
        data = json.dumps({"part_id": "demo-plate", "length_mm": lengths[len(writes)]})
        if tamper and writes:
            writes[0][0].write_text("incorrectly overwritten", encoding="utf-8")
        path = tmp_path / step.expected_files[0]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding="utf-8")
        writes.append((path, data))
        return "{}", []

    async def generate(prompt, fmt):
        assert len(writes) == 2
        return "Downstream work released after the corrected measurement passed."

    async def emit(event):
        events.append(event)

    result = asyncio.run(
        execute_prompt_workflow(
            service=app or runtime_service(tmp_path),
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
            on_event=emit,
            run_id="file-repair-run",
            action_generator=generate,
            tool_runtime=SimpleNamespace(run_task=run_task),
            **execution,
        )
    )
    return result, writes, events


def test_file_rework_keeps_failed_bytes_and_releases_only_corrected_output(tmp_path):
    result, writes, events = run_files(tmp_path)
    assert len(writes) == 2
    assert writes[0][0].read_text(encoding="utf-8") == writes[0][1]
    assert writes[0][0] != writes[1][0]
    prior = next(r for r in result["revision_attempts"] if r["task_id"] == "produce")
    receipt = prior["produced_files"][0]
    assert (
        hashlib.sha256((tmp_path / receipt["output_path"]).read_bytes()).hexdigest()
        == receipt["sha256"]
    )
    assert result["steps"][-1]["task_id"] == "consume"
    assert len([e for e in events if e["kind"] == "design_check"]) == 2
    assert prior["file_attempt_binding"]["producer_attempt"] == 1
    current = next(r for r in result["steps"] if r["task_id"] == "produce")
    assert current["file_attempt_binding"]["producer_attempt"] == 2
    from workspace_service.process_validation.application import ValidationApplication

    validation = ValidationApplication(
        str(tmp_path / "validation.db"), "workspace", str(tmp_path)
    )
    checks = [e["report"] for e in events if e["kind"] == "design_check"]
    old_assessment, old_current = validation.read(checks[0]["assessment_id"])
    latest_assessment, latest_current = validation.read(checks[1]["assessment_id"])
    assert not old_current and latest_current
    assert not old_assessment.summary.release_eligible
    assert latest_assessment.summary.release_eligible


def test_legacy_file_rework_is_rejected_before_any_provider_effect():
    with pytest.raises(
        WorkflowSourceExecutionError, match="requires wright.run-path/2"
    ):
        compile_prompt_workflow(file_rework_source(legacy=True))


@pytest.mark.parametrize(
    "lengths,code",
    [
        ((98, 98), "PROCESS_VALIDATION_NO_PROGRESS"),
        ((98, 99), "PROCESS_VALIDATION_REJECTED"),
    ],
)
def test_failed_corrections_preserve_all_files_and_hold_downstream(
    tmp_path, lengths, code
):
    writes, events = [], []
    with pytest.raises(WorkflowSourceExecutionError) as error:
        run_files(tmp_path, lengths=lengths, writes=writes, events=events)
    assert error.value.code == code
    assert len(writes) == 2
    assert all(path.read_text(encoding="utf-8") == data for path, data in writes)
    assert not any(e.get("task_id") == "consume" for e in events)
    if lengths[1] == 99:
        assert any(e["kind"] == "validation_exhausted" for e in events)


def test_provider_mutation_of_failed_evidence_blocks_corrected_output(tmp_path):
    events = []
    with pytest.raises(
        WorkflowSourceExecutionError, match="previous producer attempt's file changed"
    ):
        run_files(tmp_path, tamper=True, events=events)
    assert len([e for e in events if e["kind"] == "design_check"]) == 1
    assert not any(e.get("task_id") == "consume" for e in events)


def test_attempt_binding_does_not_change_accepted_plan_and_rejects_replay(tmp_path):
    original = compile_prompt_workflow(file_rework_source())
    plan = bind_run_paths(original, "run-one")
    reserve_run_paths(plan, str(tmp_path), "run-one")
    first = bind_attempt_paths(plan.steps[0], 1, str(tmp_path))
    second = bind_attempt_paths(plan.steps[0], 2, str(tmp_path))
    assert "{{wright.run_id}}" in original.steps[0].expected_files[0]
    assert "{{wright.producer_attempt}}" in plan.steps[0].expected_files[0]
    assert first.expected_files != second.expected_files
    with pytest.raises(WorkflowSourceExecutionError, match="reconcile its outcome"):
        bind_attempt_paths(plan.steps[0], 1, str(tmp_path))
    assert first.expected_file_ports["produce_response"] == first.expected_files[0]


@pytest.mark.parametrize("attempt", [0, 5, -1, True, "2"])
def test_attempt_number_is_typed_and_bounded(tmp_path, attempt):
    plan = bind_run_paths(compile_prompt_workflow(file_rework_source()), "run-one")
    with pytest.raises(WorkflowSourceExecutionError, match="correction bound"):
        bind_attempt_paths(plan.steps[0], attempt, str(tmp_path))
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "path",
    [
        "outputs/{{wright.run_id}}/measurement.json",
        "outputs/{{wright.producer_attempt}}/{{wright.run_id}}/measurement.json",
        "outputs/{{wright.run_id}}/{{wright.producer_attempt}}/{{wright.producer_attempt}}/measurement.json",
        "outputs/{{wright.run_id}}/{{wright.producer_attempt}}",
    ],
)
def test_bad_attempt_templates_rejected_before_provider_call(path):
    text = file_rework_source().replace(
        "outputs/{{wright.run_id}}/produce/{{wright.producer_attempt}}/measurement.json",
        path,
    )
    with pytest.raises(WorkflowSourceExecutionError):
        compile_prompt_workflow(text)


def test_version_one_does_not_interpret_attempt_token():
    plan = compile_prompt_workflow(file_rework_source())
    plan = replace(
        plan, steps=(replace(plan.steps[0], run_path_template="wright.run-path/1"),)
    )
    with pytest.raises(WorkflowSourceExecutionError, match="unsupported Wright token"):
        bind_run_paths(plan, "run-one")


def test_deleted_prior_attempt_is_reported_before_dispatch(tmp_path):
    result, writes, _ = run_files(tmp_path)
    writes[0][0].unlink()
    step = bind_run_paths(
        compile_prompt_workflow(file_rework_source()), "file-repair-run"
    ).steps[0]
    with pytest.raises(WorkflowSourceExecutionError, match="unavailable"):
        verify_prior_attempt_files(step, result["revision_attempts"], str(tmp_path))


def test_downstream_mcp_receives_verified_latest_file_without_guessing_attempt(
    tmp_path,
):
    plan = bind_run_paths(
        compile_prompt_workflow(file_rework_source(connected_consumer=True)),
        "file-repair-run",
    )
    result, writes, _ = run_files(tmp_path, plan=plan)
    consumer = result["steps"][-1]
    assert consumer["execution_kind"] == "mcp_task"
    assert (
        consumer["references"][0]["path"]
        == writes[-1][0].relative_to(tmp_path).as_posix()
    )
    from workspace_service.process_validation.application import ValidationApplication
    from workspace_service.process_validation.process import output_id, register_outputs

    digest = hashlib.sha256(writes[-1][0].read_bytes()).hexdigest()
    assert consumer["verified_file_input_digests"] == [digest]
    application = ValidationApplication(
        str(tmp_path / "validation.db"), "workspace", str(tmp_path)
    )
    identity = output_id("file-repair-run", "consume", 1, "consume_response")
    subject = application.repository.output("workspace", identity)
    assert subject.input_digests == (digest,)
    assert (
        hashlib.sha256(writes[0][0].read_bytes()).hexdigest()
        not in subject.input_digests
    )

    # Re-register a durable record after a JSON round trip, without a tool call.
    restored = json.loads(json.dumps(consumer))
    register_outputs(
        application,
        plan.steps[-1],
        restored,
        "file-repair-run",
        {"consume.consume_response": consumer["response"]},
        {},
        [],
    )
    assert application.repository.output("workspace", identity) == subject

    # Legacy records retain absent evidence even if their reference list exists.
    legacy = {
        key: value
        for key, value in restored.items()
        if key != "verified_file_input_digests"
    }
    register_outputs(
        application,
        plan.steps[-1],
        legacy,
        "legacy-run",
        {"consume.consume_response": consumer["response"]},
        {},
        [],
    )
    assert not application.repository.output(
        "workspace", output_id("legacy-run", "consume", 1, "consume_response")
    ).input_digests


@pytest.mark.parametrize("tamper", [False, True])
def test_review_continuation_retains_attempts_without_repeating_the_producer(
    tmp_path, tamper
):
    from .test_workflow_external_action_execution import (
        source as approval_source,
        service as approval_service,
    )
    from .test_workflow_execution_continuation import authorize, order

    text = approval_source()
    approval = text[
        text.index("task approve") : text.index("connection package_to_approval")
    ]
    # This controlled fixture reconciles only a fake operation in a temporary
    # database. No adapter or device operation is available to this test.
    combined = (
        file_rework_source()
        + approval
        + task("final", fmt="text")
        + order("review", "consume", "approve")
        + order("finish", "approve", "final")
    )
    plan = bind_run_paths(
        replace(compile_prompt_workflow(combined), definition_digest="a" * 64),
        "file-repair-run",
    )
    app = runtime_service(tmp_path)
    owner = approval_service(tmp_path)
    app.files = owner.files
    app.workflow_external_actions = owner.workflow_external_actions
    first, writes, _ = run_files(tmp_path, plan=plan, app=app)
    checkpoint = authorize(app, first)
    if tamper:
        writes[0][0].write_text("changed after review", encoding="utf-8")
    before = list(writes)
    if tamper:
        with pytest.raises(
            WorkflowSourceExecutionError, match="retained correction attempt"
        ):
            run_files(
                tmp_path,
                plan=plan,
                app=app,
                writes=writes,
                continuation=checkpoint["continuation"],
                completed_checkpoint=checkpoint,
            )
    else:
        final, _, _ = run_files(
            tmp_path,
            plan=plan,
            app=app,
            writes=writes,
            continuation=checkpoint["continuation"],
            completed_checkpoint=checkpoint,
        )
        assert final["run_id"] == first["run_id"]
        assert final["revision_attempts"] == first["revision_attempts"]
        assert final["steps"][-1]["task_id"] == "final"
    assert writes == before


def test_verified_segment_repeats_downstream_analysis_and_preserves_attempts(tmp_path):
    """Synthetic file work proves scheduler replay, not CAD or FEA accuracy."""
    original = compile_prompt_workflow(file_rework_source())
    producer, validator_step = original.steps[:2]
    analysis = replace(
        producer,
        id="analysis",
        title="Analyze synthetic design",
        references=(("Current design", "produce.produce_response"),),
        save=False,
        output_path="",
        expected_files=tuple(
            path.replace("/produce/", "/analysis/") for path in producer.expected_files
        ),
        expected_file_ports={
            key: path.replace("/produce/", "/analysis/")
            for key, path in producer.expected_file_ports.items()
        },
        file_dependencies={"produce.produce_response": {"source": "connected_output"}},
    )
    validator_step = replace(
        validator_step,
        validation={
            **validator_step.validation,
            "rework_scope": "verified_segment",
            "repair_subjects": ["result"],
        },
    )
    plan = bind_run_paths(
        replace(original, steps=(producer, analysis, validator_step)), "segment-run"
    )
    from workspace_service.workflow_design_check import validate_rework

    validate_rework(plan.steps, plan.revisions)
    calls, written, consumed = [], [], []

    async def run_task(step, prompt, *args, **kwargs):
        calls.append(step.id)
        if step.id == "produce":
            data = json.dumps(
                {"part_id": "demo-plate", "length_mm": 98 if len(written) == 0 else 100}
            )
        else:
            design_path, design_bytes = written[-1]
            digest = hashlib.sha256(design_bytes).hexdigest()
            assert digest in prompt
            assert design_path.relative_to(tmp_path).as_posix() in prompt
            consumed.append(digest)
            data = json.dumps({"synthetic_input_sha256": digest})
        path = tmp_path / step.expected_files[0]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data)
        written.append((path, data.encode()))
        return "{}", []

    async def generate(*args):
        raise AssertionError("No unrelated model call expected")

    result = asyncio.run(
        execute_prompt_workflow(
            service=runtime_service(tmp_path),
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
            run_id="segment-run",
            tool_runtime=SimpleNamespace(run_task=run_task),
            action_generator=generate,
        )
    )
    assert calls == ["produce", "analysis", "produce", "analysis"]
    assert len(set(consumed)) == 2
    assert len({path for path, _ in written}) == 4
    assert all(path.read_bytes() == data for path, data in written)
    assert {record["task_id"] for record in result["revision_attempts"]} == {
        "produce",
        "analysis",
        "inspect",
    }
    assert result["steps"][1]["verified_file_input_digests"] == [consumed[-1]]
