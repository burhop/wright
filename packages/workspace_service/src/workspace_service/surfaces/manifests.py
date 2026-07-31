"""Workspace-confined discovery and authorization of live-app manifests."""

from __future__ import annotations

import json
import secrets
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any

from core.surfaces.live_app_manifest import (
    AttachLaunch,
    CommandLaunch,
    LiveAppManifest,
    ManifestError,
    parse_live_app_manifest,
)

from workspace_service.workspace_path import WorkspacePath


_DENIED_ENVIRONMENT_NAMES = frozenset(
    {
        "BASH_ENV",
        "COMSPEC",
        "ENV",
        "GIT_CONFIG_COUNT",
        "NODE_OPTIONS",
        "PATH",
        "PATHEXT",
        "PERL5OPT",
        "PROMPT_COMMAND",
        "PS4",
        "PYTHONHOME",
        "PYTHONPATH",
        "RUBYOPT",
        "SHELLOPTS",
        "SYSTEMROOT",
        "WINDIR",
    }
)


class ManifestDiscoveryError(RuntimeError):
    """A stable, user-actionable failure at the manifest trust boundary."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class DiscoveredManifest:
    manifest: LiveAppManifest
    relative_path: str
    working_directory: Path


@dataclass(frozen=True, slots=True)
class AttachApproval:
    approval_id: str
    manifest_id: str
    manifest_hash: str
    normalized_url: str
    administrator_id: str
    approved_at: datetime


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ManifestDiscoveryError(
                "SURFACE_MANIFEST_DUPLICATE_KEY",
                f"Manifest contains duplicate JSON key: {key}",
            )
        value[key] = item
    return value


class WorkspaceManifestStore:
    """Discover declarations without treating validation as launch authority."""

    def __init__(
        self,
        workspace_root: str | Path,
        *,
        administrator_check: Callable[[str], bool] | None = None,
        clock: Callable[[], datetime] | None = None,
        id_factory: Callable[[], str] | None = None,
        maximum_files: int = 256,
        maximum_bytes: int = 1024 * 1024,
    ) -> None:
        if maximum_files < 1 or maximum_bytes < 1:
            raise ValueError("manifest discovery bounds must be positive")
        self._paths = WorkspacePath(workspace_root)
        self._administrator_check = administrator_check or (lambda _actor_id: False)
        self._clock = clock or (lambda: datetime.now(UTC))
        self._id_factory = id_factory or (lambda: secrets.token_urlsafe(24))
        self._maximum_files = maximum_files
        self._maximum_bytes = maximum_bytes

    @property
    def workspace_root(self) -> Path:
        return self._paths.root

    def _apps_directory(self) -> Path:
        try:
            return self._paths.resolve(".wright/apps")
        except ValueError as error:
            raise ManifestDiscoveryError(
                "SURFACE_MANIFEST_PATH_DENIED",
                "Manifest directory contains a symbolic link or leaves the workspace",
            ) from error

    def _load_file(self, candidate: Path) -> DiscoveredManifest:
        relative = candidate.relative_to(self.workspace_root).as_posix()
        try:
            confined = self._paths.resolve(relative, must_exist=True)
        except (FileNotFoundError, ValueError) as error:
            raise ManifestDiscoveryError(
                "SURFACE_MANIFEST_PATH_DENIED",
                f"Manifest {relative} contains a symbolic link or leaves the workspace",
            ) from error
        if not confined.is_file():
            raise ManifestDiscoveryError(
                "SURFACE_MANIFEST_NOT_FILE",
                f"Manifest {relative} is not a regular file",
            )
        before = confined.stat()
        if before.st_size > self._maximum_bytes:
            raise ManifestDiscoveryError(
                "SURFACE_MANIFEST_TOO_LARGE",
                f"Manifest {relative} exceeds the size limit",
            )
        try:
            document = json.loads(
                confined.read_text(encoding="utf-8"),
                object_pairs_hook=_reject_duplicate_keys,
            )
        except ManifestDiscoveryError:
            raise
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ManifestDiscoveryError(
                "SURFACE_MANIFEST_JSON_INVALID",
                f"Manifest {relative} is not valid UTF-8 JSON",
            ) from error
        after = confined.stat()
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise ManifestDiscoveryError(
                "SURFACE_MANIFEST_CHANGED",
                f"Manifest {relative} changed while it was read",
            )
        if not isinstance(document, Mapping):
            raise ManifestDiscoveryError(
                "SURFACE_MANIFEST_INVALID",
                f"Manifest {relative} must contain an object",
            )
        try:
            manifest = parse_live_app_manifest(document)
        except ManifestError as error:
            raise ManifestDiscoveryError(
                error.code, f"Manifest {relative} is invalid: {error}"
            ) from error

        if isinstance(manifest.launch, CommandLaunch):
            for name in manifest.launch.environment:
                normalized = name.upper()
                if normalized in _DENIED_ENVIRONMENT_NAMES or normalized.startswith(
                    ("DYLD_", "LD_", "WRIGHT_")
                ):
                    raise ManifestDiscoveryError(
                        "SURFACE_MANIFEST_ENVIRONMENT_DENIED",
                        f"Manifest {relative} declares a process-control environment variable",
                    )

        working_directory = self.workspace_root
        if isinstance(manifest.launch, CommandLaunch):
            declared = manifest.launch.working_directory
            try:
                working_directory = (
                    self.workspace_root
                    if declared == "."
                    else self._paths.resolve(declared, must_exist=True)
                )
            except (FileNotFoundError, ValueError) as error:
                raise ManifestDiscoveryError(
                    "SURFACE_MANIFEST_CWD_DENIED",
                    f"Manifest {relative} working directory is outside the workspace or unsafe",
                ) from error
            if not working_directory.is_dir():
                raise ManifestDiscoveryError(
                    "SURFACE_MANIFEST_CWD_DENIED",
                    f"Manifest {relative} working directory is not a directory",
                )
        return DiscoveredManifest(
            manifest=manifest,
            relative_path=relative,
            working_directory=working_directory,
        )

    def discover(self) -> Mapping[str, DiscoveredManifest]:
        directory = self._apps_directory()
        if not directory.exists():
            return MappingProxyType({})
        if not directory.is_dir():
            raise ManifestDiscoveryError(
                "SURFACE_MANIFEST_DIRECTORY_INVALID",
                ".wright/apps must be a workspace directory",
            )
        candidates = sorted(
            directory.glob("*.surface.json"), key=lambda item: item.name
        )
        if len(candidates) > self._maximum_files:
            raise ManifestDiscoveryError(
                "SURFACE_MANIFEST_COUNT_EXCEEDED",
                "Workspace contains too many live-app manifests",
            )
        discovered: dict[str, DiscoveredManifest] = {}
        for candidate in candidates:
            item = self._load_file(candidate)
            manifest_id = item.manifest.manifest_id
            if manifest_id in discovered:
                raise ManifestDiscoveryError(
                    "SURFACE_MANIFEST_ID_DUPLICATE",
                    f"Workspace contains duplicate manifest id: {manifest_id}",
                )
            discovered[manifest_id] = item
        return MappingProxyType(discovered)

    def get(self, manifest_id: str) -> DiscoveredManifest:
        item = self.discover().get(manifest_id)
        if item is None:
            raise ManifestDiscoveryError(
                "SURFACE_MANIFEST_NOT_FOUND", f"Manifest not found: {manifest_id}"
            )
        return item

    def approve_attach(
        self, manifest_id: str, *, administrator_id: str
    ) -> AttachApproval:
        if not administrator_id or not self._administrator_check(administrator_id):
            raise ManifestDiscoveryError(
                "SURFACE_ATTACH_ADMIN_REQUIRED",
                "Attach approval requires an eligible administrator",
            )
        item = self.get(manifest_id)
        if not isinstance(item.manifest.launch, AttachLaunch):
            raise ManifestDiscoveryError(
                "SURFACE_ATTACH_NOT_DECLARED",
                "Attach approval applies only to approved-attach manifests",
            )
        normalized = item.manifest.resolve_attach(administrator_approved=True).url
        return AttachApproval(
            approval_id=self._id_factory(),
            manifest_id=manifest_id,
            manifest_hash=item.manifest.canonical_hash,
            normalized_url=normalized,
            administrator_id=administrator_id,
            approved_at=self._clock(),
        )

    def authorize(
        self,
        manifest_id: str,
        *,
        attach_approval: AttachApproval | None = None,
    ) -> DiscoveredManifest:
        item = self.get(manifest_id)
        if isinstance(item.manifest.launch, CommandLaunch):
            if attach_approval is not None:
                raise ManifestDiscoveryError(
                    "SURFACE_ATTACH_APPROVAL_INVALID",
                    "Attach approval cannot authorize a Wright-owned command",
                )
            return item
        if attach_approval is None:
            raise ManifestDiscoveryError(
                "SURFACE_ATTACH_APPROVAL_REQUIRED",
                "Approved-attach manifest requires explicit administrator approval",
            )
        normalized = item.manifest.resolve_attach(administrator_approved=True).url
        if (
            attach_approval.manifest_id != manifest_id
            or attach_approval.manifest_hash != item.manifest.canonical_hash
            or attach_approval.normalized_url != normalized
            or not self._administrator_check(attach_approval.administrator_id)
        ):
            raise ManifestDiscoveryError(
                "SURFACE_ATTACH_APPROVAL_STALE",
                "Attach manifest or administrator authority changed after approval",
            )
        return item


__all__ = [
    "AttachApproval",
    "DiscoveredManifest",
    "ManifestDiscoveryError",
    "WorkspaceManifestStore",
]
