"""Explicit engineering-image limits do not widen legacy profiles or reply authority."""

import base64
import copy
from datetime import datetime, timezone
from pathlib import Path

import pytest

from core.desktop_reasoning import (
    DesktopActionReply,
    DesktopHarnessBinding,
    DesktopReasoningRequest,
    ENGINEERING_IMAGE_PROFILE,
    decode_desktop_image,
)


def inline(data):
    return "data:image/png;base64," + base64.b64encode(data).decode()


def payload(images, text="Inspect the original images"):
    return {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text},
                    *[
                        {"type": "image_url", "image_url": {"url": url}}
                        for url in images
                    ],
                ],
            }
        ],
        "tools": [],
        "tool_choice": "none",
    }


def request(body, profile=ENGINEERING_IMAGE_PROFILE):
    return DesktopReasoningRequest(
        request_id="request",
        workspace_id="workspace",
        session_id="session",
        run_id="run",
        ordinal=1,
        created_at=datetime(2026, 10, 15, tzinfo=timezone.utc).isoformat(),
        kind="response",
        output_format="text",
        binding=DesktopHarnessBinding(
            connection_id="connection", image_input_profile=profile
        ),
        instruction_set_digest="a" * 64,
        payload=body,
    )


def test_all_six_original_review_images_fit_without_mutation():
    root = Path(__file__).resolve().parents[3]
    directory = (
        root
        / "artifacts/stevecad-demonstrations/prompt-to-reviewed-cad/block-native-006/outputs"
    )
    names = (
        "cad-isometric.png",
        "cad-top.png",
        "cad-front.png",
        "render_isometric.png",
        "render_top.png",
        "render_front.png",
    )
    images = [inline((directory / name).read_bytes()) for name in names]
    body = payload(images)
    before = copy.deepcopy(body)
    accepted = request(body)
    assert body == before == accepted.payload
    assert request(body).digest == accepted.digest
    for name, url in zip(names, images):
        assert (
            decode_desktop_image(url, profile=ENGINEERING_IMAGE_PROFILE)[1]
            == (directory / name).read_bytes()
        )
    for legacy in ("unavailable", "inline-png-jpeg-v1"):
        with pytest.raises(ValueError, match="256 KiB"):
            request(body, legacy)


def test_image_and_text_bounds_are_independent():
    exact = b"\x89PNG\r\n\x1a\n" + b"0" * (2 * 1024 * 1024 - 8)
    assert (
        decode_desktop_image(inline(exact), profile=ENGINEERING_IMAGE_PROFILE)[1]
        == exact
    )
    with pytest.raises(ValueError, match="2 MiB|handoff bound"):
        decode_desktop_image(inline(exact + b"0"), profile=ENGINEERING_IMAGE_PROFILE)
    with pytest.raises(ValueError, match="non-image"):
        request(payload([inline(b"\x89PNG\r\n\x1a\n")], text="a" * 262144))
    with pytest.raises(ValueError, match="eight images"):
        request(payload([inline(b"\x89PNG\r\n\x1a\n")] * 9))
    with pytest.raises(ValueError, match="8 MiB"):
        request(payload([inline(exact)] * 3))
    with pytest.raises(ValueError):
        DesktopActionReply(content="a" * 262145)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.invalid/image.png",
        "data:image/png;base64,!",
        inline(b"not png"),
    ],
)
def test_invalid_image_rejected(url):
    with pytest.raises(
        ValueError, match="inline PNG|encoding is invalid|signature differs"
    ):
        request(payload([url]))


def test_unsupported_shape_and_profile_rejected():
    body = payload([])
    body["messages"][0]["content"].append({"type": "input_image", "image_url": "wrong"})
    with pytest.raises(ValueError, match="exact inline"):
        request(body)
    with pytest.raises(ValueError):
        request(payload([]), "unknown")
    assert (
        request(payload([])).binding.digest
        != request(payload([]), "inline-png-jpeg-v1").binding.digest
    )
