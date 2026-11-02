from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from api.main import app
from api.routers.workspace import get_workspace_service
from workspace_service.engineering_workflow_template_service import (
    EngineeringWorkflowTemplateService,
)
from workspace_service.executor import BoundedExecutor
from workspace_service.workflow_sources import WorkspaceWorkflowSourceUseCases


class _Service:
    def __init__(self, root):
        from apps.api.tests.process_interface_fixtures import bind_process_interfaces

        bind_process_interfaces(self, root, "workspace-1")
        self.executor = BoundedExecutor()
        self.workflow_sources = WorkspaceWorkflowSourceUseCases(self.executor)
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
    assert len(templates) == 11
    assert templates[-1]["template_id"] == "replacement-drawer-handle"
    assert templates[-1]["version"] == "1.0.3"
    assert templates[-1]["exploration"]["outcome_status"] == "recorded"
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


def test_handle_starter_installs_supplied_inputs_and_blocks_unconfigured_execution(
    sync_client, tmp_path
):
    service = _Service(tmp_path)
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        prefix = "/api/workspace/workflow-source-templates/replacement-drawer-handle"
        detail = sync_client.get(prefix).json()["template"]
        created = sync_client.post(
            prefix + "/instances",
            json={
                "session_id": "session-1",
                "template_version": detail["version"],
                "expected_source_digest": detail["source_digest"],
                "workflow_path": "workflows/handle.workflow.wflow",
                "request_id": "handle-request-0001",
            },
        )
        assert created.status_code == 201, created.text
        identity = created.json()["workflow_id"].removeprefix("workflow.")
        assert (tmp_path / "inputs" / identity / "concept.svg").is_file()
        assert (tmp_path / "inputs" / identity / "validation-profile.json").is_file()
        assert not (tmp_path / ".wright" / "workflow-runs").exists()
        blocked = sync_client.post(
            "/api/workspace/workflow-sources/run",
            json={
                "session_id": "session-1",
                "path": "workflows/handle.workflow.wflow",
                "expected_storage_digest": created.json()["storage_digest"],
            },
        )
        assert blocked.status_code == 409
        assert blocked.json()["error_code"] == "workflow_template_setup_required"
        assert detail["exploration"]["outcome_status"] == "recorded"
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)


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


def test_recorded_handle_preview_is_versioned_and_does_not_grant_readiness(
    sync_client, tmp_path
):
    service = _Service(tmp_path)
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        prefix = "/api/workspace/workflow-source-templates/replacement-drawer-handle"
        current = sync_client.get(prefix, params={"version": "1.0.3"})
        preview = sync_client.get(prefix + "/preview", params={"version": "1.0.3"})
        old = sync_client.get(prefix + "/preview", params={"version": "1.0.0"})
        readiness = sync_client.post(
            prefix + "/readiness",
            json={"session_id": "session-1", "template_version": "1.0.3"},
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)
    assert current.status_code == 200
    assert (
        current.json()["template"]["exploration"]["recorded_result"]["run_id"]
        == "de60e23084294148a3a8129bf2bcb1b8"
    )
    assert preview.status_code == 200
    assert preview.headers["cache-control"].endswith("immutable")
    assert b"SUPPLIED SKETCH" in preview.content and b"RECORDED MESH" in preview.content
    assert old.status_code == 404
    assert old.json()["error_code"] == "template_not_found"
    assert readiness.status_code == 200
    observed = readiness.json()
    assert observed["state"] == "setup_required"
    assert not any(
        observed[key]
        for key in ("configured", "qualified", "available", "verified_run")
    )
    assert not (tmp_path / ".wright/workflow-runs").exists()


@pytest.mark.parametrize("revised", [False, True])
def test_saved_handle_100_origin_remains_readable_with_103_catalog(
    sync_client, tmp_path, revised
):
    service = _Service(tmp_path)
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        prefix = "/api/workspace/workflow-source-templates/replacement-drawer-handle"
        detail = sync_client.get(prefix).json()["template"]
        path = "workflows/old-handle.workflow.wflow"
        created = sync_client.post(
            prefix + "/instances",
            json={
                "session_id": "session-1",
                "template_version": "1.0.3",
                "expected_source_digest": detail["source_digest"],
                "workflow_path": path,
                "request_id": "old-handle-fixture-0001",
            },
        )
        assert created.status_code == 201
        origin_path = (
            tmp_path / ".wright/workflow-sources/old-handle/template-origin.json"
        )
        origin = json.loads(origin_path.read_text())
        origin["template_version"] = "1.0.0"
        origin_path.write_text(json.dumps(origin))
        before = sync_client.get(
            "/api/workspace/workflow-sources",
            params={"session_id": "session-1", "path": path},
        )
        assert before.status_code == 200
        accepted = before.json()
        if revised:
            changed = sync_client.put(
                "/api/workspace/workflow-sources",
                json={
                    "session_id": "session-1",
                    "path": path,
                    "expected_storage_revision": accepted["storage_revision"],
                    "expected_storage_digest": accepted["storage_digest"],
                    "semantic_change_validated": True,
                    "source": accepted["source"].replace(
                        'name: "Replace a broken drawer handle"',
                        'name: "Saved revised handle"',
                        1,
                    ),
                },
            )
            assert changed.status_code == 200, changed.text
            accepted = changed.json()
        result = sync_client.get(
            "/api/workspace/workflow-sources/readiness",
            params={"session_id": "session-1", "path": path},
        )
        after = sync_client.get(
            "/api/workspace/workflow-sources",
            params={"session_id": "session-1", "path": path},
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)
    assert result.status_code == 200
    observed = result.json()
    assert observed["state"] == ("revised" if revised else "unavailable")
    if revised:
        assert observed["template_version"] == "1.0.0"
        assert all(
            observed[key] is None
            for key in ("configured", "qualified", "available", "verified_run")
        )
    else:
        assert "not found" in observed["message"]
    assert after.status_code == 200
    assert after.json()["source"] == accepted["source"]
    assert after.json()["storage_digest"] == accepted["storage_digest"]
    assert json.loads(origin_path.read_text()) == origin
    assert not (tmp_path / ".wright/workflow-runs").exists()
