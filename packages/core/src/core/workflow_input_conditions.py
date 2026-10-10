"""Bounded requirements-driven input conditions, without execution authority."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import (
    Field,
    JsonValue,
    StrictStr,
    StringConstraints,
    field_validator,
    model_validator,
)

from .process_interactions import checked_json, validate_response
from .process_validation import Contract, Digest, Identifier


OutputAddress = Annotated[
    StrictStr,
    StringConstraints(pattern=r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$", max_length=321),
]


class HumanInputCondition(Contract):
    kind: Literal["unresolved_fields"]
    source: OutputAddress
    fields: tuple[Identifier, ...] = Field(min_length=1, max_length=32)

    @field_validator("fields")
    @classmethod
    def unique_fields(cls, value):
        if len(set(value)) != len(value):
            raise ValueError("Condition fields must be unique")
        return value


class RequirementsResolution(Contract):
    version: Literal["wright.requirements-resolution/1"]
    unresolved_fields: tuple[Identifier, ...] = Field(max_length=32)
    resolved_values: dict[str, JsonValue] = Field(max_length=32)

    @field_validator("unresolved_fields")
    @classmethod
    def unique_fields(cls, value):
        if len(set(value)) != len(value):
            raise ValueError("Unresolved fields must be unique")
        return value

    @field_validator("resolved_values")
    @classmethod
    def bounded_values(cls, value):
        checked_json(value)
        return value


class ConditionalInputEvaluation(RequirementsResolution):
    version: Literal["wright.input-condition-evaluation/1"]
    source: OutputAddress
    source_digest: Digest
    decision: Literal["ask", "skip"]

    @model_validator(mode="after")
    def honest_decision(self):
        if (self.decision == "ask") != bool(self.unresolved_fields):
            raise ValueError("Condition decision does not match unresolved fields")
        return self


def validate_requirements_resolution(condition, response_schema, value):
    """Validate declared fields and known values; never reduce the answer schema."""
    resolution = RequirementsResolution.model_validate(value)
    names = set(condition.fields)
    properties = response_schema.get("properties", {})
    if (
        names != set(properties)
        or response_schema.get("additionalProperties") is not False
        or not set(resolution.unresolved_fields).issubset(names)
        or not set(resolution.resolved_values).issubset(names)
        or set(resolution.unresolved_fields) & set(resolution.resolved_values)
        or not set(response_schema.get("required", [])).issubset(
            set(resolution.unresolved_fields) | set(resolution.resolved_values)
        )
    ):
        raise ValueError("Resolution must account for the fixed declared answer fields")
    partial_schema = {**response_schema, "required": []}
    if resolution.unresolved_fields:
        # Known fields retain their original validators while outstanding fields
        # may be absent. The actual human answer uses the complete fixed schema.
        partial_schema.pop("minProperties", None)
        validate_response(partial_schema, resolution.resolved_values)
    else:
        validate_response(response_schema, resolution.resolved_values)
    return resolution
