from __future__ import annotations

import shutil
import subprocess

from scripts.release.hermes_capability import (
    probe_hermes_git_plugin_interface,
    require_released_git_plugin_interface,
)


CURRENT_GIT_HELP = """Install plugins from Git repositories.
install  Install a plugin from a Git URL or owner/repo
update   Pull latest changes for an installed plugin
remove   Remove an installed plugin
"""


def _runner(outputs: list[str]):
    def run(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout=outputs.pop(0), stderr="")

    return run


def test_current_hermes_git_interface_is_the_supported_adapter_boundary() -> None:
    result = require_released_git_plugin_interface(
        runner=_runner(["Hermes Agent v0.19.0\n", CURRENT_GIT_HELP])
    )
    assert result.version == "0.19.0"
    assert result.supported
    assert result.adapter_protocol == "hermes-git-plugin-v1"
    assert result.install_interface == "git"
    assert result.commands == ("install", "update", "remove")


def test_incomplete_git_interface_fails_closed() -> None:
    result = probe_hermes_git_plugin_interface(
        runner=_runner(["Hermes Agent v0.19.0\n", "install from Git\n"])
    )
    assert not result.supported


def test_installed_hermes_uses_the_same_real_interface_when_available() -> None:
    executable = shutil.which("hermes")
    if executable is None:
        result = probe_hermes_git_plugin_interface(
            runner=_runner(["Hermes Agent v0.19.0\n", CURRENT_GIT_HELP])
        )
    else:
        result = probe_hermes_git_plugin_interface(executable)
    if result.version in {"0.18.2", "0.19.0"}:
        assert result.adapter_protocol == "hermes-git-plugin-v1"
        assert result.install_interface == "git"
