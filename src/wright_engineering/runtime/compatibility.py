"""Manager-neutral Wright runtime and adapter compatibility policy."""

from __future__ import annotations

import json
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version


class CompatibilityError(RuntimeError):
    def __init__(self, code: str, message: str = "") -> None:
        self.code = code
        super().__init__(f"{code}: {message}" if message else code)


@dataclass(frozen=True, slots=True)
class ManagerProtocol:
    adapter_protocol: str
    install_interface: str
    host_specifier: str | None = None
    transports: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> ManagerProtocol:
        return cls(
            adapter_protocol=str(value["adapter_protocol"]),
            install_interface=str(value["install_interface"]),
            host_specifier=(
                str(value["host_specifier"]) if value.get("host_specifier") else None
            ),
            transports=tuple(str(item) for item in value.get("transports", ())),
        )

    def validate(self) -> None:
        if not self.adapter_protocol or not self.install_interface:
            raise ValueError("manager protocol fields are required")
        if self.host_specifier:
            SpecifierSet(self.host_specifier)
        if any(item not in {"stdio", "streamable-http"} for item in self.transports):
            raise ValueError("unsupported MCP transport")


@dataclass(frozen=True, slots=True)
class CompatibilityPolicy:
    contract_version: int
    runtime_version: str
    runtime_specifier: str
    python_specifier: str
    platforms: tuple[str, ...]
    data_schema_min: int
    data_schema_max: int
    manager_protocols: dict[str, ManagerProtocol]
    previous_runtime_version: str | None = None

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
                runtime_version=str(Version(value["runtime_version"])),
                runtime_specifier=str(value["runtime_specifier"]),
                python_specifier=str(value["python_specifier"]),
                platforms=tuple(str(item) for item in value["platforms"]),
                data_schema_min=int(schema["min"]),
                data_schema_max=int(schema["max"]),
                manager_protocols={
                    str(manager_id): ManagerProtocol.from_dict(protocol)
                    for manager_id, protocol in value["manager_protocols"].items()
                },
                previous_runtime_version=(
                    str(Version(value["previous_runtime_version"]))
                    if value.get("previous_runtime_version")
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
        if self.contract_version != 2:
            raise ValueError("unsupported contract version")
        if Version(self.runtime_version) not in SpecifierSet(self.runtime_specifier):
            raise ValueError("runtime version is outside its own supported range")
        SpecifierSet(self.python_specifier)
        if not self.platforms or not self.manager_protocols:
            raise ValueError("platforms and manager protocols are required")
        if self.data_schema_min < 0 or self.data_schema_max < self.data_schema_min:
            raise ValueError("invalid data schema range")
        for protocol in self.manager_protocols.values():
            protocol.validate()

    def require_runtime_compatible(
        self,
        *,
        runtime_version: str,
        python_version: str,
        platform_tag: str,
        data_schema: int,
    ) -> None:
        checks: tuple[tuple[bool, str, str], ...] = (
            (
                Version(runtime_version) in SpecifierSet(self.runtime_specifier),
                "runtime_incompatible",
                runtime_version,
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
        )
        for ok, code, actual in checks:
            if not ok:
                raise CompatibilityError(code, actual)

    def require_manager_compatible(
        self,
        *,
        manager_id: str,
        adapter_protocol: str,
        manager_version: str | None = None,
    ) -> None:
        protocol = self.manager_protocols.get(manager_id)
        if protocol is None:
            raise CompatibilityError("manager_unsupported", manager_id)
        if adapter_protocol != protocol.adapter_protocol:
            raise CompatibilityError("manager_protocol_incompatible", adapter_protocol)
        if protocol.host_specifier:
            if not manager_version:
                raise CompatibilityError("manager_version_required", manager_id)
            if Version(manager_version) not in SpecifierSet(protocol.host_specifier):
                raise CompatibilityError(
                    "manager_version_incompatible", manager_version
                )

    def require_compatible(
        self,
        *,
        runtime_version: str,
        python_version: str,
        platform_tag: str,
        data_schema: int,
        manager_id: str,
        adapter_protocol: str,
        manager_version: str | None = None,
    ) -> None:
        self.require_runtime_compatible(
            runtime_version=runtime_version,
            python_version=python_version,
            platform_tag=platform_tag,
            data_schema=data_schema,
        )
        self.require_manager_compatible(
            manager_id=manager_id,
            adapter_protocol=adapter_protocol,
            manager_version=manager_version,
        )


def current_platform_tag() -> str:
    system = platform.system().lower()
    system = {"darwin": "macos"}.get(system, system)
    machine = platform.machine().lower()
    machine = {"amd64": "x86_64", "x64": "x86_64", "aarch64": "arm64"}.get(
        machine, machine
    )
    return f"{system}-{machine}"
