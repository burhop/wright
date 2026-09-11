from __future__ import annotations

import copy
import json
import os
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from workspace_service.workflow_sources import (
    WorkflowSourceStorageError,
    WorkspaceWorkflowSourceStore,
)


SOURCE_PATH = "workflows/bracket.workflow.wflow"


def layout():
    return {
        "documentKind": "workflow-layout",
        "schemaVersion": "1.0.0-recovery.1",
        "workflowId": "workflow.bracket",
        "semanticRevision": 1,
        "layoutRevision": 1,
        "positions": {"block.design-intent": {"x": 120, "y": 40}},
        "viewport": {"x": 0, "y": 0, "zoom": 1},
    }


def save(store, current, value, *, source=None):
    return store.update(
        SOURCE_PATH,
        source=source if source is not None else current.source,
        semantic_change_validated=source is not None,
        expected_storage_revision=current.storage_revision,
        expected_storage_digest=current.storage_digest,
        layout=value,
        expected_layout_revision=current.layout_revision,
    )


def test_layout_only_save_and_reopen_keeps_source_and_semantic_identity(tmp_path):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    created = store.create(SOURCE_PATH, "workflow bracket\nend\n")
    head = tmp_path / ".wright/workflow-sources/bracket/head.json"
    original_head = head.read_bytes()
    saved = save(store, created, layout())
    assert saved.storage_revision == created.storage_revision
    assert saved.storage_digest == created.storage_digest
    assert saved.definition_revision == created.definition_revision
    assert saved.layout_revision == 1
    assert saved.layout == layout()
    assert saved.layout_status == "current"
    assert head.read_bytes() == original_head
    assert WorkspaceWorkflowSourceStore(str(tmp_path)).read(SOURCE_PATH) == saved
    assert (tmp_path / SOURCE_PATH).read_text() == created.source
    assert save(store, saved, saved.layout) == saved


def test_source_and_layout_commit_rebases_only_host_managed_identity(tmp_path):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    created = store.create(SOURCE_PATH, "before")
    saved = save(store, created, layout(), source="after")
    assert saved.definition_revision == 2
    assert saved.layout["semanticRevision"] == 2
    assert saved.layout["layoutRevision"] == 1
    assert saved.layout["positions"] == layout()["positions"]
    assert store.read(SOURCE_PATH) == saved


def test_layout_cas_rejects_stale_save_without_touching_source(tmp_path):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    created = store.create(SOURCE_PATH, "before")
    first = save(store, created, layout())
    second = layout()
    second["positions"]["block.design-intent"]["x"] = 600
    with pytest.raises(WorkflowSourceStorageError, match="layout changed") as failure:
        save(store, created, second, source="stale source")
    assert failure.value.code == "workflow_layout_conflict"
    assert store.read(SOURCE_PATH) == first


@pytest.mark.parametrize("target", ["layout-head.json", "head.json"])
def test_failed_joint_publication_restores_source_and_previous_layout(
    tmp_path, monkeypatch, target
):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    created = store.create(SOURCE_PATH, "before")
    first = save(store, created, layout())
    original_write = store._atomic_write
    failed = False

    def fail_once(path, content):
        nonlocal failed
        if path.name == target and not failed:
            failed = True
            raise OSError("injected publication failure")
        original_write(path, content)

    monkeypatch.setattr(store, "_atomic_write", fail_once)
    changed = layout()
    changed["positions"]["block.design-intent"]["x"] = 400
    with pytest.raises(WorkflowSourceStorageError):
        save(store, first, changed, source="after")
    assert store.read(SOURCE_PATH) == first


def test_legacy_source_only_save_keeps_layout_generation_but_does_not_apply_stale_layout(
    tmp_path,
):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    created = store.create(SOURCE_PATH, "before")
    first = save(store, created, layout())
    directory = tmp_path / ".wright/workflow-sources/bracket"
    previous_layout_head = (directory / "layout-head.json").read_bytes()
    updated = store.update(
        SOURCE_PATH,
        source="external authoring update",
        semantic_change_validated=True,
        expected_storage_revision=first.storage_revision,
        expected_storage_digest=first.storage_digest,
    )
    assert updated.layout is None
    assert updated.layout_status == "stale"
    assert updated.layout_revision == first.layout_revision
    assert (directory / "layout-head.json").read_bytes() == previous_layout_head
    assert store.read(SOURCE_PATH) == updated


def test_layout_pointer_failure_restores_previous_generation_and_retry_does_not_overwrite_it(
    tmp_path, monkeypatch
):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    first = save(store, store.create(SOURCE_PATH, "before"), layout())
    directory = tmp_path / ".wright/workflow-sources/bracket"
    original_head = (directory / "layout-head.json").read_bytes()
    original_write = store._atomic_write
    failed = False

    def fail_after_pointer_publish(path, content):
        nonlocal failed
        original_write(path, content)
        if path.name == "layout-head.json" and not failed:
            failed = True
            raise OSError("injected post-publication failure")

    changed = layout()
    changed["positions"]["block.design-intent"]["y"] = 900
    monkeypatch.setattr(store, "_atomic_write", fail_after_pointer_publish)
    with pytest.raises(WorkflowSourceStorageError):
        save(store, first, changed)
    assert (directory / "layout-head.json").read_bytes() == original_head
    assert store.read(SOURCE_PATH) == first
    saved = save(store, first, changed)
    assert saved.layout_revision == 2
    assert len(list((directory / "layouts").iterdir())) == 3
    assert store.read(SOURCE_PATH) == saved


def test_legacy_source_a_b_a_does_not_apply_old_layout_or_fail_after_commit(tmp_path):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    first = save(store, store.create(SOURCE_PATH, "source A"), layout())
    current = first
    for source in ("source B", "source A"):
        current = store.update(
            SOURCE_PATH,
            source=source,
            semantic_change_validated=True,
            expected_storage_revision=current.storage_revision,
            expected_storage_digest=current.storage_digest,
        )
        assert current.layout is None
        assert current.layout_status == "stale"
        assert store.read(SOURCE_PATH) == current
    assert current.definition_revision == 3
    assert current.storage_digest == first.storage_digest
    assert current.layout_revision == first.layout_revision


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update(extra="no"),
        lambda value: value.update(workflowId="../../outside"),
        lambda value: value.update(schemaVersion="2.0.0"),
        lambda value: value["positions"].update({"../outside": {"x": 0, "y": 0}}),
        lambda value: value["positions"]["block.design-intent"].update(x=float("inf")),
        lambda value: value["positions"]["block.design-intent"].update(x=True),
        lambda value: value["positions"]["block.design-intent"].update(x=10000001),
        lambda value: value["positions"]["block.design-intent"].update(x=10**400),
        lambda value: value["viewport"].update(zoom=0),
    ],
)
def test_invalid_layout_rejects_before_source_write(tmp_path, mutation):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    created = store.create(SOURCE_PATH, "before")
    value = copy.deepcopy(layout())
    mutation(value)
    with pytest.raises(WorkflowSourceStorageError) as failure:
        save(store, created, value, source="must not commit")
    assert failure.value.code == "workflow_layout_invalid"
    assert store.read(SOURCE_PATH) == created


def test_tampered_layout_generation_fails_closed_without_changing_source(tmp_path):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    created = store.create(SOURCE_PATH, "before")
    save(store, created, layout())
    directory = tmp_path / ".wright/workflow-sources/bracket"
    head = json.loads((directory / "layout-head.json").read_text())
    (directory / "layouts" / head["record"]).write_text("{}")
    with pytest.raises(WorkflowSourceStorageError) as failure:
        store.read(SOURCE_PATH)
    assert failure.value.code == "workflow_source_integrity"
    assert (tmp_path / SOURCE_PATH).read_text() == "before"


def test_input_choices_are_real_relative_files_and_exclude_hidden_and_links(tmp_path):
    (tmp_path / "design").mkdir()
    (tmp_path / "design" / "requirements.md").write_text("Real design requirements")
    (tmp_path / ".env").write_text("secret")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "dependency.js").write_text("internal")
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    assert store.list_input_files() == [
        {"path": "design/requirements.md", "name": "requirements.md"}
    ]
    (tmp_path / "design" / "requirements.md").unlink()
    assert store.list_input_files() == []


def test_input_choices_scan_the_pinned_descriptor_when_available(tmp_path, monkeypatch):
    (tmp_path / "requirements.md").write_text("workspace design intent")
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    real_scandir = os.scandir
    scanned = []

    @contextmanager
    def pinned_directory(_path, *, create):
        assert create is False
        yield SimpleNamespace(descriptor=123, assert_current=lambda: None)

    def scan(target):
        scanned.append(target)
        return real_scandir(tmp_path)

    monkeypatch.setattr(store, "_directory_capability", pinned_directory)
    monkeypatch.setattr(os, "scandir", scan)
    assert store.list_input_files() == [
        {"path": "requirements.md", "name": "requirements.md"}
    ]
    assert scanned == [123]


@pytest.mark.skipif(
    os.name == "nt",
    reason="POSIX descriptor/rename race; Windows directory handles deny rename",
)
def test_input_choices_ignore_a_directory_swap_restored_before_identity_check(
    tmp_path, monkeypatch
):
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    parked = tmp_path / "parked-workspace"
    workspace.mkdir()
    outside.mkdir()
    (workspace / "requirements.md").write_text("workspace design intent")
    (outside / "private-name.txt").write_text("must not be listed")
    store = WorkspaceWorkflowSourceStore(str(workspace))
    real_scandir = os.scandir

    @contextmanager
    def swapped_scandir(target):
        workspace.rename(parked)
        outside.rename(workspace)
        try:
            with real_scandir(target) as entries:
                yield entries
        finally:
            workspace.rename(outside)
            parked.rename(workspace)

    monkeypatch.setattr(os, "scandir", swapped_scandir)
    assert store.list_input_files() == [
        {"path": "requirements.md", "name": "requirements.md"}
    ]


@pytest.mark.parametrize("directory_link", [False, True])
def test_input_choices_exclude_real_external_file_and_directory_links(
    tmp_path, directory_link
):
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()
    (outside / "private.txt").write_text("must never be a workspace choice")
    target = outside if directory_link else outside / "private.txt"
    try:
        (workspace / "external").symlink_to(target, target_is_directory=directory_link)
    except OSError as error:
        pytest.skip(
            f"Host cannot create a real symlink for this containment test: {error}"
        )
    assert WorkspaceWorkflowSourceStore(str(workspace)).list_input_files() == []


def test_two_workflow_files_keep_independent_source_and_layout_heads(tmp_path):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    first = save(store, store.create(SOURCE_PATH, "first source"), layout())
    other_path = "workflows/another.workflow.wflow"
    second = store.create(other_path, "second source")
    changed = layout()
    changed["positions"]["block.design-intent"]["x"] = 800
    second_saved = store.update(
        other_path,
        source="second revised",
        semantic_change_validated=True,
        expected_storage_revision=second.storage_revision,
        expected_storage_digest=second.storage_digest,
        layout=changed,
        expected_layout_revision=0,
    )
    assert second_saved.layout["positions"]["block.design-intent"]["x"] == 800
    assert store.read(SOURCE_PATH) == first
    assert store.read(other_path) == second_saved
