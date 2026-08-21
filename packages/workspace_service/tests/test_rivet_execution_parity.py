from __future__ import annotations

import asyncio
import os
import shutil
import sqlite3
import time

import pytest
from core.workflow_runs import WorkflowRunState
from data_vault import (
    WorkflowReview,
    WorkflowReviewRepository,
    WorkflowRunRepository,
    upgrade_database,
)

from workspace_service.rivet_mcp import RivetMcpBinding, create_bound_rivet_service
from workspace_service.rivet_runtime_host import RivetRuntimeHost
from workspace_service.surfaces.process_supervisor import ProcessSupervisor
from workspace_service.workflow_operations import (
    WorkflowOperationsSettings,
    WorkspaceWorkflowOperations,
)
from workspace_service.workflow_runner import RunnerSettings, WorkspaceWorkflowRunner


def _supervisor() -> ProcessSupervisor:
    if os.name == "nt":
        from workspace_service.surfaces.process_windows import WindowsProcessAdapter

        adapter = WindowsProcessAdapter()
    else:
        from workspace_service.surfaces.process_posix import PosixProcessAdapter

        adapter = PosixProcessAdapter()
    return ProcessSupervisor(adapter=adapter)


async def _wait_for_terminal(
    operations: WorkspaceWorkflowOperations,
    *,
    run_id: str,
) -> None:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        run = operations.run(workspace_id="w1", session_id="s1", run_id=run_id)
        if run.state in {
            WorkflowRunState.CANCELLED,
            WorkflowRunState.FAILED,
            WorkflowRunState.SUCCEEDED,
        }:
            return
        await asyncio.sleep(0.02)
    raise AssertionError("Canvas workflow run did not reach a terminal state")


@pytest.mark.asyncio
@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")
async def test_mcp_and_canvas_execute_the_same_revision_with_identical_output(
    tmp_path,
) -> None:
    database = tmp_path / "state.db"
    upgrade_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('w1', 's1', ?, 1, 1)""",
            (str(tmp_path),),
        )

    binding = RivetMcpBinding(str(tmp_path), str(database), "w1", "s1")
    mcp_service = create_bound_rivet_service(binding)
    created = await mcp_service.dispatch(
        "create_workflow", {"slug": "parity", "templateId": "basic-flow"}
    )
    identity = created["workflow"]
    review = WorkflowReview(
        "w1",
        identity["workflowId"],
        identity["revision"],
        "approved",
        "parity-test",
        int(time.time()),
    )
    mcp_service.reviews.set(review)
    run_arguments = {
        "slug": "parity",
        "expectedRevision": identity["revision"],
        "expectedDigest": identity["digest"],
        "graph": "Passthrough",
        "inputs": {"input": "identical result"},
    }
    mcp_result = await mcp_service.dispatch("run_workflow", run_arguments)
    assert mcp_result["state"] == "succeeded", mcp_result

    settings = RunnerSettings(enabled=True, real_execution_enabled=True)
    supervisor = _supervisor()
    repository = WorkflowRunRepository(str(database))
    canvas_runner = WorkspaceWorkflowRunner(
        supervisor=supervisor,
        settings=settings,
        runtime_host=RivetRuntimeHost(supervisor=supervisor, settings=settings),
        run_repository=repository,
    )
    operations = WorkspaceWorkflowOperations(
        WorkflowReviewRepository(str(database)),
        canvas_runner,
        settings=WorkflowOperationsSettings(enabled=True),
    )
    canvas_run = await operations.start(
        workspace_id="w1",
        session_id="s1",
        workspace_dir=str(tmp_path),
        slug="parity",
        expected_revision=identity["revision"],
        expected_digest=identity["digest"],
        graph="Passthrough",
        inputs={"input": "identical result"},
    )
    await _wait_for_terminal(operations, run_id=canvas_run.run_id)
    canvas_result = canvas_runner.result(canvas_run.run_id)

    assert canvas_result is not None
    assert canvas_result.state == "succeeded"
    assert canvas_result.revision == identity["revision"]
    assert canvas_result.digest == identity["digest"]
    assert canvas_result.output_summary is not None
    assert canvas_result.output_summary["outputs"] == mcp_result["outputs"]
