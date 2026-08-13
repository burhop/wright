from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import sqlite3
import subprocess
import sys
from collections.abc import Callable, Iterable, Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .capability_models import (
    CapabilityCompatibility,
    CompatibilityReason,
    MachineCompatibilityObservation,
)
from .catalog_models import CatalogEntry

OBSERVATION_TTL = timedelta(minutes=15)
_EXECUTABLE_TOKEN = re.compile(r"^[A-Za-z0-9_.+-]{1,100}$")
_RUNTIME_COMMANDS = {"node": "node"}
_PACKAGE_MANAGER_COMMANDS = {"uv": "uv", "pip": "pip", "npm": "npm"}
_CONTAINER_COMMAND = "docker"


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def _platform_key(system: str, architecture: str) -> str:
    os_key = system.lower()
    arch = architecture.lower().replace("amd64", "x86_64")
    if os_key == "windows" and arch == "x86_64":
        return "windows_11_x64"
    if os_key == "linux" and arch == "x86_64":
        return "linux_x64"
    if os_key == "linux" and arch in {"arm64", "aarch64"}:
        return "linux_arm64"
    if os_key == "darwin" and arch == "x86_64":
        return "macos_x64"
    if os_key == "darwin" and arch in {"arm64", "aarch64"}:
        return "macos_arm64"
    return f"{os_key or 'unknown'}_{arch or 'unknown'}"


def _default_version_reader(executable: str) -> str | None:
    try:
        completed = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            check=False,
            shell=False,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    output = (completed.stdout or completed.stderr).strip().splitlines()
    return output[0][:200] if output else None


def _command_fact(
    command: str,
    *,
    which: Callable[[str], str | None],
    version_reader: Callable[[str], str | None],
    read_version: bool = True,
) -> dict[str, Any]:
    resolved = which(command)
    return {
        "available": resolved is not None,
        "resolved_path": resolved,
        "version": version_reader(resolved) if resolved and read_version else None,
    }


def observe_machine(
    *,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    which: Callable[[str], str | None] = shutil.which,
    version_reader: Callable[[str], str | None] = _default_version_reader,
    system_reader: Callable[[], str] = platform.system,
    version_system_reader: Callable[[], str] = platform.version,
    architecture_reader: Callable[[], str] = platform.machine,
    distribution_mode: str | None = None,
    network_policy: str = "unknown",
    required_executables: Iterable[str] = (),
    host_detectors: Mapping[str, Callable[[], Mapping[str, Any]]] | None = None,
) -> MachineCompatibilityObservation:
    """Capture bounded, allowlisted facts without contacting a capability endpoint."""
    observed_at = clock()
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=UTC)
    system = system_reader()
    architecture = architecture_reader()

    runtimes = {
        "python": {
            "available": True,
            "resolved_path": sys.executable,
            "version": platform.python_version(),
        }
    }
    for name, command in _RUNTIME_COMMANDS.items():
        runtimes[name] = _command_fact(
            command, which=which, version_reader=version_reader
        )

    package_managers = {
        name: _command_fact(command, which=which, version_reader=version_reader)
        for name, command in _PACKAGE_MANAGER_COMMANDS.items()
    }
    container_runtime = _command_fact(
        _CONTAINER_COMMAND, which=which, version_reader=version_reader
    )

    host_observations: dict[str, dict[str, Any]] = {}
    for executable in sorted(set(required_executables)):
        if not _EXECUTABLE_TOKEN.fullmatch(executable):
            continue
        host_observations[f"executable:{executable}"] = _command_fact(
            executable,
            which=which,
            version_reader=version_reader,
            read_version=False,
        )

    for name, detector in sorted((host_detectors or {}).items()):
        try:
            raw = detector()
            fact = dict(raw) if isinstance(raw, Mapping) else {"available": False}
            host_observations[name] = {
                "available": bool(fact.get("available", False)),
                "version": fact.get("version"),
                "reason": fact.get("reason"),
            }
        except Exception:
            host_observations[name] = {
                "available": False,
                "version": None,
                "reason": "detector_failed",
            }

    payload = {
        "observed_at": observed_at.isoformat(),
        "expires_at": (observed_at + OBSERVATION_TTL).isoformat(),
        "platform_key": _platform_key(system, architecture),
        "os_name": system,
        "os_version": version_system_reader(),
        "architecture": architecture,
        "distribution_mode": distribution_mode
        or os.getenv("WRIGHT_DISTRIBUTION_MODE", "native"),
        "runtimes": runtimes,
        "package_managers": package_managers,
        "container_runtime": container_runtime,
        "network_policy": network_policy,
        "host_observations": host_observations,
    }
    digest = hashlib.sha256(_canonical_json(payload)).hexdigest()
    return MachineCompatibilityObservation(
        observation_id=f"machine-{digest[:20]}", digest=digest, **payload
    )


def save_machine_observation(
    database_path: str | Path, observation: MachineCompatibilityObservation
) -> None:
    serialized = observation.model_dump(mode="json")
    with sqlite3.connect(str(database_path)) as connection:
        connection.execute(
            """INSERT OR REPLACE INTO machine_compatibility_observations (
                observation_id, observed_at, expires_at, platform_key, os_name,
                os_version, architecture, distribution_mode, observation_json, digest
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                observation.observation_id,
                int(observation.observed_at.timestamp()),
                int(observation.expires_at.timestamp()),
                observation.platform_key,
                observation.os_name,
                observation.os_version,
                observation.architecture,
                observation.distribution_mode,
                json.dumps(serialized, sort_keys=True),
                observation.digest,
            ),
        )


def load_latest_machine_observation(
    database_path: str | Path, *, now: datetime | None = None
) -> MachineCompatibilityObservation | None:
    now = now or datetime.now(UTC)
    try:
        with sqlite3.connect(str(database_path)) as connection:
            row = connection.execute(
                """SELECT observation_json FROM machine_compatibility_observations
                   WHERE expires_at > ? ORDER BY observed_at DESC LIMIT 1""",
                (int(now.timestamp()),),
            ).fetchone()
    except sqlite3.OperationalError:
        return None
    return MachineCompatibilityObservation.model_validate_json(row[0]) if row else None


def _reason(code: str, message: str, recovery: str, source: str) -> CompatibilityReason:
    return CompatibilityReason(
        code=code, message=message, recovery=recovery, source=source
    )


def _required_runtimes(entry: CatalogEntry) -> tuple[set[str], set[str]]:
    runtimes: set[str] = set()
    managers: set[str] = set()
    if entry.dependencies.python or entry.install_method in {"pip", "uvx"}:
        runtimes.add("python")
    if entry.install_method == "uvx":
        managers.add("uv")
    if entry.dependencies.node or entry.install_method == "npm":
        runtimes.add("node")
        managers.add("npm")
    if entry.install_method == "pip":
        managers.add("pip")
    return runtimes, managers


def evaluate_compatibility(
    entry: CatalogEntry, observation: MachineCompatibilityObservation
) -> CapabilityCompatibility:
    reasons: list[CompatibilityReason] = []
    status = "compatible"

    def worsen(candidate: str) -> None:
        nonlocal status
        order = {"compatible": 0, "uncertain": 1, "incompatible": 2, "blocked": 3}
        if order[candidate] > order[status]:
            status = candidate

    if entry.installability_tier in {"blocked", "non_working"}:
        worsen("blocked")
        reasons.append(
            _reason(
                "catalog_onboarding_blocked",
                entry.install_blocked_reason
                or "The catalog does not currently permit onboarding this capability.",
                "Review the cited evidence or choose a supported alternative.",
                "catalog.installability_tier",
            )
        )

    platform_claim = entry.platform_support.get(observation.platform_key)
    if platform_claim is None or platform_claim.status == "unknown":
        worsen("uncertain")
        reasons.append(
            _reason(
                "platform_support_unknown",
                f"Support for {observation.platform_key} is not known.",
                "Use a tested platform or perform an approved local validation.",
                "catalog.platform_support",
            )
        )
    elif platform_claim.status == "no":
        worsen("incompatible")
        reasons.append(
            _reason(
                "platform_not_supported",
                f"The catalog records {observation.platform_key} as unsupported.",
                "Choose a supported platform or another capability.",
                "catalog.platform_support",
            )
        )
    elif (
        platform_claim.status in {"likely", "host-dependent"}
        or not platform_claim.tested
    ):
        worsen("uncertain")
        reasons.append(
            _reason(
                "platform_support_unverified",
                f"Support for {observation.platform_key} is plausible but unverified.",
                "Run the read-only preflight and approved validation before use.",
                "catalog.platform_support",
            )
        )

    runtimes, managers = _required_runtimes(entry)
    for name in sorted(runtimes):
        fact = observation.runtimes.get(name)
        if not fact or not fact.get("available"):
            worsen("incompatible")
            reasons.append(
                _reason(
                    f"runtime_{name}_missing",
                    f"Required runtime '{name}' was not found.",
                    f"Install a supported {name} runtime, then observe again.",
                    "machine.runtimes",
                )
            )
    for name in sorted(managers):
        fact = observation.package_managers.get(name)
        if not fact or not fact.get("available"):
            worsen("incompatible")
            reasons.append(
                _reason(
                    f"package_manager_{name}_missing",
                    f"Required package manager '{name}' was not found.",
                    f"Install {name}, then observe again.",
                    "machine.package_managers",
                )
            )

    if entry.install_method == "docker" and not (
        observation.container_runtime and observation.container_runtime.get("available")
    ):
        worsen("incompatible")
        reasons.append(
            _reason(
                "container_runtime_missing",
                "A required container runtime was not found.",
                "Install a supported container runtime, then observe again.",
                "machine.container_runtime",
            )
        )

    for dependency in sorted(entry.dependencies.system):
        fact = observation.host_observations.get(f"executable:{dependency}")
        if fact is None:
            worsen("uncertain")
            reasons.append(
                _reason(
                    "system_dependency_unobserved",
                    f"Required system dependency '{dependency}' was not observed.",
                    "Run a capability-specific read-only observation.",
                    "machine.host_observations",
                )
            )
        elif not fact.get("available"):
            worsen("incompatible")
            reasons.append(
                _reason(
                    "system_dependency_missing",
                    f"Required system dependency '{dependency}' was not found.",
                    f"Install {dependency}, then observe again.",
                    "machine.host_observations",
                )
            )

    for host in sorted(entry.host_software_required):
        fact = observation.host_observations.get(host)
        if fact is None:
            worsen("uncertain")
            reasons.append(
                _reason(
                    "host_software_unobserved",
                    f"Required host software '{host}' could not be confirmed.",
                    "Install/configure the host and enable its approved detector.",
                    "machine.host_observations",
                )
            )
        elif not fact.get("available"):
            worsen("incompatible")
            reasons.append(
                _reason(
                    "host_software_missing",
                    f"Required host software '{host}' was not found.",
                    f"Install or start {host}, then observe again.",
                    "machine.host_observations",
                )
            )

    if entry.locality == "remote" and observation.network_policy != "allowed":
        worsen("uncertain")
        reasons.append(
            _reason(
                "network_access_unconfirmed",
                "This capability is remote and network access was not confirmed.",
                "Review the endpoint and approve network access during onboarding.",
                "machine.network_policy",
            )
        )

    return CapabilityCompatibility(
        status=status,
        platform_key=observation.platform_key,
        reasons=sorted(reasons, key=lambda reason: (reason.code, reason.message)),
        observation_id=observation.observation_id,
        observed_at=observation.observed_at,
    )
