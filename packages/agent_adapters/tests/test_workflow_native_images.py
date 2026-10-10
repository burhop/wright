"""Native image adapter boundary with synthetic SDK responses; no live account."""

import base64
import json
import sys
from types import SimpleNamespace

import pytest

from agent_adapters.hermes_role_worker import invoke
from agent_adapters import report_generation

from test_hermes_role_worker import sdk as sdk_fixture

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl2ZQAAAABJRU5ErkJggg=="
)


@pytest.fixture
def image_sdk(monkeypatch, tmp_path):
    sdk = sdk_fixture.__wrapped__(monkeypatch, tmp_path)

    def create(**kwargs):
        sdk.calls.append(kwargs)
        return SimpleNamespace(close=lambda: None)

    sdk.state["image"] = base64.b64encode(PNG).decode()
    sdk.state["items"] = None

    def consume(stream, **kwargs):
        return SimpleNamespace(
            model="configured-default",
            usage={"input_tokens": 9, "output_tokens": 12},
            output=sdk.state["items"]
            or [
                {
                    "type": "image_generation_call",
                    "id": "ig_synthetic",
                    "status": "completed",
                    "result": sdk.state["image"],
                }
            ],
        )

    sdk.client._real_client = SimpleNamespace(responses=SimpleNamespace(create=create))
    monkeypatch.setitem(
        sys.modules,
        "agent.codex_runtime",
        SimpleNamespace(_consume_codex_event_stream=consume),
    )
    return sdk


def image_request(resolution):
    return {
        "operation": "generate-image",
        "expected_resolution": resolution,
        "output_format": "png",
        "messages": [
            {"role": "system", "content": "Image-only role; no questions."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Render this part realistically."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:image/png;base64,"
                            + base64.b64encode(PNG).decode()
                        },
                    },
                ],
            },
        ],
    }


def test_native_image_preserves_configured_model_and_enables_only_the_provider_image_tool(
    image_sdk,
):
    probe = invoke({"operation": "probe-image"}, image_sdk.root)
    assert probe["available"] and probe["formats"] == ["png", "jpeg"]
    assert image_sdk.calls == []
    result = invoke(image_request(probe["resolution"]), image_sdk.root)
    body = image_sdk.calls[0]
    assert body["model"] == "configured-default"
    assert body["tools"] == [
        {"type": "image_generation", "action": "edit", "output_format": "png"}
    ]
    assert body["input"][0]["content"][1]["type"] == "input_image"
    assert base64.b64decode(result["image_base64"]) == PNG
    assert result["image_call_id"] == "ig_synthetic"
    assert "synthetic-secret-never-export" not in json.dumps(result)


def test_native_image_can_return_jpeg_using_the_same_configured_connection(image_sdk):
    jpeg = b"\xff\xd8\xff\xc0\x00\x0b\x08\x00\x02\x00\x03\x01\x01\x11\x00\xff\xd9"
    image_sdk.state["image"] = base64.b64encode(jpeg).decode()
    prepared = invoke({"operation": "probe-image"}, image_sdk.root)
    request = image_request(prepared["resolution"])
    request["output_format"] = "jpeg"
    result = invoke(request, image_sdk.root)
    assert base64.b64decode(result["image_base64"]) == jpeg
    assert image_sdk.calls[0]["tools"][0]["output_format"] == "jpeg"


@pytest.mark.parametrize(
    "change",
    [
        "configuration",
        "remote-image",
        "tools",
        "wrong-image-format",
        "unexpected-tool",
        "incomplete",
    ],
)
def test_native_image_rejects_configuration_drift_and_invalid_scope_or_output(
    image_sdk, change
):
    request = image_request(
        invoke({"operation": "probe-image"}, image_sdk.root)["resolution"]
    )
    if change == "configuration":
        image_sdk.runtime["base_url"] = "https://changed.invalid"
    elif change == "remote-image":
        request["messages"][1]["content"][1]["image_url"]["url"] = (
            "https://untrusted.invalid/image.png"
        )
    elif change == "tools":
        request["tools"] = [{"type": "terminal"}]
    elif change == "wrong-image-format":
        request["output_format"] = "jpeg"
    elif change == "unexpected-tool":
        image_sdk.state["items"] = [{"type": "function_call", "name": "terminal"}]
    elif change == "incomplete":
        image_sdk.state["items"] = [
            {"type": "image_generation_call", "status": "in_progress"}
        ]
    with pytest.raises(ValueError):
        invoke(request, image_sdk.root)
    assert len(image_sdk.calls) == (
        1 if change in {"wrong-image-format", "unexpected-tool", "incomplete"} else 0
    )


@pytest.mark.asyncio
async def test_image_response_uses_prepared_resolution_and_keeps_bytes_out_of_text(
    monkeypatch,
):
    calls = []
    resolution = {
        "model_reference": "configured-default",
        "configuration_digest": "a" * 64,
    }

    class Transport:
        async def call(self, request):
            calls.append(request)
            return {
                "image_base64": base64.b64encode(PNG).decode(),
                "output_format": "png",
                "resolution": resolution,
                "response_model": "configured-default",
                "usage": {"input_tokens": 9},
                "tool": "image_generation",
                "image_call_id": "ig_synthetic",
            }

    from agent_adapters.hermes_role import HermesRoleTransport

    monkeypatch.setattr(HermesRoleTransport, "from_host", lambda: Transport())
    result = await report_generation.generate_workflow_response(
        "Render the screenshot.",
        "image-png",
        images=["data:image/png;base64," + base64.b64encode(PNG).decode()],
        expected_resolution=resolution,
    )
    assert calls[0]["expected_resolution"] == resolution
    assert result.wright_image["content"] == PNG
    assert result.wright_outcome["status"] == "completed"
    assert str(result) == "Image generated."
    assert "image_base64" not in result.wright_image["provenance"]
