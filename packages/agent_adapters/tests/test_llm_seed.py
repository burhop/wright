import json

import yaml

from agent_adapters.llm_seed import apply_llm_seed, provider_presets, read_llm_summary


def test_provider_presets_include_codex_and_custom():
    presets = {item["id"]: item for item in provider_presets()}

    assert presets["openai-codex"]["supports_seed_file"] is True
    assert presets["custom"]["auth_type"] == "api_key_or_none"


def test_no_seed_leaves_config_untouched(tmp_path):
    config = tmp_path / "config.yaml"

    result = apply_llm_seed(config, env={})

    assert result.configured is False
    assert result.config_changed is False
    assert not config.exists()


def test_env_llm_api_url_writes_custom_provider(tmp_path):
    config = tmp_path / "config.yaml"

    result = apply_llm_seed(
        config,
        env={
            "LLM_API_URL": "http://llm.local/v1",
            "LLM_API_MODEL": "cad-model",
            "LLM_API_KEY": "secret-key",
        },
    )

    assert result.configured is True
    loaded = yaml.safe_load(config.read_text(encoding="utf-8"))
    assert loaded["model"]["provider"] == "custom"
    assert loaded["model"]["base_url"] == "http://llm.local/v1"
    assert loaded["model"]["default"] == "cad-model"
    assert loaded["custom_providers"][0]["api_key"] == "secret-key"


def test_codex_seed_writes_provider_and_auth(tmp_path):
    config = tmp_path / "config.yaml"
    auth = tmp_path / "auth.json"

    result = apply_llm_seed(
        config,
        auth_path=auth,
        seed={
            "provider": "codex",
            "model": "codex-test-model",
            "tokens": {
                "access_token": "access-token",
                "refresh_token": "refresh-token",
            },
        },
    )

    assert result.configured is True
    assert result.auth_configured is True
    assert result.base_url == "https://chatgpt.com/backend-api/codex"
    loaded_config = yaml.safe_load(config.read_text(encoding="utf-8"))
    assert loaded_config["model"]["provider"] == "openai-codex"
    loaded_auth = json.loads(auth.read_text(encoding="utf-8"))
    assert (
        loaded_auth["providers"]["openai-codex"]["tokens"]["access_token"]
        == "access-token"
    )


def test_codex_summary_requires_refresh_token(tmp_path):
    config = tmp_path / "config.yaml"
    auth = tmp_path / "auth.json"
    config.write_text(
        yaml.safe_dump(
            {
                "model": {
                    "provider": "openai-codex",
                    "base_url": "https://chatgpt.com/backend-api/codex",
                }
            }
        ),
        encoding="utf-8",
    )
    auth.write_text(
        json.dumps(
            {
                "providers": {
                    "openai-codex": {"tokens": {"access_token": "access-only"}}
                }
            }
        ),
        encoding="utf-8",
    )

    summary = read_llm_summary(config, auth_path=auth)

    assert summary["provider"] == "openai-codex"
    assert summary["auth_configured"] is False
    assert summary["configured"] is False


def test_codex_summary_rejects_exhausted_credentials(tmp_path):
    config = tmp_path / "config.yaml"
    auth = tmp_path / "auth.json"
    config.write_text(
        yaml.safe_dump(
            {
                "model": {
                    "provider": "openai-codex",
                    "base_url": "https://chatgpt.com/backend-api/codex",
                }
            }
        ),
        encoding="utf-8",
    )
    auth.write_text(
        json.dumps(
            {
                "providers": {
                    "openai-codex": {
                        "tokens": {
                            "access_token": "access",
                            "refresh_token": "refresh",
                        }
                    }
                },
                "credential_pool": {
                    "openai-codex": [
                        {
                            "access_token": "access",
                            "refresh_token": "refresh",
                            "last_status": "exhausted",
                            "last_error_code": 401,
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )

    summary = read_llm_summary(config, auth_path=auth)

    assert summary["provider"] == "openai-codex"
    assert summary["auth_configured"] is False
    assert summary["configured"] is False


def test_auth_file_merges_hermes_auth_payload(tmp_path):
    config = tmp_path / "config.yaml"
    auth = tmp_path / "auth.json"
    auth.write_text(
        json.dumps({"providers": {"other": {"tokens": {"access_token": "keep"}}}}),
        encoding="utf-8",
    )
    seed_auth = tmp_path / "seed-auth.json"
    seed_auth.write_text(
        json.dumps(
            {
                "providers": {
                    "openai-codex": {
                        "tokens": {
                            "access_token": "codex-access",
                            "refresh_token": "codex-refresh",
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    apply_llm_seed(
        config,
        auth_path=auth,
        seed={"provider": "openai-codex", "auth_file": str(seed_auth)},
    )

    merged = json.loads(auth.read_text(encoding="utf-8"))
    assert merged["providers"]["other"]["tokens"]["access_token"] == "keep"
    assert (
        merged["providers"]["openai-codex"]["tokens"]["refresh_token"]
        == "codex-refresh"
    )
