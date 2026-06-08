import pytest
from httpx import AsyncClient


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
