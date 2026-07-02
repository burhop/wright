import pytest
from httpx import AsyncClient
import sqlite3
from api.config import DATABASE_PATH


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
