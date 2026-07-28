from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tarfile
import tomllib
from typing import Any
import zipfile

from .evidence import PythonArtifact


PUBLIC_DISTRIBUTIONS = frozenset({"wright-engineering"})
FORBIDDEN_PARTS = frozenset(
    {
        ".git",
        ".github",
        ".specify",
        "specs",
        "screenshots",
        "windows-sandbox",
        "test-results",
        "outputs",
        "node_modules",
        ".env",
    }
)
FORBIDDEN_SUFFIXES = (".db", ".sqlite", ".sqlite3", ".key", ".pem", ".token")


class ArtifactPolicyError(ValueError):
    """Raised when a public Python artifact violates its content policy."""


@dataclass(frozen=True, slots=True)
class ArchiveEntry:
    name: str
    size: int


@dataclass(frozen=True, slots=True)
class NativeArtifactInspection:
    distribution: str
    version: str
    artifact_kind: str
    bundled_modules: tuple[str, ...]
    ui_manifest_sha256: str
    runtime_extra_lock_sha256: str


REQUIRED_NATIVE_PATHS = (
    "wright_engineering/__init__.py",
    "wright_engineering/hermes_plugin/__init__.py",
    "wright_engineering/runtime/lifecycle.py",
    "api/main.py",
    "core/__init__.py",
    "agent_adapters/__init__.py",
    "tool_registry/__init__.py",
    "data_vault/__init__.py",
    "workspace_service/__init__.py",
    "tool_registry/catalog/engineering-catalog.yaml",
    "wright_engineering/compatibility.json",
    "wright_engineering/runtime-extra-lock.json",
    "wright_engineering/static/web/index.html",
    "wright_engineering/static/web/asset-manifest.json",
)
PRIVATE_WRIGHT_DEPENDENCIES = frozenset(
    {
        "wright-core",
        "wright-tool-registry",
        "wright-data-vault",
        "wright-agent-adapters",
        "wright-workspace-service",
        "wright-api",
        "hermes-plugin-wright",
    }
)


def _dependency_names(requirements: list[str]) -> set[str]:
    return {
        re.split(r"[\s\[<>=!~;@]", value, maxsplit=1)[0].lower().replace("_", "-")
        for value in requirements
    }


def _validate_name(name: str) -> None:
    path = PurePosixPath(name.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts:
        raise ArtifactPolicyError(f"unsafe archive path: {name}")
    lowered = {part.lower() for part in path.parts}
    if lowered & FORBIDDEN_PARTS or name.lower().endswith(FORBIDDEN_SUFFIXES):
        raise ArtifactPolicyError(f"forbidden public artifact content: {name}")


def inspect_archive(path: Path) -> list[ArchiveEntry]:
    entries: list[ArchiveEntry] = []
    if path.suffix == ".whl" or zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            for zip_item in archive.infolist():
                _validate_name(zip_item.filename)
                unix_mode = zip_item.external_attr >> 16
                if unix_mode & 0o170000 == 0o120000:
                    raise ArtifactPolicyError(
                        f"archive symlink is forbidden: {zip_item.filename}"
                    )
                if not zip_item.is_dir():
                    entries.append(ArchiveEntry(zip_item.filename, zip_item.file_size))
    else:
        with tarfile.open(path, "r:*") as archive:
            for tar_item in archive.getmembers():
                _validate_name(tar_item.name)
                if tar_item.issym() or tar_item.islnk():
                    raise ArtifactPolicyError(
                        f"archive link is forbidden: {tar_item.name}"
                    )
                if tar_item.isfile():
                    entries.append(ArchiveEntry(tar_item.name, tar_item.size))
    if not entries:
        raise ArtifactPolicyError(f"empty artifact: {path}")
    return sorted(entries, key=lambda item: item.name)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_evidence(path: Path) -> tuple[PythonArtifact, str]:
    entries = inspect_archive(path)
    manifest = "\n".join(f"{item.size}\t{item.name}" for item in entries) + "\n"
    kind = "wheel" if path.suffix == ".whl" else "sdist"
    evidence = PythonArtifact(
        filename=path.name,
        kind=kind,
        sha256=sha256_file(path),
        content_manifest_sha256=hashlib.sha256(manifest.encode()).hexdigest(),
    )
    return evidence, manifest


def ensure_public_distribution(name: str) -> None:
    normalized = name.lower().replace("_", "-")
    if normalized not in PUBLIC_DISTRIBUTIONS:
        raise ArtifactPolicyError(
            f"distribution is private and must not be published: {name}"
        )


def _archive_payloads(path: Path) -> dict[str, bytes]:
    payloads: dict[str, bytes] = {}
    if path.suffix == ".whl" or zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            for zip_item in archive.infolist():
                if not zip_item.is_dir():
                    payloads[zip_item.filename.replace("\\", "/")] = archive.read(
                        zip_item
                    )
    else:
        with tarfile.open(path, "r:*") as archive:
            for tar_item in archive.getmembers():
                if tar_item.isfile():
                    handle = archive.extractfile(tar_item)
                    if handle is not None:
                        payloads[tar_item.name.replace("\\", "/")] = handle.read()
    return payloads


def _matching_name(names: set[str], suffix: str) -> str:
    matches = [name for name in names if name.endswith(suffix)]
    if len(matches) != 1:
        raise ArtifactPolicyError(
            f"native artifact requires exactly one {suffix}; found {len(matches)}"
        )
    return matches[0]


def _metadata_identity(payloads: dict[str, bytes]) -> tuple[str, str, str]:
    name = _matching_name(set(payloads), ".dist-info/METADATA")
    text = payloads[name].decode("utf-8", errors="strict")
    distribution = re.search(r"(?m)^Name:\s*(\S+)\s*$", text)
    version = re.search(r"(?m)^Version:\s*(\S+)\s*$", text)
    if distribution is None or version is None:
        raise ArtifactPolicyError("wheel METADATA is missing Name or Version")
    return distribution.group(1), version.group(1), text


def _validate_ui_manifest(payloads: dict[str, bytes], manifest_name: str) -> str:
    raw = payloads[manifest_name]
    try:
        manifest: dict[str, Any] = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ArtifactPolicyError("packaged UI manifest is invalid") from exc
    files = manifest.get("files")
    if manifest.get("schema_version") != 1 or not isinstance(files, list) or not files:
        raise ArtifactPolicyError("packaged UI manifest is incomplete")
    prefix = manifest_name.removesuffix("asset-manifest.json")
    for item in files:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise ArtifactPolicyError("packaged UI manifest has an invalid entry")
        name = prefix + item["path"]
        payload = payloads.get(name)
        if payload is None:
            raise ArtifactPolicyError(f"packaged UI asset is missing: {item['path']}")
        if len(payload) != item.get("size"):
            raise ArtifactPolicyError(
                f"packaged UI asset size mismatch: {item['path']}"
            )
        if hashlib.sha256(payload).hexdigest() != item.get("sha256"):
            raise ArtifactPolicyError(
                f"packaged UI asset hash mismatch: {item['path']}"
            )
    return hashlib.sha256(raw).hexdigest()


def validate_native_distribution(path: Path) -> NativeArtifactInspection:
    """Validate the complete public native application artifact.

    This operates on the archive itself, not on the checkout, so the same check
    can gate the build-once candidate and every later publication stage.
    """
    inspect_archive(path)
    payloads = _archive_payloads(path)
    names = set(payloads)
    for required in REQUIRED_NATIVE_PATHS:
        _matching_name(names, required)
    if any(name.lower().endswith(".map") for name in names):
        raise ArtifactPolicyError("frontend source maps are not public artifacts")

    artifact_kind = "wheel" if path.suffix == ".whl" else "sdist"
    if artifact_kind == "wheel":
        distribution, version, metadata = _metadata_identity(payloads)
        ensure_public_distribution(distribution)
        dependencies = [
            line.split(":", 1)[1].strip()
            for line in metadata.splitlines()
            if line.startswith("Requires-Dist:")
        ]
        normalized = _dependency_names(dependencies)
        forbidden = normalized & PRIVATE_WRIGHT_DEPENDENCIES
        if forbidden:
            raise ArtifactPolicyError(
                "public artifact depends on private Wright packages: "
                + ", ".join(sorted(forbidden))
            )
    else:
        pyproject_name = _matching_name(names, "pyproject.toml")
        pyproject = payloads[pyproject_name].decode("utf-8", errors="strict")
        name_match = re.search(r'(?m)^name\s*=\s*"([^"]+)"', pyproject)
        version_match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', pyproject)
        if name_match is None or version_match is None:
            raise ArtifactPolicyError("sdist pyproject is missing name or version")
        distribution, version = name_match.group(1), version_match.group(1)
        ensure_public_distribution(distribution)
        parsed_project = tomllib.loads(pyproject).get("project", {})
        dependencies = list(parsed_project.get("dependencies", []))
        for extra_requirements in parsed_project.get(
            "optional-dependencies", {}
        ).values():
            dependencies.extend(extra_requirements)
        forbidden = _dependency_names(dependencies) & PRIVATE_WRIGHT_DEPENDENCIES
        if forbidden:
            raise ArtifactPolicyError(
                "sdist metadata names a private Wright dependency: "
                + ", ".join(sorted(forbidden))
            )

    ui_name = _matching_name(names, "wright_engineering/static/web/asset-manifest.json")
    ui_hash = _validate_ui_manifest(payloads, ui_name)
    runtime_lock_name = _matching_name(
        names, "wright_engineering/runtime-extra-lock.json"
    )
    try:
        runtime_lock = json.loads(payloads[runtime_lock_name])
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ArtifactPolicyError("runtime-extra lock is invalid") from exc
    requirements = runtime_lock.get("requirements")
    if (
        runtime_lock.get("schema_version") != 1
        or not isinstance(requirements, list)
        or not requirements
        or requirements != sorted(set(requirements))
    ):
        raise ArtifactPolicyError(
            "runtime-extra lock is incomplete or non-deterministic"
        )
    if any(
        value.lower().replace("_", "-").startswith(tuple(PRIVATE_WRIGHT_DEPENDENCIES))
        for value in requirements
    ):
        raise ArtifactPolicyError("runtime-extra lock contains a private dependency")

    modules = tuple(
        item.split("/", 1)[0]
        for item in (
            "wright_engineering/__init__.py",
            "api/main.py",
            "core/__init__.py",
            "agent_adapters/__init__.py",
            "tool_registry/__init__.py",
            "data_vault/__init__.py",
            "workspace_service/__init__.py",
        )
    )
    return NativeArtifactInspection(
        distribution=distribution,
        version=version,
        artifact_kind=artifact_kind,
        bundled_modules=modules,
        ui_manifest_sha256=ui_hash,
        runtime_extra_lock_sha256=hashlib.sha256(
            payloads[runtime_lock_name]
        ).hexdigest(),
    )
