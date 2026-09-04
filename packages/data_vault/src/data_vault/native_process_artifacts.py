"""Generated native artifact storage reached through a workspace path capability."""

from __future__ import annotations

import hashlib
import os
import re
import stat
import uuid
from pathlib import Path
from typing import Any, Protocol

from core.tracing import traced

from .native_process_repository import NativeRepositoryError

MAX_ARTIFACT_BYTES = 10 * 1024 * 1024
_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
_STORAGE_KEY = re.compile(rf"\.wright/native/artifacts/({_UUID})/({_UUID})\.bin\Z")


class ArtifactPaths(Protocol):
    def resolve(self, user_path: str, *, must_exist: bool = False) -> Path: ...


class NativeArtifactStore:
    def __init__(self, paths: ArtifactPaths):
        self.paths = paths

    @staticmethod
    def _content(path: Path) -> bytes:
        # The resolver rejects aliases/reparse points. Reject pipes and devices
        # before opening; fstat verifies the opened handle is also a regular file.
        if not path.is_file():
            raise NativeRepositoryError(
                "NATIVE_ARTIFACT_INVALID", "Artifact is not a regular workspace file."
            )
        with path.open("rb") as handle:
            descriptor = os.fstat(handle.fileno())
            if (
                not stat.S_ISREG(descriptor.st_mode)
                or descriptor.st_size > MAX_ARTIFACT_BYTES
            ):
                raise NativeRepositoryError(
                    "NATIVE_LIMIT", "Artifact exceeds the regular-file or 10 MiB limit."
                )
            content = handle.read(MAX_ARTIFACT_BYTES + 1)
        if len(content) > MAX_ARTIFACT_BYTES:
            raise NativeRepositoryError("NATIVE_LIMIT", "Artifact exceeds 10 MiB.")
        return content

    @traced("native.artifact.input")
    def input_bytes(self, relative_path: str) -> bytes:
        return self._content(self.paths.resolve(relative_path, must_exist=True))

    @traced("native.artifact.promote")
    def promote(
        self,
        run_id: str,
        content: bytes,
        *,
        filename: str,
        port_id: str,
        provenance: dict[str, Any],
    ) -> dict[str, Any]:
        if not re.fullmatch(_UUID, run_id):
            raise NativeRepositoryError(
                "NATIVE_INVALID", "Artifact run identity is invalid."
            )
        if len(content) > MAX_ARTIFACT_BYTES:
            raise NativeRepositoryError("NATIVE_LIMIT", "Artifact exceeds 10 MiB.")
        artifact_id = str(uuid.uuid4())
        staging_key = f".wright/native/staging/{artifact_id}.tmp"
        storage_key = f".wright/native/artifacts/{run_id}/{artifact_id}.bin"
        staging = self.paths.resolve(staging_key)
        target = self.paths.resolve(storage_key)
        staging.parent.mkdir(parents=True, exist_ok=True)
        target.parent.mkdir(parents=True, exist_ok=True)
        # Re-resolve after directory creation and before promotion. A logical
        # filename (including a device basename) is never used as a storage leaf.
        staging = self.paths.resolve(staging_key)
        target = self.paths.resolve(storage_key)
        try:
            with staging.open("xb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            digest = hashlib.sha256(content).hexdigest()
            if self._content(staging) != content:
                raise NativeRepositoryError(
                    "NATIVE_ARTIFACT_INVALID", "Staged artifact verification failed."
                )
            os.replace(staging, self.paths.resolve(storage_key))
        except BaseException:
            staging.unlink(missing_ok=True)
            raise
        suffix = Path(filename).suffix.lower()
        return {
            "artifact_id": artifact_id,
            "port_id": port_id,
            "filename": filename,
            "storage_key": storage_key,
            "content_digest": digest,
            "size": len(content),
            "media_type": {
                ".txt": "text/plain",
                ".md": "text/markdown",
                ".json": "application/json",
                ".csv": "text/csv",
            }.get(suffix, "application/octet-stream"),
            "provenance": provenance,
        }

    def _stored_path(self, record: dict[str, Any]) -> Path:
        match = _STORAGE_KEY.fullmatch(record["storage_key"])
        if (
            not match
            or match[1] != record["run_id"]
            or match[2] != record["artifact_id"]
        ):
            raise NativeRepositoryError(
                "NATIVE_ARTIFACT_INVALID",
                "Stored artifact identity does not match this run.",
            )
        return self.paths.resolve(record["storage_key"], must_exist=True)

    @traced("native.artifact.read")
    def read(self, record: dict[str, Any]) -> bytes:
        content = self._content(self._stored_path(record))
        if (
            len(content) != record["size"]
            or hashlib.sha256(content).hexdigest() != record["content_digest"]
        ):
            raise NativeRepositoryError(
                "NATIVE_ARTIFACT_INVALID",
                "Artifact content no longer matches recorded evidence.",
            )
        return content

    def discard_unindexed(self, run_id: str, record: dict[str, Any]) -> bool:
        try:
            path = self._stored_path({**record, "run_id": run_id})
            path.unlink()
            return True
        except FileNotFoundError:
            return True
        except (OSError, ValueError):
            return False

    def reconcile(self, indexed_keys: frozenset[str]) -> dict[str, list[str]]:
        """Remove only generated unindexed leaves; retain indexed run evidence."""
        removed, residue = [], []
        for directory, pattern in (
            (".wright/native/staging", "*.tmp"),
            (".wright/native/artifacts", "*/*.bin"),
        ):
            root = self.paths.resolve(directory)
            if not root.exists():
                continue
            for candidate in root.glob(pattern):
                key = directory + "/" + candidate.relative_to(root).as_posix()
                if key in indexed_keys:
                    continue
                generated = (
                    _STORAGE_KEY.fullmatch(key)
                    if directory.endswith("artifacts")
                    else re.fullmatch(rf"\.wright/native/staging/{_UUID}\.tmp", key)
                )
                if not generated:
                    continue
                try:
                    safe = self.paths.resolve(key, must_exist=True)
                    safe.unlink()
                    removed.append(key)
                except (OSError, ValueError):
                    residue.append(key)
        return {"removed": removed, "residue": residue}
