from __future__ import annotations

import pytest

from agent_adapters import AgentChatRequest, AgentStreamEvent
from api.routers.agent import ChatStreamJob


class _ControlledHermesRivetEngine:
    def __init__(self) -> None:
        self.requests: list[AgentChatRequest] = []

    async def stream_chat(self, request: AgentChatRequest):
        self.requests.append(request)
        yield AgentStreamEvent(
            type="progress",
            data={
                "server": "rivet-workflows",
                "tool": "rivet-workflows__run_workflow",
                "title": "Run Rivet workflow",
                "status": "running",
                "message": "Passthrough graph starting",
                "correlationId": "rivet-run-1",
                "progress": 1,
            },
        )
        yield AgentStreamEvent(
            type="progress",
            data={
                "server": "rivet-workflows",
                "tool": "rivet-workflows__run_workflow",
                "title": "Run Rivet workflow",
                "status": "completed",
                "message": "Reviewed revision 1 completed",
                "correlationId": "rivet-run-1",
                "progress": 4,
            },
        )
        yield AgentStreamEvent(
            type="content",
            data={
                "text": (
                    "Workflow chat-basic revision 1 was validated and ran successfully; "
                    "output was hello through Wright."
                )
            },
        )
        yield AgentStreamEvent(type="stream_end", data={})


@pytest.mark.asyncio
async def test_wright_chat_relays_correlated_rivet_progress_and_grounded_result() -> (
    None
):
    engine = _ControlledHermesRivetEngine()
    request = AgentChatRequest(
        session_id="session-1",
        message=(
            "Use rivet-workflows to validate and run the approved exact revision "
            "of chat-basic."
        ),
    )
    job = ChatStreamJob("session-1", request, engine, heartbeat_seconds=60)
    job.start()

    events = [event async for event in job.stream_from()]
    rivet_progress = [
        data
        for event_type, data in events
        if event_type == "progress" and data.get("server") == "rivet-workflows"
    ]
    content = [data["text"] for event_type, data in events if event_type == "content"]

    assert engine.requests == [request]
    assert [item["status"] for item in rivet_progress] == ["running", "completed"]
    assert {item["correlationId"] for item in rivet_progress} == {"rivet-run-1"}
    assert all(
        item["tool"] == "rivet-workflows__run_workflow" for item in rivet_progress
    )
    assert content == [
        "Workflow chat-basic revision 1 was validated and ran successfully; output was hello through Wright."
    ]
