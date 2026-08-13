"""Wright-root-confined content-addressed storage for engineering model data."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Mapping

from core.model_observability import ModelBoundaryObserver

_DIGEST = re.compile(r"^[a-f0-9]{64}$")
_IDENTITY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


@dataclass(frozen=True, slots=True)
class StagedObject:
    operation_id: str
    content_digest: str
    size: int
    path: Path
    state: str = "staging"


@dataclass(frozen=True, slots=True)
class VerifiedObject:
    content_digest: str
    size: int
    path: Path
    created: bool
    state: str = "verified"


@dataclass(frozen=True, slots=True)
class CleanupResult:
    state: str
    removed_items: int
    residue: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    partial_operations: tuple[str, ...]
    quarantined_digests: tuple[str, ...]
    missing_installations: tuple[str, ...]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _identity(value: str, label: str) -> str:
    if not _IDENTITY.fullmatch(value):
        raise ValueError(f"{label} is invalid")
    return value


def _digest(value: str) -> str:
    if not _DIGEST.fullmatch(value):
        raise ValueError("Content digest is invalid")
    return value


def _artifact_path(value: str) -> str:
    if "\\" in value or "//" in value or re.match(r"^[A-Za-z]:", value):
        raise ValueError("Artifact path is unsafe")
    parts = value.split("/")
    parsed = PurePosixPath(value)
    if (
        not value
        or parsed.is_absolute()
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise ValueError("Artifact path is unsafe")
    return parsed.as_posix()


class ModelArtifactStore:
    def __init__(
        self,
        data_root: str | Path,
        *,
        observer: ModelBoundaryObserver | None = None,
    ) -> None:
        root = Path(data_root).resolve()
        if root.parent == root:
            raise ValueError("Model data root cannot be a filesystem root")
        self.root = root / "engineering-models"
        self.staging_root = self.root / "staging"
        self.objects_root = self.root / "objects"
        self.installations_root = self.root / "installations"
        self.quarantine_root = self.root / "quarantine"
        self.observer = observer or ModelBoundaryObserver()
        for directory in (
            self.staging_root,
            self.objects_root,
            self.installations_root,
            self.quarantine_root,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def _object_path(self, content_digest: str) -> Path:
        value = _digest(content_digest)
        return self.objects_root / "sha256" / value[:2] / value

    def stage_bytes(
        self,
        *,
        operation_id: str,
        expected_digest: str,
        content: bytes,
        maximum_bytes: int,
        trace_id: str = "no-active-span",
    ) -> StagedObject:
        operation = _identity(operation_id, "Operation identity")
        expected = _digest(expected_digest)
        if maximum_bytes < 0 or len(content) > maximum_bytes:
            raise ValueError("Content exceeds the confirmed maximum bytes")
        actual = hashlib.sha256(content).hexdigest()
        if actual != expected:
            raise ValueError("Content digest does not match the confirmed digest")
        directory = self.staging_root / operation
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / f"{expected}.partial"
        if target.exists():
            if target.stat().st_size != len(content) or _sha256(target) != expected:
                raise ValueError("Existing staged content is inconsistent")
        else:
            with target.open("xb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        result = StagedObject(operation, expected, len(content), target)
        self.observer.record(
            "model.storage.stage",
            trace_id=trace_id,
            attributes={
                "operation_id": operation,
                "content_digest": expected,
                "bytes": len(content),
            },
        )
        return result

    def promote(
        self, staged: StagedObject, *, trace_id: str = "no-active-span"
    ) -> VerifiedObject:
        expected_parent = (
            self.staging_root / _identity(staged.operation_id, "Operation identity")
        ).resolve()
        source = staged.path.resolve()
        if source.parent != expected_parent or not source.name.endswith(".partial"):
            raise ValueError("Staged object is outside its operation boundary")
        if (
            source.stat().st_size != staged.size
            or _sha256(source) != staged.content_digest
        ):
            raise ValueError("Staged content verification failed")
        target = self._object_path(staged.content_digest)
        target.parent.mkdir(parents=True, exist_ok=True)
        created = False
        if target.exists():
            if (
                target.stat().st_size != staged.size
                or _sha256(target) != staged.content_digest
            ):
                raise ValueError("Verified content identity collision")
            source.unlink()
        else:
            try:
                os.link(source, target)
                created = True
            except FileExistsError:
                if (
                    target.stat().st_size != staged.size
                    or _sha256(target) != staged.content_digest
                ):
                    raise ValueError("Verified content identity collision") from None
            source.unlink(missing_ok=True)
        target.chmod(stat.S_IREAD)
        try:
            expected_parent.rmdir()
        except OSError:
            pass
        result = VerifiedObject(staged.content_digest, staged.size, target, created)
        self.observer.record(
            "model.storage.promote",
            trace_id=trace_id,
            attributes={
                "operation_id": staged.operation_id,
                "content_digest": staged.content_digest,
                "bytes": staged.size,
                "created": created,
            },
        )
        return result

    def has_verified(self, content_digest: str) -> bool:
        path = self._object_path(content_digest)
        return path.is_file() and _sha256(path) == content_digest

    def read_verified(
        self, content_digest: str, *, maximum_bytes: int = 64 * 1024 * 1024
    ) -> bytes:
        path = self._object_path(content_digest)
        if not path.is_file() or path.stat().st_size > maximum_bytes:
            raise KeyError(content_digest)
        value = path.read_bytes()
        if hashlib.sha256(value).hexdigest() != content_digest:
            raise ValueError("Verified content is corrupt")
        return value

    def verified_path(self, content_digest: str) -> Path:
        """Return one private verified object path for an owned runtime supervisor."""

        path = self._object_path(content_digest)
        if not path.is_file() or _sha256(path) != content_digest:
            raise KeyError(content_digest)
        return path

    def activate(
        self,
        *,
        installation_id: str,
        manifest_digest: str,
        artifacts: Mapping[str, str],
        trace_id: str = "no-active-span",
    ) -> dict[str, object]:
        installation = _identity(installation_id, "Installation identity")
        manifest = _digest(manifest_digest)
        if not artifacts or len(artifacts) > 1000:
            raise ValueError("Installation artifacts are invalid")
        normalized: dict[str, str] = {}
        for path, content_digest in artifacts.items():
            safe = _artifact_path(path)
            digest = _digest(content_digest)
            if safe in normalized:
                raise ValueError("Installation artifact path is duplicated")
            if not self.has_verified(digest):
                raise ValueError("Installation refers to missing verified content")
            normalized[safe] = digest
        document: dict[str, object] = {
            "installation_id": installation,
            "manifest_digest": manifest,
            "artifacts": dict(sorted(normalized.items())),
        }
        encoded = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
        if len(encoded) > 64 * 1024:
            raise ValueError("Installation activation exceeds the 64 KiB limit")
        target = self.installations_root / f"{installation}.json"
        if target.exists():
            existing = json.loads(target.read_text(encoding="utf-8"))
            if existing != document:
                raise ValueError("Installation activation identity is immutable")
            self.observer.record(
                "model.storage.activate",
                trace_id=trace_id,
                attributes={
                    "installation_id": installation,
                    "manifest_digest": manifest,
                    "artifact_count": len(normalized),
                    "reused": True,
                },
            )
            return existing
        temporary = self.installations_root / f".{installation}.tmp"
        with temporary.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        self.observer.record(
            "model.storage.activate",
            trace_id=trace_id,
            attributes={
                "installation_id": installation,
                "manifest_digest": manifest,
                "artifact_count": len(normalized),
                "reused": False,
            },
        )
        return document

    def read_activation(self, installation_id: str) -> dict[str, object] | None:
        installation = _identity(installation_id, "Installation identity")
        target = self.installations_root / f"{installation}.json"
        if not target.is_file():
            return None
        value = json.loads(target.read_text(encoding="utf-8"))
        if value.get("installation_id") != installation:
            raise ValueError("Installation activation is invalid")
        return value

    def remove_activation(self, installation_id: str) -> bool:
        installation = _identity(installation_id, "Installation identity")
        target = self.installations_root / f"{installation}.json"
        if not target.exists():
            return False
        target.unlink()
        return True

    def remove_verified(self, content_digest: str) -> int:
        """Remove one verified object after the repository proves zero holds."""

        target = self._object_path(content_digest)
        if not target.is_file():
            return 0
        if _sha256(target) != content_digest:
            raise ValueError("Verified content is corrupt")
        size = target.stat().st_size
        target.chmod(stat.S_IWRITE | stat.S_IREAD)
        target.unlink()
        try:
            target.parent.rmdir()
        except OSError:
            pass
        return size

    def cleanup_staging(
        self, operation_id: str, *, trace_id: str = "no-active-span"
    ) -> CleanupResult:
        operation = _identity(operation_id, "Operation identity")
        directory = self.staging_root / operation
        if not directory.exists():
            result = CleanupResult("clean", 0)
            self.observer.record(
                "model.cleanup",
                trace_id=trace_id,
                attributes={
                    "operation_id": operation,
                    "cleanup_state": result.state,
                    "removed_items": 0,
                },
            )
            return result
        removed = 0
        residue: list[str] = []
        for item in directory.iterdir():
            if not item.is_file() or item.parent.resolve() != directory.resolve():
                residue.append(item.name)
                continue
            try:
                item.unlink()
                removed += 1
            except OSError:
                residue.append(item.name)
        try:
            directory.rmdir()
        except OSError:
            if directory.exists() and not residue:
                residue.append("operation-directory")
        result = CleanupResult(
            "residue" if residue else "clean", removed, tuple(residue)
        )
        self.observer.record(
            "model.cleanup",
            trace_id=trace_id,
            state="failed" if residue else "succeeded",
            attributes={
                "operation_id": operation,
                "cleanup_state": result.state,
                "removed_items": removed,
                "residue_count": len(residue),
            },
        )
        return result

    def _quarantine(self, path: Path, claimed_digest: str) -> str:
        actual = _sha256(path)
        destination = (
            self.quarantine_root / "objects" / f"{claimed_digest}-{actual[:12]}"
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        path.chmod(stat.S_IWRITE | stat.S_IREAD)
        os.replace(path, destination)
        return claimed_digest

    def reconcile(self, *, trace_id: str = "no-active-span") -> ReconciliationReport:
        partials = tuple(
            sorted(item.name for item in self.staging_root.iterdir() if item.is_dir())
        )
        quarantined: list[str] = []
        object_root = self.objects_root / "sha256"
        if object_root.exists():
            for path in tuple(object_root.glob("*/*")):
                claimed = path.name
                if not path.is_file() or not _DIGEST.fullmatch(claimed):
                    continue
                if _sha256(path) != claimed:
                    quarantined.append(self._quarantine(path, claimed))
        missing: list[str] = []
        for path in self.installations_root.glob("*.json"):
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
                artifacts = value.get("artifacts", {})
                if not isinstance(artifacts, dict) or any(
                    not self.has_verified(str(digest)) for digest in artifacts.values()
                ):
                    missing.append(path.stem)
            except (OSError, ValueError, json.JSONDecodeError):
                missing.append(path.stem)
        result = ReconciliationReport(
            partials, tuple(sorted(quarantined)), tuple(sorted(missing))
        )
        self.observer.record(
            "model.storage.reconcile",
            trace_id=trace_id,
            state="failed" if quarantined or missing else "succeeded",
            attributes={
                "partial_count": len(partials),
                "quarantined_count": len(quarantined),
                "missing_count": len(missing),
            },
        )
        return result


__all__ = [
    "CleanupResult",
    "ModelArtifactStore",
    "ReconciliationReport",
    "StagedObject",
    "VerifiedObject",
]
