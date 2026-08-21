from __future__ import annotations

from types import SimpleNamespace

from api.routers import workspace as workspace_router
from core.workflow_runs import WorkflowRun, WorkflowRunState
from workspace_service.workflows import WorkspaceWorkflowStore


def _inspection(run_id: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "run": {
            "run_id": run_id,
            "workspace_id": "workspace-1",
            "session_id": "session-1",
            "workflow_id": "workflow-1",
            "revision": 1,
            "digest": "a" * 64,
            "graph": "Main",
            "generation": 1,
            "state": "succeeded",
            "started_at": "2026-08-20T14:00:00Z",
            "completed_at": "2026-08-20T14:00:01Z",
            "duration_ms": 1000,
            "reason_code": None,
            "trace_id": "trace-safe",
            "latest_sequence": 2,
            "has_outputs": True,
            "has_diagnostic": False,
            "output_truncated": False,
            "output_redaction_count": 0,
        },
        "progress": {
            "phase": "completed",
            "current_step_id": None,
            "completed_steps": 1,
            "total_steps": 1,
            "last_sequence": 2,
            "updated_at": "2026-08-20T14:00:01Z",
        },
        "events": [
            {
                "sequence": 2,
                "kind": "completed",
                "occurred_at": "2026-08-20T14:00:01Z",
                "payload": {"phase": "completed"},
            }
        ],
        "steps": [],
        "final_outputs": [
            {
                "result_id": "output",
                "name": "output",
                "origin": "workflow_output",
                "kind": "structured",
                "value": {"status": "complete"},
                "preview": '{"status":"complete"}',
                "complete": True,
                "truncation_reason": None,
                "original_bytes": 21,
                "retained_bytes": 21,
                "digest": "b" * 64,
                "redaction_count": 0,
                "artifact": None,
            }
        ],
        "diagnostic": None,
        "completeness": {
            "outputs_complete": True,
            "steps_complete": True,
            "events_complete": True,
            "evidence_available": True,
            "reasons": [],
        },
    }


def test_fastapi_start_inspect_reattach_and_historical_review(
    offline_api_client, tmp_path, monkeypatch
):
    workspace_dir = tmp_path / "run-inspector-workspace"
    WorkspaceWorkflowStore(str(workspace_dir)).create("rivet", '{"nodes": []}')
    starts: list[str] = []
    run = WorkflowRun(
        "run-inspector",
        "workspace-1",
        "session-1",
        "workflow-1",
        1,
        1,
        WorkflowRunState.RUNNING,
    )

    class Operations:
        async def start(self, **kwargs):
            starts.append(kwargs["slug"])
            return run

        def inspection(self, **kwargs):
            assert kwargs["after_sequence"] in {0, 2}
            return _inspection(kwargs["run_id"])

        def recent_runs(self, **_kwargs):
            return (_inspection("run-inspector")["run"],)

    record = SimpleNamespace(
        digest="a" * 64,
        graph="Main",
        output_summary={
            "outputs": {"output": {"status": "complete"}},
            "durationMs": 1000,
        },
        output_truncated=False,
    )
    service = SimpleNamespace(
        lifecycle=SimpleNamespace(
            get_by_session=lambda session: (
                {"workspace_id": "workspace-1"} if session == "session-1" else None
            )
        ),
        resolve_workspace_dir=lambda *_args: _async_value(str(workspace_dir)),
        workflow_operations=Operations(),
        workflow_runner=SimpleNamespace(
            result=lambda _run_id: record, manifest=lambda _run_id: None
        ),
    )
    monkeypatch.setattr(workspace_router, "_runner_feature_enabled", lambda: None)
    monkeypatch.setattr(workspace_router, "_operations_feature_enabled", lambda: None)
    offline_api_client.app.dependency_overrides[
        workspace_router.get_workspace_service
    ] = lambda: service
    try:
        started = offline_api_client.post(
            "/api/workspace/workflows/rivet/runs",
            json={
                "session_id": "session-1",
                "expected_revision": 1,
                "expected_digest": "a" * 64,
                "inputs": {},
            },
        )
        assert started.status_code == 201, started.text
        assert started.json()["run_id"] == "run-inspector"

        first_client_view = offline_api_client.get(
            "/api/workspace/workflows/runs/run-inspector/inspection",
            params={"session_id": "session-1", "after_sequence": 0},
        )
        assert first_client_view.status_code == 200
        assert first_client_view.headers["cache-control"] == "no-store"
        assert first_client_view.json()["final_outputs"][0]["value"] == {
            "status": "complete"
        }

        # A recreated browser client reattaches with GET and the last event cursor;
        # it never issues a second start request.
        reattached = offline_api_client.get(
            "/api/workspace/workflows/runs/run-inspector/inspection",
            params={"session_id": "session-1", "after_sequence": 2},
        )
        assert reattached.status_code == 200
        assert starts == ["rivet"]

        recent = offline_api_client.get(
            "/api/workspace/workflows/rivet/runs",
            params={"session_id": "session-1", "limit": 20},
        )
        assert recent.status_code == 200
        assert recent.json()["current_revision"] == 1
        assert recent.json()["runs"][0]["run_id"] == "run-inspector"
    finally:
        offline_api_client.app.dependency_overrides.pop(
            workspace_router.get_workspace_service, None
        )


async def _async_value(value):
    return value
