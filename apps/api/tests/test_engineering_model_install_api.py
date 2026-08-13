from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routers.engineering_models import get_engineering_model_application, router
from api.security import ControlPlaneSecurityMiddleware, SecuritySettings


PLAN = {
    "schema_version": "1.0",
    "plan_id": "plan-1",
    "plan_digest": "a" * 64,
    "principal_id": "local-admin",
    "operation_kind": "install",
    "model_id": "wright-affine-test",
    "package_revision": 1,
    "variant_id": "json-cpu-f64",
    "snapshot_id": "snapshot-1",
    "manifest_digest": "b" * 64,
    "effects": [
        {
            "kind": "write",
            "description": "Write verified content.",
            "safe_location": "Wright model data",
            "exact_bytes": 10,
            "maximum_bytes": 10,
            "reversible": True,
        }
    ],
    "blockers": [],
    "requirements": {
        "network": "none",
        "credential": "none",
        "license_action": "none",
        "runtime_change": "separate_plan_only",
    },
    "compatibility": {
        "state": "compatible",
        "observed_at": "2026-08-13T12:00:00Z",
        "reasons": [],
    },
    "prompts": [
        {"prompt_id": "confirm-install", "message": "Install?", "required": True}
    ],
    "runtime_requirement": {
        "adapter_id": "wright-deterministic",
        "version_specifier": "==1.0.0",
        "state": "available",
        "separate_plan_required": False,
    },
    "credential_reference_present": False,
    "references": [],
    "rollback": "Remove the inactive view.",
    "cleanup": "Delete operation staging.",
    "created_at": "2026-08-13T12:00:00Z",
    "expires_at": "2026-08-13T12:10:00Z",
    "state": "confirmable",
}
OPERATION = {
    "schema_version": "1.0",
    "operation_id": "operation-1",
    "plan_id": "plan-1",
    "plan_digest": "a" * 64,
    "kind": "install",
    "state": "running",
    "phase": "acquiring",
    "progress": {
        "completed_items": 0,
        "total_items": 1,
        "completed_bytes": 0,
        "maximum_bytes": 10,
        "message": "Acquiring verified data.",
    },
    "trace_id": "trace-1",
    "cleanup_state": "not_needed",
    "created_at": "2026-08-13T12:00:00Z",
    "updated_at": "2026-08-13T12:00:01Z",
}


@dataclass(slots=True)
class FakeApplication:
    calls: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def create_plan(self, **values):
        self.calls.append(("create_plan", values))
        return PLAN

    def create_import_plan(self, *, archive: bytes, principal_id: str):
        self.calls.append(
            (
                "create_import_plan",
                {"archive_size": len(archive), "principal_id": principal_id},
            )
        )
        return {**PLAN, "operation_kind": "import"}

    def get_plan(self, plan_id: str, *, principal_id: str):
        self.calls.append(
            ("get_plan", {"plan_id": plan_id, "principal_id": principal_id})
        )
        return PLAN

    def confirm_plan(
        self, plan_id: str, *, principal_id: str, plan_digest: str, trace_id: str
    ):
        self.calls.append(("confirm_plan", locals() | {"self": None}))
        return OPERATION

    def get_operation(self, operation_id: str, *, principal_id: str):
        self.calls.append(
            (
                "get_operation",
                {"operation_id": operation_id, "principal_id": principal_id},
            )
        )
        return OPERATION

    def cancel_operation(self, operation_id: str, *, principal_id: str):
        self.calls.append(
            (
                "cancel_operation",
                {"operation_id": operation_id, "principal_id": principal_id},
            )
        )
        return {**OPERATION, "state": "cancelling"}

    def operation_events(self, operation_id: str, *, principal_id: str, after: int):
        self.calls.append(
            (
                "operation_events",
                {
                    "operation_id": operation_id,
                    "principal_id": principal_id,
                    "after": after,
                },
            )
        )
        return ({"sequence": 1, "operation": OPERATION},)


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


def test_plan_confirm_operation_and_cancel_routes_delegate_exactly() -> None:
    test_client, fake = client()
    with test_client:
        preview = test_client.post(
            "/api/v1/engineering-models/plans",
            json={
                "operation_kind": "install",
                "model_id": "wright-affine-test",
                "variant_id": "json-cpu-f64",
            },
        )
        read = test_client.get("/api/v1/engineering-models/plans/plan-1")
        confirmed = test_client.post(
            "/api/v1/engineering-models/plans/plan-1/confirm",
            json={"plan_digest": "a" * 64},
        )
        operation = test_client.get("/api/v1/engineering-models/operations/operation-1")
        cancelled = test_client.post(
            "/api/v1/engineering-models/operations/operation-1/cancel"
        )

    assert [
        item.status_code for item in (preview, read, confirmed, operation, cancelled)
    ] == [200] * 5
    assert confirmed.json()["operation_id"] == "operation-1"
    assert cancelled.json()["state"] == "cancelling"
    assert [name for name, _ in fake.calls[:5]] == [
        "create_plan",
        "get_plan",
        "confirm_plan",
        "get_operation",
        "cancel_operation",
    ]


def test_operation_events_are_bounded_authenticated_sse() -> None:
    test_client, fake = client()
    with test_client:
        response = test_client.get(
            "/api/v1/engineering-models/operations/operation-1/events",
            headers={"Last-Event-ID": "0"},
        )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: operation" in response.text
    assert "runtime_endpoint" not in response.text
    assert fake.calls[-1][0] == "operation_events"


def test_plan_and_confirmation_bodies_are_bounded() -> None:
    test_client, _ = client()
    with test_client:
        bad_kind = test_client.post(
            "/api/v1/engineering-models/plans",
            json={
                "operation_kind": "physical_actuation",
                "model_id": "x",
                "variant_id": "x",
            },
        )
        bad_digest = test_client.post(
            "/api/v1/engineering-models/plans/plan-1/confirm",
            json={"plan_digest": "not-a-digest"},
        )
    assert bad_kind.status_code == 422
    assert bad_digest.status_code == 422


def test_offline_import_upload_is_bounded_and_delegates_bytes_only() -> None:
    test_client, fake = client()
    with test_client:
        response = test_client.post(
            "/api/v1/engineering-models/imports",
            files={
                "package": (
                    "model.wright-model.zip",
                    b"bounded-archive",
                    "application/zip",
                )
            },
        )
    assert response.status_code == 200
    assert response.json()["operation_kind"] == "import"
    assert fake.calls[-1] == (
        "create_import_plan",
        {"archive_size": 15, "principal_id": "local-admin"},
    )
