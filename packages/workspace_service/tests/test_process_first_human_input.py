"""Versioned initial questions use the ordinary durable source run and checkpoint."""

import asyncio
from dataclasses import asdict, replace
import hashlib
import json

import pytest

from core.process_interactions import InputSnapshot, ProcessRef
from core.process_validation import canonical_digest
from workspace_service.process_interfaces import ProcessInterfaceService
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.process_interfaces.inputs import prepare_inputs
from workspace_service.process_interfaces.interactions import (
    input_subject,
    input_subject_digest,
)
from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    _parse,
    compile_prompt_workflow,
    execute_prompt_workflow,
    validate_workspace_authoring_shape,
)
from workspace_service.workflow_run_record import (
    record_workflow_run,
    record_workflow_resume,
)
from packages.workspace_service.tests.test_process_human_input_source import (
    DECLARATION,
    human_source,
)
from packages.workspace_service.tests.test_process_interface_continuation import (
    case as upstream_case,
)
from packages.workspace_service.tests.test_workflow_artifact_review import section, port
from packages.workspace_service.tests.test_workflow_external_action_execution import (
    service,
)


def first_input_source(*, version=2, required_evidence=False):
    text = section(
        "workflow",
        "initial_question",
        name="Choose the report focus",
        purpose="A declared first question supplies the report's focus.",
        discipline="engineering",
        reviewed_ai_suggestions=False,
    )
    text += section(
        "task",
        "choice",
        name="Choose report focus",
        purpose="Request input",
        step_type="work",
        group=None,
        performed_by="engineer",
        inputs=[port("choice_evidence", True)] if required_evidence else [],
        outputs=[{**port("choice_response", True), "kind": "structured_result"}],
        instructions="Choose the comparison to summarize.",
        tool=None,
        reusable_step=None,
        settings={
            "authoring_template": "human-input",
            "human_interaction": {**DECLARATION, "version": version},
        },
    )
    text += section(
        "task",
        "report",
        name="Summarize chosen comparison",
        purpose="Use the declared response",
        step_type="work",
        group=None,
        performed_by="ai_assisted",
        inputs=[{**port("report_input", True), "kind": "structured_result"}],
        outputs=[port("report_output")],
        prompt="Summarize the supplied selection.",
        tool=None,
        reusable_step=None,
        settings={"output_format": "text", "output_filename": "report.txt"},
    )
    return text + section(
        "connection",
        "choice_to_report",
        type="item",
        **{"from": "choice.choice_response", "to": "report.report_input"},
        label="Declared response",
        when=None,
    )


def initial_case(root):
    app = service(root)
    app.db_path = str(root / "state.db")
    app.process_interfaces = ProcessInterfaceService(app)
    source = first_input_source()
    validate_workspace_authoring_shape(source)
    frozen = InputSnapshot.create(
        snapshot_id="initial-inputs",
        process=ProcessRef(
            workspace_id="ws",
            source_path="workflows/initial-input.wflow",
            source_digest=hashlib.sha256(source.encode()).hexdigest(),
        ),
        created_at="2026-10-07T12:00:00Z",
        bindings=(),
    )
    app.process_interfaces.inputs.put_snapshot(frozen)
    plan = replace(
        compile_prompt_workflow(source),
        definition_digest=frozen.process.source_digest,
        input_snapshot=frozen,
    )
    return app, frozen, plan


def test_version_two_first_question_has_no_fake_producer_and_is_ready(tmp_path):
    app, frozen, plan = initial_case(tmp_path)
    assert [step.id for step in plan.steps] == ["choice", "report"]
    assert plan.steps[0].references == () and plan.inputs == {}
    prepared = asyncio.run(
        prepare_inputs(
            service=app,
            workspace_dir=str(tmp_path),
            process=frozen.process,
            source=first_input_source(),
        )
    )
    assert not prepared.reasons and prepared.values == {}
    dependency = next(
        d for d in prepared.dependencies if d.binding_id == "report.report_input"
    )
    assert dependency.classification == "declared_human_response"
    assert dependency.interaction_step == "choice"


@pytest.mark.parametrize("version,required", [(1, False), (2, True)])
def test_first_question_does_not_erase_legacy_or_required_evidence_contract(
    version, required
):
    with pytest.raises(
        WorkflowSourceExecutionError, match="connected upstream evidence"
    ):
        compile_prompt_workflow(
            first_input_source(version=version, required_evidence=required)
        )


def test_legacy_subject_digest_and_upstream_requirement_are_preserved(tmp_path):
    c = upstream_case(tmp_path, source_text=human_source())
    assert input_subject(c.checkpoint.subject).declaration.version == 1
    assert input_subject_digest(c.checkpoint.subject) == canonical_digest(
        c.checkpoint.subject
    )
    assert (
        input_subject(c.checkpoint.subject).model_dump(mode="json")
        == c.checkpoint.subject
    )
    invalid = {**c.checkpoint.subject, "upstream_digests": {}}
    with pytest.raises(ValueError, match="Version 1"):
        input_subject(invalid)


def test_version_two_still_binds_actual_upstream_evidence(tmp_path):
    blocks = _parse(human_source())
    next(block["fields"] for block in blocks if block["id"] == "choice")["settings"][
        "human_interaction"
    ]["version"] = 2
    source = "".join(
        section(block["kind"], block["id"], **block["fields"]) for block in blocks
    )
    c = upstream_case(tmp_path, source_text=source)
    checked = input_subject(c.checkpoint.subject)
    assert checked.declaration.version == 2
    assert set(checked.upstream_digests) == {"first.first_out"}
    assert (
        c.owner.get(
            c.checkpoint.checkpoint_id, workspace_id="ws", run_id=c.checkpoint.run_id
        )
        == c.checkpoint
    )


def test_first_question_waits_then_restarts_and_resumes_same_run_without_replay(
    tmp_path,
):
    app, frozen, plan = initial_case(tmp_path)
    calls, events = [], []

    async def generate(prompt, fmt):
        calls.append(prompt)
        return "Synthetic comparison report."

    async def observe(event):
        events.append(event)

    async def execute(emit, checkpoint=None):
        return await execute_prompt_workflow(
            service=app,
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
            on_event=emit,
            run_id="initial-same-run",
            continuation=checkpoint.continuation if checkpoint else None,
            completed_checkpoint=asdict(checkpoint) if checkpoint else None,
        )

    first = asyncio.run(
        record_workflow_run(
            service=app,
            workspace_dir=str(tmp_path),
            workspace_id="ws",
            source_path=frozen.process.source_path,
            source_digest=plan.definition_digest,
            execute=execute,
            on_event=observe,
            run_id="initial-same-run",
            required_step_ids=[step.id for step in plan.steps],
        )
    )
    assert first["status"] == "waiting_human" and calls == []
    checkpoint_id = first["input_checkpoint"]["checkpoint_id"]
    owner = app.process_interfaces.human_inputs
    checkpoint = owner.get(checkpoint_id, workspace_id="ws", run_id="initial-same-run")
    assert checkpoint.subject["upstream_digests"] == {}
    assert checkpoint.continuation["next_step_index"] == 0
    assert checkpoint.continuation["completed_step_ids"] == []
    assert checkpoint.external_action is None

    def respond(**changes):
        return owner.respond(
            checkpoint_id,
            **{
                "workspace_id": "ws",
                "run_id": "initial-same-run",
                "expected_subject_digest": checkpoint.subject_digest,
                "value": {"selection": "a"},
                "actor": "isolated-test-actor",
                "reason": "Predetermined synthetic input; no engineering approval.",
                "request_id": "initial-response",
                "integration_test": True,
                **changes,
            },
        )

    for changes, code in [
        ({"value": {}}, "RESPONSE_INVALID"),
        ({"expected_subject_digest": "b" * 64}, "SUBJECT_STALE"),
        ({"run_id": "different-run"}, "SCOPE_DENIED"),
    ]:
        with pytest.raises(ProcessInterfaceError) as error:
            respond(**changes)
        assert error.value.reason.code == code
        assert (
            owner.get(checkpoint_id, workspace_id="ws", run_id="initial-same-run")
            == checkpoint
        )

    pending, answer, created = respond()
    assert created and respond() == (pending, answer, False)
    with pytest.raises(ProcessInterfaceError) as error:
        respond(value={"selection": "b"})
    assert error.value.reason.code == "REQUEST_CONFLICT"

    # Service recreation reads the response and exact zero-producer snapshot from
    # SQLite. No browser state or retained model output is needed to resume.
    app = service(tmp_path)
    app.db_path = str(tmp_path / "state.db")
    app.process_interfaces = ProcessInterfaceService(app)
    owner = app.process_interfaces.human_inputs
    consumed = owner.consume(
        checkpoint_id,
        workspace_id="ws",
        run_id="initial-same-run",
        response_id=answer.response_id,
    )

    def resume():
        return asyncio.run(
            record_workflow_resume(
                service=app,
                workspace_dir=str(tmp_path),
                workspace_id="ws",
                checkpoint=consumed,
                execute=lambda emit: execute(emit, consumed),
                on_event=observe,
            )
        )

    final = resume()
    assert final["status"] == "completed" and final["run_id"] == first["run_id"]
    assert final["run_log_path"] == first["run_log_path"] and len(calls) == 1
    assert '"selection":"a"' in calls[0]
    assert [step["task_id"] for step in final["steps"]] == ["choice", "report"]
    assert canonical_digest(resume()) == canonical_digest(final) and len(calls) == 1
    assert [e["task_id"] for e in events if e["kind"] == "input_requested"] == [
        "choice"
    ]
    result = next(r for r in final["results"] if r["provenance"]["task_id"] == "choice")
    assert result["kind"] == "structured"
    assert ("input-snapshot:initial-inputs", frozen.digest) in result["provenance"][
        "input_revisions"
    ]
    log = json.loads((tmp_path / first["run_log_path"]).read_text())
    assert "input_checkpoint" not in log
