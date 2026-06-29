import subprocess

from agent_adapters.hermes_config import (
    hermes_config_path,
    hermes_env_path,
    parse_env_file,
    parse_top_level_config_file,
    resolve_hermes_api_settings,
)


def test_parse_env_file_reads_api_server_values(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join([
            "# Hermes secrets",
            "API_SERVER_HOST=0.0.0.0",
            "API_SERVER_PORT=8765",
            "API_SERVER_KEY=\"secret key\"",
            "export HERMES_API_KEY='explicit'",
        ]),
        encoding="utf-8",
    )

    values = parse_env_file(env_file)

    assert values["API_SERVER_HOST"] == "0.0.0.0"
    assert values["API_SERVER_PORT"] == "8765"
    assert values["API_SERVER_KEY"] == "secret key"
    assert values["HERMES_API_KEY"] == "explicit"


def test_parse_top_level_config_file_reads_api_server_values(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "\n".join([
            "API_SERVER_HOST: 0.0.0.0",
            "API_SERVER_PORT: 8765",
            "API_SERVER_KEY: secret",
            "model:",
            "  default: ignored",
        ]),
        encoding="utf-8",
    )

    values = parse_top_level_config_file(config_file)

    assert values == {
        "API_SERVER_HOST": "0.0.0.0",
        "API_SERVER_PORT": "8765",
        "API_SERVER_KEY": "secret",
    }


def test_hermes_config_path_uses_profile_cli(monkeypatch, tmp_path):
    config_file = tmp_path / "config.yaml"

    def fake_run(*args, **kwargs):
        assert args[0] == ["hermes", "-p", "wright", "config", "path"]
        return subprocess.CompletedProcess(args[0], 0, stdout=f"{config_file}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert hermes_config_path({"HERMES_PROFILE": "wright"}) == str(config_file)


def test_hermes_env_path_uses_cli(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"

    def fake_run(*args, **kwargs):
        assert args[0] == ["hermes", "config", "env-path"]
        return subprocess.CompletedProcess(args[0], 0, stdout=f"{env_file}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert hermes_env_path({}) == str(env_file)


def test_resolve_api_settings_from_hermes_config_path(monkeypatch, tmp_path):
    config_file = tmp_path / "config.yaml"
    env_file = tmp_path / ".env"
    config_file.write_text(
        "\n".join([
            "API_SERVER_HOST: 127.0.0.1",
            "API_SERVER_PORT: 9876",
            "API_SERVER_KEY: from-config",
        ]),
        encoding="utf-8",
    )
    env_file.write_text(
        "\n".join([
            "API_SERVER_PORT=1111",
            "API_SERVER_KEY=from-env",
        ]),
        encoding="utf-8",
    )

    def fake_run(*args, **kwargs):
        if args[0][-1] == "path":
            return subprocess.CompletedProcess(args[0], 0, stdout=f"{config_file}\n")
        return subprocess.CompletedProcess(args[0], 0, stdout=f"{env_file}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    settings = resolve_hermes_api_settings({})

    assert settings.base_url == "http://127.0.0.1:9876"
    assert settings.api_key == "from-config"
    assert settings.source == str(config_file)


def test_resolve_api_settings_from_hermes_env_path(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join([
            "API_SERVER_HOST=127.0.0.1",
            "API_SERVER_PORT=9876",
            "API_SERVER_KEY=from-hermes",
        ]),
        encoding="utf-8",
    )

    def fake_run(*args, **kwargs):
        if args[0][-1] == "path":
            raise FileNotFoundError("no config")
        return subprocess.CompletedProcess(args[0], 0, stdout=f"{env_file}\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    settings = resolve_hermes_api_settings({})

    assert settings.base_url == "http://127.0.0.1:9876"
    assert settings.api_key == "from-hermes"
    assert settings.source == str(env_file)


def test_resolve_api_settings_prefers_explicit_base_url(monkeypatch):
    def fail_run(*args, **kwargs):
        raise AssertionError("hermes CLI should not be called")

    monkeypatch.setattr(subprocess, "run", fail_run)

    settings = resolve_hermes_api_settings(
        {
            "HERMES_API_BASE_URL": "http://127.0.0.1:7777/",
            "HERMES_API_KEY": "explicit-key",
        }
    )

    assert settings.base_url == "http://127.0.0.1:7777"
    assert settings.api_key == "explicit-key"
    assert settings.source == "HERMES_API_BASE_URL"
