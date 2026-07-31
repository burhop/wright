"""Atomic, content-addressed payload storage for Workspace Surfaces."""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path

from opentelemetry import trace


class SurfacePayloadNotFound(FileNotFoundError):
    pass


class SurfaceVault:
    def __init__(self, root: str | Path, *, tracer=None) -> None:
        self.root = Path(root)
        self.tracer = tracer or trace.get_tracer(__name__)

    @staticmethod
    def _workspace_key(workspace_id: str) -> str:
        if not workspace_id.strip():
            raise ValueError("workspace_id is required")
        return hashlib.sha256(workspace_id.encode("utf-8")).hexdigest()

    @staticmethod
    def _digest(value: str) -> str:
        algorithm, separator, digest = value.partition(":")
        if (
            algorithm != "sha256"
            or separator != ":"
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise ValueError("surface vault digest must be sha256:<lowercase hex>")
        return digest

    def _path(self, workspace_id: str, digest: str) -> Path:
        value = self._digest(digest)
        return self.root / self._workspace_key(workspace_id) / value[:2] / value

    def put(self, *, workspace_id: str, payload: bytes) -> str:
        if not isinstance(payload, bytes):
            raise TypeError("surface vault payload must be bytes")
        digest = hashlib.sha256(payload).hexdigest()
        label = f"sha256:{digest}"
        with self.tracer.start_as_current_span(
            "surface.vault.put",
            attributes={"wright.workspace_id": workspace_id},
        ):
            target = self._path(workspace_id, label)
            if target.is_file():
                return label
            target.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{digest}.", suffix=".tmp", dir=target.parent
            )
            temporary = Path(temporary_name)
            try:
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(payload)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, target)
            finally:
                if temporary.exists():
                    temporary.unlink()
        return label

    def get(self, *, workspace_id: str, digest: str) -> bytes:
        with self.tracer.start_as_current_span(
            "surface.vault.get",
            attributes={"wright.workspace_id": workspace_id},
        ):
            path = self._path(workspace_id, digest)
            try:
                payload = path.read_bytes()
            except FileNotFoundError as error:
                raise SurfacePayloadNotFound(digest) from error
            observed = hashlib.sha256(payload).hexdigest()
            if observed != digest.removeprefix("sha256:"):
                raise OSError("surface vault payload checksum mismatch")
            return payload
