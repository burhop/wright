import pytest

from agent_adapters import HermesAdapter, OpenClawStubEngine
from agent_adapters.registry import (
    AgentEngineRegistry,
    UnsupportedAgentRuntimeError,
    create_agent_engine,
    default_agent_registry,
    resolve_agent_api_settings,
)


@pytest.fixture(autouse=True)
def isolate_host_hermes_config(monkeypatch, tmp_path):
    monkeypatch.delenv("HERMES_API_BASE_URL", raising=False)
    monkeypatch.delenv("HERMES_API_KEY", raising=False)
    monkeypatch.delenv("API_SERVER_KEY", raising=False)
    monkeypatch.setenv("HERMES_CONFIG_PATH", str(tmp_path / "missing-config.yaml"))
    monkeypatch.setenv("HERMES_ENV_PATH", str(tmp_path / "missing.env"))


def test_default_registry_selects_hermes_provider():
    registry = default_agent_registry()

    provider = registry.resolve_provider(None)

    assert provider.name == "hermes"
    assert provider.is_default is True
    assert provider.supported is True


def test_explicit_hermes_selection_creates_hermes_adapter():
    engine = create_agent_engine("hermes", db_path="test.db")

    assert isinstance(engine, HermesAdapter)
    assert engine.db_path == "test.db"


def test_blank_selection_uses_hermes_default():
    engine = create_agent_engine("  ", db_path="test.db")

    assert isinstance(engine, HermesAdapter)


def test_agent_api_settings_resolve_through_registry():
    settings = resolve_agent_api_settings(
        "hermes",
        env={
            "HERMES_API_BASE_URL": "http://127.0.0.1:7777/",
            "HERMES_API_KEY": "explicit-key",
        },
    )

    assert settings.provider_name == "hermes"
    assert settings.base_url == "http://127.0.0.1:7777"
    assert settings.api_key == "explicit-key"


def test_unknown_agent_selection_is_rejected():
    registry = default_agent_registry()

    with pytest.raises(UnsupportedAgentRuntimeError) as exc_info:
        registry.resolve_provider("unknown-agent")

    assert "Unsupported agent runtime" in str(exc_info.value)


def test_openclaw_stub_is_selectable_without_hermes():
    registry = default_agent_registry()

    assert "openclaw" in registry.known_names()
    assert "openclaw" in registry.supported_names()
    provider = registry.resolve_provider("openclaw")
    engine = provider.create_engine("test.db")

    assert provider.name == "openclaw"
    assert provider.support_level == "stub"
    assert isinstance(engine, OpenClawStubEngine)
    assert engine.db_path == "test.db"


def test_registry_requires_single_default_provider():
    with pytest.raises(ValueError):
        AgentEngineRegistry([])
