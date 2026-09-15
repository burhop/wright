from __future__ import annotations

import asyncio
import json

import pytest
from core.engineering_workflow_templates import EngineeringWorkflowTemplateError
from workspace_service.engineering_workflow_template_service import (
    EngineeringWorkflowTemplateService,
)
from workspace_service.engineering_workflow_templates import (
    EngineeringWorkflowTemplateCatalog,
)
from workspace_service.executor import BoundedExecutor
from workspace_service.workflow_sources import (
    WorkflowSourceStorageError,
    WorkspaceWorkflowSourceStore,
    WorkspaceWorkflowSourceUseCases,
)


def _service() -> EngineeringWorkflowTemplateService:
    return EngineeringWorkflowTemplateService(
        WorkspaceWorkflowSourceUseCases(BoundedExecutor()),
        EngineeringWorkflowTemplateCatalog(),
    )


async def _instantiate(service, workspace, request_id="request-0001", path=None):
    template = service._catalog.list()[0]
    return await service.instantiate(
        workspace_id="workspace-1",
        workspace_dir=str(workspace),
        template_id=template.template_id,
        template_version=template.version,
        expected_source_digest=template.source_digest,
        workflow_path=path or "workflows/replacement-part.workflow.wflow",
        request_id=request_id,
        created_by="local-user",
    )


def test_instance_atomically_creates_source_layout_and_hidden_provenance(tmp_path):
    instance = asyncio.run(_instantiate(_service(), tmp_path))
    document = instance.document

    assert document.storage_revision == 1
    assert document.definition_revision == 1
    assert document.layout_status == "current"
    assert document.layout["workflowId"] == instance.workflow_id
    assert (tmp_path / document.path).is_file()
    metadata = tmp_path / ".wright" / "workflow-sources" / "replacement-part"
    origin = json.loads((metadata / "template-origin.json").read_text("utf-8"))
    assert origin["template_id"] == "printed-replacement-part"
    assert origin["workflow_id"] == instance.workflow_id
    assert origin["template_source_digest"] == instance.template_source_digest
    input_root = tmp_path / "inputs" / instance.workflow_id.removeprefix("workflow.")
    assert (input_root / "replacement-knob-source.svg").is_file()
    assert (input_root / "rights.json").is_file()
    assert str(input_root.relative_to(tmp_path)).replace("\\", "/") in document.source
    assert {item["path"] for item in origin["template_inputs"]} == {
        f"inputs/{instance.workflow_id.removeprefix('workflow.')}/replacement-knob-source.svg",
        f"inputs/{instance.workflow_id.removeprefix('workflow.')}/rights.json",
    }
    assert not (tmp_path / ".wright" / "workflow-runs").exists()
    assert "credential" not in json.dumps(origin).lower()
    assert "approval" not in json.dumps(origin).lower()


def test_same_request_is_idempotent_and_different_request_never_overwrites(tmp_path):
    service = _service()
    first = asyncio.run(_instantiate(service, tmp_path))
    retry = asyncio.run(_instantiate(service, tmp_path))
    assert retry.workflow_id == first.workflow_id
    assert retry.document == first.document

    with pytest.raises(WorkflowSourceStorageError) as collision:
        asyncio.run(_instantiate(service, tmp_path, request_id="request-0002"))
    assert collision.value.code == "workflow_source_exists"
    assert (
        WorkspaceWorkflowSourceStore(str(tmp_path)).read(first.document.path)
        == first.document
    )


def test_reused_request_id_with_different_path_creates_independent_instance(tmp_path):
    service = _service()
    first = asyncio.run(_instantiate(service, tmp_path))
    second = asyncio.run(
        _instantiate(
            service,
            tmp_path,
            path="workflows/second-replacement-part.workflow.wflow",
        )
    )
    assert first.workflow_id != second.workflow_id
    assert first.document.path != second.document.path


def test_invalid_request_id_does_not_mutate_workspace(tmp_path):
    with pytest.raises(EngineeringWorkflowTemplateError) as error:
        asyncio.run(_instantiate(_service(), tmp_path, request_id="short"))
    assert error.value.code == "template_request_id_invalid"
    assert not (tmp_path / "workflows").exists()


def test_failed_origin_publication_rolls_back_visible_source_and_layout(
    tmp_path, monkeypatch
):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    original = store._write_once

    def fail_origin(path, content):
        if path.name == "template-origin.json":
            raise OSError("simulated origin failure")
        return original(path, content)

    monkeypatch.setattr(store, "_write_once", fail_origin)
    catalog = EngineeringWorkflowTemplateCatalog()
    template = catalog.list()[0]
    fresh = catalog.fresh_instance(
        template.template_id,
        version=template.version,
        expected_source_digest=template.source_digest,
    )
    with pytest.raises(WorkflowSourceStorageError) as error:
        store.create(
            "workflows/replacement-part.workflow.wflow",
            fresh.source,
            layout=fresh.layout,
            origin={"template_id": template.template_id},
        )
    assert error.value.code == "workflow_source_unavailable"
    assert not (tmp_path / "workflows" / "replacement-part.workflow.wflow").exists()
    metadata = tmp_path / ".wright" / "workflow-sources" / "replacement-part"
    assert not (metadata / "head.json").exists()
    assert not (metadata / "template-origin.json").exists()


def test_stale_preexisting_origin_is_not_deleted_when_creation_fails(tmp_path):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    metadata = tmp_path / ".wright" / "workflow-sources" / "replacement-part"
    metadata.mkdir(parents=True)
    origin_path = metadata / "template-origin.json"
    origin_path.write_text('{"owner":"previous"}', "utf-8")
    catalog = EngineeringWorkflowTemplateCatalog()
    template = catalog.list()[0]
    fresh = catalog.fresh_instance(
        template.template_id,
        version=template.version,
        expected_source_digest=template.source_digest,
    )

    with pytest.raises(WorkflowSourceStorageError) as error:
        store.create(
            "workflows/replacement-part.workflow.wflow",
            fresh.source,
            layout=fresh.layout,
            origin={"template_id": template.template_id},
        )

    assert error.value.code == "workflow_source_integrity"
    assert origin_path.read_text("utf-8") == '{"owner":"previous"}'
    assert not (tmp_path / "workflows" / "replacement-part.workflow.wflow").exists()
