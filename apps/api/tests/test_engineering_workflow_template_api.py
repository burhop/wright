from __future__ import annotations

from types import SimpleNamespace

from api.main import app
from api.routers.workspace import get_workspace_service
from workspace_service.engineering_workflow_template_service import (
    EngineeringWorkflowTemplateService,
)
from workspace_service.executor import BoundedExecutor
from workspace_service.workflow_sources import WorkspaceWorkflowSourceUseCases


class _Service:
    def __init__(self, root):
        self.workflow_sources = WorkspaceWorkflowSourceUseCases(BoundedExecutor())
        self.engineering_workflow_templates = EngineeringWorkflowTemplateService(
            self.workflow_sources
        )
        self.lifecycle = SimpleNamespace(
            get_by_session=lambda session_id: (
                {
                    "workspace_id": "workspace-1",
                    "session_id": session_id,
                    "local_path": str(root),
                }
                if session_id == "session-1"
                else None
            )
        )

    def ensure_workspace_path_safe(self, local_path: str) -> str:
        return local_path


def test_template_list_detail_readiness_and_instance_contract(sync_client, tmp_path):
    service = _Service(tmp_path)
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        listing = sync_client.get("/api/workspace/workflow-source-templates")
        templates = listing.json()["templates"]
        selected = templates[0]
        detail = sync_client.get(
            f"/api/workspace/workflow-source-templates/{selected['template_id']}",
            params={"version": selected["version"]},
        )
        preview = sync_client.get(
            f"/api/workspace/workflow-source-templates/{selected['template_id']}/preview",
            params={"version": selected["version"]},
        )
        readiness = sync_client.post(
            f"/api/workspace/workflow-source-templates/{selected['template_id']}/readiness",
            json={"session_id": "session-1", "template_version": selected["version"]},
        )
        body = {
            "session_id": "session-1",
            "template_version": selected["version"],
            "expected_source_digest": selected["source_digest"],
            "workflow_path": "workflows/demo-replacement.workflow.wflow",
            "request_id": "template-request-0001",
        }
        created = sync_client.post(
            f"/api/workspace/workflow-source-templates/{selected['template_id']}/instances",
            json=body,
        )
        source_readiness = sync_client.get(
            "/api/workspace/workflow-sources/readiness",
            params={"session_id": "session-1", "path": body["workflow_path"]},
        )
        retry = sync_client.post(
            f"/api/workspace/workflow-source-templates/{selected['template_id']}/instances",
            json=body,
        )
        blocked_run = sync_client.post(
            "/api/workspace/workflow-sources/run",
            json={
                "session_id": "session-1",
                "path": body["workflow_path"],
                "expected_storage_digest": created.json()["storage_digest"],
            },
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)

    assert listing.status_code == 200
    assert listing.json()["catalog_version"] == "1.0.0"
    assert len(templates) == 10
    assert detail.status_code == 200
    assert detail.json()["template"]["source"].startswith("# Built-in")
    assert preview.status_code == 200
    assert preview.headers["content-type"].startswith("image/svg+xml")
    assert preview.headers["cache-control"].endswith("immutable")
    assert preview.content.startswith(b"<svg")
    assert readiness.status_code == 200
    assert readiness.json()["state"] == "setup_required"
    assert created.status_code == 201
    assert source_readiness.status_code == 200
    assert source_readiness.json()["state"] == "setup_required"
    assert source_readiness.json()["template_id"] == selected["template_id"]
    assert created.headers["cache-control"] == "no-store"
    assert created.json()["layout_status"] == "current"
    assert created.json()["workflow_id"] == created.json()["layout"]["workflowId"]
    input_root = (
        tmp_path / "inputs" / created.json()["workflow_id"].removeprefix("workflow.")
    )
    assert (input_root / "replacement-knob-source.svg").is_file()
    assert (input_root / "rights.json").is_file()
    assert retry.status_code == 201
    assert retry.json() == created.json()
    assert blocked_run.status_code == 409
    assert blocked_run.json()["error_code"] == "workflow_template_setup_required"
    assert "Bambu P1S" in blocked_run.json()["details"]["correction"]


def test_template_api_rejects_stale_digest_collision_and_unknown_workspace(
    sync_client, tmp_path
):
    service = _Service(tmp_path)
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        selected = sync_client.get("/api/workspace/workflow-source-templates").json()[
            "templates"
        ][0]
        base = {
            "session_id": "session-1",
            "template_version": selected["version"],
            "expected_source_digest": selected["source_digest"],
            "workflow_path": "workflows/collision.workflow.wflow",
            "request_id": "template-request-0001",
        }
        first = sync_client.post(
            f"/api/workspace/workflow-source-templates/{selected['template_id']}/instances",
            json=base,
        )
        collision = sync_client.post(
            f"/api/workspace/workflow-source-templates/{selected['template_id']}/instances",
            json={**base, "request_id": "template-request-0002"},
        )
        stale = sync_client.post(
            f"/api/workspace/workflow-source-templates/{selected['template_id']}/instances",
            json={
                **base,
                "workflow_path": "workflows/stale.workflow.wflow",
                "request_id": "template-request-0003",
                "expected_source_digest": "0" * 64,
            },
        )
        unknown = sync_client.post(
            f"/api/workspace/workflow-source-templates/{selected['template_id']}/readiness",
            json={"session_id": "missing", "template_version": selected["version"]},
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)

    assert first.status_code == 201
    assert collision.status_code == 409
    assert collision.json()["error_code"] == "workflow_source_exists"
    assert stale.status_code == 409
    assert stale.json()["error_code"] == "template_digest_mismatch"
    assert unknown.status_code == 404
