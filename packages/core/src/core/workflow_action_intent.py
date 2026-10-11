"""Typed model proposals; these declarations never grant tool authority."""

from __future__ import annotations

from copy import deepcopy
from typing import Annotated, Literal

from pydantic import Field, JsonValue, StrictStr

from .process_validation import Contract, Identifier
from .workflow_instructions import ACTION_INTENT_VERSION, WorkflowAssumption


class WorkflowRequiredInformation(Contract):
    identifier: Identifier
    reason: Annotated[StrictStr, Field(min_length=1, max_length=8192)]


class WorkflowActionIntent(Contract):
    schema_version: Literal["wright.workflow-action-intent/1"]
    arguments: dict[str, JsonValue]
    assumptions: tuple[WorkflowAssumption, ...] = Field(max_length=32)
    unresolved_required_information: tuple[WorkflowRequiredInformation, ...] = Field(
        max_length=32
    )


def workflow_action_intent_schema(provider_schema: dict) -> dict:
    """Wrap an exact provider schema without changing its local reference scope."""
    arguments = deepcopy(provider_schema)

    def rebase(schema):
        if isinstance(schema, bool):
            return
        if not isinstance(schema, dict):
            raise ValueError("invalid_provider_schema")
        if (
            "$schema" in schema
            and schema["$schema"] != "https://json-schema.org/draft/2020-12/schema"
        ):
            raise ValueError("unsupported_provider_schema_dialect")
        # Moving a reference scope/anchor requires full schema-resource
        # resolution. Fail visibly rather than reinterpret a provider contract.
        if any(
            key in schema
            for key in (
                "$id",
                "$anchor",
                "$dynamicAnchor",
                "$dynamicRef",
                "$recursiveRef",
                "$recursiveAnchor",
            )
        ):
            raise ValueError("unsupported_provider_reference_scope")
        reference = schema.get("$ref")
        if reference is not None:
            if not isinstance(reference, str) or not (
                reference == "#" or reference.startswith("#/")
            ):
                raise ValueError("unsupported_provider_reference")
            schema["$ref"] = "#/properties/arguments" + reference[1:]
        # Traverse schema positions only. A $ref in const/default/example data
        # is literal provider data and must remain byte-for-byte equivalent.
        for keyword in (
            "$defs",
            "definitions",
            "properties",
            "patternProperties",
            "dependentSchemas",
        ):
            children = schema.get(keyword, {})
            if not isinstance(children, dict):
                raise ValueError("invalid_provider_schema_container")
            for child in children.values():
                rebase(child)
        for keyword in ("allOf", "anyOf", "oneOf", "prefixItems"):
            children = schema.get(keyword, [])
            if not isinstance(children, list):
                raise ValueError("invalid_provider_schema_container")
            for child in children:
                rebase(child)
        for keyword in (
            "items",
            "additionalItems",
            "contains",
            "additionalProperties",
            "unevaluatedProperties",
            "unevaluatedItems",
            "propertyNames",
            "not",
            "if",
            "then",
            "else",
        ):
            if keyword in schema:
                child = schema[keyword]
                if isinstance(child, list):
                    for item in child:
                        rebase(item)
                else:
                    rebase(child)
        dependencies = schema.get("dependencies", {})
        if not isinstance(dependencies, dict):
            raise ValueError("invalid_provider_schema_container")
        for child in dependencies.values():
            if isinstance(child, (dict, bool)):
                rebase(child)

    rebase(arguments)
    result = WorkflowActionIntent.model_json_schema()
    result["properties"]["schema_version"] = {
        "type": "string",
        "const": ACTION_INTENT_VERSION,
    }
    result["properties"]["arguments"] = arguments
    return result


def validate_workflow_action_intent(
    proposal, *, assumption_policy: str, protected_requirements=(), output_ids=()
) -> WorkflowActionIntent:
    """Validate declared completeness and choices before provider dispatch."""
    intent = WorkflowActionIntent.model_validate(proposal)
    if intent.unresolved_required_information:
        raise ValueError("required_information_unresolved")
    if intent.assumptions and assumption_policy != "document_reasonable":
        raise ValueError("strict_policy_forbids_assumptions")
    protected, declared = set(protected_requirements), set(output_ids)
    parameters = set()
    for assumption in intent.assumptions:
        if assumption.parameter in protected:
            raise ValueError("protected_requirement_assumption")
        if set(assumption.affected_outputs) - declared:
            raise ValueError("undeclared_assumption_output")
        if assumption.parameter in parameters:
            raise ValueError("duplicate_assumption_parameter")
        parameters.add(assumption.parameter)
    return intent
