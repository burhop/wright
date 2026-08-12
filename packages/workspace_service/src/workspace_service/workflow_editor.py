"""Workspace-scoped adapter grants for the isolated Rivet editor boundary."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import sys
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

from core.workflow_editor import (
    EditorAssetManifest,
    EditorAvailability,
    EditorBootstrap,
    WorkflowEditorError,
)
from core.workflows import WorkflowDocument

from .use_cases.workflows import WorkspaceWorkflowUseCases
from .workspace_path import WorkspacePath


@dataclass(frozen=True, slots=True)
class EditorSettings:
    enabled: bool = False
    grant_ttl_seconds: int = 60
    ai_enabled: bool = False
    ai_token_ttl_seconds: int = 300
    ai_request_bytes: int = 2 * 1024 * 1024
    ai_timeout_seconds: float = 300.0

    def __post_init__(self) -> None:
        if not 1 <= self.grant_ttl_seconds <= 300:
            raise ValueError("Editor grant TTL must be between 1 and 300 seconds")
        if not 1 <= self.ai_token_ttl_seconds <= 3600:
            raise ValueError("Editor AI token TTL must be between 1 and 3600 seconds")
        if not 1024 <= self.ai_request_bytes <= 10 * 1024 * 1024:
            raise ValueError("Editor AI request limit must be between 1 KiB and 10 MiB")
        if not 1 <= self.ai_timeout_seconds <= 600:
            raise ValueError("Editor AI timeout must be between 1 and 600 seconds")

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "EditorSettings":
        source = env or os.environ
        return cls(
            enabled=source.get("WRIGHT_RIVET_EDITOR_ENABLED", "0").strip().lower()
            in {"1", "true", "yes"},
            grant_ttl_seconds=int(source.get("WRIGHT_RIVET_EDITOR_GRANT_TTL", "60")),
            ai_enabled=source.get("WRIGHT_RIVET_AI_ENABLED", "0").strip().lower()
            in {"1", "true", "yes"},
            ai_token_ttl_seconds=int(source.get("WRIGHT_RIVET_AI_TOKEN_TTL", "300")),
            ai_request_bytes=int(
                source.get("WRIGHT_RIVET_AI_REQUEST_BYTES", str(2 * 1024 * 1024))
            ),
            ai_timeout_seconds=float(
                source.get("WRIGHT_RIVET_AI_TIMEOUT_SECONDS", "300")
            ),
        )


@dataclass(frozen=True, slots=True)
class _Grant:
    grant_id: str
    workspace_id: str
    session_id: str
    workflow_id: str
    slug: str
    revision: int
    expires_at: datetime
    revoked: bool = False


class EditorAssetCatalog:
    """Validates only Wright-owned local editor assets; no network fallback."""

    _RIVET_VERSION = "2.8.9"
    _SOURCE_REPOSITORY = "https://github.com/valerypopoff/rivet2.0.git"
    _SOURCE_REVISION = "4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053"
    _SOURCE_PACKAGE = "@valerypopoff/rivet-app"

    def __init__(self, manifest_path: Path | None = None) -> None:
        checkout_manifest = (
            Path(__file__).resolve().parents[4]
            / "integrations"
            / "rivet"
            / "editor"
            / "manifest.json"
        )
        packaged_manifest = (
            Path(__file__).resolve().parent / "_rivet" / "editor" / "manifest.json"
        )
        self._manifest_path = manifest_path or (
            checkout_manifest if checkout_manifest.is_file() else packaged_manifest
        )

    def status(
        self,
    ) -> tuple[EditorAvailability, EditorAssetManifest | None, str | None]:
        if not self._manifest_path.is_file():
            return EditorAvailability.MISSING, None, "Editor asset manifest is missing"
        try:
            raw = json.loads(self._manifest_path.read_text(encoding="utf-8"))
            if raw.get("schema_version") != 2:
                raise ValueError("Unsupported editor artifact schema")
            source = raw["source"]
            if source != {
                "repository": self._SOURCE_REPOSITORY,
                "revision": self._SOURCE_REVISION,
                "package": self._SOURCE_PACKAGE,
                "package_version": self._RIVET_VERSION,
            }:
                raise ValueError("Unexpected editor source")
            if raw.get("rivet_version") != self._RIVET_VERSION:
                raise ValueError("Unexpected editor version")
            if raw.get("license") != "MIT":
                raise ValueError("Unexpected editor license")
            manifest = EditorAssetManifest(
                rivet_version=str(raw["rivet_version"]),
                entrypoint=(str(raw["entrypoint"]) if raw.get("entrypoint") else None),
                sha256=(str(raw["sha256"]) if raw.get("sha256") else None),
                license=str(raw["license"]),
            )
        except (OSError, ValueError, KeyError, TypeError):
            return (
                EditorAvailability.INCOMPATIBLE,
                None,
                "Editor asset manifest is invalid",
            )
        if not manifest.entrypoint or not manifest.sha256:
            return (
                EditorAvailability.MISSING,
                manifest,
                "Pinned editor bundle is not installed",
            )
        asset_root = self._manifest_path.parent.resolve()
        asset = self._confined_file(asset_root, manifest.entrypoint)
        if asset is None or not asset.is_file():
            return (
                EditorAvailability.MISSING,
                manifest,
                "Pinned editor entry point is missing",
            )
        digest = hashlib.sha256(asset.read_bytes()).hexdigest()
        if not secrets.compare_digest(digest, manifest.sha256):
            return (
                EditorAvailability.INCOMPATIBLE,
                manifest,
                "Pinned editor checksum does not match",
            )
        try:
            self._verify_inputs(asset_root, raw, "patches")
            self._verify_inputs(asset_root, raw, "wrapper")
            self._verify_artifact_tree(asset_root, raw)
        except FileNotFoundError:
            return (
                EditorAvailability.MISSING,
                manifest,
                "Pinned editor artifact is incomplete",
            )
        except (KeyError, TypeError, ValueError):
            return (
                EditorAvailability.INCOMPATIBLE,
                manifest,
                "Pinned editor artifact integrity does not match",
            )
        return EditorAvailability.AVAILABLE, manifest, None

    @staticmethod
    def _confined_file(root: Path, relative: object) -> Path | None:
        if not isinstance(relative, str) or not relative:
            return None
        candidate = (root / relative).resolve()
        if candidate == root or root not in candidate.parents:
            return None
        return candidate

    @classmethod
    def _verify_inputs(
        cls, asset_root: Path, raw: dict[str, object], category: str
    ) -> None:
        entries = raw[category]
        if not isinstance(entries, list) or not entries:
            raise ValueError(f"Missing {category}")
        for entry in entries:
            if not isinstance(entry, dict):
                raise TypeError(category)
            path = cls._confined_file(asset_root, entry.get("path"))
            if path is None or not path.is_file():
                raise FileNotFoundError(str(entry.get("path")))
            expected = entry.get("sha256")
            if not isinstance(expected, str) or not secrets.compare_digest(
                hashlib.sha256(path.read_bytes()).hexdigest(), expected
            ):
                raise ValueError(f"Changed {category} input")

    @classmethod
    def _verify_artifact_tree(cls, asset_root: Path, raw: dict[str, object]) -> None:
        entries = raw["files"]
        if not isinstance(entries, list) or not entries:
            raise ValueError("Missing artifact inventory")
        recorded_paths: list[str] = []
        digest_lines: list[str] = []
        for entry in entries:
            if not isinstance(entry, dict):
                raise TypeError("files")
            relative = entry.get("path")
            if not isinstance(relative, str) or not relative.startswith("dist/"):
                raise ValueError("Artifact path must be under dist")
            path = cls._confined_file(asset_root, relative)
            if path is None or not path.is_file():
                raise FileNotFoundError(relative)
            content = path.read_bytes()
            digest = hashlib.sha256(content).hexdigest()
            if entry.get("bytes") != len(content) or not isinstance(
                entry.get("sha256"), str
            ):
                raise ValueError("Invalid artifact inventory entry")
            if not secrets.compare_digest(digest, str(entry["sha256"])):
                raise ValueError("Artifact file checksum does not match")
            recorded_paths.append(relative)
            digest_lines.append(f"{digest}  {relative}\n")
        # The Node inventory uses JavaScript localeCompare ordering, which is
        # deterministic but not byte-for-byte equivalent to Python's Unicode
        # sort (notably around mixed-case asset names). The signed tree digest
        # preserves that canonical order; here we separately reject duplicates.
        if len(recorded_paths) != len(set(recorded_paths)):
            raise ValueError("Artifact inventory is not canonical")
        actual_paths = sorted(
            f"dist/{path.relative_to(asset_root / 'dist').as_posix()}"
            for path in (asset_root / "dist").rglob("*")
            if path.is_file()
        )
        if set(recorded_paths) != set(actual_paths):
            raise ValueError("Artifact inventory is incomplete")
        expected_tree = raw.get("tree_sha256")
        tree_digest = hashlib.sha256("".join(digest_lines).encode()).hexdigest()
        if not isinstance(expected_tree, str) or not secrets.compare_digest(
            tree_digest, expected_tree
        ):
            raise ValueError("Artifact tree checksum does not match")

    @property
    def artifact_root(self) -> Path:
        return self._manifest_path.parent.resolve()


class WorkspaceWorkflowEditor:
    """Issue and enforce opaque grants for exactly one persisted workflow."""

    def __init__(
        self,
        workflows: WorkspaceWorkflowUseCases,
        *,
        settings: EditorSettings | None = None,
        catalog: EditorAssetCatalog | None = None,
        clock=lambda: datetime.now(UTC),
    ) -> None:
        self._workflows = workflows
        self._settings = settings or EditorSettings.from_env()
        self._catalog = catalog or EditorAssetCatalog()
        self._clock = clock
        self._grants: dict[str, _Grant] = {}

    def availability(self) -> tuple[EditorAvailability, str | None]:
        if not self._settings.enabled:
            return EditorAvailability.DISABLED, "Rivet editor is disabled"
        status, _manifest, detail = self._catalog.status()
        return status, detail

    def manual_surface_manifest(self, workspace_dir: str) -> dict[str, object] | None:
        """Provision the sole Wright-owned manual editor surface manifest."""
        availability, _detail = self.availability()
        if availability is not EditorAvailability.AVAILABLE:
            return None
        status, artifact, _detail = self._catalog.status()
        if status is not EditorAvailability.AVAILABLE or artifact is None:
            return None
        root = self._catalog.artifact_root
        host = root / "host.py"
        entrypoint = (root / artifact.entrypoint).resolve()
        if (
            not host.is_file()
            or not entrypoint.is_file()
            or root not in entrypoint.parents
        ):
            return None
        document: dict[str, object] = {
            "schemaVersion": 1,
            "id": "wright.rivet-editor",
            "version": artifact.rivet_version,
            "title": "Rivet",
            "description": "Wright-owned Rivet editor hosted from the active workspace.",
            "ownershipPolicy": "wright-owned",
            "launch": {
                "mode": "command",
                "argv": [
                    sys.executable,
                    str(host),
                    "--root",
                    str(entrypoint.parent),
                    "--host",
                    "${WRIGHT_BIND_HOST}",
                    "--port",
                    "${WRIGHT_PORT}",
                    *(
                        [
                            "--ai-enabled",
                            "--ai-token-ttl",
                            str(self._settings.ai_token_ttl_seconds),
                            "--ai-request-bytes",
                            str(self._settings.ai_request_bytes),
                            "--ai-timeout",
                            str(self._settings.ai_timeout_seconds),
                        ]
                        if self._settings.ai_enabled
                        else []
                    ),
                ],
                "workingDirectory": ".",
                "environment": {},
                "framework": "generic",
            },
            "readiness": {
                "path": "/health",
                "method": "GET",
                "expectedStatus": 200,
                "timeoutMs": 5000,
                "intervalMs": 100,
            },
            "health": {
                "path": "/health",
                "method": "GET",
                "expectedStatus": 200,
                "timeoutMs": 1000,
                "intervalMs": 1000,
            },
            "presentation": {
                "panel": True,
                "browser": True,
                "sharing": "isolated",
                "basePathMode": "root",
                "allowedFrameAncestors": [],
                "permissionsPolicy": [],
            },
            "transports": {"http": True, "websocket": False, "sse": False},
            "navigation": {
                "allowSameTargetRedirects": False,
                "externalLinks": "prompt-browser",
                "downloads": "prompt",
            },
            "lifetime": {"policy": "workspace"},
            "capabilities": [],
        }
        paths = WorkspacePath(workspace_dir)
        apps_directory = paths.resolve(".wright/apps")
        apps_directory.mkdir(parents=True, exist_ok=True)
        target = paths.resolve(".wright/apps/rivet-editor.surface.json")
        encoded = json.dumps(document, indent=2, sort_keys=True) + "\n"
        try:
            with target.open("x", encoding="utf-8") as stream:
                stream.write(encoded)
        except FileExistsError:
            if target.read_text(encoding="utf-8") != encoded:
                raise WorkflowEditorError(
                    "RIVET_EDITOR_MANIFEST_CONFLICT",
                    "Rivet editor manifest conflicts with an existing workspace file",
                ) from None
        return document

    async def bootstrap(
        self, *, workspace_id: str, session_id: str, workspace_dir: str, slug: str
    ) -> EditorBootstrap:
        availability, detail = self.availability()
        if availability is not EditorAvailability.AVAILABLE:
            return EditorBootstrap(availability, None, None, None, None, None, detail)
        document = await self._workflows.read(workspace_dir, slug)
        now = self._clock()
        grant = _Grant(
            grant_id=secrets.token_urlsafe(32),
            workspace_id=workspace_id,
            session_id=session_id,
            workflow_id=document.workflow_id,
            slug=document.slug,
            revision=document.revision,
            expires_at=now + timedelta(seconds=self._settings.grant_ttl_seconds),
        )
        self._grants[grant.grant_id] = grant
        return EditorBootstrap(
            availability,
            grant.grant_id,
            document.workflow_id,
            document.revision,
            document.digest,
            grant.expires_at,
        )

    def _grant(self, grant_id: str, *, workspace_id: str, session_id: str) -> _Grant:
        grant = self._grants.get(grant_id)
        if grant is None or grant.revoked:
            raise WorkflowEditorError(
                "RIVET_EDITOR_GRANT_INVALID", "Editor grant is unavailable"
            )
        if grant.workspace_id != workspace_id or grant.session_id != session_id:
            raise WorkflowEditorError(
                "RIVET_EDITOR_GRANT_FORBIDDEN", "Editor grant is unavailable"
            )
        if grant.expires_at <= self._clock():
            raise WorkflowEditorError(
                "RIVET_EDITOR_GRANT_EXPIRED", "Editor grant has expired"
            )
        return grant

    async def read(
        self, grant_id: str, *, workspace_id: str, session_id: str, workspace_dir: str
    ) -> WorkflowDocument:
        grant = self._grant(grant_id, workspace_id=workspace_id, session_id=session_id)
        document = await self._workflows.read(workspace_dir, grant.slug)
        if document.workflow_id != grant.workflow_id:
            raise WorkflowEditorError(
                "RIVET_EDITOR_WORKFLOW_CHANGED", "Editor workflow is unavailable"
            )
        return document

    async def save(
        self,
        grant_id: str,
        *,
        workspace_id: str,
        session_id: str,
        workspace_dir: str,
        expected_revision: int,
        project: str,
        datasets: dict[str, str],
    ) -> WorkflowDocument:
        grant = self._grant(grant_id, workspace_id=workspace_id, session_id=session_id)
        if expected_revision != grant.revision:
            raise WorkflowEditorError(
                "RIVET_EDITOR_REVISION_SCOPE", "Editor grant revision is stale"
            )
        return await self._workflows.save(
            workspace_id,
            workspace_dir,
            grant.slug,
            expected_revision,
            project,
            datasets,
        )

    def revoke(self, grant_id: str, *, workspace_id: str, session_id: str) -> None:
        grant = self._grant(grant_id, workspace_id=workspace_id, session_id=session_id)
        self._grants[grant_id] = replace(grant, revoked=True)
