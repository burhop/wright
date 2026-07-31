from types import SimpleNamespace

import pytest


@pytest.mark.asyncio
async def test_agent_health_includes_connection_details(client, mock_agent_engine):
    async def disconnected_health():
        return {
            "state": "disconnected",
            "latencyMs": 0.0,
            "baseUrl": "http://127.0.0.1:8642",
            "error": "connection refused",
        }

    mock_agent_engine.check_health = disconnected_health

    response = await client.get("/api/agent/health")

    assert response.status_code == 200
    assert response.json() == {
        "state": "disconnected",
        "latencyMs": 0.0,
        "baseUrl": "http://127.0.0.1:8642",
        "error": "connection refused",
    }


@pytest.mark.asyncio
async def test_agent_health_reports_unknown_during_workspace_gateway_refresh(
    client, mock_agent_engine
):
    from api.main import app

    async def should_not_check_live_gateway():
        raise AssertionError("health should not probe Hermes during planned refresh")

    mock_agent_engine.base_url = "http://127.0.0.1:8642"
    mock_agent_engine.check_health = should_not_check_live_gateway
    app.state.agent_sync_manager = SimpleNamespace(
        active_agent="hermes",
        gateway_refresh_in_progress=True,
        gateway_refresh_pending=True,
    )

    response = await client.get("/api/agent/health")

    assert response.status_code == 200
    assert response.json() == {
        "state": "unknown",
        "latencyMs": 0.0,
        "baseUrl": "http://127.0.0.1:8642",
        "error": "Hermes gateway is refreshing workspace tools",
    }


@pytest.mark.asyncio
async def test_inference_health_uses_agent_llm_backend_check(client, mock_agent_engine):
    async def llm_backend_health():
        return {
            "state": "disconnected",
            "latencyMs": 12.5,
            "baseUrl": "http://llm.local/v1",
            "error": "LLM backend is offline",
        }

    mock_agent_engine.check_llm_backend_health = llm_backend_health

    response = await client.get("/api/inference/health")

    assert response.status_code == 200
    assert response.json() == {
        "state": "disconnected",
        "latencyMs": 12.5,
        "baseUrl": "http://llm.local/v1",
        "error": "LLM backend is offline",
    }


@pytest.mark.asyncio
async def test_active_agent_defaults_to_hermes(client):
    from api.main import app

    app.state.agent_sync_manager.active_agent = "hermes"

    response = await client.get("/api/agent/active")

    assert response.status_code == 200
    assert response.json() == {"agent": "hermes"}


@pytest.mark.asyncio
async def test_active_agent_rejects_unknown_runtime(client):
    from api.main import app

    app.state.agent_sync_manager.active_agent = "hermes"

    response = await client.post(
        "/api/agent/active",
        json={"agent": "unknown-agent"},
    )

    assert response.status_code == 400
    assert response.json()["message"] == "Unsupported agent runtime: unknown-agent"
    assert app.state.agent_sync_manager.active_agent == "hermes"


@pytest.mark.asyncio
async def test_active_agent_accepts_openclaw_stub_runtime(client):
    from api.main import app

    app.state.agent_sync_manager.active_agent = "hermes"

    response = await client.post(
        "/api/agent/active",
        json={"agent": "openclaw"},
    )

    assert response.status_code == 200
    assert response.json() == {"agent": "openclaw"}
    assert app.state.agent_sync_manager.active_agent == "openclaw"
