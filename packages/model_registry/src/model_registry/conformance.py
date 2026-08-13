"""Static and generated-fixture conformance for model package extensions."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version

from .extensions import EngineeringExtensionRegistries, ExtensionError
from .models import ModelPackage, canonical_digest
from .policy import SAFE_FORMATS, validate_artifact_path
from .runtime import AdapterRegistration, RuntimeFailure


@dataclass(frozen=True, slots=True)
class ConformanceFinding:
    category: str
    message: str
    recovery: str

    def projection(self) -> dict[str, str]:
        return {
            "category": self.category,
            "message": self.message,
            "recovery": self.recovery,
        }


@dataclass(frozen=True, slots=True)
class ConformanceReport:
    kind: str
    identity: str
    findings: tuple[ConformanceFinding, ...]

    @property
    def passed(self) -> bool:
        return not self.findings

    def material(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "identity": self.identity,
            "passed": self.passed,
            "findings": [item.projection() for item in self.findings],
        }

    @property
    def report_digest(self) -> str:
        return canonical_digest(self.material())

    def projection(self) -> dict[str, Any]:
        return {**self.material(), "report_digest": self.report_digest}


def _finding(category: str, message: str, recovery: str) -> ConformanceFinding:
    return ConformanceFinding(category, message, recovery)


def validate_package_contract(
    package: ModelPackage, registries: EngineeringExtensionRegistries
) -> ConformanceReport:
    findings: list[ConformanceFinding] = []
    declarations = {
        item.path: item for variant in package.variants for item in variant.artifacts
    }
    license_paths = {
        item.location: item.sha256
        for item in package.license.evidence
        if item.kind == "artifact"
    }
    for variant in package.variants:
        if variant.format not in SAFE_FORMATS:
            findings.append(
                _finding(
                    "unsafe_format",
                    "The package format is not a reviewed data-only format.",
                    "Use ONNX, Safetensors, or a separately reviewed data-only format.",
                )
            )
        for artifact in variant.artifacts:
            try:
                validate_artifact_path(artifact.path)
            except ValueError:
                findings.append(
                    _finding(
                        "path_unsafe",
                        "An artifact path or suffix is unsafe.",
                        "Publish normalized data-only relative artifact paths.",
                    )
                )
                break
        try:
            adapter = registries.adapters.get(variant.runtime.adapter_id)
        except ExtensionError:
            findings.append(
                _finding(
                    "runtime_missing",
                    "The declared runtime adapter is not registered.",
                    "Register a separately reviewed adapter before the package.",
                )
            )
            adapter = None
        if adapter is not None:
            try:
                compatible = Version(adapter.adapter_version) in SpecifierSet(
                    variant.runtime.version_specifier
                )
            except (InvalidVersion, InvalidSpecifier):
                compatible = False
            if not compatible:
                findings.append(
                    _finding(
                        "runtime_incompatible",
                        "The registered adapter version does not satisfy the package.",
                        "Register an exact compatible reviewed adapter version.",
                    )
                )
            if (
                variant.format not in adapter.formats
                or not {task.task_id for task in package.tasks} <= adapter.tasks
            ):
                findings.append(
                    _finding(
                        "runtime_incompatible",
                        "The adapter does not declare the package format and tasks.",
                        "Correct the adapter declaration or choose another adapter.",
                    )
                )
        tasks = {item.task_id: item for item in package.tasks}
        limitations = {item.limitation_id for item in package.limitations}
        for vector in variant.test_vectors:
            task = tasks.get(vector.task_id)
            if task is None or (
                vector.input_schema_sha256 != canonical_digest(task.input_schema)
                or vector.output_schema_sha256 != canonical_digest(task.output_schema)
            ):
                findings.append(
                    _finding(
                        "schema_mismatch",
                        "A mandatory vector does not bind the exact task schemas.",
                        "Regenerate vector schema digests from the public task contract.",
                    )
                )
            if not set(vector.limitations_exercised) <= limitations:
                findings.append(
                    _finding(
                        "limitation_missing",
                        "A vector refers to an undeclared limitation.",
                        "Declare and exercise exact material limitations.",
                    )
                )
            if vector.expected.kind not in registries.predicates.names:
                findings.append(
                    _finding(
                        "predicate_missing",
                        "A vector predicate is not registered.",
                        "Register a reviewed declarative predicate implementation.",
                    )
                )
    if not license_paths or any(
        path not in declarations or declarations[path].sha256 != digest
        for path, digest in license_paths.items()
    ):
        findings.append(
            _finding(
                "license_unapproved",
                "License evidence does not bind a declared exact artifact.",
                "Add complete SPDX-compatible license evidence to the package.",
            )
        )
    if package.source.kind not in registries.sources.names:
        findings.append(
            _finding(
                "source_unavailable",
                "The package source kind has no registered adapter.",
                "Register a reviewed source adapter before the package.",
            )
        )
    return ConformanceReport(
        "package",
        f"{package.model_id}@{package.package_revision}",
        tuple(findings),
    )


def run_package_conformance(
    package: ModelPackage,
    artifacts: Mapping[str, bytes],
    registries: EngineeringExtensionRegistries,
) -> ConformanceReport:
    base = validate_package_contract(package, registries)
    findings = list(base.findings)
    declarations = {
        item.path: item for variant in package.variants for item in variant.artifacts
    }
    if set(artifacts) != set(declarations):
        findings.insert(
            0,
            _finding(
                "undeclared_file",
                "Generated fixture bytes do not exactly match declared artifacts.",
                "Remove undeclared bytes and regenerate the exact fixture manifest.",
            ),
        )
    else:
        for path, declaration in sorted(declarations.items()):
            value = artifacts[path]
            if len(value) != declaration.size:
                findings.append(
                    _finding(
                        "size_mismatch",
                        "Generated fixture size does not match its declaration.",
                        "Regenerate the fixture and declaration together.",
                    )
                )
            if hashlib.sha256(value).hexdigest() != declaration.sha256:
                findings.append(
                    _finding(
                        "digest_mismatch",
                        "Generated fixture digest does not match its declaration.",
                        "Regenerate the fixture and declaration together.",
                    )
                )
    return ConformanceReport(base.kind, base.identity, tuple(findings))


def _file_validation_registries(
    package: ModelPackage,
) -> EngineeringExtensionRegistries:
    from .extensions import EngineeringExtensionRegistries

    registries = EngineeringExtensionRegistries()
    registries.sources.register(package.source.kind, object)  # type: ignore[arg-type]
    for variant in package.variants:
        registries.adapters.register(
            AdapterRegistration(
                adapter_id=variant.runtime.adapter_id,
                adapter_version=variant.runtime.version_specifier.removeprefix("=="),
                contract_version=variant.runtime.contract_version,
                command=("static-validation-only",),
                formats=frozenset({variant.format}),
                tasks=frozenset(task.task_id for task in package.tasks),
                platforms=frozenset(
                    item.split("/", 1)[0] for item in variant.platforms
                ),
                architectures=frozenset(
                    item.split("/", 1)[1] for item in variant.platforms
                ),
                execution_providers=frozenset({variant.accelerator}),
            )
        )
    for name in {
        vector.expected.kind
        for variant in package.variants
        for vector in variant.test_vectors
    }:
        registries.predicates.register(name, lambda _predicate, _output: False)
    return registries


def validate_package_file(path: str | Path) -> ConformanceReport:
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
        package = ModelPackage.model_validate(document)
        return validate_package_contract(package, _file_validation_registries(package))
    except Exception:
        return ConformanceReport(
            "package",
            "invalid-package",
            (
                _finding(
                    "manifest_invalid",
                    "The model package manifest is invalid.",
                    "Validate bounded JSON against the public package contract.",
                ),
            ),
        )


def validate_adapter_file(path: str | Path) -> ConformanceReport:
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
        registration = AdapterRegistration(
            adapter_id=str(document["adapter_id"]),
            adapter_version=str(document["adapter_version"]),
            contract_version=str(document["contract_version"]),
            command=tuple(str(item) for item in document["command"]),
            formats=frozenset(str(item) for item in document["formats"]),
            tasks=frozenset(str(item) for item in document["tasks"]),
            platforms=frozenset(str(item) for item in document["platforms"]),
            architectures=frozenset(str(item) for item in document["architectures"]),
            execution_providers=frozenset(
                str(item) for item in document["execution_providers"]
            ),
            maximum_control_bytes=int(
                document.get("maximum_control_bytes", 1024 * 1024)
            ),
        )
        findings = ()
        if registration.contract_version != "1.0":
            findings = (
                _finding(
                    "contract_incompatible",
                    "The adapter contract major is unsupported.",
                    "Implement the current public adapter contract.",
                ),
            )
        return ConformanceReport(
            "adapter",
            f"{registration.adapter_id}@{registration.adapter_version}",
            findings,
        )
    except (OSError, KeyError, TypeError, ValueError, RuntimeFailure):
        return ConformanceReport(
            "adapter",
            "invalid-adapter",
            (
                _finding(
                    "adapter_invalid",
                    "The static adapter declaration is invalid.",
                    "Repair the declaration without starting its command.",
                ),
            ),
        )


__all__ = [
    "ConformanceFinding",
    "ConformanceReport",
    "run_package_conformance",
    "validate_adapter_file",
    "validate_package_contract",
    "validate_package_file",
]
