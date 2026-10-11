"""Frozen public routing identity; no credentials or model permission grants."""

from typing import Literal

from pydantic import Field, TypeAdapter, model_validator

from .process_validation import Contract, Digest, Identifier, canonical_digest


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


def parse_workflow_text_resolution(value):
    return TypeAdapter(
        WorkflowTextResolution | WorkflowSdkTextResolution
    ).validate_python(value)


class WorkflowModelRouting(Contract):
    schema_version: Literal["wright.workflow-model-routing/1"] = (
        "wright.workflow-model-routing/1"
    )
    text: WorkflowTextResolution | WorkflowSdkTextResolution | None = None
    images: dict[Identifier, dict] = Field(default_factory=dict, max_length=32)

    @model_validator(mode="after")
    def bounded_native_identity(self):
        for value in self.images.values():
            if set(value) != {
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
