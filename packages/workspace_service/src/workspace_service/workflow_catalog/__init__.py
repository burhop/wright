"""Packaged, provider-neutral Rivet workflow templates."""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from importlib.resources import files
from typing import Any

import yaml


_NODE_KEY = re.compile(r"^\[([^\]]+)\]")


class WorkflowTemplateError(ValueError):
    """Raised when the packaged template catalog or a template is invalid."""


@dataclass(frozen=True, slots=True)
class WorkflowTemplate:
    template_id: str
    title: str
    description: str
    kind: str
    resource: str
    requirements: tuple[str, ...]
    source_repository: str
    source_revision: str
    source_path: str


class WorkflowTemplateCatalog:
    """Loads reviewed templates from package resources and creates fresh projects."""

    def __init__(self, package: str = __package__, resource: str = "catalog.yaml"):
        self._package = package
        self._resource = resource
        self._templates = self._load_catalog()

    def list(self) -> list[WorkflowTemplate]:
        return list(self._templates.values())

    def instantiate(self, template_id: str) -> str:
        template = self._templates.get(template_id)
        if template is None:
            raise WorkflowTemplateError("Workflow template was not found")
        project_text = (
            files(self._package).joinpath(template.resource).read_text("utf-8")
        )
        try:
            project = yaml.safe_load(project_text)
        except yaml.YAMLError as error:
            raise WorkflowTemplateError("Workflow template YAML is invalid") from error
        if not isinstance(project, dict) or project.get("version") != 4:
            raise WorkflowTemplateError("Workflow template must use project version 4")
        data = project.get("data")
        if not isinstance(data, dict):
            raise WorkflowTemplateError("Workflow template data is missing")
        graphs = data.get("graphs")
        if not isinstance(graphs, dict) or not graphs:
            raise WorkflowTemplateError("Workflow template has no graphs")

        replacements: dict[str, str] = {}
        for graph_key, graph in graphs.items():
            if not isinstance(graph_key, str) or not isinstance(graph, dict):
                raise WorkflowTemplateError("Workflow template graph is invalid")
            new_graph_id = _fresh_id()
            replacements[graph_key] = new_graph_id
            metadata = graph.get("metadata")
            if isinstance(metadata, dict) and isinstance(metadata.get("id"), str):
                replacements[str(metadata["id"])] = new_graph_id
            nodes = graph.get("nodes")
            if not isinstance(nodes, dict):
                raise WorkflowTemplateError("Workflow template graph nodes are invalid")
            for node_key in nodes:
                if not isinstance(node_key, str):
                    raise WorkflowTemplateError("Workflow template node key is invalid")
                match = _NODE_KEY.match(node_key)
                if not match:
                    raise WorkflowTemplateError("Workflow template node key is invalid")
                replacements[match.group(1)] = _fresh_id()

        metadata = data.get("metadata")
        if not isinstance(metadata, dict):
            raise WorkflowTemplateError("Workflow template metadata is missing")
        project_id = metadata.get("id")
        if isinstance(project_id, str):
            replacements[project_id] = _fresh_id()

        instantiated = _replace_references(project, replacements)
        instantiated_data = instantiated["data"]
        instantiated_data["metadata"]["title"] = template.title
        if not instantiated_data["metadata"].get("mainGraphId"):
            instantiated_data["metadata"]["mainGraphId"] = next(
                iter(instantiated_data["graphs"])
            )
        return yaml.safe_dump(
            instantiated,
            allow_unicode=True,
            sort_keys=False,
            width=120,
        )

    def _load_catalog(self) -> dict[str, WorkflowTemplate]:
        try:
            document = yaml.safe_load(
                files(self._package).joinpath(self._resource).read_text("utf-8")
            )
        except (OSError, yaml.YAMLError) as error:
            raise WorkflowTemplateError(
                "Workflow template catalog is invalid"
            ) from error
        if not isinstance(document, dict) or document.get("format_version") != 1:
            raise WorkflowTemplateError("Unsupported workflow template catalog")
        entries = document.get("templates")
        if not isinstance(entries, list) or not entries:
            raise WorkflowTemplateError("Workflow template catalog is empty")

        result: dict[str, WorkflowTemplate] = {}
        for raw in entries:
            if not isinstance(raw, dict):
                raise WorkflowTemplateError("Workflow template entry is invalid")
            try:
                template = WorkflowTemplate(
                    template_id=str(raw["id"]),
                    title=str(raw["title"]),
                    description=str(raw["description"]),
                    kind=str(raw["kind"]),
                    resource=str(raw["resource"]),
                    requirements=tuple(
                        str(item) for item in raw.get("requirements", [])
                    ),
                    source_repository=str(raw["source_repository"]),
                    source_revision=str(raw["source_revision"]),
                    source_path=str(raw["source_path"]),
                )
            except (KeyError, TypeError) as error:
                raise WorkflowTemplateError(
                    "Workflow template entry is incomplete"
                ) from error
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", template.template_id):
                raise WorkflowTemplateError("Workflow template ID is invalid")
            if template.kind not in {"starter", "advanced", "example"}:
                raise WorkflowTemplateError("Workflow template kind is invalid")
            if template.template_id in result:
                raise WorkflowTemplateError("Workflow template ID is duplicated")
            resource = files(self._package).joinpath(template.resource)
            if not resource.is_file():
                raise WorkflowTemplateError("Workflow template resource is missing")
            result[template.template_id] = template
        return result


def _fresh_id() -> str:
    return secrets.token_urlsafe(15)


def _replace_references(value: Any, replacements: dict[str, str]) -> Any:
    ordered = sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True)
    if isinstance(value, str):
        result = value
        for old, new in ordered:
            result = result.replace(old, new)
        return result
    if isinstance(value, list):
        return [_replace_references(item, replacements) for item in value]
    if isinstance(value, dict):
        return {
            _replace_references(key, replacements): _replace_references(
                item, replacements
            )
            for key, item in value.items()
        }
    return value


__all__ = [
    "WorkflowTemplate",
    "WorkflowTemplateCatalog",
    "WorkflowTemplateError",
]
