"""Bounded, allowlisted support-diagnostic contracts.

The objects in this module are safe projections. They never accept raw command,
prompt, model-feature, artifact, environment, path, log, or authority payloads.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Collection, Mapping
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


MAX_EXPORT_BYTES = 2 * 1024 * 1024
MAX_RECORDS = 2_000
MAX_SAFE_STRING_LENGTH = 4_096
MAX_COLLECTION_ITEMS = 100
MAX_PROVIDERS = 64
MAX_FAILURES = 64
MAX_CATEGORIES = 32

_SAFE_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_REASON_CODE = re.compile(r"^[A-Z0-9_]{1,80}$")
_DIGEST = re.compile(r"^sha256:[a-f0-9]{64}$")
_SENSITIVE_KEY = re.compile(
    r"(?:token|secret|password|passwd|api[_-]?key|authorization|credential|"
    r"cookie|environment|command|arguments?|prompt|request|response|body|"
    r"model[_-]?features?|artifact|filename|path|endpoint|authority|database|"
    r"process|tool[_-]?(?:input|output|result)|raw[_-]?log)",
    re.IGNORECASE,
)
_ASSIGNMENT = re.compile(
    r"(?i)\b(token|secret|password|passwd|api[_-]?key|authorization|cookie)"
    r"\s*[=:]\s*[^\s,;]+"
)
_BEARER = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]+=*")
_WINDOWS_PATH = re.compile(r"(?i)(?:[A-Z]:\\|\\\\)[^\s\"']+")
_POSIX_PATH = re.compile(r"(?<![:A-Za-z0-9])/(?:home|users|private|tmp|var)/[^\s\"']+")
_LOCAL_ENDPOINT = re.compile(
    r"(?i)\b(?:https?|wss?)://(?:localhost|127\.0\.0\.1|\[::1\])(?::\d+)?[^\s\"']*"
)


class DiagnosticPolicyError(ValueError):
    """A diagnostic value cannot cross the safe projection boundary."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class DiagnosticModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def digest_value(value: str | bytes) -> str:
    payload = value.encode("utf-8") if isinstance(value, str) else value
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _truncate(value: str) -> str:
    if len(value) <= MAX_SAFE_STRING_LENGTH:
        return value
    return value[: MAX_SAFE_STRING_LENGTH - 1] + "…"


def _redact_text(value: str) -> str:
    cleaned = _ASSIGNMENT.sub(lambda match: f"{match.group(1)}=[REDACTED]", value)
    cleaned = _BEARER.sub("Bearer [REDACTED]", cleaned)
    cleaned = _WINDOWS_PATH.sub("[REDACTED_PATH]", cleaned)
    cleaned = _POSIX_PATH.sub("[REDACTED_PATH]", cleaned)
    cleaned = _LOCAL_ENDPOINT.sub("[REDACTED_ENDPOINT]", cleaned)
    return _truncate(cleaned)


def sanitize_untrusted(
    value: Any,
    *,
    allowed_keys: Collection[str] | None = None,
) -> Any:
    """Recursively redact untrusted material and enforce collection limits.

    Production snapshot assembly does not depend on this function to make raw
    state safe; it constructs allowlisted typed projections. This helper is the
    fail-closed boundary for probes or exception-safe metadata that cannot be
    typed at source.
    """

    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for index, (raw_key, item) in enumerate(value.items()):
            if index >= MAX_COLLECTION_ITEMS:
                break
            key = _truncate(str(raw_key))
            if _SENSITIVE_KEY.search(key) or (
                allowed_keys is not None and key not in allowed_keys
            ):
                result[key] = "[REDACTED]"
            else:
                result[key] = sanitize_untrusted(item, allowed_keys=allowed_keys)
        return result
    if isinstance(value, (list, tuple, set, frozenset)):
        return [
            sanitize_untrusted(item, allowed_keys=allowed_keys)
            for item in list(value)[:MAX_COLLECTION_ITEMS]
        ]
    if isinstance(value, str):
        return _redact_text(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return "[REDACTED]"


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as exc:
        raise DiagnosticPolicyError("DIAGNOSTIC_SERIALIZATION_FAILED") from exc
    if len(encoded) > MAX_EXPORT_BYTES:
        raise DiagnosticPolicyError("DIAGNOSTIC_EXPORT_TOO_LARGE")
    return encoded


def canonical_snapshot_bytes(value: Mapping[str, Any]) -> bytes:
    """Serialize the exact inert JSON attachment bytes."""

    return canonical_json_bytes(value)


def require_safe_identifier(
    value: str, *, code: str = "INVALID_DIAGNOSTIC_SCOPE"
) -> str:
    if not _SAFE_ID.fullmatch(value):
        raise DiagnosticPolicyError(code)
    return value


def require_reason_code(value: str) -> str:
    if not _REASON_CODE.fullmatch(value):
        raise DiagnosticPolicyError("INVALID_DIAGNOSTIC_REASON")
    return value


class DiagnosticDisposition(StrEnum):
    INCLUDED = "included"
    OMITTED = "omitted"
    REDACTED = "redacted"
    TRUNCATED = "truncated"


class DiagnosticStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    BLOCKED = "blocked"
    FAILED = "failed"


class ProviderStatus(StrEnum):
    READY = "ready"
    DEGRADED = "degraded"
    BLOCKED = "blocked"
    FAILED = "failed"
    UNKNOWN = "unknown"


class CleanupState(StrEnum):
    CLEAN = "clean"
    RESIDUE_POSSIBLE = "residue-possible"
    UNKNOWN = "unknown"


class DiagnosticScope(DiagnosticModel):
    session_id: str | None = Field(default=None, max_length=128)
    scenario_run_id: str | None = Field(default=None, max_length=128)

    @field_validator("session_id", "scenario_run_id")
    @classmethod
    def _safe_id(cls, value: str | None) -> str | None:
        return require_safe_identifier(value) if value is not None else None


class DiagnosticSummary(DiagnosticModel):
    status: DiagnosticStatus
    reason: str
    next_action: str

    @field_validator("reason", "next_action")
    @classmethod
    def _reason(cls, value: str) -> str:
        return require_reason_code(value)


class ProviderDiagnostic(DiagnosticModel):
    kind: Literal["mcp", "model", "rivet", "gateway", "runtime", "storage"]
    provider_id: str = Field(max_length=128)
    status: ProviderStatus
    identity_digest: str

    @field_validator("provider_id")
    @classmethod
    def _provider_id(cls, value: str) -> str:
        return require_safe_identifier(value)

    @field_validator("identity_digest")
    @classmethod
    def _digest(cls, value: str) -> str:
        if not _DIGEST.fullmatch(value):
            raise ValueError("invalid digest")
        return value


class CatalogSnapshotDiagnostic(DiagnosticModel):
    channel: str = Field(max_length=32)
    sequence: int = Field(ge=0)
    digest: str
    state: Literal["bundled", "active", "rollback", "unavailable"]

    @field_validator("digest")
    @classmethod
    def _digest(cls, value: str) -> str:
        if not _DIGEST.fullmatch(value):
            raise ValueError("invalid digest")
        return value


class StorageDiagnostic(DiagnosticModel):
    root: Literal[
        "data", "config", "workspaces", "models", "catalog", "reports", "manager"
    ]
    persistence: Literal["native-data-root", "docker-named-volume", "bundled-read-only"]
    available: bool
    writable: bool


class StateInventory(DiagnosticModel):
    schema_version: Literal["1.0"] = "1.0"
    data_schema: int = Field(ge=0)
    catalog_snapshot: CatalogSnapshotDiagnostic
    counts: dict[str, int] = Field(default_factory=dict, max_length=16)
    digests: dict[str, str] = Field(default_factory=dict, max_length=16)
    storage: tuple[StorageDiagnostic, ...] = Field(default_factory=tuple, max_length=12)

    @field_validator("counts")
    @classmethod
    def _counts(cls, value: dict[str, int]) -> dict[str, int]:
        if any(count < 0 or count > 1_000_000 for count in value.values()):
            raise ValueError("invalid count")
        return value

    @field_validator("digests")
    @classmethod
    def _digests(cls, value: dict[str, str]) -> dict[str, str]:
        if any(not _DIGEST.fullmatch(digest) for digest in value.values()):
            raise ValueError("invalid digest")
        return value


class DiagnosticFailure(DiagnosticModel):
    stage: str = Field(pattern=r"^[a-z0-9._-]{1,64}$")
    provider_kind: Literal["mcp", "model", "rivet", "gateway", "runtime", "storage"]
    reason: str
    cleanup: CleanupState
    recovery: str

    @field_validator("reason", "recovery")
    @classmethod
    def _reason(cls, value: str) -> str:
        return require_reason_code(value)


class DiagnosticCategory(DiagnosticModel):
    name: str = Field(pattern=r"^[a-z0-9._-]{1,64}$")
    disposition: DiagnosticDisposition
    item_count: int = Field(ge=0, le=1_000_000)
    reason: str

    @field_validator("reason")
    @classmethod
    def _reason(cls, value: str) -> str:
        return require_reason_code(value)


class SupportDiagnosticMaterial(DiagnosticModel):
    schema_version: Literal["1.0"] = "1.0"
    snapshot_id: str = Field(pattern=r"^[A-Za-z0-9_-]{16,128}$")
    created_at: datetime
    expires_at: datetime
    workspace_id: str = Field(max_length=128)
    principal_digest: str
    scope: DiagnosticScope
    summary: DiagnosticSummary
    providers: tuple[ProviderDiagnostic, ...] = Field(
        default_factory=tuple, max_length=MAX_PROVIDERS
    )
    state_inventory: StateInventory
    failures: tuple[DiagnosticFailure, ...] = Field(
        default_factory=tuple, max_length=MAX_FAILURES
    )
    categories: tuple[DiagnosticCategory, ...] = Field(
        default_factory=tuple, max_length=MAX_CATEGORIES
    )

    @field_validator("workspace_id")
    @classmethod
    def _workspace_id(cls, value: str) -> str:
        return require_safe_identifier(value)

    @field_validator("principal_digest")
    @classmethod
    def _digest(cls, value: str) -> str:
        if not _DIGEST.fullmatch(value):
            raise ValueError("invalid digest")
        return value


class SupportDiagnosticSnapshot(SupportDiagnosticMaterial):
    snapshot_digest: str

    @field_validator("snapshot_digest")
    @classmethod
    def _snapshot_digest(cls, value: str) -> str:
        if not _DIGEST.fullmatch(value):
            raise ValueError("invalid digest")
        return value

    def export_bytes(self) -> bytes:
        return canonical_snapshot_bytes(self.model_dump(mode="json", exclude_none=True))


def build_snapshot(payload: Mapping[str, Any]) -> SupportDiagnosticSnapshot:
    """Validate and seal a snapshot with its canonical material digest."""

    material = dict(payload)
    material.pop("snapshot_digest", None)
    validated = SupportDiagnosticMaterial.model_validate(material)
    material_json = validated.model_dump(mode="json", exclude_none=True)
    material_digest = digest_value(canonical_json_bytes(material_json))
    snapshot = SupportDiagnosticSnapshot.model_validate(
        {**material_json, "snapshot_digest": material_digest}
    )
    snapshot.export_bytes()
    if snapshot.expires_at <= snapshot.created_at:
        raise DiagnosticPolicyError("INVALID_DIAGNOSTIC_EXPIRY")
    return snapshot
