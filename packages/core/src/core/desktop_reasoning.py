"""Bounded desktop handoff receipts, independent of workflow run authority."""

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


class DesktopHarnessBinding(Contract):
    schema_version: Literal["wright.desktop-binding/1"] = "wright.desktop-binding/1"
    connection_id: Identifier
    adapter: Literal["openai-desktop-harness"] = "openai-desktop-harness"
    image_input_profile: Literal["unavailable", "inline-png-jpeg-v1"] = "unavailable"
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
        if len(canonical_json(self.payload).encode()) > 262144:
            raise ValueError("Desktop task exceeds the 256 KiB handoff limit")
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
