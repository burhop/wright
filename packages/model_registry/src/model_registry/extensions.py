"""Public duplicate-safe extension registries for engineering model packages."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Generic, Protocol, TypeVar

from .lifecycle import MappingArtifactSource
from .models import ModelPackage
from .runtime import (
    AdapterRegistration,
    RuntimeAdapterRegistry,
    RuntimeFailure,
    built_in_runtime_registry,
)


class ExtensionError(ValueError):
    def __init__(self, category: str, message: str) -> None:
        super().__init__(message)
        self.category = category


class SourceAdapter(Protocol):
    def fetch_artifact(self, *args: Any, **kwargs: Any) -> bytes: ...


PredicateEvaluator = Callable[[Mapping[str, Any], Mapping[str, Any]], bool]
T = TypeVar("T")


class NamedExtensionRegistry(Generic[T]):
    """Small exact-name registry; duplicate replacement is never implicit."""

    def __init__(self, *, label: str) -> None:
        self.label = label
        self._values: dict[str, T] = {}

    def register(self, name: str, value: T) -> T:
        if not name or len(name) > 128:
            raise ExtensionError(
                "extension_invalid", f"{self.label} identity is invalid"
            )
        if name in self._values:
            raise ExtensionError(
                "extension_duplicate", f"{self.label} identity is already registered"
            )
        self._values[name] = value
        return value

    def get(self, name: str) -> T:
        try:
            return self._values[name]
        except KeyError as error:
            raise ExtensionError(
                "extension_missing", f"{self.label} extension is unavailable"
            ) from error

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._values))


class AdapterExtensionRegistry:
    def __init__(self) -> None:
        self._registry = RuntimeAdapterRegistry()

    def register(self, registration: AdapterRegistration) -> AdapterRegistration:
        try:
            self._registry.register(registration)
        except RuntimeFailure as error:
            category = (
                "extension_duplicate"
                if "already registered" in str(error)
                else error.category
            )
            raise ExtensionError(category, str(error)) from error
        return registration

    def get(self, adapter_id: str) -> AdapterRegistration:
        try:
            return self._registry.get(adapter_id)
        except RuntimeFailure as error:
            raise ExtensionError(error.category, str(error)) from error

    def versions(self) -> dict[str, str]:
        return self._registry.versions()


class ModelPackageExtensionRegistry:
    def __init__(self) -> None:
        self._packages: dict[tuple[str, int], ModelPackage] = {}

    def register(
        self, package: ModelPackage, *, registries: "EngineeringExtensionRegistries"
    ) -> ModelPackage:
        identity = (package.model_id, package.package_revision)
        if identity in self._packages:
            raise ExtensionError(
                "extension_duplicate", "Model package identity is already registered"
            )
        from .conformance import validate_package_contract

        report = validate_package_contract(package, registries)
        if not report.passed:
            finding = report.findings[0]
            raise ExtensionError(finding.category, finding.message)
        self._packages[identity] = package
        return package

    def get(self, model_id: str, package_revision: int) -> ModelPackage:
        try:
            return self._packages[(model_id, package_revision)]
        except KeyError as error:
            raise ExtensionError(
                "extension_missing", "Model package extension is unavailable"
            ) from error

    @property
    def identities(self) -> tuple[str, ...]:
        return tuple(
            f"{model_id}@{revision}" for model_id, revision in sorted(self._packages)
        )


class EngineeringExtensionRegistries:
    def __init__(self) -> None:
        self.packages = ModelPackageExtensionRegistry()
        self.sources: NamedExtensionRegistry[type[SourceAdapter]] = (
            NamedExtensionRegistry(label="Source adapter")
        )
        self.adapters = AdapterExtensionRegistry()
        self.predicates: NamedExtensionRegistry[PredicateEvaluator] = (
            NamedExtensionRegistry(label="Predicate")
        )


def _declarative_predicate(
    _declaration: Mapping[str, Any], _output: Mapping[str, Any]
) -> bool:
    raise ExtensionError(
        "predicate_execution_private",
        "Built-in predicates execute only inside the reviewed evidence evaluator",
    )


def built_in_extension_registries() -> EngineeringExtensionRegistries:
    registries = EngineeringExtensionRegistries()
    registries.sources.register("wright", MappingArtifactSource)
    registries.adapters.register(
        built_in_runtime_registry().get("wright-deterministic")
    )
    for name in (
        "exact",
        "absolute_tolerance",
        "relative_tolerance",
        "range",
        "category",
    ):
        registries.predicates.register(name, _declarative_predicate)
    return registries


__all__ = [
    "AdapterExtensionRegistry",
    "EngineeringExtensionRegistries",
    "ExtensionError",
    "ModelPackageExtensionRegistry",
    "NamedExtensionRegistry",
    "PredicateEvaluator",
    "SourceAdapter",
    "built_in_extension_registries",
]
