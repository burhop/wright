"""Known root values must fail qualification before any workflow effects."""

from dataclasses import replace

import pytest

from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    compile_prompt_workflow,
)
from workspace_service.workflow_mcp_execution import schema_digest
from packages.workspace_service.tests.test_workflow_mcp_execution import (
    TOOL,
    mcp,
    runtime,
    source,
)


def step(**changes):
    plan = compile_prompt_workflow(source(mcp()))
    return replace(plan.steps[0], argument_sources={"query": "root.value"}, **changes)


def test_known_invalid_connected_value_blocks_without_calling_provider():
    gateway, owner = runtime()
    with pytest.raises(WorkflowSourceExecutionError, match="minLength"):
        owner.preflight_values(step(), {"root.value": "x"})
    assert gateway.calls == []


def test_unknown_upstream_value_is_allowed_but_known_literals_are_checked():
    gateway, owner = runtime()
    owner.preflight_values(step(), {})
    with pytest.raises(WorkflowSourceExecutionError, match="type"):
        owner.preflight_values(step(arguments={"limit": "bad"}), {})
    assert gateway.calls == []


def test_native_whole_argument_object_is_preserved_and_checked():
    gateway, owner = runtime()
    selected = replace(step(), arguments_from="root.object", argument_sources={})
    args = {"query": "engineering", "limit": 3}
    owner.preflight_values(selected, {"root.object": args})
    assert owner.arguments(selected, {"root.object": args}) == args
    with pytest.raises(WorkflowSourceExecutionError, match="type"):
        owner.preflight_values(selected, {"root.object": {"query": 3}})
    assert gateway.calls == []


def test_native_integer_is_not_stringified_for_union_schema():
    gateway, owner = runtime()
    tool = replace(
        TOOL,
        input_schema={
            "type": "object",
            "properties": {
                "query": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    )
    gateway.list_tools = lambda *args: (tool,)
    selected = step(arguments={}, schema_digest=schema_digest(tool))
    owner.preflight_values(selected, {"root.value": 3})
    assert owner.arguments(selected, {"root.value": 3})["query"] == 3
    assert isinstance(owner.arguments(selected, {"root.value": 3})["query"], int)


def test_explicit_null_connected_value_is_checked_not_treated_as_unknown():
    gateway, owner = runtime()
    with pytest.raises(WorkflowSourceExecutionError, match="type"):
        owner.preflight_values(step(), {"root.value": None})
    assert gateway.calls == []
