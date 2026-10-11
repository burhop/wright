"""Saved frontend/interface and coding-role contracts; no execution authority."""

from __future__ import annotations

import base64
import binascii
from typing import Annotated, Literal

from pydantic import (
    Field,
    StrictBool,
    StringConstraints,
    field_validator,
    model_validator,
)

from .process_interactions import (
    INTERACTION_VERSION,
    NavigationTarget,
    ProcessCapability,
    ProcessRef,
    Reason,
    Timestamp,
    checked_value_schema,
    unique_ids,
)
from .process_validation import (
    Contract,
    Digest,
    Identifier,
    Text,
    canonical_json,
    relative_locator,
)

UI_VERSION = "wright.process-ui/1"
Version = Annotated[str, StringConstraints(pattern=r"^\d+\.\d+\.\d+$", max_length=32)]


class CodingRole(Contract):
    role: Literal["process-ui-author"] = "process-ui-author"
    version: Literal["1"] = "1"
    instructions_version: Identifier
    instructions_digest: Digest
    model_policy: Literal["inherit_default"] = "inherit_default"
    allowed_tools: tuple[
        Literal["read-interface-contract", "submit-interface-source"], ...
    ] = ()
    max_repairs: Annotated[int, Field(strict=True, ge=0, le=2)] = 2


class RoleResolution(Contract):
    profile: CodingRole
    adapter: Identifier
    model_reference: Identifier
    configuration_digest: Digest
    effective_instructions_digest: Digest
    capability_scope: tuple[Identifier, ...] = ()


class InterfaceBinding(Contract):
    binding_id: Identifier
    kind: Literal[
        "input", "output", "assessment", "interaction", "observation", "action"
    ]
    selector: Identifier
    block_id: Identifier | None = None
    port_id: Identifier | None = None
    expected_schema: dict | None = None
    required: StrictBool = True
    fallback: Text | None = None

    @field_validator("expected_schema")
    @classmethod
    def schema_subset(cls, value):
        return checked_value_schema(value) if value is not None else None

    @model_validator(mode="after")
    def optional_fallback(self):
        if not self.required and not self.fallback:
            raise ValueError("Optional binding requires an explicit fallback")
        return self


class InterfaceManifest(Contract):
    schema_version: Literal["wright.process-ui/1"] = UI_VERSION
    ui_id: Identifier
    revision_id: Identifier
    parent_revision: Identifier | None = None
    title: Text
    process: ProcessRef
    interaction_version: Literal["wright.process-interaction/1"] = INTERACTION_VERSION
    client_version: Version
    kit_version: Version
    bindings: tuple[InterfaceBinding, ...] = Field(default=(), max_length=256)
    capabilities: tuple[ProcessCapability, ...] = (
        "process.read",
        "process.results",
        "process.navigate",
    )
    navigation: tuple[NavigationTarget, ...] = Field(default=(), max_length=256)
    viewers: tuple[Identifier, ...] = ()

    @model_validator(mode="after")
    def unique_bindings(self):
        unique_ids(self.bindings, "binding_id")
        if len(set(self.capabilities)) != len(self.capabilities):
            raise ValueError("Requested capabilities must be unique")
        return self


class SourceAsset(Contract):
    """Bounded local raster asset. No executable SVG, HTML or remote URL."""

    media_type: Literal["image/png", "image/jpeg", "image/webp", "image/gif"]
    data_base64: Annotated[str, Field(max_length=13_981_016)]

    def decoded(self) -> bytes:
        try:
            return base64.b64decode(self.data_base64, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ValueError("Asset must contain valid base64 bytes") from exc

    @model_validator(mode="after")
    def raster_bytes(self):
        content = self.decoded()
        signatures = {
            "image/png": content.startswith(b"\x89PNG\r\n\x1a\n"),
            "image/jpeg": content.startswith(b"\xff\xd8\xff"),
            "image/gif": content.startswith((b"GIF87a", b"GIF89a")),
            "image/webp": content.startswith(b"RIFF") and content[8:12] == b"WEBP",
        }
        if not signatures[self.media_type] or len(content) > 10_485_760:
            raise ValueError(
                "Asset must match its supported raster type and 10 MiB bound"
            )
        return self


class SourceEnvelope(Contract):
    files: dict[str, str] = Field(min_length=1, max_length=32)
    assets: dict[str, SourceAsset] = Field(default_factory=dict, max_length=31)

    @field_validator("files")
    @classmethod
    def fixed_entry(cls, value):
        if "App.tsx" not in value:
            raise ValueError("Interface source requires App.tsx")
        total = 0
        for path, content in value.items():
            relative_locator(path)
            if path not in {"App.tsx", "style.css"}:
                raise ValueError("Only fixed frontend source files are accepted")
            total += len(content.encode("utf-8"))
        if total > 1_048_576:
            raise ValueError("Interface source exceeds 1 MiB")
        return value

    @model_validator(mode="after")
    def confined_assets(self):
        if len(self.files) + len(self.assets) > 32:
            raise ValueError("Interface envelope exceeds 32 source/asset files")
        total = 0
        suffixes = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/webp": ".webp",
            "image/gif": ".gif",
        }
        for path, asset in self.assets.items():
            relative_locator(path)
            if not path.startswith("assets/") or not path.endswith(
                suffixes[asset.media_type]
            ):
                raise ValueError(
                    "Asset requires a confined assets/ path and matching extension"
                )
            total += len(asset.decoded())
        if total > 10_485_760:
            raise ValueError("Interface assets exceed 10 MiB")
        return self


class BuildReport(Contract):
    build_id: Identifier
    source_digest: Digest
    manifest_digest: Digest
    toolchain_digest: Digest
    bundle_digest: Digest | None = None
    state: Literal["built", "failed", "cancelled"]
    created_at: Timestamp
    diagnostics: tuple[Reason, ...] = Field(default=(), max_length=64)
    bundled_bytes: Annotated[int, Field(strict=True, ge=0, le=31_457_280)] = 0

    @model_validator(mode="after")
    def successful_bundle(self):
        if self.state == "built" and not self.bundle_digest:
            raise ValueError("Successful build requires its exact bundle digest")
        if self.state == "failed" and not self.diagnostics:
            raise ValueError("Failed build requires an actionable diagnostic")
        return self


class Compatibility(Contract):
    ui_id: Identifier
    revision_id: Identifier
    current_process: ProcessRef
    state: Literal["compatible", "incompatible", "unsupported"]
    reasons: tuple[Reason, ...] = ()
    optional_absences: tuple[Reason, ...] = ()

    @model_validator(mode="after")
    def blocked_reason(self):
        if self.state != "compatible" and not self.reasons:
            raise ValueError("Incompatible interface requires a focused correction")
        return self


class InterfaceRevision(Contract):
    manifest: InterfaceManifest
    source_digest: Digest
    build: BuildReport
    role_resolution: RoleResolution
    generation_request_digest: Digest
    created_at: Timestamp
    previewed_at: Timestamp

    @model_validator(mode="after")
    def exact_build(self):
        if (
            self.build.state != "built"
            or self.build.source_digest != self.source_digest
        ):
            raise ValueError(
                "Saved interface requires its successful exact-source build"
            )
        from .process_validation import canonical_digest

        if self.build.manifest_digest != canonical_digest(self.manifest):
            raise ValueError("Build manifest digest does not match the saved interface")
        return self


class ProcessUI(Contract):
    ui_id: Identifier
    process: ProcessRef
    title: Text
    active_revision: Identifier | None = None
    archived: StrictBool = False
    created_at: Timestamp
    updated_at: Timestamp


class AuthoringJob(Contract):
    job_id: Identifier
    request_id: Identifier
    request_digest: Digest
    process: ProcessRef
    base_revision: Identifier | None = None
    role_resolution: RoleResolution
    state: Literal[
        "queued",
        "resolving",
        "generating",
        "validating",
        "building",
        "preview_ready",
        "saved",
        "failed",
        "cancelled",
    ]
    repair_attempt: Annotated[int, Field(strict=True, ge=0, le=2)] = 0
    revision_id: Identifier | None = None
    created_at: Timestamp
    updated_at: Timestamp
    diagnostics: tuple[Reason, ...] = Field(default=(), max_length=64)

    @model_validator(mode="after")
    def persisted_budget(self):
        if self.repair_attempt > self.role_resolution.profile.max_repairs:
            raise ValueError("Authoring repair budget exhausted")
        if self.state in {"preview_ready", "saved"} and not self.revision_id:
            raise ValueError("Ready authoring job requires its built revision")
        if self.state == "failed" and not self.diagnostics:
            raise ValueError("Failed authoring job requires a diagnostic")
        return self


def contract_schemas() -> dict[str, dict]:
    """Deterministic schemas for API, shared frontend fixtures and installed docs."""
    from .process_interactions import (
        InputSnapshot,
        InteractionResponse,
        InteractionSnapshot,
        StartReceipt,
        ProcessRunEventPage,
        ProcessCancellationReceipt,
        NavigationResolution,
    )

    schemas = {
        model.__name__: model.model_json_schema()
        for model in (
            InteractionSnapshot,
            InputSnapshot,
            StartReceipt,
            ProcessRunEventPage,
            ProcessCancellationReceipt,
            NavigationResolution,
            InteractionResponse,
            InterfaceManifest,
            InterfaceRevision,
            Compatibility,
            ProcessUI,
            SourceEnvelope,
            CodingRole,
            AuthoringJob,
        )
    }
    canonical_json(schemas)
    return schemas
