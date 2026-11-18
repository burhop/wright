"""Transferable option source. The host owns qualification and dispatch."""

from typing import Annotated

from pydantic import Field, field_validator

from .contracts import Contract, Digest, Identifier
from .interaction_schema import InlineJSON, checked_json


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
