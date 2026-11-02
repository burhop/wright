"""Nonphysical provider fixture through actual canonical preparation/run records."""

import asyncio
import json

import pytest

from packages.workspace_service.tests.test_process_input_readiness import (
    source,
    process,
)
from packages.workspace_service.tests.test_process_preparation_service import (
    owner,
    scope,
)
from packages.workspace_service.tests.test_workflow_artifact_review import section
from packages.workspace_service.tests.test_workflow_async_operations import remote
from workspace_service.workflow_mcp_execution import schema_digest
from workspace_service.workflow_source_execution import _parse
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service import workflow_async_operations


@pytest.mark.parametrize("outcome", ["cancelled", "completed", "failed", "working"])
@pytest.mark.parametrize("lost_observer", [False, True])
@pytest.mark.asyncio
async def test_provider_cancel_is_durable_once_and_observed_outcome_is_separate(
    tmp_path, monkeypatch, outcome, lost_observer, publication_fails=False
):
    gateway, unused_runtime, _, tools = remote(("working",))
    tools[0].input_schema.update(
        properties={"requirements": {"type": "string"}}, required=["requirements"]
    )
    tools[0].upstream_meta["wright/operation"].update(
        # Cancellation must wake this poll; disk publication and provider
        # confirmation are verified separately from the wakeup itself.
        poll_seconds=30,
        cancel_confirm_seconds=1,
    )
    entered = asyncio.Event()
    poll_waiting, poll_woken = asyncio.Event(), asyncio.Event()
    cancellation_type = workflow_async_operations.OperationCancellation

    def observe_cancellation(*args, **kwargs):
        cancellation = cancellation_type(*args, **kwargs)
        wait = cancellation.changed.wait

        async def observe_wait():
            assert not cancellation.changed.is_set()
            poll_waiting.set()
            await wait()
            poll_woken.set()

        monkeypatch.setattr(cancellation.changed, "wait", observe_wait)
        return cancellation

    monkeypatch.setattr(
        workflow_async_operations, "OperationCancellation", observe_cancellation
    )
    cancelled = False
    original = gateway.call_tool

    async def call(*args, **kwargs):
        nonlocal cancelled
        if args[2] == "fea__cancel":
            # The run command must be durable before provider mutation.
            records = list((tmp_path / "runs").glob("*/*.json"))
            record = json.loads(records[0].read_bytes())
            assert any(
                e.get("kind") == "cancellation_requested"
                and e.get("principal_id") == "user"
                for e in record["events"]
            )
            cancelled = True
        result = await original(*args, **kwargs)
        if args[2] == "fea__status":
            entered.set()
            if cancelled:
                result.structured_content["status"] = outcome
        return result

    gateway.call_tool = call
    blocks = _parse(source(default="Fixture requirements"))
    first = next(b["fields"] for b in blocks if b["id"] == "first")
    first["performed_by"] = "configured_tool"
    first["settings"].update(
        authoring_template="mcp-tool",
        mcp_tool=tools[0].name,
        mcp_server=tools[0].server_id,
        mcp_schema_digest=schema_digest(tools[0]),
        mcp_arguments="{}",
        mcp_argument_ports=json.dumps({"first_in": "requirements"}),
        output_format="json",
        output_filename="first.json",
    )
    text = "".join(section(b["kind"], b["id"], **b["fields"]) for b in blocks)
    reference = process(text)
    path = tmp_path / reference.source_path
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8")
    app = owner(tmp_path, text)

    async def no_model(*args):
        raise AssertionError("This configured tool fixture must not call a model.")

    try:
        frozen = await app.set_inputs(
            scope(), reference, gateway=gateway, session_id="fixture"
        )
        receipt = await app.runs.start(
            scope(),
            reference,
            frozen.snapshot.snapshot_id,
            "submit",
            expected_input_digest=frozen.snapshot.digest,
            response_generator=no_model,
            gateway=gateway,
            session_id="fixture",
        )
        await asyncio.wait_for(entered.wait(), 15)
        # Establish the actual waiting interleaving before requesting cancel.
        await asyncio.wait_for(poll_waiting.wait(), 15)
        command = app.runs.cancel(
            scope("process.read", "process.cancel"),
            reference,
            receipt.run_id,
            "cancel-once",
        )
        requested = None
        if publication_fails:
            owned = app.runs._owned[receipt.run_id]
            emit = owned.emit

            async def ambiguous_publication(event):
                await emit(event)
                if event["kind"] == "cancellation_requested":
                    raise RuntimeError(
                        "Injected uncertain acknowledgement of durable publication"
                    )

            owned.emit = ambiguous_publication
            with pytest.raises(ProcessInterfaceError) as uncertain:
                await command
            assert uncertain.value.reason.code == "OUTCOME_UNKNOWN"
        elif lost_observer:
            saved, release = asyncio.Event(), asyncio.Event()
            owned = app.runs._owned[receipt.run_id]
            emit = owned.emit

            async def defer_ack(event):
                await emit(event)
                if event["kind"] == "cancellation_requested":
                    saved.set()
                    await release.wait()

            owned.emit = defer_ack
            observer = asyncio.create_task(command)
            await asyncio.wait_for(saved.wait(), 15)
            assert not any(n == "fea__cancel" for n, _ in gateway.calls)
            observer.cancel()
            with pytest.raises(asyncio.CancelledError):
                await observer
            release.set()
        else:
            requested = await command
            assert requested["state"] == "cancellation_requested"
        # A missed signal cannot pass by waiting out the 30s provider poll.
        await asyncio.wait_for(poll_woken.wait(), 5)
        actual = await asyncio.wait_for(
            app.runs.wait(scope(), reference, receipt.run_id), 15
        )
        assert actual["status"] == (
            "reconciliation_required"
            if publication_fails
            else "reconciliation_required"
            if outcome == "working"
            else "cancelled"
        )
        retry = await app.runs.cancel(
            scope("process.read", "process.cancel"),
            reference,
            receipt.run_id,
            "cancel-once",
        )
        assert retry["state"] == "cancellation_requested"
        assert requested is None or retry == requested
        assert [n for n, _ in gateway.calls].count("fea__submit") == 1
        assert [n for n, _ in gateway.calls].count("fea__cancel") == (
            0 if publication_fails else 1
        )
        view = await app.get_snapshot(
            scope("process.read"), reference, run_id=receipt.run_id
        )
        assert view.observations[1].operation_id == "job-123"
        assert view.observations[1].state == (
            "reconciliation_required" if outcome == "working" else outcome
        )
        assert not (tmp_path / "first.json").exists()
    finally:
        await app.runs.close()
        await unused_runtime.close()


@pytest.mark.asyncio
async def test_uncertain_cancellation_publication_blocks_following_work_without_remote_mutation(
    tmp_path,
    monkeypatch,
):
    await test_provider_cancel_is_durable_once_and_observed_outcome_is_separate(
        tmp_path,
        monkeypatch,
        "working",
        False,
        publication_fails=True,
    )
