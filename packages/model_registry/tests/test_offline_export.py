from __future__ import annotations

import zipfile

import pytest
from fixture_factory import generate_affine_fixture
from model_registry import ModelPackage
from model_registry.offline_source import (
    OfflinePackageError,
    export_offline_package,
    inspect_offline_package,
)


def test_public_export_is_deterministic_and_reimports_in_a_fresh_root(tmp_path) -> None:
    fixture = generate_affine_fixture(tmp_path / "fixture")
    first = tmp_path / "first.wright-model.zip"
    second = tmp_path / "second.wright-model.zip"

    first_result = export_offline_package(fixture.package, fixture.artifacts, first)
    second_result = export_offline_package(fixture.package, fixture.artifacts, second)

    assert first.read_bytes() == second.read_bytes()
    assert first_result.archive_sha256 == second_result.archive_sha256
    assert first_result.size == first.stat().st_size
    imported = inspect_offline_package(first)
    assert imported.package.digest == fixture.package.digest
    assert imported.artifacts == fixture.artifacts
    with zipfile.ZipFile(first) as archive:
        assert archive.namelist() == sorted(archive.namelist())


def test_export_rejects_private_or_nonredistributable_material(tmp_path) -> None:
    fixture = generate_affine_fixture(tmp_path / "fixture")
    private_document = fixture.package.model_dump(mode="json")
    private_document["source"]["access"] = "private"
    private = ModelPackage.model_validate(private_document)
    with pytest.raises(OfflinePackageError) as private_error:
        export_offline_package(private, fixture.artifacts, tmp_path / "private.zip")
    assert private_error.value.code == "export_forbidden"

    restricted_document = fixture.package.model_dump(mode="json")
    restricted_document["variants"][0]["artifacts"][0]["redistributable"] = False
    restricted = ModelPackage.model_validate(restricted_document)
    with pytest.raises(OfflinePackageError) as restricted_error:
        export_offline_package(
            restricted, fixture.artifacts, tmp_path / "restricted.zip"
        )
    assert restricted_error.value.code == "export_forbidden"
    assert not (tmp_path / "restricted.zip").exists()
