"""A fixed versioned question can depend only on typed upstream requirement fields."""

import asyncio
from dataclasses import asdict, replace
import json

import pytest

from core.process_validation import canonical_digest
from workspace_service.process_interfaces import ProcessInterfaceService
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.process_interfaces.interactions import (
    input_subject,
)
from workspace_service.workflow_human_input_runtime import (
    evaluate_input_condition,
)
from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    _parse,
    compile_prompt_workflow,
    execute_prompt_workflow,
)
from workspace_service.workflow_run_record import (
    record_workflow_run,
    record_workflow_resume,
)
from packages.workspace_service.tests.test_process_human_input_source import (
    human_source,
)
from packages.workspace_service.tests.test_process_interface_continuation import (
    case,
    two_checkpoint_source,
)
from packages.workspace_service.tests.test_workflow_artifact_review import section
from packages.workspace_service.tests.test_workflow_external_action_execution import (
    service,
)


WHEN = {
    "kind": "unresolved_fields",
    "source": "first.first_out",
    "fields": ["selection"],
}


def conditional_source(mutator=None, *, base_source=None):
    blocks = _parse(base_source or human_source())
    first = next(b["fields"] for b in blocks if b["id"] == "first")
    first["settings"]["output_format"] = "json"
    first["settings"]["output_filename"] = "first.json"
    first["outputs"][0]["kind"] = "structured_result"
    choice = next(b["fields"] for b in blocks if b["id"] == "choice")
    choice["inputs"][0]["kind"] = "structured_result"
    choice["settings"]["human_interaction"].update(version=3, when=WHEN)
    if mutator:
        mutator(choice["settings"]["human_interaction"])
    return "".join(section(b["kind"], b["id"], **b["fields"]) for b in blocks)


def resolution(*, unresolved=True):
    return {
        "version": "wright.requirements-resolution/1",
        "unresolved_fields": ["selection"] if unresolved else [],
        "resolved_values": {} if unresolved else {"selection": "a"},
    }


@pytest.mark.parametrize(
    "when",
    [
        {**WHEN, "kind": "python", "expression": "run arbitrary code"},
        {**WHEN, "source": "missing.output"},
        {**WHEN, "source": "first.first_out.extra"},
        {**WHEN, "fields": ["other"]},
        {**WHEN, "fields": ["selection", "selection"]},
        {**WHEN, "fields": []},
        None,
    ],
)
def test_malformed_condition_rejected_before_execution(when):
    with pytest.raises(WorkflowSourceExecutionError) as error:
        compile_prompt_workflow(
            conditional_source(lambda declaration: declaration.update(when=when))
        )
    assert error.value.code == "WORKFLOW_NOT_READY"


def test_condition_cannot_read_unconnected_or_untyped_output():
    for source in (human_source(), conditional_source()):
        blocks = _parse(source)
        choice = next(b["fields"] for b in blocks if b["id"] == "choice")
        choice["settings"]["human_interaction"].update(version=3, when=WHEN)
        if source == conditional_source():
            next(b["fields"] for b in blocks if b["id"] == "evidence").update(
                type="order", **{"from": "first", "to": "choice"}
            )
        text = "".join(section(b["kind"], b["id"], **b["fields"]) for b in blocks)
        with pytest.raises(
            WorkflowSourceExecutionError, match="connected structured upstream evidence"
        ):
            compile_prompt_workflow(text)


@pytest.mark.parametrize(
    "change",
    [
        {"version": "unknown"},
        {"unresolved_fields": ["unplanned_question"]},
        {"unresolved_fields": ["selection", "selection"]},
        {"unresolved_fields": [], "resolved_values": {}},
        {"unresolved_fields": [], "resolved_values": {"selection": "c"}},
        {"resolved_values": {"selection": "a"}},
        {"resolved_values": {"unplanned_question": "not declared"}},
        {"extra": "Do not invent another question"},
    ],
)
def test_invalid_requirement_result_never_creates_an_implicit_question(change):
    step = compile_prompt_workflow(conditional_source()).steps[1]
    value = {**resolution(), **change}
    with pytest.raises(WorkflowSourceExecutionError) as error:
        evaluate_input_condition(step=step, responses={"first.first_out": value})
    assert error.value.code == "WORKFLOW_INPUT_CONDITION_INVALID"


def start(c, events, calls, value):
    async def generate(prompt, fmt):
        calls.append(prompt)
        return (
            json.dumps(value)
            if fmt == "json"
            else "Synthetic selected comparison report."
        )

    async def observe(event):
        events.append(event)

    async def execute(emit, checkpoint=None):
        return await execute_prompt_workflow(
            service=c.app,
            workspace_dir=str(c.root),
            plan=c.plan,
            input_values=c.values,
            response_generator=generate,
            on_event=emit,
            run_id="conditional-same-run",
            continuation=checkpoint.continuation if checkpoint else None,
            completed_checkpoint=asdict(checkpoint) if checkpoint else None,
        )

    first = asyncio.run(
        record_workflow_run(
            service=c.app,
            workspace_dir=str(c.root),
            workspace_id="ws",
            source_path=c.frozen.process.source_path,
            source_digest=c.plan.definition_digest,
            execute=execute,
            on_event=observe,
            run_id="conditional-same-run",
            required_step_ids=[s.id for s in c.plan.steps],
        )
    )
    return first, execute, observe


def test_fully_resolved_requirement_skips_and_publishes_actual_values_without_human_authority(
    tmp_path,
):
    c = case(tmp_path, source_text=conditional_source(), build_checkpoint=False)
    events, calls = [], []
    final, _, _ = start(c, events, calls, resolution(unresolved=False))
    assert final["status"] == "completed" and len(calls) == 2
    assert '"selection":"a"' in calls[-1]
    assert not any(e["kind"] == "input_requested" for e in events)
    skipped = next(s for s in final["steps"] if s["task_id"] == "choice")
    assert skipped["execution_kind"] == "human_input_skipped"
    assert skipped["condition_evaluation"]["decision"] == "skip"
    assert json.loads(skipped["response"]) == {"selection": "a"}
    assert not {"checkpoint_id", "response_id", "actor", "review_authority"} & set(
        skipped
    )
    result = next(r for r in final["results"] if r["provenance"]["task_id"] == "choice")
    assert result["kind"] == "structured" and result["artifact_role"] == "intermediate"
    assert any(
        e["kind"] == "input_condition_evaluated"
        and e["evaluation"]["decision"] == "skip"
        for e in events
    )
    log = json.loads((tmp_path / final["run_log_path"]).read_text())
    assert "input_checkpoint" not in log


def test_unresolved_requirement_waits_with_exact_evaluation_then_recreates_and_resumes_same_run(
    tmp_path,
):
    c = case(tmp_path, source_text=conditional_source(), build_checkpoint=False)
    events, calls = [], []
    first, execute, observe = start(c, events, calls, resolution())
    assert first["status"] == "waiting_human" and len(calls) == 1
    checkpoint = c.owner.get(
        first["input_checkpoint"]["checkpoint_id"],
        workspace_id="ws",
        run_id="conditional-same-run",
    )
    subject = input_subject(checkpoint.subject)
    assert subject.condition_evaluation.decision == "ask"
    assert (
        subject.condition_evaluation.source_digest
        == subject.upstream_digests[WHEN["source"]]
    )
    assert subject.declaration.response_schema["required"] == ["selection"]

    arguments = dict(
        workspace_id="ws",
        run_id="conditional-same-run",
        expected_subject_digest=checkpoint.subject_digest,
        value={"selection": "b"},
        actor="isolated-test-actor",
        reason="Synthetic predetermined requirement answer.",
        request_id="conditional-answer",
        integration_test=True,
    )
    with pytest.raises(ProcessInterfaceError) as error:
        c.owner.respond(
            checkpoint.checkpoint_id,
            **{**arguments, "expected_subject_digest": "b" * 64},
        )
    assert error.value.reason.code == "SUBJECT_STALE"
    with pytest.raises(ProcessInterfaceError) as error:
        c.owner.respond(checkpoint.checkpoint_id, **{**arguments, "value": {}})
    assert error.value.reason.code == "RESPONSE_INVALID"
    assert (
        c.owner.get(
            checkpoint.checkpoint_id, workspace_id="ws", run_id="conditional-same-run"
        )
        == checkpoint
    )

    _, answer, _ = c.owner.respond(checkpoint.checkpoint_id, **arguments)
    c.app = service(tmp_path)
    c.app.db_path = c.db_path
    c.app.process_interfaces = ProcessInterfaceService(c.app)
    c.owner = c.app.process_interfaces.human_inputs
    consumed = c.owner.consume(
        checkpoint.checkpoint_id,
        workspace_id="ws",
        run_id="conditional-same-run",
        response_id=answer.response_id,
    )

    def resume():
        return asyncio.run(
            record_workflow_resume(
                service=c.app,
                workspace_dir=str(tmp_path),
                workspace_id="ws",
                checkpoint=consumed,
                execute=lambda emit: execute(emit, consumed),
                on_event=observe,
            )
        )

    final = resume()
    assert final["status"] == "completed" and final["run_id"] == first["run_id"]
    assert final["run_log_path"] == first["run_log_path"] and len(calls) == 2
    assert '"selection":"b"' in calls[-1]
    answered = next(s for s in final["steps"] if s["task_id"] == "choice")
    assert (
        answered["condition_evaluation"] == checkpoint.subject["condition_evaluation"]
    )
    assert canonical_digest(resume()) == canonical_digest(final) and len(calls) == 2


def test_condition_subject_cannot_change_evidence_or_transform_skip_into_wait(tmp_path):
    c = case(tmp_path, source_text=conditional_source(), build_checkpoint=False)
    first, _, _ = start(c, [], [], resolution())
    checkpoint = c.owner.get(
        first["input_checkpoint"]["checkpoint_id"],
        workspace_id="ws",
        run_id="conditional-same-run",
    )
    for change in [
        {"source_digest": "a" * 64},
        {
            "decision": "skip",
            "unresolved_fields": [],
            "resolved_values": {"selection": "a"},
        },
    ]:
        subject = {
            **checkpoint.subject,
            "condition_evaluation": {
                **checkpoint.subject["condition_evaluation"],
                **change,
            },
        }
        with pytest.raises(ValueError):
            input_subject(subject)
    edited = {
        **checkpoint.continuation,
        "responses": {
            **checkpoint.continuation["responses"],
            WHEN["source"]: {
                "type": "json",
                "value": json.dumps(resolution(unresolved=False)),
            },
        },
    }
    tampered = replace(checkpoint, continuation=edited)
    with pytest.raises(ProcessInterfaceError, match="evidence is inconsistent"):
        c.owner._validate(tampered)


def test_recorded_conditional_skip_survives_a_later_wait_and_service_recreation(
    tmp_path,
):
    c = case(
        tmp_path,
        source_text=conditional_source(base_source=two_checkpoint_source()),
        build_checkpoint=False,
    )
    events, calls = [], []
    waiting, execute, observe = start(c, events, calls, resolution(unresolved=False))
    assert waiting["status"] == "waiting_human" and len(calls) == 2
    checkpoint_id = waiting["input_checkpoint"]["checkpoint_id"]
    checkpoint = c.owner.get(
        checkpoint_id, workspace_id="ws", run_id="conditional-same-run"
    )
    assert checkpoint.step_id == "choice_two"
    assert checkpoint.continuation["completed_step_ids"] == [
        "first",
        "choice",
        "second",
    ]
    skipped = next(
        r for r in checkpoint.continuation["records"] if r["task_id"] == "choice"
    )
    assert skipped["execution_kind"] == "human_input_skipped"
    assert skipped["condition_evaluation"]["decision"] == "skip"
    _, answer, _ = c.owner.respond(
        checkpoint_id,
        workspace_id="ws",
        run_id="conditional-same-run",
        expected_subject_digest=checkpoint.subject_digest,
        value={"selection": "b"},
        actor="isolated-test-actor",
        reason="Synthetic response after recorded conditional skip.",
        request_id="after-skip-answer",
        integration_test=True,
    )
    c.app = service(tmp_path)
    c.app.db_path = c.db_path
    c.app.process_interfaces = ProcessInterfaceService(c.app)
    c.owner = c.app.process_interfaces.human_inputs
    consumed = c.owner.consume(
        checkpoint_id,
        workspace_id="ws",
        run_id="conditional-same-run",
        response_id=answer.response_id,
    )

    def resume():
        return asyncio.run(
            record_workflow_resume(
                service=c.app,
                workspace_dir=str(tmp_path),
                workspace_id="ws",
                checkpoint=consumed,
                execute=lambda emit: execute(emit, consumed),
                on_event=observe,
            )
        )

    final = resume()
    assert final["status"] == "completed" and len(calls) == 3
    assert '"selection":"b"' in calls[-1]
    assert next(s for s in final["steps"] if s["task_id"] == "choice") == skipped
    assert canonical_digest(resume()) == canonical_digest(final) and len(calls) == 3
    assert len([e for e in events if e["kind"] == "input_condition_evaluated"]) == 1
