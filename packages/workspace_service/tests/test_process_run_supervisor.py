"""Backend task lifetime is independent from observers and start retries."""

import asyncio
import json
from types import SimpleNamespace

import pytest

from core.process_interactions import ValueBinding
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from packages.workspace_service.tests.test_process_preparation_service import (
    owner,
    scope,
)
from packages.workspace_service.tests.test_process_input_readiness import (
    source,
    process,
)


async def prepared_case(root, *, later=False):
    text = source(default="Exact requirements", later=later)
    path = root / process(text).source_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    application = owner(root, text)
    prepared = await application.set_inputs(scope(), process(text))
    return application, process(text), prepared.snapshot


async def start(application, reference, frozen, generate, request_id="start-one"):
    return await application.runs.start(
        scope(),
        reference,
        frozen.snapshot_id,
        request_id,
        expected_input_digest=frozen.digest,
        response_generator=generate,
    )


@pytest.mark.asyncio
async def test_start_allocates_before_model_finishes_and_lost_ack_retry_does_not_replay(
    tmp_path,
):
    application, reference, frozen = await prepared_case(tmp_path)
    entered, release = asyncio.Event(), asyncio.Event()
    calls = []

    async def generate(prompt, fmt):
        calls.append(prompt)
        entered.set()
        await release.wait()
        return "Actual controlled model result"

    try:
        receipt = await start(application, reference, frozen, generate)
        await asyncio.wait_for(entered.wait(), 2)
        retry = await start(application, reference, frozen, generate)
        assert retry == receipt
        assert receipt.run_log_path
        assert not (tmp_path / "first.txt").exists()
        release.set()
        result = await application.runs.wait(scope(), reference, receipt.run_id)
        assert result["status"] == "completed"
        assert result["run_id"] == receipt.run_id
        assert len(calls) == 1
        assert (tmp_path / "first.txt").read_text() == "Actual controlled model result"
    finally:
        release.set()
        await application.runs.close()


@pytest.mark.asyncio
async def test_disconnected_observer_does_not_cancel_backend_work(tmp_path):
    application, reference, frozen = await prepared_case(tmp_path)
    entered, release = asyncio.Event(), asyncio.Event()

    async def generate(prompt, fmt):
        entered.set()
        await release.wait()
        return "Completed after observer disconnect"

    try:
        receipt = await start(application, reference, frozen, generate)
        await asyncio.wait_for(entered.wait(), 2)
        observer = asyncio.create_task(
            application.runs.wait(scope(), reference, receipt.run_id)
        )
        await asyncio.sleep(0)
        observer.cancel()
        with pytest.raises(asyncio.CancelledError):
            await observer
        assert application.runs.is_live(receipt.run_id)
        release.set()
        result = await application.runs.wait(scope(), reference, receipt.run_id)
        assert result["status"] == "completed"
    finally:
        release.set()
        await application.runs.close()


@pytest.mark.asyncio
async def test_reopened_supervisor_reattaches_terminal_run_without_model_work(tmp_path):
    from workspace_service.process_interfaces.runs import ProcessRunSupervisor

    application, reference, frozen = await prepared_case(tmp_path)

    async def generate(prompt, fmt):
        return "Completed artifact"

    receipt = await start(application, reference, frozen, generate)
    await application.runs.wait(scope(), reference, receipt.run_id)
    await application.runs.close()
    reopened = ProcessRunSupervisor(application)

    async def forbidden(*args):
        raise AssertionError("Reattachment must not replay model work")

    try:
        retry = await reopened.start(
            scope(),
            reference,
            frozen.snapshot_id,
            "start-one",
            expected_input_digest=frozen.digest,
            response_generator=forbidden,
        )
        assert retry == receipt
        result = await reopened.wait(scope(), reference, receipt.run_id)
        assert result["status"] == "completed"
    finally:
        await reopened.close()


@pytest.mark.asyncio
async def test_same_request_with_changed_inputs_is_a_conflict(tmp_path):
    application, reference, frozen = await prepared_case(tmp_path)

    async def generate(prompt, fmt):
        return "Result"

    try:
        receipt = await start(application, reference, frozen, generate)
        await application.runs.wait(scope(), reference, receipt.run_id)
        changed = await application.set_inputs(
            scope(),
            reference,
            bindings=(ValueBinding(input_id="brief", value="Different requirements"),),
        )
        with pytest.raises(ProcessInterfaceError) as error:
            await start(application, reference, changed.snapshot, generate)
        assert error.value.reason.code == "REQUEST_CONFLICT"
    finally:
        await application.runs.close()


@pytest.mark.asyncio
async def test_explicit_local_cancel_keeps_completed_earlier_output(tmp_path):
    application, reference, frozen = await prepared_case(tmp_path, later=True)
    waiting = asyncio.Event()
    calls = 0

    async def generate(prompt, fmt):
        nonlocal calls
        calls += 1
        if calls == 1:
            return "Retained earlier output"
        waiting.set()
        await asyncio.Event().wait()

    try:
        receipt = await start(application, reference, frozen, generate)
        await asyncio.wait_for(waiting.wait(), 2)
        requested = await application.runs.cancel(
            scope("process.read", "process.cancel"),
            reference,
            receipt.run_id,
            "cancel-one",
        )
        assert requested["state"] == "cancellation_requested"
        result = await application.runs.wait(scope(), reference, receipt.run_id)
        assert result["status"] == "cancelled"
        assert (tmp_path / "first.txt").read_text() == "Retained earlier output"
        retry = await application.runs.cancel(
            scope("process.read", "process.cancel"),
            reference,
            receipt.run_id,
            "cancel-one",
        )
        assert retry == requested
    finally:
        await application.runs.close()


@pytest.mark.asyncio
async def test_runtime_shutdown_is_interrupted_and_cannot_restart_from_receipt(
    tmp_path,
):
    application, reference, frozen = await prepared_case(tmp_path)
    entered = asyncio.Event()

    async def generate(prompt, fmt):
        entered.set()
        await asyncio.Event().wait()

    receipt = await start(application, reference, frozen, generate)
    await asyncio.wait_for(entered.wait(), 2)
    await application.runs.close()
    from workspace_service.process_interfaces.runs import ProcessRunSupervisor

    reopened = ProcessRunSupervisor(application)
    try:
        retry = await reopened.start(
            scope(),
            reference,
            frozen.snapshot_id,
            "start-one",
            expected_input_digest=frozen.digest,
            response_generator=generate,
        )
        assert retry == receipt
        assert not reopened.is_live(receipt.run_id)
        result = await reopened.wait(scope(), reference, receipt.run_id)
        assert result["status"] == "interrupted"
    finally:
        await reopened.close()


@pytest.mark.asyncio
async def test_concurrent_duplicate_start_allocates_only_one_task(tmp_path):
    application, reference, frozen = await prepared_case(tmp_path)
    entered, release = asyncio.Event(), asyncio.Event()
    calls = 0

    async def generate(prompt, fmt):
        nonlocal calls
        calls += 1
        entered.set()
        await release.wait()
        return "One result"

    try:
        receipts = await asyncio.gather(
            start(application, reference, frozen, generate),
            start(application, reference, frozen, generate),
        )
        assert receipts[0] == receipts[1]
        await asyncio.wait_for(entered.wait(), 2)
        release.set()
        await application.runs.wait(scope(), reference, receipts[0].run_id)
        assert calls == 1
    finally:
        release.set()
        await application.runs.close()


@pytest.mark.asyncio
async def test_missing_execution_record_is_unknown_without_dispatch_replay(tmp_path):
    application, reference, frozen = await prepared_case(tmp_path)
    calls = 0

    async def generate(prompt, fmt):
        nonlocal calls
        calls += 1
        return "Recorded result"

    try:
        receipt = await start(application, reference, frozen, generate)
        await application.runs.wait(scope(), reference, receipt.run_id)
        (tmp_path / receipt.run_log_path).unlink()
        retry = await start(application, reference, frozen, generate)
        assert retry == receipt
        with pytest.raises(ProcessInterfaceError) as error:
            await application.runs.wait(scope(), reference, receipt.run_id)
        assert error.value.reason.code == "OUTCOME_UNKNOWN"
        assert calls == 1
    finally:
        await application.runs.close()


@pytest.mark.asyncio
async def test_capacity_is_bounded_but_a_start_retry_remains_read_only(tmp_path):
    from workspace_service.process_interfaces.runs import ProcessRunSupervisor

    application, reference, frozen = await prepared_case(tmp_path)
    application.__dict__["runs"] = ProcessRunSupervisor(application, maximum_active=1)
    entered, release = asyncio.Event(), asyncio.Event()

    async def generate(prompt, fmt):
        entered.set()
        await release.wait()
        return "Result"

    try:
        receipt = await start(application, reference, frozen, generate)
        await asyncio.wait_for(entered.wait(), 2)
        with pytest.raises(ProcessInterfaceError) as error:
            await start(
                application, reference, frozen, generate, request_id="another-start"
            )
        assert error.value.reason.code == "CAPABILITY_UNAVAILABLE"
        assert await start(application, reference, frozen, generate) == receipt
        release.set()
        await application.runs.wait(scope(), reference, receipt.run_id)
    finally:
        release.set()
        await application.runs.close()


@pytest.mark.asyncio
async def test_wrong_input_digest_rejects_before_allocating_or_generating(tmp_path):
    application, reference, frozen = await prepared_case(tmp_path)

    async def forbidden(*args):
        raise AssertionError("Invalid identity must not generate")

    try:
        with pytest.raises(ProcessInterfaceError) as error:
            await application.runs.start(
                scope(),
                reference,
                frozen.snapshot_id,
                "invalid-start",
                expected_input_digest="0" * 64,
                response_generator=forbidden,
            )
        assert error.value.reason.code == "SUBJECT_STALE"
        assert list(tmp_path.glob("runs/**/*.json")) == []
    finally:
        await application.runs.close()


@pytest.mark.asyncio
async def test_event_attachment_is_paged_scoped_and_never_replays(tmp_path):
    application, reference, frozen = await prepared_case(tmp_path)
    calls = []

    async def generate(prompt, fmt):
        calls.append(prompt)
        return "Only one execution"

    try:
        receipt = await start(application, reference, frozen, generate)
        await application.runs.wait(scope(), reference, receipt.run_id)
        first = await application.runs.events(
            scope(), reference, receipt.run_id, limit=1
        )
        assert len(first["events"]) == 1
        assert first["events"][0]["kind"] == "run_started"
        assert first["has_more"]
        next_page = await application.runs.events(
            scope(), reference, receipt.run_id, cursor=first["cursor"], limit=256
        )
        assert next_page["events"][0]["sequence"] == 2
        assert not next_page["has_more"]
        empty = await application.runs.events(
            scope(), reference, receipt.run_id, cursor=next_page["cursor"]
        )
        assert not empty["events"]
        assert empty["state"] == "completed"
        assert len(calls) == 1
        with pytest.raises(ProcessInterfaceError) as error:
            await application.runs.events(
                scope(), reference, receipt.run_id, cursor="not-a-cursor"
            )
        assert error.value.reason.code == "SUBJECT_STALE"
        serialized = json.dumps(next_page)
        assert "Only one execution" not in serialized
        assert "engineering_result" not in serialized
    finally:
        await application.runs.close()


@pytest.mark.asyncio
async def test_event_cursor_rejects_changed_history_and_other_run(tmp_path):
    application, reference, frozen = await prepared_case(tmp_path)

    async def generate(prompt, fmt):
        return "Result"

    try:
        receipt = await start(application, reference, frozen, generate)
        await application.runs.wait(scope(), reference, receipt.run_id)
        page = await application.runs.events(
            scope(), reference, receipt.run_id, limit=1
        )
        other = await start(application, reference, frozen, generate, "start-other")
        await application.runs.wait(scope(), reference, other.run_id)
        with pytest.raises(ProcessInterfaceError):
            await application.runs.events(
                scope(), reference, other.run_id, cursor=page["cursor"]
            )
        record_path = tmp_path / receipt.run_log_path
        record = json.loads(record_path.read_text(encoding="utf-8"))
        record["events"][0]["task_title"] = "Different recorded event"
        record_path.write_text(json.dumps(record), encoding="utf-8")
        with pytest.raises(ProcessInterfaceError) as error:
            await application.runs.events(
                scope(), reference, receipt.run_id, cursor=page["cursor"]
            )
        assert error.value.reason.code == "SUBJECT_STALE"
    finally:
        await application.runs.close()


@pytest.mark.asyncio
async def test_reservation_storage_failure_closes_qualified_runtime(
    tmp_path, monkeypatch
):
    application, reference, frozen = await prepared_case(tmp_path)
    runtime_closed = []

    async def close():
        runtime_closed.append(True)

    async def qualify(**kwargs):
        return SimpleNamespace(
            runtime=SimpleNamespace(close=close), run_id="private-run"
        )

    def fail(*args):
        raise OSError("Controlled storage failure")

    monkeypatch.setattr(
        "workspace_service.process_interfaces.runs.prepare_authorized_workflow_run",
        qualify,
    )
    monkeypatch.setattr(application.inputs, "reserve_start", fail)
    with pytest.raises(OSError):
        await start(application, reference, frozen, None)
    assert runtime_closed == [True]
    assert not application.runs.is_live("private-run")


@pytest.mark.asyncio
async def test_failed_preparation_maps_to_readable_reason_before_receipt(
    tmp_path, monkeypatch
):
    from workspace_service.workflow_source_execution import WorkflowSourceExecutionError

    application, reference, frozen = await prepared_case(tmp_path)

    async def fail(**kwargs):
        raise WorkflowSourceExecutionError(
            "WORKFLOW_SOURCE_CONFLICT", "Changed source", "Reload it."
        )

    monkeypatch.setattr(
        "workspace_service.process_interfaces.runs.prepare_authorized_workflow_run",
        fail,
    )
    with pytest.raises(ProcessInterfaceError) as error:
        await start(application, reference, frozen, None)
    assert error.value.reason.code == "SOURCE_CHANGED"
    assert not (tmp_path / "runs").exists()


@pytest.mark.asyncio
async def test_cancel_observer_disconnect_does_not_abandon_persisted_command(tmp_path):
    application, reference, frozen = await prepared_case(tmp_path)
    waiting = asyncio.Event()

    async def generate(prompt, fmt):
        waiting.set()
        await asyncio.Event().wait()

    try:
        receipt = await start(application, reference, frozen, generate)
        await asyncio.wait_for(waiting.wait(), 2)
        owned = application.runs._owned[receipt.run_id]
        original_emit = owned.emit
        entered, release = asyncio.Event(), asyncio.Event()

        async def slow_emit(event):
            await original_emit(event)
            entered.set()
            await release.wait()

        owned.emit = slow_emit
        observer = asyncio.create_task(
            application.runs.cancel(
                scope("process.read", "process.cancel"),
                reference,
                receipt.run_id,
                "cancel-one",
            )
        )
        await asyncio.wait_for(entered.wait(), 2)
        observer.cancel()
        with pytest.raises(asyncio.CancelledError):
            await observer
        release.set()
        result = await asyncio.wait_for(
            application.runs.wait(scope(), reference, receipt.run_id), 2
        )
        assert result["status"] == "cancelled"
    finally:
        await application.runs.close()


@pytest.mark.asyncio
async def test_start_ack_can_be_attached_without_waiting_for_model_completion(tmp_path):
    application, reference, frozen = await prepared_case(tmp_path)
    release = asyncio.Event()

    async def generate(prompt, fmt):
        await release.wait()
        return "Eventually complete"

    try:
        receipt = await start(application, reference, frozen, generate)
        assert (tmp_path / receipt.run_log_path).is_file()
        events = await application.runs.events(scope(), reference, receipt.run_id)
        assert events["state"] == "running"
        assert events["following"]
        release.set()
        assert (await application.runs.wait(scope(), reference, receipt.run_id))[
            "status"
        ] == "completed"
    finally:
        release.set()
        await application.runs.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("failed", [False, True])
async def test_workspace_shutdown_closes_run_owner_before_file_workers(failed):
    from workspace_service import WorkspaceService

    calls = []

    async def run_close():
        calls.append("processes")
        if failed:
            raise RuntimeError("Controlled shutdown diagnostic")

    async def runner_close():
        calls.append("runner")

    async def worker_close():
        calls.append("workers")

    workspace = SimpleNamespace(
        process_interfaces=SimpleNamespace(close=run_close),
        workflow_runner=SimpleNamespace(shutdown=runner_close),
        executor=SimpleNamespace(close=worker_close),
    )
    if failed:
        with pytest.raises(RuntimeError):
            await WorkspaceService.close(workspace)
    else:
        await WorkspaceService.close(workspace)
    assert calls == ["processes", "runner", "workers"]


@pytest.mark.asyncio
async def test_read_history_allows_current_source_reference_but_cancel_pins_run_source(
    tmp_path,
):
    application, reference, frozen = await prepared_case(tmp_path)
    waiting = asyncio.Event()

    async def generate(prompt, fmt):
        waiting.set()
        await asyncio.Event().wait()

    try:
        receipt = await start(application, reference, frozen, generate)
        await asyncio.wait_for(waiting.wait(), 2)
        current = reference.model_copy(update={"source_digest": "0" * 64})
        page = await application.runs.events(scope(), current, receipt.run_id)
        assert page["state"] == "running"
        with pytest.raises(ProcessInterfaceError) as error:
            await application.runs.cancel(
                scope("process.read", "process.cancel"),
                current,
                receipt.run_id,
                "wrong-revision",
            )
        assert error.value.reason.code == "SCOPE_DENIED"
        assert application.runs.is_live(receipt.run_id)
    finally:
        await application.runs.close()


@pytest.mark.asyncio
async def test_lost_start_observer_during_publication_keeps_allocated_run(
    tmp_path, monkeypatch
):
    application, reference, frozen = await prepared_case(tmp_path)
    entered, release = asyncio.Event(), asyncio.Event()
    original = application.workspace.files.write_generated
    calls = []

    async def delayed_publication(*args, **kwargs):
        result = await original(*args, **kwargs)
        if not entered.is_set():
            entered.set()
            await release.wait()
        return result

    async def generate(prompt, fmt):
        calls.append(prompt)
        return "Completed after lost acknowledgement"

    monkeypatch.setattr(
        application.workspace.files, "write_generated", delayed_publication
    )
    try:
        observer = asyncio.create_task(start(application, reference, frozen, generate))
        await asyncio.wait_for(entered.wait(), 2)
        receipt = application.inputs.start_receipt("user", reference, "start-one")
        observer.cancel()
        with pytest.raises(asyncio.CancelledError):
            await observer
        assert application.runs.is_live(receipt.run_id)
        assert await start(application, reference, frozen, generate) == receipt
        release.set()
        result = await application.runs.wait(scope(), reference, receipt.run_id)
        assert result["status"] == "completed"
        assert len(calls) == 1
    finally:
        release.set()
        await application.runs.close()
