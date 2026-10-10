"""The action envelope must not enlarge original provider schema limits."""

from copy import deepcopy

import pytest

from agent_adapters.hermes_openai_bridge import (
    HermesBridgeError,
    HermesOpenAICompatibilityBridge,
    HermesOpenAIBridgeSettings,
)
from agent_adapters.workflow_instructions import load_default_workflow_instructions
from agent_adapters.workflow_tool_schema import (
    qualify_workflow_tool_schema_depth,
    schema_depth,
)
from core.workflow_action_intent import workflow_action_intent_schema
from test_hermes_openai_bridge import _request, _tool


def nested(depth):
    schema = {"type": "string"}
    for _ in range(depth):
        schema = {"type": "object", "properties": {"child": schema}}
    return schema


def bridge_validate(parameters, *, modern=False):
    bridge = HermesOpenAICompatibilityBridge(
        HermesOpenAIBridgeSettings(
            base_url="http://isolated.test", api_key="test-key", workflow_task=True
        )
    )
    tool = _tool()
    tool["function"]["parameters"] = parameters
    payload = _request(tools=[tool])
    if modern:
        payload["wright_instruction_set"] = (
            load_default_workflow_instructions().model_dump(mode="json")
        )
    return bridge._validate(payload)


def test_original_depth_limit_is_unchanged_and_exact_modern_wrapper_adds_only_two_levels():
    original = nested(7)  # Depth15, near the provider contract boundary.
    assert schema_depth(original) == 15
    wrapped = workflow_action_intent_schema(original)
    assert schema_depth(wrapped) == 17
    bridge_validate(original)
    bridge_validate(wrapped, modern=True)
    with pytest.raises(HermesBridgeError, match="deeply nested"):
        bridge_validate(wrapped)
    with pytest.raises(HermesBridgeError, match="deeply nested"):
        bridge_validate(nested(8), modern=True)
    with pytest.raises(HermesBridgeError, match="deeply nested"):
        bridge_validate(workflow_action_intent_schema(nested(8)), modern=True)


def test_exact_depth16_provider_and_depth18_modern_envelope_are_accepted():
    original = nested(7)
    leaf = original
    for _ in range(7):
        leaf = leaf["properties"]["child"]
    leaf["enum"] = ["bounded"]
    assert schema_depth(original) == 16
    wrapped = workflow_action_intent_schema(original)
    assert schema_depth(wrapped) == 18
    bridge_validate(original)
    bridge_validate(wrapped, modern=True)


@pytest.mark.parametrize(
    "change",
    [
        lambda schema: schema.update(additionalProperties=True),
        lambda schema: schema["required"].remove("assumptions"),
        lambda schema: schema["properties"].update(hidden={"type": "object"}),
        lambda schema: schema["$defs"]["WorkflowAssumption"]["properties"].update(
            hidden={"type": "object"}
        ),
        lambda schema: schema["properties"]["schema_version"].update(const="forged/1"),
    ],
)
def test_modern_marker_does_not_qualify_a_forged_or_unbounded_envelope(change):
    schema = deepcopy(workflow_action_intent_schema(nested(7)))
    change(schema)
    with pytest.raises(HermesBridgeError, match="deeply nested"):
        bridge_validate(schema, modern=True)


def test_direct_shared_qualification_preserves_schema_identity():
    schema = workflow_action_intent_schema(nested(7))
    before = deepcopy(schema)
    qualify_workflow_tool_schema_depth(
        schema, action_intent_contract="wright.workflow-action-intent/1"
    )
    assert schema == before
    with pytest.raises(ValueError):
        qualify_workflow_tool_schema_depth(
            schema, action_intent_contract="wright.workflow-action-intent/999"
        )
