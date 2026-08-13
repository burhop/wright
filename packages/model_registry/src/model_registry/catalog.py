"""Validated offline catalog and readiness views for engineering models."""

from __future__ import annotations

import base64
import copy
import json
import re
from dataclasses import dataclass
from importlib.resources import files
from pathlib import PurePosixPath
from typing import Any, Mapping

import yaml

from .models import ModelPackage, canonical_digest
from .policy import HostObservation, ModelPolicy, PolicyState

_MODEL_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,95}$")
_DIGEST = re.compile(r"^[a-f0-9]{64}$")
_EVIDENCE_STATES = frozenset(
    {"bundled", "cached", "live", "stale", "partial", "absent"}
)
_READINESS_STATES = frozenset(
    {
        "approved",
        "needs_review",
        "gated_external_action",
        "incompatible",
        "deprecated",
        "withdrawn",
        "blocked",
    }
)
_EVIDENCE_FACETS = (
    "source",
    "license",
    "artifact",
    "runtime",
    "compatibility",
    "security",
    "test",
)


class ModelCatalogError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class ModelCatalogSnapshot:
    snapshot_id: str
    channel: str
    sequence: int
    schema_version: str
    source_kind: str
    trust_state: str
    freshness: str
    catalog_digest: str

    def projection(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "channel": self.channel,
            "sequence": self.sequence,
            "schema_version": self.schema_version,
            "source_kind": self.source_kind,
            "trust_state": self.trust_state,
            "freshness": self.freshness,
            "catalog_digest": self.catalog_digest,
            "offline": self.freshness in {"bundled", "cached", "stale"},
        }


@dataclass(frozen=True, slots=True)
class ModelCatalogFilters:
    search: str | None = None
    task: str | None = None
    source_kind: str | None = None
    readiness: tuple[str, ...] = ()
    platform: str | None = None
    architecture: str | None = None
    accelerator: str | None = None
    evidence_state: str | None = None
    maximum_bytes: int | None = None

    def canonical(self) -> dict[str, Any]:
        return {
            "search": self.search or None,
            "task": self.task or None,
            "source_kind": self.source_kind or None,
            "readiness": sorted(set(self.readiness)),
            "platform": self.platform or None,
            "architecture": self.architecture or None,
            "accelerator": self.accelerator or None,
            "evidence_state": self.evidence_state or None,
            "maximum_bytes": self.maximum_bytes,
        }


@dataclass(frozen=True, slots=True)
class ModelCatalogPage:
    items: tuple[dict[str, Any], ...]
    next_cursor: str | None
    total: int


@dataclass(frozen=True, slots=True)
class ModelCatalogEntry:
    document: Mapping[str, Any]
    package: ModelPackage | None
    digest: str

    @property
    def model_id(self) -> str:
        return str(self.document["model_id"])

    @property
    def manifest_digest(self) -> str:
        return self.package.digest if self.package is not None else self.digest

    @property
    def generator(self) -> Mapping[str, Any] | None:
        value = self.document.get("generator")
        return dict(value) if isinstance(value, Mapping) else None


def _resource(relative: str):
    normalized = PurePosixPath(relative)
    if (
        normalized.is_absolute()
        or len(normalized.parts) != 1
        or normalized.name != relative
        or normalized.suffix not in {".json", ".yaml"}
    ):
        raise ModelCatalogError(
            "catalog_resource_invalid", "Catalog resource path is invalid"
        )
    resource = files("model_registry").joinpath("catalog", relative)
    if not resource.is_file():
        raise ModelCatalogError(
            "catalog_resource_missing", "Catalog package resource is missing"
        )
    return resource


def catalog_document() -> dict[str, Any]:
    document = yaml.safe_load(_resource("catalog.yaml").read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ModelCatalogError("catalog_invalid", "Catalog document is invalid")
    return copy.deepcopy(document)


def _validate_evidence(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != set(_EVIDENCE_FACETS):
        raise ModelCatalogError(
            "catalog_entry_invalid", "Catalog evidence facets are incomplete"
        )
    result = {str(key): str(item) for key, item in value.items()}
    if any(item not in _EVIDENCE_STATES for item in result.values()):
        raise ModelCatalogError(
            "catalog_entry_invalid", "Catalog evidence state is unsupported"
        )
    return result


def _validate_candidate(document: Mapping[str, Any]) -> None:
    required = {
        "display_name",
        "description",
        "maturity",
        "readiness",
        "source",
        "tasks",
        "license",
        "limitations",
        "variants",
        "evidence",
        "blockers",
    }
    if not required <= set(document):
        raise ModelCatalogError(
            "catalog_entry_invalid", "Candidate catalog metadata is incomplete"
        )
    source = document["source"]
    if not isinstance(source, Mapping) or not {
        "kind",
        "uri",
        "immutable_revision",
        "access",
    } <= set(source):
        raise ModelCatalogError(
            "catalog_entry_invalid", "Candidate source metadata is incomplete"
        )
    if not document["tasks"] or len(document["tasks"]) > 32:
        raise ModelCatalogError(
            "catalog_entry_invalid", "Candidate task metadata is invalid"
        )
    if len(document["variants"]) > 64 or len(document["blockers"]) > 128:
        raise ModelCatalogError(
            "catalog_entry_invalid", "Candidate catalog arrays exceed limits"
        )
    for variant in document["variants"]:
        if not isinstance(variant, Mapping):
            raise ModelCatalogError(
                "catalog_entry_invalid", "Candidate variant is invalid"
            )
        for artifact in variant.get("artifacts", ()):  # exact facts, never payloads
            digest = str(artifact.get("sha256", ""))
            if not _DIGEST.fullmatch(digest) or int(artifact.get("size", -1)) < 0:
                raise ModelCatalogError(
                    "catalog_entry_invalid", "Candidate artifact fact is invalid"
                )


def _load_package(relative: str) -> ModelPackage:
    try:
        document = json.loads(_resource(relative).read_text(encoding="utf-8"))
        return ModelPackage.model_validate(document)
    except ModelCatalogError:
        raise
    except Exception as error:
        raise ModelCatalogError(
            "catalog_package_invalid", "Catalog package metadata is invalid"
        ) from error


def validate_catalog_document(document: Mapping[str, Any]) -> "ModelCatalog":
    if document.get("format_version") != 1:
        raise ModelCatalogError(
            "catalog_version", "Catalog format version is unsupported"
        )
    snapshot = document.get("snapshot")
    entries = document.get("entries")
    if not isinstance(snapshot, Mapping) or not isinstance(entries, list):
        raise ModelCatalogError("catalog_invalid", "Catalog structure is invalid")
    if not 1 <= len(entries) <= 1000:
        raise ModelCatalogError("catalog_invalid", "Catalog entry count is invalid")
    parsed: list[ModelCatalogEntry] = []
    identities: set[str] = set()
    for raw in entries:
        if not isinstance(raw, Mapping):
            raise ModelCatalogError("catalog_entry_invalid", "Catalog entry is invalid")
        model_id = str(raw.get("model_id", ""))
        if not _MODEL_ID.fullmatch(model_id):
            raise ModelCatalogError(
                "catalog_entry_invalid", "Catalog model identity is invalid"
            )
        if model_id in identities:
            raise ModelCatalogError(
                "catalog_duplicate", "Catalog model identity is duplicated"
            )
        identities.add(model_id)
        readiness = str(raw.get("readiness", ""))
        if readiness not in _READINESS_STATES:
            raise ModelCatalogError(
                "catalog_entry_invalid", "Catalog readiness is unsupported"
            )
        _validate_evidence(raw.get("evidence"))
        package_resource = raw.get("package_resource")
        package = _load_package(str(package_resource)) if package_resource else None
        if package is None:
            _validate_candidate(raw)
        elif package.model_id != model_id:
            raise ModelCatalogError(
                "catalog_entry_invalid", "Catalog and package identities differ"
            )
        if package is not None and raw.get("generator"):
            generator = raw["generator"]
            if generator.get("manifest_digest") != package.digest:
                raise ModelCatalogError(
                    "catalog_entry_invalid", "Generator manifest digest is stale"
                )
            variant = package.variants[0]
            artifact_set = canonical_digest(
                [
                    {"path": item.path, "sha256": item.sha256, "size": item.size}
                    for item in sorted(variant.artifacts, key=lambda item: item.path)
                ]
            )
            if generator.get("artifact_set_digest") != artifact_set:
                raise ModelCatalogError(
                    "catalog_entry_invalid", "Generator artifact digest is stale"
                )
        normalized = copy.deepcopy(dict(raw))
        parsed.append(
            ModelCatalogEntry(
                document=normalized,
                package=package,
                digest=canonical_digest(normalized),
            )
        )
    catalog_digest = canonical_digest(document)
    required_snapshot = {
        "snapshot_id",
        "channel",
        "sequence",
        "schema_version",
        "source_kind",
        "trust_state",
        "freshness",
    }
    if not required_snapshot <= set(snapshot):
        raise ModelCatalogError("catalog_invalid", "Catalog snapshot is incomplete")
    projection = ModelCatalogSnapshot(
        snapshot_id=str(snapshot["snapshot_id"]),
        channel=str(snapshot["channel"]),
        sequence=int(snapshot["sequence"]),
        schema_version=str(snapshot["schema_version"]),
        source_kind=str(snapshot["source_kind"]),
        trust_state=str(snapshot["trust_state"]),
        freshness=str(snapshot["freshness"]),
        catalog_digest=catalog_digest,
    )
    return ModelCatalog(projection, tuple(parsed))


def _candidate_compatibility(
    entry: ModelCatalogEntry, host: HostObservation
) -> dict[str, Any]:
    variants = entry.document.get("variants", ())
    host_key = f"{host.platform}/{host.architecture}"
    platform_match = any(
        host_key in variant.get("platforms", ()) for variant in variants
    )
    accelerator_match = any(
        variant.get("accelerator") in {"none", *host.accelerators}
        for variant in variants
    )
    readiness = str(entry.document["readiness"])
    if readiness == "incompatible" or variants and not platform_match:
        state = "incompatible"
    elif variants and not accelerator_match:
        state = "incompatible"
    elif readiness in {"blocked", "gated_external_action"}:
        state = "blocked"
    else:
        state = "uncertain"
    return {
        "state": state,
        "reasons": [str(item["message"]) for item in entry.document["blockers"]],
    }


def _package_variant_view(
    package: ModelPackage,
    variant_id: str,
    *,
    host: HostObservation,
    evidence: Mapping[str, str],
) -> dict[str, Any]:
    variant = package.variant(variant_id)
    result = ModelPolicy().evaluate(package, variant_id=variant_id, host=host)
    document = variant.model_dump(mode="json", exclude_none=True)
    document["compatibility"] = {
        "state": str(result.state),
        "reasons": [item.message for item in result.blockers],
    }
    document["evidence"] = dict(evidence)
    return document


def _candidate_variant_view(
    variant: Mapping[str, Any], entry: ModelCatalogEntry, host: HostObservation
) -> dict[str, Any]:
    document = copy.deepcopy(dict(variant))
    document["compatibility"] = _candidate_compatibility(entry, host)
    document["evidence"] = dict(entry.document["evidence"])
    return document


class ModelCatalog:
    def __init__(
        self,
        snapshot: ModelCatalogSnapshot,
        entries: tuple[ModelCatalogEntry, ...],
    ) -> None:
        self.snapshot = snapshot
        self.entries = tuple(sorted(entries, key=lambda item: item.model_id))
        self._entries = {item.model_id: item for item in self.entries}

    @classmethod
    def load_bundled(cls) -> "ModelCatalog":
        return validate_catalog_document(catalog_document())

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(self._entries)

    def get(self, model_id: str) -> ModelCatalogEntry:
        try:
            return self._entries[model_id]
        except KeyError as error:
            raise ModelCatalogError(
                "model_not_found", "Engineering model is not present in this snapshot"
            ) from error

    def _view(
        self, entry: ModelCatalogEntry, *, host: HostObservation
    ) -> dict[str, Any]:
        evidence = dict(entry.document["evidence"])
        if entry.package is not None:
            package = entry.package
            variants = [
                _package_variant_view(
                    package, item.variant_id, host=host, evidence=evidence
                )
                for item in package.variants
            ]
            package_blockers = [
                blocker
                for item in variants
                for blocker in item["compatibility"]["reasons"]
            ]
            compatibility_state = (
                "compatible"
                if any(
                    item["compatibility"]["state"] == PolicyState.COMPATIBLE
                    for item in variants
                )
                else "incompatible"
            )
            readiness = (
                str(entry.document["readiness"])
                if compatibility_state == "compatible"
                else "incompatible"
            )
            source = package.source.model_dump(mode="json")
            tasks = [item.task_id for item in package.tasks]
            license_projection = package.license.model_dump(
                mode="json", exclude={"evidence"}
            )
            limitations = [item.model_dump(mode="json") for item in package.limitations]
            display_name = package.display_name
            description = package.description
            blockers = [
                {
                    "category": "incompatible_platform",
                    "message": message,
                    "recovery": "Choose a compatible reviewed variant or host.",
                }
                for message in package_blockers
            ]
        else:
            variants = [
                _candidate_variant_view(item, entry, host)
                for item in entry.document["variants"]
            ]
            compatibility = _candidate_compatibility(entry, host)
            compatibility_state = compatibility["state"]
            readiness = str(entry.document["readiness"])
            source = copy.deepcopy(dict(entry.document["source"]))
            tasks = [str(item) for item in entry.document["tasks"]]
            license_projection = copy.deepcopy(dict(entry.document["license"]))
            limitations = copy.deepcopy(list(entry.document["limitations"]))
            display_name = str(entry.document["display_name"])
            description = str(entry.document["description"])
            blockers = copy.deepcopy(list(entry.document["blockers"]))
        return {
            "model_id": entry.model_id,
            "display_name": display_name,
            "description": description,
            "tasks": tasks,
            "source": source,
            "license": license_projection,
            "readiness": readiness,
            "compatibility": {
                "state": compatibility_state,
                "reasons": [item["message"] for item in blockers],
            },
            "evidence": evidence,
            "limitations": limitations,
            "variants": variants,
            "blockers": blockers,
            "generator": copy.deepcopy(entry.generator),
            "manifest_digest": entry.manifest_digest,
            "entry_digest": entry.digest,
            "snapshot": self.snapshot.projection(),
        }

    def views(self, *, host: HostObservation) -> tuple[dict[str, Any], ...]:
        return tuple(self._view(item, host=host) for item in self.entries)

    def get_view(self, model_id: str, *, host: HostObservation) -> dict[str, Any]:
        return self._view(self.get(model_id), host=host)

    def list(
        self,
        filters: ModelCatalogFilters,
        *,
        host: HostObservation,
        limit: int = 50,
        cursor: str | None = None,
    ) -> ModelCatalogPage:
        if not 1 <= limit <= 100:
            raise ModelCatalogError("catalog_limit", "Catalog limit is invalid")
        if filters.maximum_bytes is not None and filters.maximum_bytes < 0:
            raise ModelCatalogError("catalog_filter", "Catalog byte filter is invalid")
        if filters.evidence_state and filters.evidence_state not in _EVIDENCE_STATES:
            raise ModelCatalogError(
                "catalog_filter", "Catalog evidence filter is invalid"
            )
        filter_digest = canonical_digest(filters.canonical())
        offset = 0
        if cursor:
            try:
                padded = cursor + "=" * (-len(cursor) % 4)
                payload = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
                if (
                    payload["catalog"] != self.snapshot.catalog_digest
                    or payload["filters"] != filter_digest
                ):
                    raise ValueError
                offset = int(payload["offset"])
            except Exception as error:
                raise ModelCatalogError(
                    "catalog_cursor", "Catalog cursor is invalid or stale"
                ) from error
        views = list(self.views(host=host))
        if filters.search:
            needle = re.sub(r"[-_]+", " ", filters.search.lower()).strip()
            views = [
                item
                for item in views
                if needle
                in re.sub(
                    r"[-_]+",
                    " ",
                    " ".join(
                        [
                            item["model_id"],
                            item["display_name"],
                            item["description"],
                            *item["tasks"],
                        ]
                    ).lower(),
                )
            ]
        if filters.task:
            views = [item for item in views if filters.task in item["tasks"]]
        if filters.source_kind:
            views = [
                item for item in views if item["source"]["kind"] == filters.source_kind
            ]
        if filters.readiness:
            requested = set(filters.readiness)
            views = [item for item in views if item["readiness"] in requested]
        if filters.platform or filters.architecture:
            platform = filters.platform or host.platform
            architecture = filters.architecture or host.architecture
            key = f"{platform}/{architecture}"
            views = [
                item
                for item in views
                if any(
                    key in variant.get("platforms", ()) for variant in item["variants"]
                )
            ]
        if filters.accelerator:
            views = [
                item
                for item in views
                if any(
                    variant.get("accelerator") == filters.accelerator
                    for variant in item["variants"]
                )
            ]
        if filters.evidence_state:
            views = [
                item
                for item in views
                if filters.evidence_state in item["evidence"].values()
            ]
        if filters.maximum_bytes is not None:
            views = [
                item
                for item in views
                if any(
                    int(variant.get("resources", {}).get("download_bytes", 0))
                    <= filters.maximum_bytes
                    for variant in item["variants"]
                )
            ]
        total = len(views)
        if offset < 0 or offset > total:
            raise ModelCatalogError("catalog_cursor", "Catalog cursor is invalid")
        selected = tuple(views[offset : offset + limit])
        next_offset = offset + len(selected)
        next_cursor = None
        if next_offset < total:
            payload = {
                "catalog": self.snapshot.catalog_digest,
                "filters": filter_digest,
                "offset": next_offset,
            }
            next_cursor = (
                base64.urlsafe_b64encode(
                    json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
                )
                .decode()
                .rstrip("=")
            )
        return ModelCatalogPage(selected, next_cursor, total)


__all__ = [
    "ModelCatalog",
    "ModelCatalogEntry",
    "ModelCatalogError",
    "ModelCatalogFilters",
    "ModelCatalogPage",
    "ModelCatalogSnapshot",
    "catalog_document",
    "validate_catalog_document",
]
