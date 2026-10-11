import pytest
from workspace_service.executor import BoundedExecutor
from workspace_service.workflow_sources import (
    WorkspaceWorkflowSourceStore,
    WorkspaceWorkflowSourceUseCases,
    WorkflowSourceConflictError,
    WorkflowSourceStorageError,
)
from packages.workspace_service.tests.test_workflow_source_layouts import layout


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "source",
    [
        "workflow legacy\nend\n",
        "workflow explicit\n  instructions: {saved: true}\nend\n",
    ],
)
async def test_copy_exact_saved_bytes_and_layout_without_instruction_default_injection(
    tmp_path, source
):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    saved = store.create(
        "workflows/original.workflow.wflow",
        source,
        layout=layout(),
        origin={"old": "template"},
    )
    executor = BoundedExecutor(max_workers=1)

    def defaults(_workspace):
        raise AssertionError("Copy must not materialize current defaults")

    service = WorkspaceWorkflowSourceUseCases(executor, instruction_defaults=defaults)
    try:
        copied = await service.copy(
            str(tmp_path),
            saved.path,
            "workflows/copied.workflow.wflow",
            saved.storage_digest,
        )
        assert copied.source == saved.source
        assert copied.storage_digest == saved.storage_digest
        assert copied.layout["positions"] == saved.layout["positions"]
        assert copied.layout_status == "current"
        assert copied.storage_revision == copied.definition_revision == 1
        assert store.read_template_origin(copied.path) is None
        assert store.read(saved.path) == saved
        with pytest.raises(WorkflowSourceStorageError, match="already exists"):
            await service.copy(
                str(tmp_path), saved.path, copied.path, saved.storage_digest
            )
        with pytest.raises(WorkflowSourceConflictError):
            await service.copy(
                str(tmp_path), saved.path, "workflows/conflict.workflow.wflow", "0" * 64
            )
        assert not (tmp_path / "workflows/conflict.workflow.wflow").exists()
        with pytest.raises(WorkflowSourceStorageError):
            await service.copy(
                str(tmp_path),
                saved.path,
                "../outside.workflow.wflow",
                saved.storage_digest,
            )
    finally:
        await executor.close()


@pytest.mark.asyncio
async def test_copy_drops_stale_layout_and_starts_distinct_revision_history(tmp_path):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    saved = store.create(
        "workflows/original.workflow.wflow", "workflow a\nend\n", layout=layout()
    )
    changed = store.update(
        saved.path,
        source="workflow b\nend\n",
        expected_storage_revision=saved.storage_revision,
        expected_storage_digest=saved.storage_digest,
        semantic_change_validated=True,
    )
    assert changed.layout_status == "stale"
    executor = BoundedExecutor(max_workers=1)
    try:
        service = WorkspaceWorkflowSourceUseCases(executor)
        copied = await service.copy(
            str(tmp_path),
            changed.path,
            "workflows/copied.workflow.wflow",
            changed.storage_digest,
        )
        assert copied.source == changed.source
        assert copied.storage_revision == copied.definition_revision == 1
        assert copied.layout is None
    finally:
        await executor.close()
