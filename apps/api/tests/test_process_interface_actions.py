"""Native supervised action transport; synthetic local/digital providers only."""

from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.routers import process_interfaces as routes
from api.routers.workspace import get_workspace_service
from packages.workspace_service.tests.test_process_action_supervision import (
    approved_action_case,
)

PREFIX = "/api/workspace/process-interfaces"


@pytest.fixture(params=[False, True], ids=["local-review", "digital-operation"])
def action_case(tmp_path, monkeypatch, request):
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
                return await approved_action_case(tmp_path, digital=request.param)

            case, gateway = client.portal.call(setup)
            owner, reference, receipt, cp, digest, calls, generate = case
            holder["owner"] = owner
            owner.workspace.lifecycle = SimpleNamespace(
                get_by_session=lambda key: (
                    {"workspace_id": "workspace", "local_path": str(tmp_path)}
                    if key == "owned-session"
                    else None
                )
            )
            app.dependency_overrides[get_workspace_service] = lambda: owner.workspace
            monkeypatch.setattr(routes, "generate_workflow_response", generate)
            monkeypatch.setattr(app.state, "gateway_service", gateway, raising=False)
            yield SimpleNamespace(
                client=client,
                owner=owner,
                case=case,
                gateway=gateway,
                calls=calls,
                url=f"{PREFIX}/actions/continue-{cp}",
                body={
                    "session_id": "owned-session",
                    "path": reference.source_path,
                    "expected_storage_digest": reference.source_digest,
                    "subject_digest": digest,
                    "request_id": "api-action",
                },
            )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)


def test_action_route_derives_identity_and_continues_the_same_run(action_case):
    c = action_case
    response = c.client.post(c.url, json=c.body)
    assert response.status_code == 202, response.text
    assert response.headers["cache-control"] == "no-store"
    snapshot = response.json()
    assert snapshot["context"]["run_id"] == c.case[2].run_id
    interaction = next(
        i for i in snapshot["interactions"] if i["checkpoint_id"] == c.case[3]
    )
    assert interaction["action_receipt"]["request_id"] == "api-action"
    assert interaction["action_receipt"]["principal_id"] == "local-control-plane"
    from packages.workspace_service.tests.test_process_action_supervision import (
        action_scope,
    )

    completed = c.client.portal.call(
        c.owner.runs.wait, action_scope(), c.case[1], c.case[2].run_id
    )
    assert completed["status"] == "completed"
    assert c.client.post(c.url, json=c.body).status_code == 202
    assert len(c.calls) == 2
    if c.gateway:
        assert len(c.gateway.calls) == 1


@pytest.mark.parametrize(
    "extra",
    [
        "principal_id",
        "actor",
        "run_id",
        "destination",
        "settings",
        "auto",
        "integration_test",
    ],
)
def test_action_route_rejects_client_supplied_authority(action_case, extra):
    c = action_case
    response = c.client.post(c.url, json={**c.body, extra: "untrusted"})
    assert response.status_code == 422, response.text
    assert len(c.calls) == 1
    if c.gateway:
        assert not c.gateway.calls
