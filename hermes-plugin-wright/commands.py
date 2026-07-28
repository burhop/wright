"""Deprecated import compatibility for the native Wright command dispatcher."""

from __future__ import annotations

from typing import Any

from wright_engineering.hermes_plugin.commands import (
    HELP as WRIGHT_HELP_TEXT,
    handle_wright,
    project_result,
    register_commands as _register_commands,
)


def register_commands(ctx: Any, _legacy_catalog: object | None = None) -> None:
    """Delegate registration; the legacy catalog argument is intentionally ignored."""
    _register_commands(ctx)


__all__ = [
    "WRIGHT_HELP_TEXT",
    "handle_wright",
    "project_result",
    "register_commands",
]
