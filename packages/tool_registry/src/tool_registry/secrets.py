"""
Secure local credential store for MCP server secrets.

Stores credentials in a JSON file at ~/.config/wright/mcp-secrets.json,
outside the repository tree. File permissions are set to 0600 (owner read/write only).
Uses advisory file locking to prevent concurrent write corruption.

Secret values are NEVER logged.
"""

import json
import os
import sys
from typing import Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)

# ---------- Cross-platform file locking ----------
if sys.platform == "win32":
    import msvcrt

    def _lock_file(f: object, exclusive: bool = False) -> None:
        """Acquire an advisory lock (Windows)."""
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK if exclusive else msvcrt.LK_LOCK, 1)

    def _unlock_file(f: object) -> None:
        """Release an advisory lock (Windows)."""
        try:
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass  # Already unlocked or file closed
else:
    import fcntl

    def _lock_file(f: object, exclusive: bool = False) -> None:
        """Acquire an advisory lock (Unix)."""
        fcntl.flock(f, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)

    def _unlock_file(f: object) -> None:
        """Release an advisory lock (Unix)."""
        fcntl.flock(f, fcntl.LOCK_UN)


# Default path, overridable via env var for testing
_DEFAULT_SECRETS_PATH = os.path.expanduser("~/.config/wright/mcp-secrets.json")

_CREDENTIAL_ALIASES: dict[str, tuple[str, ...]] = {
    "ONSHAPE_API_KEY": ("ONSHAPE_ACCESS_KEY",),
    "ONSHAPE_API_SECRET": ("ONSHAPE_SECRET_KEY",),
    "ONSHAPE_ACCESS_KEY": ("ONSHAPE_API_KEY",),
    "ONSHAPE_SECRET_KEY": ("ONSHAPE_API_SECRET",),
}


def value_for_credential(saved: Dict[str, str], name: str) -> str | None:
    """Return a saved credential value, honoring known renamed keys."""
    value = saved.get(name)
    if value:
        return value
    for alias in _CREDENTIAL_ALIASES.get(name, ()):  # compatibility for renamed vars
        alias_value = saved.get(alias)
        if alias_value:
            return alias_value
    return None


def _get_secrets_path() -> str:
    """Get the secrets file path, allowing override for testing."""
    return os.environ.get("WRIGHT_SECRETS_PATH", _DEFAULT_SECRETS_PATH)


def _ensure_secrets_dir(secrets_path: str) -> None:
    """Create the secrets directory with restricted permissions if needed."""
    secrets_dir = os.path.dirname(secrets_path)
    if not os.path.exists(secrets_dir):
        os.makedirs(secrets_dir, mode=0o700, exist_ok=True)
        logger.info("created_secrets_directory", path=secrets_dir)
    # Ensure directory permissions are correct
    try:
        os.chmod(secrets_dir, 0o700)
    except OSError as e:
        logger.warning(
            "failed_to_set_directory_permissions", path=secrets_dir, error=str(e)
        )


def _read_secrets_file(secrets_path: str) -> Dict[str, Dict[str, str]]:
    """Read the entire secrets file, returning empty dict if missing/corrupt."""
    if not os.path.exists(secrets_path):
        return {}
    try:
        with open(secrets_path, "r") as f:
            _lock_file(f, exclusive=False)
            try:
                data = json.load(f)
            finally:
                _unlock_file(f)
        if isinstance(data, dict):
            return data
        logger.warning("secrets_file_invalid_format", path=secrets_path)
        return {}
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("secrets_file_read_error", path=secrets_path, error=str(e))
        return {}


def _write_secrets_file(secrets_path: str, data: Dict[str, Dict[str, str]]) -> None:
    """Write the entire secrets file with exclusive locking and restricted permissions."""
    _ensure_secrets_dir(secrets_path)
    try:
        with open(secrets_path, "w") as f:
            _lock_file(f, exclusive=True)
            try:
                json.dump(data, f, indent=2)
                f.write("\n")
            finally:
                _unlock_file(f)
        os.chmod(secrets_path, 0o600)
    except OSError as e:
        logger.error("secrets_file_write_error", path=secrets_path, error=str(e))
        raise


def read_secrets(server_id: str) -> Dict[str, str]:
    """Read credentials for a specific server.

    Returns empty dict if file doesn't exist or server has no saved credentials.
    Secret values are never logged.
    """
    secrets_path = _get_secrets_path()
    all_secrets = _read_secrets_file(secrets_path)
    server_secrets = all_secrets.get(server_id, {})
    if server_secrets:
        logger.info(
            "credentials_loaded", server_id=server_id, var_count=len(server_secrets)
        )
    return server_secrets


def write_secrets(server_id: str, credentials: Dict[str, str]) -> None:
    """Write/update credentials for a server.

    Creates parent directory and file if needed. Sets file permissions to 0600.
    Secret values are never logged.
    """
    secrets_path = _get_secrets_path()
    all_secrets = _read_secrets_file(secrets_path)
    all_secrets[server_id] = credentials
    _write_secrets_file(secrets_path, all_secrets)
    logger.info("credentials_saved", server_id=server_id, var_count=len(credentials))


def delete_secrets(server_id: str) -> None:
    """Remove a server's credentials from the secrets file."""
    secrets_path = _get_secrets_path()
    all_secrets = _read_secrets_file(secrets_path)
    if server_id in all_secrets:
        del all_secrets[server_id]
        _write_secrets_file(secrets_path, all_secrets)
        logger.info("credentials_deleted", server_id=server_id)
    else:
        logger.info("credentials_not_found_for_delete", server_id=server_id)


def has_credentials(
    server_id: str, required_vars: Optional[List[str]] = None
) -> Dict[str, bool]:
    """Check which env vars for a server are configured.

    Args:
        server_id: The server to check.
        required_vars: List of variable names to check. If None, returns empty dict.

    Returns:
        Dict mapping variable name to whether it has a saved value.
    """
    if not required_vars:
        return {}
    saved = read_secrets(server_id)
    return {var: bool(value_for_credential(saved, var)) for var in required_vars}
