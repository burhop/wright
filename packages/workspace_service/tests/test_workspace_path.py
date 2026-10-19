import ntpath
import os
import stat
from pathlib import PureWindowsPath
from types import SimpleNamespace

import pytest

import workspace_service.workspace_path as workspace_path_module
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
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    capability = WorkspacePath(workspace)
    with pytest.raises(ValueError):
        capability.resolve(unsafe)


def test_scratch_is_workspace_local(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    capability = WorkspacePath(workspace)
    assert (
        capability.scratch("render/out.stl")
        == capability.root / ".wright" / "tmp" / "render" / "out.stl"
    )


def test_rejects_symlink_escape(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    capability = WorkspacePath(workspace)
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
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    capability = WorkspacePath(workspace)
    valid = "a" * 64
    assert capability.backup(valid) == capability.root / ".git" / "backups" / valid
    for invalid in ("../outside", "A" * 64, "a" * 63, "/" + valid):
        with pytest.raises(ValueError, match="backup ID"):
            capability.backup(invalid)


def test_capability_construction_does_not_create_workspace(tmp_path):
    workspace = tmp_path / "workspace"

    capability = WorkspacePath(workspace)

    assert capability.root == workspace.resolve()
    assert not workspace.exists()


@pytest.fixture
def windows_capability(monkeypatch, request):
    """Exercise the Windows spelling contract on every host, with explicit metadata."""
    metadata = {}

    class WindowsPathFixture(PureWindowsPath):
        def lstat(self):
            observed = metadata.get(ntpath.normcase(str(self)))
            if isinstance(observed, Exception):
                raise observed
            if observed is not None:
                return observed
            if self.name == "plate.step":
                raise FileNotFoundError(str(self))
            return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0)

        def exists(self):
            return self.name != "plate.step"

    def prefixed_realpath(value):
        value = ntpath.normpath(str(value))
        if value.startswith("\\\\"):
            return "\\\\?\\UNC\\" + value[2:]
        return "\\\\?\\" + value

    paths = SimpleNamespace(
        normpath=ntpath.normpath,
        normcase=ntpath.normcase,
        join=ntpath.join,
        realpath=prefixed_realpath,
    )
    host = SimpleNamespace(name="nt", path=paths, sep="\\")
    monkeypatch.setattr(workspace_path_module, "os", host)
    monkeypatch.setattr(workspace_path_module, "Path", WindowsPathFixture)
    capability = WorkspacePath.__new__(WorkspacePath)
    capability.root = WindowsPathFixture(getattr(request, "param", r"C:\workspace"))
    return capability, metadata, host


@pytest.mark.parametrize(
    "windows_capability", [r"C:\workspace", r"\\server\share\workspace"], indirect=True
)
def test_windows_namespace_spelling_preserves_the_exact_relative_subject(
    windows_capability,
):
    capability, _, _ = windows_capability

    target = capability.resolve("uploads/plate.step")

    assert target == capability.root / "uploads" / "plate.step"
    assert target.relative_to(capability.root).as_posix() == "uploads/plate.step"
    with pytest.raises(FileNotFoundError):
        capability.resolve("uploads/plate.step", must_exist=True)


@pytest.mark.parametrize(
    "mode,attributes",
    [(stat.S_IFLNK, 0), (stat.S_IFDIR, stat.FILE_ATTRIBUTE_REPARSE_POINT)],
)
@pytest.mark.parametrize("location", ["ancestor", "root", "parent", "target"])
def test_windows_namespace_spelling_still_rejects_existing_links(
    windows_capability, mode, attributes, location
):
    capability, metadata, _ = windows_capability
    component = {
        "ancestor": capability.root.parent,
        "root": capability.root,
        "parent": capability.root / "uploads",
        "target": capability.root / "uploads" / "plate.step",
    }[location]
    metadata[ntpath.normcase(str(component))] = SimpleNamespace(
        st_mode=mode, st_file_attributes=attributes
    )

    with pytest.raises(ValueError, match="symbolic links|reparse"):
        capability.resolve("uploads/plate.step")


@pytest.mark.parametrize(
    "resolved",
    [
        r"\\?\C:\outside\plate.step",
        r"\\?\C:\workspace\uploads\different.step",
        r"\\.\C:\workspace\uploads\plate.step",
        r"\\?\GLOBALROOT\Device\HarddiskVolume1\workspace\uploads\plate.step",
        r"\\?\Volume{00000000-0000-0000-0000-000000000000}\uploads\plate.step",
        r"\\?\C:\workspace\uploads\plate.step.",
    ],
)
def test_windows_namespace_compatibility_never_accepts_another_subject(
    windows_capability, resolved
):
    capability, _, host = windows_capability
    host.path.realpath = lambda _: resolved

    with pytest.raises(ValueError, match="symbolic links|reparse|escapes"):
        capability.resolve("uploads/plate.step")


def test_windows_namespace_validation_does_not_ignore_metadata_denial(
    windows_capability,
):
    capability, metadata, _ = windows_capability
    metadata[ntpath.normcase(str(capability.root / "uploads"))] = PermissionError(
        "Metadata denied"
    )

    with pytest.raises(PermissionError, match="Metadata denied"):
        capability.resolve("uploads/plate.step")


def test_windows_namespace_compatibility_does_not_change_posix_semantics(
    windows_capability,
):
    capability, _, host = windows_capability
    host.name = "posix"

    with pytest.raises(ValueError, match="symbolic links|reparse"):
        capability.resolve("uploads/plate.step")


@pytest.mark.skipif(os.name != "nt", reason="Requires the actual Windows path API")
def test_windows_parent_creation_during_realpath_preserves_upload_path(
    tmp_path, monkeypatch
):
    """A second writer creates parents after ERROR_PATH_NOT_FOUND, not the file."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    capability = WorkspacePath(workspace)
    target = capability.root / "uploads" / "fresh" / "plate.step"
    original = ntpath._getfinalpathname
    target_identity = ntpath.normcase(str(target))
    errors = []
    created = False

    def interleaved_final_name(value):
        nonlocal created
        try:
            return original(value)
        except FileNotFoundError as error:
            if ntpath.normcase(str(value)) == target_identity:
                errors.append(error.winerror)
                if not created:
                    assert error.winerror == 3  # ERROR_PATH_NOT_FOUND
                    target.parent.mkdir(parents=True)
                    created = True
            raise

    monkeypatch.setattr(ntpath, "_getfinalpathname", interleaved_final_name)

    assert capability.resolve("uploads/fresh/plate.step") == target
    assert created and errors[0] == 3 and 2 in errors[1:]
    assert target.parent.is_dir() and not target.exists()
