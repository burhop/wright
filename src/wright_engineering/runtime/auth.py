"""Manager-neutral local control-plane credential storage."""

from __future__ import annotations

import os
import re
import secrets
from pathlib import Path

from .layout import NativeLayout


_TOKEN = re.compile(r"^[0-9a-f]{64}$")


class ControlPlaneTokenError(RuntimeError):
    """Raised when Wright cannot safely load its local API credential."""


def _validate_token_path(layout: NativeLayout) -> Path:
    layout.ensure()
    path = layout.control_plane_token
    if path.is_symlink():
        raise ControlPlaneTokenError("control_plane_token_symlink_refused")
    try:
        layout.require_contained(path, layout.data)
    except ValueError as exc:
        raise ControlPlaneTokenError("control_plane_token_outside_wright_home") from exc
    return path


def _read_valid_token(path: Path) -> str:
    try:
        token = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ControlPlaneTokenError("control_plane_token_unreadable") from exc
    if not _TOKEN.fullmatch(token):
        raise ControlPlaneTokenError("control_plane_token_invalid")
    return token


def _tighten_permissions(path: Path) -> None:
    try:
        path.chmod(0o600)
    except OSError as exc:
        raise ControlPlaneTokenError("control_plane_token_permissions_failed") from exc
    if os.name != "nt" and path.stat().st_mode & 0o077:
        raise ControlPlaneTokenError("control_plane_token_permissions_unsafe")


def ensure_control_plane_token(layout: NativeLayout) -> str:
    """Create once and return the installation-local API token without logging it."""
    path = _validate_token_path(layout)
    if path.exists():
        _tighten_permissions(path)
        return _read_valid_token(path)

    token = secrets.token_hex(32)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError:
        if path.is_symlink():
            raise ControlPlaneTokenError("control_plane_token_symlink_refused")
        _tighten_permissions(path)
        return _read_valid_token(path)
    except OSError as exc:
        raise ControlPlaneTokenError("control_plane_token_create_failed") from exc
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(token)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    _tighten_permissions(path)
    return token


def read_control_plane_token(layout: NativeLayout) -> str:
    """Read an existing managed token; never create one from an MCP client."""
    path = _validate_token_path(layout)
    if not path.is_file():
        raise ControlPlaneTokenError("control_plane_token_missing")
    _tighten_permissions(path)
    return _read_valid_token(path)
