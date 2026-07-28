from pathlib import Path
import hashlib
import io
import json
import tarfile
import zipfile

import pytest

from scripts.release.python_artifacts import (
    ArtifactPolicyError,
    artifact_evidence,
    ensure_public_distribution,
    inspect_archive,
    validate_native_distribution,
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


def _complete_native_wheel(path: Path, *, private_dependency: bool = False) -> None:
    asset = b"console.log('wright')\n"
    manifest = {
        "schema_version": 1,
        "files": [
            {
                "path": "assets/app-123.js",
                "size": len(asset),
                "sha256": hashlib.sha256(asset).hexdigest(),
            }
        ],
    }
    runtime_lock = {
        "schema_version": 1,
        "distribution": "wright-engineering",
        "version": "0.1.5",
        "requirements": ["fastapi>=0.115,<1"],
        "uv_lock_sha256": "a" * 64,
    }
    required = {
        "wright_engineering/__init__.py": b"",
        "wright_engineering/hermes_plugin/__init__.py": b"",
        "wright_engineering/runtime/lifecycle.py": b"",
        "api/main.py": b"",
        "core/__init__.py": b"",
        "agent_adapters/__init__.py": b"",
        "tool_registry/__init__.py": b"",
        "data_vault/__init__.py": b"",
        "workspace_service/__init__.py": b"",
        "tool_registry/catalog/engineering-catalog.yaml": b"servers: []\n",
        "wright_engineering/compatibility.json": b"{}\n",
        "wright_engineering/runtime-extra-lock.json": json.dumps(
            runtime_lock, sort_keys=True
        ).encode(),
        "wright_engineering/static/web/index.html": b"<div id='root'></div>\n",
        "wright_engineering/static/web/assets/app-123.js": asset,
        "wright_engineering/static/web/asset-manifest.json": json.dumps(
            manifest, sort_keys=True
        ).encode(),
        "wright_engineering-0.1.5.dist-info/METADATA": (
            "Name: wright-engineering\nVersion: 0.1.5\n"
            + (
                "Requires-Dist: wright-core>=0.1\n"
                if private_dependency
                else "Requires-Dist: packaging<27,>=24\n"
            )
        ).encode(),
    }
    with zipfile.ZipFile(path, "w") as archive:
        for name, payload in required.items():
            archive.writestr(name, payload)


def test_complete_native_wheel_contains_ui_modules_catalog_and_runtime_lock(
    tmp_path: Path,
) -> None:
    wheel = tmp_path / "wright_engineering-0.1.5-py3-none-any.whl"
    _complete_native_wheel(wheel)

    inspection = validate_native_distribution(wheel)

    assert inspection.distribution == "wright-engineering"
    assert inspection.version == "0.1.5"
    assert set(inspection.bundled_modules) == {
        "wright_engineering",
        "api",
        "core",
        "agent_adapters",
        "tool_registry",
        "data_vault",
        "workspace_service",
    }
    assert len(inspection.ui_manifest_sha256) == 64
    assert len(inspection.runtime_extra_lock_sha256) == 64


def test_native_wheel_rejects_private_runtime_dependency(tmp_path: Path) -> None:
    wheel = tmp_path / "wright_engineering-0.1.5-py3-none-any.whl"
    _complete_native_wheel(wheel, private_dependency=True)

    with pytest.raises(ArtifactPolicyError, match="private Wright"):
        validate_native_distribution(wheel)


def _complete_native_sdist(path: Path, *, private_dependency: bool = False) -> None:
    wheel = path.with_suffix(".whl")
    _complete_native_wheel(wheel)
    root = "wright_engineering-0.1.5"
    with zipfile.ZipFile(wheel) as source, tarfile.open(path, "w:gz") as archive:
        for name in source.namelist():
            if ".dist-info/" in name:
                continue
            payload = source.read(name)
            info = tarfile.TarInfo(f"{root}/{name}")
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
        dependency = (
            '"wright-core>=0.1"' if private_dependency else '"packaging>=24,<27"'
        )
        pyproject = (
            "[project]\n"
            'name = "wright-engineering"\n'
            'version = "0.1.5"\n'
            f"dependencies = [{dependency}]\n\n"
            "[tool.uv.sources]\n"
            "wright-core = { workspace = true }\n"
        ).encode()
        info = tarfile.TarInfo(f"{root}/pyproject.toml")
        info.size = len(pyproject)
        archive.addfile(info, io.BytesIO(pyproject))
    wheel.unlink()


def test_native_sdist_ignores_non_metadata_workspace_sources(tmp_path: Path) -> None:
    sdist = tmp_path / "wright_engineering-0.1.5.tar.gz"
    _complete_native_sdist(sdist)

    inspection = validate_native_distribution(sdist)

    assert inspection.distribution == "wright-engineering"
    assert inspection.artifact_kind == "sdist"


def test_native_sdist_rejects_private_runtime_dependency(tmp_path: Path) -> None:
    sdist = tmp_path / "wright_engineering-0.1.5.tar.gz"
    _complete_native_sdist(sdist, private_dependency=True)

    with pytest.raises(ArtifactPolicyError, match="wright-core"):
        validate_native_distribution(sdist)
