from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from workspace_service.rivet_approvals import (
    RivetApprovalError,
    RivetApprovalService,
)


def _request(service: RivetApprovalService, **changes):
    values = {
        "run_id": "run-1",
        "authority_id": "authority-1",
        "node_id": "node-1",
        "binding_digest": "a" * 64,
        "session_id": "session-1",
        "server_id": "server-1",
        "qualified_tool_name": "alpha__write",
        "request_id": "request-1",
        "arguments": {"value": 2},
        "required_gates": {"engineering.write"},
        "requested_by": "runner:run-1",
        "ttl_seconds": 30,
    }
    values.update(changes)
    return service.request(**values)


def test_exact_approval_is_argument_bound_and_one_shot():
    now = datetime(2026, 8, 13, tzinfo=UTC)
    service = RivetApprovalService(clock=lambda: now, id_factory=lambda: "approval-1")
    approval = _request(service)
    with pytest.raises(RivetApprovalError, match="changed"):
        service.decide(
            approval.approval_id,
            expected_digest="b" * 64,
            actor="engineer",
            approved=True,
        )
    approved = service.decide(
        approval.approval_id,
        expected_digest=approval.approval_digest,
        actor="engineer",
        approved=True,
    )
    assert approved.state == "approved"
    consumed = service.consume(
        approval.approval_id, argument_digest=approval.argument_digest
    )
    assert consumed.state == "consumed"
    with pytest.raises(RivetApprovalError, match="pending"):
        service.consume(approval.approval_id, argument_digest=approval.argument_digest)


def test_approval_expires_and_changed_arguments_get_distinct_digest():
    now = datetime(2026, 8, 13, tzinfo=UTC)
    current = now
    service = RivetApprovalService(clock=lambda: current)
    first = _request(service)
    second = _request(service, request_id="request-2", arguments={"value": 3})
    assert first.approval_digest != second.approval_digest
    current = now + timedelta(minutes=1)
    with pytest.raises(RivetApprovalError, match="expired"):
        service.decide(
            first.approval_id,
            expected_digest=first.approval_digest,
            actor="engineer",
            approved=True,
        )
