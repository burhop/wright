"""Load immutable engineering templates and create fresh canonical instances."""

from __future__ import annotations

import hashlib
import json
import re
import secrets
from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import Any

import yaml
from core.engineering_workflow_templates import (
    EngineeringWorkflowTemplate,
    EngineeringWorkflowTemplateError,
    TemplateDefinitionStatus,
    TemplateReadiness,
    TemplateReadinessFact,
    TemplateReadinessState,
)


_RESOURCE_ROOT = Path(__file__).resolve().parent
_SAFE_RESOURCE = re.compile(
    r"^(templates|layouts|previews|inputs)/[a-z0-9][a-z0-9./_-]*$"
)
_DECLARATION = re.compile(
    r"^(workflow|item|input|task|group|connection) (__instance__|[a-z][a-z0-9_]*)\s*$",
    re.MULTILINE,
)
_CATALOG_KEYS = {"catalog_version", "templates"}
_TEMPLATE_KEYS = {
    "id",
    "version",
    "title",
    "summary",
    "discipline",
    "source",
    "layout",
    "preview",
    "provided_inputs",
    "requested_inputs",
    "expected_outputs",
    "capabilities",
    "external_effects",
    "acceptance_profile",
    "definition_status",
    "rights",
    "readiness",
    "readiness_facts",
    "blocking_reasons",
}
_SENSITIVE_KEYS = {
    "api_key",
    "access_token",
    "refresh_token",
    "password",
    "private_key",
    "secret",
}


@dataclass(frozen=True, slots=True)
class EngineeringWorkflowTemplateDetail:
    template: EngineeringWorkflowTemplate
    source: str
    layout: dict[str, Any]


@dataclass(frozen=True, slots=True)
class FreshEngineeringWorkflowInstance:
    template: EngineeringWorkflowTemplate
    workflow_id: str
    source: str
    layout: dict[str, Any]
    semantic_ids: tuple[str, ...]
    seed_files: tuple[tuple[str, bytes], ...]


def _bytes(path: Path) -> bytes:
    try:
        target = path.resolve(strict=True)
    except OSError as error:
        raise EngineeringWorkflowTemplateError(
            "template_resource_missing", "A packaged template resource is missing"
        ) from error
    if _RESOURCE_ROOT not in target.parents or not target.is_file():
        raise EngineeringWorkflowTemplateError(
            "template_resource_path_invalid", "Template resource path is unsafe"
        )
    return target.read_bytes()


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _resource(value: object) -> str:
    if (
        not isinstance(value, str)
        or not _SAFE_RESOURCE.fullmatch(value)
        or ".." in value
    ):
        raise EngineeringWorkflowTemplateError(
            "template_resource_path_invalid", "Template resource path is unsafe"
        )
    return value


def _mapping_sequence(value: object, label: str) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise EngineeringWorkflowTemplateError(
            "template_catalog_invalid", f"{label} must be a list of objects"
        )
    return tuple(dict(item) for item in value)


def _reject_sensitive_values(value: object) -> None:
    if isinstance(value, dict):
        if any(str(key).lower() in _SENSITIVE_KEYS for key in value):
            raise EngineeringWorkflowTemplateError(
                "template_credentials_forbidden",
                "Template resources cannot contain credential values",
            )
        for item in value.values():
            _reject_sensitive_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_sensitive_values(item)


class EngineeringWorkflowTemplateCatalog:
    """Fail-closed loader for the ten built-in canonical-source templates."""

    def __init__(self, resource_root: Path | None = None) -> None:
        self._root = (resource_root or _RESOURCE_ROOT).resolve()
        catalog_path = self._root / "catalog.yaml"
        try:
            document = yaml.safe_load(catalog_path.read_text("utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError) as error:
            raise EngineeringWorkflowTemplateError(
                "template_catalog_unavailable",
                "Engineering template catalog is unavailable",
            ) from error
        if (
            not isinstance(document, dict)
            or set(document) != _CATALOG_KEYS
            or document.get("catalog_version") != "1.0.0"
        ):
            raise EngineeringWorkflowTemplateError(
                "template_catalog_invalid", "Engineering template catalog is invalid"
            )
        rows = document.get("templates")
        if not isinstance(rows, list) or len(rows) != 10:
            raise EngineeringWorkflowTemplateError(
                "template_catalog_invalid",
                "Engineering template catalog must contain exactly ten entries",
            )
        _reject_sensitive_values(document)
        self.catalog_version = "1.0.0"
        templates = tuple(self._parse(row) for row in rows)
        if len({item.template_id for item in templates}) != len(templates):
            raise EngineeringWorkflowTemplateError(
                "template_catalog_invalid",
                "Engineering template identities must be unique",
            )
        self._templates = templates
        self._by_id = {item.template_id: item for item in templates}

    def _read_resource(self, resource: str) -> bytes:
        path = (self._root / resource).resolve()
        if self._root not in path.parents:
            raise EngineeringWorkflowTemplateError(
                "template_resource_path_invalid", "Template resource path is unsafe"
            )
        try:
            return path.read_bytes()
        except OSError as error:
            raise EngineeringWorkflowTemplateError(
                "template_resource_missing", "A packaged template resource is missing"
            ) from error

    def _parse(self, row: object) -> EngineeringWorkflowTemplate:
        if not isinstance(row, dict):
            raise EngineeringWorkflowTemplateError(
                "template_catalog_invalid", "Template catalog entry is invalid"
            )
        if set(row) != _TEMPLATE_KEYS:
            raise EngineeringWorkflowTemplateError(
                "template_catalog_invalid",
                "Template catalog entry contains missing or unknown fields",
            )
        source_resource = _resource(row.get("source"))
        layout_resource = _resource(row.get("layout"))
        preview = row.get("preview")
        if not isinstance(preview, dict) or set(preview) != {"asset", "alt"}:
            raise EngineeringWorkflowTemplateError(
                "template_catalog_invalid", "Template preview is invalid"
            )
        preview_asset = _resource(preview.get("asset"))
        source_bytes = self._read_resource(source_resource)
        layout_bytes = self._read_resource(layout_resource)
        self._read_resource(preview_asset)
        try:
            source = source_bytes.decode("utf-8")
            layout = json.loads(layout_bytes)
        except (UnicodeError, json.JSONDecodeError) as error:
            raise EngineeringWorkflowTemplateError(
                "template_resource_invalid", "Template source or layout is invalid"
            ) from error
        declarations = tuple(_DECLARATION.finditer(source))
        if (
            not declarations
            or sum(match.group(1) == "workflow" for match in declarations) != 1
        ):
            raise EngineeringWorkflowTemplateError(
                "template_source_invalid",
                "Template source must contain one workflow declaration",
            )
        if "__instance__" not in source:
            raise EngineeringWorkflowTemplateError(
                "template_source_invalid",
                "Template source does not declare fresh identity placeholders",
            )
        if (
            not isinstance(layout, dict)
            or layout.get("workflowId") != "workflow.__instance__"
        ):
            raise EngineeringWorkflowTemplateError(
                "template_layout_invalid",
                "Template layout does not match its source identity",
            )
        facts = tuple(
            TemplateReadinessFact(
                code=str(item["code"]),
                label=str(item["label"]),
                satisfied=bool(item["satisfied"]),
                evidence=tuple(str(value) for value in item.get("evidence", ())),
            )
            for item in row.get("readiness_facts", ())
        )
        blocking = tuple(str(value) for value in row.get("blocking_reasons", ()))
        readiness = TemplateReadiness(
            state=TemplateReadinessState(str(row["readiness"])),
            definition_valid=True,
            configured=False,
            qualified=False,
            available=False,
            verified_run=False,
            facts=facts,
            blocking_reasons=blocking,
        )
        return EngineeringWorkflowTemplate(
            template_id=str(row["id"]),
            version=str(row["version"]),
            title=str(row["title"]),
            summary=str(row["summary"]),
            discipline=str(row["discipline"]),
            source_resource=source_resource,
            layout_resource=layout_resource,
            preview_asset=preview_asset,
            preview_alt=str(preview["alt"]),
            source_digest=_digest(source_bytes),
            layout_digest=_digest(layout_bytes),
            provided_inputs=_mapping_sequence(
                row.get("provided_inputs", []), "provided_inputs"
            ),
            requested_inputs=_mapping_sequence(
                row.get("requested_inputs", []), "requested_inputs"
            ),
            expected_outputs=_mapping_sequence(
                row.get("expected_outputs", []), "expected_outputs"
            ),
            capability_requirements=_mapping_sequence(
                row.get("capabilities", []), "capabilities"
            ),
            external_effects=tuple(
                str(value) for value in row.get("external_effects", ())
            ),
            acceptance_profile=str(row["acceptance_profile"]),
            definition_status=TemplateDefinitionStatus(str(row["definition_status"])),
            rights=dict(row.get("rights", {})),
            readiness=readiness,
        )

    def list(self) -> tuple[EngineeringWorkflowTemplate, ...]:
        return self._templates

    def get(
        self, template_id: str, version: str | None = None
    ) -> EngineeringWorkflowTemplateDetail:
        template = self._by_id.get(template_id)
        if template is None or (version is not None and version != template.version):
            raise EngineeringWorkflowTemplateError(
                "template_not_found", "Engineering workflow template was not found"
            )
        source = self._read_resource(template.source_resource).decode("utf-8")
        layout = json.loads(self._read_resource(template.layout_resource))
        return EngineeringWorkflowTemplateDetail(template, source, layout)

    def preview(
        self, template_id: str, version: str | None = None
    ) -> tuple[bytes, str]:
        detail = self.get(template_id, version)
        content = self._read_resource(detail.template.preview_asset)
        media_type = (
            "image/svg+xml"
            if detail.template.preview_asset.endswith(".svg")
            else "application/octet-stream"
        )
        return content, media_type

    def fresh_instance(
        self,
        template_id: str,
        *,
        version: str,
        expected_source_digest: str,
    ) -> FreshEngineeringWorkflowInstance:
        detail = self.get(template_id, version)
        if expected_source_digest != detail.template.source_digest:
            raise EngineeringWorkflowTemplateError(
                "template_digest_mismatch", "Template changed after it was previewed"
            )
        token = f"t{secrets.token_hex(12)}"
        input_root = f"inputs/{token}"
        source = detail.source.replace("__instance__", token).replace(
            "__input_root__", input_root
        )
        layout = json.loads(json.dumps(detail.layout).replace("__instance__", token))
        semantic_ids = tuple(
            f"{match.group(1)}.{match.group(2).replace('__instance__', token).replace('_', '-')}"
            for match in _DECLARATION.finditer(detail.source)
        )
        seed_root = (self._root / "inputs" / template_id).resolve()
        seed_files: list[tuple[str, bytes]] = []
        if seed_root.is_dir():
            if self._root not in seed_root.parents:
                raise EngineeringWorkflowTemplateError(
                    "template_resource_path_invalid", "Template input path is unsafe"
                )
            candidates = sorted(path for path in seed_root.rglob("*") if path.is_file())
            if len(candidates) > 16:
                raise EngineeringWorkflowTemplateError(
                    "template_resource_invalid",
                    "A template has too many supplied inputs",
                )
            total = 0
            for path in candidates:
                relative = path.relative_to(seed_root).as_posix()
                if any(part.startswith(".") for part in PurePath(relative).parts):
                    raise EngineeringWorkflowTemplateError(
                        "template_resource_path_invalid",
                        "Template input path is unsafe",
                    )
                content = self._read_resource(f"inputs/{template_id}/{relative}")
                total += len(content)
                seed_files.append((relative, content))
            if total > 8 * 1024 * 1024:
                raise EngineeringWorkflowTemplateError(
                    "template_resource_invalid", "Template supplied inputs exceed 8 MiB"
                )
        return FreshEngineeringWorkflowInstance(
            template=detail.template,
            workflow_id=f"workflow.{token}",
            source=source,
            layout=layout,
            semantic_ids=semantic_ids,
            seed_files=tuple(seed_files),
        )


__all__ = [
    "EngineeringWorkflowTemplateCatalog",
    "EngineeringWorkflowTemplateDetail",
    "FreshEngineeringWorkflowInstance",
]
