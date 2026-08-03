from __future__ import annotations

import os
import shutil
import time

import pytest

from core.workflow_runs import WorkflowRunState
from workspace_service.surfaces.process_supervisor import ProcessSupervisor
from workspace_service.workflow_runner import RunnerSettings, WorkspaceWorkflowRunner
from workspace_service.workflows import WorkspaceWorkflowStore


@pytest.mark.asyncio
@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")
async def test_fixture_runner_cancels_owned_node_process_within_deadline(tmp_path):
    if os.name == "nt":
        from workspace_service.surfaces.process_windows import WindowsProcessAdapter

        adapter = WindowsProcessAdapter()
    else:
        from workspace_service.surfaces.process_posix import PosixProcessAdapter

        adapter = PosixProcessAdapter()
    fixture = tmp_path / "fixture.mjs"
    fixture.write_text(
        "setTimeout(() => process.exit(0), 60000);",
        encoding="utf-8",
    )
    WorkspaceWorkflowStore(str(tmp_path)).create("fixture", '{"nodes": []}')
    runner = WorkspaceWorkflowRunner(
        supervisor=ProcessSupervisor(adapter=adapter),
        settings=RunnerSettings(enabled=True, cancellation_seconds=2.0),
        fixture_path=fixture,
    )
    run = await runner.start(
        workspace_id="workspace",
        session_id="session",
        workspace_dir=str(tmp_path),
        slug="fixture",
    )
    started_at = time.monotonic()
    cancelled = await runner.cancel(run.run_id, generation=run.generation)
    assert cancelled.state is WorkflowRunState.CANCELLED
    assert time.monotonic() - started_at <= 2.0
