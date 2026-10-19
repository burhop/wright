"""Draft preservation must not change accepted source or grant execution authority."""

import json
import os
from concurrent.futures import ThreadPoolExecutor

import pytest

from workspace_service.workflow_sources import (
    WORKFLOW_SOURCE_MAX_BYTES,
    WorkflowSourceStorageError,
    WorkspaceWorkflowSourceStore,
)

PATH = "workflows/example.workflow.wflow"


@pytest.fixture
def draft(tmp_path):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    accepted = store.create(PATH, "accepted source")
    snapshot = {
        "base_storage_revision": accepted.storage_revision,
        "base_storage_digest": accepted.storage_digest,
        "source": "invalid raw source\n\x00",
        "applied_source": "last valid diagram",
        "layout": None,
        "view": "code",
    }
    return store, accepted, snapshot, tmp_path


def save(store, snapshot, **extra):
    return store.editor_draft_save(
        PATH,
        **{
            "draft_id": "editor-one",
            "request_id": "request-one",
            "expected_draft_digest": None,
            "snapshot": snapshot,
            **extra,
        },
    )["draft"]


def test_reopen_preserves_invalid_raw_and_applied_source_without_accepting(draft):
    store, accepted, snapshot, root = draft
    before = {p: p.read_bytes() for p in root.rglob("*.json")}
    saved = save(store, snapshot)
    fresh = WorkspaceWorkflowSourceStore(str(root))
    assert fresh.editor_drafts_read(PATH, "editor-one")["draft"] == saved
    rows = fresh.editor_drafts_read(PATH)["drafts"]
    assert len(rows) == 1 and "source" not in rows[0] and "layout" not in rows[0]
    assert saved["source"] == snapshot["source"]
    assert saved["applied_source"] == snapshot["applied_source"]
    assert saved["base_matches_current"] and not saved["matches_accepted"]
    assert fresh.read(PATH) == accepted
    assert all(p.read_bytes() == data for p, data in before.items())
    assert not (root / "runs").exists()


def test_cas_idempotence_and_conflicting_request_identity(draft):
    store, _, snapshot, _ = draft
    first = save(store, snapshot)
    assert save(store, snapshot) == first  # reconciliation never increments
    with pytest.raises(WorkflowSourceStorageError, match="reused"):
        save(store, {**snapshot, "source": "different"})
    with pytest.raises(WorkflowSourceStorageError, match="changed"):
        save(store, snapshot, request_id="request-two")
    second = save(
        store,
        {**snapshot, "source": "new edit"},
        request_id="request-two",
        expected_draft_digest=first["draft_digest"],
    )
    assert second["draft_revision"] == 2
    assert second["draft_digest"] != first["draft_digest"]


def test_historical_base_preserved_but_stale_never_accepted(draft):
    store, accepted, snapshot, _ = draft
    newer = store.update(
        PATH,
        expected_storage_revision=accepted.storage_revision,
        expected_storage_digest=accepted.storage_digest,
        semantic_change_validated=True,
        source="new accepted revision",
    )
    saved = save(store, snapshot)
    assert not saved["base_matches_current"]
    assert store.read(PATH) == newer
    with pytest.raises(WorkflowSourceStorageError, match="not an accepted"):
        save(store, {**snapshot, "base_storage_digest": "f" * 64}, draft_id="other")
    clean = save(
        store,
        {
            **snapshot,
            "base_storage_revision": newer.storage_revision,
            "base_storage_digest": newer.storage_digest,
            "source": newer.source,
            "applied_source": newer.source,
        },
        expected_draft_digest=saved["draft_digest"],
        request_id="clean-checkpoint",
    )
    assert clean["matches_accepted"] and clean["base_matches_current"]
    assert clean["accepted_checkpoint"]
    store.update(
        PATH,
        expected_storage_revision=newer.storage_revision,
        expected_storage_digest=newer.storage_digest,
        semantic_change_validated=True,
        source="yet another accepted revision",
    )
    historical = store.editor_drafts_read(PATH, "editor-one")["draft"]
    assert not historical["matches_accepted"] and historical["accepted_checkpoint"]


@pytest.mark.parametrize(
    "patch",
    [
        {"run": True},
        {"view": "run"},
        {"source": None},
        {"base_storage_revision": True},
        {"source": "\ud800"},
        {"source": "x" * (WORKFLOW_SOURCE_MAX_BYTES + 1)},
        {"layout": {"approval": True}},
    ],
)
def test_invalid_or_authority_fields_cannot_be_saved(draft, patch):
    store, accepted, snapshot, _ = draft
    with pytest.raises(WorkflowSourceStorageError):
        save(store, {**snapshot, **patch})
    assert store.editor_drafts_read(PATH)["drafts"] == []
    assert store.read(PATH) == accepted


def test_separate_streams_and_concurrent_cas_preserve_both_editors(draft):
    store, _, snapshot, root = draft
    first = save(store, snapshot)
    save(store, {**snapshot, "source": "other editor"}, draft_id="editor-two")

    def update(i):
        try:
            return save(
                WorkspaceWorkflowSourceStore(str(root)),
                {**snapshot, "source": str(i)},
                expected_draft_digest=first["draft_digest"],
                request_id=f"update-{i}",
            )
        except WorkflowSourceStorageError as error:
            return error.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(update, range(2)))
    assert sum(isinstance(result, dict) for result in results) == 1
    assert "workflow_draft_conflict" in results
    assert len(store.editor_drafts_read(PATH)["drafts"]) == 2
    assert (
        store.editor_drafts_read(PATH, "editor-two")["draft"]["source"]
        == "other editor"
    )


@pytest.mark.parametrize("identity", ["../escape", "a/b", ".", "x" * 97, "CON"])
def test_unsafe_identity_and_foreign_source_rejected(draft, identity):
    store, _, snapshot, _ = draft
    with pytest.raises(WorkflowSourceStorageError):
        save(store, snapshot, draft_id=identity)
    with pytest.raises(WorkflowSourceStorageError):
        store.editor_drafts_read("../other", "editor-one")


def test_tamper_and_linked_draft_fail_closed(draft):
    store, _, snapshot, root = draft
    save(store, snapshot)
    path = root / ".wright/workflow-sources/example/editor-drafts/editor-one.json"
    original = path.read_bytes()
    record = json.loads(original)
    record["source"] = "tampered"
    path.write_text(json.dumps(record))
    with pytest.raises(WorkflowSourceStorageError, match="digest"):
        store.editor_drafts_read(PATH, "editor-one")
    path.unlink()
    outside = root / "outside.json"
    outside.write_bytes(original)
    if os.name == "nt":
        pytest.skip("symlink creation requires Windows privilege")
    path.symlink_to(outside)
    with pytest.raises(WorkflowSourceStorageError):
        store.editor_drafts_read(PATH, "editor-one")
    with pytest.raises(WorkflowSourceStorageError):
        save(store, snapshot)
    assert outside.read_bytes() == original


def test_uncommitted_atomic_temporary_file_is_retained_and_never_a_draft(draft):
    store, _, snapshot, root = draft
    first = save(store, snapshot)
    temporary = (
        root
        / ".wright/workflow-sources/example/editor-drafts"
        / (".wright-workflow-source-" + "f" * 24)
    )
    temporary.write_text("partial uncommitted content")
    assert len(store.editor_drafts_read(PATH)["drafts"]) == 1
    save(store, snapshot, draft_id="second-editor")
    assert temporary.read_text() == "partial uncommitted content"
    assert store.editor_drafts_read(PATH, "editor-one")["draft"] == first


@pytest.mark.skipif(os.name == "nt", reason="Windows pinned directories deny rename")
def test_directory_swap_between_cas_read_and_publication_cannot_overwrite(draft):
    store, accepted, snapshot, root = draft
    first = save(store, snapshot)
    directory = root / ".wright/workflow-sources/example/editor-drafts"
    old = (directory / "editor-one.json").read_bytes()
    moved = directory.with_name("retained-before-swap")

    class SwappingStore(WorkspaceWorkflowSourceStore):
        def _before_filesystem_mutation(self, target):
            if target == directory / "editor-one.json" and not moved.exists():
                directory.rename(moved)
                directory.mkdir()
                target.write_bytes(b"replacement directory sentinel")

    with pytest.raises(WorkflowSourceStorageError):
        save(
            SwappingStore(str(root)),
            {**snapshot, "source": "new edit"},
            request_id="after-swap",
            expected_draft_digest=first["draft_digest"],
        )
    assert (
        directory / "editor-one.json"
    ).read_bytes() == b"replacement directory sentinel"
    assert (moved / "editor-one.json").read_bytes() == old
    assert store.read(PATH) == accepted
