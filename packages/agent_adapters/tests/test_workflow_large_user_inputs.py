"""Large engineering inputs stay complete across the actual Hermes boundary."""
# ruff: noqa: F811

import copy
import json

import httpx
import pytest

from agent_adapters.hermes_openai_bridge import (
    HermesBridgeError,
    _workflow_user_text_parts,
)
from test_workflow_hermes_normalization import normalize  # noqa: F401
from test_workflow_transcript_evidence import TOOL, bridge, reply, request


@pytest.mark.asyncio
@pytest.mark.parametrize("with_image", [False, True])
@pytest.mark.parametrize("repair", [False, True])
async def test_large_user_input_preserves_exact_text_images_roles_and_tools(
    normalize, with_image, repair
):
    # Quotes, control escapes, Unicode and an indivisible long paragraph ensure
    # neither source length nor newline-only splitting can silently lose data.
    text = 'Requirement μm 🛠 "quoted" C:\\parts\n\t\x01' * 1950
    assert len(text) > 65_536
    image = {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}}
    content = (
        [
            {"type": "text", "text": text},
            image,
            {"type": "text", "text": "Final constraint."},
        ]
        if with_image
        else text
    )
    messages = [
        {"role": "system", "content": "Preserve every engineering requirement."},
        {"role": "user", "content": content},
    ]
    original = copy.deepcopy(messages)
    sent = []

    async def handler(call):
        payload = json.loads(call.content)
        sent.append(payload)
        parts = payload["messages"][1]["content"]
        assert isinstance(parts, list)
        assert all(len(p["text"]) <= 65_536 for p in parts if p["type"] == "text")
        normalized = normalize(parts)
        joined = (
            normalized
            if isinstance(normalized, str)
            else "\n".join(p["text"] for p in normalized if p["type"] == "text")
        )
        transcript = json.loads(joined.split("\n", 1)[1])
        assert transcript["conversation"][0] == original[0]
        assert len(transcript["conversation"]) == 2
        actual = transcript["conversation"][1]
        assert actual["role"] == "user"
        assert "".join(p["text"] for p in actual["content"]) == (
            text + "[Reference image 1 attached to this request]Final constraint."
            if with_image
            else text
        )
        assert transcript["tools"] == [TOOL["function"]]
        assert "wright_transcript_omissions" not in transcript
        if with_image:
            assert [p for p in normalized if p["type"] == "image_url"] == [image]
        assert len(joined.encode()) < 120_000
        if repair and len(sent) == 1:
            return httpx.Response(
                200, json={"choices": [{"message": {"content": "invalid decision"}}]}
            )
        return reply()

    await bridge(handler).complete(request(messages))
    assert messages == original
    assert len(sent) == (2 if repair else 1)


@pytest.mark.asyncio
async def test_chunking_does_not_expand_total_budget():
    async def handler(call):
        pytest.fail("The total budget must still reject this request before HTTP")

    with pytest.raises(HermesBridgeError, match="workflow context limit"):
        await bridge(handler).complete(
            request([{"role": "user", "content": "x" * 121_000}])
        )


def test_unknown_text_part_metadata_and_other_roles_remain_untouched():
    for message in (
        {
            "role": "user",
            "content": [{"type": "text", "text": "ok", "extra": "x" * 70_000}],
        },
        {"role": "tool", "content": "x" * 70_000, "tool_call_id": "call1"},
        {"role": "system", "content": "x" * 70_000},
    ):
        original = copy.deepcopy(message)
        assert _workflow_user_text_parts(message) == original
        assert message == original
