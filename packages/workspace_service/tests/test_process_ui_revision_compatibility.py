"""Saved origin provenance stays immutable while current bindings are checked.

Real managed-source CAS, revision, presentation and grant owners; controlled
model/compiler/runtime ports. No engineering operation or review is performed.
"""

import json
from types import SimpleNamespace

import pytest

from workspace_service.executor import BoundedExecutor
from workspace_service.workflow_sources import WorkspaceWorkflowSourceUseCases
from workspace_service.process_interfaces.compatibility import (
    check_interface_compatibility,
)
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.process_interfaces.surface_bridge import ProcessSurfaceBridge
from packages.workspace_service.tests.test_process_input_readiness import (
    process,
    source,
)
from packages.workspace_service.tests.test_process_ui_authoring import (
    Engine,
    authorized,
)
from packages.workspace_service.tests.test_process_ui_presentations import (
    native_case,
    save,
    retained_grants,
)


def required_input(output):
    output["manifest"]["bindings"] = [
        {
            "binding_id": "design-brief",
            "kind": "input",
            "selector": "brief",
            "block_id": "brief",
            "port_id": "brief_out",
            "expected_schema": {"type": "string", "minLength": 1},
            "required": True,
        }
    ]
    return output


async def managed(case, executor):
    prior = await case.application.workspace.workflow_sources.read(
        case.root, case.process.source_path
    )
    case.application.workspace.workflow_sources = WorkspaceWorkflowSourceUseCases(
        executor
    )
    case.application.workspace.ensure_workspace_path_safe = lambda path: path
    await case.application.workspace.workflow_sources.create(
        str(case.root), case.process.source_path, prior.source
    )
    case.author.engine = Engine(replies=[required_input])
    job = await case.author.submit(
        authorized(), case.process, "create-one", "Show inputs"
    )
    job = await case.author.wait(authorized(), case.process, job.job_id)
    assert job.state == "preview_ready", job.diagnostics
    preview = await case.owner.open(
        case.scope,
        case.process,
        case.actor,
        job.job_id,
        "origin-preview",
        read_only=True,
    )
    revision = await save(case, job, preview)
    return job, revision


async def changed(case, text):
    sources = case.application.workspace.workflow_sources
    head = await sources.read(str(case.root), case.process.source_path)
    updated = await sources.update(
        str(case.root),
        case.process.source_path,
        source=text,
        expected_storage_revision=head.storage_revision,
        expected_storage_digest=head.storage_digest,
        semantic_change_validated=True,
    )
    reference = process(text)
    assert (
        reference.source_digest == updated.storage_digest != case.process.source_digest
    )
    return reference


@pytest.mark.asyncio
async def test_unsaved_draft_cannot_transfer_to_changed_source(tmp_path, monkeypatch):
    case = native_case(tmp_path, monkeypatch)
    executor = BoundedExecutor(max_workers=1)
    try:
        original = await case.application.workspace.workflow_sources.read(
            case.root, case.process.source_path
        )
        case.application.workspace.workflow_sources = WorkspaceWorkflowSourceUseCases(
            executor
        )
        case.application.workspace.ensure_workspace_path_safe = lambda path: path
        await case.application.workspace.workflow_sources.create(
            str(case.root), case.process.source_path, original.source
        )
        job = await case.author.submit(
            authorized(), case.process, "unsaved", "Show inputs"
        )
        assert (
            await case.author.wait(authorized(), case.process, job.job_id)
        ).state == "preview_ready"
        current = await changed(case, original.source + "\n")
        with pytest.raises(ProcessInterfaceError) as denied:
            case.application.ui_revisions.presentation_bundle(
                case.scope, current, job.job_id
            )
        assert denied.value.reason.code == "SCOPE_DENIED"
        assert not case.manager.calls and not (tmp_path / "first.txt").exists()
    finally:
        await case.author.close()
        await executor.close()


@pytest.mark.asyncio
async def test_compatible_source_revision_reuses_exact_saved_build_and_current_grants(
    tmp_path, monkeypatch
):
    case = native_case(tmp_path, monkeypatch)
    executor = BoundedExecutor(max_workers=1)
    try:
        job, revision = await managed(case, executor)
        original = revision.model_dump_json()
        head = await case.application.workspace.workflow_sources.read(
            str(case.root), case.process.source_path
        )
        current = await changed(case, head.source + "\n")
        compatibility = await check_interface_compatibility(
            case.application, case.scope, current, revision
        )
        assert compatibility.state == "compatible", compatibility
        calls, probes = len(case.author.engine.calls), case.author.engine.probes
        opened = await case.owner.open(
            case.scope,
            current,
            case.actor,
            job.job_id,
            "current-working",
            read_only=False,
        )
        assert opened["binding"].process == current
        assert opened["build"] == revision.build
        grants = retained_grants(case)
        current_grants = [
            g
            for g in grants
            if g.constraints["presentation_id"] == opened["launch"].presentation_id
        ]
        assert current_grants and all(
            g.constraints["process"] == current.model_dump(mode="json")
            for g in current_grants
        )
        descriptor, launch = opened["descriptor"], opened["launch"]
        route = SimpleNamespace(
            source_id=descriptor.source.source_id,
            source_version=descriptor.source.source_version,
            principal_id=case.actor.user_id,
            workspace_id=case.actor.workspace_id,
            session_id=case.actor.session_id,
            instance_id=launch.instance_id,
            presentation_id=launch.presentation_id,
            generation=launch.generation,
            authority_valid=lambda: True,
            target_valid=lambda: True,
            http_declared=True,
            activity=lambda: None,
        )
        bridged = ProcessSurfaceBridge(
            case.application, case.surfaces.grant_service
        ).authorize(route)
        assert (
            bridged.binding == opened["binding"]
            and bridged.scope.workspace_id == current.workspace_id
        )
        activated = await case.application.ui_revisions.activate(
            authorized(),
            current,
            revision.manifest.ui_id,
            revision.manifest.revision_id,
            expected_active_revision=revision.manifest.revision_id,
        )
        assert activated.active_revision == revision.manifest.revision_id
        # Source revision reuse is not available to generation/save's draft loader.
        with pytest.raises(ProcessInterfaceError):
            case.application.ui_revisions.preview_bundle(
                case.scope, current, job.job_id
            )
        for foreign in (
            current.model_copy(update={"workspace_id": "foreign"}),
            current.model_copy(
                update={"source_path": "workflows/foreign.workflow.wflow"}
            ),
        ):
            with pytest.raises((ProcessInterfaceError, KeyError)):
                case.application.ui_revisions.presentation_bundle(
                    case.scope, foreign, job.job_id
                )
        assert (
            case.application.interfaces.get_revision(
                current.workspace_id,
                revision.manifest.ui_id,
                revision.manifest.revision_id,
            ).model_dump_json()
            == original
        )
        assert (len(case.author.engine.calls), case.author.engine.probes) == (
            calls,
            probes,
        )
        with pytest.raises(ProcessInterfaceError) as stale:
            await case.application.resolve_process(case.scope, case.process)
        assert stale.value.reason.code == "SOURCE_CHANGED"
        assert not (tmp_path / "first.txt").exists()
    finally:
        await case.author.close()
        await executor.close()


@pytest.mark.asyncio
async def test_required_binding_change_denies_saved_open_but_focused_update_uses_current_source(
    tmp_path, monkeypatch
):
    case = native_case(tmp_path, monkeypatch)
    executor = BoundedExecutor(max_workers=1)
    try:
        job, revision = await managed(case, executor)
        current = await changed(
            case,
            source(
                default="Changed requirements",
                later=True,
                metadata={
                    "version": 1,
                    "value_schema": {"type": "string", "minLength": 4},
                    "default": "Changed requirements",
                },
            ),
        )
        compatibility = await check_interface_compatibility(
            case.application, case.scope, current, revision
        )
        assert compatibility.state == "incompatible"
        assert compatibility.reasons[0].code == "UI_INCOMPATIBLE"
        runtime_calls = len(case.manager.calls)
        with pytest.raises(ProcessInterfaceError):
            await case.owner.open(
                case.scope,
                current,
                case.actor,
                job.job_id,
                "bad-current",
                read_only=False,
            )
        assert len(case.manager.calls) == runtime_calls

        def corrected(output):
            output["manifest"]["bindings"][0]["expected_schema"] = {
                "type": "string",
                "minLength": 4,
            }
            return output

        case.author.engine.replies.append(corrected)
        update = await case.author.submit(
            authorized(),
            current,
            "source-update",
            "Update the input schema",
            ui_id=revision.manifest.ui_id,
            base_revision=revision.manifest.revision_id,
        )
        result = await case.author.wait(authorized(), current, update.job_id)
        assert result.state == "preview_ready", result.diagnostics
        prompt = json.loads(case.author.engine.calls[-1].message)
        assert prompt["previous_manifest"] == revision.manifest.model_dump(mode="json")
        assert prompt["manifest"]["process"] == current.model_dump(mode="json")
        assert prompt["previous_source"]["files"]["App.tsx"]
        current_preview = await case.owner.open(
            case.scope,
            current,
            case.actor,
            update.job_id,
            "updated-preview",
            read_only=True,
        )
        from workspace_service.process_interfaces.artifacts import (
            ProcessUIPreviewObservation,
        )

        revisions = case.application.ui_revisions
        _, manifest, report, _, _ = revisions.preview_bundle(
            case.scope, current, update.job_id
        )
        revisions.observe_preview(
            case.scope,
            current,
            update.job_id,
            ProcessUIPreviewObservation(
                current_preview["launch"].presentation_id,
                manifest.ui_id,
                manifest.revision_id,
                report.bundle_digest,
            ),
        )
        saved = await revisions.save(
            authorized(),
            current,
            update.job_id,
            expected_source_digest=report.source_digest,
            expected_manifest_digest=report.manifest_digest,
            expected_bundle_digest=report.bundle_digest,
            expected_active_revision=revision.manifest.revision_id,
        )
        assert (
            saved.manifest.process == current
            and saved.manifest.parent_revision == revision.manifest.revision_id
        )
        with pytest.raises(ProcessInterfaceError) as rollback:
            await revisions.activate(
                authorized(),
                current,
                revision.manifest.ui_id,
                revision.manifest.revision_id,
                expected_active_revision=saved.manifest.revision_id,
            )
        assert rollback.value.reason.code == "UI_INCOMPATIBLE"
        assert (
            case.application.interfaces.get_ui(
                current.workspace_id, manifest.ui_id
            ).active_revision
            == saved.manifest.revision_id
        )
        assert not (tmp_path / "first.txt").exists()
    finally:
        await case.author.close()
        await executor.close()
