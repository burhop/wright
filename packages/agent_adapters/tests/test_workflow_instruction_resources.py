"""Saved resources, typed policies and actual primary request evidence."""

import base64
import json
from types import SimpleNamespace

import pytest

from agent_adapters import report_generation
from agent_adapters import workflow_instructions as resources
from core.process_validation import canonical_digest
from core.workflow_instructions import WorkflowInstructionSet, instruction_text_digest
from core.workflow_step_outcomes import InvalidStepOutcomeError

from test_workflow_unattended_outcomes import model_transport, outcome


def changed_asset(instructions, identity, text):
    value = instructions.model_dump(mode="json")
    asset = next(asset for asset in value["assets"] if asset["id"] == identity)
    asset["body"] = text
    asset["body_digest"] = instruction_text_digest(text)
    return WorkflowInstructionSet.model_validate(value)


def test_packaged_catalog_contains_all_primary_dependencies():
    instructions = resources.load_default_workflow_instructions()
    assert instructions.profile_id == "wright.workflow-defaults"
    assert instructions.profile_version == "1.4.0"
    assert instructions.action_intent_contract == "wright.workflow-action-intent/1"
    assert instructions.policy.assumption_policy == "document_reasonable"
    assert {binding.role for binding in instructions.bindings} >= {
        "workflow-task",
        "image-generation",
        "mcp-task",
        "recovery",
        "protocol",
    }
    assert (
        instructions.digest
        == WorkflowInstructionSet.model_validate_json(
            instructions.model_dump_json()
        ).digest
    )
    assert {asset.id for asset in instructions.assets} >= {
        "policy.require-specified",
        "policy.document-reasonable",
        "format.text",
        "format.markdown",
        "format.html",
        "format.json",
    }


@pytest.mark.parametrize(
    "role,variables",
    [
        ("image-generation", {}),
        (
            "mcp-task",
            {
                "output_format": "json",
                "max_tool_calls": "3",
                "task_guidance": "Measure only",
            },
        ),
        ("recovery", {"output_format": "json"}),
        ("protocol", {}),
    ],
)
def test_saved_resource_resolution_never_reads_current_defaults(
    monkeypatch, role, variables
):
    saved = resources.load_default_workflow_instructions()
    expected = resources.resolve_workflow_instructions(
        role, instruction_set=saved, variables=variables
    )
    monkeypatch.setattr(
        resources,
        "load_default_workflow_instructions",
        lambda: pytest.fail("Fresh defaults read during execution"),
    )
    actual = resources.resolve_workflow_instructions(
        role, instruction_set=json.loads(saved.model_dump_json()), variables=variables
    )
    assert actual == expected


def test_role_override_and_policy_are_explicit_and_scoped():
    saved = resources.load_default_workflow_instructions()
    override = {
        "origin": "step.author",
        "roles": ["workflow-task"],
        "text": "Prefer a concise table",
        "assumption_policy": "require_specified",
    }
    text = resources.workflow_response_instructions(
        "text", instruction_set=saved, instruction_override=override
    )
    image = resources.resolve_workflow_instructions(
        "image-generation", instruction_set=saved, instruction_override=override
    )
    assert text.assumption_policy == "require_specified"
    assert text.text.endswith("Prefer a concise table")
    assert "policy.require-specified" in text.asset_ids
    assert image.assumption_policy == "document_reasonable"
    assert "Prefer a concise table" not in image.text


def test_missing_captured_format_does_not_fall_back_to_shipped_body():
    saved = resources.load_default_workflow_instructions().model_dump(mode="json")
    saved["assets"] = [
        asset for asset in saved["assets"] if asset["id"] != "format.json"
    ]
    for binding in saved["bindings"]:
        binding["asset_ids"] = [
            identity for identity in binding["asset_ids"] if identity != "format.json"
        ]
    with pytest.raises(ValueError, match="missing format.json"):
        resources.workflow_response_instructions("json", instruction_set=saved)


def test_named_legacy_profile_retains_strict_policy():
    legacy = resources.embedded_instruction_set()
    assert legacy.profile_id == "wright.legacy-unattended-compatibility"
    assert legacy.policy.assumption_policy == "require_specified"
    assert legacy.action_intent_contract is None
    assert resources.workflow_action_intent_instructions(None) is None


def test_action_protocol_is_embedded_exactly_and_does_not_read_new_defaults(
    monkeypatch,
):
    saved = changed_asset(
        resources.load_default_workflow_instructions(),
        "protocol.action-intent",
        "Saved protocol with explicit action choices.",
    )
    monkeypatch.setattr(
        resources,
        "load_default_workflow_instructions",
        lambda: pytest.fail("Read current defaults"),
    )
    assert (
        resources.workflow_action_intent_instructions(saved)
        == "Saved protocol with explicit action choices."
    )
    resources.validate_workflow_instruction_dependencies(saved, "mcp-task")
    legacy = saved.model_dump(mode="json")
    del legacy["action_intent_contract"]
    legacy["assets"] = [
        item for item in legacy["assets"] if item["id"] != "protocol.action-intent"
    ]
    assert resources.workflow_action_intent_instructions(legacy) is None
    resources.validate_workflow_instruction_dependencies(legacy, "mcp-task")


@pytest.mark.parametrize("change", ["missing", "wrong-role", "variables"])
def test_modern_action_protocol_cannot_fall_back_to_current_defaults(change):
    saved = resources.load_default_workflow_instructions().model_dump(mode="json")
    item = next(
        item for item in saved["assets"] if item["id"] == "protocol.action-intent"
    )
    if change == "missing":
        saved["assets"].remove(item)
    elif change == "wrong-role":
        item["role"] = "protocol"
    else:
        item["body"] = "Use {{runtime_choice}}"
        item["variables"] = ["runtime_choice"]
        item["body_digest"] = instruction_text_digest(item["body"])
    with pytest.raises(ValueError, match="action-intent"):
        resources.validate_workflow_instruction_dependencies(saved, "mcp-task")


@pytest.mark.parametrize("role", ["workflow-task", "image-generation", "mcp-task"])
def test_readiness_checks_captured_primary_dependencies_without_defaults(
    monkeypatch, role
):
    saved = resources.load_default_workflow_instructions()
    monkeypatch.setattr(
        resources,
        "load_default_workflow_instructions",
        lambda: pytest.fail("Fresh defaults read"),
    )
    resources.validate_workflow_instruction_dependencies(saved, role)


@pytest.mark.parametrize(
    "identity,role",
    [
        ("recovery.format", "mcp-task"),
        ("recovery.tool-free", "mcp-task"),
        ("policy.document-reasonable", "image-generation"),
        ("format.html", "workflow-task"),
    ],
)
def test_readiness_rejects_uncaptured_helper(identity, role):
    saved = resources.load_default_workflow_instructions().model_dump(mode="json")
    saved["assets"] = [asset for asset in saved["assets"] if asset["id"] != identity]
    for binding in saved["bindings"]:
        binding["asset_ids"] = [
            name for name in binding["asset_ids"] if name != identity
        ]
    saved["bindings"] = [
        binding for binding in saved["bindings"] if binding["asset_ids"]
    ]
    with pytest.raises(ValueError):
        resources.validate_workflow_instruction_dependencies(saved, role)


@pytest.mark.asyncio
async def test_failure_capture_observer_runs_before_invalid_outcome(monkeypatch):
    requests = model_transport(monkeypatch, [{"content": "Unstructured question?"}])
    captured = []

    async def observe(invocation):
        assert requests == []
        captured.append(invocation)

    with pytest.raises(InvalidStepOutcomeError):
        await report_generation.generate_workflow_response(
            "Test", "text", invocation_observer=observe
        )
    assert captured[0]["request_digest"] == canonical_digest(requests[0])
    assert captured[0]["messages"] == requests[0]["messages"]


@pytest.mark.asyncio
async def test_text_adapter_submits_saved_body_and_captures_image_reference(
    monkeypatch,
):
    saved = changed_asset(
        resources.load_default_workflow_instructions(),
        "task.response",
        "SAVED TASK BODY\n{{output_format_instructions}}",
    )
    requests = model_transport(monkeypatch, [{"content": json.dumps(outcome())}])
    monkeypatch.setattr(
        resources,
        "load_default_workflow_instructions",
        lambda: pytest.fail("Fresh defaults read"),
    )
    value = await report_generation.generate_workflow_response(
        "Describe image",
        "text",
        images=["data:image/png;base64,AAAA"],
        instruction_set=saved.model_dump(mode="json"),
    )
    assert "SAVED TASK BODY" in requests[0]["messages"][0]["content"]
    assert value.wright_instructions["text"] == requests[0]["messages"][0]["content"]
    captured = value.wright_invocations[0]
    assert captured["request_digest"] == canonical_digest(requests[0])
    assert captured["messages"][0] == requests[0]["messages"][0]
    assert captured["messages"][1]["content"][1]["type"] == "image_reference"
    assert "data:image" not in json.dumps(captured)
    assert captured["instruction_set_digest"] == saved.digest
    assert captured["capture_scope"] == "primary_adapter_request"


@pytest.mark.asyncio
@pytest.mark.parametrize("policy", ["document_reasonable", "require_specified"])
async def test_text_assumptions_are_typed_and_policy_checked(monkeypatch, policy):
    saved = resources.load_default_workflow_instructions().model_dump(mode="json")
    saved["policy"]["assumption_policy"] = policy
    assumptions = [
        {
            "parameter": "visual.finish",
            "value": "Brushed metal",
            "units": "",
            "rationale": "Unspecified appearance for concept only",
            "affected_outputs": ["render"],
        }
    ]
    reply = {**outcome(), "assumptions": assumptions}
    requests = model_transport(monkeypatch, [{"content": json.dumps(reply)}])
    if policy == "require_specified":
        with pytest.raises(InvalidStepOutcomeError):
            await report_generation.generate_workflow_response(
                "Prepare a concept", "text", instruction_set=saved
            )
    else:
        value = await report_generation.generate_workflow_response(
            "Prepare a concept", "text", instruction_set=saved
        )
        assert value.wright_assumptions == assumptions
        assert value.wright_outcome["assumptions"] == assumptions
    assert len(requests) == 1


@pytest.mark.asyncio
async def test_image_primary_messages_and_saved_body_are_retained(monkeypatch):
    from agent_adapters.hermes_role import HermesRoleTransport

    saved = changed_asset(
        resources.load_default_workflow_instructions(), "task.image", "SAVED IMAGE ROLE"
    )
    requests = []
    resolution = {"configuration_digest": "a" * 64, "model_reference": "model-test"}

    class Transport:
        async def call(self, payload):
            requests.append(payload)
            return {
                "image_base64": base64.b64encode(b"synthetic-private-image").decode(),
                "response_model": "model-test",
                "output_format": "png",
                "resolution": resolution,
                "tool": "image_generation",
            }

    monkeypatch.setattr(HermesRoleTransport, "from_host", lambda: Transport())
    value = await report_generation.generate_workflow_response(
        "Render",
        "image-png",
        images=["data:image/png;base64,AAAA"],
        expected_resolution=resolution,
        instruction_set=saved,
    )
    assert "SAVED IMAGE ROLE" in requests[0]["messages"][0]["content"]
    assert value.wright_invocations[0]["request_digest"] == canonical_digest(
        requests[0]
    )
    assert "synthetic-private-image" not in json.dumps(value.wright_invocations)
    assert value.wright_image["content"] == b"synthetic-private-image"


def test_capture_is_immutable_and_redacts_sensitive_tools():
    request = {
        "messages": [{"role": "user", "content": "Original"}],
        "tools": [{"token": "private-secret", "name": "measure"}],
    }
    captured = resources.invocation_evidence(request, operation="test")
    request["messages"][0]["content"] = "Changed"
    assert captured["messages"][0]["content"] == "Original"
    assert "private-secret" not in json.dumps(captured)


@pytest.mark.asyncio
async def test_null_primary_decision_retries_retain_exact_attempts(monkeypatch):
    from agent_adapters import hermes_openai_bridge

    requests = []
    messages = [
        {"role": "system", "content": "Captured main task"},
        {"role": "user", "content": "Render target"},
        {
            "role": "tool",
            "content": json.dumps(
                {
                    "status": "succeeded",
                    "tool_call_number": 1,
                    "text": "Export completed",
                }
            ),
        },
    ]

    class Bridge:
        def __init__(self, settings):
            pass

        async def complete(self, payload):
            requests.append(json.loads(json.dumps(payload)))
            raise AttributeError("'NoneType' object has no attribute 'rstrip'")

    monkeypatch.setattr(
        report_generation,
        "resolve_hermes_api_settings",
        lambda: SimpleNamespace(base_url="http://model.test-only", api_key=""),
    )
    monkeypatch.setattr(hermes_openai_bridge, "HermesOpenAICompatibilityBridge", Bridge)
    saved = resources.load_default_workflow_instructions()
    value = await report_generation.decide_workflow_tool_action(
        messages, [], output_format="json", instruction_set=saved
    )
    assert json.loads(value["content"])["status"] == "blocked"
    assert len(requests) == len(value.wright_invocations) == 3
    assert [item["attempt"] for item in value.wright_invocations] == [1, 2, 3]
    assert [item["request_digest"] for item in value.wright_invocations] == [
        canonical_digest(item) for item in requests
    ]
    assert all(item["messages"] == messages for item in value.wright_invocations)
