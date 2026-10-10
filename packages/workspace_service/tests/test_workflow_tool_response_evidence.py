"""A returned tool diagnostic survives failed engineering output validation."""

import asyncio
import json

import pytest

from core.process_validation import canonical_digest
from tool_registry.gateway_models import GatewayToolResult
from workspace_service.workflow_run_record import record_workflow_run
from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    compile_prompt_workflow,
    execute_prompt_workflow,
)
from packages.workspace_service.tests.test_workflow_mcp_execution import (
    TOOL,
    mcp,
    runtime,
    schema_digest,
)
from packages.workspace_service.tests.test_workflow_source_execution import (
    service,
    source,
)


@pytest.mark.parametrize("provider_error", [False, True])
def test_actual_response_is_retained_before_file_gate_or_error(
    tmp_path, provider_error
):
    block = mcp(
        mcp_arguments=json.dumps({"query": "Generate digital analysis"}),
        mcp_argument_ports="{}",
        expected_files="field.csv",
    )
    plan = compile_prompt_workflow(source(block))
    gateway, tools = runtime()
    returned = GatewayToolResult(
        content=(
            {"type": "text", "text": "Numerical solver stopped: invalid node value"},
        ),
        structured_content={
            "status": "failed",
            "stderr": "invalid node value",
            "api_key": "private-test-secret",
        },
        is_error=provider_error,
    )
    gateway.result = returned
    tools.preflight(plan.steps[0])
    app = service(tmp_path)

    async def execute(emit):
        return await execute_prompt_workflow(
            service=app,
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=None,
            tool_runtime=tools,
            on_event=emit,
            run_id="tool-diagnostic-test",
        )

    with pytest.raises(WorkflowSourceExecutionError) as caught:
        asyncio.run(
            record_workflow_run(
                service=app,
                workspace_dir=str(tmp_path),
                source_path="workflows/tool-diagnostic.workflow.wflow",
                source_digest=plan.definition_digest,
                execute=execute,
                run_id="tool-diagnostic-test",
            )
        )
    assert caught.value.code == (
        "MCP_CALL_FAILED" if provider_error else "WORKFLOW_OUTPUT_INVALID"
    )
    logs = list((tmp_path / "runs/tool-diagnostic").glob("*.json"))
    assert len(logs) == 1
    raw = logs[0].read_text()
    assert "private-test-secret" not in raw
    record = json.loads(raw)
    event = next(e for e in record["events"] if e["kind"] == "tool_response_received")
    assert event["task_id"] == "search" and event["tool"] == TOOL.name
    assert event["schema_digest"] == schema_digest(TOOL)
    assert event["response_digest"] == canonical_digest(
        {
            "structured_content": returned.structured_content,
            "content": returned.content,
            "is_error": returned.is_error,
        }
    )
    assert event["diagnostic"]["structured_content"]["stderr"] == "invalid node value"
    assert event["diagnostic"]["structured_content"]["api_key"] == "[REDACTED]"
    assert event["is_error"] is provider_error
    assert record["status"] == "failed" and record["code"] == caught.value.code
    assert not any(
        e["kind"] in {"result_ready", "step_completed"} for e in record["events"]
    )
    assert len(gateway.calls) == 1
