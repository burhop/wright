"""Old operational URLs are inert; saved history remains a separate reader."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routers.workspace import router
from api.schemas import workspace as schemas


@pytest.mark.parametrize(
    "method,operation",
    [
        ("POST", "prepare"),
        ("GET", "capabilities"),
        ("GET", "printer-status"),
        ("POST", "print"),
        ("GET", "dispatch"),
        ("POST", "allow-retry"),
        ("POST", "cancel"),
        ("GET", "camera.mjpeg"),
    ],
)
def test_old_operations_return_retired_without_a_workspace_or_gateway(
    method, operation
):
    app = FastAPI()
    app.include_router(router, prefix="/api/workspace")
    # Deliberately no workspace/gateway/printer state, dependencies or mocks.
    # Even malformed legacy bodies cannot reach an operational implementation.
    with TestClient(app) as client:
        response = client.request(
            method, "/api/workspace/print-demo/" + operation, json={}
        )
    assert response.status_code == 410
    assert response.json()["code"] == "PROTOTYPE_RETIRED"
    assert "saved results remain available" in response.json()["detail"].lower()


def test_retired_operation_has_no_vendor_dependencies_or_request_schema():
    routes = [r for r in router.routes if "/print-demo/" in r.path]
    assert len(routes) == 1
    assert not routes[0].dependant.dependencies
    assert not routes[0].dependant.body_params
    assert not routes[0].include_in_schema
    for name in (
        "PrintPartPrepareRequest",
        "PrintPartDispatchRequest",
        "PrintPartCancelRequest",
    ):
        assert not hasattr(schemas, name)
