"""Validated package-owned catalog of engineering scenario definitions."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping

import yaml
from core.engineering_scenarios import (
    EngineeringScenarioError,
    ResourceClass,
    ScenarioCatalogEntry,
    ScenarioTier,
)
from core.rivet_mcp import canonical_digest, reject_secret_material
from jsonschema import Draft202012Validator


_PACKAGE = "workspace_service.engineering_scenario_catalog"
_FORBIDDEN_KEYS = {
    "command",
    "args",
    "server_url",
    "serverurl",
    "endpoint",
    "authorization",
    "credential",
    "credentials_value",
    "environment_variables",
    "env",
    "launch_env",
    "host_path",
    "install_command",
}
_PLUGINS = {
    "numeric",
    "table",
    "geometry",
    "ecad",
    "fea",
    "cfd",
    "data_tree",
    "additive",
    "slicer",
    "cam",
}
_TIER1_FORBIDDEN_ENVIRONMENT = {
    "network",
    "credentials",
    "proprietary_application",
    "gpu",
    "hardware",
    "large_download",
}


@dataclass(frozen=True, slots=True)
class EngineeringScenarioManifest:
    document: Mapping[str, Any]
    digest: str
    resource: str

    @property
    def scenario_id(self) -> str:
        return str(self.document["scenario_id"])

    @property
    def entry(self) -> ScenarioCatalogEntry:
        resource = self.document["resource"]
        return ScenarioCatalogEntry(
            scenario_id=self.scenario_id,
            revision=int(self.document["revision"]),
            title=str(self.document["title"]),
            summary=str(self.document["summary"]),
            domains=tuple(str(value) for value in self.document["domains"]),
            tier=ScenarioTier(str(self.document["tier"])),
            resource_class=ResourceClass(str(resource["class"])),
            expected_duration_seconds=int(resource["expected_duration_seconds"]),
            manifest_digest=self.digest,
        )


def _resource_text(path: str) -> str:
    normalized = PurePosixPath(path)
    if normalized.is_absolute() or ".." in normalized.parts:
        raise EngineeringScenarioError(
            "scenario_resource_invalid", "Scenario resource leaves the catalog root"
        )
    resource = files(_PACKAGE).joinpath(*normalized.parts)
    if not resource.is_file():
        raise EngineeringScenarioError(
            "scenario_resource_missing", f"Scenario resource is missing: {path}"
        )
    return resource.read_text(encoding="utf-8")


def contract_document(name: str) -> dict[str, Any]:
    if name not in {
        "scenario-manifest.schema.json",
        "artifact-envelope.schema.json",
        "assertion-result.schema.json",
    }:
        raise EngineeringScenarioError(
            "scenario_contract_missing", "Unknown engineering scenario contract"
        )
    return json.loads(_resource_text(f"contracts/{name}"))


def fixture_documents(scenario_id: str, *, run_id: str) -> tuple[dict[str, Any], ...]:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", scenario_id):
        raise EngineeringScenarioError(
            "scenario_id_invalid", "Scenario identity is invalid"
        )
    values = json.loads(_resource_text(f"fixtures/{scenario_id}.json"))
    documents: list[dict[str, Any]] = []
    for value in values:
        document = json.loads(json.dumps(value).replace("{run_id}", run_id))
        documents.append(document)
    return tuple(documents)


def workflow_text(manifest: EngineeringScenarioManifest) -> str:
    return _resource_text(str(manifest.document["workflow"]["resource"]))


def _walk_forbidden(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = str(key).lower()
            if normalized in _FORBIDDEN_KEYS:
                raise EngineeringScenarioError(
                    "scenario_connection_material_forbidden",
                    f"Connection or host material is forbidden at {path}.{key}",
                )
            _walk_forbidden(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _walk_forbidden(item, f"{path}[{index}]")


def _validate_schema(document: Mapping[str, Any]) -> None:
    validator = Draft202012Validator(contract_document("scenario-manifest.schema.json"))
    errors = sorted(validator.iter_errors(document), key=lambda item: list(item.path))
    if errors:
        error = errors[0]
        field = ".".join(str(part) for part in error.path) or "$"
        raise EngineeringScenarioError(
            "scenario_manifest_invalid", f"{field}: {error.message}"
        )


def _validate_cross_fields(document: Mapping[str, Any]) -> None:
    _walk_forbidden(document)
    reject_secret_material(document)
    capabilities = tuple(document["capabilities"])
    artifacts = tuple(document["artifacts"])
    assertions = tuple(document["assertions"])
    capability_nodes = [str(value["node_id"]) for value in capabilities]
    if len(capability_nodes) != len(set(capability_nodes)):
        raise EngineeringScenarioError(
            "scenario_manifest_invalid", "Capability node identities must be unique"
        )
    artifact_ids = [str(value["artifact_id"]) for value in artifacts]
    if len(artifact_ids) != len(set(artifact_ids)):
        raise EngineeringScenarioError(
            "scenario_manifest_invalid", "Artifact identities must be unique"
        )
    if any(
        str(value["producer_node_id"]) not in capability_nodes for value in artifacts
    ):
        raise EngineeringScenarioError(
            "scenario_manifest_invalid", "Artifact producer is not a capability node"
        )
    assertion_ids: set[str] = set()
    for assertion in assertions:
        assertion_id = str(assertion["assertion_id"])
        if assertion_id in assertion_ids:
            raise EngineeringScenarioError(
                "scenario_manifest_invalid", "Assertion identities must be unique"
            )
        assertion_ids.add(assertion_id)
        if str(assertion["plugin"]) not in _PLUGINS:
            raise EngineeringScenarioError(
                "scenario_plugin_unsupported",
                f"Unsupported assertion plugin: {assertion['plugin']}",
            )
        if any(str(value) not in artifact_ids for value in assertion["artifact_ids"]):
            raise EngineeringScenarioError(
                "scenario_manifest_invalid", "Assertion references an unknown artifact"
            )
    if document["tier"] == "tier1":
        environment = document["environment"]
        blocked = sorted(
            key for key in _TIER1_FORBIDDEN_ENVIRONMENT if environment.get(key)
        )
        if blocked:
            raise EngineeringScenarioError(
                "scenario_tier_invalid",
                f"Tier 1 cannot require: {', '.join(blocked)}",
            )
        if len(capabilities) < 2:
            raise EngineeringScenarioError(
                "scenario_tier_invalid", "Tier 1 requires at least two MCP capabilities"
            )
        if document["resource"]["class"] not in {"small", "medium"}:
            raise EngineeringScenarioError(
                "scenario_tier_invalid", "Tier 1 resource class must be bounded"
            )
    provenance = document["provenance"]
    if provenance["fixture_origin"] == "third-party" and not all(
        provenance.get(field)
        for field in ("source_url", "redistribution", "modifications")
    ):
        raise EngineeringScenarioError(
            "scenario_provenance_incomplete",
            "Third-party fixtures require source, redistribution, and modification records",
        )
    workflow = document["workflow"]
    project = yaml.safe_load(_resource_text(str(workflow["resource"])))
    try:
        graph = project["data"]["graphs"][str(workflow["graph_id"])]
    except (KeyError, TypeError) as exc:
        raise EngineeringScenarioError(
            "scenario_workflow_invalid", "Scenario graph is missing"
        ) from exc
    node_documents: dict[str, Mapping[str, Any]] = {}
    for encoded, value in graph.get("nodes", {}).items():
        encoded_text = str(encoded)
        if not encoded_text.startswith("[") or "]:" not in encoded_text:
            continue
        node_documents[encoded_text[1 : encoded_text.index("]:")]] = value
    for capability in capabilities:
        node = node_documents.get(str(capability["node_id"]))
        if node is None:
            raise EngineeringScenarioError(
                "scenario_workflow_invalid",
                f"Workflow node is missing: {capability['node_id']}",
            )
        if str(node.get("data", {}).get("toolName")) != str(capability["tool_name"]):
            raise EngineeringScenarioError(
                "scenario_workflow_invalid",
                f"Workflow tool does not match manifest: {capability['node_id']}",
            )


def validate_manifest(
    document: Mapping[str, Any], *, resource: str = "inline"
) -> EngineeringScenarioManifest:
    _validate_schema(document)
    _validate_cross_fields(document)
    normalized = json.loads(json.dumps(document, sort_keys=True))
    return EngineeringScenarioManifest(
        document=normalized,
        digest=canonical_digest(normalized),
        resource=resource,
    )


class EngineeringScenarioCatalog:
    """Immutable view of the packaged scenario catalog."""

    def __init__(self) -> None:
        index = yaml.safe_load(_resource_text("catalog.yaml"))
        if index.get("format_version") != 1:
            raise EngineeringScenarioError(
                "scenario_catalog_version_unsupported", "Catalog version is unsupported"
            )
        manifests: dict[str, EngineeringScenarioManifest] = {}
        for item in index.get("scenarios", ()):
            resource = str(item["manifest"])
            document = yaml.safe_load(_resource_text(resource))
            manifest = validate_manifest(document, resource=resource)
            if manifest.scenario_id != item["scenario_id"]:
                raise EngineeringScenarioError(
                    "scenario_catalog_invalid", "Catalog and manifest identities differ"
                )
            if manifest.scenario_id in manifests:
                raise EngineeringScenarioError(
                    "scenario_catalog_invalid", "Scenario identity is duplicated"
                )
            manifests[manifest.scenario_id] = manifest
        self._manifests = manifests

    def list(
        self, *, domains: Iterable[str] = (), tier: str | None = None
    ) -> tuple[ScenarioCatalogEntry, ...]:
        required_domains = frozenset(domains)
        entries = (
            manifest.entry
            for manifest in self._manifests.values()
            if not required_domains
            or required_domains.intersection(manifest.entry.domains)
        )
        if tier is not None:
            entries = (entry for entry in entries if entry.tier == tier)
        return tuple(sorted(entries, key=lambda item: item.scenario_id))

    def get(self, scenario_id: str) -> EngineeringScenarioManifest:
        try:
            return self._manifests[scenario_id]
        except KeyError as exc:
            raise EngineeringScenarioError(
                "scenario_not_found", f"Unknown scenario: {scenario_id}"
            ) from exc


def catalog_resource_path(relative: str) -> Path:
    """Return a concrete path for tests and the existing workflow store."""
    normalized = PurePosixPath(relative)
    if normalized.is_absolute() or ".." in normalized.parts:
        raise EngineeringScenarioError(
            "scenario_resource_invalid", "Scenario resource leaves the catalog root"
        )
    return Path(str(files(_PACKAGE).joinpath(*normalized.parts)))
