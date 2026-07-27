from __future__ import annotations

import asyncio

import pytest

from test_gateway_service import service


@pytest.mark.asyncio
async def test_one_hundred_two_session_trials_do_not_leak_state() -> None:
    gateway, lifecycle, audit = service()
    for trial in range(100):
        first, second = await asyncio.gather(
            gateway.call_tool("s1", f"cad-{trial}", "cad__run", {"trial": trial}),
            gateway.call_tool("s2", f"fea-{trial}", "fea__run", {"trial": trial}),
        )
        assert first.structured_content == {"server": "cad", "workspace": "w1"}
        assert second.structured_content == {"server": "fea", "workspace": "w2"}
        assert gateway.cancel("s1", f"fea-{trial}", "foreign") is False
        assert gateway.cancel("s2", f"cad-{trial}", "foreign") is False
        assert [tool.name for tool in gateway.list_tools("s1")] == ["cad__run"]
        assert [tool.name for tool in gateway.list_tools("s2")] == ["fea__run"]
        assert gateway.read_resource("s1", "wright://workspace/w1")
        assert gateway.read_resource("s2", "wright://workspace/w2")

    assert len(lifecycle.calls) == 200
    assert {event["workspace_id"] for event in audit.events} == {"w1", "w2"}
    assert all(
        call[3]["workspace_id"] == ("w1" if call[0] == "cad" else "w2")
        for call in lifecycle.calls
    )
