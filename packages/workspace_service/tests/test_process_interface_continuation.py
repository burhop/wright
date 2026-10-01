"""Durable input checkpoints on the existing source executor and recorder."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
import copy
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.process_interactions import InputSnapshot, ProcessRef, ValueBinding
from core.process_validation import canonical_digest
from data_vault.state_store import connect_state_db
from workspace_service.process_interfaces import ProcessInterfaceService
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.workflow_execution_continuation import (
    encode_value,
    input_identities,
    restore_continuation,
    restore_result,
)
from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    compile_prompt_workflow,
    execute_prompt_workflow,
    _execution_snapshot,
    _parse,
    validate_workspace_authoring_shape,
)
from workspace_service.workflow_run_record import (
    record_workflow_run,
    record_workflow_resume,
)
from packages.workspace_service.tests.test_workflow_artifact_review import section
from workspace_service.workflow_approval_execution import resume_workflow_approval
from workspace_service.workflow_integration_policy import (
    LOCAL_REVIEW_BINDING,
    LOCAL_REVIEW_DESTINATION,
)
from workspace_service.workflow_external_actions import (
    WorkflowExternalActionError,
)
from packages.workspace_service.tests.test_process_human_input_source import (
    human_source,
)
from packages.workspace_service.tests.test_workflow_external_action_execution import (
    service,
)


def case(root, *, source_text=None, build_checkpoint=True):
    """A real file/SQLite fixture, without claiming full source-run completion.

    Execute just the first synthetic AI step with the existing executor to obtain
    actual saved result/file identities. Build a checkpoint state from that result
    for direct restoration checks. Full journeys use the same actual source and
    recorder below, with explicitly synthetic model and human responses.
    """
    db_path = str(root / "state.db")
    app = service(root)
    app.db_path = db_path
    app.process_interfaces = ProcessInterfaceService(app)
    text = source_text or human_source()
    validate_workspace_authoring_shape(text)
    frozen = InputSnapshot.create(
        snapshot_id="inputs-one",
        process=ProcessRef(
            workspace_id="ws",
            source_path="workflows/input.wflow",
            source_digest=hashlib.sha256(text.encode()).hexdigest(),
        ),
        created_at="2026-10-01T12:00:00Z",
        bindings=(ValueBinding(input_id="brief", value="Compare a and b."),),
    )
    app.process_interfaces.inputs.put_snapshot(frozen)
    plan = replace(
        compile_prompt_workflow(text),
        definition_digest=frozen.process.source_digest,
        input_snapshot=frozen,
    )
    values = {"brief": "Compare a and b."}
    if not build_checkpoint:
        return SimpleNamespace(
            app=app,
            owner=app.process_interfaces.human_inputs,
            checkpoint=None,
            frozen=frozen,
            plan=plan,
            values=values,
            root=root,
            db_path=db_path,
        )

    async def generate(prompt, fmt):
        return "Synthetic comparison a and b."

    first = asyncio.run(
        execute_prompt_workflow(
            service=app,
            workspace_dir=str(root),
            plan=replace(plan, steps=plan.steps[:1]),
            input_values=values,
            response_generator=generate,
        )
    )
    results = [restore_result(item) for item in first["results"]]
    assert len(results) == 1
    upstream = results[0]
    responses = {"first.first_out": upstream}
    files = [
        {"path": item["output_path"], "sha256": item["sha256"]}
        for item in first["outputs"]
    ]
    subject = {
        "definition_digest": plan.definition_digest,
        "input_snapshot_id": frozen.snapshot_id,
        "input_digest": frozen.digest,
        "input_digests": sorted(input_identities(values).values()),
        "artifact_digests": sorted(item["sha256"] for item in files),
        "step_id": "choice",
        "declaration": plan.steps[1].human_interaction,
        "upstream_digests": {
            "first.first_out": canonical_digest(encode_value(upstream))
        },
    }
    state = {
        "schema_version": 3,
        "checkpoint_kind": "input",
        "run_id": first["run_id"],
        "definition_digest": plan.definition_digest,
        "execution_context": {},
        "input_snapshot_id": frozen.snapshot_id,
        "input_digest": frozen.digest,
        "response_id": None,
        "response_digest": None,
        "next_step_index": 1,
        "completed_step_ids": ["first"],
        "result_ids": [upstream.id],
        "input_files": [],
        "artifact_files": files,
        **_execution_snapshot(
            input_values=values,
            responses=responses,
            records=first["steps"],
            engineering_results=results,
            artifacts_by_output={},
            attempts=[],
            revision_counts={},
            feedback={},
        ),
    }
    owner = app.process_interfaces.human_inputs
    checkpoint = owner.request(
        workspace_id="ws",
        workflow_id=frozen.process.source_path,
        run_id=first["run_id"],
        step_id="choice",
        subject=subject,
        continuation=state,
    )
    return SimpleNamespace(
        app=app,
        owner=owner,
        checkpoint=checkpoint,
        frozen=frozen,
        plan=plan,
        values=values,
        root=root,
        db_path=db_path,
    )


def respond(c, **changes):
    return c.owner.respond(
        c.checkpoint.checkpoint_id,
        **{
            "workspace_id": "ws",
            "run_id": c.checkpoint.run_id,
            "expected_subject_digest": c.checkpoint.subject_digest,
            "value": {"selection": "a"},
            "actor": "isolated-test-actor",
            "reason": "Synthetic unit response; no engineering acceptance.",
            "request_id": "respond-one",
            "integration_test": True,
            **changes,
        },
    )


def consume(c, response):
    return c.owner.consume(
        c.checkpoint.checkpoint_id,
        workspace_id="ws",
        run_id=c.checkpoint.run_id,
        response_id=response.response_id,
    )


def restore(c, saved_checkpoint, **changes):
    arguments = {
        "state": saved_checkpoint.continuation,
        "checkpoint": asdict(saved_checkpoint),
        "plan": c.plan,
        "input_values": c.values,
        "service": c.app,
        "workspace_dir": str(c.root),
        **changes,
    }
    return asyncio.run(restore_continuation(**arguments))


def test_response_survives_recreation_and_restores_exact_typed_value(tmp_path):
    c = case(tmp_path)
    pending, response, created = respond(c)
    assert created and pending.state == "pending" and pending.external_action is None
    assert pending.continuation["response_id"] == response.response_id
    assert response.integration_test and response.value == {"selection": "a"}
    app = service(tmp_path)
    app.db_path = c.db_path
    app.process_interfaces = ProcessInterfaceService(app)
    c.app, c.owner = app, app.process_interfaces.human_inputs
    consumed = consume(c, response)
    restored = restore(c, consumed)
    assert restored["human_response"] == response
    assert restored["run_id"] == c.checkpoint.run_id and restored["cursor"] == 1
    assert [record["task_id"] for record in restored["records"]] == ["first"]
    assert consumed.state == "consumed" and consumed.external_action is None
    assert c.owner.inputs.get_response("ws", response.response_id) == response


def test_exact_lost_ack_retry_retains_original_answer_after_consumption(tmp_path):
    c = case(tmp_path)
    first, response, _ = respond(c)
    assert respond(c) == (first, response, False)
    consumed = consume(c, response)
    assert respond(c) == (consumed, response, False)
    with pytest.raises(ProcessInterfaceError, match="already consumed"):
        consume(c, response)


def test_concurrent_duplicate_response_and_consumption_are_single_use(tmp_path):
    c = case(tmp_path)
    with ThreadPoolExecutor(max_workers=2) as pool:
        replies = list(pool.map(lambda _: respond(c), range(2)))
    assert sorted(reply[2] for reply in replies) == [False, True]
    assert replies[0][1] == replies[1][1]

    def consume_once(_):
        try:
            return consume(c, replies[0][1]).state
        except ProcessInterfaceError as error:
            assert error.reason.code == "REQUEST_CONFLICT"
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(consume_once, range(2))) == ["conflict", "consumed"]


@pytest.mark.parametrize(
    "changes",
    [
        {"value": {"selection": "b"}},
        {"actor": "different-actor"},
        {"request_id": "different-request"},
        {"integration_test": False},
        {"reason": "Different provenance"},
    ],
)
def test_different_response_cannot_replace_retained_evidence(tmp_path, changes):
    c = case(tmp_path)
    pending, answer, _ = respond(c)
    with pytest.raises(ProcessInterfaceError) as error:
        respond(c, **changes)
    assert error.value.reason.code == "REQUEST_CONFLICT"
    assert c.owner.repository.get(pending.checkpoint_id) == pending
    assert c.owner.inputs.get_response("ws", answer.response_id) == answer


@pytest.mark.parametrize(
    "changes,code",
    [
        ({"value": {"selection": "c"}}, "RESPONSE_INVALID"),
        ({"value": {"selection": "a", "unexpected": 1}}, "RESPONSE_INVALID"),
        ({"value": {}}, "RESPONSE_INVALID"),
        ({"value": "a"}, "RESPONSE_INVALID"),
        ({"value": {"selection": "a", "extra": float("nan")}}, "RESPONSE_INVALID"),
        ({"workspace_id": "other"}, "SCOPE_DENIED"),
        ({"run_id": "other"}, "SCOPE_DENIED"),
        ({"expected_subject_digest": "b" * 64}, "SUBJECT_STALE"),
    ],
)
def test_invalid_schema_scope_and_subject_create_no_response(tmp_path, changes, code):
    c = case(tmp_path)
    with pytest.raises(ProcessInterfaceError) as error:
        respond(c, **changes)
    assert error.value.reason.code == code
    with connect_state_db(c.db_path, read_only=True) as db:
        assert (
            db.execute("SELECT count(*) FROM process_interaction_responses").fetchone()[
                0
            ]
            == 0
        )
    assert c.owner.repository.get(c.checkpoint.checkpoint_id) == c.checkpoint


def test_attachment_rolls_back_response_when_checkpoint_write_fails(tmp_path):
    c = case(tmp_path)
    with connect_state_db(c.db_path) as db:
        db.execute("""CREATE TRIGGER fail_checkpoint_attachment
        BEFORE UPDATE ON workflow_continuation_checkpoints
        BEGIN SELECT RAISE(ABORT, 'simulated storage failure'); END""")
    with pytest.raises(Exception, match="simulated storage failure"):
        respond(c)
    with connect_state_db(c.db_path, read_only=True) as db:
        assert (
            db.execute("SELECT count(*) FROM process_interaction_responses").fetchone()[
                0
            ]
            == 0
        )
    assert c.owner.repository.get(c.checkpoint.checkpoint_id) == c.checkpoint


def test_an_answer_cannot_be_approved_or_reconciled_as_an_action(tmp_path):
    c = case(tmp_path)
    for operation in (
        lambda: c.app.workflow_external_actions.decide(
            c.checkpoint.checkpoint_id,
            workspace_id="ws",
            expected_subject_digest=c.checkpoint.subject_digest,
            actor="actor",
            approved=True,
        ),
        lambda: c.app.workflow_external_actions.consume_for_dispatch(
            c.checkpoint.checkpoint_id,
            workspace_id="ws",
            current_subject=c.checkpoint.subject,
            action_id="action-one",
        ),
        lambda: c.app.workflow_external_actions.reconcile(
            c.checkpoint.checkpoint_id,
            workspace_id="ws",
            run_id=c.checkpoint.run_id,
            expected_subject_digest=c.checkpoint.subject_digest,
            outcome="dispatched",
            evidence={},
        ),
    ):
        with pytest.raises(WorkflowExternalActionError) as error:
            operation()
        assert error.value.code == "approval_not_found"
    assert c.owner.repository.get(c.checkpoint.checkpoint_id) == c.checkpoint


@pytest.mark.parametrize(
    "mutation",
    [
        "not_consumed",
        "cursor",
        "completed",
        "definition",
        "input",
        "snapshot",
        "schema",
        "upstream",
        "artifact",
        "response_ref",
        "state_version",
    ],
)
def test_v3_restore_rejects_changed_or_unconsumed_subject(tmp_path, mutation):
    c = case(tmp_path)
    pending, answer, _ = respond(c)
    checkpoint = pending if mutation == "not_consumed" else consume(c, answer)
    state, record = copy.deepcopy(checkpoint.continuation), asdict(checkpoint)
    if mutation == "cursor":
        state["next_step_index"] = 2
    elif mutation == "completed":
        state["completed_step_ids"] = []
    elif mutation == "definition":
        c.plan = replace(c.plan, definition_digest="d" * 64)
    elif mutation == "input":
        c.values["brief"] = "Changed"
    elif mutation == "snapshot":
        frozen = InputSnapshot.create(
            **{**c.frozen.model_dump(exclude={"digest"}), "snapshot_id": "inputs-two"}
        )
        c.plan = replace(c.plan, input_snapshot=frozen)
    elif mutation == "schema":
        changed = copy.deepcopy(c.plan.steps[1].human_interaction)
        changed["response_schema"]["properties"]["selection"]["enum"] = ["b"]
        c.plan = replace(
            c.plan,
            steps=(
                c.plan.steps[0],
                replace(c.plan.steps[1], human_interaction=changed),
                *c.plan.steps[2:],
            ),
        )
    elif mutation == "upstream":
        state["responses"]["first.first_out"]["value"]["name"] = "Changed"
    elif mutation == "artifact":
        (tmp_path / "first.txt").write_text("Changed", encoding="utf-8")
    elif mutation == "response_ref":
        state["response_id"] = "other-response"
    elif mutation == "state_version":
        state["schema_version"] = 3.0
    with pytest.raises(WorkflowSourceExecutionError) as error:
        restore(c, checkpoint, state=state, checkpoint=record)
    assert error.value.code == "WORKFLOW_CONTINUATION_STALE"


def two_checkpoint_source():
    text = human_source()
    blocks = _parse(text)
    choice = copy.deepcopy(
        next(block["fields"] for block in blocks if block["id"] == "choice")
    )
    final = copy.deepcopy(
        next(block["fields"] for block in blocks if block["id"] == "second")
    )
    choice["inputs"][0]["key"] = "choice_two_evidence"
    choice["outputs"][0]["key"] = "choice_two_response"
    choice["settings"]["human_interaction"]["output_port"] = "choice_two_response"
    final["inputs"][0]["key"] = "final_input"
    final["outputs"][0]["key"] = "final_output"
    text += section("task", "choice_two", **choice)
    text += section("task", "final", **final)
    for key, before, after in (
        ("second_evidence", "second.second_output", "choice_two.choice_two_evidence"),
        ("second_response", "choice_two.choice_two_response", "final.final_input"),
    ):
        text += section(
            "connection",
            key,
            type="item",
            **{"from": before, "to": after},
            label="Next declared input",
            when=None,
        )
    return text


def test_browser_two_input_source_matches_actual_continuation_fixture():
    root = Path(__file__).resolve().parents[3]
    source = (
        root
        / "specs/083-process-working-interfaces/fixtures/two-declared-human-inputs.workflow.wflow"
    ).read_text(encoding="utf-8")
    assert source == two_checkpoint_source()
    assert [step.id for step in compile_prompt_workflow(source).steps] == [
        "first",
        "choice",
        "second",
        "choice_two",
        "final",
    ]


def test_two_source_barriers_resume_original_record_and_retry_without_model_replay(
    tmp_path,
):
    c = case(tmp_path, source_text=two_checkpoint_source(), build_checkpoint=False)
    calls, events = [], []

    async def generate(prompt, fmt):
        calls.append(prompt)
        return f"Synthetic model response {len(calls)}."

    async def observe(event):
        events.append(event)

    async def execute(emit, checkpoint=None):
        return await execute_prompt_workflow(
            service=c.app,
            workspace_dir=str(tmp_path),
            plan=c.plan,
            input_values=c.values,
            response_generator=generate,
            on_event=emit,
            run_id="same-run",
            continuation=checkpoint.continuation if checkpoint else None,
            completed_checkpoint=asdict(checkpoint) if checkpoint else None,
        )

    first = asyncio.run(
        record_workflow_run(
            service=c.app,
            workspace_dir=str(tmp_path),
            workspace_id="ws",
            source_path=c.frozen.process.source_path,
            source_digest=c.plan.definition_digest,
            execute=execute,
            on_event=observe,
            run_id="same-run",
            required_step_ids=[step.id for step in c.plan.steps],
        )
    )
    assert first["status"] == "waiting_human" and len(calls) == 1
    assert not (tmp_path / "second.txt").exists()
    c.checkpoint = c.owner.get(
        first["input_checkpoint"]["checkpoint_id"], workspace_id="ws", run_id="same-run"
    )
    _, answer, _ = respond(c)
    first_consumed = consume(c, answer)

    def resume(checkpoint):
        return asyncio.run(
            record_workflow_resume(
                service=c.app,
                workspace_dir=str(tmp_path),
                workspace_id="ws",
                checkpoint=checkpoint,
                execute=lambda emit: execute(emit, checkpoint),
                on_event=observe,
            )
        )

    second = resume(first_consumed)
    assert second["status"] == "waiting_human" and second["run_id"] == "same-run"
    assert second["run_log_path"] == first["run_log_path"] and len(calls) == 2
    assert '"selection":"a"' in calls[-1]
    assert (
        canonical_digest(resume(first_consumed)) == canonical_digest(second)
        and len(calls) == 2
    )
    # Recreate the service before the second answer/resume: all cursor/results
    # come from SQLite and the original run log, not a retained response closure.
    c.app = service(tmp_path)
    c.app.db_path = c.db_path
    c.app.process_interfaces = ProcessInterfaceService(c.app)
    c.owner = c.app.process_interfaces.human_inputs
    c.checkpoint = c.owner.get(
        second["input_checkpoint"]["checkpoint_id"],
        workspace_id="ws",
        run_id="same-run",
    )
    _, second_answer, _ = respond(c, value={"selection": "b"}, request_id="respond-two")
    second_consumed = consume(c, second_answer)
    final = resume(second_consumed)
    assert final["status"] == "completed" and final["run_id"] == "same-run"
    assert final["run_log_path"] == first["run_log_path"] and len(calls) == 3
    assert '"selection":"b"' in calls[-1]
    assert [record["task_id"] for record in final["steps"]] == [
        "first",
        "choice",
        "second",
        "choice_two",
        "final",
    ]
    assert (
        canonical_digest(resume(second_consumed)) == canonical_digest(final)
        and len(calls) == 3
    )
    assert [
        event["task_id"] for event in events if event["kind"] == "input_requested"
    ] == ["choice", "choice_two"]
    answers = [
        result
        for result in final["results"]
        if result["provenance"]["task_id"] in {"choice", "choice_two"}
    ]
    assert len(answers) == 2 and all(
        result["kind"] == "structured" for result in answers
    )
    assert all(result["artifact_role"] == "intermediate" for result in answers)
    log = json.loads((tmp_path / first["run_log_path"]).read_text(encoding="utf-8"))
    assert len(log["resume_segments"]) == 2
    assert all(
        segment["state"] == "completed" for segment in log["resume_segments"].values()
    )
    assert "input_checkpoint" not in log and "input_checkpoint" not in final
    assert all(
        record["integration_test"]
        for record in final["steps"]
        if record["execution_kind"] == "human_input"
    )


def test_interrupted_input_continuation_blocks_replay_of_uncertain_segment(tmp_path):
    c = case(tmp_path, build_checkpoint=False)
    calls = []

    async def generate(prompt, fmt):
        calls.append(prompt)
        if len(calls) == 2:
            raise RuntimeError("Simulated backend interruption after model dispatch")
        return "Synthetic comparison"

    async def execute(emit, checkpoint=None):
        return await execute_prompt_workflow(
            service=c.app,
            workspace_dir=str(tmp_path),
            plan=c.plan,
            input_values=c.values,
            response_generator=generate,
            on_event=emit,
            continuation=checkpoint.continuation if checkpoint else None,
            completed_checkpoint=asdict(checkpoint) if checkpoint else None,
        )

    first = asyncio.run(
        record_workflow_run(
            service=c.app,
            workspace_dir=str(tmp_path),
            workspace_id="ws",
            source_path=c.frozen.process.source_path,
            source_digest=c.plan.definition_digest,
            execute=execute,
        )
    )
    c.checkpoint = c.owner.get(
        first["input_checkpoint"]["checkpoint_id"],
        workspace_id="ws",
        run_id=first["run_id"],
    )
    _, answer, _ = respond(c)
    checkpoint = consume(c, answer)

    async def resume():
        return await record_workflow_resume(
            service=c.app,
            workspace_dir=str(tmp_path),
            workspace_id="ws",
            checkpoint=checkpoint,
            execute=lambda emit: execute(emit, checkpoint),
        )

    with pytest.raises(RuntimeError, match="Simulated backend interruption"):
        asyncio.run(resume())
    assert len(calls) == 2
    with pytest.raises(WorkflowSourceExecutionError) as error:
        asyncio.run(resume())
    assert error.value.code == "WORKFLOW_CONTINUATION_OUTCOME_UNKNOWN"
    assert len(calls) == 2
    log = json.loads((tmp_path / first["run_log_path"]).read_text(encoding="utf-8"))
    assert (
        log["resume_segments"][checkpoint.checkpoint_id]["state"] == "outcome_unknown"
    )


@pytest.mark.parametrize("answered", [False, True])
def test_expired_input_cannot_accept_or_consume_an_answer(
    tmp_path, monkeypatch, answered
):
    c = case(tmp_path)
    deadline = c.checkpoint.created_at + 5
    with connect_state_db(c.db_path) as db:
        db.execute(
            "UPDATE workflow_continuation_checkpoints SET expires_at=? WHERE checkpoint_id=?",
            (deadline, c.checkpoint.checkpoint_id),
        )
    if answered:
        _, answer, _ = respond(c)
    monkeypatch.setattr(
        "workspace_service.process_interfaces.interactions.time.time", lambda: deadline
    )
    with pytest.raises(ProcessInterfaceError) as error:
        consume(c, answer) if answered else respond(c)
    assert error.value.reason.code == "REQUEST_CONFLICT"
    current = c.owner.repository.get(c.checkpoint.checkpoint_id)
    assert current.state == "pending" and current.external_action is None
    with connect_state_db(c.db_path, read_only=True) as db:
        assert db.execute(
            "SELECT count(*) FROM process_interaction_responses"
        ).fetchone()[0] == int(answered)


def test_v3_approval_after_input_restores_frozen_overlay_through_existing_dispatcher(
    tmp_path,
):
    text = human_source()
    text += section(
        "task",
        "review",
        name="Synthetic review",
        purpose="Unit fixture only",
        group=None,
        step_type="review",
        performed_by="engineer",
        inputs=[],
        outputs=[],
        instructions="Review the exact fixture evidence",
        tool=None,
        reusable_step=None,
        settings={
            "authoring_template": "external-action-approval",
            "action_kind": "local_review",
            "approval_binding": LOCAL_REVIEW_BINDING,
            "approval_destination": LOCAL_REVIEW_DESTINATION,
            "approval_settings": {"review_task_id": "review"},
            "approval_action": {"kind": "local_review", "mode": "review_only"},
        },
    )
    finish = copy.deepcopy(
        next(block["fields"] for block in _parse(text) if block["id"] == "second")
    )
    finish["inputs"] = []
    finish["outputs"][0]["key"] = "finish_output"
    finish["settings"].update(output_filename="final.txt", save_output=True)
    text += section("task", "finish", **finish)
    for key, before, after in (
        ("review_order", "second", "review"),
        ("finish_order", "review", "finish"),
    ):
        text += section(
            "connection",
            key,
            type="order",
            **{"from": before, "to": after},
            label="Next",
            when=None,
        )
    c = case(tmp_path, source_text=text, build_checkpoint=False)
    c.frozen = InputSnapshot.create(
        **{
            **c.frozen.model_dump(exclude={"digest"}),
            "snapshot_id": "run-specific-inputs",
            "bindings": (
                ValueBinding(
                    input_id="brief", value="Distinct frozen run requirements"
                ),
            ),
        }
    )
    c.owner.inputs.put_snapshot(c.frozen)
    c.plan = replace(c.plan, input_snapshot=c.frozen)
    c.values = {"brief": "Distinct frozen run requirements"}
    source_path = tmp_path / c.frozen.process.source_path
    source_path.parent.mkdir(parents=True)
    source_path.write_text(text, encoding="utf-8", newline="")

    async def read_source(workspace_dir, path):
        raw = (tmp_path / path).read_bytes()
        return SimpleNamespace(
            source=raw.decode("utf-8"), storage_digest=hashlib.sha256(raw).hexdigest()
        )

    c.app.workflow_sources = SimpleNamespace(read=read_source)
    calls = []

    async def generate(prompt, fmt):
        calls.append(prompt)
        return "Synthetic result"

    async def execute(emit, checkpoint=None):
        return await execute_prompt_workflow(
            service=c.app,
            workspace_dir=str(tmp_path),
            plan=c.plan,
            input_values=c.values,
            response_generator=generate,
            on_event=emit,
            continuation=checkpoint.continuation if checkpoint else None,
            completed_checkpoint=asdict(checkpoint) if checkpoint else None,
        )

    first = asyncio.run(
        record_workflow_run(
            service=c.app,
            workspace_dir=str(tmp_path),
            workspace_id="ws",
            source_path=c.frozen.process.source_path,
            source_digest=c.plan.definition_digest,
            execute=execute,
            required_step_ids=[step.id for step in c.plan.steps],
        )
    )
    c.checkpoint = c.owner.get(
        first["input_checkpoint"]["checkpoint_id"],
        workspace_id="ws",
        run_id=first["run_id"],
    )
    _, answer, _ = respond(c)
    consumed = consume(c, answer)
    second = asyncio.run(
        record_workflow_resume(
            service=c.app,
            workspace_dir=str(tmp_path),
            workspace_id="ws",
            checkpoint=consumed,
            execute=lambda emit: execute(emit, consumed),
        )
    )
    checkpoint = c.app.workflow_external_actions.lookup(
        second["approval"]["checkpoint_id"]
    )
    assert checkpoint.continuation["schema_version"] == 3
    assert checkpoint.continuation["checkpoint_kind"] == "approval"
    assert checkpoint.continuation["input_snapshot_id"] == c.frozen.snapshot_id
    assert checkpoint.continuation["input_digest"] == c.frozen.digest
    c.app.workflow_external_actions.decide(
        checkpoint.checkpoint_id,
        workspace_id="ws",
        expected_subject_digest=checkpoint.subject_digest,
        actor="isolated-unit-reviewer",
        approved=True,
        reason="Synthetic unit decision, no engineering acceptance or external effects",
    )
    dispatched, final = asyncio.run(
        resume_workflow_approval(
            service=c.app,
            workspace_id="ws",
            workspace_dir=str(tmp_path),
            checkpoint=checkpoint,
            subject_digest=checkpoint.subject_digest,
            request_id="fixture-review",
            response_generator=generate,
        )
    )
    assert final["status"] == "completed" and final["run_id"] == first["run_id"]
    assert len(calls) == 3 and "Distinct frozen run requirements" in calls[0]
    assert dispatched.external_action["outcome"] == "dispatched"
    assert [record["task_id"] for record in final["steps"]] == [
        "first",
        "choice",
        "second",
        "review",
        "finish",
    ]
