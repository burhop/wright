from __future__ import annotations

from types import SimpleNamespace

import pytest
from data_vault import WorkflowReviewRepository
from tool_registry.gateway_models import GatewayTool
from workspace_service.rivet_capabilities import RivetCapabilityService
from workspace_service.rivet_settings import RivetMcpGatewaySettings
from workspace_service.rivet_validation import extract_rivet_mcp_requirements
from workspace_service.workflow_operations import (
    WorkflowOperationsError,
    WorkflowOperationsSettings,
    WorkspaceWorkflowOperations,
)
from workspace_service.workflows import WorkspaceWorkflowStore


def test_selected_graph_extracts_only_static_tool_bindings():
    project = """
version: 4
data:
  graphs:
    graph-a:
      metadata: {id: graph-a, name: Main}
      nodes:
        '[discover]:mcpDiscovery "Discover"':
          data: {useToolsOutput: true, usePromptsOutput: false}
        '[alpha]:mcpToolCall "Alpha"':
          data: {toolName: alpha__inspect, useToolNameInput: false}
    graph-b:
      metadata: {id: graph-b, name: Other}
      nodes:
        '[beta]:mcpToolCall "Beta"':
          data: {toolName: beta__inspect, useToolNameInput: false}
  metadata: {mainGraphId: graph-a}
"""
    result = extract_rivet_mcp_requirements(project, selected_graph="Main")
    assert result.errors == ()
    assert [(item.node_id, item.static_tool_name) for item in result.nodes] == [
        ("alpha", "alpha__inspect"),
        ("discover", None),
    ]


def test_prohibited_mcp_authority_and_prompt_operations_fail_closed():
    project = """
version: 4
data:
  graphs:
    graph:
      metadata: {id: graph, name: Main}
      nodes:
        '[discover]:mcpDiscovery "Discover"':
          data: {usePromptsOutput: true, serverId: direct-child}
        '[call]:mcpToolCall "Call"':
          data:
            toolName: inspect
            useToolNameInput: true
            authorization: Bearer forbidden
        '[prompt]:mcpGetPrompt "Prompt"': {data: {}}
  metadata:
    mainGraphId: graph
    mcpServer: {mcpServers: {direct-child: {command: child}}}
"""
    result = extract_rivet_mcp_requirements(project, selected_graph="Main")
    assert {issue.code for issue in result.errors} == {
        "RIVET_MCP_PROJECT_CONFIG_DENIED",
        "RIVET_MCP_PROMPT_DENIED",
        "RIVET_MCP_DYNAMIC_TOOL_DENIED",
    }


def test_duplicate_mcp_node_identity_is_rejected():
    project = """
version: 4
data:
  graphs:
    graph:
      metadata: {id: graph, name: Main}
      nodes:
        - {id: duplicate, type: mcpToolCall, data: {toolName: alpha__inspect}}
        - {id: duplicate, type: mcpToolCall, data: {toolName: beta__inspect}}
  metadata: {mainGraphId: graph}
"""
    result = extract_rivet_mcp_requirements(project, selected_graph="graph")
    assert "RIVET_MCP_DUPLICATE_NODE" in {item.code for item in result.errors}


def test_static_exact_binding_requirement_has_no_child_configuration():
    project = """
version: 4
data:
  graphs:
    graph:
      metadata: {id: graph, name: Main}
      nodes:
        '[call]:mcpToolCall "Call"':
          data: {toolName: alpha__inspect, useToolNameInput: false}
  metadata: {mainGraphId: graph}
"""
    result = extract_rivet_mcp_requirements(project, selected_graph="graph")
    assert result.errors == ()
    assert result.nodes[0].static_tool_name == "alpha__inspect"


class _Gateway:
    def __init__(self) -> None:
        self.child_receipts = 0
        self.tools = (
            GatewayTool(
                "alpha__inspect",
                "alpha",
                "inspect",
                "Alpha inspect",
                {"type": "object"},
                output_schema={"type": "object"},
                annotations={"readOnlyHint": True},
                provenance={
                    "server_revision": "alpha-v1",
                    "validation_evidence_id": "alpha-validation",
                },
            ),
            GatewayTool(
                "beta__inspect",
                "beta",
                "inspect",
                "Beta inspect",
                {"type": "object"},
                output_schema={"type": "object"},
                required_approvals=frozenset({"engineering.write"}),
                provenance={
                    "server_revision": "beta-v1",
                    "validation_evidence_id": "beta-validation",
                },
            ),
        )

    def list_tools(self, session_id: str):
        assert session_id == "session-a"
        return self.tools


class _BindingRepository:
    def __init__(self) -> None:
        self.by_digest = {}

    def save_binding_set(self, binding_set) -> None:
        self.by_digest[binding_set.binding_set_digest] = binding_set

    def get_binding_set_by_digest(self, digest: str):
        return self.by_digest.get(digest)


def _mcp_operations(tmp_path, gateway: _Gateway):
    project = """
version: 4
data:
  graphs:
    graph:
      metadata: {id: graph, name: Main}
      nodes:
        '[call]:mcpToolCall "Inspect"':
          data: {toolName: inspect, useToolNameInput: false}
  metadata: {id: project, title: Test, description: '', mainGraphId: graph}
  plugins: []
"""
    document = WorkspaceWorkflowStore(str(tmp_path)).create("mcp-flow", project)
    reviews = WorkflowReviewRepository(str(tmp_path / "state.db"))
    repository = _BindingRepository()
    operations = WorkspaceWorkflowOperations(
        reviews,
        SimpleNamespace(start=lambda **kwargs: None),
        settings=WorkflowOperationsSettings(enabled=True),
    )
    operations.configure_mcp(
        capabilities=RivetCapabilityService(gateway),
        repository=repository,  # type: ignore[arg-type]
        settings=RivetMcpGatewaySettings(enabled=True),
    )
    return operations, document, repository


@pytest.mark.asyncio
async def test_binding_preview_requires_exact_namespaced_resolution_and_starts_no_child(
    tmp_path,
):
    gateway = _Gateway()
    operations, document, _repository = _mcp_operations(tmp_path, gateway)
    ambiguous = await operations.preview_mcp_bindings(
        workspace_id="workspace-a",
        session_id="session-a",
        workspace_dir=str(tmp_path),
        slug="mcp-flow",
        expected_revision=document.revision,
        expected_digest=document.digest,
        graph="Main",
        selections={},
    )
    assert ambiguous.binding_set is None
    assert ambiguous.nodes[0].blockers == ("binding_ambiguous",)
    exact = await operations.preview_mcp_bindings(
        workspace_id="workspace-a",
        session_id="session-a",
        workspace_dir=str(tmp_path),
        slug="mcp-flow",
        expected_revision=document.revision,
        expected_digest=document.digest,
        graph="Main",
        selections={"call": "alpha__inspect"},
        units_policy={"call": {"length": "mm"}},
    )
    assert exact.binding_set is not None
    assert exact.nodes[0].binding.qualified_tool_name == "alpha__inspect"
    assert exact.nodes[0].binding.units_policy == {"length": "mm"}
    assert gateway.child_receipts == 0


@pytest.mark.asyncio
async def test_exact_review_rejects_cross_workspace_and_current_schema_change(tmp_path):
    gateway = _Gateway()
    operations, document, _repository = _mcp_operations(tmp_path, gateway)
    preview = await operations.preview_mcp_bindings(
        workspace_id="workspace-a",
        session_id="session-a",
        workspace_dir=str(tmp_path),
        slug="mcp-flow",
        expected_revision=document.revision,
        expected_digest=document.digest,
        graph="Main",
        selections={"call": "alpha__inspect"},
    )
    assert preview.binding_set is not None
    with pytest.raises(WorkflowOperationsError, match="stale"):
        await operations.review(
            workspace_id="workspace-b",
            session_id="session-a",
            workspace_dir=str(tmp_path),
            slug="mcp-flow",
            state="approved",
            reviewer="engineer",
            expected_digest=document.digest,
            graph="Main",
            binding_set_digest=preview.binding_set.binding_set_digest,
        )
    reviewed = await operations.review(
        workspace_id="workspace-a",
        session_id="session-a",
        workspace_dir=str(tmp_path),
        slug="mcp-flow",
        state="approved",
        reviewer="engineer",
        expected_digest=document.digest,
        graph="Main",
        binding_set_digest=preview.binding_set.binding_set_digest,
    )
    assert reviewed.review.review_digest
    gateway.tools = (
        GatewayTool(
            "alpha__inspect",
            "alpha",
            "inspect",
            "Changed",
            {"type": "object", "properties": {"changed": {"type": "boolean"}}},
            provenance={
                "server_revision": "alpha-v1",
                "validation_evidence_id": "alpha-validation",
            },
        ),
    )
    detail = await operations.detail(
        workspace_id="workspace-a",
        session_id="session-a",
        workspace_dir=str(tmp_path),
        slug="mcp-flow",
    )
    assert "tool_schema_changed" in detail.stale_reasons
