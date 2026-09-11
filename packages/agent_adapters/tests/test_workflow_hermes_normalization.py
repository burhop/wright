"""Verify evidence survives Hermes' actual per-text-part normalization boundary."""

import ast
import json
import os
from pathlib import Path
from typing import Any, Dict, List

import httpx
import pytest

from agent_adapters.hermes_openai_bridge import HermesBridgeError
from test_workflow_transcript_evidence import (
    bridge,
    request,
    reply,
    TOOL,
    observation_exchange,
)


def bounded_normalize(content):
    """Portable form of Hermes API's documented scalar/typed-text boundary."""
    if isinstance(content, str):
        return content[:65_536]
    parts = [
        ({**part, "text": part["text"][:65_536]} if part["type"] == "text" else part)
        for part in content
    ]
    return (
        "\n".join(part["text"] for part in parts)
        if all(part["type"] == "text" for part in parts)
        else parts
    )


@pytest.fixture(params=["portable", "installed"])
def normalize(request):
    if request.param == "portable":
        return bounded_normalize
    source = (
        Path(os.environ.get("LOCALAPPDATA", ""))
        / "hermes/hermes-agent/gateway/platforms/api_server.py"
    )
    if not source.is_file():
        pytest.skip("Installed Hermes API source is unavailable on this host")
    # Execute only the two pure normalization functions, never import or start
    # the gateway, agent, model client, profile configuration or credential code.
    tree = ast.parse(source.read_text(encoding="utf-8"))
    names = {"_normalize_chat_content", "_normalize_multimodal_content"}
    functions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in names
    ]
    constants = {
        node.targets[0].id: ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id
        in {"MAX_NORMALIZED_TEXT_LENGTH", "MAX_CONTENT_LIST_SIZE"}
    }
    assert constants["MAX_NORMALIZED_TEXT_LENGTH"] == 65_536
    assert len(functions) == 2
    namespace = {
        "Any": Any,
        "Dict": Dict,
        "List": List,
        **constants,
        "_TEXT_PART_TYPES": {"text", "input_text", "output_text"},
        "_IMAGE_PART_TYPES": {"image_url", "input_image"},
        "_FILE_PART_TYPES": {"file", "input_file"},
    }
    exec(
        compile(ast.Module(body=functions, type_ignores=[]), str(source), "exec"),
        namespace,
    )
    return namespace["_normalize_multimodal_content"]


@pytest.mark.asyncio
@pytest.mark.parametrize("with_image", [False, True])
@pytest.mark.parametrize("repair", [False, True])
async def test_complete_semantic_parts_survive_real_hermes_boundary(
    normalize, with_image, repair
):
    image = {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}}
    task = 'Reference μm; preserve "quoted" paths C:\\parts\\design. ' * 700
    faces = [
        {
            "faceId": f"model1:face{index}",
            "surfaceType": "plane" if index <= 8 else "cylinder",
            "radius": 0.125 if index > 8 else None,
            "observation": "measured " * 170,
        }
        for index in range(1, 15)
    ]
    faces[10]["radius"] = 0.118
    faces[11]["radius"] = 0.038
    variables = {
        "NeutralFactor": 0.48,
        "BendCalculationMethod": 0,
        "native_rows": "v" * 13000,
    }
    messages = [
        {"role": "system", "content": "Inspect every required native observation."},
        {
            "role": "user",
            "content": [{"type": "text", "text": task}, image] if with_image else task,
        },
        *observation_exchange("variables", variables, name="variables", number=4),
        *observation_exchange("faces", {"result": faces}, number=5),
    ]
    tools = [
        TOOL,
        {
            "type": "function",
            "function": {
                **TOOL["function"],
                "name": "variables",
                "description": "0=neutral-factor, 1=bend-deduction, 2=bend-allowance",
            },
        },
    ]
    original = json.dumps(messages)
    sent = []

    async def handler(call):
        payload = json.loads(call.content)
        sent.append(payload)
        content = payload["messages"][1]["content"]
        assert isinstance(content, list)
        text_parts = [p["text"] for p in content if p["type"] == "text"]
        assert len(text_parts) >= 2
        assert all(len(part) <= 65_536 for part in text_parts)
        normalized = normalize(content)
        text = (
            normalized
            if isinstance(normalized, str)
            else "\n".join(p["text"] for p in normalized if p["type"] == "text")
        )
        transcript = json.loads(text.split("\n", 1)[1])
        actual = transcript["conversation"]
        assert actual[0] == messages[0]
        assert (
            actual[1]["content"][0]["text"] if with_image else actual[1]["content"]
        ) == task
        assert json.loads(actual[-1]["content"])["result"]["result"] == faces
        assert json.loads(actual[-3]["content"])["result"] == variables
        assert [t["name"] for t in transcript["tools"]] == [
            "inspect_model",
            "variables",
        ]
        assert "0=neutral-factor" in transcript["tools"][1]["description"]
        assert actual[-2]["tool_calls"][0]["id"] == actual[-1]["tool_call_id"]
        if with_image:
            assert [p for p in normalized if p["type"] == "image_url"] == [image]
        else:
            assert isinstance(normalized, str)
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
        if repair and len(sent) == 1:
            return httpx.Response(
                200, json={"choices": [{"message": {"content": "invalid decision"}}]}
            )
        return reply()

    await bridge(handler).complete(request(messages, tools))
    assert len(sent) == (2 if repair else 1)
    assert json.dumps(messages) == original


@pytest.mark.asyncio
@pytest.mark.parametrize("item", ["task", "observation", "schema"])
async def test_indivisible_oversized_item_fails_before_http(item):
    messages = [{"role": "user", "content": "Inspect every required observation."}]
    tools = [TOOL]
    if item == "task":
        messages[0]["content"] = "x" * 66_000
    elif item == "observation":
        messages.extend(observation_exchange("large", {"evidence": "x" * 66_000}))
    else:
        tools = [
            {
                "type": "function",
                "function": {
                    **TOOL["function"],
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string", "enum": ["x" * 66_000]}
                        },
                    },
                },
            }
        ]

    async def handler(call):
        pytest.fail("Hermes must not receive an item it would silently truncate")

    with pytest.raises(HermesBridgeError, match="per-item text limit") as error:
        await bridge(handler).complete(request(messages, tools))
    assert error.value.code == "workflow_context_limit"
