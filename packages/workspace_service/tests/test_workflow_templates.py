from __future__ import annotations

import re

import pytest
import yaml

from workspace_service.workflow_catalog import (
    WorkflowTemplateCatalog,
    WorkflowTemplateError,
)


_NODE_ID = re.compile(r"^\[([^\]]+)\]")


def _project_ids(project_text: str) -> tuple[str, set[str], set[str]]:
    project = yaml.safe_load(project_text)
    data = project["data"]
    graph_ids = set(data["graphs"])
    node_ids = {
        _NODE_ID.match(key).group(1)
        for graph in data["graphs"].values()
        for key in graph["nodes"]
    }
    return data["metadata"]["id"], graph_ids, node_ids


def test_catalog_exposes_reviewed_templates_in_ui_order() -> None:
    catalog = WorkflowTemplateCatalog()

    assert [template.template_id for template in catalog.list()] == [
        "basic-flow",
        "ai-agent",
        "mcp-agent",
        "text-rpg",
    ]
    assert catalog.list()[0].requirements == ()
    assert "mcp-server-configuration" in catalog.list()[2].requirements


@pytest.mark.parametrize(
    "template_id", ["basic-flow", "ai-agent", "mcp-agent", "text-rpg"]
)
def test_each_template_instantiates_as_a_version_four_project(template_id: str) -> None:
    project = yaml.safe_load(WorkflowTemplateCatalog().instantiate(template_id))

    assert project["version"] == 4
    assert project["data"]["graphs"]
    assert project["data"]["metadata"]["title"]


def test_instantiation_replaces_project_graph_node_and_connection_ids() -> None:
    catalog = WorkflowTemplateCatalog()
    projects = [catalog.instantiate("basic-flow") for _ in range(100)]
    identities = [_project_ids(project) for project in projects]

    assert len({project_id for project_id, _, _ in identities}) == 100
    graph_ids = [graph_id for _, graphs, _ in identities for graph_id in graphs]
    node_ids = [node_id for _, _, nodes in identities for node_id in nodes]
    assert len(graph_ids) == len(set(graph_ids))
    assert len(node_ids) == len(set(node_ids))

    project = yaml.safe_load(projects[0])
    for graph in project["data"]["graphs"].values():
        graph_node_ids = {_NODE_ID.match(key).group(1) for key in graph["nodes"]}
        for node in graph["nodes"].values():
            for connection in node.get("outgoingConnections", []):
                target = connection.rsplit(" ", 1)[-1].split("/", 1)[0]
                assert target in graph_node_ids


def test_unknown_template_is_rejected() -> None:
    with pytest.raises(WorkflowTemplateError, match="not found"):
        WorkflowTemplateCatalog().instantiate("missing")
