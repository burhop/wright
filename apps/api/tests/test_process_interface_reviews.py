"""Review transport on real durable runs; synthetic model/reviewer test evidence."""

from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.routers.workspace import get_workspace_service
from packages.workspace_service.tests.test_process_review_decisions import (
    waiting_review_case,
)

PREFIX = "/api/workspace/process-interfaces"


@pytest.fixture(params=[False, True], ids=["action-review", "artifact-review"])
def review_case(tmp_path, monkeypatch, request):
    holder = {}

    @asynccontextmanager
    async def lifespan(_):
        yield
        if holder:
            await holder["owner"].close()

    monkeypatch.setattr(app.router, "lifespan_context", lifespan)
    try:
        with TestClient(app) as client:

            async def setup():
                return await waiting_review_case(tmp_path, artifact=request.param)

            owner, reference, receipt, cp, digest, calls, generate = client.portal.call(
                setup
            )
            holder["owner"] = owner
            workspace = owner.workspace
            workspace.lifecycle = SimpleNamespace(
                get_by_session=lambda key: (
                    {"workspace_id": "workspace", "local_path": str(tmp_path)}
                    if key == "owned-session"
                    else None
                )
            )
            app.dependency_overrides[get_workspace_service] = lambda: workspace
            yield SimpleNamespace(
                client=client,
                owner=owner,
                reference=reference,
                receipt=receipt,
                checkpoint=cp,
                calls=calls,
                body={
                    "session_id": "owned-session",
                    "path": reference.source_path,
                    "expected_storage_digest": reference.source_digest,
                    "subject_digest": digest,
                    "decision": "approved",
                    "reason": "Synthetic API review",
                    "request_id": "api-review",
                },
            )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)


def submit(case, **changes):
    return case.client.post(
        f"{PREFIX}/interactions/{case.checkpoint}/decision",
        json={**case.body, **changes},
    )


def test_review_route_derives_actor_and_run_and_duplicate_is_read_only(review_case):
    case = review_case
    response = submit(case)
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    result = response.json()
    assert result["context"]["run_id"] == case.receipt.run_id
    interaction = next(
        item
        for item in result["interactions"]
        if item["checkpoint_id"] == case.checkpoint
    )
    assert interaction["decision"]["actor"] == "local-control-plane"
    assert interaction["decision"]["request_id"] == "api-review"
    assert not interaction["decision"]["integration_test"]
    assert submit(case).status_code == 200
    assert len(case.calls) == 1


@pytest.mark.parametrize(
    "extra", ["actor", "run_id", "auto", "destination", "integration_test"]
)
def test_review_transport_rejects_forged_authority(review_case, extra):
    case = review_case
    response = submit(case, **{extra: "untrusted"})
    assert response.status_code == 422
    assert len(case.calls) == 1


def test_changed_review_request_conflicts_and_invalid_reason_is_rejected(review_case):
    case = review_case
    assert submit(case, decision="changes_requested", reason="   ").status_code == 422
    assert submit(case).status_code == 200
    response = submit(case, request_id="different-request")
    assert response.status_code == 409, response.text
    assert response.json()["error_code"] == "REQUEST_CONFLICT"
    assert len(case.calls) == 1
