"""Task decisions use embedded instructions and exact compatible callbacks."""

from dataclasses import replace
import json

import pytest

from agent_adapters.workflow_instructions import load_default_workflow_instructions
from workspace_service.workflow_source_execution import WorkflowSourceExecutionError
from packages.workspace_service.tests.test_workflow_mcp_integration_restriction import (
    Gateway,
    runtime,
    step,
    tool,
)


@pytest.mark.asyncio
@pytest.mark.parametrize("policy", ["document_reasonable", "require_specified"])
async def test_mcp_forwards_typed_context_and_records_actual_primary_messages(policy):
    item = tool()
    service = runtime(Gateway([item]))
    instructions = load_default_workflow_instructions().model_dump(mode="json")
    instructions["policy"]["assumption_policy"] = policy
    task = replace(
        step(item),
        agent_task=True,
        instruction_set=instructions,
        output_ports=(("result", "engineering_document"),),
    )
    events, requests = [], []
    assumptions = [
        {
            "parameter": "concept.width",
            "value": "40",
            "units": "mm",
            "rationale": "Unspecified conceptual size",
            "affected_outputs": ["result"],
        }
    ]

    async def emit(kind, **payload):
        events.append((kind, payload))

    async def decide(
        messages,
        schemas,
        *,
        required,
        output_format,
        instruction_set,
        instruction_override,
    ):
        assert output_format == "json"
        assert instruction_set.policy.assumption_policy == policy
        requests.append(json.loads(json.dumps(messages)))
        if len(requests) == 1:
            return {
                "tool_calls": [
                    {
                        "id": "one",
                        "function": {
                            "name": schemas[0]["function"]["name"],
                            "arguments": json.dumps(
                                {
                                    "schema_version": "wright.workflow-action-intent/1",
                                    "arguments": {},
                                    "assumptions": [],
                                    "unresolved_required_information": [],
                                }
                            ),
                        },
                    }
                ]
            }
        return {
            "content": json.dumps(
                {
                    "status": "completed",
                    "response": '{"concept":true}',
                    "evidence": [1],
                    "assumptions": assumptions,
                }
            )
        }

    if policy == "require_specified":
        with pytest.raises(
            WorkflowSourceExecutionError, match="invalid declared assumptions"
        ):
            await service.run_task(task, "Prepare concept", decide, emit)
    else:
        value, records = await service.run_task(task, "Prepare concept", decide, emit)
        assert json.loads(value) == {"concept": True}
        assert len(records) == 1
        assert (
            next(payload for kind, payload in events if kind == "assumptions_recorded")[
                "assumptions"
            ]
            == assumptions
        )
    captured = [
        payload["invocation"] for kind, payload in events if kind == "model_invocation"
    ]
    assert len(captured) == len(requests) == 2
    assert [item["messages"] for item in captured] == requests
    assert captured[0]["resolved_instructions"]["role"] == "mcp-task"
    assert captured[0]["profile_id"] == "wright.workflow-defaults"


@pytest.mark.asyncio
async def test_legacy_callback_is_not_retried_and_failed_request_is_captured():
    # Qualified read-only measurement permits strict legacy transport capture.
    item = tool(annotations={"readOnlyHint": True})
    service = runtime(Gateway([item]))
    events, calls = [], []

    async def emit(kind, **payload):
        events.append((kind, payload))

    async def decide(messages, tools, *, required=False):
        calls.append(messages)
        raise ValueError("Synthetic transport failure")

    with pytest.raises(ValueError, match="Synthetic transport failure"):
        await service.run_task(
            replace(step(item), agent_task=True), "Measure", decide, emit
        )
    assert len(calls) == 1
    captured = next(
        payload["invocation"] for kind, payload in events if kind == "model_invocation"
    )
    assert captured["messages"] == calls[0]
    assert captured["profile_id"] == "wright.legacy-unattended-compatibility"
    assert service.gateway.calls == []
