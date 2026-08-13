"""Bounded HTTP projections for the Engineering Models control plane."""

from __future__ import annotations

import json
from typing import Any

from core.rivet_mcp import reject_secret_material
from pydantic import BaseModel, ConfigDict, Field, model_validator

_FORBIDDEN_PUBLIC_KEYS = {
    "adapter_command",
    "credential",
    "credential_reference",
    "host_path",
    "process_handle",
    "runtime_command",
    "runtime_endpoint",
    "secret",
    "token",
}


def _validate_public(value: Any, *, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in _FORBIDDEN_PUBLIC_KEYS:
                raise ValueError(f"Private model field is forbidden at {path}.{key}")
            _validate_public(item, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_public(item, path=f"{path}[{index}]")


class CatalogSnapshotResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot_id: str = Field(min_length=1, max_length=128)
    catalog_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    freshness: str = Field(min_length=1, max_length=32)
    offline: bool
    channel: str | None = Field(default=None, max_length=128)
    sequence: int | None = Field(default=None, ge=0)
    schema_version: str | None = Field(default=None, max_length=32)
    source_kind: str | None = Field(default=None, max_length=32)
    trust_state: str | None = Field(default=None, max_length=32)


class EngineeringModelResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,95}$")
    display_name: str = Field(min_length=1, max_length=120)
    description: str = Field(max_length=4096)
    tasks: list[str] = Field(min_length=1, max_length=32)
    source: dict[str, Any]
    license: dict[str, Any]
    readiness: str = Field(min_length=1, max_length=64)
    compatibility: dict[str, Any]
    evidence: dict[str, str]
    limitations: list[dict[str, Any]] = Field(max_length=64)
    variants: list[dict[str, Any]] = Field(max_length=64)
    blockers: list[dict[str, Any]] = Field(max_length=128)
    generator: dict[str, Any] | None = None
    manifest_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    entry_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    snapshot: CatalogSnapshotResponse

    @model_validator(mode="after")
    def validate_boundary(self) -> "EngineeringModelResponse":
        document = self.model_dump(mode="json", exclude_none=True)
        reject_secret_material(document)
        _validate_public(document)
        if len(json.dumps(document, separators=(",", ":")).encode("utf-8")) > 64 * 1024:
            raise ValueError("Engineering model response exceeds 64 KiB")
        return self


class EngineeringModelListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot: CatalogSnapshotResponse
    models: list[EngineeringModelResponse] = Field(max_length=100)
    next_cursor: str | None = Field(default=None, max_length=4096)
    total: int = Field(ge=0, le=1000)


__all__ = [
    "CatalogSnapshotResponse",
    "EngineeringModelListResponse",
    "EngineeringModelResponse",
]
