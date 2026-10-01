"""Real source/store/resume orchestration with explicitly synthetic model output."""

import asyncio
import json
from dataclasses import replace

import pytest

from core.process_interactions import ProcessRef
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.process_interfaces.service import ProcessInterfaceService
from workspace_service.workflow_sources import WorkspaceWorkflowSourceStore
from packages.workspace_service.tests.test_process_human_input_source import (
    human_source,
)
from packages.workspace_service.tests.test_process_input_readiness import process
from packages.workspace_service.tests.test_process_preparation_service import (
    owner,
    scope,
)


def control(actor="user"):
    return replace(
        scope("process.read", "process.start", "process.inputs", "process.respond"),
        principal_id=actor,
    )


async def waiting_case(root, text=None):
    text = text or human_source()
    reference = process(text)
    path = root / reference.source_path
    path.parent.mkdir(parents=True, exist_ok=True)
    WorkspaceWorkflowSourceStore(str(root)).create(reference.source_path, text)
    app = owner(root, text)
    app.workspace.process_interfaces = app
    from workspace_service.workspace_file_identity import workspace_file_sha256

    async def hash_reference(workspace_dir, path):
        return workspace_file_sha256(workspace_dir, path)

    async def read_source(workspace_dir, path):
        return WorkspaceWorkflowSourceStore(workspace_dir).read(path)

    app.workspace.files.hash_reference = hash_reference
    app.workspace.workflow_sources.read = read_source
    frozen = (await app.set_inputs(control(), reference)).snapshot
    calls = []

    async def generate(prompt, fmt):
        calls.append(prompt)
        return "Synthetic orchestration artifact"

    receipt = await app.runs.start(
        control(),
        reference,
        frozen.snapshot_id,
        "start-human",
        expected_input_digest=frozen.digest,
        response_generator=generate,
    )
    view = await app.runs.wait(control(), reference, receipt.run_id)
    assert view["status"] == "waiting_human"
    assert len(calls) == 1
    checkpoint = app.human_inputs.get(
        view["input_checkpoint"]["checkpoint_id"],
        workspace_id="workspace",
        run_id=receipt.run_id,
    )
    return app, reference, receipt, checkpoint, calls, generate


async def answer(
    app,
    reference,
    checkpoint,
    generate,
    *,
    value=None,
    request="answer-one",
    actor="user",
):
    return await app.runs.respond(
        control(actor),
        reference,
        checkpoint.checkpoint_id,
        request,
        expected_subject_digest=checkpoint.subject_digest,
        value={"selection": "b"} if value is None else value,
        response_generator=generate,
    )


@pytest.mark.asyncio
async def test_projection_is_a_declared_form_and_reads_never_execute_or_respond(
    tmp_path,
):
    app, reference, receipt, cp, calls, generate = await waiting_case(tmp_path)
    try:
        for _ in range(2):
            snapshot = await app.get_snapshot(
                control(), reference, run_id=receipt.run_id
            )
            interaction = snapshot.interactions[0]
            assert snapshot.state == "waiting_human"
            assert interaction.kind == "input"
            assert interaction.checkpoint_id == cp.checkpoint_id
            assert interaction.subject_digest == cp.subject_digest
            assert (
                interaction.response_schema
                == cp.subject["declaration"]["response_schema"]
            )
            assert any(
                item.artifact_ref == "first.txt" for item in interaction.evidence
            )
            assert next(
                item for item in snapshot.actions if item.operation == "respond"
            ).enabled
        assert len(calls) == 1
        assert app.human_inputs.repository.get(cp.checkpoint_id).state == "pending"
        assert (
            app.human_inputs.repository.get(cp.checkpoint_id).continuation[
                "response_id"
            ]
            is None
        )
        readonly = await app.get_snapshot(
            scope("process.read"), reference, run_id=receipt.run_id
        )
        assert not next(
            item for item in readonly.actions if item.operation == "respond"
        ).enabled
    finally:
        await app.close()


@pytest.mark.asyncio
async def test_response_owns_task_returns_before_model_and_retries_never_repeat(
    tmp_path,
):
    app, reference, receipt, cp, calls, _ = await waiting_case(tmp_path)
    entered, release = asyncio.Event(), asyncio.Event()

    async def generate(prompt, fmt):
        calls.append(prompt)
        entered.set()
        await release.wait()
        return "Synthetic after declared selection"

    try:
        response = await answer(app, reference, cp, generate)
        assert response.run_id == receipt.run_id
        assert response.actor == "user"
        assert not response.integration_test
        await asyncio.wait_for(entered.wait(), 3)
        assert app.runs.is_live(receipt.run_id)
        assert await answer(app, reference, cp, generate) == response
        observer = asyncio.create_task(
            app.runs.wait(control(), reference, receipt.run_id)
        )
        await asyncio.sleep(0)
        observer.cancel()
        with pytest.raises(asyncio.CancelledError):
            await observer
        assert app.runs.is_live(receipt.run_id)
        release.set()
        completed = await app.runs.wait(control(), reference, receipt.run_id)
        assert completed["status"] == "completed"
        assert completed["run_id"] == receipt.run_id
        assert len(calls) == 2
        assert await answer(app, reference, cp, generate) == response
        assert len(calls) == 2
        record = json.loads(
            (tmp_path / receipt.run_log_path).read_text(encoding="utf-8")
        )
        assert record["resume_segments"][cp.checkpoint_id]["state"] == "completed"
        assert "input_checkpoint" not in record["result"]
    finally:
        release.set()
        await app.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["source", "artifact", "expiry", "subject"])
async def test_changed_subject_has_disabled_projection_and_cannot_accept_answer(
    tmp_path, change
):
    app, reference, receipt, cp, calls, generate = await waiting_case(tmp_path)
    try:
        if change == "source":
            store = WorkspaceWorkflowSourceStore(str(tmp_path))
            document = store.read(reference.source_path)
            document = store.update(
                reference.source_path,
                expected_storage_revision=document.storage_revision,
                expected_storage_digest=document.storage_digest,
                semantic_change_validated=True,
                source=human_source().replace(
                    "Select comparison", "Changed comparison"
                ),
            )
            current = process(document.source)
        elif change == "artifact":
            (tmp_path / "first.txt").write_text(
                "Changed actual upstream output", encoding="utf-8"
            )
            current = reference
        elif change == "expiry":
            from data_vault.state_store import connect_state_db

            with connect_state_db(app.db_path) as db:
                db.execute(
                    "UPDATE workflow_continuation_checkpoints SET expires_at=1 WHERE checkpoint_id=?",
                    (cp.checkpoint_id,),
                )
            current = reference
        else:
            current = reference
            cp = replace(cp, subject_digest="0" * 64)
        if change != "subject":
            snapshot = await app.get_snapshot(control(), current, run_id=receipt.run_id)
            permission = next(
                item for item in snapshot.actions if item.operation == "respond"
            )
            assert not permission.enabled
            assert snapshot.interactions[0].state == "stale"
        with pytest.raises(ProcessInterfaceError):
            await answer(app, reference, cp, generate)
        assert len(calls) == 1
        retained = app.human_inputs.repository.get(cp.checkpoint_id)
        assert retained.state == "pending"
        assert retained.continuation["response_id"] is None
    finally:
        await app.close()


@pytest.mark.asyncio
async def test_bad_value_scope_and_checkpoint_never_consume(tmp_path):
    app, reference, receipt, cp, calls, generate = await waiting_case(tmp_path)
    try:
        for value in ({"selection": "c"}, {"selection": "a", "extra": True}, "b"):
            with pytest.raises(ProcessInterfaceError) as caught:
                await answer(app, reference, cp, generate, value=value)
            assert caught.value.reason.code == "RESPONSE_INVALID"
        other = ProcessRef(
            workspace_id="workspace",
            source_path="workflows/other.workflow.wflow",
            source_digest=reference.source_digest,
        )
        with pytest.raises(ProcessInterfaceError) as caught:
            await answer(app, other, cp, generate)
        assert caught.value.reason.code == "SCOPE_DENIED"
        with pytest.raises(ProcessInterfaceError) as caught:
            await app.runs.respond(
                scope("process.read"),
                reference,
                cp.checkpoint_id,
                "denied",
                expected_subject_digest=cp.subject_digest,
                value={"selection": "a"},
                response_generator=generate,
            )
        assert caught.value.reason.code == "SCOPE_DENIED"
        assert len(calls) == 1
        assert (
            app.human_inputs.repository.get(cp.checkpoint_id).continuation[
                "response_id"
            ]
            is None
        )
    finally:
        await app.close()


@pytest.mark.asyncio
async def test_recreated_owner_resumes_pending_checkpoint_with_original_run(tmp_path):
    app, reference, receipt, cp, calls, generate = await waiting_case(tmp_path)
    await app.close()
    recreated = ProcessInterfaceService(app.workspace)
    app.workspace.process_interfaces = recreated
    try:
        response = await answer(recreated, reference, cp, generate)
        completed = await recreated.runs.wait(control(), reference, receipt.run_id)
        assert completed["status"] == "completed"
        assert response.run_id == receipt.run_id
        assert len(calls) == 2
        assert await answer(recreated, reference, cp, generate) == response
        for changes in (
            {"value": {"selection": "a"}},
            {"request": "other-request"},
            {"actor": "other-user"},
        ):
            with pytest.raises(ProcessInterfaceError) as caught:
                await answer(recreated, reference, cp, generate, **changes)
            assert caught.value.reason.code == "REQUEST_CONFLICT"
        assert len(calls) == 2
    finally:
        await recreated.close()


@pytest.mark.asyncio
async def test_unfinished_saved_claim_is_unknown_and_is_never_replayed(tmp_path):
    app, reference, receipt, cp, calls, generate = await waiting_case(tmp_path)
    try:
        cp, response, _ = app.human_inputs.respond(
            cp.checkpoint_id,
            workspace_id="workspace",
            run_id=receipt.run_id,
            expected_subject_digest=cp.subject_digest,
            value={"selection": "b"},
            actor="user",
            reason="Response to declared process input",
            request_id="answer-one",
        )
        app.human_inputs.consume(
            cp.checkpoint_id,
            workspace_id="workspace",
            run_id=receipt.run_id,
            response_id=response.response_id,
        )
        path = tmp_path / receipt.run_log_path
        record = json.loads(path.read_text(encoding="utf-8"))
        record["resume_segments"] = {
            cp.checkpoint_id: {
                "state": "executing",
                "subject_digest": cp.subject_digest,
            }
        }
        path.write_text(json.dumps(record), encoding="utf-8")
        with pytest.raises(ProcessInterfaceError) as caught:
            await answer(app, reference, cp, generate)
        assert caught.value.reason.code == "OUTCOME_UNKNOWN"
        assert len(calls) == 1
        assert not app.runs.is_live(receipt.run_id)
    finally:
        await app.close()


@pytest.mark.asyncio
async def test_two_supervised_checkpoints_survive_reopen_and_duplicate_submissions(
    tmp_path,
):
    from packages.workspace_service.tests.test_process_interface_continuation import (
        two_checkpoint_source,
    )

    app, reference, receipt, cp, calls, generate = await waiting_case(
        tmp_path, two_checkpoint_source()
    )
    try:
        first, retry = await asyncio.gather(
            answer(app, reference, cp, generate), answer(app, reference, cp, generate)
        )
        assert first == retry
        next_view = await app.runs.wait(control(), reference, receipt.run_id)
        assert next_view["status"] == "waiting_human"
        second_cp = app.human_inputs.get(
            next_view["input_checkpoint"]["checkpoint_id"],
            workspace_id="workspace",
            run_id=receipt.run_id,
        )
        assert second_cp.step_id == "choice_two"
        assert len(calls) == 2
        await app.close()
        app = ProcessInterfaceService(app.workspace)
        app.workspace.process_interfaces = app
        projected = await app.get_snapshot(control(), reference, run_id=receipt.run_id)
        assert projected.interactions[0].checkpoint_id == second_cp.checkpoint_id
        assert projected.interactions[0].state == "waiting"
        response = await answer(
            app,
            reference,
            second_cp,
            generate,
            value={"selection": "a"},
            request="second-answer",
        )
        assert response.run_id == receipt.run_id
        assert (await app.runs.wait(control(), reference, receipt.run_id))[
            "status"
        ] == "completed"
        assert await answer(app, reference, cp, generate) == first
        assert len(calls) == 3
    finally:
        await app.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("consumed", [False, True])
async def test_saved_response_without_execution_claim_can_finish_handoff(
    tmp_path, consumed
):
    app, reference, receipt, cp, calls, generate = await waiting_case(tmp_path)
    try:
        cp, response, _ = app.human_inputs.respond(
            cp.checkpoint_id,
            workspace_id="workspace",
            run_id=receipt.run_id,
            expected_subject_digest=cp.subject_digest,
            value={"selection": "b"},
            actor="user",
            reason="Response to declared process input",
            request_id="answer-one",
        )
        if consumed:
            app.human_inputs.consume(
                cp.checkpoint_id,
                workspace_id="workspace",
                run_id=receipt.run_id,
                response_id=response.response_id,
            )
        await app.close()
        app = ProcessInterfaceService(app.workspace)
        app.workspace.process_interfaces = app
        assert await answer(app, reference, cp, generate) == response
        assert (await app.runs.wait(control(), reference, receipt.run_id))[
            "status"
        ] == "completed"
        assert len(calls) == 2
    finally:
        await app.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["artifact_files", "result_ids"])
async def test_incomplete_retained_checkpoint_cannot_skip_actual_evidence_checks(
    tmp_path, field
):
    from data_vault.state_store import connect_state_db

    app, reference, receipt, cp, calls, generate = await waiting_case(tmp_path)
    try:
        state = json.loads(json.dumps(cp.continuation))
        state[field] = []
        with connect_state_db(app.db_path) as db:
            db.execute(
                "UPDATE workflow_continuation_checkpoints SET continuation_json=? WHERE checkpoint_id=?",
                (json.dumps(state), cp.checkpoint_id),
            )
        with pytest.raises(ProcessInterfaceError) as caught:
            await answer(app, reference, cp, generate)
        assert caught.value.reason.code == "SUBJECT_STALE"
        assert len(calls) == 1
        assert (
            app.human_inputs.repository.get(cp.checkpoint_id).continuation[
                "response_id"
            ]
            is None
        )
    finally:
        await app.close()
