from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from data_vault import upgrade_database
from fastapi import HTTPException
from fastapi.testclient import TestClient
from tool_registry import McpEngine
from tool_registry.capability_services import CapabilityServiceDependencies

from api.main import app
from api.routers.mcp import require_engineer_or_admin
from api.services.mcp_services import McpApiService, get_mcp_api_service

NOW = datetime(2026, 8, 12, 15, 0, tzinfo=UTC)


@pytest.fixture
def report_client(tmp_path):
    database = tmp_path / "missing-report.db"
    upgrade_database(database)
    service = McpApiService(
        McpEngine(str(database)),
        SimpleNamespace(),
        CapabilityServiceDependencies(database_path=database, clock=lambda: NOW),
    )
    app.dependency_overrides[get_mcp_api_service] = lambda: service
    try:
        with TestClient(app) as client:
            yield client, database
    finally:
        app.dependency_overrides.pop(get_mcp_api_service, None)
        app.dependency_overrides.pop(require_engineer_or_admin, None)


def _payload(**overrides):
    payload = {
        "name": "Requested CFD MCP",
        "vendor": "Example Solver",
        "source_url": "https://example.com/cfd?tracking=private",
        "domains": ["cfd"],
        "expected_task": "Run a steady-state airflow study",
        "platform": "linux_arm64",
        "host_application": "Example CFD",
        "notes": "Needed for enclosure cooling",
        "search_context": {
            "query": "enclosure cooling",
            "filters": {"domain": "cfd"},
        },
    }
    payload.update(overrides)
    return payload


def test_structured_report_is_idempotent_and_creates_no_server_row(report_client):
    client, database = report_client
    response = client.post(
        "/api/mcp/missing-capability-reports",
        headers={"Idempotency-Key": "browser-submit-1"},
        json=_payload(),
    )
    assert response.status_code == 201
    report = response.json()
    assert report["state"] == "submitted"
    assert report["search_context"]["query"] == "enclosure cooling"
    assert report["source_url"] == "https://example.com/cfd"

    retried = client.post(
        "/api/mcp/missing-capability-reports",
        headers={"Idempotency-Key": "browser-submit-1"},
        json=_payload(),
    )
    assert retried.status_code == 201
    assert retried.json()["report_id"] == report["report_id"]
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT count(*) FROM mcp_servers").fetchone()[0] == 0
        assert (
            connection.execute(
                "SELECT count(*) FROM missing_capability_reports"
            ).fetchone()[0]
            == 1
        )


def test_report_validation_and_error_response_do_not_echo_secrets(report_client):
    client, database = report_client
    sensitive_marker = "secret-sentinel-must-not-escape"
    response = client.post(
        "/api/mcp/missing-capability-reports",
        json=_payload(search_context={"api_token": sensitive_marker}),
    )
    assert response.status_code == 422
    assert sensitive_marker not in response.text
    with sqlite3.connect(database) as connection:
        rows = connection.execute("SELECT * FROM missing_capability_reports").fetchall()
    assert rows == []


def test_missing_report_requires_engineer_or_administrator(report_client):
    client, _ = report_client

    def deny_role():
        raise HTTPException(status_code=403, detail="Engineer role required")

    app.dependency_overrides[require_engineer_or_admin] = deny_role
    response = client.post("/api/mcp/missing-capability-reports", json=_payload())
    assert response.status_code == 403


def test_legacy_endpoint_keeps_shape_but_no_longer_creates_server(report_client):
    client, database = report_client
    response = client.post(
        "/api/mcp/servers/report-missing",
        json={"name": "Legacy request", "notes": "Review this capability"},
    )
    assert response.status_code == 201
    assert response.json()["server_id"].startswith("report-")
    assert response.json()["status"] == "submitted"
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT count(*) FROM mcp_servers").fetchone()[0] == 0
        assert (
            connection.execute(
                "SELECT count(*) FROM missing_capability_reports"
            ).fetchone()[0]
            == 1
        )
