"""Saved bridge helpers and each actual upstream request remain inspectable."""

import json

import httpx
import pytest

from agent_adapters.hermes_openai_bridge import (
    HermesBridgeError,
    HermesOpenAICompatibilityBridge,
    HermesOpenAIBridgeSettings,
)
from agent_adapters.workflow_instructions import load_default_workflow_instructions
from core.process_validation import canonical_digest
from core.workflow_instructions import WorkflowInstructionSet, instruction_text_digest
from test_hermes_openai_bridge import _request, _tool


def saved_instructions():
    saved = load_default_workflow_instructions().model_dump(mode="json")
    for identity, body in (
        ("bridge.translation-system", "CAPTURED BRIDGE SYSTEM"),
        ("bridge.workflow-translation", "CAPTURED TRANSLATION {{optional_notice}}"),
        ("bridge.translation-repair", "CAPTURED REPAIR {{error}}"),
    ):
        asset = next(item for item in saved["assets"] if item["id"] == identity)
        asset["body"] = body
        asset["body_digest"] = instruction_text_digest(body)
    return WorkflowInstructionSet.model_validate(saved)


@pytest.mark.asyncio
async def test_saved_bridge_translation_and_repair_capture_actual_submitted_chain(
    monkeypatch,
):
    from agent_adapters import workflow_instructions

    instructions = saved_instructions()
    requests, captured = [], []

    async def observer(invocation):
        if invocation.get("capture_phase") != "response":
            assert len(captured) // 2 == len(requests)
        captured.append(json.loads(json.dumps(invocation)))

    async def handler(request):
        payload = json.loads(request.content)
        requests.append(payload)
        assert "wright_instruction_set" not in payload
        assert payload["messages"][0]["content"] == "CAPTURED BRIDGE SYSTEM"
        assert payload["messages"][1]["content"].startswith("CAPTURED TRANSLATION")
        if len(requests) == 2:
            transcript = json.loads(
                payload["messages"][-1]["content"].split("\n", 1)[1]
            )
            assert transcript["translation_repair"]["instructions"].startswith(
                "CAPTURED REPAIR"
            )
        return httpx.Response(
            200,
            json={
                "model": "upstream-exact-model",
                "usage": {"prompt_tokens": 11},
                "choices": [
                    {
                        "message": {
                            "content": "bad decision"
                            if len(requests) == 1
                            else '{"kind":"tool_call","name":"create_graph","arguments":{"title":"Verified"}}'
                        }
                    }
                ],
            },
        )

    bridge = HermesOpenAICompatibilityBridge(
        HermesOpenAIBridgeSettings(
            base_url="http://isolated.test", api_key="private-key", workflow_task=True
        ),
        transport=httpx.MockTransport(handler),
    )
    monkeypatch.setattr(
        workflow_instructions,
        "load_default_workflow_instructions",
        lambda: pytest.fail("Fresh defaults read"),
    )
    result = await bridge.complete(
        {
            **_request(tools=[_tool()]),
            "wright_instruction_set": instructions.model_dump(mode="json"),
        },
        invocation_observer=observer,
    )
    assert result["model"] == "wright-hermes"
    assert result.wright_upstream_model == "upstream-exact-model"
    assert result["usage"] == {"prompt_tokens": 11}
    assert len(requests) == len(result.wright_invocations) == 2
    assert len(captured) == 4
    assert [item["request_digest"] for item in captured[::2]] == [
        canonical_digest(item) for item in requests
    ]
    assert [item["messages"] for item in captured[::2]] == [
        item["messages"] for item in requests
    ]
    assert all(
        item["upstream_reported_model"] == "upstream-exact-model"
        for item in result.wright_invocations
    )
    assert all(
        item["capture_scope"] == "hermes_bridge_upstream_request" for item in captured
    )
    assert "private-key" not in json.dumps(result.wright_invocations)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "last_decision",
    [
        {
            "kind": "tool_call",
            "name": "create_graph",
            "arguments": "password=fake-private-value",
        },
        {"kind": "fake-private-value", "name": "create_graph", "arguments": {}},
        ["fake-private-value"],
    ],
)
async def test_failed_repair_retains_response_shape_without_argument_values(
    last_decision,
):
    """A terminal repair must remain diagnosable without echoing model secrets."""
    captured, calls = [], []

    async def observe(invocation):
        captured.append(invocation)

    async def handler(request):
        calls.append(request)
        decision = "extra brace }" if len(calls) == 1 else json.dumps(last_decision)
        return httpx.Response(
            200, json={"choices": [{"message": {"content": decision}}]}
        )

    bridge = HermesOpenAICompatibilityBridge(
        HermesOpenAIBridgeSettings(
            base_url="http://isolated.test", api_key="test", workflow_task=True
        ),
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(HermesBridgeError) as rejected:
        await bridge.complete(_request(tools=[_tool()]), invocation_observer=observe)
    assert rejected.value.code == "translation_invalid"
    assert len(calls) == 2
    responses = [row for row in captured if row.get("capture_phase") == "response"]
    assert len(responses) == 2
    assert responses[0]["decision_response"]["json_valid"] is False
    detail = responses[1]["decision_response"]
    assert detail["json_valid"] is True
    assert detail["root_type"] == type(last_decision).__name__
    if isinstance(last_decision, dict):
        assert detail["arguments_type"] == type(last_decision["arguments"]).__name__
        assert detail["kind"] in {"tool_call", "invalid"}
    assert "fake-private-value" not in json.dumps(responses)
    assert len(detail["sha256"]) == 64


@pytest.mark.parametrize(
    "content",
    [
        "Cannot continue; password=fake-private-value Bearer fake-private-value",
        json.dumps({"response": "Cannot continue", "password": "fake-private-value"}),
        "x" * 5000,
    ],
)
def test_final_message_diagnostic_is_redacted_and_bounded(content):
    bridge = HermesOpenAICompatibilityBridge(
        HermesOpenAIBridgeSettings(
            base_url="http://isolated.test", api_key="fixture-key", workflow_task=True
        )
    )
    detail = bridge._decision_response_evidence(
        {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({"kind": "message", "content": content})
                    }
                }
            ]
        }
    )
    assert "fake-private-value" not in json.dumps(detail)
    assert len(detail["message_excerpt"]) <= 4096
    assert detail["message_excerpt_truncated"] is (len(content) > 4096)


@pytest.mark.asyncio
async def test_repair_is_complete_when_session_gateway_keeps_only_last_user_message():
    """Hermes replaces request history when an explicit session header is set."""
    calls = []
    image = {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}}

    async def handler(request):
        assert request.headers.get("X-Hermes-Session-Id")
        sent = json.loads(request.content)
        # Emulate a freshly model-locked gateway session: no stored prior turns.
        current = sent["messages"][-1]
        calls.append(current)
        if len(calls) == 1:
            content = "malformed decision }"
        else:
            assert current["role"] == "user"
            assert isinstance(current["content"], list)
            assert image in current["content"]
            text = "".join(p["text"] for p in current["content"] if p["type"] == "text")
            transcript = json.loads(text.split("\n", 1)[1])
            assert transcript["tools"][0]["name"] == "create_graph"
            assert transcript["tools"][0]["parameters"]["required"] == ["title"]
            assert (
                transcript["translation_repair"]["previous_decision"]
                == "malformed decision }"
            )
            assert any(
                "original task" in str(m["content"]) for m in transcript["conversation"]
            )
            content = json.dumps(
                {
                    "kind": "tool_call",
                    "name": "create_graph",
                    "arguments": {"title": "Repaired"},
                }
            )
        return httpx.Response(
            200, json={"choices": [{"message": {"content": content}}]}
        )

    bridge = HermesOpenAICompatibilityBridge(
        HermesOpenAIBridgeSettings(
            base_url="http://isolated.test", api_key="fixture-key", workflow_task=True
        ),
        transport=httpx.MockTransport(handler),
    )
    result = await bridge.complete(
        _request(
            tools=[_tool()],
            tool_choice="required",
            messages=[
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "original task"}, image],
                }
            ],
        )
    )
    assert len(calls) == 2
    assert (
        result["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"]
        == '{"title":"Repaired"}'
    )


@pytest.mark.asyncio
async def test_self_contained_repair_fails_before_second_http_if_context_cannot_fit():
    from dataclasses import replace

    settings = HermesOpenAIBridgeSettings(
        base_url="http://isolated.test", api_key="test", workflow_task=True
    )
    full = HermesOpenAICompatibilityBridge(settings)
    payload = _request(tools=[_tool()], tool_choice="required")
    initial = full._upstream_payload(
        full._validate(payload), translate=True, stream=False
    )
    initial_size = sum(len(m["content"].encode()) for m in initial["messages"])
    calls = []

    async def handler(request):
        calls.append(request)
        assert len(calls) == 1, "Oversize repair must fail before a second submission"
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "x" * 8192}}]}
        )

    bounded = HermesOpenAICompatibilityBridge(
        replace(settings, maximum_translation_prompt_bytes=initial_size + 100),
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(HermesBridgeError) as failure:
        await bounded.complete(payload)
    assert failure.value.code == "workflow_context_limit"
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_upstream_failure_is_observed_before_transport():
    captured = []

    async def observe(invocation):
        captured.append(invocation)

    async def handler(request):
        assert len(captured) == 1
        assert captured[0]["request_digest"] == canonical_digest(
            json.loads(request.content)
        )
        raise httpx.ReadTimeout("Synthetic failure", request=request)

    bridge = HermesOpenAICompatibilityBridge(
        HermesOpenAIBridgeSettings(
            base_url="http://isolated.test", api_key="test", workflow_task=True
        ),
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(HermesBridgeError, match="timed out"):
        await bridge.complete(
            {
                **_request(tools=[_tool()]),
                "wright_instruction_set": saved_instructions().model_dump(mode="json"),
            },
            invocation_observer=observe,
        )
    assert len(captured) == 1


@pytest.mark.parametrize(
    "change", ["null", "provider-authority", "wrong-surface", "missing-helper"]
)
def test_instruction_sidecar_cannot_change_connection_authority_or_fill_missing_assets(
    change,
):
    instructions = saved_instructions().model_dump(mode="json")
    payload = {**_request(tools=[_tool()]), "wright_instruction_set": instructions}
    if change == "null":
        payload["wright_instruction_set"] = None
    elif change == "provider-authority":
        payload["provider"] = "user-specified-provider"
    elif change == "missing-helper":
        instructions["assets"] = [
            asset
            for asset in instructions["assets"]
            if asset["id"] != "bridge.translation-repair"
        ]
    bridge = HermesOpenAICompatibilityBridge(
        HermesOpenAIBridgeSettings(
            base_url="http://isolated.test",
            api_key="test",
            workflow_task=change != "wrong-surface",
        )
    )
    with pytest.raises(HermesBridgeError):
        bridge._validate(payload)
