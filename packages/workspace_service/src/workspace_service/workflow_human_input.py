"""Compile explicit, bounded human input using the existing source grammar."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator, model_serializer, model_validator

from core.process_interactions import checked_value_schema
from core.process_validation import Contract, Identifier
from core.workflow_input_conditions import HumanInputCondition


class HumanInputDeclaration(Contract):
    # Version 1 retains its connected producer-evidence requirement. Version 2
    # explicitly permits a question anchored to the saved definition and frozen
    # run inputs before an engineering producer has run.
    version: Literal[1, 2, 3]
    kind: Literal["input"]
    instructions: str = Field(min_length=1, max_length=8000)
    response_schema: dict
    output_port: Identifier
    when: HumanInputCondition | None = None

    @field_validator("version", mode="before")
    @classmethod
    def exact_version(cls, value):
        if type(value) is not int or value not in {1, 2, 3}:
            raise ValueError("Human input requires declaration version 1, 2 or 3")
        return value

    @model_validator(mode="after")
    def versioned_condition(self):
        if (self.version == 3) != (self.when is not None):
            raise ValueError(
                "A conditional input requires version 3 and a declared condition"
            )
        if self.when and (
            set(self.when.fields) != set(self.response_schema.get("properties", {}))
            or self.response_schema.get("additionalProperties") is not False
        ):
            raise ValueError(
                "Condition fields must match the fixed closed response schema"
            )
        return self

    @model_serializer(mode="wrap")
    def preserved_legacy_shape(self, serialize):
        result = serialize(self)
        if self.when is None:
            result.pop("when", None)
        return result

    @field_validator("instructions")
    @classmethod
    def meaningful_instructions(cls, value):
        if not value.strip():
            raise ValueError("Human input requires instructions")
        return value

    @field_validator("response_schema")
    @classmethod
    def bounded_object_schema(cls, value):
        checked_value_schema(value)
        if value.get("type") != "object":
            raise ValueError("A human response must have a declared object schema")
        return value


def compile_human_input(block_id, fields, incoming, blocks):
    """Return a barrier descriptor, never an AI prompt or approval receipt."""
    from .workflow_source_execution import PromptStep, _invalid

    title = fields["name"]
    settings = fields["settings"]
    try:
        declaration = HumanInputDeclaration.model_validate(
            settings["human_interaction"]
        )
    except (ValueError, TypeError, KeyError) as error:
        raise _invalid(
            f"{title}: the declared human input is invalid.",
            "Declare versioned input instructions, a bounded object response_schema "
            "and exactly one structured response output_port.",
        ) from error
    outputs = fields.get("outputs", [])
    refs = tuple(
        (port["name"], source)
        for port in fields.get("inputs", [])
        for source in incoming.get(f"{block_id}.{port['key']}", [])
    )
    if declaration.when:
        source_id, source_port = declaration.when.source.split(".")
        producer = blocks.get(source_id)
        if (
            declaration.when.source not in {source for _, source in refs}
            or not producer
            or producer["kind"] != "task"
            or not any(
                port.get("key") == source_port
                and port.get("kind") == "structured_result"
                for port in producer["fields"].get("outputs", [])
            )
        ):
            raise _invalid(
                f"{title}: the condition needs connected structured upstream evidence.",
                "Connect the declared requirements-resolution output and select its exact source address.",
            )
    if (
        set(settings) - {"authoring_template", "human_interaction"}
        or fields.get("performed_by") != "engineer"
        or fields.get("step_type") != "work"
        or fields.get("tool") is not None
        or fields.get("reusable_step") is not None
        or fields.get("prompt") is not None
        or len(outputs) != 1
        or outputs[0].get("key") != declaration.output_port
        or outputs[0].get("kind") != "structured_result"
        or outputs[0].get("quantity") != "one"
        or (not refs and declaration.version == 1)
        or any(
            port.get("required") is True
            and len(incoming.get(f"{block_id}.{port['key']}", [])) != 1
            for port in fields.get("inputs", [])
        )
        or (
            refs
            and not any(
                blocks[source.split(".", 1)[0]]["kind"] == "task" for _, source in refs
            )
        )
    ):
        raise _invalid(
            f"{title}: human input needs an Engineer work step, one structured response "
            "output and connected upstream evidence when required by its declaration or ports.",
            "Connect the outputs to review, declare the response port and remove "
            "AI prompts, tools or reusable execution bindings from this step. "
            "Use declaration version 2 for a Request input step before any upstream work.",
        )
    return PromptStep(
        block_id,
        title,
        "",
        None,
        refs,
        "json",
        "",
        False,
        "indexed",
        output_ports=((declaration.output_port, "structured_result"),),
        human_interaction=declaration.model_dump(mode="json"),
    )


def validate_human_input_rework(steps, revisions):
    """A declared answer is never automatically replayed by a correction loop."""
    from .workflow_source_execution import _invalid

    positions = {step.id: index for index, step in enumerate(steps)}
    for check_id, target_id in revisions.items():
        if (
            target_id in positions
            and check_id in positions
            and any(
                step.human_interaction
                for step in steps[positions[target_id] : positions[check_id] + 1]
            )
        ):
            raise _invalid(
                "A bounded correction segment cannot replay a declared human input.",
                "Place the declared input outside the automatic correction segment.",
            )
