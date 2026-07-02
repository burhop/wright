import httpx
import json
import pytest
import respx

from agent_adapters.hermes import HermesAdapter
from agent_adapters.base import AgentChatRequest


@pytest.fixture(autouse=True)
def isolate_host_hermes_config(monkeypatch, tmp_path):
    monkeypatch.delenv("HERMES_API_BASE_URL", raising=False)
    monkeypatch.delenv("HERMES_API_KEY", raising=False)
    monkeypatch.delenv("API_SERVER_KEY", raising=False)
    monkeypatch.delenv("LLM_API_URL", raising=False)
    monkeypatch.delenv("LLM_HEALTH_URL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_MODEL", raising=False)
    monkeypatch.setenv("HERMES_CONFIG_PATH", str(tmp_path / "missing-config.yaml"))
    monkeypatch.setenv("HERMES_ENV_PATH", str(tmp_path / "missing.env"))


@pytest.mark.asyncio
@respx.mock
async def test_hermes_health_omits_auth_header_when_key_empty():
    route = respx.get("http://127.0.0.1:8642/health").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    adapter = HermesAdapter("http://127.0.0.1:8642", "")

    result = await adapter.check_health()

    assert result["state"] == "connected"
    assert result["baseUrl"] == "http://127.0.0.1:8642"
    assert "authorization" not in route.calls.last.request.headers


@pytest.mark.asyncio
@respx.mock
async def test_hermes_health_reports_base_url_and_error_on_failure(monkeypatch):
    monkeypatch.setenv("HERMES_API_DISABLE_DEFAULT_CANDIDATES", "1")
    respx.get("http://127.0.0.1:8642/health").mock(
        return_value=httpx.Response(404, text="missing")
    )
    adapter = HermesAdapter("http://127.0.0.1:8642", "secret")

    result = await adapter.check_health()

    assert result["state"] == "disconnected"
    assert result["baseUrl"] == "http://127.0.0.1:8642"
    assert "HTTP 404" in result["error"]


@pytest.mark.asyncio
@respx.mock
async def test_hermes_health_falls_back_to_candidate_url(monkeypatch):
    monkeypatch.setenv(
        "HERMES_API_CANDIDATES", "http://127.0.0.1:9999,http://127.0.0.1:3001"
    )
    respx.get("http://127.0.0.1:8642/health").mock(
        return_value=httpx.Response(404, text="missing")
    )
    respx.get("http://127.0.0.1:9999/health").mock(
        return_value=httpx.Response(404, text="missing")
    )
    respx.get("http://127.0.0.1:3001/health").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    adapter = HermesAdapter("http://127.0.0.1:8642", "")

    result = await adapter.check_health()

    assert result["state"] == "connected"
    assert result["baseUrl"] == "http://127.0.0.1:3001"
    assert adapter.base_url == "http://127.0.0.1:3001"


@pytest.mark.asyncio
@respx.mock
async def test_llm_backend_health_checks_configured_provider(monkeypatch, tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "\n".join(
            [
                "model:",
                "  base_url: http://llm.local/v1",
                "  default: test-model",
                "custom_providers:",
                "- base_url: http://llm.local/v1",
                "  api_key: test-key",
                "  model: test-model",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("HERMES_CONFIG_PATH", str(config_file))

    llm_route = respx.get("http://llm.local/v1/models").mock(
        return_value=httpx.Response(200, json={"data": []})
    )
    adapter = HermesAdapter("http://127.0.0.1:8642", "")

    result = await adapter.check_llm_backend_health()

    assert result["state"] == "connected"
    assert result["baseUrl"] == "http://llm.local/v1"
    assert llm_route.called
    assert llm_route.calls.last.request.headers["authorization"] == "Bearer test-key"


@pytest.mark.asyncio
@respx.mock
async def test_llm_backend_health_reports_provider_failure(monkeypatch, tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "\n".join(
            [
                "model:",
                "  base_url: http://llm.local/v1",
                "  default: test-model",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("HERMES_CONFIG_PATH", str(config_file))

    respx.get("http://llm.local/v1/models").mock(
        return_value=httpx.Response(503, text="offline")
    )
    respx.get("http://llm.local/health").mock(
        return_value=httpx.Response(404, text="missing")
    )
    adapter = HermesAdapter("http://127.0.0.1:8642", "")

    result = await adapter.check_llm_backend_health()

    assert result["state"] == "disconnected"
    assert result["baseUrl"] == "http://llm.local/v1"
    assert "http://llm.local" in result["error"]


@pytest.mark.asyncio
async def test_llm_backend_health_accepts_openai_codex_auth(monkeypatch, tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "\n".join(
            [
                "model:",
                "  provider: openai-codex",
                "  base_url: https://chatgpt.com/backend-api/codex",
                "  default: gpt-5.5",
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "auth.json").write_text(
        json.dumps(
            {
                "providers": {
                    "openai-codex": {
                        "tokens": {"access_token": "codex-token"},
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("HERMES_CONFIG_PATH", str(config_file))
    adapter = HermesAdapter("http://127.0.0.1:8642", "")

    result = await adapter.check_llm_backend_health()

    assert result["state"] == "connected"
    assert result["baseUrl"] == "https://chatgpt.com/backend-api/codex"


@pytest.mark.asyncio
async def test_llm_backend_health_reports_missing_openai_codex_auth(
    monkeypatch, tmp_path
):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "\n".join(
            [
                "model:",
                "  provider: openai-codex",
                "  base_url: https://chatgpt.com/backend-api/codex",
                "  default: gpt-5.5",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("HERMES_CONFIG_PATH", str(config_file))
    adapter = HermesAdapter("http://127.0.0.1:8642", "")

    result = await adapter.check_llm_backend_health()

    assert result["state"] == "disconnected"
    assert "openai-codex credentials" in result["error"]


@pytest.mark.asyncio
@respx.mock
async def test_hermes_health_does_not_include_llm_backend_status(monkeypatch, tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "\n".join(
            [
                "model:",
                "  base_url: http://llm.local/v1",
                "  default: test-model",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("HERMES_CONFIG_PATH", str(config_file))

    respx.get("http://127.0.0.1:8642/health").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    adapter = HermesAdapter("http://127.0.0.1:8642", "")

    result = await adapter.check_health()

    assert result["state"] == "connected"
    assert result["baseUrl"] == "http://127.0.0.1:8642"


@pytest.mark.asyncio
@respx.mock
async def test_hermes_list_sessions_falls_back_to_candidate_url(monkeypatch):
    monkeypatch.setenv("HERMES_API_CANDIDATES", "http://127.0.0.1:3001")
    respx.get("http://127.0.0.1:8642/api/sessions").mock(
        return_value=httpx.Response(404, text="missing")
    )
    respx.get("http://127.0.0.1:3001/api/sessions").mock(
        return_value=httpx.Response(
            200,
            json={
                "sessions": [
                    {
                        "id": "session-1",
                        "title": "Session One",
                        "created_at": 1000,
                        "updated_at": 2000,
                        "message_count": 3,
                    }
                ]
            },
        )
    )
    adapter = HermesAdapter("http://127.0.0.1:8642", "")

    sessions = await adapter.list_sessions()

    assert len(sessions) == 1
    assert sessions[0].session_id == "session-1"
    assert adapter.base_url == "http://127.0.0.1:3001"


def test_hermes_candidate_urls_do_not_use_ui_log_ports(monkeypatch, tmp_path):
    local_app_data = tmp_path / "LocalAppData"
    log_dir = local_app_data / "hermes" / "logs"
    log_dir.mkdir(parents=True)
    (log_dir / "desktop.log").write_text(
        "[hermes] ui listening on port 54608",
        encoding="utf-8",
    )
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))
    monkeypatch.setenv("HERMES_API_DISABLE_DEFAULT_CANDIDATES", "1")

    adapter = HermesAdapter("http://127.0.0.1:8642", "")

    assert adapter._candidate_base_urls() == ["http://127.0.0.1:8642"]


@pytest.mark.asyncio
async def test_hermes_messages_include_wright_onshape_search_hint(monkeypatch):
    adapter = HermesAdapter("http://127.0.0.1:8642", "")

    async def fake_history(_session_id):
        return []

    async def fake_workspace(_session_id):
        return "/home/agent/wright/3d-printing"

    monkeypatch.setattr(adapter, "get_chat_history", fake_history)
    monkeypatch.setattr(adapter, "get_session_workspace", fake_workspace)

    messages = await adapter._build_messages(
        AgentChatRequest(
            session_id="session-1",
            message="Export the iPhone stand as an STL.",
        )
    )

    assert messages[0]["role"] == "system"
    assert "jarvisonshapemcp__search_documents" in messages[0]["content"]
    assert "prefer the most recently modified" in messages[0]["content"]
    assert messages[-1]["role"] == "user"
    assert "[Workspace::v1: /home/agent/wright/3d-printing]" in messages[-1]["content"]


@pytest.mark.asyncio
@respx.mock
async def test_hermes_list_sessions_explains_gateway_is_required(monkeypatch):
    monkeypatch.setenv("HERMES_API_DISABLE_DEFAULT_CANDIDATES", "1")
    respx.get("http://127.0.0.1:8642/api/sessions").mock(
        return_value=httpx.Response(404, text="missing")
    )
    adapter = HermesAdapter("http://127.0.0.1:8642", "")

    with pytest.raises(RuntimeError) as exc_info:
        await adapter.list_sessions()

    message = str(exc_info.value)
    assert "Hermes API Server is not reachable" in message
    assert "hermes gateway run" in message
    assert "%LOCALAPPDATA%\\hermes\\.env" in message


@pytest.mark.asyncio
@respx.mock
async def test_hermes_health_does_not_accept_html_shell(monkeypatch):
    monkeypatch.setenv("HERMES_API_DISABLE_DEFAULT_CANDIDATES", "1")
    respx.get("http://127.0.0.1:50350/health").mock(
        return_value=httpx.Response(
            200,
            html="<!doctype html><html><body>Hermes Desktop</body></html>",
        )
    )
    adapter = HermesAdapter("http://127.0.0.1:50350", "")

    result = await adapter.check_health()

    assert result["state"] == "disconnected"
    assert "returned HTML, not Hermes API health" in result["error"]
