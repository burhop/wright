from __future__ import annotations

import pytest
import yaml

from data_vault import WorkflowRepository
from workspace_service.executor import BoundedExecutor
from workspace_service.use_cases.workflows import WorkspaceWorkflowUseCases
from workspace_service.workflow_graph import (
    WorkflowGraphError,
    WorkspaceWorkflowGraphOperations,
    lint_project,
)
from workspace_service.rivet_project import normalize_graph_output_ids


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

INCOMPLETE_MCP_PROJECT = """version: 4
data:
  graphs:
    main:
      metadata:
        id: main
        name: Main
      nodes:
        '[mcp-call]:mcpToolCall "MCP Tool Call"':
          data:
            serverId: ''
            toolName: ''
            useToolNameInput: true
            useToolArgumentsInput: true
          outgoingConnections: []
          visualData: 0/0/250/0
  metadata:
    id: project
    title: MCP Fixture
    mainGraphId: main
"""

DUPLICATE_OUTPUT_PROJECT = """version: 4
data:
  graphs:
    main:
      metadata:
        id: main
        name: Main
      nodes:
        '[output-a]:graphOutput "First"':
          data:
            id: output
            dataType: object
        '[output-b]:graphOutput "Second"':
          data:
            id: output
            dataType: object
  metadata:
    id: project
    title: Duplicate outputs
    mainGraphId: main
"""


def test_graph_output_ids_are_normalized_before_editor_save() -> None:
    original = yaml.safe_load(DUPLICATE_OUTPUT_PROJECT)
    assert {issue.get("code") for issue in lint_project(original)} == {
        "RIVET_GRAPH_OUTPUT_ID_DUPLICATE"
    }

    normalized_text = normalize_graph_output_ids(DUPLICATE_OUTPUT_PROJECT)
    normalized = yaml.safe_load(normalized_text)
    nodes = normalized["data"]["graphs"]["main"]["nodes"]

    assert [node["data"]["id"] for node in nodes.values()] == ["output", "output_2"]
    assert lint_project(normalized) == ()
    assert normalized_text.count("dataType: object") == 2


@pytest.mark.asyncio
async def test_workflow_save_persists_unique_graph_output_ids(tmp_path) -> None:
    executor = BoundedExecutor()
    workflows = WorkspaceWorkflowUseCases(
        executor, WorkflowRepository(str(tmp_path / "state.db"))
    )
    try:
        created = await workflows.create(
            "workspace-a", str(tmp_path), "flow", DUPLICATE_OUTPUT_PROJECT
        )

        saved = await workflows.save(
            "workspace-a",
            str(tmp_path),
            "flow",
            created.revision,
            DUPLICATE_OUTPUT_PROJECT,
        )

        nodes = yaml.safe_load(saved.project)["data"]["graphs"]["main"]["nodes"]
        assert [node["data"]["id"] for node in nodes.values()] == [
            "output",
            "output_2",
        ]
    finally:
        await executor.close()


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
        await workflows.create("workspace-a", str(tmp_path), "flow", TERMINAL_PROJECT)

        result = await graph.lint(workspace_dir=str(tmp_path), slug="flow")

        output = next(
            node for node in result.graph.nodes if node.node_type == "graphOutput"
        )
        assert output.outgoing_connections == ()
        assert result.issues == ()
    finally:
        await executor.close()


@pytest.mark.asyncio
async def test_graph_lint_rejects_an_unbound_dynamic_mcp_tool(tmp_path) -> None:
    executor = BoundedExecutor()
    workflows = WorkspaceWorkflowUseCases(
        executor, WorkflowRepository(str(tmp_path / "state.db"))
    )
    graph = WorkspaceWorkflowGraphOperations(workflows)
    try:
        await workflows.create(
            "workspace-a", str(tmp_path), "flow", INCOMPLETE_MCP_PROJECT
        )

        result = await graph.lint(workspace_dir=str(tmp_path), slug="flow")

        assert {issue.get("code") for issue in result.issues} == {
            "RIVET_MCP_DYNAMIC_TOOL_DENIED",
            "RIVET_MCP_TOOL_REQUIRED",
        }
    finally:
        await executor.close()
