from contextlib import asynccontextmanager
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest

from agent_adapters.base import AgentChatRequest
from agent_adapters.hermes import HermesAdapter
from agent_adapters import hermes
from agent_adapters.workflow_instructions import load_default_workflow_instructions
from core.process_validation import canonical_digest


@pytest.mark.asyncio
@pytest.mark.parametrize("failed", [False, True])
async def test_chat_actual_request_is_observed_before_transport_including_failure(
    monkeypatch, failed
):
    adapter = HermesAdapter("http://gateway.test", "private-api-key")
    monkeypatch.setattr(adapter, "get_chat_history", AsyncMock(return_value=[]))
    monkeypatch.setattr(adapter, "get_session_workspace", AsyncMock(return_value=None))
    monkeypatch.setattr(
        adapter, "_generated_image_media_token_for_turn", AsyncMock(return_value=None)
    )
    records, sent = [], []

    @asynccontextmanager
    async def connect(client, method, url, **kwargs):
        assert records, "Evidence must persist before the network request"
        sent.append(kwargs["json"])
        if failed:
            raise httpx.ConnectError("Gateway unreachable")

        async def events():
            yield SimpleNamespace(
                event="message",
                data=json.dumps(
                    {
                        "model": "provider-reported-revision",
                        "choices": [{"delta": {"content": "Rendered"}}],
                    }
                ),
            )
            yield SimpleNamespace(event="message", data="[DONE]")

        yield SimpleNamespace(
            response=httpx.Response(200, request=httpx.Request("POST", url)),
            aiter_sse=events,
        )

    monkeypatch.setattr(hermes, "aconnect_sse", connect)

    async def observe(value):
        records.append(value)

    instructions = load_default_workflow_instructions()
    request = AgentChatRequest(
        "session",
        "Render my part",
        attachments=["data:image/png;base64,ZmFrZQ=="],
        instruction_set=instructions.model_dump(mode="json"),
        invocation_observer=observe,
    )
    events = [event async for event in adapter.stream_chat(request)]
    assert len(records) == (1 if failed else 2) and len(sent) == 1
    record = records[0]
    assert record["request_digest"] == canonical_digest(sent[0])
    assert record["request_fields"]["session_id"] == sent[0]["session_id"]
    assert record["request_fields"]["model"] == "hermes"
    assert record["resolved_instructions"]["asset_ids"]
    assert record["instruction_set_digest"] == instructions.digest
    assert record["messages"][0]["content"] == sent[0]["messages"][0]["content"]
    assert record["messages"][1]["content"][1]["type"] == "image_reference"
    assert "base64,ZmFrZQ" not in str(record) and "private-api-key" not in str(record)
    if not failed:
        assert records[1]["capture_phase"] == "response"
        assert records[1]["upstream_reported_model"] == "provider-reported-revision"
    assert any(event.type == ("error" if failed else "stream_end") for event in events)


@pytest.mark.asyncio
@pytest.mark.parametrize("phase", ["submission", "response"])
async def test_chat_audit_storage_failure_is_not_swallowed_as_stream_syntax(
    monkeypatch, phase
):
    adapter = HermesAdapter("http://gateway.test", "private-api-key")
    monkeypatch.setattr(adapter, "get_chat_history", AsyncMock(return_value=[]))
    monkeypatch.setattr(adapter, "get_session_workspace", AsyncMock(return_value=None))
    sent = []

    @asynccontextmanager
    async def connect(client, method, url, **kwargs):
        sent.append(kwargs["json"])

        async def events():
            yield SimpleNamespace(
                event="message",
                data=json.dumps(
                    {
                        "model": "actual-model",
                        "choices": [{"delta": {"content": "Reply"}}],
                    }
                ),
            )

        yield SimpleNamespace(
            response=httpx.Response(200, request=httpx.Request("POST", url)),
            aiter_sse=events,
        )

    monkeypatch.setattr(hermes, "aconnect_sse", connect)

    async def observe(value):
        if value["capture_phase"] == phase:
            raise OSError("PRIVATE filesystem details")

    request = AgentChatRequest("session", "Describe", invocation_observer=observe)
    events = [event async for event in adapter.stream_chat(request)]
    assert len(sent) == (0 if phase == "submission" else 1)
    assert events[-1].type == "error"
    assert (
        events[-1].data["message"] == "Chat invocation evidence could not be retained."
    )
    assert "PRIVATE" not in str(events) and adapter._active_clients == {}
