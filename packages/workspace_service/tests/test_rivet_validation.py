from __future__ import annotations

from importlib.resources import files

import pytest

from workspace_service.rivet_validation import (
    WorkflowIdentityMismatch,
    extract_rivet_mcp_requirements,
    validate_rivet_project,
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
