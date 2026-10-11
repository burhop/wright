import asyncio
import base64
import hashlib
from copy import deepcopy
from types import SimpleNamespace

import pytest

from api.main import app
from api.routers.workspace import get_workspace_service
from workspace_service.executor import BoundedExecutor
from workspace_service.workflow_bundles import WorkflowBundleService
from workspace_service.workflow_sources import WorkspaceWorkflowSourceStore
from packages.workspace_service.tests.test_workflow_bundles import source


@pytest.fixture
def transfer_case(tmp_path, monkeypatch):
    origin, target = tmp_path / "origin", tmp_path / "target"
    origin.mkdir()
    target.mkdir()
    executor = BoundedExecutor(max_workers=1)
    service = SimpleNamespace(
        executor=executor, ensure_workspace_path_safe=lambda path: path
    )
    service.lifecycle = SimpleNamespace(
        get_by_session=lambda session: (
            {
                "workspace_id": session,
                "local_path": str(origin if session == "origin" else target),
            }
            if session in {"origin", "target"}
            else None
        )
    )
    service.workflow_bundles = WorkflowBundleService(service)
    monkeypatch.setattr(app.state, "gateway_service", None, raising=False)
    app.dependency_overrides[get_workspace_service] = lambda: service
    document = WorkspaceWorkflowSourceStore(origin).create(
        "workflows/design.workflow.wflow", source()
    )
    yield SimpleNamespace(document=document, target=target)
    app.dependency_overrides.pop(get_workspace_service, None)
    asyncio.run(executor.close())


def test_authenticated_scoped_export_inspect_and_import(sync_client, transfer_case):
    response = sync_client.post(
        "/api/workspace/workflow-bundles/export",
        json={
            "session_id": "origin",
            "path": transfer_case.document.path,
            "expected_storage_digest": transfer_case.document.storage_digest,
        },
    )
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    exported = response.json()
    request = {
        "session_id": "target",
        "bundle": exported["bundle"],
        "destination_path": "workflows/imported.workflow.wflow",
    }
    checked = sync_client.post("/api/workspace/workflow-bundles/inspect", json=request)
    assert checked.status_code == 200, checked.text
    assert checked.json()["can_import"] and not checked.json()["can_run"]
    imported = sync_client.post(
        "/api/workspace/workflow-bundles/import",
        json={
            **request,
            "expected_bundle_digest": exported["bundle_digest"],
        },
    )
    assert imported.status_code == 200, imported.text
    assert imported.json()["source"]["source"] == transfer_case.document.source
    assert imported.json()["source"]["workspace_id"] == "target"
    assert imported.json()["source"]["metadata_authority"] == "wright_host"
    denied = sync_client.post(
        "/api/workspace/workflow-bundles/inspect",
        json={**request, "session_id": "other"},
    )
    assert denied.status_code == 404


def test_transport_rejects_extra_authority_and_body_limit(sync_client, transfer_case):
    result = sync_client.post(
        "/api/workspace/workflow-bundles/export",
        json={
            "session_id": "origin",
            "path": transfer_case.document.path,
            "expected_storage_digest": transfer_case.document.storage_digest,
            "approvals": ["grant"],
        },
    )
    assert result.status_code == 422
    oversized = sync_client.post(
        "/api/workspace/workflow-bundles/import",
        content=b" " * 21_000_001,
        headers={"Content-Type": "application/json"},
    )
    assert oversized.status_code == 413
    assert not (transfer_case.target / "workflows").exists()


@pytest.mark.parametrize(
    "failure", ["asset_digest", "source_digest", "duplicate_asset", "unsafe_path"]
)
def test_invalid_bundle_returns_safe_json_422_without_echoing_request(
    sync_client, transfer_case, failure
):
    exported = sync_client.post(
        "/api/workspace/workflow-bundles/export",
        json={
            "session_id": "origin",
            "path": transfer_case.document.path,
            "expected_storage_digest": transfer_case.document.storage_digest,
        },
    ).json()
    bundle = deepcopy(exported["bundle"])
    private_payload = b"Private transfer contents must not appear in errors"
    asset = {
        "path": "references/example.txt",
        "sha256": hashlib.sha256(private_payload).hexdigest(),
        "data_base64": base64.b64encode(private_payload).decode(),
    }
    bundle["mode"] = "bundle"
    bundle["assets"] = [asset]
    if failure == "asset_digest":
        asset["sha256"] = "0" * 64
    elif failure == "source_digest":
        bundle["source_digest"] = "0" * 64
    elif failure == "duplicate_asset":
        bundle["assets"].append(deepcopy(asset))
    else:
        asset["path"] = "../private-secret.txt"
    response = sync_client.post(
        "/api/workspace/workflow-bundles/inspect",
        json={
            "session_id": "target",
            "bundle": bundle,
            "destination_path": "workflows/imported.workflow.wflow",
        },
    )
    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["error_code"] == "VALIDATION_ERROR"
    assert body["details"]["errors"]
    assert bundle["source"] not in response.text
    assert asset["data_base64"] not in response.text
    assert "private-secret" not in response.text
    for error in body["details"]["errors"]:
        assert "input" not in error and "ctx" not in error
    assert not (transfer_case.target / "workflows").exists()
