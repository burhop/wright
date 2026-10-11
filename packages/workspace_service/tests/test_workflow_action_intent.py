"""Pre-dispatch declarations must pass before any real provider invocation."""

import asyncio
from dataclasses import replace
import json

import pytest
from jsonschema import Draft202012Validator

from agent_adapters.workflow_instructions import load_default_workflow_instructions
from core.workflow_action_intent import workflow_action_intent_schema
from packages.workspace_service.tests.test_workflow_ai_task import plan, call, done
from packages.workspace_service.tests.test_workflow_mcp_execution import runtime, TOOL
from packages.workspace_service.tests.test_workflow_source_execution import service
from workspace_service.workflow_source_execution import (
    execute_prompt_workflow,
    WorkflowSourceExecutionError,
)


def profile(policy="require_specified", *, modern=True, protected=()):
    result = load_default_workflow_instructions().model_dump(mode="json")
    result["policy"] = {
        "assumption_policy": policy,
        "protected_requirements": list(protected),
    }
    if not modern:
        result.pop("action_intent_contract")
    return result


def proposal(*, assumptions=(), unresolved=()):
    return {
        "schema_version": "wright.workflow-action-intent/1",
        "arguments": {"query": "bracket"},
        "assumptions": list(assumptions),
        "unresolved_required_information": list(unresolved),
    }


def choice(parameter="bend_angle", outputs=("research_response",)):
    return {
        "parameter": parameter,
        "value": "90",
        "units": "deg",
        "rationale": "Delegated mockup design choice",
        "affected_outputs": list(outputs),
    }


def run(tmp_path, proposed, instructions, *, readonly=False):
    workflow = plan()
    workflow = replace(
        workflow,
        steps=(
            replace(
                workflow.steps[0],
                instruction_set=instructions,
                instruction_override=None,
            ),
        ),
    )
    gateway, runner = runtime()
    if readonly:
        gateway.list_tools = lambda *args: (
            replace(TOOL, annotations={"readOnlyHint": True}),
        )
    action = call()
    action["tool_calls"][0]["function"]["arguments"] = json.dumps(proposed)
    actions = iter([action, done("Actual evidence")])
    events, schemas = [], []

    async def decide(messages, tools, **kwargs):
        schemas.append(tools)
        return next(actions)

    async def emit(event):
        events.append(event)

    error = None
    try:
        asyncio.run(
            execute_prompt_workflow(
                service=service(tmp_path),
                workspace_dir=str(tmp_path),
                plan=workflow,
                input_values={},
                response_generator=None,
                action_generator=decide,
                tool_runtime=runner,
                on_event=emit,
            )
        )
    except WorkflowSourceExecutionError as caught:
        error = caught
    return gateway, events, schemas, error


def test_strict_fully_declared_proposal_unwraps_exact_provider_arguments(tmp_path):
    gateway, events, schemas, error = run(tmp_path, proposal(), profile())
    assert error is None
    assert len(gateway.calls) == 1
    assert gateway.calls[0][0][3] == {"query": "bracket"}
    parameters = schemas[0][0]["function"]["parameters"]
    assert parameters["additionalProperties"] is False
    assert set(parameters["required"]) == {
        "schema_version",
        "arguments",
        "assumptions",
        "unresolved_required_information",
    }
    assert parameters["properties"]["arguments"] == TOOL.input_schema
    validated = next(
        event for event in events if event["kind"] == "action_intent_validated"
    )
    started = next(event for event in events if event["kind"] == "tool_started")
    assert events.index(validated) < events.index(started)


@pytest.mark.parametrize(
    "mutation,policy,protected",
    [
        ("strict", "require_specified", ()),
        ("protected", "document_reasonable", ("bend_angle",)),
        ("unknown_output", "document_reasonable", ()),
        ("missing", "document_reasonable", ()),
        ("malformed", "document_reasonable", ()),
    ],
)
def test_invalid_intent_never_dispatches_or_asks_for_input(
    tmp_path, mutation, policy, protected
):
    proposed = proposal(assumptions=[choice()])
    if mutation == "unknown_output":
        proposed["assumptions"] = [choice(outputs=("invented_file",))]
    if mutation == "missing":
        proposed = proposal(
            unresolved=[{"identifier": "sheet_thickness", "reason": "Not supplied"}]
        )
    if mutation == "malformed":
        proposed = {
            "query": "bracket"
        }  # Direct legacy arguments cannot bypass a modern marker.
    gateway, events, _, error = run(
        tmp_path, proposed, profile(policy, protected=protected)
    )
    assert error.code == "WORKFLOW_ACTION_INTENT_INVALID"
    assert gateway.calls == []
    assert any(event["kind"] == "action_intent_rejected" for event in events)
    assert not any(
        event["kind"] in {"tool_started", "input_requested", "assumptions_recorded"}
        for event in events
    )


def test_documented_choice_is_retained_after_successful_provider_call(tmp_path):
    gateway, events, _, error = run(
        tmp_path, proposal(assumptions=[choice()]), profile("document_reasonable")
    )
    assert error is None and len(gateway.calls) == 1
    recorded = next(
        event for event in events if event["kind"] == "assumptions_recorded"
    )
    assert recorded["assumptions"] == [choice()]


@pytest.mark.parametrize("instructions", [None, profile(modern=False)])
def test_strict_legacy_potential_mutation_is_readiness_error(tmp_path, instructions):
    gateway, events, schemas, error = run(tmp_path, {"query": "bracket"}, instructions)
    assert error.code == "WORKFLOW_ACTION_INTENT_UPGRADE_REQUIRED"
    assert gateway.calls == [] and schemas == []
    assert "upgrade" in error.correction.lower()


def test_known_readonly_legacy_can_use_original_schema(tmp_path):
    gateway, _, schemas, error = run(
        tmp_path, {"query": "bracket"}, profile(modern=False), readonly=True
    )
    assert error is None and len(gateway.calls) == 1
    assert schemas[0][0]["function"]["parameters"] == TOOL.input_schema


def test_legacy_documented_profile_stays_explicitly_unqualified(tmp_path):
    gateway, events, schemas, error = run(
        tmp_path, {"query": "bracket"}, profile("document_reasonable", modern=False)
    )
    assert error is None and len(gateway.calls) == 1
    assert not any(event["kind"].startswith("action_intent_") for event in events)
    assert schemas[0][0]["function"]["parameters"] == TOOL.input_schema


def test_nested_schema_references_keep_provider_semantics_and_original_identity():
    original = {
        "type": "object",
        "$defs": {"positive": {"type": "integer", "minimum": 1}},
        "properties": {"count": {"$ref": "#/$defs/positive"}},
        "required": ["count"],
    }
    before = json.dumps(original, sort_keys=True)
    model_schema = workflow_action_intent_schema(original)
    assert json.dumps(original, sort_keys=True) == before
    valid = proposal()
    valid["arguments"] = {"count": 2}
    assert not list(Draft202012Validator(model_schema).iter_errors(valid))
    valid["arguments"] = {"count": 0}
    assert list(Draft202012Validator(model_schema).iter_errors(valid))


def test_schema_wrapper_preserves_literal_reference_shaped_provider_data():
    literal = {
        "$ref": "#/literal",
        "$id": "data-not-a-schema",
        "nested": {"$dynamicRef": "#data"},
    }
    original = {
        "type": "object",
        "properties": {
            "payload": {"const": literal, "default": literal, "examples": [literal]}
        },
        "required": ["payload"],
    }
    wrapped = workflow_action_intent_schema(original)
    assert wrapped["properties"]["arguments"] == original
    valid = proposal()
    valid["arguments"] = {"payload": literal}
    assert not list(Draft202012Validator(wrapped).iter_errors(valid))


def test_successful_choices_survive_post_call_observation_failure():
    workflow = plan()
    step = replace(
        workflow.steps[0],
        instruction_set=profile("document_reasonable"),
        instruction_override=None,
    )
    gateway, runner = runtime()
    action = call()
    action["tool_calls"][0]["function"]["arguments"] = json.dumps(
        proposal(assumptions=[choice()])
    )
    events = []

    class Observer:
        records = []

        def allows_tool(self, tool):
            return True

        def guard(self, tool, arguments):
            return arguments

        async def validate_creation(self, tool, arguments):
            pass

        def observe(self, tool, value):
            raise ValueError("Synthetic post-success observation failure")

    async def decide(*args, **kwargs):
        return action

    async def emit(kind, **payload):
        events.append({"kind": kind, **payload})

    with pytest.raises(ValueError, match="post-success"):
        asyncio.run(
            runner.run_task(
                step, "Explicitly delegated mockup", decide, emit, cad=Observer()
            )
        )
    assert len(gateway.calls) == 1
    assert next(e for e in events if e["kind"] == "assumptions_recorded")[
        "assumptions"
    ] == [choice()]


def test_reworded_rationale_keeps_value_and_evidence_without_false_conflict():
    from workspace_service.workflow_mcp_execution import merged_task_assumptions

    original = choice()
    updated = {
        **choice(outputs=("another_declared_output",)),
        "rationale": "Same choice described differently",
    }
    merged = merged_task_assumptions({"bend_angle": original}, [updated])
    assert merged["bend_angle"]["value"] == "90"
    assert merged["bend_angle"]["affected_outputs"] == [
        "research_response",
        "another_declared_output",
    ]
    assert original["affected_outputs"] == ["research_response"]
    with pytest.raises(ValueError, match="conflicting_action_assumption"):
        merged_task_assumptions(merged, [{**updated, "value": "45"}])


@pytest.mark.parametrize("original_value,updated_value", [(True, 1), (False, 0)])
def test_exact_json_choices_do_not_merge_boolean_and_number(
    original_value, updated_value
):
    from workspace_service.workflow_mcp_execution import merged_task_assumptions

    original = {**choice(), "value": original_value}
    updated = {**choice(), "value": updated_value}
    with pytest.raises(ValueError, match="conflicting_action_assumption"):
        merged_task_assumptions({"bend_angle": original}, [updated])


@pytest.mark.parametrize("value", [True, False, 0, 1])
def test_non_string_choice_rejected_before_gateway(tmp_path, value):
    proposed = proposal(assumptions=[{**choice(), "value": value}])
    gateway, events, _, error = run(tmp_path, proposed, profile("document_reasonable"))
    assert error.code == "WORKFLOW_ACTION_INTENT_INVALID"
    assert gateway.calls == []
    assert not any(event["kind"] == "tool_started" for event in events)


@pytest.mark.parametrize(
    "scope",
    [
        {"$id": "https://provider.test/schema"},
        {"$anchor": "node"},
        {"$dynamicRef": "#node"},
        {"$recursiveRef": "#"},
        {"$ref": "#node"},
        {"$ref": "https://provider.test/schema"},
        {"$schema": "http://json-schema.org/draft-07/schema#"},
        {"properties": []},
        {"allOf": {}},
    ],
)
def test_unsupported_reference_scope_fails_readiness_before_model_or_gateway(
    tmp_path, scope
):
    from workspace_service.workflow_mcp_execution import WorkflowMcpRuntime

    workflow = plan()
    step = replace(workflow.steps[0], instruction_set=profile())
    gateway, _ = runtime()
    schema = {"type": "object", "properties": {"query": {"type": "string", **scope}}}
    tool = replace(TOOL, input_schema=schema)
    gateway.list_tools = lambda *args: (tool,)
    runner = WorkflowMcpRuntime(gateway, workspace_id="workspace", session_id="test")
    with pytest.raises(WorkflowSourceExecutionError) as caught:
        runner.preflight(step)
    assert caught.value.code == "WORKFLOW_ACTION_INTENT_SCHEMA_UNSUPPORTED"
    assert gateway.calls == []


def test_deep_provider_schema_has_an_actionable_depth_diagnostic():
    from workspace_service.workflow_mcp_execution import model_action_schema

    schema = {"type": "string", "enum": ["value"]}
    for _ in range(8):
        schema = {"type": "object", "properties": {"child": schema}}
    tool = replace(TOOL, title="Nested engineering operation", input_schema=schema)
    with pytest.raises(WorkflowSourceExecutionError) as caught:
        model_action_schema(tool)
    assert caught.value.code == "WORKFLOW_ACTION_INTENT_SCHEMA_UNSUPPORTED"
    assert "nesting depth" in str(caught.value)
    assert "MCP tool selection" in caught.value.correction
    assert "JSON pointer" not in caught.value.correction


def test_explicit_task_scope_excludes_unneeded_deep_tool_without_relaxing_bound():
    from workspace_service.workflow_mcp_execution import WorkflowMcpRuntime

    schema = {"type": "string"}
    for _ in range(9):
        schema = {"type": "object", "properties": {"child": schema}}
    deep = replace(
        TOOL,
        name=TOOL.name + "_deep",
        tool_name=TOOL.tool_name + "_deep",
        input_schema=schema,
    )
    gateway, _ = runtime()
    gateway.list_tools = lambda *args: (TOOL, deep)
    runner = WorkflowMcpRuntime(gateway, workspace_id="workspace", session_id="test")
    step = replace(
        plan().steps[0],
        instruction_set=profile(),
        task_tool_allowlist=(TOOL.tool_name,),
    )
    runner.preflight(step)
    assert runner.task_tools(step) == (TOOL,)
    with pytest.raises(WorkflowSourceExecutionError, match="nesting depth"):
        runner.preflight(replace(step, task_tool_allowlist=(deep.tool_name,)))
    with pytest.raises(WorkflowSourceExecutionError, match="nesting depth"):
        runner.preflight(replace(step, task_tool_allowlist=()))
    assert gateway.calls == []
