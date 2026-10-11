import asyncio
from types import SimpleNamespace
import pytest
from api.main import app
from api.routers.workspace import get_workspace_service
from workspace_service.executor import BoundedExecutor
from workspace_service.workflow_sources import (
    WorkspaceWorkflowSourceStore,
    WorkspaceWorkflowSourceUseCases,
)


@pytest.fixture
def copy_case(tmp_path):
    executor = BoundedExecutor(max_workers=1)
    service = SimpleNamespace(ensure_workspace_path_safe=lambda path: path)
    service.lifecycle = SimpleNamespace(
        get_by_session=lambda session: (
            {
                "workspace_id": "workspace-copy",
                "local_path": str(tmp_path),
            }
            if session == "copy-session"
            else None
        )
    )
    service.workflow_sources = WorkspaceWorkflowSourceUseCases(executor)
    saved = WorkspaceWorkflowSourceStore(str(tmp_path)).create(
        "workflows/original.workflow.wflow", "workflow legacy\nend\n"
    )
    app.dependency_overrides[get_workspace_service] = lambda: service
    yield saved
    app.dependency_overrides.pop(get_workspace_service, None)
    asyncio.run(executor.close())


def test_scoped_copy_preserves_legacy_source_and_cas_with_no_overwrite(
    sync_client, copy_case
):
    body = {
        "session_id": "copy-session",
        "source_path": copy_case.path,
        "destination_path": "workflows/copy.workflow.wflow",
        "expected_storage_digest": copy_case.storage_digest,
    }
    response = sync_client.post("/api/workspace/workflow-sources/copy", json=body)
    assert response.status_code == 201, response.text
    result = response.json()
    assert result["workspace_id"] == "workspace-copy"
    assert result["metadata_authority"] == "wright_host"
    assert result["path"] == body["destination_path"]
    assert result["source"] == copy_case.source
    assert result["storage_revision"] == result["definition_revision"] == 1
    assert response.headers["cache-control"] == "no-store"
    assert (
        sync_client.post("/api/workspace/workflow-sources/copy", json=body).status_code
        == 409
    )
    assert (
        sync_client.post(
            "/api/workspace/workflow-sources/copy",
            json={
                **body,
                "destination_path": "workflows/stale.workflow.wflow",
                "expected_storage_digest": "0" * 64,
            },
        ).status_code
        == 409
    )
    assert (
        sync_client.post(
            "/api/workspace/workflow-sources/copy", json={**body, "session_id": "other"}
        ).status_code
        == 404
    )
    assert (
        sync_client.post(
            "/api/workspace/workflow-sources/copy",
            json={**body, "destination_path": "../outside.workflow.wflow"},
        ).status_code
        == 400
    )
