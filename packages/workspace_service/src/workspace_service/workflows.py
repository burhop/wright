"""Workspace-authoritative Rivet workflow persistence.

This module deliberately has no Rivet or Node dependency.  It stores opaque
project content as ordinary workspace files and exposes revision-aware,
workspace-confined operations for later editor and runner slices.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
import uuid
from pathlib import Path

from core.workflows import (
    WorkflowDocument,
    WorkflowPersistenceError,
    WorkflowRevisionConflict,
)

from .workspace_path import WorkspacePath

_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
_MAX_PROJECT_BYTES = 4 * 1024 * 1024
_MAX_DATASET_BYTES = 8 * 1024 * 1024


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _validate_slug(slug: str) -> str:
    candidate = slug.strip().lower()
    if not _SLUG.fullmatch(candidate):
        raise WorkflowPersistenceError(
            "Workflow slug must be 1-63 lowercase letters, digits, or hyphens"
        )
    return candidate


def _validate_content(content: str, limit: int, label: str) -> bytes:
    encoded = content.encode("utf-8")
    if len(encoded) > limit:
        raise WorkflowPersistenceError(f"{label} exceeds the supported size limit")
    return encoded


class WorkspaceWorkflowStore:
    """File-authoritative store rooted in one server-selected workspace."""

    def __init__(self, workspace_dir: str) -> None:
        self._paths = WorkspacePath(workspace_dir)

    def _directory(self, slug: str) -> Path:
        try:
            return self._paths.resolve(f"workflows/{_validate_slug(slug)}")
        except ValueError as error:
            raise WorkflowPersistenceError(str(error)) from error

    def _metadata_path(self, slug: str) -> Path:
        return self._paths.resolve(
            f"workflows/{_validate_slug(slug)}/.wright-workflow.json"
        )

    @staticmethod
    def _atomic_write(path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Resolve after creation and before replace to reject a link introduced
        # between request validation and mutation.
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
            raise WorkflowPersistenceError(
                "Workflow path may not contain symbolic links"
            )
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".wright-workflow-", dir=path.parent
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    def create(
        self, slug: str, project: str, datasets: dict[str, str] | None = None
    ) -> WorkflowDocument:
        slug = _validate_slug(slug)
        directory = self._directory(slug)
        if directory.exists():
            raise WorkflowPersistenceError("Workflow slug already exists")
        workflow_id = str(uuid.uuid4())
        return self._write(slug, workflow_id, 1, project, datasets or {})

    def read(self, slug: str) -> WorkflowDocument:
        slug = _validate_slug(slug)
        metadata = self._metadata_path(slug)
        project_path = self._paths.resolve(
            f"workflows/{slug}/workflow.rivet-project", must_exist=True
        )
        if not metadata.is_file() or not project_path.is_file():
            raise FileNotFoundError(slug)
        data = json.loads(metadata.read_text(encoding="utf-8"))
        datasets_dir = self._paths.resolve(f"workflows/{slug}/datasets")
        datasets = (
            {
                item.stem: item.read_text(encoding="utf-8")
                for item in datasets_dir.glob("*.json")
                if item.is_file() and not item.is_symlink()
            }
            if datasets_dir.is_dir()
            else {}
        )
        project = project_path.read_text(encoding="utf-8")
        return WorkflowDocument(
            str(data["workflow_id"]),
            slug,
            int(data["revision"]),
            str(data["digest"]),
            project,
            datasets,
        )

    def save(
        self,
        slug: str,
        expected_revision: int,
        project: str,
        datasets: dict[str, str] | None = None,
    ) -> WorkflowDocument:
        current = self.read(slug)
        if current.revision != expected_revision:
            raise WorkflowRevisionConflict(current.revision, current.digest)
        return self._write(
            current.slug,
            current.workflow_id,
            current.revision + 1,
            project,
            datasets or current.datasets,
        )

    def rename(
        self, slug: str, expected_revision: int, new_slug: str
    ) -> WorkflowDocument:
        current = self.read(slug)
        if current.revision != expected_revision:
            raise WorkflowRevisionConflict(current.revision, current.digest)
        destination_slug = _validate_slug(new_slug)
        source = self._directory(current.slug)
        destination = self._directory(destination_slug)
        if destination.exists():
            raise WorkflowPersistenceError("Workflow slug already exists")
        os.replace(source, destination)
        return self._write(
            destination_slug,
            current.workflow_id,
            current.revision + 1,
            current.project,
            current.datasets,
        )

    def _write(
        self,
        slug: str,
        workflow_id: str,
        revision: int,
        project: str,
        datasets: dict[str, str],
    ) -> WorkflowDocument:
        project_bytes = _validate_content(project, _MAX_PROJECT_BYTES, "Project")
        directory = self._directory(slug)
        self._atomic_write(directory / "workflow.rivet-project", project_bytes)
        datasets_dir = directory / "datasets"
        for name, value in datasets.items():
            if not _SLUG.fullmatch(name):
                raise WorkflowPersistenceError("Dataset name must be a safe slug")
            self._atomic_write(
                datasets_dir / f"{name}.json",
                _validate_content(value, _MAX_DATASET_BYTES, "Dataset"),
            )
        document = WorkflowDocument(
            workflow_id, slug, revision, _digest(project_bytes), project, dict(datasets)
        )
        metadata = json.dumps(
            {
                "workflow_id": workflow_id,
                "revision": revision,
                "digest": document.digest,
                "updated_at": int(time.time()),
            },
            sort_keys=True,
        ).encode("utf-8")
        self._atomic_write(directory / ".wright-workflow.json", metadata)
        return document

    def delete(self, slug: str, expected_revision: int) -> str:
        current = self.read(slug)
        if current.revision != expected_revision:
            raise WorkflowRevisionConflict(current.revision, current.digest)
        source = self._directory(current.slug)
        recovery_id = f"{current.workflow_id}-{current.revision}"
        target = self._paths.resolve(f"workflows/.deleted/{recovery_id}")
        target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(source, target)
        return recovery_id

    def recover(self, recovery_id: str, slug: str) -> WorkflowDocument:
        if not re.fullmatch(r"[0-9a-f-]{36,64}", recovery_id):
            raise WorkflowPersistenceError("Invalid recovery ID")
        target = self._directory(slug)
        source = self._paths.resolve(
            f"workflows/.deleted/{recovery_id}", must_exist=True
        )
        if target.exists():
            raise WorkflowPersistenceError("Workflow slug already exists")
        os.replace(source, target)
        return self.read(slug)

    def list_slugs(self) -> list[str]:
        root = self._paths.resolve("workflows")
        if not root.exists():
            return []
        return [
            child.name
            for child in root.iterdir()
            if child.name != ".deleted"
            and child.is_dir()
            and not child.is_symlink()
            and _SLUG.fullmatch(child.name)
        ]
