from __future__ import annotations

import asyncio

from wright_engineering.hermes_plugin.commands import handle_wright
from wright_engineering.runtime.models import LifecycleResult, LifecycleState, utc_now


def result(command: str) -> LifecycleResult:
    now = utc_now()
    return LifecycleResult(
        operation_id="op",
        command=command,
        ok=True,
        state=LifecycleState.STOPPED,
        code="ok",
        summary=f"{command} complete",
        started_at=now,
        finished_at=now,
    )


class FakeLifecycle:
    def update(self, version=None):
        return result("update")

    def rollback(self, version=None):
        return result("rollback")


def test_update_and_rollback_commands_project_results() -> None:
    runtime = FakeLifecycle()
    assert "update complete" in asyncio.run(handle_wright("update", lifecycle=runtime))  # type: ignore[arg-type]
    assert "rollback complete" in asyncio.run(
        handle_wright("rollback", lifecycle=runtime)
    )  # type: ignore[arg-type]
