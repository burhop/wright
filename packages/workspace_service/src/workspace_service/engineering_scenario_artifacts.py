"""Normalization boundary for untrusted engineering artifact claims."""

from __future__ import annotations

import json
import math
import re
from hashlib import sha256
from typing import Any, Callable, Collection, Mapping

from core.engineering_scenarios import (
    MAX_INLINE_ARTIFACT_BYTES,
    ArtifactProducer,
    EngineeringScenarioError,
    NormalizedArtifact,
)
from core.rivet_mcp import canonical_json, reject_secret_material


_UNSAFE_TEXT = re.compile(
    r"(?i)(<\s*script|javascript\s*:|data\s*:\s*text/html|(?:^|[\\/])\.\.(?:[\\/]|$)|file\s*://)"
)
_RAW_ABSOLUTE_PATH = re.compile(r"^(?:[A-Za-z]:[\\/]|/[^/])")
_UNRESTRICTED_URI = re.compile(r"(?i)^[a-z][a-z0-9+.-]*://")
_DIGEST = re.compile(r"^[a-f0-9]{64}$")
_ALLOWED_FIELDS = {
    "schema_version",
    "artifact_id",
    "domain",
    "kind",
    "source_schema",
    "producer",
    "upstream_digests",
    "units",
    "coordinate_system",
    "content",
    "vault_reference",
    "content_digest",
    "validation_state",
}
_DEFAULT_SOURCE_SCHEMAS = {
    ("mesh", "wright-mesh-summary", "1.0"),
    ("mesh", "wright-enclosure-summary", "1.0"),
    ("numeric-table", "wright-numeric-table", "1.0"),
    ("fea-result", "wright-fea-summary", "1.0"),
    ("ecad-board", "kicad-pcb-summary", "20240108"),
    ("cfd-result", "wright-cfd-summary", "1.0"),
    ("data-tree", "grasshopper-data-tree-summary", "1.0"),
    ("3mf-summary", "3mf-core", "1.3"),
    ("slicer-summary", "wright-slicer-summary", "1.0"),
    ("gcode-static", "rs274ngc-static-summary", "3"),
}
NormalizerValidator = Callable[[Mapping[str, Any]], None]


class EngineeringArtifactNormalizerRegistry:
    """Versioned artifact schema registry used before generic normalization."""

    def __init__(self, *, include_defaults: bool = True) -> None:
        self._normalizers: dict[tuple[str, str, str], NormalizerValidator | None] = {}
        if include_defaults:
            for kind, name, version in sorted(_DEFAULT_SOURCE_SCHEMAS):
                self.register(kind, name, version)

    def register(
        self,
        kind: str,
        schema_name: str,
        schema_version: str,
        validator: NormalizerValidator | None = None,
    ) -> None:
        key = (kind, schema_name, schema_version)
        if not all(value.strip() for value in key):
            raise EngineeringScenarioError(
                "scenario_normalizer_invalid",
                "Artifact normalizer identity is incomplete",
            )
        if key in self._normalizers:
            raise EngineeringScenarioError(
                "scenario_normalizer_conflict",
                f"Artifact normalizer already exists: {kind}/{schema_name}@{schema_version}",
            )
        self._normalizers[key] = validator

    def validate(
        self,
        kind: str,
        source_schema: Mapping[str, str],
        raw: Mapping[str, Any],
    ) -> None:
        key = (kind, source_schema["name"], source_schema["version"])
        try:
            validator = self._normalizers[key]
        except KeyError as exc:
            raise EngineeringScenarioError(
                "artifact_source_schema_unsupported",
                "Artifact kind and source schema version are not supported",
            ) from exc
        if validator is not None:
            validator(raw)


_DEFAULT_REGISTRY = EngineeringArtifactNormalizerRegistry()


def _inspect_text(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _inspect_text(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _inspect_text(item, f"{path}[{index}]")
    elif isinstance(value, str):
        if (
            _UNSAFE_TEXT.search(value)
            or _RAW_ABSOLUTE_PATH.search(value)
            or _UNRESTRICTED_URI.search(value)
        ):
            raise EngineeringScenarioError(
                "artifact_executable_or_path_content",
                f"Artifact contains executable markup or an unsafe path at {path}",
            )
    elif isinstance(value, float) and not math.isfinite(value):
        raise EngineeringScenarioError(
            "artifact_non_finite_value",
            f"Artifact contains a non-finite value at {path}",
        )


def _source_schema(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise EngineeringScenarioError(
            "artifact_schema_invalid", "Artifact source schema is missing"
        )
    result = {
        "name": str(value.get("name", "")),
        "version": str(value.get("version", "")),
        "media_type": str(value.get("media_type", "")),
    }
    if not all(result.values()):
        raise EngineeringScenarioError(
            "artifact_schema_invalid", "Artifact source schema is incomplete"
        )
    return result


def _canonical_content(value: Any) -> Any:
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, Mapping):
        return {str(key): _canonical_content(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical_content(item) for item in value]
    return value


def artifact_content_digest(content: Any) -> str:
    """Hash JSON numbers stably across MCP/Pydantic integer normalization."""

    encoded = canonical_json(_canonical_content(content)).encode("utf-8")
    return sha256(encoded).hexdigest()


def normalize_artifact(
    raw: Mapping[str, Any],
    *,
    authorized_vault_ids: Collection[str] = (),
    registry: EngineeringArtifactNormalizerRegistry | None = None,
) -> NormalizedArtifact:
    """Validate and canonicalize a child-supplied artifact envelope."""
    reject_secret_material(raw)
    _inspect_text(raw)
    unexpected = sorted(set(raw) - _ALLOWED_FIELDS)
    if unexpected:
        raise EngineeringScenarioError(
            "artifact_field_unsupported",
            f"Artifact contains unsupported fields: {', '.join(unexpected)}",
        )
    if raw.get("schema_version") != "1.0":
        raise EngineeringScenarioError(
            "artifact_version_unsupported", "Artifact version is unsupported"
        )
    source_schema = _source_schema(raw.get("source_schema"))
    kind = str(raw.get("kind", ""))
    (registry or _DEFAULT_REGISTRY).validate(kind, source_schema, raw)
    if raw.get("validation_state") != "valid":
        raise EngineeringScenarioError(
            "artifact_validation_state_invalid",
            "Child artifact must declare a structurally valid envelope",
        )
    producer_raw = raw.get("producer")
    if not isinstance(producer_raw, Mapping):
        raise EngineeringScenarioError(
            "artifact_producer_invalid", "Artifact producer is missing"
        )
    producer = ArtifactProducer(
        run_id=str(producer_raw.get("run_id", "")),
        node_id=str(producer_raw.get("node_id", "")),
        call_id=str(producer_raw.get("call_id", "")),
        capability=str(producer_raw.get("capability", "")),
    )
    content_present = "content" in raw
    vault_present = "vault_reference" in raw
    if content_present == vault_present:
        raise EngineeringScenarioError(
            "artifact_storage_invalid",
            "Artifact must contain exactly one of inline content or vault reference",
        )
    content = raw.get("content") if content_present else None
    vault = raw.get("vault_reference") if vault_present else None
    if content_present:
        encoded = canonical_json(content).encode("utf-8")
        if len(encoded) > MAX_INLINE_ARTIFACT_BYTES:
            raise EngineeringScenarioError(
                "artifact_limit_exceeded", "Inline artifact exceeds 64 KiB"
            )
        computed_digest = artifact_content_digest(content)
    else:
        if not isinstance(vault, Mapping):
            raise EngineeringScenarioError(
                "artifact_vault_reference_invalid", "Vault reference is invalid"
            )
        if set(vault) != {"artifact_id", "media_type", "digest"}:
            raise EngineeringScenarioError(
                "artifact_vault_reference_invalid", "Vault reference fields are invalid"
            )
        if not all(str(vault.get(key, "")).strip() for key in vault):
            raise EngineeringScenarioError(
                "artifact_vault_reference_invalid", "Vault reference is incomplete"
            )
        if _RAW_ABSOLUTE_PATH.search(str(vault["artifact_id"])):
            raise EngineeringScenarioError(
                "artifact_vault_reference_invalid", "Raw paths are not vault identities"
            )
        if str(vault["artifact_id"]) not in set(authorized_vault_ids):
            raise EngineeringScenarioError(
                "artifact_vault_reference_unauthorized",
                "Vault reference is not authorized for this scenario run",
            )
        computed_digest = str(vault["digest"])
    if not _DIGEST.fullmatch(computed_digest):
        raise EngineeringScenarioError(
            "artifact_digest_invalid", "Artifact content digest is invalid"
        )
    declared_digest = str(raw.get("content_digest", ""))
    if not _DIGEST.fullmatch(declared_digest):
        raise EngineeringScenarioError(
            "artifact_digest_invalid", "Artifact must declare a content digest"
        )
    if declared_digest != computed_digest:
        raise EngineeringScenarioError(
            "artifact_digest_mismatch", "Artifact content digest does not match"
        )
    upstream = tuple(str(item) for item in raw.get("upstream_digests", ()))
    return NormalizedArtifact(
        schema_version="1.0",
        artifact_id=str(raw.get("artifact_id", "")),
        domain=str(raw.get("domain", "")),
        kind=kind,
        source_schema=source_schema,
        producer=producer,
        upstream_digests=upstream,
        content_digest=computed_digest,
        validation_state=str(raw.get("validation_state", "unvalidated")),
        content=content,
        vault_reference=dict(vault) if isinstance(vault, Mapping) else None,
        units=dict(raw.get("units", {})),
        coordinate_system=(
            dict(raw["coordinate_system"])
            if isinstance(raw.get("coordinate_system"), Mapping)
            else None
        ),
    )


def artifact_document(artifact: NormalizedArtifact) -> dict[str, Any]:
    return json.loads(canonical_json(artifact.canonical()))
