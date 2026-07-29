from __future__ import annotations

from dataclasses import dataclass
import re
import subprocess
from typing import Callable


Runner = Callable[..., subprocess.CompletedProcess[str]]
REQUIRED_COMMANDS = ("install", "update", "remove")


@dataclass(frozen=True, slots=True)
class HermesGitInterface:
    version: str
    adapter_protocol: str
    install_interface: str
    commands: tuple[str, ...]
    supported: bool


def probe_hermes_git_plugin_interface(
    executable: str = "hermes", *, runner: Runner = subprocess.run
) -> HermesGitInterface:
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
        raise RuntimeError("hermes_git_interface_probe_failed")
    version_output = version_result.stdout + version_result.stderr
    help_output = help_result.stdout + help_result.stderr
    match = re.search(r"Hermes Agent v([^\s]+)", version_output)
    version = match.group(1) if match else "unknown"
    commands = tuple(item for item in REQUIRED_COMMANDS if item in help_output)
    git_interface = bool(
        re.search(
            r"install plugins from git|git url|pull latest|git", help_output, re.I
        )
    )
    supported = commands == REQUIRED_COMMANDS and git_interface
    return HermesGitInterface(
        version=version,
        adapter_protocol="hermes-git-plugin-v1",
        install_interface="git",
        commands=commands,
        supported=supported,
    )


def require_released_git_plugin_interface(
    executable: str = "hermes", *, runner: Runner = subprocess.run
) -> HermesGitInterface:
    result = probe_hermes_git_plugin_interface(executable, runner=runner)
    if not result.supported:
        raise RuntimeError(
            "released Hermes does not expose the required Git plugin "
            "install/update/remove interface"
        )
    return result
