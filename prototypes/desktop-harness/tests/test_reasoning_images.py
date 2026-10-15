import base64
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from core.desktop_reasoning import DesktopHarnessBinding, DesktopReasoningRequest


@pytest.fixture(
    params=[
        (kind, profile)
        for kind in ("response", "action")
        for profile in ("inline-png-jpeg-v1", "inline-png-jpeg-engineering-v1")
    ]
)
def image_case(monkeypatch, request):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from mcp_bridge import server

    kind, profile = request.param
    root = Path(__file__).resolve().parents[3]
    image_path = (
        "artifacts/stevecad-demonstrations/qualification/native/06-inspect-coupon-1.png"
        if profile == "inline-png-jpeg-v1"
        else "artifacts/stevecad-demonstrations/prompt-to-reviewed-cad/block-native-006/outputs/render_isometric.png"
    )
    data = (root / image_path).read_bytes()
    encoded = base64.b64encode(data).decode()
    request = DesktopReasoningRequest(
        request_id="request",
        workspace_id="workspace",
        session_id="session",
        run_id="run",
        ordinal=1,
        created_at="2026-10-14T00:00:00Z",
        kind=kind,
        output_format="text",
        binding=DesktopHarnessBinding(
            connection_id="connection", image_input_profile=profile
        ),
        instruction_set_digest="a" * 64,
        payload={
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Inspect"},
                        {
                            "type": "image_url",
                            "image_url": {"url": "data:image/png;base64," + encoded},
                        },
                    ],
                }
            ]
        },
    )
    item = {
        "request": request.model_dump(mode="json"),
        "request_digest": request.digest,
        "binding_digest": request.binding.digest,
    }
    client = SimpleNamespace(
        scope=AsyncMock(),
        call=AsyncMock(return_value=[item]),
        binding=request.binding.model_dump(mode="json"),
    )
    args = {
        "workspace_id": "workspace",
        "session_id": "session",
        "request_id": "request",
        "request_digest": request.digest,
        "binding_digest": request.binding.digest,
        "image_index": 0,
    }
    return server(client), client, item, args, data, encoded


@pytest.mark.asyncio
async def test_exact_pending_image_is_content_not_text_and_projection_does_not_mutate(
    image_case,
):
    server, client, item, args, data, encoded = image_case
    before = json.dumps(item, sort_keys=True)
    pending_content = await server.call_tool(
        "wright_reasoning_pending", {k: args[k] for k in ("workspace_id", "session_id")}
    )
    pending = json.loads(pending_content[0].text)
    assert encoded not in json.dumps(pending)
    assert pending["tasks"][0]["request_digest"] == args["request_digest"]
    assert (
        pending["tasks"][0]["image_references"][0]["sha256"]
        == hashlib.sha256(data).hexdigest()
    )
    assert json.dumps(item, sort_keys=True) == before
    result = await server.call_tool("wright_reasoning_image", args)
    images = [part for part in result.content if part.type == "image"]
    assert len(images) == 1 and images[0].mimeType == "image/png"
    assert base64.b64decode(images[0].data) == data
    assert encoded not in json.dumps(result.structuredContent)
    assert all(call.args[0] == "GET" for call in client.call.call_args_list)
    assert json.dumps(item, sort_keys=True) == before


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "patch",
    [
        {"request_digest": "b" * 64},
        {"binding_digest": "b" * 64},
        {"request_id": "other"},
        {"image_index": -1},
        {"image_index": 1},
        {"workspace_id": "other"},
    ],
)
async def test_wrong_request_scope_digest_or_image_index_is_denied(image_case, patch):
    server, client, _, args, _, _ = image_case
    with pytest.raises(Exception):
        await server.call_tool("wright_reasoning_image", {**args, **patch})
    assert all(call.args[0] == "GET" for call in client.call.call_args_list)


@pytest.mark.asyncio
async def test_image_from_previous_connection_is_not_delivered(image_case):
    server, client, _, args, _, _ = image_case
    client.binding = {**client.binding, "connection_id": "replacement-connection"}
    with pytest.raises(Exception, match="another frozen connection"):
        await server.call_tool("wright_reasoning_image", args)
