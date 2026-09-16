from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

from api.main import app
from api.routers.workspace import get_workspace_service


class _Service:
    def __init__(self, root):
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
        self.workflow_demo_captures = SimpleNamespace(
            create=AsyncMock(
                return_value={
                    "path": "captures/run-1.demo-capture.zip",
                    "size_bytes": 1024,
                    "sha256": "a" * 64,
                    "manifest_digest": "b" * 64,
                    "artifact_count": 1,
                    "published": False,
                }
            )
        )

    def ensure_workspace_path_safe(self, local_path: str) -> str:
        return local_path


def test_capture_endpoint_is_workspace_scoped_and_never_claims_publish(
    sync_client, tmp_path
):
    service = _Service(tmp_path)
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        response = sync_client.post(
            "/api/workspace/workflow-runs/run-1/capture",
            json={
                "session_id": "session-1",
                "run_log_path": "runs/example/run.json",
                "artifact_ids": ["result-1"],
                "caption": "Verified local engineering result.",
            },
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)

    assert response.status_code == 201
    assert response.json()["published"] is False
    service.workflow_demo_captures.create.assert_awaited_once_with(
        workspace_dir=str(tmp_path),
        run_log_path="runs/example/run.json",
        expected_run_id="run-1",
        artifact_ids=["result-1"],
        caption="Verified local engineering result.",
    )


def test_capture_endpoint_rejects_unknown_session_before_service_call(
    sync_client, tmp_path
):
    service = _Service(tmp_path)
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        response = sync_client.post(
            "/api/workspace/workflow-runs/run-1/capture",
            json={
                "session_id": "foreign",
                "run_log_path": "runs/example/run.json",
                "artifact_ids": ["result-1"],
                "caption": "Verified local engineering result.",
            },
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)

    assert response.status_code == 404
    service.workflow_demo_captures.create.assert_not_awaited()
