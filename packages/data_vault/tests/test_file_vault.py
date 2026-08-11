from pathlib import Path

import pytest

from data_vault import FileVault, VaultPathError


def test_store_uses_generated_key_not_client_path(tmp_path: Path):
    vault = FileVault(tmp_path / "vault")

    stored = vault.store("../../outside.PDF", b"pdf-data")

    assert stored.display_name == "outside.PDF"
    assert stored.storage_key.endswith(".pdf")
    assert "outside" not in stored.storage_key
    assert "/" not in stored.storage_key
    assert "\\" not in stored.storage_key
    assert stored.path.parent == (tmp_path / "vault").resolve()
    assert stored.path.read_bytes() == b"pdf-data"
    assert not (tmp_path / "outside.PDF").exists()


def test_resolve_file_id_finds_stored_file_without_client_suffix(tmp_path: Path):
    vault = FileVault(tmp_path / "vault")
    stored = vault.store("clipboard.png", b"image-data")

    assert vault.resolve_file_id(stored.file_id) == stored.path


def test_resolve_file_id_rejects_non_uuid(tmp_path: Path):
    vault = FileVault(tmp_path / "vault")

    with pytest.raises(VaultPathError):
        vault.resolve_file_id("../not-an-upload")


@pytest.mark.parametrize(
    "name",
    [
        "../secret.txt",
        "..\\secret.txt",
        "/etc/passwd",
        r"C:\Windows\win.ini",
        r"\\server\share\secret.txt",
        "prefix/../secret.txt",
        "secret\x00.txt",
        ".",
        "..",
    ],
)
def test_resolve_rejects_non_basename_and_ambiguous_names(tmp_path: Path, name: str):
    vault = FileVault(tmp_path / "vault")

    with pytest.raises(VaultPathError):
        vault.resolve(name)


def test_resolve_reads_confined_legacy_file(tmp_path: Path):
    root = tmp_path / "vault"
    root.mkdir()
    legacy = root / "123e4567_legacy model.step"
    legacy.write_bytes(b"step")

    resolved = FileVault(root).resolve(legacy.name)

    assert resolved == legacy.resolve()


def test_resolve_rejects_sibling_prefix_traversal(tmp_path: Path):
    root = tmp_path / "vault"
    sibling = tmp_path / "vault-evil"
    root.mkdir()
    sibling.mkdir()
    (sibling / "secret.txt").write_text("secret", encoding="utf-8")

    with pytest.raises(VaultPathError):
        FileVault(root).resolve("../vault-evil/secret.txt")


def test_resolve_rejects_symlink_to_outside(tmp_path: Path):
    root = tmp_path / "vault"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    link = root / "linked.txt"
    try:
        link.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"host cannot create symlinks: {exc}")

    with pytest.raises(VaultPathError):
        FileVault(root).resolve(link.name)


def test_store_drops_unsafe_or_excessive_extension(tmp_path: Path):
    vault = FileVault(tmp_path / "vault")

    stored = vault.store("payload." + "x" * 40, b"data")

    assert "." not in stored.storage_key
