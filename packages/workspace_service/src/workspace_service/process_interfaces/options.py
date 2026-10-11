"""Provider-owned choices from exact configured read-only MCP capabilities."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Annotated

from pydantic import Field, field_validator

from core.process_interactions import (
    CapabilityRef,
    InlineJSON,
    InputOption,
    OptionBinding,
    checked_json,
    validate_response,
)
from core.process_validation import (
    Contract,
    Digest,
    Identifier,
    canonical_digest,
    canonical_json,
)
from core.redaction import redact_text

from ..workflow_source_execution import PromptStep, WorkflowSourceExecutionError
from .errors import ProcessInterfaceError


class OptionSource(Contract):
    binding_id: Identifier
    server_id: Identifier
    tool_name: Identifier
    schema_digest: Digest
    arguments: dict[str, InlineJSON] = Field(default_factory=dict)
    options_pointer: Identifier = "/options"
    id_pointer: Identifier = "/id"
    title_pointer: Identifier = "/title"
    value_pointer: Identifier = "/value"
    resource_pointer: Identifier | None = None
    freshness_seconds: Annotated[int, Field(strict=True, ge=1, le=300)] = 30
    timeout_seconds: Annotated[int, Field(strict=True, ge=1, le=30)] = 10

    @field_validator("arguments")
    @classmethod
    def bounded_arguments(cls, value):
        checked_json(value)

        def inspect(item):
            if isinstance(item, dict):
                for key, child in item.items():
                    if any(
                        marker in key.casefold().replace("-", "_")
                        for marker in (
                            "token",
                            "password",
                            "secret",
                            "credential",
                            "api_key",
                            "authorization",
                        )
                    ):
                        raise ValueError(
                            "Option declarations cannot contain credentials"
                        )
                    inspect(child)
            elif isinstance(item, list):
                for child in item:
                    inspect(child)

        inspect(value)
        return value

    @field_validator(
        "options_pointer",
        "id_pointer",
        "title_pointer",
        "value_pointer",
        "resource_pointer",
    )
    @classmethod
    def pointer(cls, value):
        if value is not None and (
            not value.startswith("/") or len(value.split("/")) > 24
        ):
            raise ValueError("Choose a bounded local JSON pointer")
        return value

    def capability(self, resource_digest=None):
        return CapabilityRef(
            binding_id=self.binding_id,
            schema_digest=self.schema_digest,
            resource_digest=resource_digest,
        )


@dataclass(frozen=True)
class OptionCatalog:
    capability: CapabilityRef
    options: tuple[InputOption, ...]
    observed_at: str
    stale_after: str
    freshness_seconds: int


def at_pointer(value, pointer):
    for token in pointer.split("/")[1:]:
        token = token.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


async def read_options(configuration, runtime, *, input_id, value_schema, now=None):
    if runtime is None:
        raise ProcessInterfaceError(
            "CAPABILITY_UNAVAILABLE",
            "Available choices could not be read from the configured provider.",
            "Connect its qualified read-only MCP capability and refresh the choices.",
        )
    step = PromptStep(
        id=f"options-{input_id}",
        title="Read available process choices",
        prompt="",
        prompt_from=None,
        references=(),
        output_format="json",
        output_path="",
        save=False,
        file_policy="indexed",
        server_id=configuration.server_id,
        tool_name=configuration.tool_name,
        schema_digest=configuration.schema_digest,
        arguments=configuration.arguments,
    )
    try:
        tool = runtime.resolve(step)
        if tool.annotations.get("readOnlyHint") is not True or tool.required_approvals:
            raise ProcessInterfaceError(
                "READINESS_UNSUPPORTED",
                "The option source is not a qualified read-only capability.",
                "Select a read-only provider operation that requires no mutation approval.",
            )
        runtime.preflight(step)
        async with asyncio.timeout(configuration.timeout_seconds):
            structured, _ = await runtime.call(
                step, configuration.arguments, monitor=False
            )
        choices = at_pointer(structured, configuration.options_pointer)
        checked_json(choices)
        if not isinstance(choices, list) or len(choices) > 256:
            raise ValueError("Provider choices exceed the bounded list contract")
        options = []
        for choice in choices:
            identity = at_pointer(choice, configuration.id_pointer)
            value = at_pointer(choice, configuration.value_pointer)
            validate_response(value_schema, value)
            try:
                title = at_pointer(choice, configuration.title_pointer)
            except (KeyError, IndexError):
                title = identity
            options.append(
                InputOption(option_id=identity, title=redact_text(title), value=value)
            )
        if len({item.option_id for item in options}) != len(options):
            raise ValueError("Provider choices must have distinct exact identities")
        provider_revision = (
            at_pointer(structured, configuration.resource_pointer)
            if configuration.resource_pointer
            else None
        )
        checked_json(provider_revision)
        digest = canonical_digest(
            {
                "provider_revision": provider_revision,
                "options": [
                    {"id": item.option_id, "value": item.value} for item in options
                ],
            }
        )
        observed = (
            datetime.fromisoformat(now.replace("Z", "+00:00"))
            if now
            else datetime.now(timezone.utc)
        )
        return OptionCatalog(
            configuration.capability(digest),
            tuple(options),
            observed.isoformat(),
            (observed + timedelta(seconds=configuration.freshness_seconds)).isoformat(),
            configuration.freshness_seconds,
        )
    except ProcessInterfaceError:
        raise
    except (
        WorkflowSourceExecutionError,
        TimeoutError,
        ValueError,
        TypeError,
        KeyError,
        IndexError,
    ) as error:
        raise ProcessInterfaceError(
            "CAPABILITY_UNAVAILABLE",
            "The provider's available choices could not be verified.",
            "Check its current capability/schema and refresh the supported choices.",
            details={
                "capability_error": getattr(error, "code", "invalid_option_catalog")
            },
        ) from error


def verify_option(binding: OptionBinding, catalog: OptionCatalog):
    observed = datetime.fromisoformat(binding.observed_at.replace("Z", "+00:00"))
    current = datetime.fromisoformat(catalog.observed_at)
    expires = (
        datetime.fromisoformat(binding.stale_after.replace("Z", "+00:00"))
        if binding.stale_after
        else None
    )
    selected = next(
        (item for item in catalog.options if item.option_id == binding.option_id), None
    )
    if (
        binding.capability != catalog.capability
        or selected is None
        or canonical_json(selected.value) != canonical_json(binding.value)
        or observed > current
        or (current - observed).total_seconds() > catalog.freshness_seconds
        or expires is None
        or expires <= current
        or expires > observed + timedelta(seconds=catalog.freshness_seconds)
    ):
        raise ProcessInterfaceError(
            "OPTION_STALE",
            "The selected provider choice is stale or no longer available.",
            "Refresh the choices and select the current exact option before starting.",
        )
