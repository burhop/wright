"""Source subroute validation is bounded JSON and never returns private inputs."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request

from api.main import app, validation_exception_handler
from api.routers.workspace import get_workspace_service


@pytest.mark.parametrize(
    "path",
    [
        "/api/workspace/workflow-sources",
        "/api/workspace/workflow-sources/",
        "/api/workspace/workflow-sources/run",
        "/api/workspace/workflow-sources/readiness",
        "/api/workspace/workflow-sources/copy",
        "/api/workspace/workflow-sources/images",
    ],
)
def test_value_error_context_is_safe_without_echoing_private_request(path):
    private = "PRIVATE prompt and model selection must never be returned"
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": path,
            "headers": [],
            "query_string": b"",
            "server": ("test", 80),
            "scheme": "http",
        }
    )
    exc = RequestValidationError(
        [
            {
                "type": "value_error",
                "loc": ("body", private),
                "msg": "Value error, " + private,
                "input": {"source": private},
                "ctx": {"error": ValueError(private)},
            }
        ]
    )
    response = asyncio.run(validation_exception_handler(request, exc))
    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store"
    body = json.loads(response.body)
    assert body["error_code"] == "VALIDATION_ERROR"
    errors = body["details"]["errors"]
    assert errors == [
        {
            "type": "value_error",
            "loc": ["body", "[field]"],
            "msg": "Invalid declared request field",
        }
    ]
    assert private.encode() not in response.body


@pytest.mark.parametrize(
    "path,body",
    [
        ("run", {"request_id": ""}),
        ("run", {"request_id": "x" * 161}),
        ("run", {"model": {"private-model-option": "PRIVATE prompt"}}),
        ("run", {"expected_storage_digest": "PRIVATE prompt"}),
        ("run", {"source": "PRIVATE prompt"}),
        (
            "copy",
            {"source_path": "PRIVATE prompt", "expected_storage_digest": "invalid"},
        ),
    ],
)
def test_invalid_source_subroute_body_rejects_before_execution(sync_client, path, body):
    service = SimpleNamespace(lifecycle=SimpleNamespace(get_by_session=Mock()))
    app.dependency_overrides[get_workspace_service] = lambda: service
    request = {
        "session_id": "private-session",
        "path": "workflows/example.wflow",
        "expected_storage_digest": "a" * 64,
        **body,
    }
    try:
        response = sync_client.post(
            "/api/workspace/workflow-sources/" + path, json=request
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)
    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store"
    result = response.json()
    assert result["error_code"] == "VALIDATION_ERROR"
    assert result["details"]["errors"]
    assert "PRIVATE prompt" not in response.text
    assert "private-model-option" not in response.text
    assert "private-session" not in response.text
    assert all(
        "input" not in error and "ctx" not in error
        for error in result["details"]["errors"]
    )
    service.lifecycle.get_by_session.assert_not_called()
