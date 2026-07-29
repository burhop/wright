from __future__ import annotations

import shutil
import subprocess

import pytest

from scripts.release.hermes_capability import (
    probe_hermes_package_capability,
    require_released_package_capability,
)


CURRENT_GIT_ONLY_HELP = """Install plugins from Git repositories.
install  Install a plugin from a Git URL or owner/repo
update   Pull latest changes for an installed plugin
remove   Remove an installed plugin
"""


def _runner(outputs: list[str]):
    def run(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout=outputs.pop(0), stderr="")

    return run


def test_current_git_only_hermes_interface_is_rejected() -> None:
    result = probe_hermes_package_capability(
        runner=_runner(["Hermes Agent v0.19.0\n", CURRENT_GIT_ONLY_HELP])
    )
    assert result.version == "0.19.0"
    assert result.git_only
    assert not result.supported
    assert result.capability is None

    with pytest.raises(RuntimeError, match="Git-only"):
        require_released_package_capability(
            runner=_runner(["Hermes Agent v0.19.0\n", CURRENT_GIT_ONLY_HELP])
        )


def test_required_package_interface_is_accepted_only_when_complete() -> None:
    package_help = " ".join(
        (
            "Install plugins from immutable Python distributions.",
            "install-package",
            "update-package",
            "rollback-package",
            "remove-package",
        )
    )
    result = require_released_package_capability(
        runner=_runner(["Hermes Agent v0.20.0\n", package_help])
    )
    assert result.supported
    assert result.capability == "python-distribution-v1"


def test_installed_known_git_only_hermes_is_not_mistaken_for_package_capable() -> None:
    executable = shutil.which("hermes")
    if executable is None:
        result = probe_hermes_package_capability(
            runner=_runner(["Hermes Agent v0.19.0\n", CURRENT_GIT_ONLY_HELP])
        )
    else:
        result = probe_hermes_package_capability(executable)
    if result.version in {"0.18.2", "0.19.0"}:
        assert result.git_only
        assert not result.supported
