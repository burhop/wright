from __future__ import annotations

import zipfile
import hashlib
import json

import pytest
from fixture_factory import generate_affine_fixture
from model_registry import ModelPackage
from model_registry.generated import (
    chatter_fixture_artifacts,
    generated_chatter_package,
)
from model_registry.models import canonical_json
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


def _private_archive(path, package, artifacts) -> None:
    manifest = canonical_json(
        package.model_dump(mode="json", exclude_none=True)
    ).encode()
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, value in sorted(
            {**artifacts, "engineering-model-package.json": manifest}.items()
        ):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = 0o100600 << 16
            archive.writestr(info, value)


def test_private_chatter_import_requires_exact_current_parity_evidence(
    tmp_path,
) -> None:
    package = generated_chatter_package()
    artifacts = chatter_fixture_artifacts(package)
    archive = tmp_path / "chatter.wright-model.zip"
    _private_archive(archive, package, artifacts)
    inspected = inspect_offline_package(archive)
    assert inspected.package.digest == package.digest
    assert inspected.artifacts == artifacts
    with pytest.raises(OfflinePackageError) as forbidden:
        export_offline_package(package, artifacts, tmp_path / "export.zip")
    assert forbidden.value.code == "export_forbidden"

    changed = dict(artifacts)
    parity = json.loads(changed["evidence/conversion-parity.json"])
    parity["source_identity"]["dataset_digest"] = "f" * 64
    changed["evidence/conversion-parity.json"] = canonical_json(parity).encode()
    document = package.model_dump(mode="json")
    declaration = next(
        item
        for item in document["variants"][0]["artifacts"]
        if item["path"] == "evidence/conversion-parity.json"
    )
    declaration["size"] = len(changed["evidence/conversion-parity.json"])
    declaration["sha256"] = hashlib.sha256(
        changed["evidence/conversion-parity.json"]
    ).hexdigest()
    stale = ModelPackage.model_validate(document)
    stale_archive = tmp_path / "stale.wright-model.zip"
    _private_archive(stale_archive, stale, changed)
    with pytest.raises(OfflinePackageError) as stale_error:
        inspect_offline_package(stale_archive)
    assert stale_error.value.code == "parity_invalid"
