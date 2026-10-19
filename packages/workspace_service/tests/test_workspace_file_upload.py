"""Real confined atomic input staging; uploads never overwrite existing bytes."""

import asyncio
import hashlib

import pytest
import pytest_asyncio

from workspace_service.adapters.filesystem import LocalWorkspaceFiles
from workspace_service.adapters.runtime import WorkspaceManager
from workspace_service.executor import BoundedExecutor
from workspace_service.use_cases.files import WorkspaceFileUseCases


@pytest_asyncio.fixture
async def staging(tmp_path):
    WorkspaceManager(str(tmp_path))
    executor = BoundedExecutor(max_workers=8)
    owner = WorkspaceFileUseCases(
        str(tmp_path / "unused.db"), executor, LocalWorkspaceFiles
    )
    yield owner, tmp_path
    await executor.close()


@pytest.mark.asyncio
async def test_simultaneous_identical_uploads_publish_one_complete_copy(staging):
    owner, root = staging
    content = b"ISO-10303-21;\x00\xff\n" * 1000
    digest = hashlib.sha256(content).hexdigest()
    (root / "existing.step").write_bytes(b"existing engineering evidence")
    paths = await asyncio.gather(
        *(
            owner.stage_upload(str(root), "plate.step", content, digest)
            for _ in range(8)
        )
    )
    assert set(paths) == {f"uploads/{digest}/plate.step"}
    assert (root / paths[0]).read_bytes() == content
    assert len(list((root / "uploads").rglob("*.step"))) == 1
    assert not list(root.rglob(".wright-output-*"))
    assert (root / "existing.step").read_bytes() == b"existing engineering evidence"


@pytest.mark.asyncio
async def test_changed_saved_bytes_are_never_overwritten(staging):
    owner, root = staging
    content = b"time,position\n0,1\n"
    digest = hashlib.sha256(content).hexdigest()
    path = await owner.stage_upload(str(root), "telemetry.csv", content, digest)
    (root / path).write_bytes(b"changed after upload")
    with pytest.raises(FileExistsError):
        await owner.stage_upload(str(root), "telemetry.csv", content, digest)
    assert (root / path).read_bytes() == b"changed after upload"
    assert len(list((root / "uploads").rglob("*.csv"))) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name",
    [
        "../escape",
        "/absolute",
        "C:\\file",
        ".env",
        "bad:stream",
        "a/b",
        "bad\nname",
        "trailing.",
        " name.txt",
        "NUL.txt",
        "COM1.csv",
        "bad?.step",
    ],
)
async def test_invalid_names_do_not_publish(staging, name):
    owner, root = staging
    with pytest.raises(ValueError):
        await owner.stage_upload(
            str(root), name, b"data", hashlib.sha256(b"data").hexdigest()
        )
    assert not (root / "uploads").exists()


@pytest.mark.asyncio
async def test_byte_bound_digest_and_link_confinement(staging, tmp_path):
    owner, root = staging
    for content, digest in [
        (b"", hashlib.sha256(b"").hexdigest()),
        (b"x" * (16 * 1024 * 1024 + 1), "a" * 64),
        (b"actual", "a" * 64),
    ]:
        with pytest.raises(ValueError):
            await owner.stage_upload(str(root), "input.txt", content, digest)
    outside = tmp_path.parent / (tmp_path.name + "-outside")
    outside.mkdir()
    (root / "uploads").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        await owner.stage_upload(
            str(root), "input.txt", b"actual", hashlib.sha256(b"actual").hexdigest()
        )
    assert not list(outside.iterdir())
