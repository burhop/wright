"""Scoped campaign readiness uses the ordinary source endpoint and durable recorder."""

import hashlib
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio
from fastapi import HTTPException

from api.routers import workspace as router
from api.schemas.workspace import WorkflowSourceRunRequest
from api.schemas.workspace import (
    WorkflowApprovalDecisionRequest,
    WorkflowApprovalResumeRequest,
)
from workspace_service.executor import BoundedExecutor
from workspace_service.workflow_integration_policy import (
    WorkflowIntegrationPolicyService,
)
from workspace_service.workflow_sources import WorkspaceWorkflowSourceUseCases
from packages.workspace_service.tests.test_workflow_external_action_execution import (
    service,
)
from packages.workspace_service.tests.test_workflow_artifact_review import section, port


@pytest_asyncio.fixture
async def prepared(tmp_path, monkeypatch):
    svc = service(tmp_path)
    svc.workflow_sources = WorkspaceWorkflowSourceUseCases(BoundedExecutor())
    text = section(
        "workflow",
        "campaign",
        name="API test",
        purpose="Scoped execution",
        discipline="engineering",
        reviewed_ai_suggestions=False,
    )
    text += section(
        "task",
        "report",
        name="Report",
        purpose="Generate report",
        group=None,
        step_type="work",
        performed_by="ai_assisted",
        tool=None,
        reusable_step=None,
        inputs=[],
        outputs=[port("report_response")],
        prompt="Write a report",
        settings={
            "output_format": "text",
            "save_output": True,
            "output_filename": "outputs/attempt/report.txt",
        },
    )
    path = "workflows/campaign.workflow.wflow"
    document = await svc.workflow_sources.create(str(tmp_path), path, text)
    (tmp_path / "brief.md").write_bytes(b"Synthetic engineering test brief")
    svc.workflow_sources.read_template_origin = AsyncMock(
        return_value={
            "template_id": "printed-replacement-part",
            "template_version": "1.0.0",
        }
    )
    svc.engineering_workflow_templates = SimpleNamespace(
        readiness=Mock(
            return_value={
                "state": "setup_required",
                "blocking_reasons": ["Not publicly qualified"],
            }
        )
    )
    svc.workflow_integration_policies = WorkflowIntegrationPolicyService(
        str(tmp_path / "state.db"), enabled=True
    )
    svc.lifecycle = SimpleNamespace(
        get_by_session=lambda _: {
            "workspace_id": "ws",
            "local_path": str(tmp_path),
        }
    )
    svc.ensure_workspace_path_safe = lambda p: p
    grant = svc.workflow_integration_policies.enroll(
        campaign_id="focused-test",
        dataset_id="case-01",
        dataset_digest="d" * 64,
        workspace_id="ws",
        source_path=path,
        source_digest=document.storage_digest,
        input_files={
            "brief.md": hashlib.sha256((tmp_path / "brief.md").read_bytes()).hexdigest()
        },
        output_root="outputs/attempt",
        allowed_tools=[],
        approval_mode="auto",
    )
    generate = AsyncMock(return_value="Actual test model response")
    monkeypatch.setattr(router, "generate_workflow_response", generate)
    request = SimpleNamespace(
        headers={}, app=SimpleNamespace(state=SimpleNamespace(gateway_service=None))
    )
    body = WorkflowSourceRunRequest(
        session_id="session",
        path=path,
        expected_storage_digest=document.storage_digest,
        integration_policy_digest=grant,
    )
    return svc, request, body, generate


@pytest.mark.asyncio
async def test_enrolled_run_records_real_start_and_preserves_public_readiness(
    prepared, tmp_path
):
    svc, request, body, generate = prepared
    result = await router.run_workflow_source_endpoint(body, request, svc)
    record = json.loads((tmp_path / result.run_log_path).read_text())
    assert result.status == "completed"
    assert record["run_id"] == result.run_id
    assert (
        record["execution_context"]["integration_policy_digest"]
        == body.integration_policy_digest
    )
    assert record["execution_context"]["actor"] == "integration_test:focused-test"
    assert record["required_step_ids"] == ["report"]
    assert [
        (e["run_id"], e["kind"]) for e in record["events"] if e["kind"] == "run_started"
    ] == [(result.run_id, "run_started")]
    assert record["events"][-1]["required_steps_completed"] == ["report"]
    assert (
        tmp_path / "outputs/attempt/report.txt"
    ).read_text() == "Actual test model response"
    generate.assert_awaited_once()
    svc.engineering_workflow_templates.readiness.assert_not_called()
    with pytest.raises(HTTPException) as blocked:
        await router.run_workflow_source_endpoint(
            body.model_copy(update={"integration_policy_digest": None}), request, svc
        )
    assert blocked.value.status_code == 409
    assert blocked.value.detail["code"] == "workflow_template_setup_required"
    generate.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mutation", ["revoked", "disabled", "changed_input", "wrong_source"]
)
async def test_invalid_grants_never_start_a_run(prepared, tmp_path, mutation):
    svc, request, body, generate = prepared
    policies = svc.workflow_integration_policies
    if mutation == "revoked":
        policies.revoke(body.integration_policy_digest)
    elif mutation == "disabled":
        policies.enabled = False
    elif mutation == "changed_input":
        (tmp_path / "brief.md").write_bytes(b"Changed after enrollment")
    else:
        body = body.model_copy(update={"path": "workflows/other.workflow.wflow"})
    with pytest.raises(HTTPException) as error:
        await router.run_workflow_source_endpoint(body, request, svc)
    assert error.value.status_code == 422
    assert error.value.detail["code"].startswith("workflow_integration_")
    generate.assert_not_awaited()
    assert not (tmp_path / "runs").exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("handoff", [False, True])
async def test_v2_approval_routes_continue_and_return_full_execution(tmp_path, handoff):
    from packages.workspace_service.tests.test_workflow_approval_execution import (
        setup_case,
    )

    case = await setup_case(tmp_path, handoff=handoff)
    svc = case.services
    svc.lifecycle = SimpleNamespace(
        get_by_session=lambda _: {
            "workspace_id": "ws",
            "local_path": str(tmp_path),
        }
    )
    svc.ensure_workspace_path_safe = lambda p: p
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(gateway_service=None))
    )
    approval = await router.decide_workflow_approval_checkpoint_endpoint(
        case.checkpoint.run_id,
        case.checkpoint.checkpoint_id,
        WorkflowApprovalDecisionRequest(
            session_id="session",
            subject_digest=case.checkpoint.subject_digest,
            decision="approved",
            auto=True,
            request_id="decision-01",
        ),
        request,
        svc,
    )
    assert approval.actor == "integration_test:campaign"
    from unittest.mock import patch

    body = WorkflowApprovalResumeRequest(
        session_id="session",
        checkpoint_id=case.checkpoint.checkpoint_id,
        subject_digest=case.checkpoint.subject_digest,
        request_id="resume-01",
    )
    with patch.object(router, "generate_workflow_response", case.generate):
        first = await router.resume_workflow_approval_checkpoint_endpoint(
            case.checkpoint.run_id,
            body,
            request,
            svc,
        )
        replay = await router.resume_workflow_approval_checkpoint_endpoint(
            case.checkpoint.run_id,
            body,
            request,
            svc,
        )
    assert first.state == "consumed"
    assert first.execution_result["status"] == "completed"
    assert first.execution_result["run_id"] == case.checkpoint.run_id
    assert [s["task_id"] for s in first.execution_result["steps"]] == [
        "package",
        "approve",
        "after",
    ]
    assert len(case.calls) == 2
    assert replay.model_dump(mode="json") == first.model_dump(mode="json")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mutation", ["revoked", "expired", "manual", "input", "artifact", "workspace"]
)
async def test_auto_approval_api_rechecks_current_authority_before_handoff(
    tmp_path, monkeypatch, mutation
):
    import time
    from packages.workspace_service.tests.test_workflow_approval_execution import (
        setup_case,
    )

    expiry = int(time.time()) + 60
    case = await setup_case(
        tmp_path,
        handoff=True,
        mode="manual" if mutation == "manual" else "auto",
        expires_at=expiry if mutation == "expired" else None,
    )
    svc = case.services
    svc.lifecycle = SimpleNamespace(
        get_by_session=lambda _: {
            "workspace_id": "foreign" if mutation == "workspace" else "ws",
            "local_path": str(tmp_path),
        }
    )
    svc.ensure_workspace_path_safe = lambda p: p
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(gateway_service=None))
    )
    if mutation == "revoked":
        svc.workflow_integration_policies.revoke(
            case.context["integration_policy_digest"]
        )
    elif mutation == "expired":
        monkeypatch.setattr(
            "workspace_service.workflow_integration_policy.time.time", lambda: expiry
        )
    elif mutation in {"input", "artifact"}:
        relative = "brief.md" if mutation == "input" else "outputs/attempt/package.json"
        (tmp_path / relative).write_bytes(b"Changed after the recorded checkpoint")
    body = WorkflowApprovalDecisionRequest(
        session_id="session",
        subject_digest=case.checkpoint.subject_digest,
        decision="approved",
        auto=True,
        request_id="denied-auto-request",
    )
    with pytest.raises(HTTPException) as denied:
        await router.decide_workflow_approval_checkpoint_endpoint(
            case.checkpoint.run_id, case.checkpoint.checkpoint_id, body, request, svc
        )
    assert denied.value.status_code in {404, 409, 422}
    stored = svc.workflow_external_actions.lookup(case.checkpoint.checkpoint_id)
    assert stored.state == "pending"
    assert stored.external_action is None
    assert len(case.calls) == 1
    assert not (tmp_path / "outputs/attempt/receipt.json").exists()
    assert not (tmp_path / "outputs/attempt/after.txt").exists()


@pytest.mark.asyncio
async def test_manual_changes_requested_api_prevents_test_handoff(tmp_path):
    from packages.workspace_service.tests.test_workflow_approval_execution import (
        setup_case,
    )

    case = await setup_case(tmp_path, handoff=True)
    svc = case.services
    svc.lifecycle = SimpleNamespace(
        get_by_session=lambda _: {
            "workspace_id": "ws",
            "local_path": str(tmp_path),
        }
    )
    svc.ensure_workspace_path_safe = lambda p: p
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(gateway_service=None))
    )
    decision = await router.decide_workflow_approval_checkpoint_endpoint(
        case.checkpoint.run_id,
        case.checkpoint.checkpoint_id,
        WorkflowApprovalDecisionRequest(
            session_id="session",
            subject_digest=case.checkpoint.subject_digest,
            decision="changes_requested",
            auto=False,
            reason="Revise the package before release",
            request_id="manual-revision",
        ),
        request,
        svc,
    )
    assert decision.actor == "local_workspace_user"
    assert decision.state == "changes_requested"
    with pytest.raises(HTTPException) as denied:
        await router.resume_workflow_approval_checkpoint_endpoint(
            case.checkpoint.run_id,
            WorkflowApprovalResumeRequest(
                session_id="session",
                checkpoint_id=case.checkpoint.checkpoint_id,
                subject_digest=case.checkpoint.subject_digest,
                request_id="declined-resume",
            ),
            request,
            svc,
        )
    assert denied.value.status_code in {409, 422}
    assert len(case.calls) == 1
    assert not (tmp_path / "outputs/attempt/receipt.json").exists()
