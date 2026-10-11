"""Supervised exact digital/local actions; no physical provider is exercised."""

import asyncio
import json
from dataclasses import replace

import pytest

from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.process_interfaces.service import ProcessInterfaceService
from packages.workspace_service.tests.test_process_review_decisions import (
    waiting_review_case,
    review_source,
    review_scope,
)
from packages.workspace_service.tests.test_workflow_artifact_review import section, port
from packages.workspace_service.tests.test_workflow_mcp_operations import (
    DigitalGateway,
    configured_source,
)


def action_scope(actor="operator"):
    return replace(
        review_scope(actor),
        capabilities=review_scope().capabilities | {"process.action", "process.cancel"},
    )


def with_after(text):
    text += section(
        "task",
        "after",
        name="Use the reviewed result",
        purpose="Continue the same run",
        step_type="work",
        group=None,
        performed_by="ai_assisted",
        inputs=[],
        outputs=[port("after_out")],
        prompt="Use the completed approved step.",
        tool=None,
        reusable_step=None,
        settings={"output_format": "text", "output_filename": "after.txt"},
    )
    checkpoint = "approve" if "task approve\n" in text else "review"
    return text + section(
        "connection",
        "continue_after",
        type="order",
        **{"from": checkpoint, "to": "after"},
        label="After the declared action",
        when=None,
    )


async def approved_action_case(root, *, digital=False, gateway=None, text=None):
    gateway = gateway or (DigitalGateway() if digital else None)
    text = text or with_after(
        configured_source(tool=gateway.tool) if digital else review_source()
    )
    case = await waiting_review_case(root, text=text, gateway=gateway)
    app, reference, _, cp, digest, *_ = case
    await app.reviews.decide(
        review_scope(),
        reference,
        cp,
        "review-action",
        expected_subject_digest=digest,
        decision="approved",
        reason="Synthetic nonphysical test review",
        gateway=gateway,
    )
    return case, gateway


async def submit(
    case, gateway=None, *, request_id="action-one", actor="operator", generate=None
):
    app, reference, _, cp, digest, _, original_generate = case
    return await app.runs.request_action(
        action_scope(actor),
        reference,
        f"continue-{cp}",
        request_id,
        expected_subject_digest=digest,
        response_generator=generate or original_generate,
        gateway=gateway,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("digital", [False, True])
async def test_action_returns_durable_authority_while_backend_owns_continuation(
    tmp_path, digital
):
    case, gateway = await approved_action_case(tmp_path, digital=digital)
    app, reference, receipt, cp, _, calls, _ = case
    entered, release = asyncio.Event(), asyncio.Event()

    async def generate(prompt, fmt):
        calls.append(prompt)
        entered.set()
        await release.wait()
        return "Synthetic continued result"

    try:
        snapshot = await submit(case, gateway, generate=generate)
        interaction = next(i for i in snapshot.interactions if i.checkpoint_id == cp)
        assert interaction.action_receipt.request_id == "action-one"
        assert interaction.action_receipt.principal_id == "operator"
        await asyncio.wait_for(entered.wait(), 4)
        assert app.runs.is_live(receipt.run_id)
        observer = asyncio.create_task(
            app.runs.wait(action_scope(), reference, receipt.run_id)
        )
        await asyncio.sleep(0)
        observer.cancel()
        with pytest.raises(asyncio.CancelledError):
            await observer
        assert app.runs.is_live(receipt.run_id)
        duplicate = await submit(case, gateway, generate=generate)
        assert duplicate.context.run_id == receipt.run_id
        with pytest.raises(ProcessInterfaceError) as conflict:
            await submit(case, gateway, request_id="other-action", generate=generate)
        assert conflict.value.reason.code == "REQUEST_CONFLICT"
        release.set()
        result = await app.runs.wait(action_scope(), reference, receipt.run_id)
        assert result["status"] == "completed" and result["run_id"] == receipt.run_id
        assert len(calls) == 2
        if digital:
            assert len(gateway.calls) == 1
        await app.close()
        recreated = ProcessInterfaceService(app.workspace)
        app.workspace.process_interfaces = recreated
        case = (recreated, *case[1:])
        recovered = await submit(case, gateway, generate=generate)
        assert recovered.context.run_id == receipt.run_id
        assert len(calls) == 2
        if digital:
            assert len(gateway.calls) == 1
        await recreated.close()
    finally:
        release.set()
        await app.close()


@pytest.mark.asyncio
async def test_action_acknowledges_authorization_before_provider_acceptance(tmp_path):
    class SlowGateway(DigitalGateway):
        async def call_tool(self, *args, **kwargs):
            self.entered.set()
            await self.release.wait()
            return await super().call_tool(*args, **kwargs)

    gateway = SlowGateway()
    gateway.entered, gateway.release = asyncio.Event(), asyncio.Event()
    case, _ = await approved_action_case(tmp_path, digital=True, gateway=gateway)
    app, reference, receipt, cp, *_ = case
    try:
        snapshot = await submit(case, gateway)
        await asyncio.wait_for(gateway.entered.wait(), 4)
        action = next(
            i for i in snapshot.interactions if i.checkpoint_id == cp
        ).action_receipt
        assert action.submission == "authorized" and not action.delivery_completed
        assert not gateway.calls
        assert app.runs.is_live(receipt.run_id)
        gateway.release.set()
        completed = await app.runs.wait(action_scope(), reference, receipt.run_id)
        assert completed["status"] == "completed" and len(gateway.calls) == 1
    finally:
        gateway.release.set()
        await app.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("digital", [False, True])
@pytest.mark.parametrize(
    "change", ["approval", "artifact", "source", "scope", "subject"]
)
async def test_action_preflight_rejects_unapproved_changed_or_unscoped_requests(
    tmp_path, digital, change
):
    gateway = DigitalGateway() if digital else None
    text = with_after(configured_source() if digital else review_source())
    if change == "approval":
        case = await waiting_review_case(tmp_path, text=text, gateway=gateway)
    else:
        case, _ = await approved_action_case(
            tmp_path, digital=digital, gateway=gateway, text=text
        )
    app, reference, receipt, cp, digest, calls, generate = case
    try:
        if change == "artifact":
            (tmp_path / ("package.json" if digital else "first.txt")).write_text(
                "Changed actual reviewed artifact"
            )
        if change == "source":
            path = tmp_path / reference.source_path
            path.write_bytes(path.read_bytes() + b"\n")
        with pytest.raises(ProcessInterfaceError):
            await app.runs.request_action(
                review_scope() if change == "scope" else action_scope(),
                reference,
                f"continue-{cp}",
                "action-one",
                expected_subject_digest="0" * 64 if change == "subject" else digest,
                response_generator=generate,
                gateway=gateway,
            )
        assert len(calls) == 1
        if gateway:
            assert not gateway.calls
        assert (
            app.workspace.workflow_external_actions.lookup(cp).external_action is None
        )
        assert not app.runs.is_live(receipt.run_id)
    finally:
        await app.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("publication_fails", [False, True])
async def test_action_acknowledges_durable_consume_before_slow_run_log_publication(
    tmp_path, monkeypatch, publication_fails
):
    from workspace_service import workflow_approval_execution as approvals

    case, gateway = await approved_action_case(tmp_path, digital=True)
    app, reference, receipt, cp, _, calls, _ = case
    entered, release = asyncio.Event(), asyncio.Event()
    original = approvals.record_workflow_approval_transition

    async def delayed_publication(**kwargs):
        if kwargs["kind"] == "external_action_authorized":
            entered.set()
            await release.wait()
            if publication_fails:
                raise OSError("Synthetic run-log publication failure")
        return await original(**kwargs)

    monkeypatch.setattr(
        approvals, "record_workflow_approval_transition", delayed_publication
    )
    try:
        snapshot = await asyncio.wait_for(submit(case, gateway), 4)
        await asyncio.wait_for(entered.wait(), 4)
        interaction = next(
            item for item in snapshot.interactions if item.checkpoint_id == cp
        )
        assert interaction.action_receipt.request_id == "action-one"
        assert interaction.action_receipt.submission == "authorized"
        assert not interaction.action_receipt.delivery_completed
        retained = app.workspace.workflow_external_actions.lookup(cp)
        assert retained.state == "consumed"
        assert retained.external_action["action_id"] == "action-one"
        assert not gateway.calls and len(calls) == 1
        assert app.runs.is_live(receipt.run_id)
        release.set()
        if publication_fails:
            # The wait API returns recorded authority even when its owned task
            # fails; the checkpoint remains the authority for replay refusal.
            await app.runs.wait(action_scope(), reference, receipt.run_id)
            retained = app.workspace.workflow_external_actions.lookup(cp)
            assert retained.external_action["outcome"] == "outcome_unknown"
            with pytest.raises(ProcessInterfaceError) as unknown:
                await submit(case, gateway)
            assert unknown.value.reason.code == "OUTCOME_UNKNOWN"
            assert not gateway.calls and len(calls) == 1
        else:
            completed = await app.runs.wait(action_scope(), reference, receipt.run_id)
            assert completed["status"] == "completed"
            assert completed["run_id"] == receipt.run_id and len(gateway.calls) == 1
    finally:
        release.set()
        await app.close()


@pytest.mark.asyncio
async def test_accepted_digital_operation_is_observed_and_cancelled_via_existing_owner(
    tmp_path,
):
    from tool_registry.gateway_models import GatewayToolResult
    from packages.workspace_service.tests.test_workflow_mcp_operations import (
        ObservedGateway,
        PROFILE,
        TOOL,
        STATUS_TOOL,
        QUALIFICATION,
        digest,
    )

    cancel_tool = replace(
        STATUS_TOOL,
        name="digital-proof__cancel",
        tool_name="cancel",
        annotations={"readOnlyHint": False},
    )
    profile = {**PROFILE, "cancel_tool": "cancel", "cancel_confirm_seconds": 0.5}

    class CancelGateway(ObservedGateway):
        def __init__(self):
            super().__init__()
            self.tool = replace(
                TOOL, upstream_meta={**TOOL.upstream_meta, "wright/operation": profile}
            )
            self.cancelled = False
            self.working = asyncio.Event()

        def list_tools(self, *args):
            return self.tool, STATUS_TOOL, cancel_tool

        async def call_tool(self, *args, **kwargs):
            if args[2] == cancel_tool.name:
                self.calls.append((args, kwargs))
                self.cancelled = True
                return GatewayToolResult(
                    content=(), structured_content={"request": "accepted"}
                )
            if args[2] == STATUS_TOOL.name:
                self.calls.append((args, kwargs))
                self.working.set()
                return GatewayToolResult(
                    content=(),
                    structured_content={
                        "operation_id": "digital-private-1",
                        "job_state": "cancelled" if self.cancelled else "working",
                    },
                )
            return await super().call_tool(*args, **kwargs)

    gateway = CancelGateway()
    case, _ = await approved_action_case(
        tmp_path,
        digital=True,
        gateway=gateway,
        text=with_after(
            configured_source(
                tool=gateway.tool,
                settings_patch={
                    "operation_policy": {
                        "mode": "observe",
                        "qualification_digest": digest(QUALIFICATION),
                        "profile_digest": digest(profile),
                    }
                },
            )
        ),
    )
    app, reference, receipt, cp, *_ = case
    try:
        await submit(case, gateway)
        await asyncio.wait_for(gateway.working.wait(), 4)
        snapshot = await app.get_snapshot(
            action_scope(), reference, run_id=receipt.run_id, gateway=gateway
        )
        approved = next(
            i for i in snapshot.interactions if i.checkpoint_id == cp
        ).action_receipt
        assert approved.submission == "accepted" and not approved.delivery_completed
        assert approved.observed_outcome is None
        assert next(a for a in snapshot.actions if a.operation == "cancel").enabled
        requested = await app.runs.cancel(
            action_scope(), reference, receipt.run_id, "cancel-operation"
        )
        assert requested["state"] == "cancellation_requested"
        completed = await app.runs.wait(action_scope(), reference, receipt.run_id)
        assert completed["status"] == "cancelled"
        final = await app.get_snapshot(
            action_scope(), reference, run_id=receipt.run_id, gateway=gateway
        )
        evidence = next(
            i for i in final.interactions if i.checkpoint_id == cp
        ).action_receipt
        assert evidence.submission == "accepted"
        assert (
            evidence.cancellation_requested
            and evidence.cancellation_outcome == "cancelled"
        )
        assert (
            evidence.observed_outcome == "cancelled" and not evidence.delivery_completed
        )
        assert len(case[5]) == 1
        assert len([call for call in gateway.calls if call[0][2] == TOOL.name]) == 1
        assert (
            len([call for call in gateway.calls if call[0][2] == cancel_tool.name]) == 1
        )
        record = json.loads((tmp_path / receipt.run_log_path).read_text())
        assert (
            len(
                [
                    event
                    for event in record["events"]
                    if event["kind"] == "cancellation_requested"
                ]
            )
            == 1
        )
    finally:
        await app.close()


@pytest.mark.asyncio
async def test_disconnected_action_request_does_not_cancel_registered_work(
    tmp_path, monkeypatch
):
    from workspace_service import workflow_approval_execution as approval

    case, gateway = await approved_action_case(tmp_path, digital=True)
    app, reference, receipt, _, _, calls, _ = case
    original = approval._prepare
    entered, release = asyncio.Event(), asyncio.Event()
    preparation_count = 0

    async def delayed(*args, **kwargs):
        nonlocal preparation_count
        preparation_count += 1
        result = await original(*args, **kwargs)
        if preparation_count == 2:
            entered.set()
            await release.wait()
        return result

    monkeypatch.setattr(approval, "_prepare", delayed)
    request = asyncio.create_task(submit(case, gateway))
    try:
        await asyncio.wait_for(entered.wait(), 4)
        request.cancel()
        with pytest.raises(asyncio.CancelledError):
            await request
        assert app.runs.is_live(receipt.run_id)
        release.set()
        completed = await app.runs.wait(action_scope(), reference, receipt.run_id)
        assert completed["status"] == "completed"
        assert len(gateway.calls) == 1 and len(calls) == 2
    finally:
        release.set()
        await app.close()


@pytest.mark.asyncio
async def test_unfinished_claimed_action_continuation_is_not_replayed(tmp_path):
    case, gateway = await approved_action_case(tmp_path, digital=True)
    app, reference, receipt, cp, _, calls, _ = case
    entered = asyncio.Event()

    async def blocked(prompt, fmt):
        calls.append(prompt)
        entered.set()
        await asyncio.Future()

    try:
        await submit(case, gateway, generate=blocked)
        await asyncio.wait_for(entered.wait(), 4)
        await app.close()
        record = json.loads((tmp_path / receipt.run_log_path).read_text())
        assert record["resume_segments"][cp]["state"] == "outcome_unknown"
        recreated = ProcessInterfaceService(app.workspace)
        app.workspace.process_interfaces = recreated
        with pytest.raises(ProcessInterfaceError) as unknown:
            await submit((recreated, *case[1:]), gateway, generate=blocked)
        assert unknown.value.reason.code == "OUTCOME_UNKNOWN"
        assert len(gateway.calls) == 1 and len(calls) == 2
        await recreated.close()
    finally:
        await app.close()


@pytest.mark.asyncio
async def test_confirmed_delivery_can_continue_after_a_lost_unclaimed_segment(
    tmp_path, monkeypatch
):
    from workspace_service import workflow_approval_execution as approval

    case, gateway = await approved_action_case(tmp_path, digital=True)
    app, reference, receipt, cp, _, calls, _ = case
    original = approval.record_workflow_resume

    async def before_claim(**kwargs):
        raise OSError("Synthetic interruption before any downstream claim")

    monkeypatch.setattr(approval, "record_workflow_resume", before_claim)
    try:
        await submit(case, gateway)
        await app.runs.wait(action_scope(), reference, receipt.run_id)
        record = json.loads((tmp_path / receipt.run_log_path).read_text())
        assert cp not in record.get("resume_segments", {})
        assert len(gateway.calls) == len(calls) == 1
        monkeypatch.setattr(approval, "record_workflow_resume", original)
        await submit(case, gateway)
        result = await app.runs.wait(action_scope(), reference, receipt.run_id)
        assert result["status"] == "completed"
        assert len(gateway.calls) == 1 and len(calls) == 2
    finally:
        await app.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("unknown", [False, True])
async def test_rejected_or_unknown_consumed_submission_never_replays(tmp_path, unknown):
    gateway = DigitalGateway()
    if unknown:
        gateway.exception = ConnectionError("Synthetic uncertain provider effect")
    else:
        gateway.response = {"status": "rejected"}
    case, _ = await approved_action_case(tmp_path, digital=True, gateway=gateway)
    app, reference, receipt, cp, *_ = case
    try:
        accepted = await submit(case, gateway)
        assert accepted.context.run_id == receipt.run_id
        await app.runs.wait(action_scope(), reference, receipt.run_id)
        with pytest.raises(ProcessInterfaceError) as refused:
            await submit(case, gateway)
        assert refused.value.reason.code == "OUTCOME_UNKNOWN"
        assert len(gateway.calls) == len(case[5]) == 1
        record = json.loads((tmp_path / receipt.run_log_path).read_text())
        assert record["status"] == (
            "external_action_outcome_unknown"
            if unknown
            else "external_action_not_dispatched"
        )
    finally:
        await app.close()
