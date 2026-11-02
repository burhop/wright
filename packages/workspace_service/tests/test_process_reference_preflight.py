"""Catalog setup guidance precedes placeholder compilation only in a new view."""

import hashlib
from unittest.mock import AsyncMock, Mock

import pytest

from core.process_interactions import NavigationTarget, ProcessRef
from packages.workspace_service.tests.test_process_preparation_service import (
    owner,
    scope,
    source,
)
from workspace_service.engineering_workflow_template_service import (
    EngineeringWorkflowTemplateService,
)
from workspace_service.executor import BoundedExecutor
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    compile_prompt_workflow,
)
from workspace_service.workflow_sources import WorkspaceWorkflowSourceUseCases


async def starter(root, template_id):
    app = owner(root, "")
    sources = WorkspaceWorkflowSourceUseCases(BoundedExecutor())
    templates = EngineeringWorkflowTemplateService(sources)
    detail = templates.detail(template_id)
    instance = await templates.instantiate(
        workspace_id="workspace",
        workspace_dir=str(root),
        template_id=template_id,
        template_version=detail["version"],
        expected_source_digest=detail["source_digest"],
        workflow_path=f"workflows/{template_id}.workflow.wflow",
        request_id="reference-view-0001",
        created_by="local-user",
    )
    app.workspace.workflow_sources = sources
    app.workspace.engineering_workflow_templates = templates
    return app, instance.document


def reference(document):
    return ProcessRef(
        workspace_id="workspace",
        source_path=document.path,
        source_digest=document.storage_digest,
    )


def files(root):
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "template_id", ["replacement-drawer-handle", "heat-spreader-sizing"]
)
async def test_unchanged_reference_view_returns_catalog_guidance_without_effects(
    tmp_path, template_id
):
    app, document = await starter(tmp_path, template_id)
    gateway = Mock(side_effect=AssertionError("A reference view cannot open tools"))
    model = AsyncMock(side_effect=AssertionError("A reference view cannot call models"))
    app.workspace.workflow_model_capabilities = model
    before = files(tmp_path)

    # Both actual shipped references contain unbound review placeholders.
    with pytest.raises(WorkflowSourceExecutionError, match="not configured to run"):
        compile_prompt_workflow(document.source)
    with pytest.raises(ProcessInterfaceError) as error:
        await app.get_snapshot(
            scope("process.read"), reference(document), gateway=gateway
        )
    assert error.value.reason.code == "CAPABILITY_UNAVAILABLE"
    assert error.value.reason.message == (
        "This engineering template needs setup or qualification before a live run."
    )
    assert error.value.reason.correction == " ".join(
        app.workspace.engineering_workflow_templates.readiness(template_id)[
            "blocking_reasons"
        ]
    )
    assert error.value.reason.navigation == NavigationTarget(kind="process")
    gateway.assert_not_called()
    model.assert_not_awaited()
    assert files(tmp_path) == before
    assert "runs" not in app.__dict__
    assert "inputs" not in app.__dict__

    # The existing editor navigation and explicit input operation retain their
    # own semantics; the preflight belongs only to the no-run common view.
    target = NavigationTarget(kind="process")
    navigation = await app.navigation.resolve(
        scope("process.navigate"), reference(document), target
    )
    assert navigation.process == reference(document)
    assert navigation.target == target
    with pytest.raises(ProcessInterfaceError, match="not configured to run") as inputs:
        await app.set_inputs(scope("process.inputs"), reference(document))
    assert inputs.value.reason.code == "READINESS_UNSUPPORTED"
    assert files(tmp_path) == before


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("changed", "expected"),
    [("digest", "SOURCE_CHANGED"), ("workspace", "SCOPE_DENIED")],
)
async def test_identity_failure_precedes_catalog_access(tmp_path, changed, expected):
    app, document = await starter(tmp_path, "replacement-drawer-handle")
    origin = AsyncMock(
        side_effect=AssertionError("Unverified identity cannot read origin")
    )
    app.workspace.workflow_sources.read_template_origin = origin
    current = reference(document).model_copy(
        update={"source_digest": "f" * 64}
        if changed == "digest"
        else {"workspace_id": "foreign"}
    )
    with pytest.raises(ProcessInterfaceError) as error:
        await app.get_snapshot(scope("process.read"), current)
    assert error.value.reason.code == expected
    origin.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("configured", [False, True])
async def test_accepted_revision_reaches_current_compiler_and_input_readiness(
    tmp_path, configured
):
    app, initial = await starter(tmp_path, "replacement-drawer-handle")
    text = (
        source(default="Declared current requirements")
        if configured
        else initial.source.replace(
            'name: "Confirm visual intent"', 'name: "Revised visual review"', 1
        )
    )
    document = await app.workspace.workflow_sources.update(
        str(tmp_path),
        initial.path,
        expected_storage_revision=initial.storage_revision,
        expected_storage_digest=initial.storage_digest,
        semantic_change_validated=True,
        source=text,
    )
    assert document.definition_revision > 1
    gateway = Mock(side_effect=AssertionError("No tool is required by this source"))
    before = files(tmp_path)
    if configured:
        snapshot = await app.get_snapshot(
            scope("process.read"), reference(document), gateway=gateway
        )
        assert snapshot.readiness.state == "ready"
        assert snapshot.inputs[0].default.value == "Declared current requirements"
        assert snapshot.inputs[0].current_value is None
        assert snapshot.context.process == reference(document)
        assert not snapshot.actions[0].enabled  # Reading never persists preparation.
    else:
        with pytest.raises(ProcessInterfaceError) as error:
            await app.get_snapshot(
                scope("process.read"), reference(document), gateway=gateway
            )
        assert error.value.reason.code == "READINESS_UNSUPPORTED"
        assert "Create the handle geometry is not configured to run" in str(error.value)
    gateway.assert_not_called()
    assert files(tmp_path) == before


@pytest.mark.asyncio
async def test_recorded_run_read_does_not_requalify_catalog_origin(tmp_path):
    from packages.workspace_service.tests.test_process_run_supervisor import (
        prepared_case,
        start,
    )

    app, current, frozen = await prepared_case(tmp_path)

    async def generate(prompt, fmt):
        return "Controlled recorded result"

    try:
        receipt = await start(app, current, frozen, generate)
        assert (await app.runs.wait(scope(), current, receipt.run_id))["status"] == (
            "completed"
        )
        origin = AsyncMock(
            side_effect=AssertionError("Recorded reads cannot requalify the catalog")
        )
        app.workspace.workflow_sources.read_template_origin = origin
        before = files(tmp_path)
        # Existing result projection can initialize repository tables. Verify
        # the source, recorded run and produced artifacts, not SQLite page bytes.
        before.pop("state.db")
        snapshot = await app.get_snapshot(scope(), current, run_id=receipt.run_id)
        assert snapshot.context.run_id == receipt.run_id
        assert snapshot.state == "completed"
        origin.assert_not_awaited()
        after = files(tmp_path)
        after.pop("state.db")
        assert after == before
    finally:
        await app.close()
