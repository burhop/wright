from __future__ import annotations

import json
import zipfile

from fixture_factory import generate_affine_fixture


def test_affine_fixture_is_deterministic_bounded_and_self_describing(tmp_path) -> None:
    first = generate_affine_fixture(tmp_path / "first", revision=2)
    second = generate_affine_fixture(tmp_path / "second", revision=2)

    assert first.manifest_digest == second.manifest_digest
    assert first.archive_path.read_bytes() == second.archive_path.read_bytes()
    assert first.package.package_revision == 2
    assert first.package.variant("json-cpu-f64").resources.download_bytes == sum(
        len(value) for value in first.artifacts.values()
    )

    with zipfile.ZipFile(first.archive_path) as archive:
        assert archive.namelist() == sorted(
            [*first.artifacts, "engineering-model-package.json"]
        )
        manifest = json.loads(archive.read("engineering-model-package.json"))
    assert manifest == first.package.model_dump(mode="json", exclude_none=True)


def test_affine_fixture_revision_changes_identity_and_expected_value(tmp_path) -> None:
    first = generate_affine_fixture(tmp_path / "first", revision=1)
    second = generate_affine_fixture(
        tmp_path / "second", revision=2, scale=3.0, offset=-1.0
    )

    assert first.manifest_digest != second.manifest_digest
    assert first.artifact_set_digest != second.artifact_set_digest
    vector = second.package.variant("json-cpu-f64").test_vectors[0]
    assert vector.expected.value == {"y": 5.0}


def test_affine_fixture_rejects_unsafe_or_unbounded_generation_root(tmp_path) -> None:
    target = tmp_path / "fixture"
    generate_affine_fixture(target)

    try:
        generate_affine_fixture(target)
    except FileExistsError as error:
        assert "empty" in str(error)
    else:  # pragma: no cover - fail with a focused contract message
        raise AssertionError("fixture generation unexpectedly reused mutable state")
