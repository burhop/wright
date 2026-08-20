"""Small format-preserving repairs for Wright-owned Rivet projects."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any


def _node_kind(node_id: str) -> str | None:
    if node_id.startswith("[") and "]:" in node_id:
        return node_id.split("]:", 1)[1].split(" ", 1)[0] or None
    return None


def _load_project(project: str) -> tuple[dict[str, Any], str]:
    try:
        loaded = json.loads(project)
        if isinstance(loaded, dict):
            return loaded, "json"
    except json.JSONDecodeError:
        pass
    return {}, "yaml"


def _dump_project(project: Mapping[str, Any], original_format: str) -> str:
    if original_format == "json":
        return json.dumps(project, indent=2, sort_keys=True) + "\n"
    return ""


def _normalize_yaml_graph_output_ids(project: str) -> str:
    lines = project.splitlines(keepends=True)
    used: set[str] = set()
    output_indent: int | None = None
    changed = False
    for index, line in enumerate(lines):
        indent = len(line) - len(line.lstrip())
        if re.search(r'graphOutput\s+"[^"]+"\'\s*:\s*$', line.rstrip("\r\n")):
            output_indent = indent
            continue
        if output_indent is not None and line.strip() and indent <= output_indent:
            output_indent = None
        if output_indent is None:
            continue
        match = re.match(
            r'^(\s+id:\s*)(["\']?)([^"\'\r\n]*?)(["\']?)(\s*)(\r?\n)?$',
            line,
        )
        if not match:
            continue
        output_id = match.group(3).strip() or "output"
        unique_output_id = output_id
        suffix = 2
        while unique_output_id in used:
            unique_output_id = f"{output_id}_{suffix}"
            suffix += 1
        used.add(unique_output_id)
        if match.group(3) != unique_output_id:
            lines[index] = (
                f"{match.group(1)}{match.group(2)}{unique_output_id}"
                f"{match.group(4)}{match.group(5)}{match.group(6) or ''}"
            )
            changed = True
    return "".join(lines) if changed else project


def normalize_graph_output_ids(project: str) -> str:
    """Assign deterministic unique IDs when Rivet creates duplicate outputs."""

    loaded, original_format = _load_project(project)
    if original_format == "yaml":
        return _normalize_yaml_graph_output_ids(project)
    data = loaded.get("data")
    graphs = data.get("graphs") if isinstance(data, dict) else None
    if not isinstance(graphs, dict):
        return project
    changed = False
    for graph in graphs.values():
        if not isinstance(graph, dict):
            continue
        nodes = graph.get("nodes")
        if not isinstance(nodes, dict):
            continue
        used: set[str] = set()
        for node_id, node in nodes.items():
            if not isinstance(node, dict):
                continue
            node_type = str(node.get("type") or _node_kind(str(node_id)) or "")
            if node_type != "graphOutput":
                continue
            node_data = node.setdefault("data", {})
            if not isinstance(node_data, dict):
                continue
            raw_output_id = node_data.get("id")
            output_id = (
                raw_output_id.strip()
                if isinstance(raw_output_id, str) and raw_output_id.strip()
                else "output"
            )
            unique_output_id = output_id
            suffix = 2
            while unique_output_id in used:
                unique_output_id = f"{output_id}_{suffix}"
                suffix += 1
            used.add(unique_output_id)
            if raw_output_id != unique_output_id:
                node_data["id"] = unique_output_id
                changed = True
    return _dump_project(loaded, original_format) if changed else project
