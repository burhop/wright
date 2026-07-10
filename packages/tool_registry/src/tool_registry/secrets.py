"""Compatibility API for MCP credentials backed by Wright's SecretProvider."""

from __future__ import annotations

import json
from typing import Dict, List, Optional

import structlog
from core.secrets import CredentialReference, default_secret_provider

logger = structlog.get_logger(__name__)

_CREDENTIAL_ALIASES: dict[str, tuple[str, ...]] = {
    "ONSHAPE_API_KEY": ("ONSHAPE_ACCESS_KEY",),
    "ONSHAPE_API_SECRET": ("ONSHAPE_SECRET_KEY",),
    "ONSHAPE_ACCESS_KEY": ("ONSHAPE_API_KEY",),
    "ONSHAPE_SECRET_KEY": ("ONSHAPE_API_SECRET",),
}


def value_for_credential(saved: Dict[str, str], name: str) -> str | None:
    value = saved.get(name)
    if value:
        return value
    for alias in _CREDENTIAL_ALIASES.get(name, ()):
        alias_value = saved.get(alias)
        if alias_value:
            return alias_value
    return None


def _reference(server_id: str) -> CredentialReference:
    return CredentialReference("mcp", server_id, "CREDENTIAL_BUNDLE")


def read_secrets(server_id: str) -> Dict[str, str]:
    """Return one server's credentials for internal process construction only."""
    raw = default_secret_provider().get(_reference(server_id))
    if raw is None:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Stored MCP credentials are corrupt") from exc
    if not isinstance(payload, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in payload.items()
    ):
        raise RuntimeError("Stored MCP credentials have an invalid format")
    logger.info("credentials_loaded", server_id=server_id, var_count=len(payload))
    return payload


def write_secrets(server_id: str, credentials: Dict[str, str]) -> None:
    """Atomically replace one server's credential bundle."""
    if not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in credentials.items()
    ):
        raise TypeError("Credential keys and values must be strings")
    default_secret_provider().set(
        _reference(server_id),
        json.dumps(credentials, sort_keys=True, separators=(",", ":")),
    )
    logger.info("credentials_saved", server_id=server_id, var_count=len(credentials))


def delete_secrets(server_id: str) -> None:
    default_secret_provider().delete(_reference(server_id))
    logger.info("credentials_deleted", server_id=server_id)


def has_credentials(
    server_id: str, required_vars: Optional[List[str]] = None
) -> Dict[str, bool]:
    if not required_vars:
        return {}
    saved = read_secrets(server_id)
    return {name: bool(value_for_credential(saved, name)) for name in required_vars}
