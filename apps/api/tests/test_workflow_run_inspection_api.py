from __future__ import annotations

from types import SimpleNamespace

import pytest
from api.routers import workspace as workspace_router
from fastapi import HTTPException, Response


def _summary(**overrides):
    value = {
        "run_id": "run-1",
        "workspace_id": "workspace-1",
        "session_id": "session-1",
        "workflow_id": "workflow-1",
        "revision": 2,
        "digest": "a" * 64,
        "graph": "Main",
        "generation": 3,
        "state": "succeeded",
        "started_at": "2026-08-20T14:00:00Z",
        "completed_at": "2026-08-20T14:00:03Z",
        "duration_ms": 3000,
        "reason_code": None,
        "trace_id": "trace-1",
        "latest_sequence": 4,
        "has_outputs": True,
        "has_diagnostic": False,
        "output_truncated": False,
        "output_redaction_count": 0,
    }
    value.update(overrides)
    return value


def _inspection():
    return {
        "schema_version": 1,
        "run": _summary(),
        "progress": {
            "phase": "completed",
            "current_step_id": None,
            "completed_steps": 1,
            "total_steps": 1,
            "last_sequence": 4,
            "updated_at": "2026-08-20T14:00:03Z",
        },
        "events": [
            {
                "sequence": 4,
                "kind": "completed",
                "occurred_at": "2026-08-20T14:00:03Z",
                "payload": {"phase": "completed"},
            }
        ],
        "run_inputs": [
            {
                "result_id": "run_input:length",
                "name": "length",
                "origin": "run_input",
                "kind": "number",
                "data_type": "number",
                "evidence_state": "available",
                "value": 25,
                "preview": "25",
                "complete": True,
                "truncation_reason": None,
                "original_bytes": 2,
                "retained_bytes": 2,
                "digest": "c" * 64,
                "redaction_count": 0,
                "artifact": None,
            }
        ],
        "inputs_state": "available",
        "steps": [
            {
                "step_id": "node:node-prepare",
                "sequence": 1,
                "node_id": "node-prepare",
                "node_type": "code",
                "label": "Prepare inputs",
                "kind": "node",
                "qualified_tool_name": None,
                "request_id": None,
                "trace_id": "trace-1",
                "state": "succeeded",
                "started_at": "2026-08-20T14:00:00Z",
                "completed_at": "2026-08-20T14:00:01Z",
                "duration_ms": 1000,
                "reason_code": None,
                "inputs": [],
                "outputs": [],
                "input_state": "available",
                "output_state": "available",
                "result": None,
                "artifacts": [],
                "redaction_count": 0,
                "complete": True,
            }
        ],
        "final_outputs": [
            {
                "result_id": "output",
                "name": "output",
                "origin": "workflow_output",
                "kind": "text",
                "data_type": "string",
                "evidence_state": "available",
                "value": "done",
                "preview": "done",
                "complete": True,
                "truncation_reason": None,
                "original_bytes": 4,
                "retained_bytes": 4,
                "digest": "b" * 64,
                "redaction_count": 0,
                "artifact": None,
            }
        ],
        "diagnostic": None,
        "completeness": {
            "inputs_complete": True,
            "outputs_complete": True,
            "steps_complete": True,
            "events_complete": True,
            "evidence_available": True,
            "reasons": [],
        },
    }


@pytest.fixture(autouse=True)
def _features(monkeypatch):
    monkeypatch.setattr(workspace_router, "_runner_feature_enabled", lambda: None)
    monkeypatch.setattr(workspace_router, "_operations_feature_enabled", lambda: None)


@pytest.mark.asyncio
async def test_inspection_is_scoped_incremental_typed_and_non_cacheable():
    calls = []

    class Operations:
        def inspection(self, **kwargs):
            calls.append(kwargs)
            return _inspection()

    service = SimpleNamespace(
        lifecycle=SimpleNamespace(
            get_by_session=lambda session: (
                {"workspace_id": "workspace-1"} if session == "session-1" else None
            )
        ),
        workflow_operations=Operations(),
    )
    response = Response()
    projected = await workspace_router.workflow_run_inspection_endpoint(
        "run-1", response, "session-1", 3, service
    )
    assert calls == [
        {
            "workspace_id": "workspace-1",
            "session_id": "session-1",
            "run_id": "run-1",
            "after_sequence": 3,
        }
    ]
    assert response.headers["Cache-Control"] == "no-store"
    assert projected.steps[0].node_type == "code"
    assert projected.steps[0].label == "Prepare inputs"
    assert projected.run_inputs[0].name == "length"
    assert projected.run_inputs[0].data_type == "number"
    assert projected.final_outputs[0].value == "done"
    assert projected.completeness.inputs_complete is True
    assert projected.completeness.outputs_complete is True

    with pytest.raises(HTTPException) as hidden:
        await workspace_router.workflow_run_inspection_endpoint(
            "run-1", Response(), "session-other", 0, service
        )
    assert hidden.value.status_code == 404


@pytest.mark.asyncio
async def test_run_artifact_is_run_scoped_digest_verified_and_non_cacheable():
    calls = []

    class Operations:
        def run(self, **kwargs):
            calls.append(("run", kwargs))
            return SimpleNamespace(run_id="run-1")

    class Artifacts:
        def read_for_run(self, **kwargs):
            calls.append(("artifact", kwargs))
            return (
                SimpleNamespace(
                    relative_path="reports/design review.md",
                    media_type="text/markdown",
                ),
                b"# Design review\n",
            )

    service = SimpleNamespace(
        lifecycle=SimpleNamespace(
            get_by_session=lambda session: (
                {"workspace_id": "workspace-1"} if session == "session-1" else None
            )
        ),
        workflow_operations=Operations(),
        workspace_document_artifacts=Artifacts(),
        resolve_workspace_dir=lambda *_args: _async_value("D:/workspace"),
    )
    response = await workspace_router.workflow_run_artifact_endpoint(
        "run-1",
        "artifact-1",
        "session-1",
        SimpleNamespace(),
        service,
    )

    assert response.body == b"# Design review\n"
    assert response.media_type == "text/markdown"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "design%20review.md" in response.headers["content-disposition"]
    assert calls == [
        (
            "run",
            {
                "workspace_id": "workspace-1",
                "session_id": "session-1",
                "run_id": "run-1",
            },
        ),
        (
            "artifact",
            {
                "workspace_id": "workspace-1",
                "session_id": "session-1",
                "workspace_path": "D:/workspace",
                "run_id": "run-1",
                "artifact_id": "artifact-1",
            },
        ),
    ]

    with pytest.raises(HTTPException) as hidden:
        await workspace_router.workflow_run_artifact_endpoint(
            "run-1",
            "artifact-1",
            "session-other",
            SimpleNamespace(),
            service,
        )
    assert hidden.value.status_code == 404


@pytest.mark.asyncio
async def test_recent_runs_include_current_revision_and_enforce_scope_and_limit(
    monkeypatch,
):
    calls = []

    class Operations:
        def recent_runs(self, **kwargs):
            calls.append(kwargs)
            return (_summary(), _summary(run_id="run-old", revision=1, state="failed"))

    class Store:
        def __init__(self, _path):
            pass

        def read(self, slug):
            assert slug == "workflow"
            return SimpleNamespace(workflow_id="workflow-1", revision=2)

    monkeypatch.setattr(workspace_router, "WorkspaceWorkflowStore", Store)
    service = SimpleNamespace(
        lifecycle=SimpleNamespace(
            get_by_session=lambda session: (
                {"workspace_id": "workspace-1"} if session == "session-1" else None
            )
        ),
        resolve_workspace_dir=lambda *_args: _async_value("D:/workspace"),
        workflow_operations=Operations(),
    )
    response = Response()
    projected = await workspace_router.recent_workflow_runs_endpoint(
        "workflow", response, "session-1", 20, SimpleNamespace(), service
    )
    assert response.headers["Cache-Control"] == "no-store"
    assert projected.current_revision == 2
    assert [item.run_id for item in projected.runs] == ["run-1", "run-old"]
    assert calls[0]["limit"] == 20

    with pytest.raises(HTTPException) as hidden:
        await workspace_router.recent_workflow_runs_endpoint(
            "workflow", Response(), "session-other", 20, SimpleNamespace(), service
        )
    assert hidden.value.status_code == 404


async def _async_value(value):
    return value
