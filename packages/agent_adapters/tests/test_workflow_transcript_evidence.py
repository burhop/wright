"""Transport coverage for complete engineering inputs and native observations."""

import json

import httpx
import pytest

from agent_adapters.hermes_openai_bridge import (
    HermesBridgeError,
    HermesOpenAIBridgeSettings,
    HermesOpenAICompatibilityBridge,
)


TOOL = {
    "type": "function",
    "function": {
        "name": "inspect_model",
        "description": "Inspect the identified model.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
}


def exchange(identity, result):
    return [
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": identity,
                    "type": "function",
                    "function": {"name": "inspect_model", "arguments": "{}"},
                }
            ],
        },
        {"role": "tool", "tool_call_id": identity, "content": result},
    ]


def observation_exchange(
    identity,
    result,
    *,
    name="inspect_model",
    arguments=None,
    number=None,
    status="succeeded",
):
    """Use the actual workflow executor envelope for evictable observations."""
    messages = exchange(
        identity,
        json.dumps(
            {
                "tool_call_number": number,
                "status": status,
                "result": result,
                "text": "",
            }
        ),
    )
    messages[0]["tool_calls"][0]["function"] = {
        "name": name,
        "arguments": json.dumps(arguments or {}),
    }
    return messages


def bridge(handler, **settings):
    return HermesOpenAICompatibilityBridge(
        HermesOpenAIBridgeSettings(
            base_url="http://127.0.0.1:8642",
            api_key="test-only",
            workflow_task=True,
            maximum_translation_prompt_bytes=120_000,
            **settings,
        ),
        transport=httpx.MockTransport(handler),
    )


def request(messages, tools=None):
    return {"model": "wright-hermes", "messages": messages, "tools": tools or [TOOL]}


def reply():
    return httpx.Response(
        200,
        json={
            "choices": [
                {
                    "message": {
                        "content": '{"kind":"tool_call","name":"inspect_model","arguments":{}}',
                    }
                }
            ]
        },
    )


def transcript_text(upstream):
    content = upstream["messages"][1]["content"]
    prompt = (
        "\n".join(part["text"] for part in content if part.get("type") == "text")
        if isinstance(content, list)
        else content
    )
    assert len(prompt.encode("utf-8")) <= 120_000
    return prompt


def conversation(upstream):
    prompt = transcript_text(upstream)
    return json.loads(prompt.split("\n", 1)[1])["conversation"]


@pytest.mark.asyncio
async def test_complete_large_task_and_middle_geometry_survive_transport_with_image():
    task = (
        "Préface μm. " * 1400
        + "HOLES MUST BE 25 mm FROM THE FREE EDGE."
        + " Finish." * 1700
    )
    faces = [
        {"face_id": f"face-{index}", "observed": "surface " * 32}
        for index in range(100)
    ]
    faces[50] = {"face_id": "critical-hole", "distance_to_free_edge_mm": 23.3998}
    measurement = json.dumps({"faces": faces})
    image = {
        "type": "image_url",
        "image_url": {"url": "data:image/png;base64," + "AAAA" * 16000},
    }
    messages = [
        {
            "role": "system",
            "content": "Compare actual dimensions; do not assume acceptance.",
        },
        {"role": "user", "content": [{"type": "text", "text": task}, image]},
        *exchange("measurement", measurement),
    ]
    before = json.dumps(messages)

    async def handler(sent):
        upstream = json.loads(sent.content)
        actual = conversation(upstream)
        assert actual[1]["content"][0]["text"] == task
        assert actual[-1]["content"] == measurement
        assert json.loads(actual[-1]["content"])["faces"][50] == faces[50]
        assert upstream["messages"][1]["content"][-1] == image
        assert actual[-2]["tool_calls"][0]["id"] == actual[-1]["tool_call_id"]
        return reply()

    await bridge(handler).complete(request(messages))
    assert json.dumps(messages) == before


@pytest.mark.asyncio
@pytest.mark.parametrize("maximum_messages", [128, 9])
async def test_compaction_removes_whole_old_exchanges_and_preserves_instructions(
    maximum_messages,
):
    instructions = [
        {"role": "system", "content": "Preserve the source model."},
        {
            "role": "developer",
            "content": "Failed evidence cannot release manufacturing.",
        },
        {"role": "user", "content": "Make and measure the requested bracket."},
    ]
    messages = [*instructions]
    for index in range(70):
        messages.extend(observation_exchange(f"old-{index}", {"history": "x" * 2200}))
    latest = json.dumps(
        {"faces": [{"id": index, "geometry": "x" * 200} for index in range(140)]}
    )
    messages.extend(exchange("latest", latest))
    correction = {
        "role": "user",
        "content": "Keep all four holes; report failures accurately.",
    }
    messages.append(correction)

    async def handler(sent):
        actual = conversation(json.loads(sent.content))
        assert len(actual) <= maximum_messages
        assert actual[:3] == instructions
        assert actual[-1] == correction
        assert actual[-2]["content"] == latest
        assert actual[-3]["tool_calls"][0]["id"] == "latest"
        calls = {
            call["id"] for message in actual for call in message.get("tool_calls", [])
        }
        results = {
            message["tool_call_id"] for message in actual if message["role"] == "tool"
        }
        assert calls == results
        assert "old-0" not in calls
        return reply()

    await bridge(handler, maximum_messages=maximum_messages).complete(request(messages))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "overflow", ["task", "observation", "schemas", "message_count"]
)
async def test_required_current_context_overflow_fails_before_model_call(overflow):
    calls = []

    async def handler(sent):
        calls.append(sent)
        pytest.fail("Incomplete engineering evidence must never reach the model")

    messages = [{"role": "user", "content": "Inspect the supplied part."}]
    tools = [TOOL]
    settings = {}
    if overflow == "task":
        messages[0]["content"] = "μ" * 65000
    if overflow == "schemas":
        tools = [
            {
                "type": "function",
                "function": {
                    **TOOL["function"],
                    "parameters": {
                        "type": "object",
                        "properties": {"value": {"enum": ["x" * 121000]}},
                    },
                },
            }
        ]
    if overflow == "message_count":
        settings["maximum_messages"] = 3
    messages.extend(
        exchange("latest", "x" * 121000 if overflow == "observation" else "current")
    )
    # A short newest user message must not cause the newest tool evidence to be evicted.
    messages.append({"role": "user", "content": "Evaluate that observation."})
    with pytest.raises(HermesBridgeError, match="no evidence was truncated") as error:
        await bridge(handler, **settings).complete(request(messages, tools))
    assert error.value.code == "workflow_context_limit"
    assert calls == []


@pytest.mark.asyncio
async def test_multi_result_exchange_is_retained_as_one_complete_observation():
    messages = [{"role": "user", "content": "Compare both measurements."}]
    for index in range(8):
        messages.extend(observation_exchange(f"old-{index}", "old measurement"))
    latest = exchange("dimension", "dimension result")
    latest[0]["tool_calls"].append(
        {
            "id": "holes",
            "type": "function",
            "function": {"name": "inspect_model", "arguments": "{}"},
        }
    )
    latest.append({"role": "tool", "tool_call_id": "holes", "content": "holes result"})
    messages.extend(latest)

    async def handler(sent):
        actual = conversation(json.loads(sent.content))
        assert actual == [messages[0], *latest]
        return reply()

    await bridge(handler, maximum_messages=5).complete(request(messages))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "rejected", ["x" * 8192, "μ" * 8192], ids=["ascii", "multibyte"]
)
async def test_retry_overflow_does_not_send_incomplete_current_evidence(rejected):
    sent = []
    task = "required " + "x" * 58400

    async def handler(request):
        sent.append(json.loads(request.content))
        assert len(sent) == 1, "Oversized retry must fail before transport"
        assert [message["content"] for message in conversation(sent[0])] == [task, task]
        return httpx.Response(
            200, json={"choices": [{"message": {"content": rejected}}]}
        )

    with pytest.raises(HermesBridgeError) as error:
        await bridge(handler).complete(
            request(
                [{"role": "user", "content": task}, {"role": "user", "content": task}]
            )
        )
    assert error.value.code == "workflow_context_limit"
    assert len(sent) == 1


@pytest.mark.asyncio
async def test_retry_budget_evicts_only_older_exchanges_and_preserves_latest_evidence():
    messages = [{"role": "user", "content": "Verify actual geometry."}]
    for index in range(35):
        messages.extend(observation_exchange(f"old-{index}", "x" * 3000))
    latest = exchange("latest", "CURRENT MEASUREMENTS " + "μ" * 4000)
    messages.extend(latest)
    sent = []

    async def handler(request):
        payload = json.loads(request.content)
        sent.append(payload)
        actual = conversation(payload)
        assert actual[-2:] == latest
        if len(sent) == 1:
            return httpx.Response(
                200, json={"choices": [{"message": {"content": "μ" * 8192}}]}
            )
        assert len(actual) < len(conversation(sent[0]))
        assert (
            sum(
                len(
                    (
                        "\n".join(
                            p["text"]
                            for p in message["content"]
                            if p.get("type") == "text"
                        )
                        if isinstance(message["content"], list)
                        else message["content"]
                    ).encode("utf-8")
                )
                for message in payload["messages"]
            )
            <= 120000
        )
        calls = {
            call["id"] for message in actual for call in message.get("tool_calls", [])
        }
        results = {
            message["tool_call_id"] for message in actual if message["role"] == "tool"
        }
        assert calls == results
        return reply()

    await bridge(handler).complete(request(messages))
    assert len(sent) == 2


@pytest.mark.asyncio
async def test_compaction_preserves_each_tool_and_discloses_different_argument_history():
    image = {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}}
    instructions = [
        {"role": "system", "content": "Inspect before releasing the model."},
        {"role": "developer", "content": "Preserve all critical requirements."},
        {
            "role": "user",
            "content": [{"type": "text", "text": "Requirements " + "x" * 52000}, image],
        },
    ]
    messages = [*instructions]
    records = [
        ("server_info", {"provider": "solid_edge"}),
        ("status", {"connected": True}),
        ("capabilities", {"capabilities": "c" * 5000}),
        ("features", {"features": "f" * 4000}),
        ("variables", {"variables": "v" * 8500}),
    ]
    for number, (name, result) in enumerate(records, 1):
        messages.extend(observation_exchange(name, result, name=name, number=number))
    for number, unit in ((6, "mm"), (7, "in")):
        messages.extend(
            observation_exchange(
                f"faces-{unit}",
                {
                    "geometry": "g" * 30000,
                    "unit": unit,
                    "evidenceStatus": {
                        "disposition": "not_evaluated",
                        "provenance": "observed",
                    },
                },
                name="faces",
                arguments={"documentId": "model-1", "unit": unit},
                number=number,
            )
        )
    original = json.dumps(messages)

    async def handler(sent):
        upstream = json.loads(sent.content)
        actual = conversation(upstream)
        retained = {
            call["id"] for message in actual for call in message.get("tool_calls", [])
        }
        assert retained == {name for name, _ in records} | {"faces-in"}
        results = {
            message["tool_call_id"] for message in actual if message["role"] == "tool"
        }
        assert retained == results
        assert actual[:2] == instructions[:2]
        assert actual[2]["content"][0] == instructions[2]["content"][0]
        assert upstream["messages"][1]["content"][-1] == image
        payload = json.loads(transcript_text(upstream).split("\n", 1)[1])
        omission = payload["wright_transcript_omissions"]
        assert "does not prove an earlier result superseded" in omission["notice"]
        assert "never obtained" in omission["notice"]
        assert len(omission["exchanges"]) == 1
        omitted = omission["exchanges"][0]
        assert omitted["tool_call_number"] == 6
        assert omitted["tool"] == "faces"
        assert json.loads(omitted["arguments"]) == {
            "documentId": "model-1",
            "unit": "mm",
        }
        assert (
            json.loads(actual[-2]["tool_calls"][0]["function"]["arguments"])["unit"]
            == "in"
        )
        assert json.loads(actual[-1]["content"])["result"]["geometry"] == "g" * 30000
        return reply()

    await bridge(handler).complete(request(messages))
    assert json.dumps(messages) == original


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "earlier",
    [
        observation_exchange("earlier", {}, status="failed"),
        observation_exchange("earlier", {}, status="invalid_arguments"),
        observation_exchange(
            "earlier",
            {"evidenceStatus": {"disposition": "fail", "provenance": "observed"}},
        ),
        observation_exchange(
            "earlier",
            {
                "evidenceStatus": {
                    "disposition": "not_evaluated",
                    "provenance": "unavailable",
                }
            },
        ),
        observation_exchange("earlier", {"allCriticalRequirementsPass": False}),
        # A recognizable verification report is conservatively retained even if partial or marked pass.
        observation_exchange("earlier", {"inspection": {"status": "pass"}}),
        observation_exchange("earlier", {"status": "unverified"}),
        observation_exchange("earlier", {"isValid": False}),
        observation_exchange("earlier", {"isSuccess": False}),
        observation_exchange("earlier", {"isSatisfied": False}),
        observation_exchange("earlier", {"overall": "fail"}),
        observation_exchange("earlier", {"overall": {"disposition": "fail"}}),
        observation_exchange("earlier", {"verdict": "pass"}),
        exchange("earlier", "Unknown provider envelope"),
    ],
)
async def test_earlier_unsuccessful_or_uncertain_evidence_is_not_evicted_by_later_success(
    earlier,
):
    latest = observation_exchange("latest", {"observed": 25})
    messages = [
        {"role": "user", "content": "Compare observations, including failures."},
        *earlier,
        *observation_exchange("evictable", {"observed": 24}),
        *latest,
    ]

    async def handler(sent):
        actual = conversation(json.loads(sent.content))
        assert actual == [messages[0], *earlier, *latest]
        return reply()

    await bridge(handler, maximum_messages=5).complete(request(messages))


@pytest.mark.asyncio
async def test_required_distinct_tool_floor_overflow_fails_without_model_request():
    messages = [{"role": "user", "content": "Inspect all evidence."}]
    for name in ("features", "variables", "faces"):
        messages.extend(
            observation_exchange(name, {"evidence": "x" * 45000}, name=name)
        )

    async def handler(sent):
        pytest.fail("Do not trade away a unique observation to fit the prompt")

    with pytest.raises(HermesBridgeError) as error:
        await bridge(handler).complete(request(messages))
    assert error.value.code == "workflow_context_limit"


@pytest.mark.asyncio
async def test_omission_metadata_is_part_of_required_context_budget():
    # A large argument on an earlier call cannot be silently lost in a tiny notice.
    messages = [
        {"role": "user", "content": "Preserve source identity."},
        *observation_exchange(
            "earlier", {"old": True}, arguments={"selector": "x" * 120000}
        ),
        *observation_exchange("latest", {"current": True}),
    ]

    async def handler(sent):
        pytest.fail("The required omission notice must fit before transport")

    with pytest.raises(HermesBridgeError) as error:
        await bridge(handler).complete(request(messages))
    assert error.value.code == "workflow_context_limit"


@pytest.mark.asyncio
async def test_schema_repair_identifies_nested_missing_field():
    tool = {
        "type": "function",
        "function": {
            **TOOL["function"],
            "parameters": {
                "type": "object",
                "properties": {
                    "recipe": {
                        "type": "object",
                        "properties": {"height": {"type": "number"}},
                        "required": ["height"],
                    }
                },
                "required": ["recipe"],
            },
        },
    }
    sent = []

    async def handler(request):
        payload = json.loads(request.content)
        sent.append(payload)
        if len(sent) == 2:
            correction = payload["messages"][-1]["content"]
            assert '"path":["recipe"]' in correction
            assert '"missing":["height"]' in correction
        arguments = {"recipe": {} if len(sent) == 1 else {"height": 60}}
        decision = {
            "kind": "tool_call",
            "name": "inspect_model",
            "arguments": arguments,
        }
        return httpx.Response(
            200, json={"choices": [{"message": {"content": json.dumps(decision)}}]}
        )

    result = await bridge(handler).complete(
        request([{"role": "user", "content": "Inspect."}], [tool])
    )
    assert len(sent) == 2
    assert (
        json.loads(
            result["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"]
        )["recipe"]["height"]
        == 60
    )


@pytest.mark.asyncio
async def test_schema_failure_reports_location_and_type_without_argument_values():
    secret = "SENSITIVE-ARGUMENT-VALUE"
    tool = {
        "type": "function",
        "function": {
            **TOOL["function"],
            "parameters": {
                "type": "object",
                "properties": {"height": {"type": "number"}},
            },
        },
    }

    async def handler(request):
        decision = {
            "kind": "tool_call",
            "name": "inspect_model",
            "arguments": {"height": secret},
        }
        return httpx.Response(
            200, json={"choices": [{"message": {"content": json.dumps(decision)}}]}
        )

    with pytest.raises(HermesBridgeError) as error:
        await bridge(handler).complete(
            request([{"role": "user", "content": "Inspect."}], [tool])
        )
    assert '"path":["height"]' in str(error.value)
    assert '"expected_type":"number"' in str(error.value)
    assert secret not in str(error.value)
