"""Structured graph operations for Wright-owned Rivet project files."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

import yaml

from core.workflows import WorkflowDocument, WorkflowPersistenceError

from .use_cases.workflows import WorkspaceWorkflowUseCases

GraphAction = Literal[
    "add_node",
    "edit_node",
    "delete_node",
    "connect_ports",
    "disconnect_ports",
    "save_revision",
]


class WorkflowGraphError(WorkflowPersistenceError):
    """A safe graph validation or mutation failure."""


@dataclass(frozen=True, slots=True)
class WorkflowGraphNode:
    node_id: str
    node_type: str | None
    title: str | None
    data: Mapping[str, Any]
    outgoing_connections: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkflowGraphSummary:
    graph_id: str
    name: str | None
    main: bool
    nodes: tuple[WorkflowGraphNode, ...]


@dataclass(frozen=True, slots=True)
class WorkflowGraphResult:
    document: WorkflowDocument
    graph: WorkflowGraphSummary
    issues: tuple[Mapping[str, Any], ...] = ()


def _load_project(project: str) -> tuple[dict[str, Any], str]:
    try:
        loaded = json.loads(project)
        if not isinstance(loaded, dict):
            raise WorkflowGraphError("Rivet project root must be an object")
        return loaded, "json"
    except json.JSONDecodeError:
        pass
    try:
        loaded = yaml.safe_load(project)
    except yaml.YAMLError as error:
        raise WorkflowGraphError("Rivet project is not valid YAML or JSON") from error
    if not isinstance(loaded, dict):
        raise WorkflowGraphError("Rivet project root must be an object")
    return loaded, "yaml"


def _dump_project(project: Mapping[str, Any], original_format: str) -> str:
    if original_format == "json":
        return json.dumps(project, indent=2, sort_keys=True) + "\n"
    return yaml.safe_dump(dict(project), sort_keys=False, allow_unicode=False)


def _graphs(project: Mapping[str, Any]) -> dict[str, Any]:
    data = project.get("data")
    if not isinstance(data, dict):
        raise WorkflowGraphError("Rivet project is missing data")
    graphs = data.get("graphs")
    if not isinstance(graphs, dict) or not graphs:
        raise WorkflowGraphError("Rivet project has no graphs")
    return graphs


def _main_graph_id(project: Mapping[str, Any], graph_id: str | None) -> str:
    graphs = _graphs(project)
    if graph_id:
        if graph_id not in graphs:
            raise WorkflowGraphError("Requested graph was not found")
        return graph_id
    metadata = project.get("data", {}).get("metadata")  # type: ignore[union-attr]
    candidate = metadata.get("mainGraphId") if isinstance(metadata, dict) else None
    if isinstance(candidate, str) and candidate in graphs:
        return candidate
    return next(iter(graphs))


def _graph(
    project: Mapping[str, Any], graph_id: str | None
) -> tuple[str, dict[str, Any]]:
    resolved = _main_graph_id(project, graph_id)
    graph = _graphs(project).get(resolved)
    if not isinstance(graph, dict):
        raise WorkflowGraphError("Rivet graph must be an object")
    nodes = graph.setdefault("nodes", {})
    if not isinstance(nodes, dict):
        raise WorkflowGraphError("Rivet graph nodes must be an object")
    return resolved, graph


def _node_kind(node_id: str) -> str | None:
    if node_id.startswith("[") and "]:" in node_id:
        return node_id.split("]:", 1)[1].split(" ", 1)[0] or None
    return None


def _node_title(node_id: str) -> str | None:
    if '"' not in node_id:
        return None
    parts = node_id.split('"')
    return parts[1] if len(parts) >= 3 else None


def _outgoing_connections(node: object) -> tuple[str, ...]:
    if not isinstance(node, dict):
        return ()
    connections = node.get("outgoingConnections")
    if not isinstance(connections, list):
        return ()
    return tuple(str(item) for item in connections if isinstance(item, str))


def summarize_graph(
    project: Mapping[str, Any], graph_id: str | None = None
) -> WorkflowGraphSummary:
    resolved, graph = _graph(project, graph_id)
    metadata = graph.get("metadata")
    nodes = graph.get("nodes")
    assert isinstance(nodes, dict)
    main_id = _main_graph_id(project, None)
    return WorkflowGraphSummary(
        graph_id=resolved,
        name=(
            str(metadata.get("name"))
            if isinstance(metadata, dict) and metadata.get("name") is not None
            else None
        ),
        main=resolved == main_id,
        nodes=tuple(
            WorkflowGraphNode(
                node_id=str(node_id),
                node_type=_node_kind(str(node_id)),
                title=_node_title(str(node_id)),
                data=(
                    dict(node.get("data"))
                    if isinstance(node, dict) and isinstance(node.get("data"), dict)
                    else {}
                ),
                outgoing_connections=_outgoing_connections(node),
            )
            for node_id, node in nodes.items()
        ),
    )


def lint_project(
    project: Mapping[str, Any], graph_id: str | None = None
) -> tuple[Mapping[str, Any], ...]:
    issues: list[Mapping[str, Any]] = []
    try:
        graphs = _graphs(project)
    except WorkflowGraphError as error:
        return ({"level": "error", "message": str(error)},)
    metadata = project.get("data", {}).get("metadata")  # type: ignore[union-attr]
    main_graph = metadata.get("mainGraphId") if isinstance(metadata, dict) else None
    if isinstance(main_graph, str) and main_graph not in graphs:
        issues.append(
            {
                "level": "error",
                "message": "mainGraphId does not reference an existing graph",
                "graph_id": main_graph,
            }
        )
    target_graphs = [graph_id] if graph_id else list(graphs)
    for current_graph_id in target_graphs:
        graph = graphs.get(current_graph_id)
        if not isinstance(graph, dict):
            issues.append(
                {
                    "level": "error",
                    "message": "Graph must be an object",
                    "graph_id": current_graph_id,
                }
            )
            continue
        nodes = graph.get("nodes")
        if not isinstance(nodes, dict):
            issues.append(
                {
                    "level": "error",
                    "message": "Graph nodes must be an object",
                    "graph_id": current_graph_id,
                }
            )
            continue
        graph_output_ids: dict[str, str] = {}
        for node_id, node in nodes.items():
            if not isinstance(node, dict):
                issues.append(
                    {
                        "level": "error",
                        "message": "Node must be an object",
                        "graph_id": current_graph_id,
                        "node_id": str(node_id),
                    }
                )
                continue
            connections = node.get("outgoingConnections", [])
            if not isinstance(connections, list) or not all(
                isinstance(item, str) for item in connections
            ):
                issues.append(
                    {
                        "level": "error",
                        "message": "Node outgoingConnections must be strings",
                        "graph_id": current_graph_id,
                        "node_id": str(node_id),
                    }
                )
            node_type = str(node.get("type") or _node_kind(str(node_id)) or "")
            if node_type == "graphOutput":
                data = node.get("data")
                data = data if isinstance(data, dict) else {}
                output_id = data.get("id")
                if not isinstance(output_id, str) or not output_id.strip():
                    issues.append(
                        {
                            "level": "error",
                            "code": "RIVET_GRAPH_OUTPUT_ID_REQUIRED",
                            "message": "Give every Graph Output a stable output ID",
                            "graph_id": current_graph_id,
                            "node_id": str(node_id),
                        }
                    )
                elif output_id.strip() in graph_output_ids:
                    issues.append(
                        {
                            "level": "error",
                            "code": "RIVET_GRAPH_OUTPUT_ID_DUPLICATE",
                            "message": (
                                f"Graph Output ID '{output_id.strip()}' is duplicated; "
                                "each visible output must have a unique ID"
                            ),
                            "graph_id": current_graph_id,
                            "node_id": str(node_id),
                            "conflicting_node_id": graph_output_ids[output_id.strip()],
                        }
                    )
                else:
                    graph_output_ids[output_id.strip()] = str(node_id)
            if node_type == "mcpToolCall":
                data = node.get("data")
                data = data if isinstance(data, dict) else {}
                if any(
                    data.get(key) not in (None, "", [], {})
                    for key in (
                        "serverId",
                        "serverUrl",
                        "command",
                        "args",
                        "env",
                        "environment",
                        "headers",
                        "authorization",
                    )
                ):
                    issues.append(
                        {
                            "level": "error",
                            "code": "RIVET_MCP_PROJECT_CONFIG_DENIED",
                            "message": (
                                "Leave MCP connection settings empty; Wright binds "
                                "the workspace tool when the workflow runs"
                            ),
                            "graph_id": current_graph_id,
                            "node_id": str(node_id),
                        }
                    )
                if data.get("useToolNameInput") is not False:
                    issues.append(
                        {
                            "level": "error",
                            "code": "RIVET_MCP_DYNAMIC_TOOL_DENIED",
                            "message": (
                                "Choose one static MCP tool name instead of using "
                                "a dynamic tool-name input"
                            ),
                            "graph_id": current_graph_id,
                            "node_id": str(node_id),
                        }
                    )
                if (
                    not isinstance(data.get("toolName"), str)
                    or not str(data.get("toolName")).strip()
                ):
                    issues.append(
                        {
                            "level": "error",
                            "code": "RIVET_MCP_TOOL_REQUIRED",
                            "message": "Choose the exact workspace MCP tool for this node",
                            "graph_id": current_graph_id,
                            "node_id": str(node_id),
                        }
                    )
    return tuple(issues)


def _require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WorkflowGraphError(f"{label} is required")
    return value


def _connection(arguments: Mapping[str, Any]) -> str:
    direct = arguments.get("connection")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    source_port = _require_string(arguments.get("source_port"), "source_port")
    target = _require_string(arguments.get("target_node_ref"), "target_node_ref")
    target_port = _require_string(arguments.get("target_port"), "target_port")
    return f"{source_port}->{target}/{target_port}"


def mutate_project(
    project: Mapping[str, Any],
    action: GraphAction,
    arguments: Mapping[str, Any],
) -> dict[str, Any]:
    mutable = json.loads(json.dumps(project))
    if action == "save_revision":
        return mutable
    graph_id, graph = _graph(mutable, arguments.get("graph_id"))
    del graph_id
    nodes = graph["nodes"]
    if not isinstance(nodes, dict):
        raise WorkflowGraphError("Rivet graph nodes must be an object")

    if action == "add_node":
        node_id = _require_string(arguments.get("node_id"), "node_id")
        if node_id in nodes:
            raise WorkflowGraphError("Node already exists")
        raw_node = arguments.get("node")
        if raw_node is not None and not isinstance(raw_node, dict):
            raise WorkflowGraphError("node must be an object")
        nodes[node_id] = dict(raw_node or {})
        nodes[node_id].setdefault("data", dict(arguments.get("data") or {}))
        nodes[node_id].setdefault("outgoingConnections", [])
        nodes[node_id].setdefault(
            "visualData", arguments.get("visual_data") or "0/0/180/0"
        )
        return mutable

    if action == "edit_node":
        node_id = _require_string(arguments.get("node_id"), "node_id")
        node = nodes.get(node_id)
        if not isinstance(node, dict):
            raise WorkflowGraphError("Node was not found")
        patch = arguments.get("node_patch") or {}
        data_patch = arguments.get("data") or {}
        if not isinstance(patch, dict) or not isinstance(data_patch, dict):
            raise WorkflowGraphError("node_patch and data must be objects")
        node.update(patch)
        if data_patch:
            data = node.setdefault("data", {})
            if not isinstance(data, dict):
                raise WorkflowGraphError("Node data must be an object")
            data.update(data_patch)
        return mutable

    if action == "delete_node":
        node_id = _require_string(arguments.get("node_id"), "node_id")
        if node_id not in nodes:
            raise WorkflowGraphError("Node was not found")
        del nodes[node_id]
        for node in nodes.values():
            if isinstance(node, dict) and isinstance(
                node.get("outgoingConnections"), list
            ):
                node["outgoingConnections"] = [
                    item
                    for item in node["outgoingConnections"]
                    if isinstance(item, str) and node_id not in item
                ]
        return mutable

    if action == "connect_ports":
        node_id = _require_string(
            arguments.get("source_node_id") or arguments.get("node_id"),
            "source_node_id",
        )
        node = nodes.get(node_id)
        if not isinstance(node, dict):
            raise WorkflowGraphError("Source node was not found")
        connections = node.setdefault("outgoingConnections", [])
        if not isinstance(connections, list):
            raise WorkflowGraphError("Source node outgoingConnections must be a list")
        connection = _connection(arguments)
        if connection not in connections:
            connections.append(connection)
        return mutable

    if action == "disconnect_ports":
        node_id = _require_string(
            arguments.get("source_node_id") or arguments.get("node_id"),
            "source_node_id",
        )
        node = nodes.get(node_id)
        if not isinstance(node, dict):
            raise WorkflowGraphError("Source node was not found")
        connections = node.get("outgoingConnections")
        if not isinstance(connections, list):
            raise WorkflowGraphError("Source node outgoingConnections must be a list")
        connection = arguments.get("connection")
        target = arguments.get("target_node_ref")
        if not connection and not target:
            raise WorkflowGraphError("connection or target_node_ref is required")
        node["outgoingConnections"] = [
            item
            for item in connections
            if not (
                isinstance(item, str)
                and (
                    item == connection
                    or (isinstance(target, str) and target and target in item)
                )
            )
        ]
        return mutable

    raise WorkflowGraphError("Unsupported graph action")


class WorkspaceWorkflowGraphOperations:
    """Graph/project data operations that preserve workflow revision semantics."""

    def __init__(self, workflows: WorkspaceWorkflowUseCases) -> None:
        self._workflows = workflows

    async def inspect(
        self, *, workspace_dir: str, slug: str, graph_id: str | None = None
    ) -> WorkflowGraphResult:
        document = await self._workflows.read(workspace_dir, slug)
        project, _format = _load_project(document.project)
        return WorkflowGraphResult(
            document=document,
            graph=summarize_graph(project, graph_id),
            issues=lint_project(project, graph_id),
        )

    async def lint(
        self, *, workspace_dir: str, slug: str, graph_id: str | None = None
    ) -> WorkflowGraphResult:
        document = await self._workflows.read(workspace_dir, slug)
        project, _format = _load_project(document.project)
        return WorkflowGraphResult(
            document=document,
            graph=summarize_graph(project, graph_id),
            issues=lint_project(project, graph_id),
        )

    async def apply(
        self,
        *,
        workspace_id: str,
        workspace_dir: str,
        slug: str,
        expected_revision: int,
        action: GraphAction,
        arguments: Mapping[str, Any],
    ) -> WorkflowGraphResult:
        current = await self._workflows.read(workspace_dir, slug)
        project, project_format = _load_project(current.project)
        if action == "save_revision":
            raw_project = arguments.get("project")
            if not isinstance(raw_project, str):
                raise WorkflowGraphError("project is required")
            project, project_format = _load_project(raw_project)
        else:
            project = mutate_project(project, action, arguments)
        issues = lint_project(project, arguments.get("graph_id"))
        if any(issue.get("level") == "error" for issue in issues):
            raise WorkflowGraphError("Graph operation would leave the project invalid")
        saved = await self._workflows.save(
            workspace_id,
            workspace_dir,
            slug,
            expected_revision,
            _dump_project(project, project_format),
            (
                arguments.get("datasets")
                if isinstance(arguments.get("datasets"), dict)
                else current.datasets
            ),
        )
        saved_project, _saved_format = _load_project(saved.project)
        return WorkflowGraphResult(
            document=saved,
            graph=summarize_graph(saved_project, arguments.get("graph_id")),
            issues=lint_project(saved_project, arguments.get("graph_id")),
        )
