"""Safe inspection of deterministic offline engineering-model packages."""

from __future__ import annotations

import hashlib
import json
import stat
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from .models import ModelPackage, ModelRegistryError
from .policy import validate_artifact_path

_MANIFEST = "engineering-model-package.json"
_ARCHIVE_SUFFIXES = (".zip", ".tar", ".tgz", ".gz", ".bz2", ".xz", ".7z")


class OfflinePackageError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class InspectedOfflinePackage:
    package: ModelPackage
    artifacts: dict[str, bytes]
    manifest_digest: str


def _safe_entry(info: zipfile.ZipInfo) -> str:
    name = unicodedata.normalize("NFC", info.filename)
    if name != info.filename or name != _MANIFEST:
        try:
            validate_artifact_path(name)
        except ValueError as error:
            raise OfflinePackageError(
                "path_unsafe", "Archive path is unsafe"
            ) from error
    if name.lower().endswith(_ARCHIVE_SUFFIXES):
        raise OfflinePackageError("path_unsafe", "Nested archives are prohibited")
    mode = (info.external_attr >> 16) & 0xFFFF
    if stat.S_ISLNK(mode) or (mode and mode & 0o111):
        raise OfflinePackageError(
            "path_unsafe", "Links and executable archive entries are prohibited"
        )
    if info.is_dir():
        raise OfflinePackageError("path_unsafe", "Archive directories are not accepted")
    return name


def inspect_offline_package(
    archive_path: str | Path,
    *,
    maximum_archive_bytes: int = 256 * 1024 * 1024,
    maximum_expanded_bytes: int = 512 * 1024 * 1024,
) -> InspectedOfflinePackage:
    path = Path(archive_path)
    if (
        maximum_archive_bytes <= 0
        or maximum_expanded_bytes <= 0
        or not path.is_file()
        or path.stat().st_size > maximum_archive_bytes
    ):
        raise OfflinePackageError(
            "size_exceeded", "Offline package exceeds its ceiling"
        )
    try:
        archive = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as error:
        raise OfflinePackageError(
            "manifest_invalid", "Offline package is not a valid ZIP"
        ) from error
    with archive:
        infos = archive.infolist()
        if not infos or len(infos) > 1001:
            raise OfflinePackageError(
                "size_exceeded", "Offline package entry count is invalid"
            )
        if sum(item.file_size for item in infos) > maximum_expanded_bytes:
            raise OfflinePackageError(
                "size_exceeded", "Offline package expands beyond its ceiling"
            )
        names: dict[str, zipfile.ZipInfo] = {}
        folded: set[str] = set()
        for info in infos:
            name = _safe_entry(info)
            key = name.casefold()
            if key in folded:
                raise OfflinePackageError(
                    "path_collision", "Archive paths collide after normalization"
                )
            folded.add(key)
            names[name] = info
        if _MANIFEST not in names:
            raise OfflinePackageError(
                "manifest_invalid", "Offline package manifest is missing"
            )
        try:
            manifest_bytes = archive.read(names[_MANIFEST])
            if len(manifest_bytes) > 64 * 1024:
                raise OfflinePackageError(
                    "size_exceeded", "Offline manifest exceeds 64 KiB"
                )
            package = ModelPackage.model_validate(json.loads(manifest_bytes))
        except OfflinePackageError:
            raise
        except (
            json.JSONDecodeError,
            ValidationError,
            ModelRegistryError,
            UnicodeDecodeError,
        ) as error:
            raise OfflinePackageError(
                "manifest_invalid", "Offline package manifest is invalid"
            ) from error
        declarations = {
            item.path: item
            for variant in package.variants
            for item in variant.artifacts
        }
        expected = {_MANIFEST, *declarations}
        if set(names) != expected:
            raise OfflinePackageError(
                "undeclared_file", "Offline package files do not match the manifest"
            )
        artifacts: dict[str, bytes] = {}
        for relative, declaration in declarations.items():
            value = archive.read(names[relative])
            if len(value) != declaration.size:
                raise OfflinePackageError(
                    "digest_mismatch", "Offline artifact size did not match"
                )
            if hashlib.sha256(value).hexdigest() != declaration.sha256:
                raise OfflinePackageError(
                    "digest_mismatch", "Offline artifact digest did not match"
                )
            artifacts[relative] = value
        license_paths = {
            item.location
            for item in package.license.evidence
            if item.kind == "artifact"
        }
        if not license_paths or not license_paths <= set(artifacts):
            raise OfflinePackageError(
                "license_unapproved", "License evidence is missing"
            )
        return InspectedOfflinePackage(package, artifacts, package.digest)


__all__ = ["InspectedOfflinePackage", "OfflinePackageError", "inspect_offline_package"]
