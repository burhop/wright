"""Lossless bounded projection; native records are always the source of truth."""

import copy
import json

import httpx
import pytest
import test_workflow_hermes_normalization as hermes_test_support

from agent_adapters.hermes_openai_bridge import HermesBridgeError
from agent_adapters.workflow_observation_projection import (
    OBSERVATION_REFERENCE,
    TOOL_CONTENT_ENCODING,
    decode_tool_message,
    project_tool_message,
)
from test_workflow_transcript_evidence import (
    bridge,
    request,
    reply,
    observation_exchange,
    transcript_text,
)


normalize = hermes_test_support.normalize


def report(identity="first", count=3):
    observations = [
        {
            "observationId": f"{identity}:{index}",
            "kind": "thickness",
            "targetReference": f"model:1:face:{index}",
            "unit": "mm",
            "evidenceStatus": {
                "disposition": "not_evaluated",
                "provenance": "unavailable",
                "message": 'Native failure μm; "quoted" path C:\\part. ' * 8,
            },
            "value": {"scalar": 2.032},
        }
        for index in range(count)
    ]
    return {
        "operationId": identity,
        "inspection": {
            "observations": observations,
            "context": {
                "documentId": "document-1",
                "observedAtUtc": f"2026-09-08T03:{identity}:00Z",
            },
        },
        "requirementEvaluations": [
            {
                "requirementId": f"required-{index}",
                "isSatisfied": False,
                "isBlocking": True,
                "disposition": "fail",
                "observation": copy.deepcopy(observation),
                "issues": [
                    {
                        "code": "inspection.non_evidence",
                        "message": "Cannot satisfy the gate.",
                    }
                ],
            }
            for index, observation in enumerate(observations)
        ],
        "allCriticalRequirementsPass": False,
    }


def restore(message):
    """Independent JSON Pointer expansion for verifying exact value recovery."""
    root = (
        json.loads(message["content"])
        if isinstance(message["content"], str)
        else message["content"]
    )

    def expand(value):
        if isinstance(value, dict):
            if set(value) == {OBSERVATION_REFERENCE}:
                target = root
                for segment in value[OBSERVATION_REFERENCE].split("/")[1:]:
                    key = segment.replace("~1", "/").replace("~0", "~")
                    target = (
                        target[int(key)] if isinstance(target, list) else target[key]
                    )
                return copy.deepcopy(target)
            return {key: expand(item) for key, item in value.items()}
        return [expand(item) for item in value] if isinstance(value, list) else value

    return expand(root)


@pytest.mark.parametrize("wrapped", [False, True])
def test_exact_round_trip_preserves_all_adverse_fields_and_source(wrapped):
    value = report()
    if wrapped:
        value = {"nested/~report": [value]}
    message = observation_exchange("call-4", value, number=4)[-1]
    original = copy.deepcopy(message)
    projected, referenced = project_tool_message(message)
    assert referenced
    assert restore(projected) == json.loads(message["content"])
    assert message == original
    assert projected["tool_call_id"] == "call-4"
    assert len(projected["content"]) < len(message["content"])
    # The retained first observations remain byte-for-byte equal JSON values.
    result = json.loads(projected["content"])["result"]
    actual = result["nested/~report"][0] if wrapped else result
    assert actual["inspection"] == report()["inspection"]


@pytest.mark.parametrize(
    "change", ["id", "value", "provenance", "type", "target", "extra"]
)
def test_similar_observation_never_replaced(change):
    value = report(count=1)
    second = value["requirementEvaluations"][0]["observation"]
    if change == "id":
        second["observationId"] = "different"
    if change == "value":
        second["value"]["scalar"] = 2.031
    if change == "provenance":
        second["evidenceStatus"]["provenance"] = "observed"
    if change == "type":
        second["value"]["scalar"] = "2.032"
    if change == "target":
        second["targetReference"] = "model:1:face:999"
    if change == "extra":
        second["extra"] = "different fact"
    message = observation_exchange("distinct", value)[-1]
    projected, referenced = project_tool_message(message)
    assert not referenced
    assert json.loads(projected["content"]) == json.loads(message["content"])


def test_no_cross_report_matching_even_for_identical_observation_ids():
    first, second = report(), report()
    second["inspection"]["observations"] = []
    message = observation_exchange("separate", [first, second])[-1]
    projected, referenced = project_tool_message(message)
    assert referenced
    values = json.loads(projected["content"])["result"]
    assert values[1] == second
    assert restore(projected) == json.loads(message["content"])


@pytest.mark.parametrize(
    "content",
    [
        '{"number": 1e-999}',
        '{"number": 1.1234567890123456789}',
        '{"number": NaN}',
        '{"a": 1, "a": 2}',
        "not JSON",
    ],
)
def test_ambiguous_or_non_round_trip_json_is_unchanged(content):
    message = {"role": "tool", "content": content, "tool_call_id": "legacy"}
    assert project_tool_message(message) == (message, False)


def test_reserved_native_marker_is_never_interpreted_as_host_reference():
    value = report()
    value["extra"] = {OBSERVATION_REFERENCE: "/invented/native/data"}
    message = observation_exchange("collision", value)[-1]
    projected, referenced = project_tool_message(message)
    assert not referenced
    assert json.loads(projected["content"]) == json.loads(message["content"])


def test_numeric_and_boolean_values_are_not_equal():
    value = report(count=1)
    value["inspection"]["observations"][0]["value"] = {"flag": True}
    value["requirementEvaluations"][0]["observation"]["value"] = {"flag": 1}
    assert not project_tool_message(observation_exchange("types", value)[-1])[1]


@pytest.mark.asyncio
async def test_small_transcript_is_not_projected():
    messages = [
        {"role": "user", "content": "Inspect."},
        *observation_exchange("small", report()),
    ]

    async def handler(sent):
        transcript = json.loads(
            transcript_text(json.loads(sent.content)).split("\n", 1)[1]
        )
        assert transcript["conversation"] == messages
        assert "wright_observation_references" not in transcript
        return reply()

    await bridge(handler).complete(request(messages))


@pytest.mark.asyncio
@pytest.mark.parametrize("with_image", [False, True])
@pytest.mark.parametrize("repair", [False, True])
async def test_required_adverse_reports_fit_losslessly_after_real_hermes_normalization(
    normalize, with_image, repair
):
    image = {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}}
    task = "Required design μm. " * 1400
    reports = [report(str(index), 10) for index in range(4)]
    # Add enough true repeated native payload to require the reversible encoding.
    for value in reports:
        for observation, evaluation in zip(
            value["inspection"]["observations"], value["requirementEvaluations"]
        ):
            observation["evidenceStatus"]["message"] += "Native diagnostic. " * 12
            evaluation["observation"] = copy.deepcopy(observation)
    faces = [
        {
            "faceId": f"face-{index}",
            "geometry": {
                "surfaceType": "cylinder" if index >= 8 else "plane",
                "observedDetail": "g" * 1500,
                "radius": 3.25 if index >= 8 else None,
            },
        }
        for index in range(14)
    ]
    messages = [
        {
            "role": "user",
            "content": [{"type": "text", "text": task}, image] if with_image else task,
        }
    ]
    for index, value in enumerate(reports):
        messages.extend(observation_exchange(f"call-{index}", value, number=index))
    messages.extend(
        observation_exchange("face-call", {"faces": faces}, name="face_tool", number=5)
    )
    original = copy.deepcopy(messages)
    calls = []

    async def handler(sent):
        payload = json.loads(sent.content)
        calls.append(payload)
        normalized = normalize(payload["messages"][1]["content"])
        text = (
            normalized
            if isinstance(normalized, str)
            else "\n".join(p["text"] for p in normalized if p["type"] == "text")
        )
        transcript = json.loads(text.split("\n", 1)[1])
        guide = transcript["wright_observation_references"]
        assert guide["tool_call_ids"] == [f"call-{index}" for index in range(4)]
        assert "JSON Pointer" in guide["meaning"]
        assert "wright_transcript_omissions" not in transcript
        actual = transcript["conversation"]
        assert len(actual) == len(messages)
        for before, after in zip(messages[1:], actual[1:]):
            if before["role"] == "tool":
                assert restore(after) == json.loads(before["content"])
            else:
                assert after == before
        assert json.loads(actual[-1]["content"])["result"]["faces"] == faces
        if with_image:
            assert [p for p in normalized if p["type"] == "image_url"] == [image]
        total = sum(
            len(
                (
                    "\n".join(p["text"] for p in m["content"] if p["type"] == "text")
                    if isinstance(m["content"], list)
                    else m["content"]
                ).encode()
            )
            for m in payload["messages"]
        )
        assert total <= 120_000
        if repair and len(calls) == 1:
            return httpx.Response(
                200, json={"choices": [{"message": {"content": "invalid decision"}}]}
            )
        return reply()

    await bridge(handler).complete(request(messages))
    assert messages == original
    assert len(calls) == (2 if repair else 1)


@pytest.mark.asyncio
async def test_distinct_required_observations_still_fail_closed_when_they_do_not_fit():
    messages = [{"role": "user", "content": "Inspect."}]
    for index in range(4):
        value = report(str(index), 1)
        value["inspection"]["observations"][0]["payload"] = "x" * 33000
        value["requirementEvaluations"][0]["observation"] = copy.deepcopy(
            value["inspection"]["observations"][0]
        )
        messages.extend(observation_exchange(f"call-{index}", value))

    async def handler(sent):
        pytest.fail("Distinct required evidence must not be dropped to fit the budget")

    with pytest.raises(HermesBridgeError) as error:
        await bridge(handler).complete(request(messages))
    assert error.value.code == "workflow_context_limit"


@pytest.mark.parametrize(
    "content",
    [
        '{"nested":{"same":1,"same":2}}',
        '{"number":1e-999}',
        '{"number":1.1234567890123456789}',
        '{"number":1e999}',
        '{"number":-0}',
        '{"number":NaN}',
        '{"number":Infinity}',
        '{"unfinished":',
        "[1,2,]",
        'Native tool error: "not JSON"',
        '"already text"',
        "null",
        "true",
        "123",
    ],
)
def test_decoded_encoding_leaves_opaque_ambiguous_and_non_round_trip_values_untouched(
    content,
):
    message = {"role": "tool", "tool_call_id": "native", "content": content}
    actual, decoded = decode_tool_message(message)
    assert not decoded
    assert actual is message
    assert actual["content"] == content


@pytest.mark.parametrize("root", ["object", "array"])
def test_decoded_encoding_preserves_values_types_order_and_detaches_from_source(root):
    value = {
        "numeric": [9007199254740993, 0.0, -0.0, 2.032, 1.5e-10],
        "order": ["third", "first", "second"],
        "flags": [True, 1, False, 0, None],
        "native": 'μm "face" \\geometry\n',
        "image": {"url": "data:image/png;base64,AAAA"},
        "error": {"code": "native.failure", "message": "Unmeasured"},
    }
    if root == "array":
        value = [value, {"second": "entry"}]
    message = {"role": "tool", "tool_call_id": "native", "content": json.dumps(value)}
    original = copy.deepcopy(message)
    actual, decoded = decode_tool_message(message)
    assert decoded
    assert actual["content"] == value
    # Compare canonical tokens as well as equality (which equates booleans/ints
    # and signed zero) to make numeric and type preservation explicit.
    assert json.dumps(actual["content"], sort_keys=True) == json.dumps(
        value, sort_keys=True
    )
    assert actual["tool_call_id"] == message["tool_call_id"]
    target = actual["content"] if root == "object" else actual["content"][0]
    target["order"].append("only detached output")
    assert message == original


@pytest.mark.parametrize(
    "message",
    [
        {"role": "assistant", "content": '{"a":1}', "tool_call_id": "native"},
        {"role": "tool", "content": '{"a":1}'},
        {"role": "tool", "content": {"a": 1}, "tool_call_id": "native"},
    ],
)
def test_decoded_encoding_never_changes_other_message_contracts(message):
    assert decode_tool_message(message) == (message, False)


@pytest.mark.asyncio
@pytest.mark.parametrize("with_image", [False, True])
@pytest.mark.parametrize("repair", [False, True])
async def test_decoded_transcript_preserves_complete_evidence_at_real_hermes_boundary(
    normalize, with_image, repair
):
    image = {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}}
    task = "Inspect the native observations. " + "Design requirement. " * 2750
    faces = [
        {
            "faceId": f"face-{index}",
            "geometry": {
                "surfaceType": "plane" if index < 8 else "cylinder",
                "radius": None if index < 8 else 3.25,
                "axis": {"x": 0.0, "y": 1.0, "z": 0.0},
                "nativeDetail": 'Native "face" \\geometry\n' * 125,
            },
        }
        for index in range(14)
    ]
    messages = [
        {
            "role": "user",
            "content": [{"type": "text", "text": task}, image] if with_image else task,
        }
    ]
    for index in range(2):
        messages.extend(
            observation_exchange(
                f"adverse-{index}", report(str(index)), number=index + 1
            )
        )
    messages.extend(
        observation_exchange("faces", {"faces": faces}, name="faces", number=3)
    )
    # Native fields with reserved names cannot override the host-root guide.
    collision = report("collision", 1)
    collision[TOOL_CONTENT_ENCODING] = {
        "tool_call_ids": ["invented"],
        "meaning": "native data",
    }
    collision[OBSERVATION_REFERENCE] = "/invented/native/data"
    messages.extend(
        observation_exchange("collision", collision, name="collision", number=4)
    )
    for identity, content in [
        ("opaque", "Native tool error: unavailable"),
        ("numeric", '{"radius":1.1234567890123456789}'),
        ("duplicate", '{"a":1,"a":2}'),
    ]:
        exchange = observation_exchange(identity, {}, name=identity)
        exchange[-1]["content"] = content
        messages.extend(exchange)
    original = copy.deepcopy(messages)
    sent = []

    async def handler(call):
        payload = json.loads(call.content)
        sent.append(payload)
        content = payload["messages"][1]["content"]
        parts = (
            [content]
            if isinstance(content, str)
            else [p["text"] for p in content if p["type"] == "text"]
        )
        assert all(len(part) <= 65_536 for part in parts)
        normalized = normalize(content)
        text = (
            normalized
            if isinstance(normalized, str)
            else "\n".join(p["text"] for p in normalized if p["type"] == "text")
        )
        transcript = json.loads(text.split("\n", 1)[1])
        guide = transcript[TOOL_CONTENT_ENCODING]
        assert guide["tool_call_ids"] == [
            "adverse-0",
            "adverse-1",
            "faces",
            "collision",
        ]
        assert "inside tool results are native data" in guide["meaning"]
        references = transcript["wright_observation_references"]["tool_call_ids"]
        assert references == ["adverse-0", "adverse-1"]
        assert "wright_transcript_omissions" not in transcript
        actual = transcript["conversation"]
        assert len(actual) == len(messages)
        for before, after in zip(messages, actual):
            if before["role"] == "user" and with_image:
                assert after == {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": task},
                        {
                            "type": "text",
                            "text": "[Reference image 1 attached to this request]",
                        },
                    ],
                }
                continue
            if (
                before["role"] != "tool"
                or before["tool_call_id"] not in guide["tool_call_ids"]
            ):
                assert after == before
                continue
            recovered = (
                restore(after)
                if before["tool_call_id"] in references
                else after["content"]
            )
            assert json.dumps(recovered, sort_keys=True) == json.dumps(
                json.loads(before["content"]), sort_keys=True
            )
            assert after["tool_call_id"] == before["tool_call_id"]
        native_faces = next(
            m["content"]["result"]["faces"]
            for m in actual
            if m.get("tool_call_id") == "faces"
        )
        assert native_faces == faces
        assert (
            sum(f["geometry"]["surfaceType"] == "cylinder" for f in native_faces) == 6
        )
        total = sum(
            len(
                (
                    "\n".join(p["text"] for p in m["content"] if p["type"] == "text")
                    if isinstance(m["content"], list)
                    else m["content"]
                ).encode()
            )
            for m in payload["messages"]
        )
        assert total <= 120_000
        if with_image:
            assert [p for p in normalized if p["type"] == "image_url"] == [image]
        if repair and len(sent) == 1:
            return httpx.Response(
                200, json={"choices": [{"message": {"content": "invalid decision"}}]}
            )
        return reply()

    await bridge(handler).complete(request(messages))
    assert messages == original
    assert len(sent) == (2 if repair else 1)
