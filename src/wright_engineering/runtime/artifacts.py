"""Exact runtime artifact identity and channel policy."""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path

from packaging.version import InvalidVersion, Version

from .models import SourceChannel


class ArtifactError(RuntimeError):
    pass


_WHEEL_VERSION = re.compile(
    r"^wright_engineering-(?P<version>[^-]+)-[^-]+-[^-]+-[^-]+\.whl$",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class RuntimeArtifact:
    path: Path
    filename: str
    version: str
    sha256: str
    channel: SourceChannel

    @classmethod
    def from_local(
        cls, path: str | Path, version: str, channel: SourceChannel
    ) -> RuntimeArtifact:
        source = Path(path).expanduser().resolve(strict=False)
        if not source.is_file():
            raise ArtifactError("artifact_missing")
        try:
            normalized = str(Version(version))
        except InvalidVersion as exc:
            raise ArtifactError("artifact_version_not_exact") from exc
        match = _WHEEL_VERSION.fullmatch(source.name)
        if not match:
            raise ArtifactError("artifact_filename_invalid")
        if Version(match.group("version")) != Version(normalized):
            raise ArtifactError("artifact_version_mismatch")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        return cls(source, source.name, normalized, digest, SourceChannel(channel))


class ArtifactResolver:
    def resolve_environment(self) -> RuntimeArtifact | None:
        """Resolve the immutable artifact handed to Wright by Hermes.

        The package-plugin boundary is intentionally explicit: Wright never
        searches a checkout or asks Git for source.  Candidate fixtures and a
        compatible released Hermes set these values after they have resolved
        and verified the package subject.
        """
        path = os.environ.get("WRIGHT_RUNTIME_ARTIFACT", "").strip()
        if not path:
            return None
        version = os.environ.get("WRIGHT_RUNTIME_VERSION", "").strip()
        channel = os.environ.get("WRIGHT_RUNTIME_CHANNEL", "").strip()
        if not version or not channel:
            raise ArtifactError("artifact_environment_incomplete")
        return self.resolve_local(
            path,
            version=version,
            channel=SourceChannel(channel),
            expected_sha256=os.environ.get("WRIGHT_RUNTIME_SHA256") or None,
        )

    def resolve_local(
        self,
        path: str | Path,
        *,
        version: str,
        channel: SourceChannel,
        expected_sha256: str | None = None,
    ) -> RuntimeArtifact:
        if str(version).strip().lower() in {"latest", "stable", "*", ""}:
            raise ArtifactError("artifact_version_not_exact")
        try:
            approved = SourceChannel(channel)
        except ValueError as exc:
            raise ArtifactError("artifact_channel_unapproved") from exc
        artifact = RuntimeArtifact.from_local(path, version, approved)
        if expected_sha256 and artifact.sha256.lower() != expected_sha256.lower():
            raise ArtifactError("artifact_hash_mismatch")
        return artifact
