"""Bounded native image output over the installed model SDK, without local tools."""

from __future__ import annotations

import base64
import binascii
import hashlib

MAX_IMAGE_BYTES = 12 * 1024 * 1024


def image_capabilities(client, resolution):
    native = getattr(client, "_real_client", None)
    available = (
        resolution["provider"] == "openai-codex"
        and resolution["api_mode"] == "codex_responses"
        and callable(getattr(getattr(native, "responses", None), "create", None))
    )
    return {
        "ok": True,
        "available": available,
        "formats": ["png", "jpeg"] if available else [],
        "resolution": resolution,
        "reason": None
        if available
        else "This configured AI connection has no qualified native image-output transport.",
    }


def generate_native_image(client, resolution, request, *, sdk_observer=None):
    if not image_capabilities(client, resolution)["available"]:
        raise ValueError("Native image output is unavailable")
    fmt = request.get("output_format")
    messages = request.get("messages")
    if (
        fmt not in {"png", "jpeg"}
        or not isinstance(messages, list)
        or len(messages) != 2
        or [m.get("role") for m in messages if isinstance(m, dict)]
        != ["system", "user"]
        or any(set(m) != {"role", "content"} for m in messages)
        or not isinstance(messages[0]["content"], str)
        or not isinstance(messages[1]["content"], list)
    ):
        raise ValueError("Invalid scoped image request")
    parts = []
    image_count = 0
    for part in messages[1]["content"]:
        if not isinstance(part, dict):
            raise ValueError("Invalid image input")
        if (
            set(part) == {"type", "text"}
            and part["type"] == "text"
            and isinstance(part["text"], str)
        ):
            parts.append({"type": "input_text", "text": part["text"]})
        elif set(part) == {"type", "image_url"} and part["type"] == "image_url":
            image = part["image_url"]
            url = image.get("url") if isinstance(image, dict) else None
            if not isinstance(url, str) or not url.startswith(
                ("data:image/png;base64,", "data:image/jpeg;base64,")
            ):
                raise ValueError("Only prepared workspace image bytes are accepted")
            parts.append({"type": "input_image", "image_url": url})
            image_count += 1
        else:
            raise ValueError("Unsupported image input part")
    if (
        not parts
        or image_count > 8
        or not any(p["type"] == "input_text" and p["text"].strip() for p in parts)
    ):
        raise ValueError("Supply bounded image instructions")
    from agent.codex_runtime import _consume_codex_event_stream

    sdk_payload = dict(
        model=resolution["model_reference"],
        instructions=messages[0]["content"],
        input=[{"role": "user", "content": parts}],
        tools=[
            {
                "type": "image_generation",
                "action": "edit" if image_count else "generate",
                "output_format": fmt,
            }
        ],
        tool_choice={"type": "image_generation"},
        store=False,
        stream=True,
        timeout=120,
    )
    if sdk_observer is not None:
        sdk_observer(sdk_payload, resolution)
    stream = client._real_client.responses.create(**sdk_payload)
    try:
        final = _consume_codex_event_stream(stream, model=resolution["model_reference"])
    finally:
        stream.close()

    def field(item, key):
        return item.get(key) if isinstance(item, dict) else getattr(item, key, None)

    items = getattr(final, "output", None) or []
    if any(
        field(item, "type") not in {"reasoning", "message", "image_generation_call"}
        for item in items
    ):
        raise ValueError("Unexpected capability in image response")
    generated = [
        item for item in items if field(item, "type") == "image_generation_call"
    ]
    if len(generated) != 1 or field(generated[0], "status") != "completed":
        raise ValueError("No completed image output")
    encoded = field(generated[0], "result")
    if not isinstance(encoded, str) or len(encoded) > MAX_IMAGE_BYTES * 4 // 3 + 4:
        raise ValueError("Image output exceeds its bound")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error):
        raise ValueError("Invalid image output") from None
    signature = b"\x89PNG\r\n\x1a\n" if fmt == "png" else b"\xff\xd8\xff"
    if not raw.startswith(signature) or len(raw) > MAX_IMAGE_BYTES:
        raise ValueError("Image output does not match the declared format")
    usage = field(final, "usage")
    counts = {
        key: field(usage, key)
        for key in ("input_tokens", "output_tokens", "total_tokens")
    }
    return {
        "ok": True,
        "resolution": resolution,
        "image_base64": encoded,
        "output_format": fmt,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "usage": {
            key: value
            for key, value in counts.items()
            if type(value) is int and value >= 0
        },
        "response_model": field(final, "model") or resolution["model_reference"],
        "tool": "image_generation",
        "image_call_id": field(generated[0], "id"),
    }
