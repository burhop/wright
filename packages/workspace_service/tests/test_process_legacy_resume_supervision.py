"""Compatibility resume shares backend task lifetime and exact cancellation."""

import asyncio
import json
from dataclasses import replace

import pytest

from workspace_service.process_interfaces.errors import ProcessInterfaceError
from packages.workspace_service.tests.test_process_action_supervision import (
    action_scope,
    approved_action_case,
)


async def resume(
    case, generate, *, request_id="legacy-resume", scope=None, checkpoint=None
):
    app, reference, _, checkpoint_id, digest, *_ = case
    checkpoint = checkpoint or app.workspace.workflow_external_actions.lookup(
        checkpoint_id
    )
    return await app.runs.resume_legacy_approval(
        scope or action_scope(),
        reference,
        checkpoint,
        request_id,
        expected_subject_digest=digest,
        response_generator=generate,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("cancel", [False, True])
async def test_legacy_observer_disconnect_keeps_same_run_supervised(tmp_path, cancel):
    case, _ = await approved_action_case(tmp_path)
    app, reference, receipt, _, _, calls, _ = case
    entered, release = asyncio.Event(), asyncio.Event()

    async def generate(prompt, fmt):
        calls.append(prompt)
        entered.set()
        await release.wait()
        return "Controlled resumed output"

    observer = asyncio.create_task(resume(case, generate))
    try:
        await asyncio.wait_for(entered.wait(), 4)
        assert app.runs.is_live(receipt.run_id)
        assert app.runs.cancellation_capability(receipt.run_id) == (True, "")
        observer.cancel()
        with pytest.raises(asyncio.CancelledError):
            await observer
        assert app.runs.is_live(receipt.run_id)
        with pytest.raises(ProcessInterfaceError) as conflict:
            await resume(case, generate, request_id="another-resume")
        assert conflict.value.reason.code == "REQUEST_CONFLICT"
        duplicate = asyncio.create_task(resume(case, generate))
        await asyncio.sleep(0)
        if cancel:
            accepted = await app.runs.cancel(
                action_scope(), reference, receipt.run_id, "cancel-legacy"
            )
            assert accepted["state"] == "cancellation_requested"
            with pytest.raises(asyncio.CancelledError):
                await duplicate
            result = await app.runs.wait(action_scope(), reference, receipt.run_id)
            assert result["status"] == "cancelled"
        else:
            release.set()
            checkpoint, result = await duplicate
            assert result["status"] == "completed"
            assert checkpoint.external_action["principal_id"] == "operator"
            # Replayed records use JSON arrays where the in-memory result has
            # tuples. The public serialized result must remain identical.
            assert json.loads(
                json.dumps((await resume(case, generate))[1])
            ) == json.loads(json.dumps(result))
        assert len(calls) == 2
        assert not app.runs.is_live(receipt.run_id)
    finally:
        release.set()
        await app.close()


@pytest.mark.asyncio
async def test_preparing_resume_is_live_without_claiming_cancellation(
    tmp_path, monkeypatch
):
    from workspace_service import workflow_approval_execution as approval

    case, _ = await approved_action_case(tmp_path)
    app, reference, receipt, _, _, _, generate = case
    entered, release = asyncio.Event(), asyncio.Event()
    original = approval._prepare

    async def delayed(**kwargs):
        entered.set()
        await release.wait()
        return await original(**kwargs)

    monkeypatch.setattr(approval, "_prepare", delayed)
    request = asyncio.create_task(resume(case, generate))
    try:
        await asyncio.wait_for(entered.wait(), 4)
        assert app.runs.is_live(receipt.run_id)
        enabled, reason = app.runs.cancellation_capability(receipt.run_id)
        assert not enabled and "Execution is preparing" in reason
        with pytest.raises(ProcessInterfaceError) as unavailable:
            await app.runs.cancel(
                action_scope(), reference, receipt.run_id, "premature-cancel"
            )
        assert unavailable.value.reason.code == "CAPABILITY_UNAVAILABLE"
        release.set()
        assert (await request)[1]["status"] == "completed"
    finally:
        release.set()
        await app.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "changed", ["workspace", "source", "subject", "run_scope", "capability"]
)
async def test_legacy_resume_rejects_crossed_scope_before_execution(tmp_path, changed):
    case, _ = await approved_action_case(tmp_path)
    app, _, receipt, checkpoint_id, _, calls, generate = case
    checkpoint = app.workspace.workflow_external_actions.lookup(checkpoint_id)
    scope = action_scope()
    if changed == "workspace":
        checkpoint = replace(checkpoint, workspace_id="elsewhere")
    elif changed == "source":
        checkpoint = replace(
            checkpoint, workflow_id="workflows/elsewhere.workflow.wflow"
        )
    elif changed == "subject":
        checkpoint = replace(checkpoint, subject_digest="f" * 64)
    elif changed == "run_scope":
        scope = replace(scope, run_bound=True, run_id="another-run")
    else:
        scope = replace(scope, capabilities=frozenset({"process.read"}))
    try:
        with pytest.raises(ProcessInterfaceError):
            await resume(case, generate, checkpoint=checkpoint, scope=scope)
        assert not app.runs.is_live(receipt.run_id)
        assert len(calls) == 1
    finally:
        await app.close()
