from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from data_vault import upgrade_database
from fastapi import HTTPException
from fastapi.testclient import TestClient
from tool_registry import McpEngine
from tool_registry.capability_services import CapabilityServiceDependencies
from tool_registry.catalog_reconcile import reconcile_engineering_catalog
from tool_registry.config_import import ImportPreviewRepository
from tool_registry.db import get_server

from api.main import app
from api.routers.mcp import require_admin
from api.services.mcp_services import McpApiService, get_mcp_api_service

NOW = datetime(2026, 8, 12, 12, tzinfo=UTC)


class FakeRemoteAdapter:
    kind = "remote_endpoint"
    version = "test-1"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def _call(self, name: str) -> dict:
        self.calls.append(name)
        return {"step": name, "status": "succeeded"}

    def prepare(self) -> dict:
        return self._call("prepare")

    def apply(self) -> dict:
        return self._call("apply")

    def validate(self) -> dict:
        return self._call("validate")

    def rollback(self) -> dict:
        return self._call("rollback")


@pytest.fixture
def onboarding_client(tmp_path):
    database = tmp_path / "onboarding-api.db"
    upgrade_database(database)
    adapter = FakeRemoteAdapter()
    service = McpApiService(
        McpEngine(str(database)),
        SimpleNamespace(),
        CapabilityServiceDependencies(
            database_path=database,
            clock=lambda: NOW,
            import_preview_repository=ImportPreviewRepository(),
            onboarding_adapters={"remote_endpoint": adapter},
        ),
    )
    app.dependency_overrides[get_mcp_api_service] = lambda: service
    with TestClient(app) as client:
        yield client, adapter
    app.dependency_overrides.pop(get_mcp_api_service, None)
    app.dependency_overrides.pop(require_admin, None)


def test_import_preview_plan_staleness_and_redaction(onboarding_client) -> None:
    client, _ = onboarding_client
    configuration = """{
      "mcpServers": {
        "private": {
          "command": "uvx",
          "args": ["safe-mcp"],
          "env": {"API_TOKEN": "never-return-this"}
        }
      }
    }"""
    preview_response = client.post(
        "/api/mcp/imports/preview", json={"configuration": configuration}
    )
    assert preview_response.status_code == 200
    preview = preview_response.json()
    assert "never-return-this" not in preview_response.text
    draft = preview["drafts"][0]

    stale = client.post(
        "/api/mcp/install-plans",
        json={
            "import_preview_id": preview["preview_id"],
            "draft_id": draft["draft_id"],
            "draft_digest": "0" * 64,
            "requested_scope": "global_registered",
        },
    )
    assert stale.status_code == 409
    assert stale.json()["error_code"] == "import_draft_digest_mismatch"

    plan_response = client.post(
        "/api/mcp/install-plans",
        json={
            "import_preview_id": preview["preview_id"],
            "draft_id": draft["draft_id"],
            "draft_digest": draft["draft_digest"],
            "requested_scope": "workspace",
            "workspace_id": "workspace-a",
        },
    )
    assert plan_response.status_code == 200
    plan = plan_response.json()
    assert plan["state"] == "blocked"
    assert plan["backend_kind"] == "local_command"
    assert "never-return-this" not in plan_response.text


def test_catalog_plan_approve_apply_get_and_idempotent_retry(onboarding_client) -> None:
    client, adapter = onboarding_client
    plan_response = client.post(
        "/api/mcp/install-plans",
        json={
            "capability_id": "onshape-labs-featurescript-mcp",
            "requested_scope": "global_registered",
            "independently_completed_license": True,
        },
    )
    assert plan_response.status_code == 200
    plan = plan_response.json()
    assert plan["state"] == "reviewable"
    assert plan["backend_kind"] == "remote_endpoint"

    stale = client.post(
        f"/api/mcp/install-plans/{plan['plan_id']}/approve",
        json={"plan_digest": "0" * 64},
    )
    assert stale.status_code == 409
    assert stale.json()["error_code"] == "install_plan_digest_mismatch"

    approved = client.post(
        f"/api/mcp/install-plans/{plan['plan_id']}/approve",
        json={"plan_digest": plan["plan_digest"]},
    )
    assert approved.status_code == 200
    assert approved.json()["state"] == "approved"

    applied = client.post(
        f"/api/mcp/install-plans/{plan['plan_id']}/apply",
        json={"plan_digest": plan["plan_digest"]},
    )
    assert applied.status_code == 200
    run = applied.json()
    assert run["state"] == "completed"
    assert adapter.calls == ["prepare", "apply", "validate"]
    fetched = client.get(f"/api/mcp/onboarding-runs/{run['run_id']}")
    assert fetched.status_code == 200
    assert fetched.json() == run

    retried = client.post(
        f"/api/mcp/install-plans/{plan['plan_id']}/apply",
        json={"plan_digest": plan["plan_digest"]},
    )
    assert retried.json() == run
    assert adapter.calls == ["prepare", "apply", "validate"]

    cancelled = client.post(f"/api/mcp/onboarding-runs/{run['run_id']}/cancel")
    assert cancelled.status_code == 409
    assert cancelled.json()["error_code"] == "onboarding_run_finished"


def test_approve_and_apply_require_administrator(onboarding_client) -> None:
    client, _ = onboarding_client

    def deny_admin():
        raise HTTPException(status_code=403, detail="Administrator role required")

    app.dependency_overrides[require_admin] = deny_admin
    response = client.post(
        "/api/mcp/install-plans/plan-unknown/approve",
        json={"plan_digest": "0" * 64},
    )
    assert response.status_code == 403
    assert response.json()["message"] == "Administrator role required"


def test_default_service_applies_reviewed_remote_plan_to_registry(tmp_path) -> None:
    database = tmp_path / "default-onboarding.db"
    upgrade_database(database)
    reconcile_engineering_catalog(database)
    service = McpApiService(
        McpEngine(str(database)),
        SimpleNamespace(),
        CapabilityServiceDependencies(database_path=database, clock=lambda: NOW),
    )
    plan = service.create_install_plan(
        capability_id="onshape-labs-featurescript-mcp",
        import_preview_id=None,
        draft_id=None,
        draft_digest=None,
        requested_scope="global_registered",
        workspace_id=None,
        independently_completed_license=True,
        actor="administrator",
    )
    approved = service.approve_install_plan(
        plan.plan_id, plan.plan_digest, actor="administrator"
    )

    run = service.apply_install_plan(
        approved.plan_id,
        approved.plan_digest,
        actor="administrator",
        trace_id="trace-default-onboarding",
    )

    assert run["state"] == "completed"
    server = get_server(str(database), "onshape-labs-featurescript-mcp")
    assert server is not None
    assert server.is_installed is True
    assert server.is_active is False
