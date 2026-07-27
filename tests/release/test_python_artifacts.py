from pathlib import Path
import tarfile
import zipfile

import pytest

from scripts.release.python_artifacts import (
    ArtifactPolicyError,
    artifact_evidence,
    ensure_public_distribution,
    inspect_archive,
)


def test_zip_artifact_has_deterministic_manifest(tmp_path: Path) -> None:
    artifact = tmp_path / "wright_engineering-0.1.0-py3-none-any.whl"
    with zipfile.ZipFile(artifact, "w") as archive:
        archive.writestr("wright_engineering/__init__.py", "__version__='0.1.0'\n")
        archive.writestr(
            "wright_engineering-0.1.0.dist-info/METADATA", "Name: wright-engineering\n"
        )
    evidence, manifest = artifact_evidence(artifact)
    assert evidence.kind == "wheel"
    assert "wright_engineering/__init__.py" in manifest
    assert len(evidence.sha256) == 64


def test_archive_rejects_traversal_and_forbidden_content(tmp_path: Path) -> None:
    artifact = tmp_path / "bad.whl"
    with zipfile.ZipFile(artifact, "w") as archive:
        archive.writestr("../token", "secret")
    with pytest.raises(ArtifactPolicyError, match="unsafe"):
        inspect_archive(artifact)
    artifact.unlink()
    with zipfile.ZipFile(artifact, "w") as archive:
        archive.writestr("specs/private.md", "bad")
    with pytest.raises(ArtifactPolicyError, match="forbidden"):
        inspect_archive(artifact)


def test_tar_artifact_rejects_symlink(tmp_path: Path) -> None:
    artifact = tmp_path / "bad.tar.gz"
    with tarfile.open(artifact, "w:gz") as archive:
        info = tarfile.TarInfo("wright/link")
        info.type = tarfile.SYMTYPE
        info.linkname = "/etc/passwd"
        archive.addfile(info)
    with pytest.raises(ArtifactPolicyError, match="link"):
        inspect_archive(artifact)


def test_only_wright_engineering_is_public() -> None:
    ensure_public_distribution("wright_engineering")
    for name in ("wright-core", "wright-tool-registry", "wright-api"):
        with pytest.raises(ArtifactPolicyError, match="private"):
            ensure_public_distribution(name)
