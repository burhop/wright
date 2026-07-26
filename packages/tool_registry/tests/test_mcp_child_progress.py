from __future__ import annotations

import os
import sys

import pytest

from tool_registry.runners.stdio import StdioRunner


@pytest.mark.asyncio
async def test_stdio_forwards_matching_monotonic_child_progress() -> None:
    server = os.path.join(os.path.dirname(__file__), "mock_server.py")
    runner = StdioRunner([sys.executable, server])
    updates: list[dict] = []
    await runner.start()
    try:
        result = await runner.call_tool(
            "test_tool",
            {"val": "progress"},
            progress_callback=lambda update: updates.append(dict(update)),
        )
    finally:
        await runner.stop()

    assert result["content"][0]["type"] == "text"
    assert updates == [
        {"progress": 1.0, "total": 2.0, "message": "Preparing"},
        {"progress": 2.0, "total": 2.0, "message": "Completed"},
    ]


@pytest.mark.asyncio
async def test_progress_validation_and_terminal_cleanup(monkeypatch) -> None:
    runner = StdioRunner(["unused"])
    updates: list[dict] = []
    observed_token: str | None = None

    async def respond(method, params):
        nonlocal observed_token
        observed_token = params["_meta"]["progressToken"]
        await runner._handle_progress_notification(
            {
                "progressToken": observed_token,
                "progress": 3,
                "total": 5,
                "message": "x" * 600,
            }
        )
        await runner._handle_progress_notification(
            {"progressToken": observed_token, "progress": 2, "total": 5}
        )
        await runner._handle_progress_notification(
            {"progressToken": observed_token, "progress": 4, "total": 0}
        )
        return {"content": []}

    monkeypatch.setattr(runner, "_send_request", respond)
    await runner.call_tool(
        "test_tool",
        {},
        progress_callback=lambda update: updates.append(dict(update)),
    )

    assert observed_token is not None
    assert len(updates) == 1
    assert len(updates[0]["message"]) == 512
    assert runner._progress_callbacks == {}
    await runner._handle_progress_notification(
        {"progressToken": observed_token, "progress": 5, "total": 5}
    )
    assert len(updates) == 1
