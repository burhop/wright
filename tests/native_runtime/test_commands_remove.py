from __future__ import annotations

import asyncio

from wright_engineering.hermes_plugin import register
from wright_engineering.hermes_plugin.commands import handle_wright
from wright_engineering.runtime.models import LifecycleResult, LifecycleState, utc_now


def result(command: str, code: str = "ok") -> LifecycleResult:
    now = utc_now()
    return LifecycleResult(
        operation_id="op",
        command=command,
        ok=True,
        state=LifecycleState.NOT_INSTALLED,
        code=code,
        summary=f"{command} complete",
        details={"confirmation_code": "code"} if command == "purge" else {},
        started_at=now,
        finished_at=now,
    )


class FakeLifecycle:
    def uninstall(self):
        return result("uninstall")

    def purge(self, confirmation=None):
        return result("purge")


def test_uninstall_and_purge_commands_project_results() -> None:
    runtime = FakeLifecycle()
    assert "uninstall complete" in asyncio.run(
        handle_wright("uninstall", lifecycle=runtime)
    )  # type: ignore[arg-type]
    assert "purge complete" in asyncio.run(
        handle_wright("purge token", lifecycle=runtime)
    )  # type: ignore[arg-type]


def test_entrypoint_registers_pre_remove_callback_when_hermes_supports_it() -> None:
    class Context:
        def __init__(self):
            self.hooks = {}

        def register_command(self, **kwargs):
            pass

        def register_hook(self, *, name, handler):
            self.hooks[name] = handler

    context = Context()
    register(context)
    assert "pre_remove" in context.hooks
