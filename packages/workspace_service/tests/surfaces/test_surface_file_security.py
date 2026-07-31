from __future__ import annotations

import os
from pathlib import Path

import pytest

from data_vault import FileVault, SurfacePayloadNotFound, SurfaceVault, VaultPathError
from workspace_service.workspace_path import WorkspacePath


pytestmark = pytest.mark.workspace_surfaces


@pytest.mark.parametrize(
    "hostile",
    [
        "../outside.txt",
        "nested/../../outside.txt",
        "/etc/passwd",
        "C:\\Windows\\win.ini",
        "\\\\server\\share\\secret.txt",
        "//server/share/secret.txt",
        "file.txt:secret-stream",
        "\\?\\C:\\Windows\\win.ini",
    ],
)
def test_workspace_resource_paths_reject_traversal_unc_drive_and_ads(
    tmp_path: Path, hostile: str
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    with pytest.raises(ValueError, match="denied|relative|traversal|stream"):
        WorkspacePath(workspace).resolve(hostile)


def test_symbolic_link_or_reparse_escape_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    link = workspace / "link.txt"
    try:
        link.symlink_to(outside)
    except OSError:
        original_realpath = os.path.realpath

        def fake_realpath(value):
            if os.path.normcase(os.path.abspath(value)) == os.path.normcase(str(link)):
                return str(outside)
            return original_realpath(value)

        monkeypatch.setattr(os.path, "realpath", fake_realpath)
    with pytest.raises(ValueError, match="symbolic links|reparse|escapes"):
        WorkspacePath(workspace).resolve("link.txt")


def test_surface_vault_digest_is_workspace_scoped(tmp_path: Path) -> None:
    vault = SurfaceVault(tmp_path / "surface-vault")
    digest = vault.put(workspace_id="workspace-1", payload=b"private drawing")
    assert vault.get(workspace_id="workspace-1", digest=digest) == b"private drawing"
    with pytest.raises(SurfacePayloadNotFound):
        vault.get(workspace_id="workspace-2", digest=digest)


def test_generated_file_vault_never_accepts_caller_paths(tmp_path: Path) -> None:
    vault = FileVault(tmp_path / "files")
    stored = vault.store("../../drawing.svg", b"<svg/>")
    assert stored.display_name == "drawing.svg"
    assert stored.path.parent == vault.root
    for hostile in ("../drawing.svg", "folder/drawing.svg", "file.txt:ads"):
        with pytest.raises(VaultPathError):
            vault.resolve(hostile)
