"""A starter's lineage must not replace current-source readiness or grant authority."""

import asyncio
import json
from types import SimpleNamespace

import pytest

from packages.workspace_service.tests.test_workflow_mcp_execution import Gateway, mcp
from packages.workspace_service.tests.test_workflow_source_execution import source, task
from workspace_service.engineering_workflow_template_service import (
    EngineeringWorkflowTemplateService,
)
from workspace_service.executor import BoundedExecutor
from workspace_service.workflow_run_preparation import (
    prepare_authorized_workflow_run,
    qualify_workflow_run_origin,
)
from workspace_service.workflow_source_execution import WorkflowSourceExecutionError
from workspace_service.workflow_source_execution import _parse
from workspace_service.workflow_sources import WorkspaceWorkflowSourceUseCases


async def starter(root):
    sources = WorkspaceWorkflowSourceUseCases(BoundedExecutor())
    templates = EngineeringWorkflowTemplateService(sources)
    template = next(
        item
        for item in templates._catalog.list()
        if item.template_id == "replacement-drawer-handle"
    )
    instance = await templates.instantiate(
        workspace_id="workspace-1",
        workspace_dir=str(root),
        template_id=template.template_id,
        template_version=template.version,
        expected_source_digest=template.source_digest,
        workflow_path="workflows/handle.workflow.wflow",
        request_id="setup-transition-0001",
        created_by="local-user",
    )
    service = SimpleNamespace(
        workflow_sources=sources,
        engineering_workflow_templates=templates,
    )
    return service, instance.document


def configured_source(*tasks):
    """Complete the editor fields omitted by the compiler's smaller fixtures."""
    sections = _parse(source(*tasks))
    for section in sections:
        fields = section["fields"]
        fields.setdefault("purpose", "Test current-source qualification")
        if section["kind"] == "workflow":
            fields.update(discipline="engineering", reviewed_ai_suggestions=True)
        if section["kind"] == "task":
            fields.setdefault("group", None)
            if "prompt" not in fields:
                fields.setdefault("instructions", "Use the selected capability.")
            for port in fields["inputs"] + fields["outputs"]:
                for key, value in {
                    "item": None,
                    "required": False,
                    "quantity": "one",
                    "description": "Test evidence",
                }.items():
                    port.setdefault(key, value)
    return "".join(
        f"{section['kind']} {section['id']}\n"
        + "".join(
            f"  {key}: {json.dumps(value)}\n"
            for key, value in section["fields"].items()
        )
        + "end\n"
        for section in sections
    )


async def revise(service, root, document, text, *, semantic=True):
    return await service.workflow_sources.update(
        str(root),
        document.path,
        expected_storage_revision=document.storage_revision,
        expected_storage_digest=document.storage_digest,
        semantic_change_validated=semantic,
        source=text,
    )


async def qualify(service, root, document, **overrides):
    return await qualify_workflow_run_origin(
        **{
            "service": service,
            "workspace_dir": str(root),
            "workspace_id": "workspace-1",
            "source_path": document.path,
            "source_digest": document.storage_digest,
            **overrides,
        }
    )


@pytest.mark.parametrize("edit", ["unchanged", "format-only", "reverted", "legacy"])
def test_unconfigured_initial_or_unidentified_source_remains_blocked(tmp_path, edit):
    async def check():
        service, initial = await starter(tmp_path)
        current = initial
        if edit == "format-only":
            current = await revise(
                service, tmp_path, initial, initial.source + "\n", semantic=False
            )
        elif edit in {"reverted", "legacy"}:
            current = await revise(service, tmp_path, initial, source(task()))
            if edit == "reverted":
                current = await revise(service, tmp_path, current, initial.source)
            else:
                path = tmp_path / ".wright/workflow-sources/handle/template-origin.json"
                origin = json.loads(path.read_text())
                origin.pop("instantiated_source_digest")
                path.write_text(json.dumps(origin))
        with pytest.raises(WorkflowSourceExecutionError) as error:
            await qualify(service, tmp_path, current)
        assert error.value.code == "WORKFLOW_TEMPLATE_SETUP_REQUIRED"

    asyncio.run(check())


def test_accepted_revision_preserves_lineage_without_grant_and_rejects_stale_identity(
    tmp_path,
):
    async def check():
        service, initial = await starter(tmp_path)
        origin = await service.workflow_sources.read_template_origin(
            str(tmp_path), initial.path
        )
        current = await revise(service, tmp_path, initial, source(task()))
        assert await qualify(service, tmp_path, current) is None
        assert (
            await service.workflow_sources.read_template_origin(
                str(tmp_path), current.path
            )
            == origin
        )
        assert origin["instantiated_source_digest"] == initial.storage_digest
        with pytest.raises(WorkflowSourceExecutionError) as error:
            await qualify(service, tmp_path, current, source_digest="f" * 64)
        assert error.value.code == "WORKFLOW_SOURCE_CONFLICT"

    asyncio.run(check())


@pytest.mark.parametrize("missing", ["model", "tool"])
def test_accepted_source_still_passes_real_compiler_and_live_qualification(
    tmp_path, missing
):
    async def check():
        service, initial = await starter(tmp_path)
        current = await revise(
            service,
            tmp_path,
            initial,
            configured_source(mcp() if missing == "tool" else task()),
        )
        gateway = Gateway()
        gateway.enabled = False
        capabilities = []

        async def unavailable_model():
            capabilities.append(True)
            return {"available": False}

        service.workflow_model_capabilities = unavailable_model
        with pytest.raises(WorkflowSourceExecutionError) as error:
            await prepare_authorized_workflow_run(
                service=service,
                workspace_dir=str(tmp_path),
                workspace_id="workspace-1",
                session_id="session-1",
                source_path=current.path,
                source_digest=current.storage_digest,
                gateway=gateway,
            )
        assert error.value.code == (
            "WORKFLOW_MODEL_UNAVAILABLE" if missing == "model" else "WORKFLOW_NOT_READY"
        )
        assert capabilities == ([True] if missing == "model" else [])
        assert gateway.calls == []
        assert gateway.closed is (missing == "tool")
        assert not (tmp_path / ".wright/workflow-runs").exists()

    asyncio.run(check())


@pytest.mark.parametrize("change", ["cosmetic_edit", "copy"])
def test_cosmetic_edit_or_copy_does_not_make_placeholder_starter_runnable(
    tmp_path, change
):
    async def check():
        service, initial = await starter(tmp_path)
        if change == "copy":
            current = await service.workflow_sources.copy(
                str(tmp_path),
                initial.path,
                "workflows/handle-copy.workflow.wflow",
                initial.storage_digest,
            )
            assert (
                await service.workflow_sources.read_template_origin(
                    str(tmp_path), current.path
                )
                is None
            )
        else:
            current = await revise(
                service,
                tmp_path,
                initial,
                initial.source.replace(
                    'name: "Replace a broken drawer handle"',
                    'name: "My drawer handle"',
                    1,
                ),
            )
        gateway = Gateway()
        with pytest.raises(WorkflowSourceExecutionError) as error:
            await prepare_authorized_workflow_run(
                service=service,
                workspace_dir=str(tmp_path),
                workspace_id="workspace-1",
                session_id="session-1",
                source_path=current.path,
                source_digest=current.storage_digest,
                gateway=gateway,
            )
        assert error.value.code == "WORKFLOW_NOT_READY"
        assert gateway.calls == []
        assert not (tmp_path / ".wright/workflow-runs").exists()

    asyncio.run(check())


def test_revised_saved_100_handle_uses_current_source_qualification_after_catalog_103(
    tmp_path,
):
    async def check():
        service, initial = await starter(tmp_path)
        origin_path = tmp_path / ".wright/workflow-sources/handle/template-origin.json"
        origin = json.loads(origin_path.read_text())
        assert origin["template_version"] == "1.0.3"
        origin["template_version"] = "1.0.0"
        origin_path.write_text(json.dumps(origin))
        current = await revise(service, tmp_path, initial, configured_source(task()))
        assert await qualify(service, tmp_path, current) is None

        async def unavailable_model():
            return {"available": False}

        service.workflow_model_capabilities = unavailable_model
        gateway = Gateway()
        with pytest.raises(WorkflowSourceExecutionError) as error:
            await prepare_authorized_workflow_run(
                service=service,
                workspace_dir=str(tmp_path),
                workspace_id="workspace-1",
                session_id="session-1",
                source_path=current.path,
                source_digest=current.storage_digest,
                gateway=gateway,
            )
        assert error.value.code == "WORKFLOW_MODEL_UNAVAILABLE"
        assert gateway.calls == []
        assert json.loads(origin_path.read_text()) == origin
        assert not (tmp_path / ".wright/workflow-runs").exists()

    asyncio.run(check())
