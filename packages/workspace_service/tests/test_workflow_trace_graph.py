from data_vault import WorkflowRunEventRecord, WorkflowRunRecord
from workspace_service.rivet_validation import project_graph_trace
from workspace_service.workflow_inspection import build_workflow_inspection


PROJECT = """version: 4
data:
  graphs:
    graph-1:
      metadata:
        id: graph-1
        name: Review graph
      nodes:
        '[first]:text "Prepare"':
          data:
            text: Use the retained design document.
          outgoingConnections:
            - output->"Check" second/input
          visualData: 10/20/220/null//
        '[second]:text "Check"':
          data: {}
          visualData: 360/20/220/null//
  metadata:
    mainGraphId: graph-1
"""


def test_executed_graph_projection_keeps_layout_prompt_and_connections() -> None:
    graph, complete = project_graph_trace(PROJECT, selected_graph="graph-1")
    assert complete is True
    assert graph["name"] == "Review graph"
    assert graph["nodes"][0]["node_id"] == "first"
    assert graph["nodes"][0]["x"] == 10
    assert graph["nodes"][0]["prompt"] == "Use the retained design document."
    assert graph["connections"][0]["source_node_id"] == "first"
    assert graph["connections"][0]["target_node_id"] == "second"


def test_repeated_node_visits_remain_ordered_attempts() -> None:
    record = WorkflowRunRecord(
        run_id="run-1",
        workspace_id="workspace-1",
        session_id="session-1",
        workflow_id="workflow-1",
        revision=1,
        digest="a" * 64,
        graph="graph-1",
        state="succeeded",
        generation=1,
        started_at=1,
        completed_at=6,
        reason_code=None,
        output_summary={"outputs": {}},
        output_truncated=False,
    )
    events = tuple(
        WorkflowRunEventRecord("run-1", sequence, sequence, "progress", payload)
        for sequence, payload in enumerate(
            (
                {"phase": "node-start", "nodeId": "first", "nodeTitle": "Prepare"},
                {"phase": "node-error", "nodeId": "first", "errorCode": "retry"},
                {"phase": "node-start", "nodeId": "first", "nodeTitle": "Prepare"},
                {"phase": "node-finish", "nodeId": "first", "outputValues": []},
            ),
            start=1,
        )
    )
    inspection = build_workflow_inspection(
        record=record, events=events, incremental_events=(), child_calls=(), manifest={}
    )
    assert [(step["attempt"], step["state"]) for step in inspection["steps"]] == [
        (1, "failed"),
        (2, "succeeded"),
    ]
    assert inspection["steps"][0]["step_id"] == "node:first"
    assert inspection["steps"][1]["step_id"] == "node:first:attempt:2"
