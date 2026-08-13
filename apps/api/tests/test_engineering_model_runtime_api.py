from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routers.engineering_models import get_engineering_model_application, router
from api.security import ControlPlaneSecurityMiddleware, SecuritySettings


EVIDENCE = {
    "evidence_id": "evidence-one",
    "state": "passed",
    "material_digest": "a" * 64,
    "observation_digest": "b" * 64,
    "material": {"vector_id": "predict-two", "result": "passed"},
    "observation": {"timing_ms": 1},
}
TEST_RESULT = {
    "installation_id": "installation-one",
    "installation_state": "ready",
    "adapter_id": "wright-deterministic",
    "adapter_version": "1.0.0",
    "evidence": [EVIDENCE],
}
BINDING = {
    "binding_id": "binding-one",
    "binding_digest": "c" * 64,
    "workspace_id": "workspace-one",
    "installation_id": "installation-one",
    "task_id": "predict",
    "tool_name": "wright_model__wright_affine_test__predict",
    "policy_snapshot_digest": "d" * 64,
    "state": "enabled",
}


@dataclass(slots=True)
class FakeApplication:
    calls: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    async def run_standard_test(self, installation_id, *, principal_id, trace_id):
        self.calls.append(("run_standard_test", locals() | {"self": None}))
        return TEST_RESULT

    def get_standard_test_evidence(self, installation_id, *, principal_id):
        self.calls.append(("get_standard_test_evidence", locals() | {"self": None}))
        return TEST_RESULT

    def create_workspace_binding(
        self, installation_id, *, task_id, workspace_id, principal_id
    ):
        self.calls.append(("create_workspace_binding", locals() | {"self": None}))
        return BINDING

    def set_workspace_binding_state(
        self, binding_id, *, state, workspace_id, principal_id
    ):
        self.calls.append(("set_workspace_binding_state", locals() | {"self": None}))
        return {**BINDING, "state": state}


def client():
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


def test_standard_test_evidence_and_workspace_binding_routes_delegate_exactly() -> None:
    test_client, fake = client()
    with test_client:
        tested = test_client.post(
            "/api/v1/engineering-models/installations/installation-one/standard-test"
        )
        evidence = test_client.get(
            "/api/v1/engineering-models/installations/installation-one/evidence"
        )
        enabled = test_client.post(
            "/api/v1/engineering-models/workspaces/workspace-one/bindings",
            json={"installation_id": "installation-one", "task_id": "predict"},
            headers={"X-Wright-Workspace-ID": "workspace-one"},
        )
        disabled = test_client.patch(
            "/api/v1/engineering-models/workspaces/workspace-one/bindings/binding-one",
            json={"state": "disabled"},
            headers={"X-Wright-Workspace-ID": "workspace-one"},
        )

    assert [
        tested.status_code,
        evidence.status_code,
        enabled.status_code,
        disabled.status_code,
    ] == [200] * 4
    assert tested.json()["installation_state"] == "ready"
    assert evidence.json()["evidence"][0]["material_digest"] == "a" * 64
    assert enabled.json()["tool_name"] == "wright_model__wright_affine_test__predict"
    assert disabled.json()["state"] == "disabled"
    assert [name for name, _ in fake.calls] == [
        "run_standard_test",
        "get_standard_test_evidence",
        "create_workspace_binding",
        "set_workspace_binding_state",
    ]


def test_runtime_bodies_are_bounded_and_private_fields_are_rejected() -> None:
    test_client, _ = client()
    with test_client:
        bad_task = test_client.post(
            "/api/v1/engineering-models/workspaces/workspace-one/bindings",
            json={
                "installation_id": "installation-one",
                "task_id": "physical-actuation",
            },
            headers={"X-Wright-Workspace-ID": "workspace-one"},
        )
        bad_state = test_client.patch(
            "/api/v1/engineering-models/workspaces/workspace-one/bindings/binding-one",
            json={"state": "purged"},
            headers={"X-Wright-Workspace-ID": "workspace-one"},
        )
    assert bad_task.status_code == 422
    assert bad_state.status_code == 422


def test_cross_workspace_binding_header_mismatch_fails_closed() -> None:
    test_client, fake = client()
    with test_client:
        response = test_client.post(
            "/api/v1/engineering-models/workspaces/workspace-one/bindings",
            json={"installation_id": "installation-one", "task_id": "predict"},
            headers={"X-Wright-Workspace-ID": "workspace-two"},
        )
    assert response.status_code == 409
    assert response.json()["detail"]["category"] == "invalid_binding"
    assert fake.calls == []
