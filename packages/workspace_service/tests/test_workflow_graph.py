from __future__ import annotations

import pytest

from data_vault import WorkflowRepository
from workspace_service.executor import BoundedExecutor
from workspace_service.use_cases.workflows import WorkspaceWorkflowUseCases
from workspace_service.workflow_graph import (
    WorkflowGraphError,
    WorkspaceWorkflowGraphOperations,
)


PROJECT = """version: 4
data:
  graphs:
    main:
      metadata:
        id: main
        name: Main
      nodes:
        '[graph-input]:graphInput "Input"':
          data:
            id: value
          outgoingConnections: []
          visualData: 0/0/180/0
  metadata:
    id: project
    title: Fixture
    mainGraphId: main
"""

TERMINAL_PROJECT = """version: 4
data:
  graphs:
    main:
      metadata:
        id: main
        name: Main
      nodes:
        '[graph-output]:graphOutput "Output"':
          data:
            id: result
            dataType: string
          visualData: 220/0/180/0
  metadata:
    id: project
    title: Fixture
    mainGraphId: main
"""


@pytest.mark.asyncio
async def test_graph_operations_save_workspace_revision(tmp_path) -> None:
    executor = BoundedExecutor()
    workflows = WorkspaceWorkflowUseCases(
        executor, WorkflowRepository(str(tmp_path / "state.db"))
    )
    graph = WorkspaceWorkflowGraphOperations(workflows)
    try:
        created = await workflows.create("workspace-a", str(tmp_path), "flow", PROJECT)

        result = await graph.apply(
            workspace_id="workspace-a",
            workspace_dir=str(tmp_path),
            slug="flow",
            expected_revision=created.revision,
            action="add_node",
            arguments={
                "node_id": '[graph-output]:graphOutput "Output"',
                "data": {"id": "result", "dataType": "string"},
            },
        )

        assert result.document.revision == 2
        assert len(result.graph.nodes) == 2
        saved = await workflows.read(str(tmp_path), "flow")
        assert "graphOutput" in saved.project
        assert (tmp_path / "workflows" / "flow" / "workflow.rivet-project").is_file()
    finally:
        await executor.close()


@pytest.mark.asyncio
async def test_graph_edit_rejects_invalid_shape_without_saving(tmp_path) -> None:
    executor = BoundedExecutor()
    workflows = WorkspaceWorkflowUseCases(
        executor, WorkflowRepository(str(tmp_path / "state.db"))
    )
    graph = WorkspaceWorkflowGraphOperations(workflows)
    try:
        created = await workflows.create("workspace-a", str(tmp_path), "flow", PROJECT)

        with pytest.raises(WorkflowGraphError, match="Node was not found"):
            await graph.apply(
                workspace_id="workspace-a",
                workspace_dir=str(tmp_path),
                slug="flow",
                expected_revision=created.revision,
                action="edit_node",
                arguments={"node_id": "missing", "data": {"id": "changed"}},
            )

        assert (await workflows.read(str(tmp_path), "flow")).revision == 1
    finally:
        await executor.close()


@pytest.mark.asyncio
async def test_graph_lint_accepts_terminal_node_without_outgoing_connections(
    tmp_path,
) -> None:
    executor = BoundedExecutor()
    workflows = WorkspaceWorkflowUseCases(
        executor, WorkflowRepository(str(tmp_path / "state.db"))
    )
    graph = WorkspaceWorkflowGraphOperations(workflows)
    try:
        await workflows.create(
            "workspace-a", str(tmp_path), "flow", TERMINAL_PROJECT
        )

        result = await graph.lint(workspace_dir=str(tmp_path), slug="flow")

        output = next(node for node in result.graph.nodes if node.node_type == "graphOutput")
        assert output.outgoing_connections == ()
        assert result.issues == ()
    finally:
        await executor.close()
