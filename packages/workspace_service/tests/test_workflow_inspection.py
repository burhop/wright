from __future__ import annotations

from data_vault import WorkflowRunEventRecord, WorkflowRunRecord
from workspace_service.workflow_inspection import build_workflow_inspection


def persisted_run(**overrides) -> WorkflowRunRecord:
    values = {
        "run_id": "run-1",
        "workspace_id": "workspace-1",
        "session_id": "session-1",
        "workflow_id": "workflow-1",
        "revision": 2,
        "digest": "a" * 64,
        "graph": "Main",
        "state": "failed",
        "generation": 3,
        "started_at": 100,
        "completed_at": 109,
        "reason_code": "RIVET_MCP_TRANSPORT_CANCELLED",
        "output_summary": {"outputs": {"upstream": {"ok": True}}, "durationMs": 9000},
        "output_truncated": False,
        "trace_id": "trace-run-1",
    }
    values.update(overrides)
    return WorkflowRunRecord(**values)


def run_event(sequence: int, kind: str, **payload) -> WorkflowRunEventRecord:
    return WorkflowRunEventRecord("run-1", sequence, 100 + sequence, kind, payload)


def child_call(**overrides) -> dict:
    values = {
        "call_id": "call-1",
        "request_id": "request-1",
        "run_id": "run-1",
        "node_id": "node-search",
        "qualified_tool_name": "onshape.search",
        "trace_id": "trace-child-1",
        "state": "failed",
        "child_received": True,
        "started_at": "1970-01-01T00:01:41Z",
        "completed_at": "1970-01-01T00:01:42Z",
        "reason_code": "RIVET_MCP_TRANSPORT_CANCELLED",
        "result": None,
        "result_complete": True,
        "artifacts": [],
        "redaction_count": 0,
    }
    values.update(overrides)
    return values


def test_failed_child_is_correlated_with_plain_recovery_and_upstream_output() -> None:
    inspection = build_workflow_inspection(
        record=persisted_run(),
        events=(
            run_event(1, "started", phase="running"),
            run_event(2, "failed", code="RIVET_MCP_TRANSPORT_CANCELLED"),
        ),
        incremental_events=(
            run_event(2, "failed", code="RIVET_MCP_TRANSPORT_CANCELLED"),
        ),
        child_calls=(child_call(),),
        manifest={"residue_possible": False},
    )

    assert inspection["run"]["latest_sequence"] == 2
    assert inspection["steps"][0]["node_id"] == "node-search"
    assert inspection["diagnostic"]["code"] == "RIVET_MCP_TRANSPORT_CANCELLED"
    assert inspection["diagnostic"]["failed_step_id"] == "call-1"
    assert inspection["diagnostic"]["full_rerun_available"] is True
    assert inspection["diagnostic"]["partial_retry_available"] is False
    assert inspection["final_outputs"][0]["name"] == "upstream"


def test_old_success_record_is_projected_without_child_evidence() -> None:
    inspection = build_workflow_inspection(
        record=persisted_run(
            state="succeeded",
            reason_code=None,
            output_summary={"outputs": {"answer": 42}, "durationMs": 5},
        ),
        events=(run_event(1, "completed", duration_ms=5),),
        incremental_events=(),
        child_calls=(),
        manifest=None,
    )

    assert inspection["diagnostic"] is None
    assert inspection["final_outputs"][0]["value"] == 42
    assert inspection["completeness"]["outputs_complete"] is True
    assert inspection["events"] == []


def test_raw_typed_output_is_normalized_for_historical_inspection() -> None:
    markdown = (
        "# CAD providers\n\n| Provider | Status |\n| --- | --- |\n| Onshape | Ready |"
    )

    inspection = build_workflow_inspection(
        record=persisted_run(
            state="succeeded",
            reason_code=None,
            output_summary={
                "durationMs": 5,
                "outputs": {
                    "cadProviderDocumentationChain": {
                        "type": "object",
                        "value": {"result": markdown},
                    }
                },
            },
        ),
        events=(run_event(1, "completed", duration_ms=5),),
        incremental_events=(),
        child_calls=(),
        manifest=None,
    )

    projected = inspection["final_outputs"][0]
    assert projected["name"] == "cadProviderDocumentationChain"
    assert projected["kind"] == "structured"
    assert projected["value"] == {"result": markdown}
    assert projected["value"]["result"].splitlines()[2] == "| Provider | Status |"


def test_stored_typed_output_is_normalized_for_historical_inspection() -> None:
    markdown = (
        "# CAD providers\n\n| Provider | Status |\n| --- | --- |\n| Onshape | Ready |"
    )
    stored_result = {
        "result_id": "final_output:cadProviderDocumentationChain",
        "name": "cadProviderDocumentationChain",
        "origin": "final_output",
        "kind": "structured",
        "value": {"type": "object", "value": {"result": markdown}},
        "preview": "serialized transport envelope",
        "complete": True,
        "truncation_reason": None,
        "original_bytes": 128,
        "retained_bytes": 128,
        "digest": "b" * 64,
        "redaction_count": 2,
        "artifact": None,
    }

    inspection = build_workflow_inspection(
        record=persisted_run(
            state="succeeded",
            reason_code=None,
            output_summary={"results": [stored_result], "durationMs": 5},
        ),
        events=(run_event(1, "completed", duration_ms=5),),
        incremental_events=(),
        child_calls=(),
        manifest=None,
    )

    projected = inspection["final_outputs"][0]
    assert projected["kind"] == "structured"
    assert projected["value"] == {"result": markdown}
    assert projected["redaction_count"] == 2
    assert projected["digest"] != stored_result["digest"]


def test_lifecycle_events_project_all_nodes_and_merge_mcp_detail_by_node_id() -> None:
    inspection = build_workflow_inspection(
        record=persisted_run(
            state="succeeded", reason_code=None, output_summary={"outputs": {}}
        ),
        events=(
            run_event(
                1,
                "progress",
                phase="node-start",
                nodeId="node-prepare",
                nodeType="code",
                nodeTitle="Prepare inputs",
            ),
            run_event(
                2,
                "progress",
                phase="node-finish",
                nodeId="node-prepare",
                nodeType="code",
                nodeTitle="Prepare inputs",
            ),
            run_event(
                3,
                "progress",
                phase="node-start",
                nodeId="node-search",
                nodeType="mcpToolCall",
                nodeTitle="Inspect CAD",
            ),
            run_event(
                4,
                "progress",
                phase="node-finish",
                nodeId="node-search",
                nodeType="mcpToolCall",
                nodeTitle="Inspect CAD",
            ),
        ),
        incremental_events=(),
        child_calls=(
            child_call(
                state="succeeded",
                reason_code=None,
                qualified_tool_name=(
                    "1dbbe3ee-e4ae-4e86-b5df-e46de9c4eb59__list_cad_providers"
                ),
                started_at="1970-01-01T00:01:43Z",
                completed_at="1970-01-01T00:01:44Z",
            ),
        ),
        manifest={},
    )

    assert [step["node_id"] for step in inspection["steps"]] == [
        "node-prepare",
        "node-search",
    ]
    assert inspection["steps"][0] == {
        "step_id": "node:node-prepare",
        "sequence": 1,
        "node_id": "node-prepare",
        "node_type": "code",
        "label": "Prepare inputs",
        "kind": "node",
        "qualified_tool_name": None,
        "request_id": None,
        "trace_id": None,
        "state": "succeeded",
        "started_at": "1970-01-01T00:01:41Z",
        "completed_at": "1970-01-01T00:01:42Z",
        "duration_ms": 1000,
        "reason_code": None,
        "inputs": [],
        "outputs": [],
        "input_state": "unavailable",
        "output_state": "unavailable",
        "result": None,
        "artifacts": [],
        "redaction_count": 0,
        "complete": False,
    }
    merged = inspection["steps"][1]
    assert merged["step_id"] == "call-1"
    assert merged["kind"] == "mcp_call"
    assert merged["label"] == "Inspect CAD"
    assert "1dbbe3ee" not in merged["label"]
    assert merged["request_id"] == "request-1"
    assert inspection["progress"]["completed_steps"] == 2
    assert inspection["progress"]["total_steps"] == 2


def test_non_mcp_node_error_names_failed_node_and_preserves_code_duration() -> None:
    inspection = build_workflow_inspection(
        record=persisted_run(
            reason_code="RIVET_RUNNER_NETWORK_DENIED",
            output_summary={"outputs": {}},
            trace_id="trace-network-denied",
        ),
        events=(
            run_event(
                1,
                "progress",
                phase="node-start",
                nodeId="llm-node",
                nodeType="llmChatV2",
                nodeTitle="LLM Chat",
            ),
            run_event(
                3,
                "progress",
                phase="node-error",
                nodeId="llm-node",
                nodeType="llmChatV2",
                nodeTitle="LLM Chat",
                errorCode="RIVET_RUNNER_NETWORK_DENIED",
                errorMessage="sensitive request detail must not project",
            ),
            run_event(4, "failed", code="RIVET_RUNNER_NETWORK_DENIED"),
        ),
        incremental_events=(),
        child_calls=(),
        manifest=None,
    )

    step = inspection["steps"][0]
    assert step["label"] == "LLM Chat"
    assert step["node_type"] == "llmChatV2"
    assert step["state"] == "failed"
    assert step["reason_code"] == "RIVET_RUNNER_NETWORK_DENIED"
    assert step["duration_ms"] == 2000
    assert "errorMessage" not in step
    assert inspection["diagnostic"] == {
        "code": "RIVET_RUNNER_NETWORK_DENIED",
        "summary": "The workflow stopped before every step completed.",
        "recovery_action": "Inspect the failed step and run the saved revision again.",
        "failed_step_id": "node:llm-node",
        "failed_node_id": "llm-node",
        "failed_node_label": "LLM Chat",
        "qualified_tool_name": None,
        "trace_id": "trace-network-denied",
        "full_rerun_available": True,
        "partial_retry_available": False,
        "residue_possible": False,
    }
    assert inspection["completeness"]["evidence_available"] is True


def test_partial_historical_lifecycle_uses_stable_type_not_uuid_as_label() -> None:
    historical_node_id = "8125ebb1-16eb-4a6e-8101-ed49189ef106"
    inspection = build_workflow_inspection(
        record=persisted_run(state="running", completed_at=None, reason_code=None),
        events=(
            run_event(
                1,
                "progress",
                phase="node-start",
                nodeId=historical_node_id,
                nodeType="textNode",
            ),
        ),
        incremental_events=(),
        child_calls=(),
        manifest={"event_truncated": True},
    )

    assert inspection["steps"][0]["node_id"] == historical_node_id
    assert inspection["steps"][0]["label"] == "textNode"
    assert inspection["steps"][0]["state"] == "running"
    assert inspection["steps"][0]["completed_at"] is None
    assert inspection["steps"][0]["duration_ms"] is None
    assert inspection["progress"]["current_step_id"] == f"node:{historical_node_id}"
    assert inspection["completeness"]["steps_complete"] is False
    assert set(inspection["completeness"]["reasons"]) == {
        "step_results_incomplete",
        "inputs_not-retained",
        "inventory_not-retained",
        "events_truncated",
    }


def _projected_value(name: str, origin: str, value, data_type: str) -> dict:
    return {
        "result_id": f"{origin}:{name}",
        "name": name,
        "origin": origin,
        "kind": "number" if isinstance(value, int) else "text",
        "data_type": data_type,
        "evidence_state": "available",
        "value": value,
        "preview": str(value),
        "complete": True,
        "truncation_reason": None,
        "original_bytes": len(str(value)),
        "retained_bytes": len(str(value)),
        "digest": "c" * 64,
        "redaction_count": 0,
        "artifact": None,
    }


def test_exact_revision_inventory_inputs_and_node_values_are_projected_once() -> None:
    inspection = build_workflow_inspection(
        record=persisted_run(
            state="succeeded", reason_code=None, output_summary={"outputs": {}}
        ),
        events=(
            run_event(
                1,
                "inspection-context",
                revision=2,
                digest="a" * 64,
                runInputs=[_projected_value("length", "run_input", 25, "number")],
                inputsState="available",
                graphNodes=[
                    {
                        "node_id": "node-a",
                        "node_type": "code",
                        "label": "Prepare dimensions",
                        "order": 1,
                    },
                    {
                        "node_id": "node-b",
                        "node_type": "mcpToolCall",
                        "label": "Inspect CAD",
                        "order": 2,
                    },
                    {
                        "node_id": "node-c",
                        "node_type": "graphOutput",
                        "label": "Final result",
                        "order": 3,
                    },
                ],
                inventoryState="available",
            ),
            run_event(
                2,
                "progress",
                phase="node-start",
                nodeId="node-a",
                nodeType="code",
                nodeTitle="Prepare dimensions",
                inputValues=[_projected_value("length", "node_input", 25, "number")],
                inputState="available",
            ),
            run_event(
                3,
                "progress",
                phase="node-finish",
                nodeId="node-a",
                nodeType="code",
                nodeTitle="Prepare dimensions",
                durationMs=12,
                outputValues=[_projected_value("length", "node_output", 25, "number")],
                outputState="available",
            ),
            run_event(
                4,
                "progress",
                phase="node-excluded",
                nodeId="node-b",
                nodeType="mcpToolCall",
                nodeTitle="Inspect CAD",
                exclusionReason="control flow excluded",
                inputValues=[],
                outputValues=[],
                inputState="not-run",
                outputState="not-run",
            ),
        ),
        incremental_events=(),
        child_calls=(),
        manifest={},
    )

    assert inspection["inputs_state"] == "available"
    assert inspection["run_inputs"][0]["value"] == 25
    assert [step["node_id"] for step in inspection["steps"]] == [
        "node-a",
        "node-b",
        "node-c",
    ]
    assert inspection["steps"][0]["duration_ms"] == 12
    assert inspection["steps"][0]["inputs"][0]["name"] == "length"
    assert inspection["steps"][0]["outputs"][0]["value"] == 25
    assert inspection["steps"][0]["complete"] is True
    assert inspection["steps"][1]["state"] == "not-run"
    assert inspection["steps"][2]["state"] == "not-run"
    assert inspection["progress"]["current_step_id"] is None


def test_artifacts_are_first_and_terminal_failure_without_reason_has_diagnosis() -> (
    None
):
    manifest = {
        "artifacts": [
            {
                "artifact_id": "models/bracket.stl",
                "media_type": "model/stl",
                "sha256": "d" * 64,
                "bytes": 2048,
                "label": "Bracket STL",
            }
        ]
    }
    succeeded = build_workflow_inspection(
        record=persisted_run(
            state="succeeded",
            reason_code=None,
            output_summary={"outputs": {"message": "models/other.stl"}},
        ),
        events=(),
        incremental_events=(),
        child_calls=(),
        manifest=manifest,
    )
    assert [item["kind"] for item in succeeded["final_outputs"]] == [
        "artifact",
        "text",
    ]
    assert succeeded["final_outputs"][0]["artifact"]["sha256"] == "d" * 64
    assert succeeded["final_outputs"][1]["artifact"] is None

    failed = build_workflow_inspection(
        record=persisted_run(
            state="failed",
            reason_code=None,
            output_summary=None,
            trace_id="trace-unknown-failure",
        ),
        events=(),
        incremental_events=(),
        child_calls=(),
        manifest=None,
    )
    assert failed["diagnostic"]["code"] == "RIVET_RUN_FAILED"
    assert failed["diagnostic"]["failed_node_label"] is None
    assert failed["diagnostic"]["trace_id"] == "trace-unknown-failure"
    assert failed["run"]["has_diagnostic"] is True
