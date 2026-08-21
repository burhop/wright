"""Provider-neutral values for deterministic engineering scenario evidence."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Any, Mapping, Sequence

from .rivet_mcp import canonical_digest, reject_secret_material


_DIGEST = re.compile(r"^[a-f0-9]{64}$")
_SLUG = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")
MAX_INLINE_ARTIFACT_BYTES = 64 * 1024
MAX_REPORT_ITEMS = 1_000


class ScenarioTier(StrEnum):
    TIER1 = "tier1"
    TIER2 = "tier2"
    TIER3 = "tier3"


class ResourceClass(StrEnum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    EXTERNAL = "external"


class ScenarioState(StrEnum):
    PREFLIGHT = "preflight"
    BLOCKED = "blocked"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ERROR = "error"


class AssertionState(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"


class AssertionCategory(StrEnum):
    PREFLIGHT = "preflight"
    POLICY = "policy"
    TRANSPORT = "transport"
    TOOL = "tool"
    CONTRACT = "contract"
    UNIT = "unit"
    GEOMETRY = "geometry"
    ECAD = "ecad"
    CONVERGENCE = "convergence"
    NUMERIC = "numeric"
    TOPOLOGY = "topology"
    ADDITIVE = "additive"
    CAM_SAFETY = "cam_safety"
    CORRELATION = "correlation"
    ENVIRONMENT = "environment"
    CLEANUP = "cleanup"
    TIMEOUT = "timeout"
    INTERNAL = "internal"


class EngineeringScenarioError(ValueError):
    """Stable scenario validation/evaluation failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class UnitDefinition:
    symbol: str
    dimension: str
    scale: Decimal
    offset: Decimal = Decimal("0")
    absolute: bool = False

    def to_si(self, value: Decimal | int | float | str) -> Decimal:
        number = Decimal(str(value))
        if not number.is_finite():
            raise EngineeringScenarioError("non_finite_value", "Value must be finite")
        return (number + self.offset) * self.scale

    def from_si(self, value: Decimal | int | float | str) -> Decimal:
        number = Decimal(str(value))
        if not number.is_finite():
            raise EngineeringScenarioError("non_finite_value", "Value must be finite")
        return (number / self.scale) - self.offset


_UNITS = {
    "1": UnitDefinition("1", "dimensionless", Decimal("1")),
    "%": UnitDefinition("%", "dimensionless", Decimal("0.01")),
    "m": UnitDefinition("m", "length", Decimal("1")),
    "mm": UnitDefinition("mm", "length", Decimal("0.001")),
    "cm": UnitDefinition("cm", "length", Decimal("0.01")),
    "m2": UnitDefinition("m2", "area", Decimal("1")),
    "mm2": UnitDefinition("mm2", "area", Decimal("0.000001")),
    "m3": UnitDefinition("m3", "volume", Decimal("1")),
    "mm3": UnitDefinition("mm3", "volume", Decimal("0.000000001")),
    "kg": UnitDefinition("kg", "mass", Decimal("1")),
    "g": UnitDefinition("g", "mass", Decimal("0.001")),
    "s": UnitDefinition("s", "time", Decimal("1")),
    "ms": UnitDefinition("ms", "time", Decimal("0.001")),
    "K": UnitDefinition("K", "temperature", Decimal("1"), absolute=True),
    "degC": UnitDefinition(
        "degC", "temperature", Decimal("1"), Decimal("273.15"), absolute=True
    ),
    "delta_K": UnitDefinition("delta_K", "temperature_delta", Decimal("1")),
    "delta_degC": UnitDefinition("delta_degC", "temperature_delta", Decimal("1")),
    "rad": UnitDefinition("rad", "angle", Decimal("1")),
    "deg": UnitDefinition("deg", "angle", Decimal(str(math.pi)) / Decimal("180")),
    "N": UnitDefinition("N", "force", Decimal("1")),
    "kN": UnitDefinition("kN", "force", Decimal("1000")),
    "Pa": UnitDefinition("Pa", "pressure", Decimal("1")),
    "kPa": UnitDefinition("kPa", "pressure", Decimal("1000")),
    "MPa": UnitDefinition("MPa", "pressure", Decimal("1000000")),
    "m/s": UnitDefinition("m/s", "velocity", Decimal("1")),
    "mm/s": UnitDefinition("mm/s", "velocity", Decimal("0.001")),
    "W": UnitDefinition("W", "power", Decimal("1")),
    "kW": UnitDefinition("kW", "power", Decimal("1000")),
    "J": UnitDefinition("J", "energy", Decimal("1")),
    "kJ": UnitDefinition("kJ", "energy", Decimal("1000")),
}


def unit_definition(symbol: str) -> UnitDefinition:
    try:
        return _UNITS[symbol]
    except KeyError as exc:
        raise EngineeringScenarioError(
            "unit_unsupported", f"Unsupported unit: {symbol}"
        ) from exc


def convert_unit(
    value: Decimal | int | float | str, source: str, target: str
) -> Decimal:
    source_unit = unit_definition(source)
    target_unit = unit_definition(target)
    if source_unit.dimension != target_unit.dimension:
        raise EngineeringScenarioError(
            "unit_dimension_mismatch",
            f"Cannot convert {source_unit.dimension} to {target_unit.dimension}",
        )
    return target_unit.from_si(source_unit.to_si(value))


def _require_text(value: str, label: str, maximum: int = 200) -> None:
    if not value or not value.strip() or len(value) > maximum:
        raise EngineeringScenarioError("invalid_field", f"{label} is invalid")


def _require_digest(value: str, label: str) -> None:
    if not _DIGEST.fullmatch(value):
        raise EngineeringScenarioError("invalid_digest", f"{label} is invalid")


@dataclass(frozen=True, slots=True)
class ArtifactProducer:
    run_id: str
    node_id: str
    call_id: str
    capability: str

    def __post_init__(self) -> None:
        for label, value in (
            ("Run identity", self.run_id),
            ("Node identity", self.node_id),
            ("Call identity", self.call_id),
            ("Capability", self.capability),
        ):
            _require_text(value, label)

    def canonical(self) -> dict[str, str]:
        return {
            "run_id": self.run_id,
            "node_id": self.node_id,
            "call_id": self.call_id,
            "capability": self.capability,
        }


@dataclass(frozen=True, slots=True)
class NormalizedArtifact:
    artifact_id: str
    domain: str
    kind: str
    source_schema: Mapping[str, str]
    producer: ArtifactProducer
    upstream_digests: tuple[str, ...]
    content_digest: str
    validation_state: str
    content: Any | None = None
    vault_reference: Mapping[str, Any] | None = None
    units: Mapping[str, Any] = field(default_factory=dict)
    coordinate_system: Mapping[str, Any] | None = None
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if self.schema_version != "1.0":
            raise EngineeringScenarioError(
                "artifact_version_unsupported", "Artifact version is unsupported"
            )
        for label, value in (
            ("Artifact identity", self.artifact_id),
            ("Domain", self.domain),
            ("Artifact kind", self.kind),
        ):
            _require_text(value, label)
        if not _SLUG.fullmatch(self.artifact_id):
            raise EngineeringScenarioError(
                "invalid_field", "Artifact identity must be a slug"
            )
        if (self.content is None) == (self.vault_reference is None):
            raise EngineeringScenarioError(
                "artifact_storage_invalid",
                "Artifact must contain exactly one of inline content or vault reference",
            )
        _require_digest(self.content_digest, "Content digest")
        for digest in self.upstream_digests:
            _require_digest(digest, "Upstream digest")
        reject_secret_material(self.canonical())

    def canonical(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "schema_version": self.schema_version,
            "artifact_id": self.artifact_id,
            "domain": self.domain,
            "kind": self.kind,
            "source_schema": dict(self.source_schema),
            "producer": self.producer.canonical(),
            "upstream_digests": self.upstream_digests,
            "units": dict(self.units),
            "content_digest": self.content_digest,
            "validation_state": self.validation_state,
        }
        if self.coordinate_system is not None:
            value["coordinate_system"] = dict(self.coordinate_system)
        if self.content is not None:
            value["content"] = self.content
        else:
            value["vault_reference"] = dict(self.vault_reference or {})
        return value


@dataclass(frozen=True, slots=True)
class AssertionResult:
    assertion_id: str
    plugin: str
    plugin_version: str
    state: AssertionState
    category: AssertionCategory
    reason_code: str
    artifact_digests: tuple[str, ...]
    producer: Mapping[str, str]
    expected: Any = None
    observed: Any = None
    units: Mapping[str, Any] | None = None
    message: str | None = None
    recovery: str | None = None
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if self.schema_version != "1.0":
            raise EngineeringScenarioError(
                "assertion_version_unsupported", "Assertion version is unsupported"
            )
        for value in (self.assertion_id, self.plugin, self.reason_code):
            _require_text(value, "Assertion field")
        if self.state in {AssertionState.FAIL, AssertionState.ERROR} and (
            not self.message or not self.recovery
        ):
            raise EngineeringScenarioError(
                "assertion_diagnostic_missing",
                "Failed assertions require a message and recovery",
            )
        for digest in self.artifact_digests:
            _require_digest(digest, "Artifact digest")
        reject_secret_material(self.canonical())

    def canonical(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "schema_version": self.schema_version,
            "assertion_id": self.assertion_id,
            "plugin": self.plugin,
            "plugin_version": self.plugin_version,
            "state": self.state,
            "category": self.category,
            "reason_code": self.reason_code,
            "expected": self.expected,
            "observed": self.observed,
            "artifact_digests": list(self.artifact_digests),
            "producer": dict(self.producer),
        }
        if self.units is not None:
            value["units"] = dict(self.units)
        if self.message is not None:
            value["message"] = self.message
        if self.recovery is not None:
            value["recovery"] = self.recovery
        return value

    @property
    def digest(self) -> str:
        return canonical_digest(self.canonical())


@dataclass(frozen=True, slots=True)
class ScenarioCatalogEntry:
    scenario_id: str
    revision: int
    title: str
    summary: str
    domains: tuple[str, ...]
    tier: ScenarioTier
    resource_class: ResourceClass
    expected_duration_seconds: int
    manifest_digest: str

    def __post_init__(self) -> None:
        if not _SLUG.fullmatch(self.scenario_id):
            raise EngineeringScenarioError(
                "scenario_id_invalid", "Scenario identity is invalid"
            )
        if self.revision < 1 or not self.domains or self.expected_duration_seconds < 1:
            raise EngineeringScenarioError(
                "scenario_manifest_invalid", "Scenario metadata is invalid"
            )
        _require_text(self.title, "Scenario title", 120)
        _require_text(self.summary, "Scenario summary", 500)
        _require_digest(self.manifest_digest, "Manifest digest")

    def canonical(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "revision": self.revision,
            "title": self.title,
            "summary": self.summary,
            "domains": self.domains,
            "tier": self.tier,
            "resource_class": self.resource_class,
            "expected_duration_seconds": self.expected_duration_seconds,
            "manifest_digest": self.manifest_digest,
        }


def assert_bounded_sequence(value: Sequence[Any], label: str) -> None:
    if len(value) > MAX_REPORT_ITEMS:
        raise EngineeringScenarioError(
            "report_limit_exceeded", f"{label} exceeds the report item limit"
        )
