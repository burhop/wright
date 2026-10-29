import asyncio
from pathlib import Path
from types import SimpleNamespace

from fastapi import HTTPException
import pytest
from api.routers.workspace import workflow_pending_navigation as read
from data_vault import workflow_continuation_repository as c
from workspace_service.workflow_external_actions import WorkflowExternalActionService
from workspace_service.workflow_artifact_review import WorkflowArtifactReviewService
from dataclasses import replace


def checkpoint(index, **changes):
    return replace(
        c.WorkflowContinuationCheckpoint(
            checkpoint_id=f"checkpoint-{index:04}",
            workspace_id="workspace-a",
            workflow_id="workflows/handle.wflow",
            run_id=f"run-{index}",
            step_id="review",
            action_kind="local_review",
            subject={"private_evidence": "must not leave owner"},
            subject_digest=f"{index:064x}",
            state="pending",
            continuation={
                "run_log_path": f"runs/{index}.json",
                "source_digest": "a" * 64,
                "step_title": "Review strength results",
                "execution_context": {"private": True},
            },
            actor=None,
            reason=None,
            created_at=index,
            updated_at=index,
            expires_at=None,
            external_action=None,
        ),
        **changes,
    )


def service(tmp_path):
    db = str(tmp_path / "state.db")
    return SimpleNamespace(
        db_path=db,
        lifecycle=SimpleNamespace(
            get_by_session=lambda session: (
                {"workspace_id": "workspace-a", "local_path": str(tmp_path)}
                if session == "session-a"
                else None
            )
        ),
        ensure_workspace_path_safe=lambda path: Path(path),
        workflow_external_actions=WorkflowExternalActionService(
            c.WorkflowContinuationRepository(db)
        ),
        workflow_artifact_reviews=WorkflowArtifactReviewService(db),
    )


def test_api_combines_only_persisted_session_workspace_navigation(tmp_path):
    owner = service(tmp_path)
    original = checkpoint(1)
    c.WorkflowContinuationRepository(owner.db_path).create(original)
    c.WorkflowContinuationRepository(owner.db_path).create(
        checkpoint(2, workspace_id="workspace-b")
    )
    owner.workflow_artifact_reviews.repository.create(
        "review-1",
        "workspace-a",
        "workflows/robot.wflow",
        "f" * 64,
        {
            "summary": {
                "run_id": "robot-run",
                "run_log_path": "runs/robot.json",
                "source_digest": "b" * 64,
            }
        },
    )
    reply = asyncio.run(read("session-a", service=owner))
    assert reply["workspace_id"] == "workspace-a"
    assert [r["run_id"] for r in reply["checkpoints"]["items"]] == ["run-1"]
    assert [r["run_id"] for r in reply["reviews"]["items"]] == ["robot-run"]
    assert (
        c.WorkflowContinuationRepository(owner.db_path).get(original.checkpoint_id)
        == original
    )
    assert (
        owner.workflow_artifact_reviews.repository.get("workspace-a", "review-1")[
            "state"
        ]
        == "pending"
    )


def test_unknown_session_cannot_query_other_workspace(tmp_path):
    with pytest.raises(HTTPException) as error:
        asyncio.run(read("unknown", service=service(tmp_path)))
    assert error.value.status_code == 404


def test_resolved_review_disappears_without_changing_another_wait(tmp_path):
    owner = service(tmp_path)
    original = checkpoint(1)
    c.WorkflowContinuationRepository(owner.db_path).create(original)
    repository = owner.workflow_artifact_reviews.repository
    repository.create(
        "review",
        "workspace-a",
        "workflows/robot.wflow",
        "e" * 64,
        {"summary": {"run_id": "robot-run"}},
    )
    assert len(asyncio.run(read("session-a", service=owner))["reviews"]["items"]) == 1
    repository.decide("workspace-a", "review", "e" * 64, {"state": "changes_requested"})
    result = asyncio.run(read("session-a", service=owner))
    assert result["reviews"]["items"] == []
    assert (
        c.WorkflowContinuationRepository(owner.db_path).get(original.checkpoint_id)
        == original
    )
    assert repository.get("workspace-a", "review")["state"] == "changes_requested"


def test_http_route_uses_real_owners_and_rejects_unknown_session(tmp_path):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from api.routers import workspace as router

    owner = service(tmp_path)
    c.WorkflowContinuationRepository(owner.db_path).create(checkpoint(1))
    app = FastAPI()
    app.include_router(router.router, prefix="/api/workspace")
    app.dependency_overrides[router.get_workspace_service] = lambda: owner
    with TestClient(app) as client:
        response = client.get(
            "/api/workspace/workflow-sources/pending",
            params={"session_id": "session-a"},
        )
        assert response.status_code == 200
        assert response.json()["checkpoints"]["items"][0]["run_id"] == "run-1"
        assert (
            client.get(
                "/api/workspace/workflow-sources/pending",
                params={"session_id": "unknown"},
            ).status_code
            == 404
        )
    assert (
        c.WorkflowContinuationRepository(owner.db_path).get("checkpoint-0001").state
        == "pending"
    )
