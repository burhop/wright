"""Versioned Pydantic transport projections for Workspace Surfaces."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Annotated, Any, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.surfaces.models import (
    DisplaySurfaceSource,
    ExternalUrlSurfaceSource,
    FileSurfaceSource,
    LiveAppOwnership,
    LiveAppSurfaceSource,
    McpAppSurfaceSource,
    SurfaceDescriptor,
)
from workspace_service.surfaces.service import ActorRole, SurfaceActor


class _ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ExternalUrlDeclareRequest(_ContractModel):
    schema_version: Literal[1] = Field(alias="schemaVersion")
    kind: Literal["external_url"]
    url: str = Field(min_length=1, max_length=4096)
    approval: Literal["explicit_view_only_instance"]

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        parts = urlsplit(value)
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            raise ValueError("url must be an absolute http or https URL")
        if parts.username is not None or parts.password is not None:
            raise ValueError("url must not contain credentials")
        return value


class LiveAppDeclareRequest(_ContractModel):
    schema_version: Literal[1] = Field(alias="schemaVersion")
    kind: Literal["live_app"]
    manifest: dict[str, Any]

    @field_validator("manifest")
    @classmethod
    def validate_manifest_identity(cls, value: dict[str, Any]) -> dict[str, Any]:
        for name in ("id", "title", "version", "launch"):
            if name not in value:
                raise ValueError(f"manifest requires {name}")
        return value


DeclareSurfaceRequest = Annotated[
    ExternalUrlDeclareRequest | LiveAppDeclareRequest, Field(discriminator="kind")
]


def declare_request_to_domain(
    body: DeclareSurfaceRequest,
    *,
    actor: SurfaceActor,
    idempotency_key: str,
):
    if isinstance(body, ExternalUrlDeclareRequest):
        approval_id = (
            "approval-"
            + hashlib.sha256(
                f"{actor.user_id}:{actor.workspace_id}:{idempotency_key}".encode()
            ).hexdigest()[:24]
        )
        source = ExternalUrlSurfaceSource(
            normalized_url=body.url, approval_id=approval_id, view_only=True
        )
        return source, urlsplit(body.url).hostname or "External application"
    manifest = body.manifest
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    launch = manifest["launch"]
    ownership = (
        LiveAppOwnership.APPROVED_ATTACH
        if launch.get("mode") == "attach"
        else LiveAppOwnership.WRIGHT_OWNED
    )
    source = LiveAppSurfaceSource(
        manifest_id=str(manifest["id"]),
        manifest_version=str(manifest["version"]),
        manifest_hash=hashlib.sha256(encoded).hexdigest(),
        ownership=ownership,
        administrator_approved=actor.role is ActorRole.ADMIN,
        sharing_mode=str(manifest.get("presentation", {}).get("sharing", "shared")),
    )
    return source, str(manifest["title"])


class FileSourceResponse(_ContractModel):
    kind: Literal["file"] = "file"
    source_id: str = Field(alias="sourceId")
    source_version: str = Field(alias="sourceVersion")
    path: str
    media_type: str = Field(alias="mediaType")


class DisplaySourceResponse(_ContractModel):
    kind: Literal["display"] = "display"
    source_id: str = Field(alias="sourceId")
    source_version: str = Field(alias="sourceVersion")
    display_id: str = Field(alias="displayId")
    revision: int


class LiveAppSourceResponse(_ContractModel):
    kind: Literal["live_app"] = "live_app"
    source_id: str = Field(alias="sourceId")
    source_version: str = Field(alias="sourceVersion")
    manifest_id: str = Field(alias="manifestId")


class McpAppSourceResponse(_ContractModel):
    kind: Literal["mcp_app"] = "mcp_app"
    source_id: str = Field(alias="sourceId")
    source_version: str = Field(alias="sourceVersion")
    server_id: str = Field(alias="serverId")
    resource_uri: str = Field(alias="resourceUri")
    content_hash: str = Field(alias="contentHash")


class ExternalUrlSourceResponse(_ContractModel):
    kind: Literal["external_url"] = "external_url"
    source_id: str = Field(alias="sourceId")
    source_version: str = Field(alias="sourceVersion")
    display_url: str = Field(alias="displayUrl")
    view_only: Literal[True] = Field(alias="viewOnly")


SurfaceSourceResponse = Annotated[
    FileSourceResponse
    | DisplaySourceResponse
    | LiveAppSourceResponse
    | McpAppSourceResponse
    | ExternalUrlSourceResponse,
    Field(discriminator="kind"),
]


def _source_response(source) -> SurfaceSourceResponse:
    common = {
        "sourceId": source.source_id,
        "sourceVersion": source.source_version,
    }
    if isinstance(source, FileSurfaceSource):
        return FileSourceResponse(
            **common, path=source.path, mediaType=source.media_type
        )
    if isinstance(source, DisplaySurfaceSource):
        return DisplaySourceResponse(
            **common,
            displayId=source.display_id,
            revision=source.artifact_revision,
        )
    if isinstance(source, LiveAppSurfaceSource):
        return LiveAppSourceResponse(**common, manifestId=source.manifest_id)
    if isinstance(source, McpAppSurfaceSource):
        return McpAppSourceResponse(
            **common,
            serverId=source.server_id,
            resourceUri=source.resource_uri,
            contentHash=source.content_hash,
        )
    assert isinstance(source, ExternalUrlSurfaceSource)
    return ExternalUrlSourceResponse(
        **common, displayUrl=source.normalized_url, viewOnly=True
    )


class SurfaceDescriptorResponse(_ContractModel):
    schema_version: Literal[1] = Field(alias="schemaVersion")
    surface_id: str = Field(alias="surfaceId")
    workspace_id: str = Field(alias="workspaceId")
    source: SurfaceSourceResponse
    title: str
    lifecycle: str
    instance: dict[str, Any] | None = None
    presentations: list[dict[str, Any]]
    capabilities: list[dict[str, Any]]
    diagnostic_summary: dict[str, Any] | None = Field(
        default=None, alias="diagnosticSummary"
    )
    revision: int
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    @classmethod
    def from_domain(cls, descriptor: SurfaceDescriptor):
        return cls(
            schemaVersion=1,
            surfaceId=str(descriptor.surface_id),
            workspaceId=descriptor.workspace_id,
            source=_source_response(descriptor.source),
            title=descriptor.title,
            lifecycle=descriptor.lifecycle.value,
            instance=descriptor.instance,
            presentations=list(descriptor.presentations),
            capabilities=list(descriptor.capabilities),
            diagnosticSummary=descriptor.diagnostic_summary,
            revision=int(descriptor.revision),
            createdAt=descriptor.created_at,
            updatedAt=descriptor.updated_at,
        )


class SurfaceListResponse(_ContractModel):
    items: list[SurfaceDescriptorResponse]
