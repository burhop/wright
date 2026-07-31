import asyncio
import io
import json

import pytest
from httpx import AsyncClient
import sqlite3
from api.config import DATABASE_PATH
from agent_adapters.health_probe import HealthProbeResult


def clear_setup_settings():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute(
        "DELETE FROM system_settings WHERE key IN ('llm_api_url', 'active_agent', 'llm_provider', 'llm_model')"
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
async def test_get_setup_status_reports_hermes_llm_summary(
    client: AsyncClient, monkeypatch, tmp_path
):
    clear_setup_settings()
    config = tmp_path / "config.yaml"
    config.write_text(
        "\n".join(
            [
                "model:",
                "  provider: openai-codex",
                "  base_url: https://chatgpt.com/backend-api/codex",
                "  default: codex-test",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "auth.json").write_text(
        '{"providers":{"openai-codex":{"tokens":{"access_token":"a","refresh_token":"r"}}}}',
        encoding="utf-8",
    )
    monkeypatch.setenv("HERMES_CONFIG_PATH", str(config))

    response = await client.get("/api/setup/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["llm_provider"] == "openai-codex"
    assert payload["llm_model"] == "codex-test"
    assert payload["llm_configured"] is True
    assert payload["llm_auth_configured"] is True


@pytest.mark.asyncio
async def test_get_setup_status_requires_valid_codex_auth(
    client: AsyncClient, monkeypatch, tmp_path
):
    clear_setup_settings()
    config = tmp_path / "config.yaml"
    config.write_text(
        "\n".join(
            [
                "model:",
                "  provider: openai-codex",
                "  base_url: https://chatgpt.com/backend-api/codex",
                "  default: codex-test",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "auth.json").write_text(
        json.dumps(
            {
                "providers": {
                    "openai-codex": {
                        "tokens": {"access_token": "a", "refresh_token": "r"}
                    }
                },
                "credential_pool": {
                    "openai-codex": [
                        {
                            "access_token": "a",
                            "refresh_token": "r",
                            "last_status": "exhausted",
                            "last_error_code": 401,
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("HERMES_CONFIG_PATH", str(config))

    response = await client.get("/api/setup/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["llm_provider"] == "openai-codex"
    assert payload["llm_configured"] is False
    assert payload["llm_auth_configured"] is False
    assert payload["is_configured"] is False


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
async def test_list_llm_providers_includes_codex(client: AsyncClient):
    response = await client.get("/api/setup/llm/providers")

    assert response.status_code == 200
    providers = {item["id"]: item for item in response.json()["providers"]}
    assert providers["openai-codex"]["auth_type"] == "oauth_device_or_seed_file"
    assert providers["custom"]["supports_seed_file"] is True


@pytest.mark.asyncio
async def test_configure_llm_provider_writes_hermes_custom_config(
    client: AsyncClient, monkeypatch, tmp_path
):
    clear_setup_settings()
    config = tmp_path / "config.yaml"
    config.write_text("terminal:\n  backend: local\n", encoding="utf-8")
    monkeypatch.setenv("HERMES_CONFIG_PATH", str(config))

    response = await client.post(
        "/api/setup/llm/configure",
        json={
            "provider": "openai-compatible",
            "base_url": "http://llm.local/v1",
            "model": "cad-model",
            "api_key": "do-not-echo",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["configured"] is True
    assert "do-not-echo" not in response.text
    loaded = config.read_text(encoding="utf-8")
    assert "http://llm.local/v1" in loaded
    assert "cad-model" in loaded
    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = dict(connection.execute("SELECT key, value FROM system_settings"))
    assert rows["llm_api_url"] == "http://llm.local/v1"
    assert rows["llm_model"] == "cad-model"


@pytest.mark.asyncio
async def test_configure_codex_reports_auth_needed(
    client: AsyncClient, monkeypatch, tmp_path
):
    clear_setup_settings()
    config = tmp_path / "config.yaml"
    config.write_text("terminal:\n  backend: local\n", encoding="utf-8")
    monkeypatch.setenv("HERMES_CONFIG_PATH", str(config))

    response = await client.post(
        "/api/setup/llm/configure",
        json={"provider": "openai-codex", "model": "codex-test"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "openai-codex"
    assert payload["configured"] is False
    assert payload["auth_configured"] is False
    assert "credentials" in payload["message"]


@pytest.mark.asyncio
async def test_configure_llm_provider_rejects_missing_url(client: AsyncClient):
    response = await client.post(
        "/api/setup/llm/configure",
        json={"provider": "openai-compatible", "model": "cad-model"},
    )

    assert response.status_code == 400
    assert "base URL" in response.json()["message"]


@pytest.mark.asyncio
async def test_codex_login_flow_surfaces_device_code(
    client: AsyncClient, monkeypatch
):
    from api.routers import setup as setup_router

    setup_router._CODEX_LOGIN_JOBS.clear()

    class FakeProcess:
        def __init__(self, *args, **kwargs):
            self.stdout = io.StringIO(
                "\n".join(
                    [
                        "Signing in to OpenAI Codex...",
                        "  1. Open this URL in your browser:",
                        "     \x1b[94mhttps://auth.openai.com/codex/device\x1b[0m",
                        "  2. Enter this code:",
                        "     \x1b[94mABCD-EFGH\x1b[0m",
                        "Waiting for sign-in... (press Ctrl+C to cancel)",
                        "Login successful!",
                    ]
                )
                + "\n"
            )
            self.returncode = 0

        def wait(self):
            return self.returncode

    monkeypatch.setattr("api.routers.setup.subprocess.Popen", FakeProcess)

    response = await client.post("/api/setup/llm/codex/start")
    assert response.status_code == 200
    session_id = response.json()["session_id"]

    payload = None
    for _ in range(10):
        await asyncio.sleep(0.02)
        status_response = await client.get(f"/api/setup/llm/codex/status/{session_id}")
        assert status_response.status_code == 200
        payload = status_response.json()
        if payload["status"] == "succeeded":
            break

    assert payload is not None
    assert payload["status"] == "succeeded"
    assert payload["verification_url"] == "https://auth.openai.com/codex/device"
    assert payload["user_code"] == "ABCD-EFGH"


@pytest.mark.asyncio
async def test_codex_login_status_404_for_unknown_session(client: AsyncClient):
    response = await client.get("/api/setup/llm/codex/status/not-a-session")

    assert response.status_code == 404
    assert "not found" in response.json()["message"]


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
