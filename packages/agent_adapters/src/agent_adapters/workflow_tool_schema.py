"""Bound provider schemas independently of the fixed action-intent envelope."""

from core.workflow_action_intent import workflow_action_intent_schema
from core.workflow_instructions import ACTION_INTENT_VERSION


def schema_depth(value: object, depth: int = 0) -> int:
    if isinstance(value, dict):
        return max([depth, *(schema_depth(item, depth + 1) for item in value.values())])
    if isinstance(value, list):
        return max([depth, *(schema_depth(item, depth + 1) for item in value)])
    return depth


def qualify_workflow_tool_schema_depth(parameters, *, action_intent_contract=None):
    """Keep the original depth16 limit; allow exactly two fixed wrapper levels.

    The marker alone never expands the bound. Compare every outer contract field
    with the shared typed schema, substituting only the bounded argument schema.
    No provider transport or permission is performed by this qualification.
    """
    if not isinstance(parameters, dict):
        raise ValueError("Tool schema must be an object")
    depth = schema_depth(parameters)
    if depth <= 16:
        return
    if action_intent_contract != ACTION_INTENT_VERSION or depth > 18:
        raise ValueError("Tool schema exceeds its bounded depth")
    properties = parameters.get("properties")
    if not isinstance(properties, dict):
        raise ValueError("Action-intent properties must be an object")
    arguments = properties.get("arguments")
    if not isinstance(arguments, dict) or schema_depth(arguments) > 16:
        raise ValueError("Provider argument schema exceeds its original bounded depth")
    expected = workflow_action_intent_schema({"type": "object"})
    expected["properties"]["arguments"] = arguments
    if parameters != expected:
        raise ValueError(
            "Tool schema is not the exact supported action-intent envelope"
        )
