"""Workspace-scoped use cases for canonical engineering workflow templates."""

from __future__ import annotations

import hashlib
import asyncio
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any

from core.engineering_workflow_templates import EngineeringWorkflowTemplateError

from .engineering_workflow_templates import EngineeringWorkflowTemplateCatalog
from .workflow_sources import WorkflowSourceDocument, WorkspaceWorkflowSourceUseCases
from .workspace_path import WorkspacePath


_REQUEST_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")


@dataclass(frozen=True, slots=True)
class EngineeringWorkflowTemplateInstance:
    workspace_id: str
    workflow_id: str
    document: WorkflowSourceDocument
    template_id: str
    template_version: str
    template_source_digest: str
    template_layout_digest: str


def _request_digest(
    *, template_id: str, version: str, source_digest: str, path: str
) -> str:
    value = json.dumps(
        {
            "path": path,
            "source_digest": source_digest,
            "template_id": template_id,
            "version": version,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(value).hexdigest()


class EngineeringWorkflowTemplateService:
    def __init__(
        self,
        workflow_sources: WorkspaceWorkflowSourceUseCases,
        catalog: EngineeringWorkflowTemplateCatalog | None = None,
    ) -> None:
        self._sources = workflow_sources
        self._catalog = catalog or EngineeringWorkflowTemplateCatalog()

    @property
    def catalog_version(self) -> str:
        return self._catalog.catalog_version

    def list(self) -> tuple[dict[str, Any], ...]:
        return tuple(item.summary_document() for item in self._catalog.list())

    def detail(self, template_id: str, version: str | None = None) -> dict[str, Any]:
        detail = self._catalog.get(template_id, version)
        return {
            **detail.template.summary_document(),
            "source": detail.source,
            "layout": detail.layout,
            "capability_requirements": list(detail.template.capability_requirements),
            "acceptance_profile": detail.template.acceptance_profile,
            "definition_status": detail.template.definition_status,
            "rights": dict(detail.template.rights),
            "layout_digest": detail.template.layout_digest,
        }

    def readiness(self, template_id: str, version: str | None = None) -> dict[str, Any]:
        return self._catalog.get(template_id, version).template.summary_document()[
            "readiness"
        ]

    def preview(
        self, template_id: str, version: str | None = None
    ) -> tuple[bytes, str]:
        return self._catalog.preview(template_id, version)

    async def instantiate(
        self,
        *,
        workspace_id: str,
        workspace_dir: str,
        template_id: str,
        template_version: str,
        expected_source_digest: str,
        workflow_path: str,
        request_id: str,
        created_by: str,
    ) -> EngineeringWorkflowTemplateInstance:
        if not _REQUEST_ID.fullmatch(request_id):
            raise EngineeringWorkflowTemplateError(
                "template_request_id_invalid", "Template request identity is invalid"
            )
        request_digest = _request_digest(
            template_id=template_id,
            version=template_version,
            source_digest=expected_source_digest,
            path=workflow_path,
        )
        fresh = self._catalog.fresh_instance(
            template_id,
            version=template_version,
            expected_source_digest=expected_source_digest,
        )
        origin: dict[str, object] = {
            "schema_version": 1,
            "workspace_id": workspace_id,
            "workflow_id": fresh.workflow_id,
            "template_id": fresh.template.template_id,
            "template_version": fresh.template.version,
            "template_source_digest": fresh.template.source_digest,
            "template_layout_digest": fresh.template.layout_digest,
            "request_id": request_id,
            "request_digest": request_digest,
            "created_at": int(time.time()),
            "created_by": created_by,
            "template_inputs": [
                {
                    "path": f"inputs/{fresh.workflow_id.removeprefix('workflow.')}/{name}",
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "size_bytes": len(content),
                }
                for name, content in fresh.seed_files
            ],
        }
        try:
            document = await self._sources.create(
                workspace_dir,
                workflow_path,
                fresh.source,
                layout=fresh.layout,
                origin=origin,
            )
        except Exception as error:
            if getattr(error, "code", None) != "workflow_source_exists":
                raise
            existing_origin = await self._sources.read_template_origin(
                workspace_dir, workflow_path
            )
            if (
                existing_origin is None
                or existing_origin.get("request_id") != request_id
                or existing_origin.get("request_digest") != request_digest
            ):
                raise
            document = await self._sources.read(workspace_dir, workflow_path)
            fresh = type(fresh)(
                template=fresh.template,
                workflow_id=str(existing_origin["workflow_id"]),
                source=document.source,
                layout=document.layout or fresh.layout,
                semantic_ids=fresh.semantic_ids,
                seed_files=fresh.seed_files,
            )
        await self._install_seed_files(workspace_dir, fresh)
        return EngineeringWorkflowTemplateInstance(
            workspace_id=workspace_id,
            workflow_id=fresh.workflow_id,
            document=document,
            template_id=fresh.template.template_id,
            template_version=fresh.template.version,
            template_source_digest=fresh.template.source_digest,
            template_layout_digest=fresh.template.layout_digest,
        )

    @staticmethod
    async def _install_seed_files(workspace_dir: str, fresh) -> None:
        """Exclusively install immutable distributable inputs; retries verify bytes."""

        if not fresh.seed_files:
            return

        def install() -> None:
            paths = WorkspacePath(workspace_dir)
            root = f"inputs/{fresh.workflow_id.removeprefix('workflow.')}"
            for relative, content in fresh.seed_files:
                target = paths.resolve(f"{root}/{relative}")
                target.parent.mkdir(parents=True, exist_ok=True)
                try:
                    with target.open("xb") as stream:
                        stream.write(content)
                        stream.flush()
                        os.fsync(stream.fileno())
                except FileExistsError:
                    existing = target.read_bytes()
                    if (
                        not hashlib.sha256(existing).digest()
                        == hashlib.sha256(content).digest()
                    ):
                        raise EngineeringWorkflowTemplateError(
                            "template_input_conflict",
                            "A supplied template input path already contains different bytes",
                        )

        await asyncio.to_thread(install)
