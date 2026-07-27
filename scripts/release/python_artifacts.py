from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path, PurePosixPath
import tarfile
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
