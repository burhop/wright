"""HTTP proof of the installed setup route, with discovery metadata only."""

import json
import re
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from api.main import app
from api.routers.workspace import get_workspace_service
from apps.api.tests.test_engineering_workflow_template_api import _Service
from workspace_service import handle_setup_resources as resources
from workspace_service.workflow_mcp_execution import WorkflowMcpRuntime

PREFIX = "/api/workspace/workflow-source-templates/replacement-drawer-handle"


@pytest.mark.parametrize("mount", ["native", "windows", "different"])
def test_handle_setup_http_proposes_inspectable_revision_then_explicit_cas(
    sync_client, tmp_path, monkeypatch, mount
):
    monkeypatch.setattr(
        app.state,
        "gateway_service",
        SimpleNamespace(
            open_session=lambda **_: None,
            initialize_session=lambda *_, **__: None,
            close_session=AsyncMock(),
        ),
        raising=False,
    )
    service = _Service(tmp_path)
    service.executor = service.workflow_sources._executor
    tools = [
        {
            "server_id": "fixture-" + role,
            "name": "fixture-" + role + "__" + value["tool_name"],
            **value,
        }
        for role, value in resources.contract()["tools"].items()
    ]
    monkeypatch.setattr(WorkflowMcpRuntime, "available", lambda _: tools)
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        detail = sync_client.get(PREFIX).json()["template"]
        created = sync_client.post(
            PREFIX + "/instances",
            json={
                "session_id": "session-1",
                "template_version": detail["version"],
                "expected_source_digest": detail["source_digest"],
                "workflow_path": "workflows/handle.workflow.wflow",
                "request_id": "http-setup-0001",
            },
        )
        assert created.status_code == 201, created.text
        document = created.json()
        scope = {
            "session_id": "session-1",
            "path": document["path"],
            "expected_storage_revision": document["storage_revision"],
            "expected_storage_digest": document["storage_digest"],
        }
        options = sync_client.post(PREFIX + "/setup/options", json=scope)
        assert options.status_code == 200, options.text
        assert options.headers["cache-control"] == "no-store"
        assert options.json()["workspace_id"] == "workspace-1"
        profile = json.loads(
            (
                resources.PACKAGE
                / "process_validation/profiles/printed-replacement-part-02.json"
            ).read_bytes()
        )
        profiles = {}
        for role in ("machine", "process", "filament"):
            value = {
                item["selector"].removeprefix("/"): item["constraint"]["expected"]
                for item in profile["checks"]
                if item["subject_role"] == role + "_profile"
                and item["reader"] == "structured"
            }
            if role == "process":
                value["tree_support_wall_count"] = "-1"
                (tmp_path / "process_original.json").write_text(json.dumps(value))
                profiles["process_original"] = {"path": "process_original.json"}
                role = "process_orca"
                value["tree_support_wall_count"] = "0"
            (tmp_path / (role + ".json")).write_text(json.dumps(value))
            profiles[role] = {"path": role + ".json"}
        body = {
            **scope,
            "tools": {
                role: {key: tool[key] for key in ("server_id", "name", "schema_digest")}
                for role, tool in zip(resources.contract()["tools"], tools)
            },
            "profiles": profiles,
            "workspace_mount": {
                "native": str(tmp_path),
                "windows": r"C:\wright\workspace",
                "different": "/different-workspace",
            }[mount],
            "selected_orientation": "side",
        }
        proposed = sync_client.post(PREFIX + "/setup/proposals", json=body)
        if mount != "native" or not re.fullmatch(r"/[A-Za-z0-9_/-]+", str(tmp_path)):
            # This installed recipe has only qualified a shared POSIX mount.
            # Native Windows must diagnose it before staging or accepting source.
            assert proposed.status_code == 400, proposed.text
            assert proposed.json()["error_code"] == "handle_setup_invalid"
            assert "exact managed POSIX workspace path" in proposed.json()["message"]
            assert (tmp_path / document["path"]).read_text() == document["source"]
            assert not (tmp_path / ".wright/handle-setup").exists()
            assert not (tmp_path / ".wright/workflow-runs").exists()
            assert not list(tmp_path.rglob("*.stl"))
            return
        assert proposed.status_code == 201, proposed.text
        proposal = proposed.json()
        assert proposal["expected_storage_digest"] == document["storage_digest"]
        assert proposal["source_digest"] != document["storage_digest"]
        assert (tmp_path / document["path"]).read_text() == document["source"]
        assert proposal["summary"]["selected_orientation"] == "side"
        accepted = sync_client.post(
            PREFIX + "/setup/accept",
            json={
                **scope,
                "proposal_id": proposal["proposal_id"],
                "proposal_digest": proposal["proposal_digest"],
            },
        )
        assert accepted.status_code == 200, accepted.text
        assert accepted.json()["source"] == proposal["source"]
        assert accepted.json()["storage_digest"] == proposal["source_digest"]
        assert accepted.json()["storage_revision"] == document["storage_revision"] + 1
        stale = sync_client.post(PREFIX + "/setup/options", json=scope)
        assert stale.status_code == 409, stale.text
        assert not (tmp_path / ".wright/workflow-runs").exists()
        assert not list(tmp_path.rglob("*.stl"))
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)


def test_handle_setup_http_rejects_unknown_code_and_unknown_session(
    sync_client, tmp_path, monkeypatch
):
    monkeypatch.setattr(
        app.state,
        "gateway_service",
        SimpleNamespace(
            open_session=lambda **_: None,
            initialize_session=lambda *_, **__: None,
            close_session=AsyncMock(),
        ),
        raising=False,
    )
    service = _Service(tmp_path)
    service.executor = service.workflow_sources._executor
    monkeypatch.setattr(WorkflowMcpRuntime, "available", lambda _: [])
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        scope = {
            "session_id": "unknown",
            "path": "workflows/handle.workflow.wflow",
            "expected_storage_revision": 1,
            "expected_storage_digest": "a" * 64,
        }
        assert (
            sync_client.post(PREFIX + "/setup/options", json=scope).status_code == 404
        )
        assert (
            sync_client.post(
                PREFIX + "/setup/options", json={**scope, "code": "arbitrary()"}
            ).status_code
            == 422
        )
        assert not (tmp_path / ".wright/handle-setup").exists()
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)
