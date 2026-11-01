from __future__ import annotations

from time import perf_counter

from core.workflow_trace import (
    TraceEvidenceRecord,
    TraceEvidenceSubject,
    TraceRunRecord,
)
from data_vault import (
    WorkflowRunEventRecord,
    WorkflowRunRecord,
    WorkflowTraceRepository,
)
from workspace_service.workflow_inspection import build_workflow_inspection
from workspace_service.workflow_trace.projection import WorkflowTraceProjection


def test_representative_trace_initial_projection_stays_under_two_seconds(
    tmp_path,
) -> None:
    graph_nodes = [
        {
            "node_id": f"node-{index}",
            "node_type": "generic",
            "label": f"Engineering step {index}",
            "order": index + 1,
        }
        for index in range(100)
    ]
    record = WorkflowRunRecord(
        run_id="run-performance",
        workspace_id="workspace-1",
        session_id="session-1",
        workflow_id="workflow-1",
        revision=1,
        digest="a" * 64,
        graph="main",
        state="succeeded",
        generation=1,
        started_at=1,
        completed_at=2,
        reason_code=None,
        output_summary={"outputs": {"result": "ready"}},
        output_truncated=False,
    )
    events = (
        WorkflowRunEventRecord(
            run_id=record.run_id,
            sequence=1,
            occurred_at=1,
            kind="inspection-context",
            payload={
                "revision": 1,
                "digest": "a" * 64,
                "inputsState": "available",
                "inventoryState": "available",
                "inventoryComplete": True,
                "graphNodes": graph_nodes,
                "graphTrace": {
                    "graph_id": "main",
                    "name": "Main",
                    "nodes": [
                        {
                            **node,
                            "x": (index % 10) * 240,
                            "y": (index // 10) * 120,
                            "width": 220,
                            "prompt": None,
                            "configuration": {},
                        }
                        for index, node in enumerate(graph_nodes)
                    ],
                    "connections": [],
                },
            },
        ),
    )
    repository = WorkflowTraceRepository(tmp_path / "state.db")
    repository.put_run(
        TraceRunRecord(
            workspace_id="workspace-1",
            run_id=record.run_id,
            source_kind="rivet",
            source_record_ref=f"rivet-run:{record.run_id}",
            source_record_digest="b" * 64,
            workflow_id="workflow-1",
            definition_digest="a" * 64,
            original_status="succeeded",
            outcome="completed",
            capture_state="complete",
            started_at=1,
            ended_at=2,
        )
    )
    repository.put_evidence(
        TraceEvidenceRecord(
            evidence_id="evidence-performance",
            run_id=record.run_id,
            producer="performance-fixture",
            producer_version="1",
            producer_record_id="record-1",
            kind="validation",
            recorded_at=2,
            subjects=tuple(
                TraceEvidenceSubject(
                    subject_kind="artifact_version",
                    subject_id=f"artifact-{index}",
                    revision="1",
                )
                for index in range(1000)
            ),
            statement="Representative evidence reference set.",
        )
    )

    started = perf_counter()
    inspection = build_workflow_inspection(
        record=record,
        events=events,
        incremental_events=(),
        child_calls=(),
        manifest=None,
    )
    summary = WorkflowTraceProjection(repository).summary(
        workspace_id="workspace-1", run_id=record.run_id
    )
    elapsed = perf_counter() - started

    assert len(inspection["graph"]["nodes"]) == 100
    assert len(summary["evidence"][0]["subjects"]) == 1000
    assert elapsed < 2
