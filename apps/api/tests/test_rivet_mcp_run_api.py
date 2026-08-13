from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from api.routers import workspace as workspace_router
from api.schemas.workspace import RivetCallApprovalDecisionRequest
from core.rivet_mcp import ApprovalState, PendingRivetCallApproval
from core.workflow_runs import WorkflowRun, WorkflowRunState
from fastapi import HTTPException
from workspace_service.workflow_operations import WorkflowOperationsError


def _run(workspace_id="workspace-1", session_id="session-1"):
    return WorkflowRun(
        "run-1",
        workspace_id,
        session_id,
        "workflow-1",
        1,
        1,
        WorkflowRunState.RUNNING,
    )


def _approval(state=ApprovalState.PENDING):
    now = datetime.now(UTC)
    return PendingRivetCallApproval(
        approval_id="approval-1",
        run_id="run-1",
        authority_id="authority-1",
        node_id="node-1",
        binding_digest="a" * 64,
        session_id="gateway-session",
        server_id="beta",
        qualified_tool_name="beta__write",
        request_id="request-1",
        argument_digest="b" * 64,
        argument_summary={"length": 2, "authorization": "[REDACTED]"},
        required_gates=("engineering.write",),
        state=state,
        requested_by="runner:run-1",
        created_at=now,
        expires_at=now + timedelta(minutes=5),
        approval_digest="c" * 64,
    )


@pytest.fixture(autouse=True)
def _features(monkeypatch):
    monkeypatch.setattr(workspace_router, "_runner_feature_enabled", lambda: None)
    monkeypatch.setattr(workspace_router, "_operations_feature_enabled", lambda: None)


@pytest.mark.asyncio
async def test_pending_approval_api_is_run_and_workspace_scoped_and_redacted():
    calls = []

    class Operations:
        def call_approvals(self, **kwargs):
            calls.append(kwargs)
            return (_approval(),)

    service = SimpleNamespace(
        lifecycle=SimpleNamespace(
            get_by_session=lambda session: (
                {"workspace_id": "workspace-1"} if session == "session-1" else None
            )
        ),
        workflow_operations=Operations(),
    )
    response = await workspace_router.workflow_run_approvals_endpoint(
        "run-1", "session-1", service
    )
    assert calls == [
        {
            "workspace_id": "workspace-1",
            "session_id": "session-1",
            "run_id": "run-1",
        }
    ]
    assert response.approvals[0].qualified_tool_name == "beta__write"
    encoded = response.model_dump_json()
    assert "gateway-session" not in encoded
    assert "authority-1" not in encoded
    assert "[REDACTED]" in encoded

    with pytest.raises(HTTPException) as denied:
        await workspace_router.workflow_run_approvals_endpoint(
            "run-1", "session-other", service
        )
    assert denied.value.status_code == 404


@pytest.mark.asyncio
async def test_approval_decision_forwards_exact_digest_and_hides_cross_run_records():
    calls = []

    class Operations:
        def decide_call_approval(self, **kwargs):
            calls.append(kwargs)
            if kwargs["run_id"] != "run-1":
                raise WorkflowOperationsError(
                    "RIVET_CALL_APPROVAL_NOT_FOUND", "not found"
                )
            return _approval(ApprovalState.APPROVED)

    service = SimpleNamespace(
        lifecycle=SimpleNamespace(
            get_by_session=lambda _session: {"workspace_id": "workspace-1"}
        ),
        workflow_operations=Operations(),
    )
    response = await workspace_router.decide_workflow_run_approval_endpoint(
        "run-1",
        "approval-1",
        RivetCallApprovalDecisionRequest(
            session_id="session-1",
            expected_digest="c" * 64,
            decision="approved",
            actor="engineer",
        ),
        service,
    )
    assert response.state == "approved"
    assert calls[0]["expected_digest"] == "c" * 64
    assert calls[0]["approved"] is True
    assert "client_approval_hint" not in calls[0]

    with pytest.raises(HTTPException) as hidden:
        await workspace_router.decide_workflow_run_approval_endpoint(
            "run-other",
            "approval-1",
            RivetCallApprovalDecisionRequest(
                session_id="session-1",
                expected_digest="c" * 64,
                decision="denied",
                actor="engineer",
            ),
            service,
        )
    assert hidden.value.status_code == 404
