"""Dependency-light Hermes plugin entry point for Wright.

The module intentionally imports only the Python standard library at import
time. Runtime dependencies are installed and launched in an isolated process.
"""

from __future__ import annotations

from typing import Any


def register(ctx: Any) -> None:
    """Register Wright with Hermes without importing application dependencies."""
    from .commands import register_commands

    register_commands(ctx)
    register_hook = getattr(ctx, "register_hook", None)
    if callable(register_hook):
        import asyncio

        async def pre_remove(**_: object) -> dict[str, object]:
            from wright_engineering.runtime.lifecycle import NativeLifecycle

            result = await asyncio.to_thread(NativeLifecycle.default().uninstall)
            return result.to_dict()

        register_hook(name="pre_remove", handler=pre_remove)
