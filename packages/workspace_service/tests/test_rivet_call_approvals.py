from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from core.rivet_mcp import ApprovalState, canonical_digest
from workspace_service.rivet_approvals import RivetApprovalError, RivetApprovalService


def _request(service: RivetApprovalService, **changes):
    values = {
        "run_id": "run-1",
        "authority_id": "authority-1",
        "node_id": "node-1",
        "binding_digest": "a" * 64,
        "session_id": "session-1",
        "server_id": "cad",
        "qualified_tool_name": "cad__write",
        "request_id": "request-1",
        "arguments": {"length": 2},
        "required_gates": {"engineering.write"},
        "requested_by": "runner:run-1",
        "ttl_seconds": 60,
    }
    values.update(changes)
    return service.request(**values)


def test_approval_is_digest_bound_denyable_and_one_shot():
    now = datetime(2026, 8, 13, tzinfo=UTC)
    service = RivetApprovalService(clock=lambda: now, id_factory=lambda: "approval-1")
    pending = _request(service)
    assert pending.state is ApprovalState.PENDING
    assert pending.argument_digest == canonical_digest({"length": 2})
    assert "client" not in pending.approval_digest

    with pytest.raises(RivetApprovalError, match="changed"):
        service.decide(
            pending.approval_id,
            expected_digest="b" * 64,
            actor="engineer",
            approved=True,
        )
    approved = service.decide(
        pending.approval_id,
        expected_digest=pending.approval_digest,
        actor="engineer",
        approved=True,
    )
    assert approved.state is ApprovalState.APPROVED
    with pytest.raises(RivetApprovalError, match="arguments changed"):
        service.consume(
            approved.approval_id, argument_digest=canonical_digest({"length": 3})
        )
    consumed = service.consume(
        approved.approval_id, argument_digest=canonical_digest({"length": 2})
    )
    assert consumed.state is ApprovalState.CONSUMED
    with pytest.raises(RivetApprovalError, match="not pending"):
        service.consume(
            approved.approval_id, argument_digest=canonical_digest({"length": 2})
        )


@pytest.mark.asyncio
async def test_denied_expired_and_cancelled_calls_wake_waiters():
    current = datetime(2026, 8, 13, tzinfo=UTC)
    service = RivetApprovalService(clock=lambda: current)
    denied = _request(service, request_id="deny")
    waiter = asyncio.create_task(service.wait(denied.approval_id))
    await asyncio.sleep(0)
    service.decide(
        denied.approval_id,
        expected_digest=denied.approval_digest,
        actor="engineer",
        approved=False,
        reason="Not authorized",
    )
    assert (await waiter).state is ApprovalState.DENIED

    cancelled = _request(service, request_id="cancel")
    cancel_waiter = asyncio.create_task(service.wait(cancelled.approval_id))
    await asyncio.sleep(0)
    assert service.cancel_run("run-1") == 1
    assert (await cancel_waiter).state is ApprovalState.CANCELLED

    expired = _request(service, request_id="expired", ttl_seconds=1)
    current += timedelta(seconds=2)
    with pytest.raises(RivetApprovalError, match="expired"):
        service.decide(
            expired.approval_id,
            expected_digest=expired.approval_digest,
            actor="engineer",
            approved=True,
        )


def test_same_request_cannot_change_arguments_or_gate_scope():
    service = RivetApprovalService()
    _request(service)
    with pytest.raises(RivetApprovalError, match="changed"):
        _request(service, arguments={"length": 3})
    with pytest.raises(RivetApprovalError, match="changed"):
        _request(service, required_gates={"physical.actuation"})
