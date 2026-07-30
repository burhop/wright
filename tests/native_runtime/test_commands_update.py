from __future__ import annotations

import asyncio

from .adapter_support import load_adapter_commands


COMMANDS = load_adapter_commands()


def _invoke(command: str, argument: str | None) -> dict[str, object]:
    return {
        "ok": True,
        "code": "ok",
        "summary": f"{command} complete",
        "details": {"argument": argument},
        "remediation": [],
    }


def test_update_and_rollback_commands_project_results() -> None:
    assert "update complete" in asyncio.run(
        COMMANDS.handle_wright("update 0.1.5", invoker=_invoke)
    )
    assert "rollback complete" in asyncio.run(
        COMMANDS.handle_wright("rollback", invoker=_invoke)
    )
