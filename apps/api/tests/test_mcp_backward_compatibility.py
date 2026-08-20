from __future__ import annotations

from datetime import UTC, datetime
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace

import pytest
from core.secrets import configure_default_secret_provider
from data_vault import upgrade_database
from data_vault.secret_provider import (
    FileSecretProvider,
    create_default_secret_provider,
)
from fastapi.testclient import TestClient
from tool_registry import McpEngine
from tool_registry.capability_services import CapabilityServiceDependencies
from tool_registry.catalog_reconcile import reconcile_active_engineering_catalog
from tool_registry.secrets import write_secrets

from api.main import app
from api.services.mcp_services import McpApiService, get_mcp_api_service

_FIXTURE_PATH = (
    Path(__file__).parents[3]
    / "packages"
    / "data_vault"
    / "tests"
    / "capability_library_v12.py"
)
_FIXTURE_SPEC = spec_from_file_location("api_capability_library_v12", _FIXTURE_PATH)
assert _FIXTURE_SPEC is not None and _FIXTURE_SPEC.loader is not None
_FIXTURE = module_from_spec(_FIXTURE_SPEC)
_FIXTURE_SPEC.loader.exec_module(_FIXTURE)
CUSTOM_SERVER_ID = _FIXTURE.CUSTOM_SERVER_ID
LEGACY_CATALOG_SERVER_ID = _FIXTURE.LEGACY_CATALOG_SERVER_ID
LEGACY_TOOL_ID = _FIXTURE.LEGACY_TOOL_ID
create_capability_library_v12_database = _FIXTURE.create_capability_library_v12_database


@pytest.fixture
def migrated_legacy_client(tmp_path, monkeypatch):
    database = create_capability_library_v12_database(tmp_path / "legacy-api.db")
    upgrade_database(database)
    count, diagnostic = reconcile_active_engineering_catalog(str(database))
    assert count == 70
    assert diagnostic is None

    configure_default_secret_provider(
        lambda: FileSecretProvider(tmp_path / "legacy-secrets.json")
    )
    write_secrets(LEGACY_CATALOG_SERVER_ID, {"APS_CLIENT_ID": "never-return-this"})
    monkeypatch.setattr(
        "api.services.mcp_services.sync_mcp_server_to_wright_gateway",
        lambda _server: None,
    )
    service = McpApiService(
        McpEngine(str(database)),
        SimpleNamespace(),
        CapabilityServiceDependencies(
            database_path=database,
            clock=lambda: datetime(2026, 8, 12, 12, 0, tzinfo=UTC),
        ),
    )
    app.dependency_overrides[get_mcp_api_service] = lambda: service
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_mcp_api_service, None)
        configure_default_secret_provider(create_default_secret_provider)


def test_migrated_v12_legacy_endpoints_keep_shapes_and_user_rows(
    migrated_legacy_client,
) -> None:
    client = migrated_legacy_client

    listed = client.get("/api/mcp/servers")
    assert listed.status_code == 200
    assert set(listed.json()) == {"servers"}
    servers = listed.json()["servers"]
    assert {LEGACY_CATALOG_SERVER_ID, CUSTOM_SERVER_ID}.issubset(
        {server["server_id"] for server in servers}
    )
    legacy = next(
        server for server in servers if server["server_id"] == LEGACY_CATALOG_SERVER_ID
    )
    assert legacy["is_installed"] is True
    assert legacy["is_active"] is False
    assert legacy["installed_version"] == "2.4.0"

    tools = client.get("/api/mcp/tools")
    assert tools.status_code == 200
    assert set(tools.json()) == {"tools"}
    legacy_tool = next(
        tool for tool in tools.json()["tools"] if tool["tool_id"] == LEGACY_TOOL_ID
    )
    assert legacy_tool["is_enabled"] is False

    credentials = client.get(f"/api/mcp/servers/{LEGACY_CATALOG_SERVER_ID}/credentials")
    assert credentials.status_code == 200
    assert credentials.json()["server_id"] == LEGACY_CATALOG_SERVER_ID
    assert credentials.json()["configured"]["APS_CLIENT_ID"] is True
    assert "never-return-this" not in credentials.text

    tool_toggle = client.patch(
        f"/api/mcp/tools/{LEGACY_TOOL_ID}", json={"is_enabled": True}
    )
    assert tool_toggle.status_code == 200
    assert tool_toggle.json() == {"tool_id": LEGACY_TOOL_ID, "is_enabled": True}

    installed = client.post(f"/api/mcp/servers/{CUSTOM_SERVER_ID}/install")
    assert installed.status_code == 200
    assert set(installed.json()) == {
        "server_id",
        "is_installed",
        "status",
        "error_message",
        "type",
    }
    assert installed.json()["server_id"] == CUSTOM_SERVER_ID

    stopped = client.patch(
        f"/api/mcp/servers/{LEGACY_CATALOG_SERVER_ID}",
        json={"is_active": False},
    )
    assert stopped.status_code == 200
    assert set(stopped.json()) == {
        "server_id",
        "is_active",
        "status",
        "error_message",
        "type",
    }
    assert stopped.json()["is_active"] is False


@pytest.mark.asyncio
async def test_explicit_activation_reuses_recorded_server_approvals(
    monkeypatch,
) -> None:
    captured = {}
    server = SimpleNamespace(
        server_id="remote",
        approval_gates=("network_access_approval", "cloud_data_approval"),
    )

    async def toggle(engine, server_id, is_active, *, approval_context=None):
        captured["context"] = approval_context
        return SimpleNamespace(
            server_id=server_id,
            is_active=is_active,
            status="active",
            error_message=None,
            type="sse",
        )

    monkeypatch.setattr("api.services.mcp_services.get_server", lambda *_: server)
    monkeypatch.setattr(
        "api.services.mcp_services.registry_services.toggle_server_activation", toggle
    )
    monkeypatch.setattr(
        "api.services.mcp_services.sync_mcp_server_to_wright_gateway", lambda *_: None
    )
    service = McpApiService(SimpleNamespace(db_path="state.db"), SimpleNamespace())

    await service.toggle_server_activation("remote", True)

    assert captured["context"].machine_approvals == {
        "network_access_approval",
        "cloud_data_approval",
    }
