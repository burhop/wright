"""Fail-closed model source, artifact, license, and compatibility policy."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import Mapping
from urllib.parse import urlsplit

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version

from .models import ModelPackage

SAFE_FORMATS = frozenset({"onnx", "safetensors", "numpy-npz", "wright-affine-json"})
UNSAFE_SUFFIXES = frozenset(
    {
        ".bat",
        ".bin",
        ".cmd",
        ".com",
        ".dll",
        ".dylib",
        ".exe",
        ".jar",
        ".joblib",
        ".js",
        ".macro",
        ".msi",
        ".plugin",
        ".pickle",
        ".pkl",
        ".ps1",
        ".pt",
        ".pth",
        ".py",
        ".pyc",
        ".sh",
        ".so",
        ".tar",
        ".tgz",
        ".whl",
        ".zip",
    }
)
_ACTUATION = re.compile(
    r"(?i)(?:start|command|control|drive|move|heat|extrude|spin)[-_. ]*(?:spindle|printer|robot|plc|motor|axis|heater|extruder|machine)"
)


class PolicyState(StrEnum):
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    UNCERTAIN = "uncertain"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class PolicyBlocker:
    category: str
    message: str
    recovery: str


@dataclass(frozen=True, slots=True)
class PolicyResult:
    state: PolicyState
    blockers: tuple[PolicyBlocker, ...]


@dataclass(frozen=True, slots=True)
class HostObservation:
    platform: str
    architecture: str
    available_disk_bytes: int
    available_ram_bytes: int
    accelerators: frozenset[str]
    runtime_adapters: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "runtime_adapters", MappingProxyType(dict(self.runtime_adapters))
        )
        if self.available_disk_bytes < 0 or self.available_ram_bytes < 0:
            raise ValueError("Host resources cannot be negative")

    @classmethod
    def reference(cls) -> "HostObservation":
        return cls(
            platform="windows",
            architecture="x86_64",
            available_disk_bytes=1_000_000_000,
            available_ram_bytes=1_000_000_000,
            accelerators=frozenset({"cpu"}),
            runtime_adapters={"wright-deterministic": "1.0.0"},
        )


def validate_artifact_path(path: str) -> str:
    normalized = unicodedata.normalize("NFC", path)
    if normalized != path or "\\" in path or "//" in path:
        raise ValueError("Artifact path is not normalized")
    if re.match(r"^[A-Za-z]:", path):
        raise ValueError("Artifact path cannot contain a drive")
    parsed = PurePosixPath(path)
    raw_parts = path.split("/")
    if (
        parsed.is_absolute()
        or not path
        or any(part in {"", ".", ".."} for part in raw_parts)
    ):
        raise ValueError("Artifact path must be a normalized relative path")
    if parsed.suffix.lower() in UNSAFE_SUFFIXES:
        raise ValueError("Artifact path has a prohibited executable/archive format")
    return parsed.as_posix()


class ModelPolicy:
    def evaluate(
        self,
        package: ModelPackage,
        *,
        variant_id: str,
        host: HostObservation,
    ) -> PolicyResult:
        blockers: list[PolicyBlocker] = []
        try:
            variant = package.variant(variant_id)
        except KeyError:
            return PolicyResult(
                PolicyState.BLOCKED,
                (
                    PolicyBlocker(
                        "variant_missing",
                        "The selected model variant is not present.",
                        "Choose an available reviewed variant.",
                    ),
                ),
            )
        if package.review_state != "approved":
            blockers.append(
                PolicyBlocker(
                    "model_not_approved",
                    "The model package is not approved for installation.",
                    "Review its current trust evidence and blockers.",
                )
            )
        if package.source.access in {"gated", "private"}:
            blockers.append(
                PolicyBlocker(
                    "source_gated",
                    "The source requires independently granted access.",
                    "Complete any publisher-controlled action outside Wright, then make a fresh plan.",
                )
            )
        source = urlsplit(package.source.uri)
        if (
            package.source.kind in {"hugging_face", "https"}
            and source.scheme != "https"
        ):
            blockers.append(
                PolicyBlocker(
                    "source_insecure",
                    "The external source does not use approved HTTPS transport.",
                    "Use a pinned HTTPS source from an approved host.",
                )
            )
        if source.hostname and package.source.allowed_hosts:
            if source.hostname.lower() not in {
                item.lower() for item in package.source.allowed_hosts
            }:
                blockers.append(
                    PolicyBlocker(
                        "source_host_unapproved",
                        "The source host is not declared by the package.",
                        "Review and republish the package with the exact approved host.",
                    )
                )
        if package.license.acceptance_required:
            blockers.append(
                PolicyBlocker(
                    "license_action_required",
                    "The license requires an external acceptance action.",
                    "Review and accept terms independently before creating a fresh plan.",
                )
            )
        if package.license.redistribution == "review_required":
            blockers.append(
                PolicyBlocker(
                    "license_unapproved",
                    "The redistribution policy still needs review.",
                    "Record authoritative license evidence and an explicit decision.",
                )
            )
        if variant.format not in SAFE_FORMATS:
            blockers.append(
                PolicyBlocker(
                    "unsafe_format",
                    "The model format is not on the reviewed data-only allowlist.",
                    "Select a Safetensors, ONNX, or reviewed Wright data-only variant.",
                )
            )
        for artifact in variant.artifacts:
            try:
                validate_artifact_path(artifact.path)
            except ValueError:
                blockers.append(
                    PolicyBlocker(
                        "path_unsafe",
                        "A declared artifact path or format is unsafe.",
                        "Publish a normalized data-only artifact manifest.",
                    )
                )
                break
        if any(_ACTUATION.search(task.task_id) for task in package.tasks):
            blockers.append(
                PolicyBlocker(
                    "physical_actuation_forbidden",
                    "Physical actuation tasks are outside the model capability boundary.",
                    "Use analysis-only engineering tasks; Gate E remains closed.",
                )
            )
        if f"{host.platform}/{host.architecture}" not in variant.platforms:
            blockers.append(
                PolicyBlocker(
                    "incompatible_platform",
                    "This variant does not support the observed platform and architecture.",
                    "Choose a compatible variant or machine.",
                )
            )
        required_disk = (
            variant.resources.download_bytes + variant.resources.installed_bytes
        )
        if host.available_disk_bytes < required_disk:
            blockers.append(
                PolicyBlocker(
                    "insufficient_disk",
                    "Available disk is below the declared acquisition and install ceiling.",
                    "Free disk space or choose a smaller variant.",
                )
            )
        if host.available_ram_bytes < variant.resources.ram_bytes:
            blockers.append(
                PolicyBlocker(
                    "insufficient_resources",
                    "Available RAM is below the declared load ceiling.",
                    "Close other workloads or choose a smaller variant.",
                )
            )
        if (
            variant.accelerator != "none"
            and variant.accelerator not in host.accelerators
        ):
            blockers.append(
                PolicyBlocker(
                    "insufficient_resources",
                    "The declared execution provider is unavailable.",
                    "Choose a declared CPU fallback or compatible accelerator.",
                )
            )
        installed = host.runtime_adapters.get(variant.runtime.adapter_id)
        if installed is None:
            blockers.append(
                PolicyBlocker(
                    "runtime_missing",
                    "The required runtime adapter is not installed.",
                    "Review the adapter through its separate install plan.",
                )
            )
        else:
            try:
                matches = Version(installed) in SpecifierSet(
                    variant.runtime.version_specifier
                )
            except (InvalidVersion, InvalidSpecifier):
                matches = False
            if not matches:
                blockers.append(
                    PolicyBlocker(
                        "runtime_incompatible",
                        "The installed runtime adapter version is incompatible.",
                        "Install a separately reviewed compatible adapter version.",
                    )
                )
        return PolicyResult(
            PolicyState.BLOCKED if blockers else PolicyState.COMPATIBLE,
            tuple(blockers),
        )


__all__ = [
    "HostObservation",
    "ModelPolicy",
    "PolicyBlocker",
    "PolicyResult",
    "PolicyState",
    "SAFE_FORMATS",
    "validate_artifact_path",
]
