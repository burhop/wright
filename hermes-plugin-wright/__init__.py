"""Production Wright adapter for Hermes' Git plugin interface."""

from __future__ import annotations

from typing import Any


def register(ctx: Any) -> None:
    from .commands import register_commands

    register_commands(ctx)


__all__ = ["register"]
