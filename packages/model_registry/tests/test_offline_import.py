from __future__ import annotations

import zipfile

import pytest

from fixture_factory import generate_affine_fixture
from model_registry.offline_source import OfflinePackageError, inspect_offline_package


def rewrite_archive(source, target, mutate) -> None:
    with zipfile.ZipFile(source) as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}
    mutate(entries)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, content in entries.items():
            archive.writestr(name, content)


def test_offline_import_returns_only_declared_verified_data(tmp_path) -> None:
    fixture = generate_affine_fixture(tmp_path / "fixture")
    imported = inspect_offline_package(
        fixture.archive_path,
        maximum_archive_bytes=1_000_000,
        maximum_expanded_bytes=1_000_000,
    )
    assert imported.package == fixture.package
    assert imported.artifacts == fixture.artifacts
    assert imported.manifest_digest == fixture.manifest_digest


@pytest.mark.parametrize(
    ("entry", "code"),
    [
        ("../escape.json", "path_unsafe"),
        ("/absolute.json", "path_unsafe"),
        ("nested/archive.zip", "path_unsafe"),
        ("model/extra.json", "undeclared_file"),
    ],
)
def test_offline_import_rejects_paths_nested_archives_and_undeclared_files(
    tmp_path, entry: str, code: str
) -> None:
    fixture = generate_affine_fixture(tmp_path / "fixture")
    changed = tmp_path / "changed.zip"
    rewrite_archive(
        fixture.archive_path, changed, lambda entries: entries.update({entry: b"x"})
    )
    with pytest.raises(OfflinePackageError) as raised:
        inspect_offline_package(changed)
    assert raised.value.code == code


def test_offline_import_rejects_normalization_collision_links_and_executables(
    tmp_path,
) -> None:
    fixture = generate_affine_fixture(tmp_path / "fixture")
    collision = tmp_path / "collision.zip"
    with (
        zipfile.ZipFile(fixture.archive_path) as source,
        zipfile.ZipFile(collision, "w") as target,
    ):
        for info in source.infolist():
            target.writestr(info, source.read(info.filename))
        target.writestr("MODEL/COEFFICIENTS.JSON", b"x")
    with pytest.raises(OfflinePackageError) as raised:
        inspect_offline_package(collision)
    assert raised.value.code == "path_collision"

    for mode, code in ((0o120777, "path_unsafe"), (0o100755, "path_unsafe")):
        changed = tmp_path / f"mode-{mode}.zip"
        with (
            zipfile.ZipFile(fixture.archive_path) as source,
            zipfile.ZipFile(changed, "w") as target,
        ):
            for info in source.infolist():
                replacement = zipfile.ZipInfo(info.filename)
                replacement.create_system = 3
                replacement.external_attr = mode << 16
                target.writestr(replacement, source.read(info.filename))
        with pytest.raises(OfflinePackageError) as raised:
            inspect_offline_package(changed)
        assert raised.value.code == code


def test_offline_import_rejects_size_digest_license_and_manifest_tampering(
    tmp_path,
) -> None:
    fixture = generate_affine_fixture(tmp_path / "fixture")
    for name, mutation, code in (
        (
            "digest",
            lambda entries: entries.__setitem__("model/coefficients.json", b"tampered"),
            "digest_mismatch",
        ),
        (
            "license",
            lambda entries: entries.pop("LICENSE"),
            "undeclared_file",
        ),
        (
            "manifest",
            lambda entries: entries.__setitem__(
                "engineering-model-package.json", b"{}"
            ),
            "manifest_invalid",
        ),
    ):
        changed = tmp_path / f"{name}.zip"
        rewrite_archive(fixture.archive_path, changed, mutation)
        with pytest.raises(OfflinePackageError) as raised:
            inspect_offline_package(changed)
        assert raised.value.code == code

    with pytest.raises(OfflinePackageError) as raised:
        inspect_offline_package(fixture.archive_path, maximum_archive_bytes=1)
    assert raised.value.code == "size_exceeded"
    with pytest.raises(OfflinePackageError) as raised:
        inspect_offline_package(fixture.archive_path, maximum_expanded_bytes=1)
    assert raised.value.code == "size_exceeded"
