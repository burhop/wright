from __future__ import annotations

import json

import httpx
import pytest
import agent_adapters.hermes_openai_bridge as bridge_module

from agent_adapters.hermes_openai_bridge import (
    HermesBridgeError,
    HermesOpenAICompatibilityBridge,
    HermesOpenAIBridgeSettings,
)


def _request(**overrides):
    value = {
        "model": "wright-hermes",
        "messages": [{"role": "user", "content": "Build a greeting graph"}],
        "stream": False,
    }
    value.update(overrides)
    return value


def _tool(name="create_graph"):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": "Create a small graph",
            "parameters": {
                "type": "object",
                "properties": {"title": {"type": "string"}},
                "required": ["title"],
                "additionalProperties": False,
            },
        },
    }


def _bridge(handler, *, timeout=5.0, translation_context=""):
    return HermesOpenAICompatibilityBridge(
        HermesOpenAIBridgeSettings(
            base_url="http://127.0.0.1:8642",
            api_key="test-secret-hermes-key",
            timeout_seconds=timeout,
            translation_context=translation_context,
        ),
        transport=httpx.MockTransport(handler),
    )


class _CaptureLogger:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, object]]] = []

    def info(self, event: str, **values: object) -> None:
        self.events.append((event, values))


@pytest.mark.asyncio
async def test_structured_bridge_timing_is_correlated_and_redacted(monkeypatch):
    captured = _CaptureLogger()
    monkeypatch.setattr(bridge_module, "logger", captured)

    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"kind":"tool_call","name":"create_graph",'
                                '"arguments":{"title":"Greeting"}}'
                            )
                        }
                    }
                ]
            },
        )

    await _bridge(handler).complete(
        _request(
            messages=[{"role": "user", "content": "prompt-secret"}],
            tools=[_tool()],
            tool_choice="required",
        ),
        request_id="bridge-correlation",
    )

    assert [event for event, _values in captured.events] == [
        "rivet_ai_bridge_completed"
    ]
    values = captured.events[0][1]
    assert values["request_id"] == "bridge-correlation"
    assert values["tool_count"] == 1
    for name in ("validation_ms", "upstream_ms", "translation_ms", "total_ms"):
        assert isinstance(values[name], float)
        assert values[name] >= 0
    encoded = json.dumps(captured.events)
    assert "test-secret-hermes-key" not in encoded
    assert "prompt-secret" not in encoded


@pytest.mark.asyncio
async def test_plain_completion_uses_hermes_api_and_aliases_model():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "http://127.0.0.1:8642/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer test-secret-hermes-key"
        upstream = json.loads(request.content)
        assert upstream["model"] == "hermes"
        return httpx.Response(
            200,
            json={
                "id": "upstream",
                "object": "chat.completion",
                "created": 10,
                "model": "private-model",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "hello"},
                        "finish_reason": "stop",
                    }
                ],
            },
        )

    result = await _bridge(handler).complete(_request())
    assert result["model"] == "wright-hermes"
    assert result["choices"][0]["message"]["content"] == "hello"
    assert "private-model" not in json.dumps(result)


@pytest.mark.asyncio
async def test_tool_request_translates_and_validates_one_call():
    async def handler(request: httpx.Request) -> httpx.Response:
        upstream = json.loads(request.content)
        prompt = upstream["messages"][-1]["content"]
        assert "create_graph" in prompt
        assert "exactly one JSON object" in prompt
        assert "reuse exact identifiers and port names" in prompt
        assert "retryable error" in prompt
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": '{"kind":"tool_call","name":"create_graph","arguments":{"title":"Greeting"}}',
                        }
                    }
                ]
            },
        )

    result = await _bridge(handler).complete(
        _request(tools=[_tool()], tool_choice="required", parallel_tool_calls=False)
    )
    choice = result["choices"][0]
    assert choice["finish_reason"] == "tool_calls"
    call = choice["message"]["tool_calls"][0]
    assert call["function"] == {
        "name": "create_graph",
        "arguments": '{"title":"Greeting"}',
    }


@pytest.mark.asyncio
async def test_tool_translation_includes_bounded_workspace_mcp_catalog():
    qualified = "server-id__brep.app.status"
    context = json.dumps(
        {
            "schemaVersion": 1,
            "tools": [
                {
                    "qualified_tool_name": qualified,
                    "tool_name": "brep.app.status",
                    "title": "BREP status",
                    "input": {"required": [], "properties": {}},
                }
            ],
        }
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        prompt = json.loads(request.content)["messages"][-1]["content"]
        assert qualified in prompt
        assert "The user must never supply an internal qualified name" in prompt
        assert "useToolNameInput to false" in prompt
        assert "useToolArgumentsInput to true" in prompt
        assert "connect structuredContent and apply catalog paths" in prompt
        assert "do not append [0] after that property" in prompt
        assert "Preserve requested dependencies between MCP nodes" in prompt
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": '{"kind":"tool_call","name":"create_graph","arguments":{"title":"Greeting"}}'
                        }
                    }
                ]
            },
        )

    await _bridge(handler, translation_context=context).complete(
        _request(tools=[_tool()], tool_choice="required")
    )


@pytest.mark.asyncio
async def test_tool_translation_deduplicates_repeated_graph_builder_authority():
    authority = "Use the graph editing tools safely and call one function per turn."
    messages = [{"role": "system", "content": authority} for _ in range(40)]
    messages.extend(
        [
            {"role": "user", "content": "Build the BREP status workflow."},
            {
                "role": "tool",
                "tool_call_id": "current",
                "content": "CURRENT_GRAPH has one configured BREP MCP node.",
            },
        ]
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        prompt = json.loads(request.content)["messages"][-1]["content"]
        assert prompt.count(authority) == 1
        assert "CURRENT_GRAPH has one configured BREP MCP node" in prompt
        assert "prefer it for a new multi-node workflow" in prompt
        assert "validated and applied atomically" in prompt
        assert len(prompt.encode("utf-8")) <= 60_000
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": '{"kind":"tool_call","name":"create_graph","arguments":{"title":"BREP"}}'
                        }
                    }
                ]
            },
        )

    await _bridge(handler).complete(
        _request(messages=messages, tools=[_tool()], tool_choice="required")
    )


@pytest.mark.asyncio
async def test_tool_translation_compacts_protocol_amplified_message_count():
    authority = "Use the graph editing tools safely."
    objective = "Build a connected provider status workflow."
    messages = []
    for index in range(65):
        call_id = f"call-{index}"
        messages.extend(
            [
                {"role": "system", "content": authority},
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": "create_graph",
                                "arguments": '{"title":"chain"}',
                            },
                        }
                    ],
                },
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": f"result-{index}",
                },
                {"role": "user", "content": objective},
            ]
        )

    async def handler(request: httpx.Request) -> httpx.Response:
        prompt = json.loads(request.content)["messages"][-1]["content"]
        assert prompt.count(authority) == 1
        assert prompt.count(objective) == 1
        assert "result-64" in prompt
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"kind":"tool_call","name":"create_graph",'
                                '"arguments":{"title":"connected"}}'
                            )
                        }
                    }
                ]
            },
        )

    result = await _bridge(handler).complete(
        _request(messages=messages, tools=[_tool()], tool_choice="required")
    )

    call = result["choices"][0]["message"]["tool_calls"][0]
    assert call["function"]["arguments"] == '{"title":"connected"}'


@pytest.mark.asyncio
async def test_tool_request_repairs_one_schema_mismatch():
    attempts = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        upstream = json.loads(request.content)
        if attempts == 1:
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": (
                                    '{"kind":"tool_call","name":"create_graph",'
                                    '"arguments":{"authoringChoiceId":"Greeting"}}'
                                ),
                            }
                        }
                    ]
                },
            )
        assert "previous decision was rejected" in upstream["messages"][-1]["content"]
        assert "exact argument property names" in upstream["messages"][-1]["content"]
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": (
                                '{"kind":"tool_call","name":"create_graph",'
                                '"arguments":{"title":"Greeting"}}'
                            ),
                        }
                    }
                ]
            },
        )

    result = await _bridge(handler).complete(
        _request(tools=[_tool()], tool_choice="required", parallel_tool_calls=False)
    )

    assert attempts == 2
    call = result["choices"][0]["message"]["tool_calls"][0]
    assert call["function"] == {
        "name": "create_graph",
        "arguments": '{"title":"Greeting"}',
    }


@pytest.mark.asyncio
async def test_tool_translation_compacts_old_history_and_preserves_current_results():
    messages = [
        {"role": "system", "content": "Use the graph editing tools safely."},
        {
            "role": "user",
            "content": "Create three numeric inputs and connect them to the Onshape tool.",
        },
    ]
    for index in range(35):
        call_id = f"call-{index}"
        messages.extend(
            [
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": "create_graph",
                                "arguments": '{"title":"old"}',
                            },
                        }
                    ],
                },
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": f"stale-result-{index}:" + ("x" * 2_000),
                },
            ]
        )
    messages.extend(
        [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call-current",
                        "type": "function",
                        "function": {
                            "name": "create_graph",
                            "arguments": '{"title":"current"}',
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "tool_call_id": "call-current",
                "content": "CURRENT_RESULT node IDs width length height and onshape-call",
            },
        ]
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        upstream = json.loads(request.content)
        prompt = upstream["messages"][-1]["content"]
        assert len(prompt.encode("utf-8")) <= 60_000
        assert "three numeric inputs" in prompt
        assert "CURRENT_RESULT node IDs width length height and onshape-call" in prompt
        assert "stale-result-0" not in prompt
        json.loads(prompt.split("\n", 1)[1])
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"kind":"tool_call","name":"create_graph",'
                                '"arguments":{"title":"connected"}}'
                            )
                        }
                    }
                ]
            },
        )

    result = await _bridge(handler).complete(
        _request(messages=messages, tools=[_tool()], tool_choice="required")
    )

    call = result["choices"][0]["message"]["tool_calls"][0]
    assert call["function"]["arguments"] == '{"title":"connected"}'


def test_translation_message_compaction_keeps_bounded_head_and_tail():
    content = "HEAD:" + ("x" * 20_000) + ":TAIL"

    compacted = HermesOpenAICompatibilityBridge._compact_translation_message(
        {"role": "tool", "content": content}
    )

    assert compacted["content"].startswith("HEAD:")
    assert compacted["content"].endswith(":TAIL")
    assert "Wright omitted older bounded content" in compacted["content"]
    assert len(compacted["content"].encode("utf-8")) <= 12_000


@pytest.mark.asyncio
async def test_tool_choice_none_bypasses_translation():
    async def handler(request: httpx.Request) -> httpx.Response:
        upstream = json.loads(request.content)
        assert "tools" not in upstream
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {"role": "assistant", "content": "plain"},
                        "finish_reason": "stop",
                    }
                ]
            },
        )

    result = await _bridge(handler).complete(
        _request(tools=[_tool()], tool_choice="none")
    )
    assert result["choices"][0]["message"]["content"] == "plain"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("content", "code"),
    [
        ("```json\n{}\n```", "translation_invalid"),
        ('{"kind":"tool_call","name":"unknown","arguments":{}}', "translation_invalid"),
        (
            '{"kind":"tool_call","name":"create_graph","arguments":{"title":7}}',
            "translation_invalid",
        ),
        (
            '[{"kind":"tool_call","name":"create_graph","arguments":{"title":"a"}}]',
            "translation_invalid",
        ),
    ],
)
async def test_translation_fails_closed(content, code):
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": content}}]},
        )

    with pytest.raises(HermesBridgeError) as caught:
        await _bridge(handler).complete(
            _request(tools=[_tool()], tool_choice="required")
        )
    assert caught.value.code == code
    assert "test-secret-hermes-key" not in str(caught.value)


@pytest.mark.asyncio
async def test_named_choice_rejects_a_different_allowed_tool():
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": '{"kind":"tool_call","name":"other","arguments":{"title":"x"}}'
                        }
                    }
                ]
            },
        )

    with pytest.raises(HermesBridgeError, match="named tool"):
        await _bridge(handler).complete(
            _request(
                tools=[_tool(), _tool("other")],
                tool_choice={"type": "function", "function": {"name": "create_graph"}},
            )
        )


@pytest.mark.asyncio
async def test_standard_sse_shape_for_translation():
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": '{"kind":"tool_call","name":"create_graph","arguments":{"title":"x"}}'
                        }
                    }
                ]
            },
        )

    chunks = [
        part
        async for part in _bridge(handler).stream(
            _request(
                stream=True,
                tools=[_tool()],
                tool_choice="required",
                parallel_tool_calls=False,
            )
        )
    ]
    assert chunks[-1] == "data: [DONE]\n\n"
    joined = "".join(chunks)
    assert '"tool_calls"' in joined
    assert "test-secret-hermes-key" not in joined


@pytest.mark.asyncio
async def test_upstream_auth_failure_and_payload_validation_are_redacted():
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="provider said test-secret-hermes-key")

    with pytest.raises(HermesBridgeError) as caught:
        await _bridge(handler).complete(_request())
    assert caught.value.code == "hermes_auth_failed"
    assert "test-secret-hermes-key" not in str(caught.value)

    bridge = _bridge(handler)
    with pytest.raises(HermesBridgeError) as invalid:
        await bridge.complete(
            _request(
                tools=[_tool()],
                parallel_tool_calls=True,
                tool_choice="required",
            )
        )
    assert invalid.value.code == "unsupported_tool_contract"


@pytest.mark.asyncio
async def test_message_decision_is_allowed_only_for_auto_choice():
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": '{"kind":"message","content":"clarify"}'}}
                ]
            },
        )

    result = await _bridge(handler).complete(
        _request(tools=[_tool()], tool_choice="auto")
    )
    assert result["choices"][0]["message"]["content"] == "clarify"
    with pytest.raises(HermesBridgeError):
        await _bridge(handler).complete(
            _request(tools=[_tool()], tool_choice="required")
        )
