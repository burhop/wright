"""Final formatting repair cannot execute tools or alter completion evidence."""

import json
from dataclasses import replace

import pytest

from packages.workspace_service.tests.test_workflow_mcp_integration_restriction import (
    Gateway,
    runtime,
    step,
    tool,
)
from workspace_service.workflow_source_execution import WorkflowSourceExecutionError


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "repair_kind",
    [
        "valid",
        "tool_call",
        "changed_evidence",
        "boolean_evidence",
        "changed_status",
        "invalid_json",
        "model_error",
    ],
)
async def test_tool_free_format_correction_preserves_single_actual_call(repair_kind):
    item = tool()
    gateway = Gateway([item])
    service = runtime(gateway)
    events, decisions = [], []

    async def emit(kind, **payload):
        events.append((kind, payload))

    async def decide(messages, schemas, **kwargs):
        decisions.append(schemas)

        class Decision(dict):
            pass

        def observed(value):
            message = Decision(value)
            message.wright_usage = {
                "status": "reported",
                "model": "test-model",
                "input_tokens": len(decisions),
                "cached_input_tokens": 0,
                "output_tokens": 1,
                "reasoning_output_tokens": 0,
                "total_tokens": len(decisions) + 1,
                "duration_ms": len(decisions),
            }
            return message

        if len(decisions) == 1:
            return observed(
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": "first",
                            "function": {
                                "name": schemas[0]["function"]["name"],
                                "arguments": "{}",
                            },
                        }
                    ],
                }
            )
        if len(decisions) == 2:
            return observed(
                {
                    "role": "assistant",
                    "content": json.dumps(
                        {
                            "status": "completed",
                            "response": "The observed volume is 123 cubic millimeters.",
                            "evidence": [1],
                        }
                    ),
                }
            )
        assert schemas == []
        assert len(messages) == 2
        assert [message["role"] for message in messages] == ["system", "user"]
        assert all(isinstance(message["content"], str) for message in messages)
        assert "PRIVATE_TASK_PROMPT" not in json.dumps(messages)
        assert "data:image" not in json.dumps(messages)
        assert "tool_calls" not in json.dumps(messages)
        assert json.loads(messages[1]["content"]) == {
            "status": "completed",
            "response": "The observed volume is 123 cubic millimeters.",
            "evidence": [1],
        }
        if repair_kind == "model_error":
            raise ValueError("Provider request rejected")
        corrected = {
            "status": "completed",
            "response": '{"volume_mm3":123}',
            "evidence": [1],
        }
        if repair_kind == "changed_evidence":
            corrected["evidence"] = [2]
        if repair_kind == "invalid_json":
            corrected["response"] = "Still prose"
        if repair_kind == "boolean_evidence":
            corrected["evidence"] = [True]
        if repair_kind == "changed_status":
            corrected["status"] = "blocked"
        message = {"role": "assistant", "content": json.dumps(corrected)}
        if repair_kind == "tool_call":
            message["tool_calls"] = [
                {"function": {"name": "tool_0", "arguments": "{}"}}
            ]
        return observed(message)

    if repair_kind == "valid":
        result, records = await service.run_task(
            replace(step(item), agent_task=True),
            "PRIVATE_TASK_PROMPT",
            decide,
            emit,
            images=["data:image/png;base64,private"],
        )
        assert json.loads(result) == {"volume_mm3": 123}
        assert len(records) == 1
    else:
        with pytest.raises(WorkflowSourceExecutionError, match="formatting"):
            await service.run_task(
                replace(step(item), agent_task=True),
                "PRIVATE_TASK_PROMPT",
                decide,
                emit,
                images=["data:image/png;base64,private"],
            )
    assert len(gateway.calls) == 1
    assert len(decisions) == 3
    usage = [payload for kind, payload in events if kind == "model_usage"]
    assert len(usage) == 3
    assert [payload["usage"]["input_tokens"] for payload in usage] == [
        1,
        2,
        None if repair_kind == "model_error" else 3,
    ]
    assert usage[-1]["usage"]["status"] == (
        "unknown" if repair_kind == "model_error" else "reported"
    )
    assert any(kind == "task_response_format_repair" for kind, _ in events)
    failures = [
        payload
        for kind, payload in events
        if kind == "task_response_format_repair_failed"
    ]
    assert len(failures) == (repair_kind != "valid")
    if failures:
        assert failures[0]["evidence"] == [1]
        assert len(failures[0]["correction_preview"]) <= 2048
