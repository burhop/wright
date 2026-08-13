from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from data_vault import upgrade_database
from fastapi.testclient import TestClient
from tool_registry import McpEngine
from tool_registry.capability_services import CapabilityServiceDependencies
from tool_registry.catalog_reconcile import reconcile_engineering_catalog
from tool_registry.catalog_reconcile import reconcile_wright_managed_servers

from api.main import app
from api.services.mcp_services import McpApiService, get_mcp_api_service


@pytest.fixture
def capability_client(tmp_path):
    database_path = tmp_path / "capabilities.db"
    upgrade_database(str(database_path))
    reconcile_engineering_catalog(str(database_path))
    service = McpApiService(
        McpEngine(str(database_path)),
        SimpleNamespace(),
        CapabilityServiceDependencies(
            database_path=database_path,
            clock=lambda: datetime(2026, 8, 12, 12, 0, tzinfo=UTC),
        ),
    )
    app.dependency_overrides[get_mcp_api_service] = lambda: service
    with TestClient(app) as client:
        yield client, database_path
    app.dependency_overrides.pop(get_mcp_api_service, None)


def test_offline_capability_list_filter_and_pagination(capability_client) -> None:
    client, _ = capability_client
    response = client.get(
        "/api/mcp/capabilities",
        params=[
            ("search", "FeatureScript"),
            ("domain", "cad"),
            ("lifecycle_stage", "verified_mcp"),
            ("maturity", "official"),
            ("evidence_class", "official_preview"),
        ],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["snapshot"]["offline"] is True
    assert body["snapshot"]["channel"] == "bundled"
    assert body["total"] == 1
    assert body["capabilities"][0]["capability_id"] == (
        "onshape-labs-featurescript-mcp"
    )
    assert body["capabilities"][0]["compatibility"]["reasons"]
    assert body["capabilities"][0]["lifecycle_stage"] == "verified_mcp"
    assert body["capabilities"][0]["maturity"] == "official"
    assert body["capabilities"][0]["data_touched"]
    assert body["capabilities"][0]["examples"]
    assert body["capabilities"][0]["field_provenance"]
    assert body["capabilities"][0]["requirements"]["supported_platforms"]

    first = client.get("/api/mcp/capabilities", params={"limit": 1}).json()
    assert first["total"] == 70
    assert first["next_cursor"]
    second = client.get(
        "/api/mcp/capabilities",
        params={"limit": 1, "cursor": first["next_cursor"]},
    ).json()
    assert (
        second["capabilities"][0]["capability_id"]
        != (first["capabilities"][0]["capability_id"])
    )


def test_fresh_start_managed_server_does_not_overclaim_legacy_validation(
    capability_client,
) -> None:
    client, database_path = capability_client
    reconcile_wright_managed_servers(str(database_path))

    response = client.get("/api/mcp/capabilities", params={"limit": 200})

    assert response.status_code == 200
    managed = next(
        capability
        for capability in response.json()["capabilities"]
        if capability["capability_id"] == "rivet-workflows"
    )
    assert managed["validation_result"]["status"] == "not_tested"
    assert managed["validation_result"]["evidence_status"] == "unverified"


def test_capability_detail_resolves_alias_without_leaking_secrets(
    capability_client,
) -> None:
    client, _ = capability_client
    response = client.get("/api/mcp/capabilities/onshape-featurescript-mcp-official")

    assert response.status_code == 200
    body = response.json()
    assert body["canonical_id"] == "onshape-labs-featurescript-mcp"
    assert body["evidence_class"] == "official_preview"
    assert body["transport"] == "streamable_http"
    assert "api_key" not in response.text.lower()
    assert "authorization" not in response.text.lower()


def test_capability_errors_are_bounded_and_stable(capability_client) -> None:
    client, _ = capability_client
    missing = client.get("/api/mcp/capabilities/not-present")
    invalid_cursor = client.get(
        "/api/mcp/capabilities", params={"cursor": "not-a-cursor!"}
    )

    assert missing.status_code == 404
    assert invalid_cursor.status_code == 400
    assert "private" not in invalid_cursor.text.lower()


def test_observe_is_read_only_and_persists_only_machine_facts(
    capability_client, monkeypatch
) -> None:
    client, database_path = capability_client

    def network_must_not_run(*args, **kwargs):
        raise AssertionError("capability observation contacted the network")

    monkeypatch.setattr("urllib.request.urlopen", network_must_not_run)
    response = client.post(
        "/api/mcp/capabilities/onshape-labs-featurescript-mcp/observe"
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["observation"]["digest"]) == 64
    assert body["compatibility"]["status"] == "uncertain"
    with sqlite3.connect(database_path) as connection:
        stored = connection.execute(
            "SELECT observation_json FROM machine_compatibility_observations"
        ).fetchone()
    assert stored is not None
    assert "fs-mcp.labs.onshape.app" not in stored[0]
