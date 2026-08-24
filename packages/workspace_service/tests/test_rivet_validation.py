from __future__ import annotations

from importlib.resources import files
from datetime import UTC, datetime

import pytest
from core.rivet_mcp import CapabilityBinding, canonical_digest

from workspace_service.rivet_validation import (
    WorkflowIdentityMismatch,
    extract_rivet_mcp_requirements,
    project_graph_inventory,
    validate_rivet_project,
    validate_requested_deliverable_effect,
)


def _template(name: str) -> str:
    return (
        files("workspace_service.workflow_catalog")
        .joinpath(f"templates/{name}.rivet-project")
        .read_text(encoding="utf-8")
    )


def test_validation_summarizes_graphs_ports_and_main_graph():
    project = _template("ai-agent")
    result = validate_rivet_project(
        project,
        workflow_id="workflow-1",
        revision=2,
        digest="b" * 64,
    )

    assert result.valid
    assert result.workflow_id == "workflow-1"
    assert result.revision == 2
    assert result.main_graph is not None
    assert result.main_graph.id
    assert result.main_graph.name
    assert result.graphs
    assert "ai" in result.requirements


def test_validation_reports_missing_main_and_selected_graph():
    without_main = validate_rivet_project(
        _template("basic-flow"),
        workflow_id="workflow-1",
        revision=1,
        digest="c" * 64,
    )
    assert not without_main.valid
    assert {issue.code for issue in without_main.errors} == {"RIVET_MAIN_GRAPH_MISSING"}

    selected = validate_rivet_project(
        _template("basic-flow"),
        workflow_id="workflow-1",
        revision=1,
        digest="c" * 64,
        selected_graph="Passthrough",
    )
    assert selected.valid
    assert selected.main_graph.name == "Passthrough"
    assert [port.id for port in selected.main_graph.inputs] == ["input"]
    assert [port.id for port in selected.main_graph.outputs] == ["output"]
    assert selected.requirements == ()

    inventory, complete = project_graph_inventory(
        _template("basic-flow"), selected_graph=selected.main_graph.id
    )
    assert complete is True
    assert [item["label"] for item in inventory] == [
        "Graph Output",
        "Graph Input",
    ]
    assert [item["node_type"] for item in inventory] == [
        "graphOutput",
        "graphInput",
    ]


def test_validation_handles_malformed_projects_and_bounds_issues():
    malformed = validate_rivet_project(
        "not: [valid",
        workflow_id="workflow-1",
        revision=1,
        digest="d" * 64,
    )
    assert not malformed.valid
    assert malformed.errors[0].code == "RIVET_PROJECT_PARSE_FAILED"
    assert len(malformed.errors[0].message) <= 256


def test_validation_rejects_stale_identity_before_parse():
    with pytest.raises(WorkflowIdentityMismatch):
        validate_rivet_project(
            _template("basic-flow"),
            workflow_id="workflow-1",
            revision=2,
            digest="e" * 64,
            expected_revision=1,
            expected_digest="e" * 64,
        )


def test_mcp_requirement_extraction_rejects_child_config_dynamic_tools_and_prompts():
    project = """
version: 4
data:
  graphs:
    graph:
      metadata: {id: graph, name: Main}
      nodes:
        '[discovery]:mcpDiscovery "Discover"':
          data: {serverUrl: 'http://child.invalid/mcp', usePromptsOutput: true}
        '[call]:mcpToolCall "Call"':
          data: {toolName: inspect, useToolNameInput: true}
        '[prompt]:mcpGetPrompt "Prompt"':
          data: {}
  metadata:
    mainGraphId: graph
    mcpServer: {mcpServers: {unsafe: {command: node}}}
"""
    result = extract_rivet_mcp_requirements(project, selected_graph="Main")
    assert [item.node_id for item in result.nodes] == ["call", "discovery"]
    assert {item.code for item in result.errors} == {
        "RIVET_MCP_PROJECT_CONFIG_DENIED",
        "RIVET_MCP_PROMPT_DENIED",
        "RIVET_MCP_DYNAMIC_TOOL_DENIED",
    }


def test_mcp_requirement_extraction_accepts_static_wright_bound_nodes():
    project = """
version: 4
data:
  graphs:
    graph:
      metadata: {id: graph, name: Main}
      nodes:
        '[discovery]:mcpDiscovery "Discover"':
          data: {usePromptsOutput: false, useToolsOutput: true}
        '[call]:mcpToolCall "Call"':
          data: {toolName: alpha__inspect, useToolNameInput: false}
  metadata: {mainGraphId: graph}
"""
    result = extract_rivet_mcp_requirements(project, selected_graph="Main")
    assert result.errors == ()
    assert [item.static_tool_name for item in result.nodes] == [
        "alpha__inspect",
        None,
    ]


def _document_project(
    *,
    connect_output: bool = True,
    tool: str = "wright-workspace-files__write_text_document",
) -> str:
    connection = (
        """
      connections:
        - {outputNodeId: writer, outputId: result, inputNodeId: output, inputId: value}
"""
        if connect_output
        else "      connections: []\n"
    )
    return f"""
version: 4
data:
  graphs:
    graph:
      metadata: {{id: graph, name: Main}}
      nodes:
        '[writer]:mcpToolCall "Create workspace document"':
          data:
            toolName: {tool}
            useToolNameInput: false
            useToolArgumentsInput: false
            toolArguments: '{{"relativePath":"reports/review.md","content":"review","mediaType":"text/markdown","overwrite":false}}'
        '[output]:graphOutput "Graph Output"':
          data: {{id: artifact, dataType: any}}
{connection}  metadata:
    mainGraphId: graph
    wrightRequestedDeliverable:
      kind: workspace_document
      label: Design review
      suggestedRelativePath: reports/review.md
      confirmedAt: '2026-08-21T20:00:00Z'
      confirmationRevision: 0
"""


def _document_binding() -> CapabilityBinding:
    declaration = {
        "effect_kind": "workspace_document",
        "artifact_output": True,
        "native_format": False,
        "required_approvals": ["workspace_write_approval"],
    }
    return CapabilityBinding.build(
        binding_id="binding-document",
        workspace_id="workspace-1",
        workflow_id="workflow-1",
        workflow_revision=1,
        workflow_digest="a" * 64,
        graph_id="graph",
        node_id="writer",
        node_handle="wright:abcdefghijklmnop",
        requirement_id=None,
        qualified_tool_name="wright-workspace-files__write_text_document",
        server_id="wright-workspace-files",
        server_revision="v1",
        capability_digest="b" * 64,
        validation_evidence_id="reviewed-document-v1",
        workspace_grant_digest="c" * 64,
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        risk={"required_approvals": ["workspace_write_approval"]},
        units_policy={},
        material_defaults={},
        argument_constraints={"type": "object"},
        created_at=datetime.now(UTC),
        artifact_producer=declaration,
        artifact_producer_digest=canonical_digest(declaration),
    )


def test_document_deliverable_requires_exact_producer_output_and_reviewed_binding():
    project = _document_project()

    assert validate_requested_deliverable_effect(project) == ()
    assert (
        validate_requested_deliverable_effect(
            project,
            bindings=(_document_binding(),),
            require_reviewed_binding=True,
        )
        == ()
    )
    assert validate_rivet_project(
        project,
        workflow_id="workflow-1",
        revision=1,
        digest="a" * 64,
    ).valid


def test_document_deliverable_rejects_missing_dependency_and_value_only_tool_substitute():
    disconnected = validate_requested_deliverable_effect(
        _document_project(connect_output=False)
    )
    assert {issue.code for issue in disconnected} == {
        "RIVET_DELIVERABLE_OUTPUT_REQUIRED"
    }
    wrong_tool = validate_requested_deliverable_effect(
        _document_project(tool="other__return_path")
    )
    assert wrong_tool[0].code == "RIVET_DELIVERABLE_PRODUCER_REQUIRED"


def test_native_deliverable_rejects_writer_without_matching_producer_declaration():
    project = (
        _document_project()
        .replace("kind: workspace_document", "kind: native_cad")
        .replace("      suggestedRelativePath: reports/review.md\n", "")
    )
    issues = validate_requested_deliverable_effect(
        project,
        bindings=(_document_binding(),),
        require_reviewed_binding=True,
    )
    assert issues[0].code == "RIVET_DELIVERABLE_PRODUCER_REQUIRED"
    assert "artifact-producing MCP tool" in issues[0].message
