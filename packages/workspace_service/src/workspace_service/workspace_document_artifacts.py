"""Confined, immutable publication and read authority for text documents."""

from __future__ import annotations

import hashlib
import os
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote

from data_vault import (
    WorkspaceArtifactRecord,
    WorkspaceArtifactRepository,
)
from tool_registry.gateway_models import (
    GatewayError,
    GatewayErrorCode,
    GatewayResource,
    GatewaySessionContext,
)
from tool_registry.gateway_resources import ResourceContent

from .workspace_path import WorkspacePath


WORKSPACE_DOCUMENT_TOOL_NAME = "wright-workspace-files__write_text_document"
WORKSPACE_DOCUMENT_PROVIDER_ID = "wright-workspace-files"
WORKSPACE_WRITE_APPROVAL = "workspace_write_approval"
MAX_DOCUMENT_BYTES = 1024 * 1024

TEXT_MEDIA_BY_EXTENSION = {
    ".csv": "text/csv",
    ".json": "application/json",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
    ".txt": "text/plain",
    ".yaml": "application/yaml",
    ".yml": "application/yaml",
}
_WINDOWS_DEVICE = re.compile(r"(?i)^(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?$")


class WorkspaceDocumentArtifactError(ValueError):
    pass


def document_producer_declaration() -> dict[str, object]:
    return {
        "effect_kind": "workspace_document",
        "artifact_output": True,
        "native_format": False,
        "required_approvals": [WORKSPACE_WRITE_APPROVAL],
    }


def document_producer_declaration_digest() -> str:
    from core.rivet_mcp import canonical_digest

    return canonical_digest(document_producer_declaration())


def _safe_relative_path(
    root: str, value: object, media_type: object
) -> tuple[str, Path, str]:
    if not isinstance(value, str) or not value or len(value) > 512:
        raise WorkspaceDocumentArtifactError(
            "Document path must be a bounded relative path"
        )
    normalized = value.replace("\\", "/")
    parts = tuple(part for part in normalized.split("/") if part not in {"", "."})
    if any(part.startswith(".") for part in parts):
        raise WorkspaceDocumentArtifactError(
            "Hidden and Wright-owned paths are not available to document workflows"
        )
    if any(_WINDOWS_DEVICE.fullmatch(part) for part in parts):
        raise WorkspaceDocumentArtifactError("Device paths are not allowed")
    try:
        target = WorkspacePath(root).resolve(normalized)
    except ValueError as error:
        raise WorkspaceDocumentArtifactError(str(error)) from error
    extension = target.suffix.lower()
    expected_media = TEXT_MEDIA_BY_EXTENSION.get(extension)
    if expected_media is None:
        raise WorkspaceDocumentArtifactError(
            "Document path must use a reviewed text extension"
        )
    if not isinstance(media_type, str) or media_type != expected_media:
        raise WorkspaceDocumentArtifactError(
            f"Document media type must be {expected_media} for {extension}"
        )
    return "/".join(parts), target, expected_media


def _verify_bytes(record: WorkspaceArtifactRecord, target: Path) -> bytes:
    try:
        payload = target.read_bytes()
    except (FileNotFoundError, OSError) as error:
        raise WorkspaceDocumentArtifactError("Artifact is unavailable") from error
    if (
        len(payload) != record.byte_count
        or hashlib.sha256(payload).hexdigest() != record.sha256
    ):
        raise WorkspaceDocumentArtifactError("Artifact integrity could not be verified")
    return payload


class WorkspaceDocumentArtifactService:
    def __init__(self, repository: WorkspaceArtifactRepository) -> None:
        self.repository = repository

    def publish(
        self,
        *,
        session: GatewaySessionContext,
        relative_path: object,
        content: object,
        media_type: object,
        overwrite: object,
        request_id: str,
        correlation_id: str,
    ) -> WorkspaceArtifactRecord:
        if overwrite not in {None, False}:
            raise WorkspaceDocumentArtifactError(
                "Document overwrite is not supported; choose a new path"
            )
        if not isinstance(content, str):
            raise WorkspaceDocumentArtifactError("Document content must be UTF-8 text")
        try:
            payload = content.encode("utf-8", errors="strict")
        except UnicodeError as error:
            raise WorkspaceDocumentArtifactError(
                "Document content must be valid UTF-8 text"
            ) from error
        if len(payload) > MAX_DOCUMENT_BYTES:
            raise WorkspaceDocumentArtifactError(
                f"Document content exceeds the {MAX_DOCUMENT_BYTES}-byte limit"
            )
        normalized, target, safe_media = _safe_relative_path(
            session.workspace_path, relative_path, media_type
        )
        workspace = WorkspacePath(session.workspace_path)
        parent_parts = normalized.split("/")[:-1]
        current = workspace.root
        for part in parent_parts:
            current = current / part
            try:
                current.mkdir()
            except FileExistsError:
                pass
            if not current.is_dir():
                raise WorkspaceDocumentArtifactError(
                    "Document parent is not a directory"
                )
            workspace.resolve(
                str(current.relative_to(workspace.root)).replace("\\", "/")
            )
        # Re-resolve after parent creation so a link/reparse race fails closed.
        target = workspace.resolve(normalized)
        temporary = target.with_name(f".{target.name}.wright-{uuid.uuid4().hex}.tmp")
        digest = hashlib.sha256(payload).hexdigest()
        artifact_id = f"artifact-{uuid.uuid4().hex}"
        published = False
        try:
            descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                with os.fdopen(descriptor, "wb", closefd=True) as stream:
                    stream.write(payload)
                    stream.flush()
                    os.fsync(stream.fileno())
            except Exception:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
                raise
            try:
                os.link(temporary, target)
            except FileExistsError as error:
                raise WorkspaceDocumentArtifactError(
                    "Document already exists; choose a new path"
                ) from error
            published = True
            record = WorkspaceArtifactRecord(
                artifact_id=artifact_id,
                workspace_id=session.workspace_id,
                session_id=session.binding_session_id or session.session_id,
                principal_id=session.principal_id,
                relative_path=normalized,
                media_type=safe_media,
                sha256=digest,
                byte_count=len(payload),
                producer_provider_id=WORKSPACE_DOCUMENT_PROVIDER_ID,
                producer_tool_name=WORKSPACE_DOCUMENT_TOOL_NAME,
                producer_declaration_digest=document_producer_declaration_digest(),
                request_id=request_id,
                correlation_id=correlation_id,
                created_at=datetime.now(UTC),
            )
            try:
                self.repository.insert(record)
            except Exception:
                # Compensate only the just-published bytes and only while their
                # identity remains exactly the bytes produced by this request.
                try:
                    if (
                        published
                        and target.is_file()
                        and os.path.samefile(temporary, target)
                        and hashlib.sha256(target.read_bytes()).hexdigest() == digest
                    ):
                        target.unlink()
                finally:
                    raise
            return record
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

    def list_resources(
        self, session: GatewaySessionContext
    ) -> tuple[GatewayResource, ...]:
        scope_session = session.binding_session_id or session.session_id
        return tuple(
            GatewayResource(
                uri=f"wright://artifact/{session.workspace_id}/{record.artifact_id}",
                name=Path(record.relative_path).name,
                description="Verified workspace document",
                mime_type=record.media_type,
                provenance={
                    "artifact_id": record.artifact_id,
                    "sha256": record.sha256,
                    "bytes": record.byte_count,
                },
            )
            for record in self.repository.list_for_scope(
                workspace_id=session.workspace_id,
                session_id=scope_session,
            )
        )

    def read_resource(
        self, session: GatewaySessionContext, uri: str
    ) -> ResourceContent:
        prefix = f"wright://artifact/{session.workspace_id}/"
        artifact_id = (
            unquote(uri.removeprefix(prefix)) if uri.startswith(prefix) else ""
        )
        record = self.repository.get(artifact_id, workspace_id=session.workspace_id)
        scope_session = session.binding_session_id or session.session_id
        if record is None or record.session_id != scope_session:
            raise GatewayError(
                GatewayErrorCode.NOT_FOUND, "Artifact resource not found"
            )
        try:
            target = WorkspacePath(session.workspace_path).resolve(
                record.relative_path, must_exist=True
            )
            payload = _verify_bytes(record, target)
        except (ValueError, FileNotFoundError, WorkspaceDocumentArtifactError) as error:
            raise GatewayError(
                GatewayErrorCode.NOT_FOUND,
                "Artifact resource is unavailable or failed integrity verification",
            ) from error
        return ResourceContent(payload, record.media_type)

    def read_for_run(
        self,
        *,
        workspace_id: str,
        session_id: str,
        workspace_path: str,
        run_id: str,
        artifact_id: str,
    ) -> tuple[WorkspaceArtifactRecord, bytes]:
        record = self.repository.get_for_run(
            workspace_id=workspace_id,
            session_id=session_id,
            run_id=run_id,
            artifact_id=artifact_id,
        )
        if record is None:
            raise WorkspaceDocumentArtifactError("Artifact is unavailable")
        target = WorkspacePath(workspace_path).resolve(
            record.relative_path, must_exist=True
        )
        return record, _verify_bytes(record, target)
