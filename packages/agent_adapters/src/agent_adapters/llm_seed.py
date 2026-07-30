"""Hermes model-provider seed helpers for Docker and setup flows."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import yaml

from .config_merge import atomic_merge_yaml

DEFAULT_CODEX_BASE_URL = "https://chatgpt.com/backend-api/codex"
DEFAULT_CUSTOM_PROVIDER_NAME = "wright-llm"

PROVIDER_ALIASES = {
    "codex": "openai-codex",
    "openai_codex": "openai-codex",
    "chatgpt": "openai-codex",
    "openai-compatible": "custom",
    "openai_compatible": "custom",
    "openai-api": "custom",
    "openai": "custom",
    "ollama": "custom",
    "lmstudio": "custom",
    "docker-model-runner": "custom",
}


@dataclass(frozen=True)
class LlmSeedResult:
    source: str | None
    provider: str | None
    model: str | None
    base_url: str | None
    config_changed: bool
    auth_changed: bool
    auth_configured: bool
    configured: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
            "config_changed": self.config_changed,
            "auth_changed": self.auth_changed,
            "auth_configured": self.auth_configured,
            "configured": self.configured,
        }


def provider_presets() -> list[dict[str, Any]]:
    """Return Wright-supported first-run provider choices."""
    return [
        {
            "id": "openai-codex",
            "label": "Codex / ChatGPT Login",
            "auth_type": "oauth_device_or_seed_file",
            "requires_api_key": False,
            "default_base_url": DEFAULT_CODEX_BASE_URL,
            "supports_seed_file": True,
            "notes": "Uses Hermes' OpenAI Codex provider and Hermes-owned auth.json.",
        },
        {
            "id": "custom",
            "label": "OpenAI-Compatible Endpoint",
            "auth_type": "api_key_or_none",
            "requires_api_key": False,
            "default_base_url": "",
            "supports_seed_file": True,
            "notes": "Works with OpenAI API, OpenRouter, Groq, Ollama, LM Studio, or Docker Model Runner when they expose a /v1 API.",
        },
        {
            "id": "nous",
            "label": "Nous Portal",
            "auth_type": "hermes_oauth",
            "requires_api_key": False,
            "default_base_url": "",
            "supports_seed_file": False,
            "notes": "Use Hermes' portal flow; browser UI wrapping can call the same Hermes setup path.",
        },
    ]


def load_seed_file(path: str | Path) -> dict[str, Any]:
    seed_path = Path(path).expanduser()
    loaded = yaml.safe_load(seed_path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"LLM seed file must be a mapping: {seed_path}")
    return loaded


def _first_present(mapping: Mapping[str, str], *names: str) -> str:
    for name in names:
        value = mapping.get(name, "")
        if value and value.strip():
            return value.strip()
    return ""


def _normalize_provider(provider: str | None) -> str:
    normalized = (provider or "").strip().lower()
    if not normalized:
        return "custom"
    return PROVIDER_ALIASES.get(normalized, normalized)


def _seed_from_env(env: Mapping[str, str]) -> tuple[dict[str, Any] | None, str | None]:
    seed: dict[str, Any] = {}
    source: str | None = None

    seed_file = _first_present(env, "WRIGHT_LLM_CONFIG_FILE", "WRIGHT_MODEL_CONFIG_FILE")
    if seed_file:
        seed = load_seed_file(seed_file)
        source = seed_file

    env_provider = _first_present(env, "WRIGHT_LLM_PROVIDER")
    env_base_url = _first_present(env, "WRIGHT_LLM_BASE_URL", "LLM_API_URL")
    env_model = _first_present(env, "WRIGHT_LLM_MODEL", "LLM_API_MODEL")
    env_api_key = _first_present(env, "WRIGHT_LLM_API_KEY", "LLM_API_KEY")
    env_auth_file = _first_present(
        env,
        "WRIGHT_LLM_AUTH_FILE",
        "WRIGHT_LLM_HERMES_AUTH_FILE",
        "WRIGHT_LLM_CODEX_AUTH_FILE",
    )

    if env_provider or env_base_url or env_model or env_api_key or env_auth_file:
        source = source or "environment"
        if env_provider:
            seed["provider"] = env_provider
        elif not seed.get("provider") and env_base_url:
            seed["provider"] = "custom"
        if env_base_url:
            seed["base_url"] = env_base_url
        if env_model:
            seed["model"] = env_model
        if env_api_key:
            seed["api_key"] = env_api_key
        if env_auth_file:
            seed["auth_file"] = env_auth_file

    return (seed, source) if seed else (None, None)


def _load_mapping(path: str | Path) -> dict[str, Any]:
    loaded = yaml.safe_load(Path(path).expanduser().read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected a mapping in {path}")
    return loaded


def _auth_payload_from_seed(seed: Mapping[str, Any]) -> dict[str, Any] | None:
    auth_file = seed.get("auth_file") or seed.get("hermes_auth_file")
    if isinstance(auth_file, str) and auth_file.strip():
        payload = _load_mapping(auth_file)
    else:
        payload = seed.get("auth") if isinstance(seed.get("auth"), dict) else None

    codex_cli_auth_file = seed.get("codex_cli_auth_file")
    if isinstance(codex_cli_auth_file, str) and codex_cli_auth_file.strip():
        payload = _load_mapping(codex_cli_auth_file)

    if not payload:
        tokens = seed.get("tokens") if isinstance(seed.get("tokens"), dict) else None
        if not tokens:
            access_token = str(seed.get("access_token") or "").strip()
            refresh_token = str(seed.get("refresh_token") or "").strip()
            if access_token or refresh_token:
                tokens = {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                }
        if tokens:
            payload = {"tokens": tokens}

    if not isinstance(payload, dict):
        return None

    if "providers" in payload or "credential_pool" in payload:
        return payload

    tokens = payload.get("tokens") if isinstance(payload.get("tokens"), dict) else None
    if tokens:
        last_refresh = str(
            payload.get("last_refresh")
            or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )
        provider_state: dict[str, Any] = {
            "tokens": tokens,
            "last_refresh": last_refresh,
            "auth_mode": str(payload.get("auth_mode") or "chatgpt"),
        }
        label = payload.get("label")
        if isinstance(label, str) and label.strip():
            provider_state["label"] = label.strip()
        return {"providers": {"openai-codex": provider_state}}

    return None


def _merge_auth_store(path: str | Path, payload: Mapping[str, Any]) -> bool:
    auth_path = Path(path).expanduser()
    auth_path.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, Any]
    if auth_path.exists():
        existing = _load_mapping(auth_path)
    else:
        existing = {}

    changed = dict(existing)
    providers = changed.get("providers") if isinstance(changed.get("providers"), dict) else {}
    incoming_providers = payload.get("providers")
    if isinstance(incoming_providers, dict):
        providers = {**providers, **incoming_providers}
        changed["providers"] = providers

    pool = (
        changed.get("credential_pool")
        if isinstance(changed.get("credential_pool"), dict)
        else {}
    )
    incoming_pool = payload.get("credential_pool")
    if isinstance(incoming_pool, dict):
        pool = {**pool, **incoming_pool}
        changed["credential_pool"] = pool

    if changed == existing:
        return False

    temporary = auth_path.with_name(f".{auth_path.name}.tmp")
    temporary.write_text(json.dumps(changed, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(temporary, auth_path)
    return True


def _codex_auth_configured(auth_path: str | Path | None) -> bool:
    if not auth_path:
        return False
    path = Path(auth_path).expanduser()
    if not path.exists():
        return False
    try:
        auth = _load_mapping(path)
    except Exception:
        return False
    providers = auth.get("providers") if isinstance(auth.get("providers"), dict) else {}
    codex = providers.get("openai-codex") if isinstance(providers, dict) else None
    if isinstance(codex, dict):
        tokens = codex.get("tokens")
        if (
            isinstance(tokens, dict)
            and str(tokens.get("access_token") or "").strip()
            and str(tokens.get("refresh_token") or "").strip()
        ):
            return True
    pool = (
        auth.get("credential_pool")
        if isinstance(auth.get("credential_pool"), dict)
        else {}
    )
    entries = pool.get("openai-codex") if isinstance(pool, dict) else None
    if isinstance(entries, list):
        return any(
            isinstance(entry, dict)
            and str(entry.get("access_token") or "").strip()
            and str(entry.get("refresh_token") or "").strip()
            for entry in entries
        )
    return False


def apply_llm_seed(
    config_path: str | Path,
    *,
    auth_path: str | Path | None = None,
    seed: Mapping[str, Any] | None = None,
    env: Mapping[str, str] | None = None,
) -> LlmSeedResult:
    """Apply file/env provider seed data to a Hermes config/auth pair."""
    env = os.environ if env is None else env
    source = "explicit"
    if seed is None:
        seed_payload, source = _seed_from_env(env)
        seed = seed_payload
    if not seed:
        return LlmSeedResult(None, None, None, None, False, False, False, False)

    provider = _normalize_provider(str(seed.get("provider") or "custom"))
    if provider not in {"custom", "openai-codex", "nous"}:
        provider = "custom"

    base_url = str(seed.get("base_url") or "").strip()
    if provider == "openai-codex" and not base_url:
        base_url = DEFAULT_CODEX_BASE_URL
    model = str(seed.get("model") or "").strip()
    api_key = str(seed.get("api_key") or "").strip()
    custom_name = str(seed.get("custom_provider_name") or DEFAULT_CUSTOM_PROVIDER_NAME)

    def update_config(config: dict[str, Any]) -> None:
        model_config = config.get("model")
        if not isinstance(model_config, dict):
            model_config = {}
        if provider == "custom":
            model_config["provider"] = "custom"
            if base_url:
                model_config["base_url"] = base_url
            if model:
                model_config["default"] = model
            model_config.setdefault("context_length", 131072)

            custom_providers = config.get("custom_providers")
            if not isinstance(custom_providers, list):
                custom_providers = []
            owned = {
                "name": custom_name,
                "base_url": base_url,
                "model": model,
                "api_key": api_key or "NotNeeded",
            }
            custom_providers = [
                item
                for item in custom_providers
                if not isinstance(item, dict) or item.get("name") != custom_name
            ]
            config["custom_providers"] = [*custom_providers, owned]
        else:
            model_config["provider"] = provider
            if base_url:
                model_config["base_url"] = base_url
            if model:
                model_config["default"] = model
            model_config.setdefault("context_length", 131072)
        config["model"] = model_config

    config_changed = atomic_merge_yaml(config_path, update_config)

    auth_changed = False
    if provider == "openai-codex" and auth_path:
        auth_payload = _auth_payload_from_seed(seed)
        if auth_payload:
            auth_changed = _merge_auth_store(auth_path, auth_payload)

    auth_configured = provider != "openai-codex" or _codex_auth_configured(auth_path)
    configured = bool(provider == "openai-codex" or base_url) and auth_configured
    return LlmSeedResult(
        source,
        provider,
        model or None,
        base_url or None,
        config_changed,
        auth_changed,
        auth_configured,
        configured,
    )


def read_llm_summary(
    config_path: str | Path | None,
    *,
    auth_path: str | Path | None = None,
) -> dict[str, Any]:
    if not config_path or not Path(config_path).expanduser().exists():
        return {
            "provider": None,
            "model": None,
            "base_url": None,
            "auth_configured": False,
            "configured": False,
        }
    config = _load_mapping(config_path)
    model = config.get("model") if isinstance(config.get("model"), dict) else {}
    provider = _normalize_provider(str(model.get("provider") or "custom"))
    base_url = str(model.get("base_url") or "").strip() or None
    model_name = str(model.get("default") or "").strip() or None
    auth_configured = provider != "openai-codex" or _codex_auth_configured(auth_path)
    configured = bool(provider == "openai-codex" or base_url) and auth_configured
    return {
        "provider": provider,
        "model": model_name,
        "base_url": base_url,
        "auth_configured": auth_configured,
        "configured": configured,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply a Wright LLM seed to Hermes")
    parser.add_argument("--config-path", required=True)
    parser.add_argument("--auth-path")
    parser.add_argument("--status-path")
    args = parser.parse_args(argv)

    result = apply_llm_seed(args.config_path, auth_path=args.auth_path)
    payload = result.as_dict()
    if args.status_path:
        status_path = Path(args.status_path)
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
