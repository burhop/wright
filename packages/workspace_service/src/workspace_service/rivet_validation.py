from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import yaml


_NODE_TYPE = re.compile(r"\]:([A-Za-z0-9_-]+)(?:\s|$)")
_NODE_ID = re.compile(r"^\[([^\]]+)\]:")
_MAX_GRAPHS = 256
_MAX_PORTS = 256
_MAX_ISSUES = 64
_MAX_MESSAGE = 256


class WorkflowIdentityMismatch(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    message: str
    graph_id: str | None = None
    node_id: str | None = None


@dataclass(frozen=True, slots=True)
class GraphPortSummary:
    id: str
    data_type: str
    required: bool


@dataclass(frozen=True, slots=True)
class GraphSummary:
    id: str
    name: str
    inputs: tuple[GraphPortSummary, ...]
    outputs: tuple[GraphPortSummary, ...]


@dataclass(frozen=True, slots=True)
class WorkflowValidationResult:
    workflow_id: str
    revision: int
    digest: str
    valid: bool
    main_graph: GraphSummary | None
    graphs: tuple[GraphSummary, ...]
    requirements: tuple[str, ...]
    errors: tuple[ValidationIssue, ...]
    warnings: tuple[ValidationIssue, ...]


@dataclass(frozen=True, slots=True)
class RivetMcpNodeRequirement:
    graph_id: str
    node_id: str
    node_type: str
    static_tool_name: str | None


@dataclass(frozen=True, slots=True)
class RivetMcpRequirementResult:
    nodes: tuple[RivetMcpNodeRequirement, ...]
    errors: tuple[ValidationIssue, ...]


def _issue(code: str, message: object, **location: str | None) -> ValidationIssue:
    safe = " ".join(str(message).split())[:_MAX_MESSAGE]
    return ValidationIssue(code, safe, **location)


def _node_type(serialized_id: object, node: object) -> str:
    if isinstance(node, dict) and isinstance(node.get("type"), str):
        return str(node["type"])
    match = _NODE_TYPE.search(str(serialized_id))
    return match.group(1) if match else "unknown"


def _node_id(serialized_id: object, node: object) -> str:
    if isinstance(node, dict) and isinstance(node.get("id"), str):
        return str(node["id"])
    match = _NODE_ID.search(str(serialized_id))
    return match.group(1) if match else str(serialized_id)


def _referenced_graph_ids(node_type: str, node: dict[str, Any]) -> set[str]:
    data = node.get("data")
    if not isinstance(data, dict):
        return set()

    if node_type in {"subGraph", "loopUntil"}:
        key = "graphId" if node_type == "subGraph" else "targetGraph"
        target = data.get(key)
        return {target.strip()} if isinstance(target, str) and target.strip() else set()

    if node_type != "delegateFunctionCall":
        return set()
    handlers = data.get("handlers")
    if not isinstance(handlers, list):
        return set()
    return {
        str(handler["value"]).strip()
        for handler in handlers
        if isinstance(handler, dict)
        and isinstance(handler.get("value"), str)
        and handler["value"].strip()
    }


def _nodes(graph: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    raw = graph.get("nodes")
    if isinstance(raw, dict):
        return [
            (str(key), value) for key, value in raw.items() if isinstance(value, dict)
        ]
    if isinstance(raw, list):
        return [
            (str(value.get("id") or index), value)
            for index, value in enumerate(raw)
            if isinstance(value, dict)
        ]
    return []


def _port(node: dict[str, Any]) -> GraphPortSummary | None:
    data = node.get("data")
    if not isinstance(data, dict):
        return None
    port_id = data.get("id")
    if not isinstance(port_id, str) or not port_id.strip():
        return None
    data_type = data.get("dataType")
    return GraphPortSummary(
        port_id.strip(),
        str(data_type)[:64] if data_type is not None else "any",
        not bool(data.get("useDefaultValueInput", False)),
    )


def _requirements(node_types: set[str]) -> tuple[str, ...]:
    requirements: set[str] = set()
    for value in node_types:
        node_type = value.lower()
        if (
            "chat" in node_type
            or "embedding" in node_type
            or node_type in {"generate", "generateimage", "generateaudio"}
        ):
            requirements.add("ai")
        if "dataset" in node_type or node_type in {"vectorknn", "vectorstore"}:
            requirements.add("dataset")
        if node_type in {
            "readfile",
            "writefile",
            "readallfiles",
            "readdirectory",
        }:
            requirements.add("native-filesystem")
        if node_type in {"code", "codenew"}:
            requirements.add("code")
        if node_type in {"httpcall", "urlreference"}:
            requirements.add("network")
        if "mcp" in node_type or node_type in {"externalcall", "delegatetoolcall"}:
            requirements.add("mcp")
        if node_type in {"userinput", "chatloop", "waitforevent"}:
            requirements.add("interactive-user-input")
    return tuple(sorted(requirements))


def validate_rivet_project(
    project: str,
    *,
    workflow_id: str,
    revision: int,
    digest: str,
    selected_graph: str | None = None,
    expected_revision: int | None = None,
    expected_digest: str | None = None,
) -> WorkflowValidationResult:
    if expected_revision is not None and revision != expected_revision:
        raise WorkflowIdentityMismatch(
            f"Workflow revision changed from {expected_revision} to {revision}"
        )
    if expected_digest is not None and digest != expected_digest:
        raise WorkflowIdentityMismatch("Workflow digest changed")

    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []
    try:
        document = yaml.safe_load(project)
    except yaml.YAMLError as error:
        errors.append(_issue("RIVET_PROJECT_PARSE_FAILED", error))
        return WorkflowValidationResult(
            workflow_id,
            revision,
            digest,
            False,
            None,
            (),
            (),
            tuple(errors),
            (),
        )
    if not isinstance(document, dict) or not isinstance(document.get("data"), dict):
        errors.append(
            _issue("RIVET_PROJECT_INVALID", "Project must contain a data mapping")
        )
        return WorkflowValidationResult(
            workflow_id,
            revision,
            digest,
            False,
            None,
            (),
            (),
            tuple(errors),
            (),
        )

    data = document["data"]
    raw_graphs = data.get("graphs")
    if not isinstance(raw_graphs, dict) or not raw_graphs:
        errors.append(_issue("RIVET_GRAPHS_MISSING", "Project has no graphs"))
        raw_graphs = {}
    if len(raw_graphs) > _MAX_GRAPHS:
        errors.append(
            _issue(
                "RIVET_GRAPH_LIMIT_EXCEEDED",
                f"Project contains more than {_MAX_GRAPHS} graphs",
            )
        )

    graph_summaries: list[GraphSummary] = []
    node_types_by_graph: dict[str, set[str]] = {}
    referenced_graphs_by_graph: dict[str, set[str]] = {}
    for serialized_graph_id, raw_graph in list(raw_graphs.items())[:_MAX_GRAPHS]:
        if not isinstance(raw_graph, dict):
            errors.append(
                _issue(
                    "RIVET_GRAPH_INVALID",
                    "Graph must be a mapping",
                    graph_id=str(serialized_graph_id),
                )
            )
            continue
        metadata = raw_graph.get("metadata")
        metadata = metadata if isinstance(metadata, dict) else {}
        graph_id = str(metadata.get("id") or serialized_graph_id)
        name = str(metadata.get("name") or graph_id)
        inputs: list[GraphPortSummary] = []
        outputs: list[GraphPortSummary] = []
        node_types: set[str] = set()
        referenced_graph_ids: set[str] = set()
        for serialized_node_id, node in _nodes(raw_graph):
            node_type = _node_type(serialized_node_id, node)
            node_types.add(node_type)
            referenced_graph_ids.update(_referenced_graph_ids(node_type, node))
            port = _port(node)
            if port is None:
                continue
            if node_type == "graphInput" and len(inputs) < _MAX_PORTS:
                inputs.append(port)
            elif node_type == "graphOutput" and len(outputs) < _MAX_PORTS:
                outputs.append(port)
        graph_summaries.append(
            GraphSummary(
                graph_id,
                name[:256],
                tuple(sorted(inputs, key=lambda value: value.id)),
                tuple(sorted(outputs, key=lambda value: value.id)),
            )
        )
        node_types_by_graph[graph_id] = node_types
        referenced_graphs_by_graph[graph_id] = referenced_graph_ids

    metadata = data.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    main_selector = selected_graph or metadata.get("mainGraphId")
    main_graph = next(
        (
            graph
            for graph in graph_summaries
            if main_selector is not None
            and (graph.id == str(main_selector) or graph.name == str(main_selector))
        ),
        None,
    )
    if main_selector is None:
        errors.append(
            _issue(
                "RIVET_MAIN_GRAPH_MISSING",
                "Project has no main graph; select a graph explicitly",
            )
        )
    elif main_graph is None:
        errors.append(
            _issue(
                "RIVET_GRAPH_NOT_FOUND",
                f'Graph "{main_selector}" was not found',
            )
        )

    # Runtime services are started only for the graph that will execute. We
    # still validate every graph above, so malformed inactive graphs remain
    # visible without making a no-AI graph depend on Hermes.
    execution_node_types: set[str] = set()
    if main_graph is not None:
        reachable_graph_ids: set[str] = set()
        pending_graph_ids = [main_graph.id]
        while pending_graph_ids:
            graph_id = pending_graph_ids.pop()
            if graph_id in reachable_graph_ids:
                continue
            reachable_graph_ids.add(graph_id)
            execution_node_types.update(node_types_by_graph.get(graph_id, set()))
            pending_graph_ids.extend(
                target
                for target in referenced_graphs_by_graph.get(graph_id, set())
                if target in node_types_by_graph and target not in reachable_graph_ids
            )
    else:
        execution_node_types = set().union(*node_types_by_graph.values())
    return WorkflowValidationResult(
        workflow_id,
        revision,
        digest,
        not errors,
        main_graph,
        tuple(graph_summaries),
        _requirements(execution_node_types),
        tuple(errors[:_MAX_ISSUES]),
        tuple(warnings[:_MAX_ISSUES]),
    )


def extract_rivet_mcp_requirements(
    project: str, *, selected_graph: str | None = None
) -> RivetMcpRequirementResult:
    """Extract executable MCP nodes and reject project-owned connection authority."""

    errors: list[ValidationIssue] = []
    requirements: list[RivetMcpNodeRequirement] = []
    try:
        document = yaml.safe_load(project)
    except yaml.YAMLError as error:
        return RivetMcpRequirementResult(
            (), (_issue("RIVET_PROJECT_PARSE_FAILED", error),)
        )
    if not isinstance(document, dict) or not isinstance(document.get("data"), dict):
        return RivetMcpRequirementResult(
            (),
            (_issue("RIVET_PROJECT_INVALID", "Project must contain a data mapping"),),
        )
    data = document["data"]
    metadata = data.get("metadata")
    if isinstance(metadata, dict) and metadata.get("mcpServer") is not None:
        errors.append(
            _issue(
                "RIVET_MCP_PROJECT_CONFIG_DENIED",
                "Project-owned MCP server configuration is not permitted",
            )
        )
    raw_graphs = data.get("graphs")
    if not isinstance(raw_graphs, dict):
        return RivetMcpRequirementResult((), tuple(errors))
    for serialized_graph_id, graph in list(raw_graphs.items())[:_MAX_GRAPHS]:
        if not isinstance(graph, dict):
            continue
        graph_metadata = graph.get("metadata")
        graph_metadata = graph_metadata if isinstance(graph_metadata, dict) else {}
        graph_id = str(graph_metadata.get("id") or serialized_graph_id)
        graph_name = str(graph_metadata.get("name") or graph_id)
        if selected_graph is not None and selected_graph not in {graph_id, graph_name}:
            # A selected graph can call subgraphs. Inspecting every graph is the
            # fail-closed choice for prohibited configuration, while only the
            # selected graph contributes direct binding requirements here.
            include_requirement = False
        else:
            include_requirement = True
        seen_node_ids: set[str] = set()
        for serialized_node_id, node in _nodes(graph):
            node_type = _node_type(serialized_node_id, node)
            if node_type not in {"mcpDiscovery", "mcpToolCall", "mcpGetPrompt"}:
                continue
            node_id = _node_id(serialized_node_id, node)
            if node_id in seen_node_ids:
                errors.append(
                    _issue(
                        "RIVET_MCP_DUPLICATE_NODE",
                        "MCP node identities must be unique within a graph",
                        graph_id=graph_id,
                        node_id=node_id,
                    )
                )
            seen_node_ids.add(node_id)
            node_data = node.get("data")
            node_data = node_data if isinstance(node_data, dict) else {}
            if node_type == "mcpGetPrompt" or (
                node_type == "mcpDiscovery" and bool(node_data.get("usePromptsOutput"))
            ):
                errors.append(
                    _issue(
                        "RIVET_MCP_PROMPT_DENIED",
                        "MCP prompt operations are not enabled for reviewed tool runs",
                        graph_id=graph_id,
                        node_id=node_id,
                    )
                )
            if any(
                node_data.get(key) not in (None, "", [], {})
                for key in (
                    "serverUrl",
                    "command",
                    "args",
                    "env",
                    "environment",
                    "headers",
                    "authorization",
                    "serverId",
                )
            ):
                errors.append(
                    _issue(
                        "RIVET_MCP_PROJECT_CONFIG_DENIED",
                        "MCP node connection configuration is not permitted",
                        graph_id=graph_id,
                        node_id=node_id,
                    )
                )
            if node_type == "mcpToolCall" and bool(node_data.get("useToolNameInput")):
                errors.append(
                    _issue(
                        "RIVET_MCP_DYNAMIC_TOOL_DENIED",
                        "MCP tool identity must be static",
                        graph_id=graph_id,
                        node_id=node_id,
                    )
                )
            if node_type == "mcpToolCall" and not (
                isinstance(node_data.get("toolName"), str)
                and str(node_data.get("toolName")).strip()
            ):
                errors.append(
                    _issue(
                        "RIVET_MCP_TOOL_REQUIRED",
                        "Choose the exact workspace MCP tool for this node",
                        graph_id=graph_id,
                        node_id=node_id,
                    )
                )
            if include_requirement and node_type in {"mcpDiscovery", "mcpToolCall"}:
                raw_tool = node_data.get("toolName")
                requirements.append(
                    RivetMcpNodeRequirement(
                        graph_id,
                        node_id,
                        node_type,
                        str(raw_tool)
                        if isinstance(raw_tool, str) and raw_tool
                        else None,
                    )
                )
    return RivetMcpRequirementResult(
        tuple(sorted(requirements, key=lambda item: (item.graph_id, item.node_id))),
        tuple(errors[:_MAX_ISSUES]),
    )
