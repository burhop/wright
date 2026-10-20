"""Bounded desktop handoff receipts, independent of workflow run authority."""

import base64
import binascii
from copy import deepcopy
from typing import Annotated, Literal

from pydantic import Field, JsonValue, StringConstraints, model_validator

from .process_interactions import Timestamp
from .process_validation import (
    Contract,
    Digest,
    Identifier,
    canonical_digest,
    canonical_json,
)


ReplyText = Annotated[
    str, StringConstraints(strict=True, min_length=1, max_length=262144)
]

ENGINEERING_IMAGE_PROFILE = "inline-png-jpeg-engineering-v1"


def desktop_image_url(part):
    """Accept the shared MCP producer's high-detail hint without widening media.

    The hint remains request provenance, not proof of the desktop model's
    resolution. Byte/profile validation is still required by each caller.
    """
    image = part.get("image_url") if isinstance(part, dict) else None
    if (
        not isinstance(part, dict)
        or set(part) != {"type", "image_url"}
        or part["type"] != "image_url"
        or not isinstance(image, dict)
        or not (
            set(image) == {"url"}
            or (set(image) == {"url", "detail"} and image["detail"] == "high")
        )
    ):
        raise ValueError("Desktop image parts require the exact inline image contract")
    return image["url"]


def decode_desktop_image(url, *, profile="inline-png-jpeg-v1"):
    """Validate bounded inline bytes; never fetch, transform or repair an image."""
    if profile not in {"inline-png-jpeg-v1", ENGINEERING_IMAGE_PROFILE}:
        raise ValueError("Desktop image profile unavailable")
    maximum = (
        262144
        if profile == "inline-png-jpeg-v1"
        else 4 * ((2 * 1024 * 1024 + 2) // 3) + 23
    )
    if not isinstance(url, str) or len(url) > maximum:
        raise ValueError("Desktop inline image exceeds the handoff bound")
    prefix, separator, encoded = url.partition(";base64,")
    if not separator or prefix not in {"data:image/png", "data:image/jpeg"}:
        raise ValueError("Desktop images require inline PNG or JPEG")
    try:
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error):
        raise ValueError("Desktop inline image encoding is invalid") from None
    if profile == ENGINEERING_IMAGE_PROFILE and len(data) > 2 * 1024 * 1024:
        raise ValueError("Desktop engineering image exceeds 2 MiB")
    signature = b"\x89PNG\r\n\x1a\n" if prefix == "data:image/png" else b"\xff\xd8\xff"
    if not data.startswith(signature):
        raise ValueError("Desktop image media signature differs")
    return prefix.removeprefix("data:"), data


class DesktopHarnessBinding(Contract):
    schema_version: Literal["wright.desktop-binding/1"] = "wright.desktop-binding/1"
    connection_id: Identifier
    adapter: Literal["openai-desktop-harness"] = "openai-desktop-harness"
    image_input_profile: Literal[
        "unavailable", "inline-png-jpeg-v1", "inline-png-jpeg-engineering-v1"
    ] = "unavailable"
    requested_model: Identifier | None = None
    reported_model: Identifier | None = None
    model_identity_source: Literal["unreported", "client_reported"] = "unreported"
    reported_app_build: Identifier | None = None
    protocol_version: Literal["wright.desktop-reasoning/1"] = (
        "wright.desktop-reasoning/1"
    )

    @model_validator(mode="after")
    def honest_model_identity(self):
        if (self.reported_model is None) != (
            self.model_identity_source == "unreported"
        ):
            raise ValueError(
                "Reported model requires explicit client-reported attribution"
            )
        return self

    @property
    def digest(self):
        return canonical_digest(self)


class DesktopReasoningRequest(Contract):
    schema_version: Literal["wright.desktop-reasoning/1"] = "wright.desktop-reasoning/1"
    request_id: Identifier
    workspace_id: Identifier
    session_id: Identifier
    run_id: Identifier
    ordinal: int = Field(ge=1, le=10000)
    created_at: Timestamp
    kind: Literal["response", "action"]
    output_format: Literal["text", "markdown", "html", "json"]
    binding: DesktopHarnessBinding
    instruction_set_digest: Digest
    payload: dict[str, JsonValue]

    @model_validator(mode="after")
    def bounded_payload(self):
        engineering = self.binding.image_input_profile == ENGINEERING_IMAGE_PROFILE
        maximum = 8 * 1024 * 1024 if engineering else 262144
        if len(canonical_json(self.payload).encode()) > maximum:
            if engineering:
                raise ValueError("Desktop engineering task exceeds 8 MiB")
            raise ValueError("Desktop task exceeds the 256 KiB handoff limit")
        if engineering:
            text_payload = deepcopy(self.payload)
            messages = text_payload.get("messages", [])
            if not isinstance(messages, list):
                raise ValueError("Desktop engineering messages must be a list")
            count = 0
            for message in messages:
                content = message.get("content") if isinstance(message, dict) else None
                if not isinstance(content, list):
                    continue
                for part in content:
                    if not isinstance(part, dict) or part.get("type") not in {
                        "image_url",
                        "image",
                        "input_image",
                    }:
                        continue
                    url = desktop_image_url(part)
                    count += 1
                    if count > 8:
                        raise ValueError(
                            "Desktop engineering task exceeds eight images"
                        )
                    decode_desktop_image(
                        url,
                        profile=self.binding.image_input_profile,
                    )
                    part["image_url"]["url"] = ""
            if len(canonical_json(text_payload).encode()) > 262144:
                raise ValueError("Desktop non-image task content exceeds 256 KiB")
        return self

    @property
    def digest(self):
        return canonical_digest(self)


class DesktopActionReply(Contract):
    role: Literal["assistant"] = "assistant"
    content: str | None = Field(default=None, max_length=262144)
    tool_calls: list[dict[str, JsonValue]] = Field(default_factory=list, max_length=1)

    @model_validator(mode="after")
    def nonempty_bounded_action(self):
        if not self.content and not self.tool_calls:
            raise ValueError(
                "Desktop decision must contain a result or a proposed action"
            )
        if len(canonical_json(self).encode()) > 262144:
            raise ValueError("Desktop decision exceeds 256 KiB")
        return self


class DesktopReasoningResponse(Contract):
    schema_version: Literal["wright.desktop-response/1"] = "wright.desktop-response/1"
    request_id: Identifier
    request_digest: Digest
    binding_digest: Digest
    response_id: Identifier
    received_at: Timestamp
    reply: ReplyText | DesktopActionReply

    @property
    def digest(self):
        return canonical_digest(self)
