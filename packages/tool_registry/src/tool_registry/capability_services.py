from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from .canonical_catalog import ApprovedCatalogChannel


class MachineDetector(Protocol):
    def __call__(self) -> Mapping[str, Any]: ...


class OnboardingAdapter(Protocol):
    kind: str
    version: str


@dataclass(frozen=True, slots=True)
class CapabilityServiceDependencies:
    database_path: Path
    clock: Callable[[], datetime] = lambda: datetime.now(UTC)
    trust_roots: Mapping[str, Any] = field(default_factory=dict)
    catalog_channels: Mapping[str, ApprovedCatalogChannel] = field(default_factory=dict)
    catalog_fetcher: Callable[[ApprovedCatalogChannel], dict[str, Any]] | None = None
    machine_detectors: Mapping[str, MachineDetector] = field(default_factory=dict)
    onboarding_adapters: Mapping[str, OnboardingAdapter] = field(default_factory=dict)
    validation_clients: Mapping[str, Any] = field(default_factory=dict)
    validation_gateway_clients: Mapping[str, Any] = field(default_factory=dict)
    validation_read_only_probes: Mapping[str, Mapping[str, Any]] = field(
        default_factory=dict
    )
    import_preview_repository: Any | None = None

    @classmethod
    def for_database(cls, database_path: str | Path) -> "CapabilityServiceDependencies":
        return cls(database_path=Path(database_path))
