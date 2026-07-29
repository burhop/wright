import pytest
from httpx import AsyncClient
import sqlite3
from api.config import DATABASE_PATH
from agent_adapters.health_probe import HealthProbeResult


def clear_setup_settings():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute(
        "DELETE FROM system_settings WHERE key IN ('llm_api_url', 'active_agent')"
    )
    conn.commit()
    conn.close()


@pytest.mark.asyncio
async def test_get_setup_status_theme(client: AsyncClient, monkeypatch):
    # Test default theme value
    monkeypatch.setenv("UI_THEME", "dark")
    response = await client.get("/api/setup/status")
    assert response.status_code == 200
    data = response.json()
    assert "theme" in data
    assert data["theme"] == "dark"


@pytest.mark.asyncio
async def test_get_setup_status_theme_light(client: AsyncClient, monkeypatch):
    # Test light theme override
    monkeypatch.setenv("UI_THEME", "light")
    response = await client.get("/api/setup/status")
    assert response.status_code == 200
    data = response.json()
    assert "theme" in data
    assert data["theme"] == "light"


@pytest.mark.asyncio
async def test_get_setup_status_is_configured_when_launched_by_hermes(
    client: AsyncClient, monkeypatch
):
    clear_setup_settings()
    monkeypatch.delenv("LLM_API_URL", raising=False)
    monkeypatch.delenv("LLM_HEALTH_URL", raising=False)
    monkeypatch.setenv("WRIGHT_LAUNCHED_BY_HERMES", "1")

    response = await client.get("/api/setup/status")

    assert response.status_code == 200
    data = response.json()
    assert data["active_agent"] == "hermes"
    assert data["llm_api_url"] == ""
    assert data["is_configured"] is True


@pytest.mark.asyncio
async def test_configure_allows_empty_llm_url_for_hermes(client: AsyncClient):
    clear_setup_settings()

    response = await client.post(
        "/api/setup/configure",
        json={"llm_api_url": "", "active_agent": "hermes"},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_configure_rejects_unknown_agent(client: AsyncClient):
    clear_setup_settings()

    response = await client.post(
        "/api/setup/configure",
        json={"llm_api_url": "http://llm.local/v1", "active_agent": "unknown-agent"},
    )

    assert response.status_code == 400
    assert response.json()["message"] == "Unsupported agent runtime: unknown-agent"


@pytest.mark.asyncio
async def test_configure_accepts_openclaw_stub_agent(client: AsyncClient):
    clear_setup_settings()

    response = await client.post(
        "/api/setup/configure",
        json={"llm_api_url": "http://llm.local/v1", "active_agent": "openclaw"},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_custom_health_delegates_with_configured_local_origins(
    client: AsyncClient, monkeypatch
):
    captured: dict[str, object] = {}

    async def fake_probe(url: str, *, trusted_local_origins):
        captured["url"] = url
        captured["origins"] = tuple(trusted_local_origins)
        return HealthProbeResult(status="healthy", latency_ms=12.5)

    monkeypatch.setattr("api.routers.setup.probe_health", fake_probe)
    monkeypatch.setattr(
        "api.config.get_llm_api_url", lambda: "http://192.168.1.20:11434/v1"
    )
    monkeypatch.setattr(
        "api.config.get_llm_health_url", lambda: "http://192.168.1.20:11434/health"
    )

    response = await client.get(
        "/api/setup/health", params={"url": "http://192.168.1.20:11434/v1"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "latency_ms": 12.5,
        "error": None,
    }
    assert captured == {
        "url": "http://192.168.1.20:11434/v1",
        "origins": (
            "http://192.168.1.20:11434/v1",
            "http://192.168.1.20:11434/health",
        ),
    }


@pytest.mark.asyncio
async def test_custom_health_returns_only_sanitized_probe_error(
    client: AsyncClient, monkeypatch
):
    async def fake_probe(url: str, *, trusted_local_origins):
        return HealthProbeResult(
            status="unhealthy",
            latency_ms=1.0,
            error="URL is not permitted",
        )

    monkeypatch.setattr("api.routers.setup.probe_health", fake_probe)

    response = await client.get(
        "/api/setup/health",
        params={"url": "http://169.254.169.254/latest/meta-data"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "unhealthy"
    assert payload["error"] == "URL is not permitted"
    assert "169.254" not in payload["error"]
