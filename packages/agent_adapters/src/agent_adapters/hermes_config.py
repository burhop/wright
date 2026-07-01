import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class HermesApiSettings:
    base_url: str
    api_key: str
    source: str


def _parse_env_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_env_file(path: str | Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return values

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export ") :].strip()
        if key:
            values[key] = _parse_env_value(value)
    return values


def parse_top_level_config_file(path: str | Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return values

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        if raw_line[:1].isspace():
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key.startswith("API_SERVER_"):
            values[key] = _parse_env_value(value)
    return values


def _hermes_config_command(
    command: str,
    env: Mapping[str, str],
) -> str | None:
    profile = (env.get("HERMES_PROFILE") or "").strip()
    args = ["hermes"]
    if profile:
        args.extend(["-p", profile])
    args.extend(["config", command])

    try:
        result = subprocess.run(
            args,
            check=True,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    if result.stdout.strip():
        return result.stdout.strip().splitlines()[-1]
    return None


def hermes_config_path(env: Mapping[str, str] | None = None) -> str | None:
    env = env or os.environ
    explicit = env.get("HERMES_CONFIG_PATH")
    if explicit:
        return explicit

    cli_path = _hermes_config_command("path", env)
    if cli_path:
        return cli_path

    hermes_home = Path(env.get("HERMES_HOME") or Path.home() / ".hermes")
    profile = (env.get("HERMES_PROFILE") or "").strip()
    candidates = []
    if profile:
        candidates.append(hermes_home / "profiles" / profile / "config.yaml")
    candidates.append(hermes_home / "config.yaml")

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def hermes_env_path(env: Mapping[str, str] | None = None) -> str | None:
    env = env or os.environ
    explicit = env.get("HERMES_ENV_PATH")
    if explicit:
        return explicit

    cli_path = _hermes_config_command("env-path", env)
    if cli_path:
        return cli_path

    candidates = []
    hermes_home = Path(env.get("HERMES_HOME") or Path.home() / ".hermes")
    profile = (env.get("HERMES_PROFILE") or "").strip()
    if profile:
        candidates.append(hermes_home / "profiles" / profile / ".env")
    local_app_data = env.get("LOCALAPPDATA")
    if local_app_data:
        candidates.append(Path(local_app_data) / "hermes" / ".env")
    candidates.append(hermes_home / ".env")

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def resolve_hermes_api_settings(
    env: Mapping[str, str] | None = None,
) -> HermesApiSettings:
    env = env or os.environ
    explicit_base_url = env.get("HERMES_API_BASE_URL", "").strip().rstrip("/")
    explicit_key = env.get("HERMES_API_KEY", "").strip()
    api_server_key = env.get("API_SERVER_KEY", "").strip()

    if explicit_base_url:
        return HermesApiSettings(
            base_url=explicit_base_url,
            api_key=explicit_key or api_server_key,
            source="HERMES_API_BASE_URL",
        )

    config_path = hermes_config_path(env)
    env_path = hermes_env_path(env)
    config_values = parse_top_level_config_file(config_path) if config_path else {}
    env_values = parse_env_file(env_path) if env_path else {}

    host = (
        env.get("API_SERVER_HOST")
        or config_values.get("API_SERVER_HOST")
        or env_values.get("API_SERVER_HOST")
        or "127.0.0.1"
    ).strip()
    port = (
        env.get("API_SERVER_PORT")
        or config_values.get("API_SERVER_PORT")
        or env_values.get("API_SERVER_PORT")
        or "8642"
    ).strip()
    api_key = (
        explicit_key
        or api_server_key
        or config_values.get("HERMES_API_KEY", "")
        or config_values.get("API_SERVER_KEY", "")
        or env_values.get("HERMES_API_KEY", "")
        or env_values.get("API_SERVER_KEY", "")
    ).strip()

    scheme = "http"
    base_url = f"{scheme}://{host}:{port}".rstrip("/")
    return HermesApiSettings(
        base_url=base_url,
        api_key=api_key,
        source=config_path or env_path or "API_SERVER_DEFAULTS",
    )
