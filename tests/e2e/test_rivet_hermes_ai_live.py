from __future__ import annotations

import json
import os

import pytest

from agent_adapters import (
    AgentChatRequest,
    HermesOpenAICompatibilityBridge,
    HermesOpenAIBridgeSettings,
    create_agent_engine,
    resolve_agent_api_settings,
)
from api.routers.agent import ChatStreamJob


def _live_enabled(marker_expression: str, environment: dict[str, str]) -> bool:
    opted_in = environment.get("WRIGHT_RIVET_LIVE_AI", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    return opted_in and "rivet_live_ai" in marker_expression


def _require_live(pytestconfig: pytest.Config) -> None:
    if not _live_enabled(pytestconfig.getoption("-m"), dict(os.environ)):
        pytest.skip(
            "Live Rivet AI requires both -m rivet_live_ai and "
            "WRIGHT_RIVET_LIVE_AI=1 before any subscription request."
        )


def test_live_guard_requires_marker_and_environment_before_network() -> None:
    assert not _live_enabled("", {})
    assert not _live_enabled("rivet_live_ai", {})
    assert not _live_enabled("", {"WRIGHT_RIVET_LIVE_AI": "1"})
    assert _live_enabled(
        "rivet_live_ai", {"WRIGHT_RIVET_LIVE_AI": "1"}
    )


@pytest.mark.asyncio
@pytest.mark.rivet_live_ai
async def test_live_rivet_shaped_structured_tool_call(pytestconfig) -> None:
    _require_live(pytestconfig)
    hermes = resolve_agent_api_settings("hermes")
    bridge = HermesOpenAICompatibilityBridge(
        HermesOpenAIBridgeSettings(
            base_url=hermes.base_url,
            api_key=hermes.api_key,
            timeout_seconds=60,
        )
    )
    result = await bridge.complete(
        {
            "model": "wright-hermes",
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Select create_graph with title Live Rivet Canary and "
                        "connected set to true."
                    ),
                }
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "create_graph",
                        "description": "Return the requested deterministic canary graph.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "const": "Live Rivet Canary",
                                },
                                "connected": {"type": "boolean", "const": True},
                            },
                            "required": ["title", "connected"],
                            "additionalProperties": False,
                        },
                    },
                }
            ],
            "tool_choice": {
                "type": "function",
                "function": {"name": "create_graph"},
            },
            "parallel_tool_calls": False,
        },
        request_id="live-rivet-structured-canary",
    )

    choice = result["choices"][0]
    call = choice["message"]["tool_calls"][0]
    assert choice["finish_reason"] == "tool_calls"
    assert call["function"]["name"] == "create_graph"
    assert json.loads(call["function"]["arguments"]) == {
        "connected": True,
        "title": "Live Rivet Canary",
    }


@pytest.mark.asyncio
@pytest.mark.rivet_live_ai
async def test_live_wright_chat_reports_rivet_mcp_progress_and_grounding(
    pytestconfig,
    tmp_path,
) -> None:
    _require_live(pytestconfig)
    engine = create_agent_engine("hermes")
    session = await engine.create_session(
        workspace=str(tmp_path),
        instructions="This is a bounded Wright Rivet MCP live canary.",
    )
    request = AgentChatRequest(
        session_id=session.session_id,
        message=(
            "Use the rivet-workflows MCP list_templates tool exactly once. "
            "Do not create or run anything. Report whether the Basic Flow "
            "template exists and its declared requirements."
        ),
        trace_id="live-rivet-chat-canary",
    )
    job = ChatStreamJob(session.session_id, request, engine, heartbeat_seconds=60)
    job.start()
    try:
        events = [event async for event in job.stream_from()]
    finally:
        await engine.delete_session(session.session_id)

    errors = [data for kind, data in events if kind == "error"]
    assert not errors, errors
    progress = [data for kind, data in events if kind == "progress"]
    rivet_progress = [
        data
        for data in progress
        if "rivet" in json.dumps(data, sort_keys=True).lower()
    ]
    response = "".join(
        str(data.get("text", ""))
        for kind, data in events
        if kind in {"token", "content"}
    )
    assert rivet_progress, progress
    assert "basic flow" in response.lower()
    assert "requirement" in response.lower()
