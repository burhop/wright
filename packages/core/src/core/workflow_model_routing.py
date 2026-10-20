"""Frozen public routing identity; no credentials or model permission grants."""

from typing import Literal

from pydantic import Field, TypeAdapter, model_validator

from .process_validation import Contract, Digest, Identifier, canonical_digest
from .desktop_reasoning import DesktopHarnessBinding

SdkReasoningEffort = Literal["low", "medium", "high", "xhigh", "max"]


class _WorkflowTextResolution(Contract):
    provider: Identifier
    model_reference: Identifier
    profile: Identifier
    endpoint_digest: Digest
    configuration_digest: Digest

    @model_validator(mode="after")
    def exact_configuration(self):
        public = self.model_dump(mode="json", exclude={"configuration_digest"})
        if canonical_digest(public) != self.configuration_digest:
            raise ValueError(
                "Model routing configuration digest differs from its public identity"
            )
        return self


class WorkflowTextResolution(_WorkflowTextResolution):
    adapter: Literal["hermes-http"] = "hermes-http"


class WorkflowSdkTextResolution(_WorkflowTextResolution):
    adapter: Literal["hermes-model-sdk"] = "hermes-model-sdk"
    api_mode: Literal["chat_completions", "codex_responses", "anthropic_messages"]
    sdk_digest: Digest
    reasoning_effort: SdkReasoningEffort | None = Field(
        default=None, exclude_if=lambda value: value is None
    )

    @model_validator(mode="after")
    def qualified_reasoning_transport(self):
        if self.reasoning_effort is not None and self.api_mode != "codex_responses":
            raise ValueError("Reasoning is not qualified for this SDK transport")
        return self


class WorkflowDesktopTextResolution(Contract):
    """Freeze an observable connection; it does not attest the selected model."""

    adapter: Literal["openai-desktop-harness"] = "openai-desktop-harness"
    binding: DesktopHarnessBinding
    configuration_digest: Digest

    @model_validator(mode="after")
    def exact_configuration(self):
        public = self.model_dump(mode="json", exclude={"configuration_digest"})
        if canonical_digest(public) != self.configuration_digest:
            raise ValueError("Desktop routing digest differs from its public binding")
        return self


def parse_workflow_text_resolution(value):
    return TypeAdapter(
        WorkflowTextResolution
        | WorkflowSdkTextResolution
        | WorkflowDesktopTextResolution
    ).validate_python(value)


class WorkflowModelRouting(Contract):
    schema_version: Literal["wright.workflow-model-routing/1"] = (
        "wright.workflow-model-routing/1"
    )
    text: (
        WorkflowTextResolution
        | WorkflowSdkTextResolution
        | WorkflowDesktopTextResolution
        | None
    ) = None
    images: dict[Identifier, dict] = Field(default_factory=dict, max_length=32)

    @model_validator(mode="after")
    def bounded_native_identity(self):
        for value in self.images.values():
            if set(value) - {"reasoning_effort"} != {
                "provider",
                "model_reference",
                "api_mode",
                "endpoint_digest",
                "sdk_digest",
                "configuration_digest",
            }:
                raise ValueError(
                    "Native image routing identity has an unsupported shape"
                )
            if "reasoning_effort" in value:
                TypeAdapter(SdkReasoningEffort).validate_python(
                    value["reasoning_effort"]
                )
                if value["api_mode"] != "codex_responses":
                    raise ValueError(
                        "Reasoning is not qualified for this SDK transport"
                    )
            public = {
                key: entry
                for key, entry in value.items()
                if key != "configuration_digest"
            }
            # The qualified SDK resolver uses its existing sorted JSON encoding,
            # not wright-json-v1. Preserve that established identity exactly.
            import hashlib
            import json

            if not all(
                isinstance(entry, str) and 0 < len(entry) <= 160
                for entry in value.values()
            ):
                raise ValueError(
                    "Native image routing identity contains invalid values"
                )
            if (
                hashlib.sha256(json.dumps(public, sort_keys=True).encode()).hexdigest()
                != value["configuration_digest"]
            ):
                raise ValueError(
                    "Native image routing digest differs from its saved identity"
                )
        return self
