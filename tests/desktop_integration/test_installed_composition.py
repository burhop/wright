"""Installed desktop composition preserves normal auth and canonical owners."""

import asyncio
import hashlib
import json
import secrets
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI

from api.desktop.composition import DesktopBoundaryMiddleware, configure, enabled
from api.desktop import mcp_bridge
from api.security import ControlPlaneSecurityMiddleware, SecuritySettings
from data_vault import upgrade_database


@pytest.fixture
def candidate(tmp_path, monkeypatch):
    monkeypatch.setenv("WRIGHT_DESKTOP_ENABLED", "1")
    monkeypatch.setenv("WRIGHT_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("WRIGHT_MCP_OAUTH_FLOW", "device_code")
    database = str(tmp_path / "wright.db")
    upgrade_database(database)
    app = FastAPI()
    token = secrets.token_urlsafe(32)
    app.state.security_settings = SecuritySettings("enforced", token, (), "127.0.0.1")

    @app.get("/{path:path}")
    async def frontend(path: str):
        return {"frontend": path}

    configure(app, SimpleNamespace(db_path=database))
    app.add_middleware(DesktopBoundaryMiddleware)
    app.add_middleware(ControlPlaneSecurityMiddleware)
    return app, token, tmp_path


def test_default_does_not_replace_existing_agent_or_routes(monkeypatch):
    monkeypatch.delenv("WRIGHT_DESKTOP_ENABLED", raising=False)
    app = FastAPI()
    original = object()
    app.state.agent_engine = original
    routes = list(app.router.routes)
    configure(app, None)
    assert not enabled()
    assert app.state.agent_engine is original
    assert app.router.routes == routes
    assert not hasattr(app.state, "desktop_backend")
    monkeypatch.setenv("WRIGHT_DESKTOP_ENABLED", "yes")
    with pytest.raises(ValueError, match="must be 0 or 1"):
        enabled()


@pytest.mark.parametrize(
    "mode,host", [("compat", "127.0.0.1"), ("enforced", "0.0.0.0")]
)
def test_opt_in_requires_authenticated_loopback(monkeypatch, mode, host):
    monkeypatch.setenv("WRIGHT_DESKTOP_ENABLED", "1")
    app = FastAPI()
    app.state.security_settings = SecuritySettings(mode, None, (), host)
    with pytest.raises(ValueError, match="authenticated loopback"):
        configure(app, None)
    assert not hasattr(app.state, "desktop_backend")


@pytest.mark.parametrize("mode", ["authorization_code", "device_code"])
def test_public_signin_mode_preserves_canonical_runtime_provenance(tmp_path, mode):
    from api.desktop.desktop_backend import DesktopBackend
    from core.process_validation import canonical_digest

    database = str(tmp_path / "wright.db")
    upgrade_database(database)
    backend = DesktopBackend(
        SimpleNamespace(db_path=database), tmp_path, 0, remote_signin_mode=mode
    )
    metadata = json.loads((tmp_path / "desktop-versions.json").read_text())
    assert metadata["remote_oauth_flow"] == mode
    assert metadata == backend.runtime
    assert (
        backend.binding.connection_id
        == "wright-desktop-prototype:" + canonical_digest(metadata)
    )


def test_unknown_signin_mode_is_rejected_before_persistence_without_echo(tmp_path):
    from api.desktop.desktop_backend import DesktopBackend

    invalid = "not-a-supported-public-mode"
    with pytest.raises(ValueError, match="^Unsupported remote OAuth flow$") as failure:
        DesktopBackend(None, tmp_path, 0, remote_signin_mode=invalid)
    assert invalid not in str(failure.value)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.asyncio
async def test_metadata_is_authenticated_uses_same_owners_and_no_private_descriptors(
    candidate,
):
    app, token, state = candidate
    backend = app.state.desktop_backend
    assert app.state.agent_engine is backend
    assert app.state.mcp_device_authorization_presenter == backend.oauth.present_device
    assert backend.runtime["remote_oauth_flow"] == "device_code"
    assert not (state / "desktop-binding.json").exists()
    assert not (state / "desktop-versions.json").exists()
    assert not (state / "preview.json").exists()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        denied = await client.get("/api/desktop/configuration")
        assert denied.status_code == 401
        result = await client.get(
            "/api/desktop/configuration", headers={"Authorization": "Bearer " + token}
        )
        assert result.status_code == 200
        document = result.json()
        assert document["binding"] == backend.binding.model_dump(mode="json")
        assert document["versions"] == backend.runtime
        assert token not in result.text
        assert (
            document["versions"]["files"]["transport"]
            == hashlib.sha256(Path(mcp_bridge.__file__).read_bytes()).hexdigest()
        )
        # A runtime with desktop reasoning must not silently dispatch API chat to Hermes.
        rejected = await client.post(
            "/api/agent/chat", json={}, headers={"Authorization": "Bearer " + token}
        )
        assert rejected.status_code == 503
        assert rejected.json()["detail"]["code"] == "DESKTOP_BRIDGE_NOT_CONNECTED"
        invalid = await client.post(
            "/api/workspace/process-interfaces/readiness",
            content="{",
            headers={
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json",
            },
        )
        assert invalid.status_code == 400
        assert "valid JSON" in invalid.json()["detail"]


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com",
        "http://127.0.0.1:8000/?token=bad",
        "http://user@127.0.0.1:8000",
        "http://127.0.0.1:8000/api",
    ],
)
def test_invalid_destination_rejected_before_credentials_or_network(url, tmp_path):
    with pytest.raises(ValueError, match="loopback Wright API"):
        mcp_bridge.WrightDesktopClient.from_runtime(
            api_url=url, token_path=tmp_path / "absent"
        )


def test_installed_client_negotiates_frozen_configuration(candidate, monkeypatch):
    app, token, state = candidate
    backend = app.state.desktop_backend
    token_path = state / "control-plane.token"
    token_path.write_text(token)
    token_path.chmod(0o600)
    configuration = {
        "binding": backend.binding.model_dump(mode="json"),
        "versions": backend.runtime,
    }
    requests = []

    def exchange(request):
        requests.append(request)
        assert request.headers["Authorization"] == "Bearer " + token
        return httpx.Response(200, json=configuration)

    real_client = httpx.Client
    monkeypatch.setattr(
        mcp_bridge.httpx,
        "Client",
        lambda **options: real_client(
            transport=httpx.MockTransport(exchange), **options
        ),
    )
    client = mcp_bridge.WrightDesktopClient.from_runtime(
        api_url="http://127.0.0.1:8000", token_path=token_path
    )
    try:
        assert client.binding == configuration["binding"]
        assert len(requests) == 1
        assert requests[0].url.path == "/api/desktop/configuration"
        configuration["versions"]["mcp_sdk"] = "different"
        with pytest.raises(ValueError, match="SDK version differs"):
            mcp_bridge.WrightDesktopClient.from_runtime(
                api_url="http://127.0.0.1:8000", token_path=token_path
            )
        configuration.clear()
        with pytest.raises(ValueError, match="configuration is invalid"):
            mcp_bridge.WrightDesktopClient.from_runtime(
                api_url="http://127.0.0.1:8000", token_path=token_path
            )
    finally:
        asyncio.run(client.http.aclose())
    assert not list(state.glob("desktop-*.json"))
    assert token not in json.dumps(backend.runtime)
