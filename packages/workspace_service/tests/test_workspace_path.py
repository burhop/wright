import pytest

from workspace_service.workspace_path import WorkspacePath


@pytest.mark.parametrize(
    "unsafe",
    [
        "../outside",
        "/tmp/outside",
        r"C:\\outside",
        "C:outside",
        r"\\server\\share\\x",
        r"\\?\\C:\\x",
        "file:stream",
    ],
)
def test_rejects_traversal_absolute_windows_and_unc_paths(tmp_path, unsafe):
    capability = WorkspacePath(tmp_path / "workspace")
    with pytest.raises(ValueError):
        capability.resolve(unsafe)


def test_scratch_is_workspace_local(tmp_path):
    capability = WorkspacePath(tmp_path / "workspace")
    assert (
        capability.scratch("render/out.stl")
        == capability.root / ".wright" / "tmp" / "render" / "out.stl"
    )


def test_rejects_symlink_escape(tmp_path):
    capability = WorkspacePath(tmp_path / "workspace")
    outside = tmp_path / "outside"
    outside.mkdir()
    link = capability.root / "linked"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"Host cannot create test symlink: {error}")
    with pytest.raises(ValueError, match="symbolic links"):
        capability.resolve("linked/secret.txt")


def test_backup_ids_are_fixed_format(tmp_path):
    capability = WorkspacePath(tmp_path / "workspace")
    valid = "a" * 64
    assert capability.backup(valid) == capability.root / ".git" / "backups" / valid
    for invalid in ("../outside", "A" * 64, "a" * 63, "/" + valid):
        with pytest.raises(ValueError, match="backup ID"):
            capability.backup(invalid)
