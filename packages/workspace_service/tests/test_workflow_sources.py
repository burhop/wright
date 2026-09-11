from __future__ import annotations

import asyncio
import multiprocessing
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from workspace_service.workflow_sources import (
    WORKFLOW_SOURCE_MAX_BYTES,
    WORKFLOW_SOURCE_METADATA_MAX_BYTES,
    WorkflowSourceConflictError,
    WorkflowSourceStorageError,
    WorkspaceWorkflowSourceStore,
    WorkspaceWorkflowSourceUseCases,
)
from workspace_service.executor import BoundedExecutor
from workspace_service.errors import WorkspaceTimeoutError


SOURCE_PATH = "workflows/mounting-bracket.workflow.wflow"


def _metadata_path(workspace: Path) -> Path:
    return workspace / ".wright" / "workflow-sources" / "mounting-bracket"


def _lock_path(workspace: Path) -> Path:
    return _metadata_path(workspace) / ".lock"


def _multiprocess_update(
    workspace: str,
    revision: int,
    digest: str,
    source: str,
    barrier,
    results,
) -> None:
    try:
        barrier.wait(timeout=15)
        document = WorkspaceWorkflowSourceStore(workspace).update(
            SOURCE_PATH,
            expected_storage_revision=revision,
            expected_storage_digest=digest,
            semantic_change_validated=True,
            source=source,
        )
        results.put(("success", document.storage_revision, document.source))
    except WorkflowSourceConflictError as error:
        results.put(("conflict", error.storage_revision, error.storage_digest))
    except BaseException as error:  # pragma: no cover - surfaced by parent assertion
        results.put(("error", type(error).__name__, str(error)))


def _hold_workflow_source_transaction(
    workspace: str,
    ready,
    release,
    results,
) -> None:
    store = WorkspaceWorkflowSourceStore(workspace)
    try:
        _normalized, slug, source_path = store._source_path(SOURCE_PATH)
        with store._transaction(slug, source_path):
            ready.set()
            if not release.wait(timeout=15):
                raise TimeoutError("parent did not release held transaction")
        results.put(("released",))
    except BaseException as error:  # pragma: no cover - surfaced by parent assertion
        results.put(("error", type(error).__name__, str(error)))


def test_source_file_is_visible_opaque_and_revisioned_outside_definition(tmp_path):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    source = "workflow mounting_bracket\nend\n"

    created = store.create(SOURCE_PATH, source)

    assert created.path == SOURCE_PATH
    assert created.storage_revision == 1
    assert created.definition_revision == 1
    assert created.size_bytes == len(source.encode("utf-8"))
    assert len(created.storage_digest) == 64
    assert (tmp_path / SOURCE_PATH).read_text(encoding="utf-8") == source
    assert "revision" not in (tmp_path / SOURCE_PATH).read_text(encoding="utf-8")
    metadata = _metadata_path(tmp_path)
    assert (metadata / "head.json").is_file()
    assert (metadata / "revisions" / "00000000000000000001.json").is_file()

    reread = store.read(SOURCE_PATH)
    assert reread == created


def test_storage_and_definition_revisions_have_separate_host_managed_meanings(
    tmp_path,
):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    first = store.create(SOURCE_PATH, "first")
    formatting_only = store.update(
        SOURCE_PATH,
        expected_storage_revision=first.storage_revision,
        expected_storage_digest=first.storage_digest,
        semantic_change_validated=False,
        source="first\n",
    )
    semantic = store.update(
        SOURCE_PATH,
        expected_storage_revision=formatting_only.storage_revision,
        expected_storage_digest=formatting_only.storage_digest,
        semantic_change_validated=True,
        source="second",
    )

    assert formatting_only.storage_revision == 2
    assert formatting_only.definition_revision == 1
    assert semantic.storage_revision == 3
    assert semantic.definition_revision == 2
    assert store.read(SOURCE_PATH) == semantic

    unchanged = store.update(
        SOURCE_PATH,
        expected_storage_revision=semantic.storage_revision,
        expected_storage_digest=semantic.storage_digest,
        semantic_change_validated=True,
        source="second",
    )
    assert unchanged == semantic

    with pytest.raises(WorkflowSourceConflictError) as conflict:
        store.update(
            SOURCE_PATH,
            expected_storage_revision=first.storage_revision,
            expected_storage_digest=first.storage_digest,
            semantic_change_validated=True,
            source="stale",
        )
    assert conflict.value.storage_revision == semantic.storage_revision
    assert conflict.value.storage_digest == semantic.storage_digest


def test_per_workflow_thread_lock_allows_only_one_same_base_update(tmp_path):
    first = WorkspaceWorkflowSourceStore(str(tmp_path)).create(SOURCE_PATH, "base")

    def update(source: str):
        return WorkspaceWorkflowSourceStore(str(tmp_path)).update(
            SOURCE_PATH,
            expected_storage_revision=first.storage_revision,
            expected_storage_digest=first.storage_digest,
            semantic_change_validated=True,
            source=source,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(update, source) for source in ("left", "right")]
    successes = []
    conflicts = []
    for future in futures:
        try:
            successes.append(future.result())
        except WorkflowSourceConflictError as error:
            conflicts.append(error)

    assert len(successes) == 1
    assert len(conflicts) == 1
    assert successes[0].storage_revision == 2
    assert successes[0].definition_revision == 2
    assert WorkspaceWorkflowSourceStore(str(tmp_path)).read(SOURCE_PATH).source in {
        "left",
        "right",
    }


def test_file_lock_allows_only_one_same_base_update_across_processes(tmp_path):
    first = WorkspaceWorkflowSourceStore(str(tmp_path)).create(SOURCE_PATH, "base")
    context = multiprocessing.get_context("spawn")
    barrier = context.Barrier(2)
    results = context.Queue()
    processes = [
        context.Process(
            target=_multiprocess_update,
            args=(
                str(tmp_path),
                first.storage_revision,
                first.storage_digest,
                source,
                barrier,
                results,
            ),
        )
        for source in ("left", "right")
    ]

    for process in processes:
        process.start()
    for process in processes:
        process.join(timeout=20)
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
            pytest.fail("workflow-source update process did not finish")
        assert process.exitcode == 0

    outcomes = [results.get(timeout=5), results.get(timeout=5)]
    assert sorted(outcome[0] for outcome in outcomes) == ["conflict", "success"]
    current = WorkspaceWorkflowSourceStore(str(tmp_path)).read(SOURCE_PATH)
    assert current.storage_revision == 2
    assert current.definition_revision == 2
    assert current.source in {"left", "right"}


def test_cross_process_lock_deadline_fails_before_commit_and_never_commits_later(
    tmp_path,
):
    first = WorkspaceWorkflowSourceStore(str(tmp_path)).create(SOURCE_PATH, "base")
    context = multiprocessing.get_context("spawn")
    ready = context.Event()
    release = context.Event()
    results = context.Queue()
    process = context.Process(
        target=_hold_workflow_source_transaction,
        args=(str(tmp_path), ready, release, results),
    )
    process.start()
    try:
        assert ready.wait(timeout=10)
        store = WorkspaceWorkflowSourceStore(str(tmp_path), lock_timeout_seconds=0.15)
        started = time.monotonic()
        with pytest.raises(WorkflowSourceStorageError) as error:
            store.update(
                SOURCE_PATH,
                expected_storage_revision=first.storage_revision,
                expected_storage_digest=first.storage_digest,
                semantic_change_validated=True,
                source="must-not-commit",
            )
        elapsed = time.monotonic() - started
        assert error.value.code == "workflow_source_unavailable"
        assert elapsed < 2

        release.set()
        process.join(timeout=10)
        assert not process.is_alive()
        assert process.exitcode == 0
        assert results.get(timeout=5) == ("released",)
        time.sleep(0.05)
        assert WorkspaceWorkflowSourceStore(str(tmp_path)).read(SOURCE_PATH) == first
    finally:
        release.set()
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)


def test_external_historical_byte_rollback_fails_closed(tmp_path):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    first = store.create(SOURCE_PATH, "first")
    second = store.update(
        SOURCE_PATH,
        expected_storage_revision=first.storage_revision,
        expected_storage_digest=first.storage_digest,
        semantic_change_validated=True,
        source="second",
    )
    assert second.storage_revision == 2

    (tmp_path / SOURCE_PATH).write_text("first", encoding="utf-8")

    with pytest.raises(WorkflowSourceStorageError) as error:
        store.read(SOURCE_PATH)
    assert error.value.code == "workflow_source_integrity"


def test_external_head_and_source_rollback_cannot_rewind_journal(tmp_path):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    first = store.create(SOURCE_PATH, "first")
    metadata = _metadata_path(tmp_path)
    first_head = (metadata / "head.json").read_bytes()
    store.update(
        SOURCE_PATH,
        expected_storage_revision=first.storage_revision,
        expected_storage_digest=first.storage_digest,
        semantic_change_validated=True,
        source="second",
    )

    (tmp_path / SOURCE_PATH).write_text("first", encoding="utf-8")
    (metadata / "head.json").write_bytes(first_head)

    with pytest.raises(WorkflowSourceStorageError) as error:
        store.read(SOURCE_PATH)
    assert error.value.code == "workflow_source_integrity"
    assert "latest journal entry" in str(error.value)


def test_absurd_revision_filename_is_rejected_without_unbounded_range(tmp_path):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    store.create(SOURCE_PATH, "source")
    revisions = _metadata_path(tmp_path) / "revisions"
    (revisions / "99999999999999999999.json").write_text("{}", encoding="utf-8")

    started = time.monotonic()
    with pytest.raises(WorkflowSourceStorageError) as error:
        store.read(SOURCE_PATH)

    assert error.value.code == "workflow_source_integrity"
    assert time.monotonic() - started < 2


def test_sparse_maximum_revision_is_rejected_in_bounded_space(tmp_path):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    store.create(SOURCE_PATH, "source")
    revisions = _metadata_path(tmp_path) / "revisions"
    original = revisions / "00000000000000000001.json"
    original.rename(revisions / "00000000000000100000.json")

    with pytest.raises(WorkflowSourceStorageError) as error:
        store.read(SOURCE_PATH)

    assert error.value.code == "workflow_source_integrity"


def test_failed_definition_replace_preserves_prior_bytes_and_head(
    tmp_path, monkeypatch
):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    first = store.create(SOURCE_PATH, "accepted bytes")
    metadata = _metadata_path(tmp_path)
    original_head = (metadata / "head.json").read_bytes()
    original_atomic_write = store._atomic_write

    def fail_definition(path, content):
        if path.name.endswith(".workflow.wflow") and content == b"new bytes":
            raise OSError("simulated interrupted replace")
        original_atomic_write(path, content)

    monkeypatch.setattr(store, "_atomic_write", fail_definition)
    with pytest.raises(WorkflowSourceStorageError) as error:
        store.update(
            SOURCE_PATH,
            expected_storage_revision=first.storage_revision,
            expected_storage_digest=first.storage_digest,
            semantic_change_validated=True,
            source="new bytes",
        )
    assert error.value.code == "workflow_source_unavailable"

    assert (tmp_path / SOURCE_PATH).read_bytes() == b"accepted bytes"
    assert (metadata / "head.json").read_bytes() == original_head
    assert not (metadata / "revisions" / "00000000000000000002.json").exists()
    assert store.read(SOURCE_PATH) == first


def test_failed_head_replace_rolls_back_source_and_uncommitted_journal(
    tmp_path, monkeypatch
):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    first = store.create(SOURCE_PATH, "accepted bytes")
    metadata = _metadata_path(tmp_path)
    original_head = (metadata / "head.json").read_bytes()
    original_atomic_write = store._atomic_write

    def fail_head(path, content):
        if path.name == "head.json" and b'"storage_revision":2' in content:
            raise OSError("simulated head failure")
        original_atomic_write(path, content)

    monkeypatch.setattr(store, "_atomic_write", fail_head)
    with pytest.raises(WorkflowSourceStorageError) as error:
        store.update(
            SOURCE_PATH,
            expected_storage_revision=first.storage_revision,
            expected_storage_digest=first.storage_digest,
            semantic_change_validated=True,
            source="new bytes",
        )
    assert error.value.code == "workflow_source_unavailable"

    assert (tmp_path / SOURCE_PATH).read_bytes() == b"accepted bytes"
    assert (metadata / "head.json").read_bytes() == original_head
    assert not (metadata / "revisions" / "00000000000000000002.json").exists()
    assert store.read(SOURCE_PATH) == first


def test_failed_initial_journal_write_leaves_creation_retryable(tmp_path, monkeypatch):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    original_write_once = store._write_once

    def fail_journal(path, content):
        raise OSError("simulated journal failure")

    monkeypatch.setattr(store, "_write_once", fail_journal)
    with pytest.raises(WorkflowSourceStorageError) as error:
        store.create(SOURCE_PATH, "source")
    assert error.value.code == "workflow_source_unavailable"

    assert not (tmp_path / SOURCE_PATH).exists()
    monkeypatch.setattr(store, "_write_once", original_write_once)
    created = store.create(SOURCE_PATH, "source")
    assert created.storage_revision == 1
    assert store.read(SOURCE_PATH) == created


def test_committed_journal_entry_has_no_overwrite_path(tmp_path):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    store.create(SOURCE_PATH, "source")
    record = _metadata_path(tmp_path) / "revisions" / "00000000000000000001.json"
    original = record.read_bytes()

    with pytest.raises(WorkflowSourceStorageError) as error:
        store._write_once(record, b"replacement")

    assert error.value.code == "workflow_source_integrity"
    assert record.read_bytes() == original


@pytest.mark.parametrize(
    "slug",
    [
        "con",
        "aux",
        "nul",
        "prn",
        *(f"com{index}" for index in range(1, 10)),
        *(f"lpt{index}" for index in range(1, 10)),
    ],
)
def test_source_path_rejects_windows_reserved_slugs_on_every_host(tmp_path, slug):
    with pytest.raises(WorkflowSourceStorageError) as error:
        WorkspaceWorkflowSourceStore(str(tmp_path)).create(
            f"workflows/{slug}.workflow.wflow", "source"
        )
    assert error.value.code == "workflow_source_path_invalid"


@pytest.mark.parametrize(
    "path",
    [
        "mounting-bracket.workflow.wflow",
        "workflows/../outside.workflow.wflow",
        "C:/workflows/bracket.workflow.wflow",
        "/workflows/bracket.workflow.wflow",
        "workflows/bracket.wflow",
        "workflows/bracket.workflow.json",
        "workflows/Two Words.workflow.wflow",
    ],
)
def test_source_path_rejects_unscoped_traversal_absolute_and_wrong_extension(
    tmp_path, path
):
    with pytest.raises(WorkflowSourceStorageError) as error:
        WorkspaceWorkflowSourceStore(str(tmp_path)).create(path, "source")
    assert error.value.code == "workflow_source_path_invalid"


def test_source_rejects_symlink_escape(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    workflows = tmp_path / "workflows"
    workflows.mkdir()
    try:
        (workflows / "linked.workflow.wflow").symlink_to(outside / "source.wflow")
    except OSError as error:
        pytest.skip(f"Host cannot create symlinks: {error}")

    with pytest.raises(WorkflowSourceStorageError) as error:
        WorkspaceWorkflowSourceStore(str(tmp_path)).create(
            "workflows/linked.workflow.wflow", "source"
        )
    assert error.value.code == "workflow_source_path_invalid"


def test_metadata_parent_retarget_is_rejected_before_out_of_root_mutation(
    tmp_path, monkeypatch
):
    wright = tmp_path / ".wright"
    wright.mkdir()
    outside_target = tmp_path.parent / f"{tmp_path.name}-outside-target"
    outside_moved = tmp_path.parent / f"{tmp_path.name}-outside-moved"
    outside_target.mkdir()
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    attempted = False

    def retarget(target: Path) -> None:
        nonlocal attempted
        if attempted or target != wright / "workflow-sources":
            return
        attempted = True
        try:
            wright.rename(outside_moved)
        except OSError:
            # Windows directory capabilities intentionally deny this rename.
            return
        try:
            wright.symlink_to(outside_target, target_is_directory=True)
        except OSError:
            outside_moved.rename(wright)

    monkeypatch.setattr(store, "_before_filesystem_mutation", retarget)
    try:
        store.create(SOURCE_PATH, "source")
    except WorkflowSourceStorageError as error:
        assert error.code in {
            "workflow_source_path_invalid",
            "workflow_source_unavailable",
        }

    assert attempted
    assert list(outside_target.iterdir()) == []
    if outside_moved.exists():
        assert not (outside_moved / "workflow-sources").exists()


def test_visible_source_parent_retarget_cannot_redirect_atomic_replace(
    tmp_path, monkeypatch
):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    first = store.create(SOURCE_PATH, "base")
    workflows = tmp_path / "workflows"
    outside_target = tmp_path.parent / f"{tmp_path.name}-outside-source-target"
    outside_moved = tmp_path.parent / f"{tmp_path.name}-outside-source-moved"
    outside_target.mkdir()
    attempted = False

    def retarget(target: Path) -> None:
        nonlocal attempted
        if attempted or target != tmp_path / SOURCE_PATH:
            return
        attempted = True
        try:
            workflows.rename(outside_moved)
        except OSError:
            # Windows directory capabilities intentionally deny this rename.
            return
        try:
            workflows.symlink_to(outside_target, target_is_directory=True)
        except OSError:
            outside_moved.rename(workflows)

    monkeypatch.setattr(store, "_before_filesystem_mutation", retarget)
    try:
        updated = store.update(
            SOURCE_PATH,
            expected_storage_revision=first.storage_revision,
            expected_storage_digest=first.storage_digest,
            semantic_change_validated=True,
            source="changed",
        )
        assert updated.source == "changed"
    except WorkflowSourceStorageError as error:
        assert error.code in {
            "workflow_source_path_invalid",
            "workflow_source_unavailable",
        }

    assert attempted
    assert list(outside_target.iterdir()) == []
    if outside_moved.exists():
        assert (outside_moved / Path(SOURCE_PATH).name).read_text(
            encoding="utf-8"
        ) == "base"


def test_lock_file_rejects_dangling_symlink_before_initialization(tmp_path):
    metadata = _metadata_path(tmp_path)
    metadata.mkdir(parents=True)
    outside = tmp_path.parent / f"{tmp_path.name}-outside-lock"
    lock_path = _lock_path(tmp_path)
    try:
        lock_path.symlink_to(outside)
    except OSError as error:
        pytest.skip(f"Host cannot create symlinks: {error}")

    with pytest.raises(WorkflowSourceStorageError) as error:
        WorkspaceWorkflowSourceStore(str(tmp_path)).create(SOURCE_PATH, "source")

    assert error.value.code == "workflow_source_path_invalid"
    assert not outside.exists()


def test_lock_file_rejects_hardlink_without_modifying_other_name(tmp_path):
    metadata = _metadata_path(tmp_path)
    metadata.mkdir(parents=True)
    outside = tmp_path.parent / f"{tmp_path.name}-outside-hardlink"
    outside.write_bytes(b"sentinel")
    try:
        os.link(outside, _lock_path(tmp_path))
    except OSError as error:
        pytest.skip(f"Host cannot create hardlinks: {error}")

    with pytest.raises(WorkflowSourceStorageError) as error:
        WorkspaceWorkflowSourceStore(str(tmp_path)).create(SOURCE_PATH, "source")

    assert error.value.code == "workflow_source_path_invalid"
    assert outside.read_bytes() == b"sentinel"


def test_lock_file_rejects_non_regular_path(tmp_path):
    lock_path = _lock_path(tmp_path)
    lock_path.mkdir(parents=True)

    with pytest.raises(WorkflowSourceStorageError) as error:
        WorkspaceWorkflowSourceStore(str(tmp_path)).create(SOURCE_PATH, "source")

    assert error.value.code == "workflow_source_path_invalid"


def test_source_byte_cap_is_applied_to_utf8_bytes(tmp_path):
    with pytest.raises(WorkflowSourceStorageError) as error:
        WorkspaceWorkflowSourceStore(str(tmp_path)).create(
            SOURCE_PATH,
            "é" * (WORKFLOW_SOURCE_MAX_BYTES // 2 + 1),
        )
    assert error.value.code == "workflow_source_too_large"
    assert not (tmp_path / SOURCE_PATH).exists()


def test_external_oversized_source_is_rejected_by_bounded_read(tmp_path):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    store.create(SOURCE_PATH, "source")
    source_path = tmp_path / SOURCE_PATH
    with source_path.open("r+b") as stream:
        stream.truncate(WORKFLOW_SOURCE_MAX_BYTES + 1)

    with pytest.raises(WorkflowSourceStorageError) as error:
        store.read(SOURCE_PATH)

    assert error.value.code == "workflow_source_too_large"
    assert str(WORKFLOW_SOURCE_MAX_BYTES) in str(error.value)


def test_source_at_exact_byte_cap_remains_readable(tmp_path):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    source = "x" * WORKFLOW_SOURCE_MAX_BYTES

    created = store.create(SOURCE_PATH, source)

    assert store.read(SOURCE_PATH) == created


@pytest.mark.parametrize(
    "relative_path",
    [
        Path("head.json"),
        Path("revisions") / "00000000000000000001.json",
    ],
)
def test_oversized_metadata_is_rejected_by_explicit_cap(tmp_path, relative_path):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    store.create(SOURCE_PATH, "source")
    metadata_path = _metadata_path(tmp_path) / relative_path
    with metadata_path.open("r+b") as stream:
        stream.truncate(WORKFLOW_SOURCE_METADATA_MAX_BYTES + 1)

    with pytest.raises(WorkflowSourceStorageError) as error:
        store.read(SOURCE_PATH)

    assert error.value.code == "workflow_source_integrity"
    assert "metadata limit" in str(error.value)


@pytest.mark.parametrize(
    "payload",
    [
        b'{"schema_version":' + (b"9" * 5000) + b"}",
        b'{"nested":' + (b"[" * 1500) + b"0" + (b"]" * 1500) + b"}",
    ],
)
def test_bounded_malicious_metadata_maps_parser_limits_to_integrity(tmp_path, payload):
    assert len(payload) <= WORKFLOW_SOURCE_METADATA_MAX_BYTES
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    store.create(SOURCE_PATH, "source")
    (_metadata_path(tmp_path) / "head.json").write_bytes(payload)

    with pytest.raises(WorkflowSourceStorageError) as error:
        store.read(SOURCE_PATH)

    assert error.value.code == "workflow_source_integrity"


def test_committed_reads_never_call_unbounded_path_read_bytes(tmp_path, monkeypatch):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    created = store.create(SOURCE_PATH, "source")

    def reject_unbounded_read(_path):
        raise AssertionError("unbounded Path.read_bytes was called")

    monkeypatch.setattr(Path, "read_bytes", reject_unbounded_read)

    assert store.read(SOURCE_PATH) == created


def test_semantic_change_indication_must_be_explicit_boolean(tmp_path):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    created = store.create(SOURCE_PATH, "source")
    with pytest.raises(WorkflowSourceStorageError) as error:
        store.update(
            SOURCE_PATH,
            expected_storage_revision=created.storage_revision,
            expected_storage_digest=created.storage_digest,
            semantic_change_validated=1,  # type: ignore[arg-type]
            source="updated",
        )
    assert error.value.code == "workflow_source_semantic_change_invalid"


def test_raw_filesystem_failure_is_mapped_without_path_leak(tmp_path, monkeypatch):
    store = WorkspaceWorkflowSourceStore(str(tmp_path))

    def fail_write(path, content):
        raise OSError(r"access denied at C:\sensitive\workflow")

    monkeypatch.setattr(store, "_atomic_write", fail_write)
    with pytest.raises(WorkflowSourceStorageError) as error:
        store.create(SOURCE_PATH, "source")

    assert error.value.code == "workflow_source_unavailable"
    assert str(error.value) == "Workflow source storage is unavailable"
    assert "sensitive" not in str(error.value)


@pytest.mark.asyncio
async def test_write_use_case_defers_cancellation_until_worker_finishes(tmp_path):
    started = threading.Event()
    release = threading.Event()
    committed = threading.Event()

    class SlowStore:
        def create(self, path: str, source: str):
            started.set()
            assert release.wait(timeout=5)
            committed.set()
            return "committed"

    executor = BoundedExecutor(max_workers=1)
    use_cases = WorkspaceWorkflowSourceUseCases(
        executor, store_factory=lambda _workspace: SlowStore()
    )
    task = asyncio.create_task(use_cases.create(str(tmp_path), SOURCE_PATH, "source"))
    assert await asyncio.to_thread(started.wait, 2)

    task.cancel()
    await asyncio.sleep(0.05)
    assert not task.done()
    assert not committed.is_set()

    release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert committed.is_set()
    await executor.close()


@pytest.mark.asyncio
async def test_read_use_case_maps_executor_timeout_to_typed_storage_error(tmp_path):
    class TimeoutExecutor:
        async def run(self, operation, work, *, timeout_seconds):
            raise WorkspaceTimeoutError(
                "sensitive internal executor path", operation=operation
            )

    use_cases = WorkspaceWorkflowSourceUseCases(TimeoutExecutor())  # type: ignore[arg-type]
    with pytest.raises(WorkflowSourceStorageError) as error:
        await use_cases.read(str(tmp_path), SOURCE_PATH)

    assert error.value.code == "workflow_source_unavailable"
    assert "sensitive" not in str(error.value)
