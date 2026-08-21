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

PLAN = {
    "schema_version": "1.0",
    "plan_id": "plan-purge",
    "plan_digest": "a" * 64,
    "principal_id": "local-compat",
    "operation_kind": "purge",
    "model_id": "wright-affine-test",
    "package_revision": 1,
    "variant_id": "json-cpu-f64",
    "snapshot_id": "bundled-models-1",
    "manifest_digest": "b" * 64,
    "effects": [],
    "blockers": [],
    "requirements": {},
    "compatibility": {},
    "prompts": [],
    "runtime_requirement": {},
    "credential_reference_present": False,
    "references": [],
    "rollback": "Retain exact content until commit.",
    "cleanup": "Report residue truthfully.",
    "created_at": "2026-08-13T12:00:00Z",
    "expires_at": "2026-08-13T12:10:00Z",
    "state": "confirmable",
}


@dataclass(slots=True)
class FakeApplication:
    calls: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def create_plan(self, **values):
        self.calls.append(("create_plan", values))
        return {**PLAN, "principal_id": values["principal_id"]}

    def list_installations(self, *, model_id, principal_id):
        self.calls.append(
            ("list_installations", {"model_id": model_id, "principal_id": principal_id})
        )
        return {
            "installations": [
                {
                    "installation_id": "installation-one",
                    "model_id": "wright-affine-test",
                    "package_revision": 1,
                    "variant_id": "json-cpu-f64",
                    "manifest_digest": "b" * 64,
                    "state": "ready",
                    "active_revision": True,
                    "runtime_adapter_id": "wright-deterministic",
                    "runtime_adapter_version": "1.0.0",
                    "installed_at": "2026-08-13T12:00:00Z",
                }
            ]
        }

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


def test_maintenance_plan_requires_exact_operation_identity() -> None:
    client, fake = _client()
    with client:
        planned = client.post(
            "/api/v1/engineering-models/plans",
            json={
                "operation_kind": "purge",
                "installation_id": "installation-one",
            },
        )
        ambiguous = client.post(
            "/api/v1/engineering-models/plans",
            json={
                "operation_kind": "purge",
                "installation_id": "installation-one",
                "model_id": "wright-affine-test",
            },
        )
        missing_target = client.post(
            "/api/v1/engineering-models/plans",
            json={
                "operation_kind": "rollback",
                "installation_id": "installation-one",
            },
        )

    assert planned.status_code == 200
    assert ambiguous.status_code == 422
    assert missing_target.status_code == 422
    assert fake.calls[0][0] == "create_plan"
    assert fake.calls[0][1]["installation_id"] == "installation-one"


def test_installation_listing_rehydrates_opaque_durable_state() -> None:
    client, fake = _client()
    with client:
        response = client.get(
            "/api/v1/engineering-models/installations",
            params={"model_id": "wright-affine-test"},
        )

    assert response.status_code == 200
    assert response.json()["installations"][0]["installation_id"] == "installation-one"
    assert "path" not in str(response.json()).lower()
    assert fake.calls[0][0] == "list_installations"
