from api.config import get_ui_theme
import importlib


def test_get_ui_theme_default(monkeypatch):
    monkeypatch.delenv("UI_THEME", raising=False)
    assert get_ui_theme() == "dark"


def test_get_ui_theme_custom(monkeypatch):
    monkeypatch.setenv("UI_THEME", "light")
    assert get_ui_theme() == "light"


def test_hermes_api_key_falls_back_to_api_server_key(monkeypatch):
    import api.config as config

    monkeypatch.delenv("HERMES_API_KEY", raising=False)
    monkeypatch.setenv("API_SERVER_KEY", "wright-local-dev")

    reloaded = importlib.reload(config)
    try:
        assert reloaded.HERMES_API_KEY == "wright-local-dev"
    finally:
        importlib.reload(config)


def test_llm_api_url_is_unconfigured_without_env_or_database(monkeypatch):
    import api.config as config

    monkeypatch.delenv("LLM_API_URL", raising=False)
    monkeypatch.delenv("LLM_HEALTH_URL", raising=False)

    reloaded = importlib.reload(config)
    try:
        assert reloaded.get_llm_api_url() == ""
        assert reloaded.get_llm_health_url() == ""
    finally:
        importlib.reload(config)


def test_llm_health_url_derived_from_v1_api_url(monkeypatch):
    import api.config as config

    monkeypatch.setenv("LLM_API_URL", "http://192.168.1.165:8000/v1")
    monkeypatch.delenv("LLM_HEALTH_URL", raising=False)

    reloaded = importlib.reload(config)
    try:
        assert reloaded.get_llm_api_url() == "http://192.168.1.165:8000/v1"
        assert reloaded.get_llm_health_url() == "http://192.168.1.165:8000/health"
    finally:
        importlib.reload(config)
