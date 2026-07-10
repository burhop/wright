import json
import sqlite3

import pytest

from api.config import DATABASE_PATH


@pytest.fixture(autouse=True)
def clean_settings(monkeypatch, tmp_path):
    monkeypatch.setenv("WRIGHT_SECRETS_PATH", str(tmp_path / "credentials.json"))
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("DELETE FROM system_settings WHERE key = 'api_keys'")
        connection.commit()


@pytest.mark.asyncio
async def test_settings_write_never_echoes_or_persists_api_key(client):
    credential_value = "test-secret-value"
    response = await client.post(
        "/api/settings",
        json={
            "llm_provider": "openai",
            "theme": "dark",
            "api_keys": {"OPENAI_API_KEY": credential_value},
        },
    )

    assert response.status_code == 200
    assert credential_value not in response.text
    read_response = await client.get("/api/settings")
    assert read_response.status_code == 200
    assert credential_value not in read_response.text
    assert read_response.json()["api_keys"]["OPENAI_API_KEY"] == ""
    assert read_response.json()["api_key_status"]["OPENAI_API_KEY"] is True

    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute("SELECT key, value FROM system_settings").fetchall()
    assert credential_value not in json.dumps(rows)


@pytest.mark.asyncio
async def test_blank_placeholders_do_not_clear_existing_key(client):
    await client.post(
        "/api/settings",
        json={
            "llm_provider": "openai",
            "theme": "dark",
            "api_keys": {"OPENAI_API_KEY": "keep-me"},
        },
    )

    await client.post(
        "/api/settings",
        json={
            "llm_provider": "openai",
            "theme": "light",
            "api_keys": {"OPENAI_API_KEY": ""},
        },
    )

    response = await client.get("/api/settings")
    assert response.json()["api_key_status"]["OPENAI_API_KEY"] is True


@pytest.mark.asyncio
async def test_explicit_removal_clears_key(client):
    await client.post(
        "/api/settings",
        json={
            "llm_provider": "openai",
            "theme": "dark",
            "api_keys": {"OPENAI_API_KEY": "remove-me"},
        },
    )
    response = await client.post(
        "/api/settings",
        json={
            "llm_provider": "openai",
            "theme": "dark",
            "api_keys": {},
            "remove_api_keys": ["OPENAI_API_KEY"],
        },
    )

    assert response.json()["api_key_status"]["OPENAI_API_KEY"] is False
