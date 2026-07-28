"""Fail-closed compatibility metadata available to the thin Hermes plugin."""

from __future__ import annotations

import json
import platform
from dataclasses import dataclass
from pathlib import Path

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version


class CompatibilityError(RuntimeError):
    def __init__(self, code: str, message: str = "") -> None:
        self.code = code
        super().__init__(f"{code}: {message}" if message else code)


@dataclass(frozen=True, slots=True)
class CompatibilityPolicy:
    contract_version: int
    plugin_version: str
    runtime_specifier: str
    hermes_specifier: str
    python_specifier: str
    platforms: tuple[str, ...]
    data_schema_min: int
    data_schema_max: int
    plugin_install_capability: str
    released_hermes_version: str | None = None
    production_native_available: bool = False
    previous_native_version: str | None = None

    @classmethod
    def load(cls, path: str | Path) -> CompatibilityPolicy:
        source = Path(path)
        if not source.is_file():
            raise CompatibilityError("compatibility_contract_missing", str(source))
        try:
            value = json.loads(source.read_text(encoding="utf-8"))
            schema = value["data_schema"]
            policy = cls(
                contract_version=int(value["contract_version"]),
                plugin_version=str(Version(value["plugin_version"])),
                runtime_specifier=str(value["runtime_specifier"]),
                hermes_specifier=str(value["hermes_specifier"]),
                python_specifier=str(value["python_specifier"]),
                platforms=tuple(str(item) for item in value["platforms"]),
                data_schema_min=int(schema["min"]),
                data_schema_max=int(schema["max"]),
                plugin_install_capability=str(value["plugin_install_capability"]),
                released_hermes_version=(
                    str(value["released_hermes_version"])
                    if value.get("released_hermes_version")
                    else None
                ),
                production_native_available=bool(
                    value.get("production_native_available", False)
                ),
                previous_native_version=(
                    str(value["previous_native_version"])
                    if value.get("previous_native_version")
                    else None
                ),
            )
            policy.validate()
            return policy
        except (
            OSError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
            InvalidVersion,
            InvalidSpecifier,
        ) as exc:
            raise CompatibilityError(
                "compatibility_contract_invalid", str(exc)
            ) from exc

    def validate(self) -> None:
        if self.contract_version != 1:
            raise ValueError("unsupported contract version")
        SpecifierSet(self.runtime_specifier)
        SpecifierSet(self.hermes_specifier)
        SpecifierSet(self.python_specifier)
        if not self.platforms or not self.plugin_install_capability:
            raise ValueError("platforms and capability are required")
        if self.data_schema_min < 0 or self.data_schema_max < self.data_schema_min:
            raise ValueError("invalid data schema range")
        if self.production_native_available:
            if self.released_hermes_version is None:
                raise ValueError("released Hermes version is required for production")
            if Version(self.released_hermes_version) not in SpecifierSet(
                self.hermes_specifier
            ):
                raise ValueError(
                    "released Hermes version is outside the supported range"
                )
            if self.previous_native_version is None:
                raise ValueError(
                    "previous native version is required for rollback evidence"
                )

    def require_compatible(
        self,
        *,
        plugin_version: str,
        runtime_version: str,
        hermes_version: str,
        python_version: str,
        platform_tag: str,
        data_schema: int,
        capability: str,
    ) -> None:
        checks: tuple[tuple[bool, str, str], ...] = (
            (
                Version(plugin_version) == Version(self.plugin_version),
                "plugin_incompatible",
                plugin_version,
            ),
            (
                Version(runtime_version) in SpecifierSet(self.runtime_specifier),
                "runtime_incompatible",
                runtime_version,
            ),
            (
                Version(hermes_version) in SpecifierSet(self.hermes_specifier),
                "hermes_incompatible",
                hermes_version,
            ),
            (
                Version(python_version) in SpecifierSet(self.python_specifier),
                "python_incompatible",
                python_version,
            ),
            (platform_tag in self.platforms, "platform_incompatible", platform_tag),
            (
                self.data_schema_min <= data_schema <= self.data_schema_max,
                "data_schema_incompatible",
                str(data_schema),
            ),
            (
                capability == self.plugin_install_capability,
                "plugin_capability_incompatible",
                capability,
            ),
        )
        for ok, code, actual in checks:
            if not ok:
                raise CompatibilityError(code, actual)


def current_platform_tag() -> str:
    system = platform.system().lower()
    system = {"darwin": "macos"}.get(system, system)
    machine = platform.machine().lower()
    machine = {"amd64": "x86_64", "x64": "x86_64", "aarch64": "arm64"}.get(
        machine, machine
    )
    return f"{system}-{machine}"
