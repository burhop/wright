from __future__ import annotations

from types import SimpleNamespace

from workspace_service.workflow_trace.canonical import (
    build_canonical_trace,
    canonical_artifact_paths,
    project_prompt_workflow_trace,
)


def test_new_canonical_run_snapshot_preserves_graph_prompts_and_connections() -> None:
    first = SimpleNamespace(
        id="requirements",
        title="Read requirements",
        prompt="Read the approved requirements.",
        references=(),
        output_format="markdown",
        output_path="requirements.md",
        agent_task=False,
        tool_name="",
        server_id="",
        max_revisions=0,
    )
    second = SimpleNamespace(
        id="design",
        title="Create design",
        prompt="Create the design from the requirements.",
        references=(("requirements", "requirements.document"),),
        output_format="step",
        output_path="housing.step",
        agent_task=False,
        tool_name="cad.create",
        server_id="cad",
        max_revisions=2,
    )
    graph = project_prompt_workflow_trace(
        SimpleNamespace(title="Housing review", steps=(first, second))
    )

    assert graph["nodes"][1]["prompt"] == second.prompt
    assert graph["connections"] == [
        {
            "connection_id": "requirements:design:requirements",
            "source_node_id": "requirements",
            "target_node_id": "design",
            "source_port": "document",
            "target_port": "requirements",
            "label": "requirements",
        }
    ]


def test_canonical_trace_keeps_repeated_attempts_and_partial_failure_results() -> None:
    artifact = {
        "id": "housing-v1",
        "kind": "cad_model",
        "name": "Housing",
        "representations": [
            {
                "kind": "workspace_file",
                "location": "outputs/housing.step",
                "format": "model/step",
                "sha256": "a" * 64,
                "size_bytes": 42,
            }
        ],
    }
    record = {
        "workflow_path": "workflows/housing.workflow.wflow",
        "source_digest": "b" * 64,
        "started_at": "2026-09-16T10:00:00Z",
        "completed_at": "2026-09-16T10:00:10Z",
        "status": "failed",
        "error": "Mesh generation stopped.",
        "partial_results": {"housing-v1": artifact},
        "result": {
            "run_id": "run-1",
            "revision_attempts": [
                {
                    "task_id": "requirements",
                    "task_title": "Read requirements",
                    "response": "first requirement revision",
                },
                {
                    "task_id": "design",
                    "task_title": "Create design",
                    "response": "first revision",
                },
            ],
            "steps": [
                {
                    "task_id": "requirements",
                    "task_title": "Read requirements",
                    "response": "second requirement revision",
                },
                {
                    "task_id": "design",
                    "task_title": "Create design",
                    "response": "second revision",
                },
            ],
        },
        "trace_inputs": {"requirements": "c" * 64},
        "trace_definition": {
            "graph_id": "canonical",
            "name": "Housing",
            "nodes": [],
            "connections": [
                {
                    "connection_id": "requirements:design:document",
                    "source_node_id": "requirements",
                    "target_node_id": "design",
                    "source_port": "document",
                    "target_port": "requirements",
                    "label": "requirements",
                }
            ],
        },
        "events": [{"kind": "run_started"}, {"kind": "step_completed"}],
    }
    trace = build_canonical_trace(
        record,
        workspace_id="workspace-1",
        session_id="session-1",
        path="runs/housing/run.json",
    )

    assert trace["run"]["state"] == "failed"
    assert trace["diagnostic"]["summary"] == "Mesh generation stopped."
    assert [step["attempt"] for step in trace["steps"]] == [1, 1, 2, 2]
    assert trace["graph"]["connections"][0]["traversals"] == [
        {
            "traversal_id": "canonical:requirements:design:document:1",
            "sequence": 2,
            "source_step_id": "canonical:requirements:attempt:1",
            "target_step_id": "canonical:design:attempt:1",
            "source_attempt": 1,
            "target_attempt": 1,
        },
        {
            "traversal_id": "canonical:requirements:design:document:2",
            "sequence": 4,
            "source_step_id": "canonical:requirements:attempt:2",
            "target_step_id": "canonical:design:attempt:2",
            "source_attempt": 2,
            "target_attempt": 2,
        },
    ]
    assert trace["final_outputs"][0]["artifact"]["workspace_path"] == (
        "outputs/housing.step"
    )


def test_campaign_trace_projects_recorded_steps_and_sibling_artifacts() -> None:
    record = {
        "schema_version": 1,
        "scenario_id": "printed-replacement-part-01",
        "attempt_id": "attempt-003",
        "run_id": "campaign-run-1",
        "status": "completed",
        "started_at": "2026-09-14T20:00:00Z",
        "finished_at": "2026-09-14T20:00:03Z",
        "definition_digest": "d" * 64,
        "terminal_step_reached": True,
        "all_required_steps_succeeded": True,
        "required_step_ids": ["create_mesh_t" + "a" * 24, "inspect_mesh"],
        "completed_step_ids": ["create_mesh_t" + "a" * 24, "inspect_mesh"],
        "produced_files": [
            {
                "artifact_id": "mesh-v1",
                "path": "models/part.stl",
                "workspace_path": "old-host/path/part.stl",
                "sha256": "e" * 64,
                "size_bytes": 42,
                "task_id": "create_mesh_t" + "a" * 24,
                "artifact_role": "deliverable",
            },
            {
                "artifact_id": "report-v1",
                "path": "reports/inspection-report.md",
                "sha256": "f" * 64,
                "size_bytes": 84,
                "task_id": "inspect_mesh",
                "artifact_role": "verification_report",
            },
        ],
        "step_events": [
            {
                "kind": "step_started",
                "at": "2026-09-14T20:00:00Z",
                "task_id": "create_mesh_t" + "a" * 24,
            },
            {
                "kind": "step_completed",
                "at": "2026-09-14T20:00:01Z",
                "task_id": "create_mesh_t" + "a" * 24,
            },
            {
                "kind": "step_started",
                "at": "2026-09-14T20:00:01Z",
                "task_id": "inspect_mesh",
            },
            {
                "kind": "step_completed",
                "at": "2026-09-14T20:00:03Z",
                "task_id": "inspect_mesh",
            },
        ],
        "approval_evidence": [{"outcome": "approved"}],
    }

    trace = build_canonical_trace(
        record,
        workspace_id="workspace-1",
        session_id="session-1",
        path="runs/printed/attempt-003/run.json",
    )

    assert trace["run"]["state"] == "succeeded"
    assert trace["run"]["duration_ms"] == 3000
    assert len(trace["graph"]["connections"]) == 1
    assert trace["graph"]["connections"][0] | {"connection_id": "ignored"} == {
        "connection_id": "ignored",
        "source_node_id": "create_mesh_t" + "a" * 24,
        "target_node_id": "inspect_mesh",
        "label": "Next recorded activity",
        "basis": "recorded_execution_order",
        "traversals": [],
    }
    assert trace["graph"]["nodes"][0]["label"] == "Create mesh"
    assert [step["state"] for step in trace["steps"]] == [
        "succeeded",
        "succeeded",
    ]
    assert trace["steps"][0]["duration_ms"] == 1000
    assert trace["completeness"]["outputs_complete"] is True
    assert trace["completeness"]["evidence_available"] is True
    assert trace["final_outputs"][0]["name"] == "reports/inspection-report.md"
    artifacts = canonical_artifact_paths(trace)
    assert [artifact["artifact_id"] for artifact in artifacts] == [
        "report-v1",
        "mesh-v1",
    ]
    assert {artifact["workspace_path"] for artifact in artifacts} == {
        "runs/printed/attempt-003/artifacts/models/part.stl",
        "runs/printed/attempt-003/artifacts/reports/inspection-report.md",
    }


def test_campaign_trace_preserves_repeated_step_occurrences() -> None:
    task_id = "repair_mesh"
    record = {
        "schema_version": 1,
        "scenario_id": "printed-replacement-part-03",
        "attempt_id": "attempt-016",
        "run_id": "campaign-run-2",
        "status": "failed",
        "started_at": "2026-09-14T20:00:00Z",
        "finished_at": "2026-09-14T20:00:04Z",
        "definition_digest": "d" * 64,
        "required_step_ids": [task_id],
        "completed_step_ids": [],
        "all_required_steps_succeeded": False,
        "produced_files": [],
        "step_events": [
            {"kind": "step_started", "at": "2026-09-14T20:00:00Z", "task_id": task_id},
            {
                "kind": "step_completed",
                "at": "2026-09-14T20:00:01Z",
                "task_id": task_id,
            },
            {"kind": "step_started", "at": "2026-09-14T20:00:02Z", "task_id": task_id},
        ],
        "error_code": "repair_failed",
        "error": "The retained repair operation failed.",
    }

    trace = build_canonical_trace(
        record,
        workspace_id="workspace-1",
        session_id="session-1",
        path="runs/printed/attempt-016/run.json",
    )

    assert [step["attempt"] for step in trace["steps"]] == [1, 2]
    assert [step["state"] for step in trace["steps"]] == ["succeeded", "failed"]
    assert trace["diagnostic"]["failed_step_id"] == "campaign:repair_mesh:attempt:2"
    assert trace["diagnostic"]["summary"] == "The retained repair operation failed."
