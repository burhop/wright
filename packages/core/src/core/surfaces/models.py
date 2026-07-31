"""Side-effect-neutral values and state transitions for Workspace Surfaces."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any, TypeAlias
from urllib.parse import urlsplit, urlunsplit


_OPAQUE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_HEX_256 = re.compile(r"^[0-9a-f]{64}$")


def _required(value: str, label: str, *, maximum: int = 256) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{label} must not be empty")
    if len(normalized) > maximum:
        raise ValueError(f"{label} must be {maximum} characters or fewer")
    return normalized


def _opaque(value: str, label: str) -> str:
    normalized = _required(value, label, maximum=128)
    if not _OPAQUE_ID.fullmatch(normalized):
        raise ValueError(f"{label} must be an opaque identifier")
    return normalized


def _hash(value: str, label: str) -> str:
    normalized = _required(value, label, maximum=128).lower()
    if not _HEX_256.fullmatch(normalized):
        raise ValueError(f"{label} must be a lowercase SHA-256 hex digest")
    return normalized


@dataclass(frozen=True, slots=True)
class SurfaceId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _opaque(self.value, "surface_id"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class SurfaceInstanceId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _opaque(self.value, "instance_id"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class SurfaceRevision:
    value: int

    def __post_init__(self) -> None:
        if (
            isinstance(self.value, bool)
            or int(self.value) != self.value
            or self.value <= 0
        ):
            raise ValueError("surface revision must be a positive integer")

    def __int__(self) -> int:
        return self.value

    def next(self) -> "SurfaceRevision":
        return SurfaceRevision(self.value + 1)


class SurfaceSourceKind(StrEnum):
    FILE = "file"
    DISPLAY = "display"
    LIVE_APP = "live_app"
    MCP_APP = "mcp_app"
    EXTERNAL_URL = "external_url"


class SurfaceLifecycle(StrEnum):
    DECLARED = "declared"
    STARTING = "starting"
    READY = "ready"
    UNHEALTHY = "unhealthy"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class LiveAppOwnership(StrEnum):
    WRIGHT_OWNED = "wright_owned"
    APPROVED_ATTACH = "approved_attach"


class SharingMode(StrEnum):
    SHARED = "shared"
    ISOLATED = "isolated"


class ProvenanceMode(StrEnum):
    AGENT_GENERATED = "agent_generated"
    DIRECT_EXECUTION = "direct_execution"


class InvalidSurfaceTransition(ValueError):
    def __init__(self, current: SurfaceLifecycle, target: SurfaceLifecycle) -> None:
        super().__init__(
            f"invalid surface transition: {current.value} -> {target.value}"
        )
        self.current = current
        self.target = target


_TRANSITIONS: dict[SurfaceLifecycle, frozenset[SurfaceLifecycle]] = {
    SurfaceLifecycle.DECLARED: frozenset(
        {SurfaceLifecycle.STARTING, SurfaceLifecycle.STOPPED}
    ),
    SurfaceLifecycle.STARTING: frozenset(
        {
            SurfaceLifecycle.READY,
            SurfaceLifecycle.FAILED,
            SurfaceLifecycle.STOPPING,
        }
    ),
    SurfaceLifecycle.READY: frozenset(
        {
            SurfaceLifecycle.UNHEALTHY,
            SurfaceLifecycle.STOPPING,
            SurfaceLifecycle.FAILED,
        }
    ),
    SurfaceLifecycle.UNHEALTHY: frozenset(
        {
            SurfaceLifecycle.READY,
            SurfaceLifecycle.STOPPING,
            SurfaceLifecycle.FAILED,
        }
    ),
    SurfaceLifecycle.STOPPING: frozenset(
        {SurfaceLifecycle.STOPPED, SurfaceLifecycle.FAILED}
    ),
    SurfaceLifecycle.STOPPED: frozenset({SurfaceLifecycle.STARTING}),
    SurfaceLifecycle.FAILED: frozenset({SurfaceLifecycle.STARTING}),
}


def require_surface_transition(
    current: SurfaceLifecycle, target: SurfaceLifecycle
) -> SurfaceLifecycle:
    if target not in _TRANSITIONS[current]:
        raise InvalidSurfaceTransition(current, target)
    return target


def next_generation(current: SurfaceLifecycle, generation: int) -> int:
    if current not in {SurfaceLifecycle.STOPPED, SurfaceLifecycle.FAILED}:
        raise InvalidSurfaceTransition(current, SurfaceLifecycle.STARTING)
    if generation < 1:
        raise ValueError("generation must be positive")
    return generation + 1


@dataclass(frozen=True, slots=True)
class FileSurfaceSource:
    path: str
    file_revision: str
    media_type: str
    provider_id: str

    def __post_init__(self) -> None:
        normalized = self.path.strip().replace("\\", "/")
        parts = tuple(part for part in normalized.split("/") if part not in {"", "."})
        if (
            not normalized
            or normalized.startswith("/")
            or ".." in parts
            or re.match(r"^[A-Za-z]:", normalized)
        ):
            raise ValueError("file path must be workspace-relative without traversal")
        object.__setattr__(self, "path", "/".join(parts))
        object.__setattr__(
            self, "file_revision", _required(self.file_revision, "file_revision")
        )
        object.__setattr__(self, "media_type", _required(self.media_type, "media_type"))
        object.__setattr__(
            self, "provider_id", _required(self.provider_id, "provider_id")
        )

    @property
    def kind(self) -> SurfaceSourceKind:
        return SurfaceSourceKind.FILE

    @property
    def source_id(self) -> str:
        return self.path

    @property
    def source_version(self) -> str:
        return self.file_revision


@dataclass(frozen=True, slots=True)
class DisplaySurfaceSource:
    execution_id: str
    display_id: str
    artifact_revision: int
    durability: str
    media_types: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "execution_id", _opaque(self.execution_id, "execution_id")
        )
        object.__setattr__(self, "display_id", _opaque(self.display_id, "display_id"))
        if self.artifact_revision < 1:
            raise ValueError("artifact_revision must be positive")
        if self.durability not in {"durable", "session", "ephemeral"}:
            raise ValueError("durability must be durable, session, or ephemeral")
        media_types = tuple(
            _required(item, "media_type", maximum=128) for item in self.media_types
        )
        if not media_types:
            raise ValueError("display source requires at least one media type")
        object.__setattr__(self, "media_types", media_types)

    @property
    def kind(self) -> SurfaceSourceKind:
        return SurfaceSourceKind.DISPLAY

    @property
    def source_id(self) -> str:
        return f"{self.execution_id}:{self.display_id}"

    @property
    def source_version(self) -> str:
        return f"{self.execution_id}:{self.display_id}:{self.artifact_revision}"


@dataclass(frozen=True, slots=True)
class LiveAppSurfaceSource:
    manifest_id: str
    manifest_version: str
    manifest_hash: str
    ownership: LiveAppOwnership
    administrator_approved: bool
    sharing_mode: SharingMode | str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "manifest_id", _opaque(self.manifest_id, "manifest_id")
        )
        object.__setattr__(
            self,
            "manifest_version",
            _required(self.manifest_version, "manifest_version"),
        )
        object.__setattr__(
            self, "manifest_hash", _hash(self.manifest_hash, "manifest_hash")
        )
        object.__setattr__(self, "ownership", LiveAppOwnership(self.ownership))
        object.__setattr__(self, "sharing_mode", SharingMode(self.sharing_mode))

    @property
    def kind(self) -> SurfaceSourceKind:
        return SurfaceSourceKind.LIVE_APP

    @property
    def source_id(self) -> str:
        return self.manifest_id

    @property
    def source_version(self) -> str:
        return self.manifest_hash


@dataclass(frozen=True, slots=True)
class McpAppSurfaceSource:
    gateway_session_id: str
    server_id: str
    server_connection_id: str
    resource_uri: str
    content_hash: str
    protocol_version: str
    initial_tool_input: Mapping[str, Any] | None = None
    fallback_result: Mapping[str, Any] | None = None
    declared_host_capabilities: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "gateway_session_id",
            _opaque(self.gateway_session_id, "gateway_session_id"),
        )
        object.__setattr__(self, "server_id", _opaque(self.server_id, "server_id"))
        object.__setattr__(
            self,
            "server_connection_id",
            _opaque(self.server_connection_id, "server_connection_id"),
        )
        uri = _required(self.resource_uri, "resource_uri", maximum=2048)
        if not uri.startswith("ui://"):
            raise ValueError("MCP App resource_uri must use ui://")
        object.__setattr__(self, "resource_uri", uri)
        object.__setattr__(
            self, "content_hash", _hash(self.content_hash, "content_hash")
        )
        object.__setattr__(
            self,
            "protocol_version",
            _required(self.protocol_version, "protocol_version"),
        )
        for label in ("initial_tool_input", "fallback_result"):
            value = getattr(self, label)
            if value is None:
                continue
            if not isinstance(value, Mapping):
                raise ValueError(f"{label} must be a JSON object")
            copied = dict(value)
            try:
                encoded = json.dumps(copied, allow_nan=False, separators=(",", ":"))
            except (TypeError, ValueError) as error:
                raise ValueError(f"{label} must contain JSON values") from error
            if len(encoded.encode("utf-8")) > 1024 * 1024:
                raise ValueError(f"{label} exceeds the 1 MiB surface limit")
            object.__setattr__(self, label, MappingProxyType(copied))
        allowed = {"context.update", "user.message", "open.link"}
        declared = frozenset(str(item) for item in self.declared_host_capabilities)
        if not declared.issubset(allowed):
            raise ValueError("declared_host_capabilities contains an unsupported value")
        object.__setattr__(self, "declared_host_capabilities", declared)

    @property
    def kind(self) -> SurfaceSourceKind:
        return SurfaceSourceKind.MCP_APP

    @property
    def source_id(self) -> str:
        return f"{self.server_connection_id}:{self.resource_uri}"

    @property
    def source_version(self) -> str:
        return self.content_hash


@dataclass(frozen=True, slots=True)
class ExternalUrlSurfaceSource:
    normalized_url: str
    approval_id: str
    view_only: bool = True

    def __post_init__(self) -> None:
        if self.view_only is not True:
            raise ValueError("external URL surfaces must be view-only")
        parts = urlsplit(_required(self.normalized_url, "normalized_url", maximum=4096))
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            raise ValueError("external URL must use http or https with a hostname")
        if parts.username is not None or parts.password is not None:
            raise ValueError("external URL must not contain credentials")
        normalized = urlunsplit(
            (
                parts.scheme.lower(),
                parts.netloc.lower(),
                parts.path or "/",
                parts.query,
                "",
            )
        )
        object.__setattr__(self, "normalized_url", normalized)
        object.__setattr__(
            self, "approval_id", _opaque(self.approval_id, "approval_id")
        )

    @property
    def kind(self) -> SurfaceSourceKind:
        return SurfaceSourceKind.EXTERNAL_URL

    @property
    def source_id(self) -> str:
        return self.approval_id

    @property
    def source_version(self) -> str:
        return hashlib.sha256(self.normalized_url.encode("utf-8")).hexdigest()


SurfaceSource: TypeAlias = (
    FileSurfaceSource
    | DisplaySurfaceSource
    | LiveAppSurfaceSource
    | McpAppSurfaceSource
    | ExternalUrlSurfaceSource
)


def surface_source_to_dict(source: SurfaceSource) -> dict[str, Any]:
    common = {
        "kind": source.kind.value,
        "source_id": source.source_id,
        "source_version": source.source_version,
    }
    if isinstance(source, FileSurfaceSource):
        return {
            **common,
            "path": source.path,
            "file_revision": source.file_revision,
            "media_type": source.media_type,
            "provider_id": source.provider_id,
        }
    if isinstance(source, DisplaySurfaceSource):
        return {
            **common,
            "execution_id": source.execution_id,
            "display_id": source.display_id,
            "artifact_revision": source.artifact_revision,
            "durability": source.durability,
            "media_types": list(source.media_types),
        }
    if isinstance(source, LiveAppSurfaceSource):
        return {
            **common,
            "manifest_id": source.manifest_id,
            "manifest_version": source.manifest_version,
            "manifest_hash": source.manifest_hash,
            "ownership": source.ownership.value,
            "administrator_approved": source.administrator_approved,
            "sharing_mode": source.sharing_mode.value,
        }
    if isinstance(source, McpAppSurfaceSource):
        return {
            **common,
            "gateway_session_id": source.gateway_session_id,
            "server_id": source.server_id,
            "server_connection_id": source.server_connection_id,
            "resource_uri": source.resource_uri,
            "content_hash": source.content_hash,
            "protocol_version": source.protocol_version,
            "initial_tool_input": (
                dict(source.initial_tool_input)
                if source.initial_tool_input is not None
                else None
            ),
            "fallback_result": (
                dict(source.fallback_result)
                if source.fallback_result is not None
                else None
            ),
            "declared_host_capabilities": sorted(
                source.declared_host_capabilities
            ),
        }
    return {
        **common,
        "normalized_url": source.normalized_url,
        "approval_id": source.approval_id,
        "view_only": source.view_only,
    }


def surface_source_from_dict(value: dict[str, Any]) -> SurfaceSource:
    kind = SurfaceSourceKind(value.get("kind"))
    if kind is SurfaceSourceKind.FILE:
        return FileSurfaceSource(
            path=value["path"],
            file_revision=value["file_revision"],
            media_type=value["media_type"],
            provider_id=value["provider_id"],
        )
    if kind is SurfaceSourceKind.DISPLAY:
        return DisplaySurfaceSource(
            execution_id=value["execution_id"],
            display_id=value["display_id"],
            artifact_revision=int(value["artifact_revision"]),
            durability=value["durability"],
            media_types=tuple(value["media_types"]),
        )
    if kind is SurfaceSourceKind.LIVE_APP:
        return LiveAppSurfaceSource(
            manifest_id=value["manifest_id"],
            manifest_version=value["manifest_version"],
            manifest_hash=value["manifest_hash"],
            ownership=LiveAppOwnership(value["ownership"]),
            administrator_approved=bool(value["administrator_approved"]),
            sharing_mode=SharingMode(value["sharing_mode"]),
        )
    if kind is SurfaceSourceKind.MCP_APP:
        return McpAppSurfaceSource(
            gateway_session_id=value["gateway_session_id"],
            # Compatibility for pre-host records that retained only the connection id.
            server_id=value.get("server_id", value["server_connection_id"]),
            server_connection_id=value["server_connection_id"],
            resource_uri=value["resource_uri"],
            content_hash=value["content_hash"],
            protocol_version=value["protocol_version"],
            initial_tool_input=value.get("initial_tool_input"),
            fallback_result=value.get("fallback_result"),
            declared_host_capabilities=frozenset(
                value.get("declared_host_capabilities", ())
            ),
        )
    return ExternalUrlSurfaceSource(
        normalized_url=value["normalized_url"],
        approval_id=value["approval_id"],
        view_only=bool(value["view_only"]),
    )


@dataclass(frozen=True, slots=True)
class GenerationProvenance:
    mode: ProvenanceMode
    prompt: str | None
    no_prompt: bool
    effective_constraints: dict[str, Any]
    script_vault_digest: str
    script_content_hash: str
    script_revision: int
    task_id: str
    execution_id: str
    trace_id: str
    created_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "mode", ProvenanceMode(self.mode))
        if self.mode is ProvenanceMode.AGENT_GENERATED:
            if self.no_prompt or not (self.prompt and self.prompt.strip()):
                raise ValueError("agent-generated provenance requires the exact prompt")
            object.__setattr__(self, "prompt", self.prompt.strip())
        elif self.prompt is not None or not self.no_prompt:
            raise ValueError("direct execution requires an explicit no-prompt marker")
        if not self.script_vault_digest.startswith("sha256:"):
            raise ValueError("script_vault_digest must be content-addressed")
        _hash(self.script_vault_digest.removeprefix("sha256:"), "script_vault_digest")
        object.__setattr__(
            self,
            "script_content_hash",
            _hash(self.script_content_hash, "script_content_hash"),
        )
        if self.script_revision < 1:
            raise ValueError("script_revision must be positive")
        object.__setattr__(self, "task_id", _opaque(self.task_id, "task_id"))
        object.__setattr__(
            self, "execution_id", _opaque(self.execution_id, "execution_id")
        )
        object.__setattr__(
            self, "trace_id", _required(self.trace_id, "trace_id", maximum=64)
        )
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        object.__setattr__(
            self,
            "effective_constraints",
            MappingProxyType(dict(self.effective_constraints)),
        )


def generation_provenance_to_dict(value: GenerationProvenance) -> dict[str, Any]:
    """Serialize protected provenance for workspace-authorized persistence only."""

    return {
        "mode": value.mode.value,
        "prompt": value.prompt,
        "no_prompt": value.no_prompt,
        "effective_constraints": dict(value.effective_constraints),
        "script_vault_digest": value.script_vault_digest,
        "script_content_hash": value.script_content_hash,
        "script_revision": value.script_revision,
        "task_id": value.task_id,
        "execution_id": value.execution_id,
        "trace_id": value.trace_id,
        "created_at": value.created_at.isoformat(),
    }


def generation_provenance_from_dict(value: dict[str, Any]) -> GenerationProvenance:
    """Restore protected provenance from its version-1 durable representation."""

    return GenerationProvenance(
        mode=ProvenanceMode(value["mode"]),
        prompt=value.get("prompt"),
        no_prompt=bool(value["no_prompt"]),
        effective_constraints=dict(value["effective_constraints"]),
        script_vault_digest=value["script_vault_digest"],
        script_content_hash=value["script_content_hash"],
        script_revision=int(value["script_revision"]),
        task_id=value["task_id"],
        execution_id=value["execution_id"],
        trace_id=value["trace_id"],
        created_at=datetime.fromisoformat(value["created_at"]),
    )


@dataclass(frozen=True, slots=True)
class SurfaceDescriptor:
    schema_version: int
    surface_id: SurfaceId
    workspace_id: str
    source: SurfaceSource
    title: str
    lifecycle: SurfaceLifecycle
    revision: SurfaceRevision
    created_at: datetime
    updated_at: datetime
    instance: dict[str, Any] | None = None
    presentations: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    capabilities: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    diagnostic_summary: dict[str, Any] | None = None
    generation_provenance: GenerationProvenance | None = None

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("schema_version must be 1")
        if not isinstance(self.surface_id, SurfaceId):
            object.__setattr__(self, "surface_id", SurfaceId(str(self.surface_id)))
        object.__setattr__(
            self, "workspace_id", _opaque(self.workspace_id, "workspace_id")
        )
        object.__setattr__(self, "title", _required(self.title, "title", maximum=256))
        object.__setattr__(self, "lifecycle", SurfaceLifecycle(self.lifecycle))
        if not isinstance(self.revision, SurfaceRevision):
            object.__setattr__(self, "revision", SurfaceRevision(int(self.revision)))
        if self.created_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise ValueError("created_at and updated_at must be timezone-aware")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at must not be earlier than created_at")
        object.__setattr__(self, "presentations", tuple(self.presentations))
        object.__setattr__(self, "capabilities", tuple(self.capabilities))

    def with_lifecycle(
        self, target: SurfaceLifecycle, *, updated_at: datetime
    ) -> "SurfaceDescriptor":
        require_surface_transition(self.lifecycle, target)
        return replace(
            self,
            lifecycle=target,
            revision=self.revision.next(),
            updated_at=updated_at,
        )
