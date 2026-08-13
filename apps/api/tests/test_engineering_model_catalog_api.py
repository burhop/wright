from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routers.engineering_models import (
    get_engineering_model_application,
    router,
)
from api.security import ControlPlaneSecurityMiddleware, SecuritySettings


@dataclass(slots=True)
class FakeModelApplication:
    calls: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def list_catalog(self, **filters):
        self.calls.append(("list_catalog", filters))
        return {
            "snapshot": {
                "snapshot_id": "wright-models-bundled-1",
                "catalog_digest": "a" * 64,
                "freshness": "bundled",
                "offline": True,
            },
            "models": [model_view()],
            "next_cursor": None,
            "total": 1,
        }

    def get_catalog_model(self, model_id: str):
        self.calls.append(("get_catalog_model", {"model_id": model_id}))
        if model_id != "wright-affine-test":
            raise KeyError(model_id)
        return model_view()


def model_view() -> dict[str, Any]:
    return {
        "model_id": "wright-affine-test",
        "display_name": "Wright Affine Test Model",
        "description": "Generated deterministic lifecycle fixture.",
        "tasks": ["predict"],
        "source": {
            "kind": "wright",
            "uri": "wright://generated/affine-test",
            "immutable_revision": "fixture-revision-1",
        },
        "license": {
            "expression": "MIT",
            "attribution": "Wright contributors",
            "redistribution": "allowed",
        },
        "readiness": "approved",
        "compatibility": {"state": "compatible", "reasons": []},
        "evidence": {
            "source": "bundled",
            "license": "bundled",
            "artifact": "bundled",
            "runtime": "bundled",
            "compatibility": "cached",
            "security": "bundled",
            "test": "bundled",
        },
        "limitations": [
            {
                "limitation_id": "test-only",
                "description": "Not a production engineering model.",
                "severity": "critical",
            }
        ],
        "variants": [],
        "blockers": [],
        "generator": None,
        "manifest_digest": "b" * 64,
        "entry_digest": "c" * 64,
        "snapshot": {
            "snapshot_id": "wright-models-bundled-1",
            "catalog_digest": "a" * 64,
            "freshness": "bundled",
            "offline": True,
        },
    }


@pytest.fixture
def client():
    application = FastAPI()
    application.state.security_settings = SecuritySettings(
        mode="compat",
        api_token=None,
        allowed_origins=("http://127.0.0.1:5173",),
        bind_host="127.0.0.1",
    )
    application.add_middleware(ControlPlaneSecurityMiddleware)
    application.include_router(router, prefix="/api/v1/engineering-models")
    fake = FakeModelApplication()
    application.dependency_overrides[get_engineering_model_application] = lambda: fake
    with TestClient(application) as test_client:
        yield test_client, application, fake


def test_catalog_api_delegates_filters_and_has_no_mutation(client) -> None:
    test_client, _, fake = client
    response = test_client.get(
        "/api/v1/engineering-models/catalog",
        params={"search": "affine", "task": "predict", "limit": 25},
    )

    assert response.status_code == 200
    assert response.json()["models"][0]["model_id"] == "wright-affine-test"
    assert fake.calls == [
        (
            "list_catalog",
            {
                "search": "affine",
                "task": "predict",
                "source_kind": None,
                "readiness": (),
                "platform": None,
                "architecture": None,
                "accelerator": None,
                "evidence_state": None,
                "maximum_bytes": None,
                "cursor": None,
                "limit": 25,
            },
        )
    ]


def test_catalog_detail_is_bounded_and_missing_is_stable(client) -> None:
    test_client, _, _ = client
    detail = test_client.get("/api/v1/engineering-models/catalog/wright-affine-test")
    missing = test_client.get("/api/v1/engineering-models/catalog/not-present")

    assert detail.status_code == 200
    assert "runtime_command" not in detail.text
    assert "host_path" not in detail.text
    assert missing.status_code == 404
    assert missing.json()["detail"]["category"] == "model_not_found"


def test_catalog_api_requires_authentication_when_control_plane_is_enforced(
    client,
) -> None:
    test_client, application, _ = client
    application.state.security_settings = SecuritySettings(
        mode="enforced",
        api_token="synthetic-test-token",
        allowed_origins=("http://127.0.0.1:5173",),
        bind_host="127.0.0.1",
    )

    denied = test_client.get("/api/v1/engineering-models/catalog")
    allowed = test_client.get(
        "/api/v1/engineering-models/catalog",
        headers={"Authorization": "Bearer synthetic-test-token"},
    )

    assert denied.status_code == 401
    assert allowed.status_code == 200
