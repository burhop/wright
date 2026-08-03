from __future__ import annotations

import pytest

from data_vault import WorkflowRepository
from workspace_service.executor import BoundedExecutor
from workspace_service.use_cases.workflows import WorkspaceWorkflowUseCases

from workspace_service.workflows import (
    WorkflowPersistenceError,
    WorkflowRevisionConflict,
    WorkspaceWorkflowStore,
)


def test_workspace_workflow_is_revisioned_recoverable_and_file_authoritative(tmp_path):
    store = WorkspaceWorkflowStore(str(tmp_path))
    created = store.create("first-flow", "version: 4", {"inputs": "[]"})
    assert (tmp_path / "workflows" / "first-flow" / "workflow.rivet-project").read_text() == "version: 4"
    updated = store.save("first-flow", created.revision, "version: 4\nname: updated")
    with pytest.raises(WorkflowRevisionConflict):
        store.save("first-flow", created.revision, "stale")
    recovery_id = store.delete("first-flow", updated.revision)
    restored = store.recover(recovery_id, "restored-flow")
    assert restored.project.endswith("updated")
    assert restored.datasets == {"inputs": "[]"}


def test_workspace_workflow_rename_is_revisioned(tmp_path):
    store = WorkspaceWorkflowStore(str(tmp_path))
    created = store.create("first-flow", "version: 4")
    renamed = store.rename("first-flow", created.revision, "renamed-flow")
    assert renamed.slug == "renamed-flow"
    assert renamed.revision == 2
    assert not (tmp_path / "workflows" / "first-flow").exists()


@pytest.mark.parametrize("slug", ["../outside", "C:/outside", "two words", "", "a" * 64])
def test_workspace_workflow_rejects_unsafe_slug(tmp_path, slug):
    with pytest.raises(WorkflowPersistenceError):
        WorkspaceWorkflowStore(str(tmp_path)).create(slug, "version: 4")


def test_workspace_workflows_are_isolated(tmp_path):
    left = WorkspaceWorkflowStore(str(tmp_path / "left"))
    right = WorkspaceWorkflowStore(str(tmp_path / "right"))
    left.create("same", "left")
    right.create("same", "right")
    assert left.read("same").project == "left"
    assert right.read("same").project == "right"


def test_one_hundred_stale_save_trials_preserve_current_document(tmp_path):
    store = WorkspaceWorkflowStore(str(tmp_path))
    current = store.create("flow", "initial")
    for number in range(100):
        next_document = store.save("flow", current.revision, f"revision-{number}")
        with pytest.raises(WorkflowRevisionConflict):
            store.save("flow", current.revision, "stale overwrite")
        assert store.read("flow").project == f"revision-{number}"
        current = next_document


def test_workflow_store_rejects_symlinked_workflow_directory(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    workflows = tmp_path / "workflows"
    workflows.mkdir()
    try:
        (workflows / "linked").symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"Symlinks unavailable in this test environment: {error}")
    with pytest.raises(WorkflowPersistenceError):
        WorkspaceWorkflowStore(str(tmp_path)).create("linked", "version: 4")


@pytest.mark.asyncio
async def test_use_cases_keep_index_rebuildable_from_authoritative_files(tmp_path):
    use_cases = WorkspaceWorkflowUseCases(
        BoundedExecutor(), WorkflowRepository(str(tmp_path / "state.db"))
    )
    try:
        created = await use_cases.create("workspace-a", str(tmp_path / "workspace"), "flow", "version: 4")
        await use_cases.save("workspace-a", str(tmp_path / "workspace"), "flow", created.revision, "version: 4\nname: saved")
        assert await use_cases.rebuild_index("workspace-a", str(tmp_path / "workspace")) == 1
    finally:
        await use_cases._executor.close()
