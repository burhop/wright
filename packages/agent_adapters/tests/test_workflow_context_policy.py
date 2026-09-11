"""Workflow policy supports complete engineering evidence, with bounded transport."""
import copy
import json
from types import SimpleNamespace

import httpx
import pytest

from agent_adapters import hermes_openai_bridge, report_generation
from agent_adapters.hermes_openai_bridge import HermesOpenAIBridgeSettings
from test_workflow_hermes_normalization import normalize  # noqa: F401
from test_workflow_transcript_evidence import TOOL, observation_exchange, reply


def route_to_transport(monkeypatch, handler):
    actual_bridge = hermes_openai_bridge.HermesOpenAICompatibilityBridge
    monkeypatch.setattr(report_generation, "resolve_hermes_api_settings", lambda: SimpleNamespace(
        base_url="http://invalid.test-only", api_key="not-a-credential"))

    def construct(settings, **kwargs):
        if not kwargs:  # Production entry point; repair subtracts its reserve.
            assert settings.maximum_translation_prompt_bytes == 200_000
        else:
            assert 0 < settings.maximum_translation_prompt_bytes < 200_000
        return actual_bridge(settings, transport=kwargs.get("transport", httpx.MockTransport(handler)))

    monkeypatch.setattr(hermes_openai_bridge, "HermesOpenAICompatibilityBridge", construct)


@pytest.mark.asyncio
@pytest.mark.parametrize("repair", [False, True])
async def test_workflow_policy_preserves_twenty_messages_and_image_through_hermes(normalize, monkeypatch, repair):  # noqa: F811
    image = {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}}
    messages = [{"role": "system", "content": "Keep unknown and adverse observations."},
                {"role": "user", "content": [{"type": "text", "text": "Requirements μm. " * 1700}, image]}]
    for index, size in enumerate((5394, 3784, 13047, 31159, 4354, 18094, 215, 397, 34247)):
        messages.extend(observation_exchange(f"native-{index}", {
            "observationId": f"distinct-{index}", "nativeDetail": str(index) * size,
            "evidenceStatus": {"provenance": "unavailable" if index == 5 else "observed",
                               "disposition": "fail" if index == 8 else "not_evaluated"},
            "isSatisfied": False, "measured": -0.0 if index == 5 else 2.032,
            "targetReference": f"model:1:face:{index + 35}",
        }, number=index + 1, arguments={"unit": "mm" if index < 8 else "in"}))
    original = copy.deepcopy(messages)
    sent = []

    async def handler(call):
        payload = json.loads(call.content)
        sent.append(payload)
        content = payload["messages"][1]["content"]
        normalized = normalize(content)
        parts = [part["text"] for part in content if part["type"] == "text"]
        assert all(len(part) <= 65_536 for part in parts)
        text = "\n".join(part["text"] for part in normalized if part["type"] == "text")
        transcript = json.loads(text.split("\n", 1)[1])
        expected = copy.deepcopy(messages)
        expected[1]["content"][1] = {"type": "text", "text": "[Reference image 1 attached to this request]"}
        assert transcript["conversation"] == expected
        assert len(transcript["conversation"]) == 20
        assert transcript["tools"][0] == TOOL["function"]
        assert "wright_transcript_omissions" not in transcript
        assert [part for part in normalized if part["type"] == "image_url"] == [image]
        total = sum(len(("\n".join(p["text"] for p in m["content"] if p["type"] == "text")
                         if isinstance(m["content"], list) else m["content"]).encode()) for m in payload["messages"])
        assert 120_000 < total <= 200_000
        if repair and len(sent) == 1:
            return httpx.Response(200, json={"choices": [{"message": {"content": "invalid decision"}}]})
        return reply()

    route_to_transport(monkeypatch, handler)
    await report_generation.decide_workflow_tool_action(messages, [TOOL])
    assert messages == original
    assert len(sent) == (2 if repair else 1)
    assert HermesOpenAIBridgeSettings(base_url="http://invalid", api_key="test").maximum_translation_prompt_bytes == 60_000


@pytest.mark.asyncio
@pytest.mark.parametrize("limit", ["mandatory_floor", "single_item"])
async def test_workflow_policy_still_fails_before_http_for_unrepresentable_evidence(monkeypatch, limit):
    messages = [{"role": "user", "content": "Inspect all native evidence."}]
    for index in range(7 if limit == "mandatory_floor" else 1):
        messages.extend(observation_exchange(f"required-{index}", {
            "isSatisfied": False, "evidence": str(index) * (31000 if limit == "mandatory_floor" else 66000),
        }, number=index + 1))

    async def handler(call):
        pytest.fail("Evidence must not be truncated or sent beyond the enforced limits")

    route_to_transport(monkeypatch, handler)
    with pytest.raises(ValueError, match="workflow_context_limit"):
        await report_generation.decide_workflow_tool_action(messages, [TOOL])
