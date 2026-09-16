from __future__ import annotations

from types import SimpleNamespace
import hashlib

from api.main import app
from api.routers.workspace import get_workspace_service
from data_vault import WorkflowContinuationRepository
from workspace_service.workflow_external_actions import WorkflowExternalActionService


def subject():
    return {
        "definition_digest": "a" * 64,
        "input_digests": ["b" * 64],
        "artifact_digests": ["c" * 64],
        "binding": {"server": "slicer", "tool": "slice", "schema": "d" * 64},
        "destination": {"kind": "printer", "id": "bambu-p1s-01"},
        "settings": {"material": "PLA", "profile": "0.20-standard"},
        "action": {"kind": "printer_transfer", "package": "c" * 64},
    }


class _Service:
    def __init__(self, db_path):
        self.workflow_external_actions = WorkflowExternalActionService(
            WorkflowContinuationRepository(str(db_path))
        )
        self.lifecycle = SimpleNamespace(
            get_by_session=lambda session_id: (
                {
                    "workspace_id": "workspace-1",
                    "session_id": session_id,
                    "local_path": "D:/workspace",
                }
                if session_id == "session-1"
                else None
            )
        )
        self.source_digest = "a" * 64
        self.artifact_bytes = b"approved artifact"

        async def read_source(workspace_dir, path):
            return SimpleNamespace(storage_digest=self.source_digest)

        async def read_artifact(workspace_dir, path):
            return self.artifact_bytes

        self.workflow_sources = SimpleNamespace(read=read_source)
        self.files = SimpleNamespace(
            read_reference=read_artifact, read_capture_file=read_artifact
        )

    def ensure_workspace_path_safe(self, local_path: str):
        return local_path

    def require_safe_workspace(self, workspace_id: str):
        if workspace_id != "workspace-1":
            raise AssertionError("unexpected workspace")
        return {"workspace_id": workspace_id, "local_path": "D:/workspace"}


def test_exact_approval_decision_resume_and_reconciliation_api(sync_client, tmp_path):
    service = _Service(tmp_path / "state.db")
    pending = service.workflow_external_actions.request(
        workspace_id="workspace-1",
        workflow_id="workflow-1",
        run_id="run-1",
        step_id="transfer",
        action_kind="printer_transfer",
        subject=subject(),
        continuation={"next_step": "transfer"},
    )
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        detail = sync_client.get(
            f"/api/workspace/workflow-runs/run-1/approvals/{pending.checkpoint_id}",
            params={"session_id": "session-1"},
        )
        approved = sync_client.post(
            f"/api/workspace/workflow-runs/run-1/approvals/{pending.checkpoint_id}/decisions",
            json={
                "session_id": "session-1",
                "subject_digest": pending.subject_digest,
                "decision": "approved",
                "reason": "Package and destination checked",
                "request_id": "decision-request-1",
            },
        )
        resumed = sync_client.post(
            "/api/workspace/workflow-runs/run-1/resume",
            json={
                "session_id": "session-1",
                "checkpoint_id": pending.checkpoint_id,
                "subject_digest": pending.subject_digest,
                "request_id": "resume-request-01",
            },
        )
        resumed_retry = sync_client.post(
            "/api/workspace/workflow-runs/run-1/resume",
            json={
                "session_id": "session-1",
                "checkpoint_id": pending.checkpoint_id,
                "subject_digest": pending.subject_digest,
                "request_id": "resume-request-01",
            },
        )
        reconciled = sync_client.post(
            f"/api/workspace/workflow-runs/run-1/approvals/{pending.checkpoint_id}/reconcile",
            json={
                "session_id": "session-1",
                "subject_digest": pending.subject_digest,
                "outcome": "outcome_unknown",
                "evidence": {"reason": "connection closed after dispatch boundary"},
            },
        )
        replay = sync_client.post(
            "/api/workspace/workflow-runs/run-1/resume",
            json={
                "session_id": "session-1",
                "checkpoint_id": pending.checkpoint_id,
                "subject_digest": pending.subject_digest,
                "request_id": "resume-request-02",
            },
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)

    assert detail.status_code == 200
    assert detail.json()["state"] == "pending"
    assert approved.status_code == 200
    assert approved.json()["state"] == "approved"
    assert resumed.status_code == 200
    assert resumed.json()["state"] == "consumed"
    assert resumed.json()["external_action"]["outcome"] == "not_dispatched"
    assert resumed_retry.status_code == 200
    assert resumed_retry.json() == resumed.json()
    assert reconciled.status_code == 200
    assert reconciled.json()["external_action"]["outcome"] == "outcome_unknown"
    assert replay.status_code == 422


def test_approval_api_rejects_wrong_run_and_stale_subject(sync_client, tmp_path):
    service = _Service(tmp_path / "state.db")
    pending = service.workflow_external_actions.request(
        workspace_id="workspace-1",
        workflow_id="workflow-1",
        run_id="run-1",
        step_id="transfer",
        action_kind="printer_transfer",
        subject=subject(),
        continuation={},
    )
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        wrong_run = sync_client.get(
            f"/api/workspace/workflow-runs/run-2/approvals/{pending.checkpoint_id}",
            params={"session_id": "session-1"},
        )
        stale = sync_client.post(
            f"/api/workspace/workflow-runs/run-1/approvals/{pending.checkpoint_id}/decisions",
            json={
                "session_id": "session-1",
                "subject_digest": "0" * 64,
                "decision": "approved",
                "request_id": "decision-request-2",
            },
        )
        foreign = sync_client.get(
            f"/api/workspace/workflow-runs/run-1/approvals/{pending.checkpoint_id}",
            params={"session_id": "foreign"},
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)

    assert wrong_run.status_code == 404
    assert stale.status_code == 409
    assert foreign.status_code == 404
    assert (
        service.workflow_external_actions.lookup(pending.checkpoint_id).state
        == "pending"
    )


def test_resume_recomputes_workspace_artifact_digest_server_side(sync_client, tmp_path):
    service = _Service(tmp_path / "state.db")
    approved_subject = subject()
    approved_subject["artifact_digests"] = [
        hashlib.sha256(service.artifact_bytes).hexdigest()
    ]
    pending = service.workflow_external_actions.request(
        workspace_id="workspace-1",
        workflow_id="workflows/example.workflow.wflow",
        run_id="run-1",
        step_id="transfer",
        action_kind="printer_transfer",
        subject=approved_subject,
        continuation={
            "workflow_path": "workflows/example.workflow.wflow",
            "artifact_files": [
                {
                    "path": "outputs/package.3mf",
                    "sha256": approved_subject["artifact_digests"][0],
                }
            ],
        },
    )
    service.workflow_external_actions.decide(
        pending.checkpoint_id,
        workspace_id="workspace-1",
        expected_subject_digest=pending.subject_digest,
        actor="local_workspace_user",
        approved=True,
    )
    service.artifact_bytes = b"changed artifact"
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        resumed = sync_client.post(
            "/api/workspace/workflow-runs/run-1/resume",
            json={
                "session_id": "session-1",
                "checkpoint_id": pending.checkpoint_id,
                "subject_digest": pending.subject_digest,
                "request_id": "resume-request-stale",
            },
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)

    assert resumed.status_code == 409
    assert resumed.json()["error_code"] == "approval_stale"
    assert (
        service.workflow_external_actions.lookup(pending.checkpoint_id).state == "stale"
    )
