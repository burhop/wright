"""Large checkpoint artifacts retain exact approval and continuation authority."""

import hashlib
import os

import pytest

from workspace_service import workspace_file_identity as identity
from workspace_service.adapters.filesystem import LocalWorkspaceFiles
from workspace_service.executor import BoundedExecutor
from workspace_service.use_cases.files import WorkspaceFileUseCases
from workspace_service.workflow_approval_execution import (
    decide_workflow_approval,
    resume_workflow_approval,
)
from workspace_service.workflow_external_actions import WorkflowExternalActionError
from packages.workspace_service.tests.test_workflow_approval_execution import setup_case


@pytest.mark.asyncio
async def test_large_artifact_approves_and_resumes_same_run_with_bounded_file_service(
    tmp_path,
):
    case = await setup_case(tmp_path, package_artifact=b"x" * (4 * 1024 * 1024 + 1))
    executor = BoundedExecutor(max_workers=1)
    files = WorkspaceFileUseCases("", executor, LocalWorkspaceFiles)
    # Keep the fixture's string-to-bytes output adapter; use actual production
    # reads and hashing to exercise the former 4 MiB cap in both restore phases.
    case.services.files.read_reference = files.read_reference
    case.services.files.hash_reference = files.hash_reference
    artifact = next(
        item
        for item in case.checkpoint.continuation["artifact_files"]
        if item["path"].endswith("large-artifact.pdf")
    )
    assert (tmp_path / artifact["path"]).stat().st_size > 4 * 1024 * 1024
    try:
        with pytest.raises(ValueError, match="smaller than 4 MiB"):
            await files.read_reference(str(tmp_path), artifact["path"])
        assert (
            await files.hash_reference(str(tmp_path), artifact["path"])
            == artifact["sha256"]
        )
        approved = await decide_workflow_approval(
            **case.args, decision="approved", auto=True
        )
        assert approved.state == "approved"
        checkpoint, result = await resume_workflow_approval(
            **case.args,
            request_id="large-artifact-first-resume",
            response_generator=case.generate,
        )
        assert result["status"] == "completed"
        assert result["run_id"] == case.result["run_id"]
        assert checkpoint.external_action["outcome"] == "dispatched"
        assert len(case.calls) == 1 and len(case.tool_calls) == 1
        assert (
            tmp_path / "outputs/attempt/after.txt"
        ).read_text() == "Final generated report"
    finally:
        await executor.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("when", ["before_decision", "before_resume"])
async def test_large_artifact_change_still_blocks_authority(tmp_path, when):
    case = await setup_case(tmp_path, package_artifact=b"x" * (4 * 1024 * 1024 + 1))
    if when == "before_resume":
        await decide_workflow_approval(**case.args, decision="approved", auto=True)
    path = tmp_path / "outputs/attempt/large-artifact.pdf"
    with path.open("r+b") as stream:
        stream.seek(-2, 2)
        stream.write(b"y")
    with pytest.raises(WorkflowExternalActionError, match="changed"):
        if when == "before_decision":
            await decide_workflow_approval(**case.args, decision="approved", auto=True)
        else:
            await resume_workflow_approval(
                **case.args,
                request_id="must-not-dispatch",
                response_generator=case.generate,
            )
    checkpoint = case.services.workflow_external_actions.lookup(
        case.checkpoint.checkpoint_id
    )
    assert checkpoint.state == ("pending" if when == "before_decision" else "approved")
    assert checkpoint.external_action is None
    assert len(case.calls) == 0 and len(case.tool_calls) == 1
    assert not (tmp_path / "outputs/attempt/after.txt").exists()


@pytest.mark.parametrize(
    "path", ["../outside.pdf", "C:/outside.pdf", "file.pdf:stream", "missing.pdf"]
)
def test_identity_rejects_unavailable_or_unconfined_path(tmp_path, path):
    with pytest.raises((OSError, ValueError)):
        identity.workspace_file_sha256(str(tmp_path), path)


def test_identity_rejects_oversize_without_reading_contents(tmp_path, monkeypatch):
    (tmp_path / "file.pdf").write_bytes(b"123456789")
    monkeypatch.setattr(identity, "MAX_IDENTITY_BYTES", 8)
    with pytest.raises(ValueError, match="exceeds"):
        identity.workspace_file_sha256(str(tmp_path), "file.pdf")


def test_identity_rejects_directory_before_opening(tmp_path):
    (tmp_path / "folder").mkdir()
    with pytest.raises(ValueError, match="regular"):
        identity.workspace_file_sha256(str(tmp_path), "folder")


def test_identity_rejects_symlink(tmp_path):
    (tmp_path / "actual.pdf").write_bytes(b"actual")
    try:
        (tmp_path / "link.pdf").symlink_to(tmp_path / "actual.pdf")
    except OSError as error:
        pytest.skip(f"This host cannot create test symlinks: {error}")
    with pytest.raises(ValueError, match="symbolic links"):
        identity.workspace_file_sha256(str(tmp_path), "link.pdf")


def test_identity_rejects_write_during_chunk_hashing(tmp_path, monkeypatch):
    target = tmp_path / "file.pdf"
    target.write_bytes(b"x" * (2 * 1024 * 1024))
    real_sha256 = hashlib.sha256

    class ChangingDigest:
        def __init__(self):
            self.digest = real_sha256()
            self.changed = False

        def update(self, chunk):
            self.digest.update(chunk)
            if not self.changed:
                self.changed = True
                target.write_bytes(b"truncated concurrently")

    monkeypatch.setattr(identity.hashlib, "sha256", ChangingDigest)
    with pytest.raises(ValueError, match="changed"):
        identity.workspace_file_sha256(str(tmp_path), "file.pdf")


def test_identity_rejects_same_size_timestamp_replacement_after_read(
    tmp_path, monkeypatch
):
    target, replacement = tmp_path / "file.pdf", tmp_path / "new.pdf"
    target.write_bytes(b"original")
    replacement.write_bytes(b"replaced")
    original_stat = target.stat()
    os.utime(replacement, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
    real_resolve = identity.WorkspacePath.resolve
    resolves = 0

    def resolve(paths, path, **kwargs):
        nonlocal resolves
        resolves += 1
        if resolves == 2:
            replacement.replace(target)
        return real_resolve(paths, path, **kwargs)

    monkeypatch.setattr(identity.WorkspacePath, "resolve", resolve)
    with pytest.raises(ValueError, match="changed"):
        identity.workspace_file_sha256(str(tmp_path), "file.pdf")


def test_file_identity_returns_only_exact_digest(tmp_path):
    data = b"binary\x00data\xff"
    (tmp_path / "file.pdf").write_bytes(data)
    assert (
        identity.workspace_file_sha256(str(tmp_path), "file.pdf")
        == hashlib.sha256(data).hexdigest()
    )
