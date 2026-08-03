"""Workspace-scoped adapter grants for the isolated Rivet editor boundary."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
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


@dataclass(frozen=True, slots=True)
class EditorSettings:
    enabled: bool = False
    grant_ttl_seconds: int = 60

    def __post_init__(self) -> None:
        if not 1 <= self.grant_ttl_seconds <= 300:
            raise ValueError("Editor grant TTL must be between 1 and 300 seconds")

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "EditorSettings":
        source = env or os.environ
        return cls(
            enabled=source.get("WRIGHT_RIVET_EDITOR_ENABLED", "0").strip().lower()
            in {"1", "true", "yes"},
            grant_ttl_seconds=int(source.get("WRIGHT_RIVET_EDITOR_GRANT_TTL", "60")),
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

    def __init__(self, manifest_path: Path | None = None) -> None:
        self._manifest_path = manifest_path or (
            Path(__file__).resolve().parents[4]
            / "integrations"
            / "rivet"
            / "editor"
            / "manifest.json"
        )

    def status(
        self,
    ) -> tuple[EditorAvailability, EditorAssetManifest | None, str | None]:
        if not self._manifest_path.is_file():
            return EditorAvailability.MISSING, None, "Editor asset manifest is missing"
        try:
            raw = json.loads(self._manifest_path.read_text(encoding="utf-8"))
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
        asset = (self._manifest_path.parent / manifest.entrypoint).resolve()
        if asset.parent != self._manifest_path.parent.resolve() or not asset.is_file():
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
        return EditorAvailability.AVAILABLE, manifest, None


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
