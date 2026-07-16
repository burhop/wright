import asyncio

import pytest

from agent_adapters import AgentChatRequest, AgentStreamEvent
from api.routers.agent import ChatStreamJob, _friendly_progress_data


class _SlowEngine:
    async def stream_chat(self, request):
        await asyncio.sleep(0.03)
        yield AgentStreamEvent(
            type="progress",
            data={
                "tool": ("mcp__wrightgateway__server__cad_create_part_from_recipe"),
                "status": "running",
            },
        )
        yield AgentStreamEvent(type="stream_end", data={})


def test_friendly_progress_data_describes_visible_solid_edge_creation():
    data = _friendly_progress_data(
        {
            "tool": "mcp__wrightgateway__server__cad_create_part_from_recipe",
            "status": "running",
        },
        12.34,
    )

    assert data["label"] == "Creating a new Solid Edge part"
    assert data["phase"] == "solid_edge_creation"
    assert data["elapsedSeconds"] == 12.3
    assert "visible in Solid Edge" in data["message"]


@pytest.mark.asyncio
async def test_chat_stream_emits_planning_and_elapsed_heartbeat_progress():
    request = AgentChatRequest(session_id="session-1", message="Create a part")
    job = ChatStreamJob("session-1", request, _SlowEngine(), heartbeat_seconds=0.01)
    job.start()

    events = [event async for event in job.stream_from()]
    progress = [data for event_type, data in events if event_type == "progress"]

    assert progress[0]["phase"] == "planning"
    assert any(item.get("heartbeat") for item in progress)
    assert any(item.get("phase") == "solid_edge_creation" for item in progress)
