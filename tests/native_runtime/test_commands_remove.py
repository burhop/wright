from __future__ import annotations

import asyncio

from .adapter_support import load_adapter, load_adapter_commands


COMMANDS = load_adapter_commands()


def _invoke(command: str, argument: str | None) -> dict[str, object]:
    return {
        "ok": True,
        "code": "ok",
        "summary": f"{command} complete",
        "details": {"confirmation_code": argument} if command == "purge" else {},
        "remediation": [],
    }


def test_uninstall_and_purge_commands_project_results() -> None:
    assert "uninstall complete" in asyncio.run(
        COMMANDS.handle_wright("uninstall", invoker=_invoke)
    )
    assert "purge complete" in asyncio.run(
        COMMANDS.handle_wright("purge token", invoker=_invoke)
    )


def test_entrypoint_registers_only_documented_command_and_no_remove_hook() -> None:
    class Context:
        def __init__(self):
            self.commands = {}
            self.hooks = {}

        def register_command(self, **kwargs):
            self.commands[kwargs["name"]] = kwargs["handler"]

        def register_hook(self, *, name, handler):
            self.hooks[name] = handler

    context = Context()
    load_adapter().register(context)
    assert set(context.commands) == {"wright"}
    assert context.hooks == {}
