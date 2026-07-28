from __future__ import annotations

from dataclasses import dataclass
import re
import subprocess
from typing import Callable


Runner = Callable[..., subprocess.CompletedProcess[str]]
REQUIRED_COMMANDS = (
    "install-package",
    "update-package",
    "rollback-package",
    "remove-package",
)


@dataclass(frozen=True, slots=True)
class HermesPackageCapability:
    version: str
    capability: str | None
    commands: tuple[str, ...]
    git_only: bool
    supported: bool


def probe_hermes_package_capability(
    executable: str = "hermes", *, runner: Runner = subprocess.run
) -> HermesPackageCapability:
    version_result = runner(
        [executable, "--version"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    help_result = runner(
        [executable, "plugins", "--help"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if version_result.returncode or help_result.returncode:
        raise RuntimeError("hermes_capability_probe_failed")
    version_output = version_result.stdout + version_result.stderr
    help_output = help_result.stdout + help_result.stderr
    match = re.search(r"Hermes Agent v([^\s]+)", version_output)
    version = match.group(1) if match else "unknown"
    commands = tuple(item for item in REQUIRED_COMMANDS if item in help_output)
    git_only = bool(
        re.search(r"install plugins from git|git url|pull latest", help_output, re.I)
    )
    supported = commands == REQUIRED_COMMANDS and not git_only
    return HermesPackageCapability(
        version=version,
        capability="python-distribution-v1" if supported else None,
        commands=commands,
        git_only=git_only,
        supported=supported,
    )


def require_released_package_capability(
    executable: str = "hermes", *, runner: Runner = subprocess.run
) -> HermesPackageCapability:
    result = probe_hermes_package_capability(executable, runner=runner)
    if not result.supported:
        raise RuntimeError(
            "released Hermes does not provide python-distribution-v1; "
            "Git-only plugins cannot satisfy native Wright installation"
        )
    return result
