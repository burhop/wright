import httpx
import pytest
import respx

from agent_adapters.hermes import HermesAdapter


@pytest.fixture(autouse=True)
def isolate_host_hermes_config(monkeypatch, tmp_path):
    monkeypatch.delenv("HERMES_API_BASE_URL", raising=False)
    monkeypatch.delenv("HERMES_API_KEY", raising=False)
    monkeypatch.delenv("API_SERVER_KEY", raising=False)
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
    monkeypatch.setenv("HERMES_API_CANDIDATES", "http://127.0.0.1:9999,http://127.0.0.1:3001")
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
