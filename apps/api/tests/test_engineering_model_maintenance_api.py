from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routers.engineering_models import get_engineering_model_application, router
from api.security import ControlPlaneSecurityMiddleware, SecuritySettings


MAINTENANCE = {
    "installation_id": "installation-one",
    "state": "ready",
    "active": True,
    "reclaimable_bytes": 64,
    "blockers": [],
    "references": [],
}


@dataclass(slots=True)
class FakeApplication:
    calls: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def get_installation_maintenance(self, installation_id, *, principal_id):
        self.calls.append(("get_installation_maintenance", locals() | {"self": None}))
        return MAINTENANCE

    def compare_installation_update(
        self, installation_id, *, model_id, variant_id, principal_id
    ):
        self.calls.append(("compare_installation_update", locals() | {"self": None}))
        return {
            "changed_facets": ["artifacts"],
            "requires_retest": True,
            "diff_digest": "a" * 64,
        }

    def maintain_installation(
        self, installation_id, *, action, target_installation_id, principal_id, trace_id
    ):
        self.calls.append(("maintain_installation", locals() | {"self": None}))
        return {
            **MAINTENANCE,
            "state": action,
            "target_installation_id": target_installation_id,
        }

    def set_model_reference_state(self, reference_id, *, state, principal_id):
        self.calls.append(("set_model_reference_state", locals() | {"self": None}))
        return {"reference_id": reference_id, "state": state}

    def create_offline_export(self, installation_id, *, principal_id, trace_id):
        self.calls.append(("create_offline_export", locals() | {"self": None}))
        return {"artifact_id": "export-a1", "sha256": "b" * 64, "size": 128}


def _client():
    app = FastAPI()
    app.state.security_settings = SecuritySettings(
        mode="compat",
        api_token=None,
        allowed_origins=("http://127.0.0.1:5173",),
        bind_host="127.0.0.1",
    )
    app.add_middleware(ControlPlaneSecurityMiddleware)
    app.include_router(router, prefix="/api/v1/engineering-models")
    fake = FakeApplication()
    app.dependency_overrides[get_engineering_model_application] = lambda: fake
    return TestClient(app), fake


def test_maintenance_routes_delegate_without_exposing_paths() -> None:
    client, fake = _client()
    with client:
        detail = client.get(
            "/api/v1/engineering-models/installations/installation-one/maintenance"
        )
        compared = client.post(
            "/api/v1/engineering-models/installations/installation-one/compare-update",
            json={"model_id": "wright-affine-test", "variant_id": "json-cpu-f64"},
        )
        rolled_back = client.post(
            "/api/v1/engineering-models/installations/installation-one/maintenance",
            json={"action": "rollback", "target_installation_id": "installation-zero"},
        )
        archived = client.patch(
            "/api/v1/engineering-models/references/reference-one",
            json={"state": "archived"},
        )
        exported = client.post(
            "/api/v1/engineering-models/installations/installation-one/exports"
        )

    assert [
        detail.status_code,
        compared.status_code,
        rolled_back.status_code,
        archived.status_code,
        exported.status_code,
    ] == [200] * 5
    assert compared.json()["requires_retest"] is True
    assert rolled_back.json()["target_installation_id"] == "installation-zero"
    assert exported.json()["artifact_id"] == "export-a1"
    assert "path" not in str(exported.json()).lower()
    assert [name for name, _ in fake.calls] == [
        "get_installation_maintenance",
        "compare_installation_update",
        "maintain_installation",
        "set_model_reference_state",
        "create_offline_export",
    ]


def test_maintenance_request_actions_are_bounded() -> None:
    client, fake = _client()
    with client:
        bad = client.post(
            "/api/v1/engineering-models/installations/installation-one/maintenance",
            json={"action": "force-delete"},
        )
    assert bad.status_code == 422
    assert fake.calls == []
