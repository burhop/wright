"""Preserve optional interface source and its binding manifest without activating it."""

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

from .contracts import Contract, Identifier
from .interaction_schema import (
    INTERACTION_VERSION,
    NavigationTarget,
    ProcessCapability,
    ProcessRef,
    Text,
    checked_value_schema,
    relative_locator,
    unique_ids,
)

UI_VERSION = "wright.process-ui/1"


Version = Annotated[str, StringConstraints(pattern=r"^\d+\.\d+\.\d+$", max_length=32)]


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
