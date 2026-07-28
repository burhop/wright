from __future__ import annotations

import json
from pathlib import Path
import tomllib

from wright_engineering.hermes_plugin.commands import HELP


ROOT = Path(__file__).resolve().parents[1]
COMMANDS = (
    "start",
    "status",
    "doctor",
    "stop",
    "update",
    "rollback",
    "uninstall",
    "purge",
)


def test_commands_and_package_identity_do_not_drift_across_public_surfaces() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]
    compatibility = json.loads(
        (ROOT / "src/wright_engineering/compatibility.json").read_text(encoding="utf-8")
    )
    native = (ROOT / "docs/getting-started/hermes-plugin.md").read_text(
        encoding="utf-8"
    )
    runbook = (ROOT / "docs/release/release-runbook.md").read_text(encoding="utf-8")

    assert project["name"] == "wright-engineering"
    assert project["version"] == compatibility["plugin_version"]
    assert project["entry-points"]["hermes_agent.plugins"]["wright"].endswith(
        ":register"
    )
    assert project["optional-dependencies"]["runtime"]
    assert compatibility["plugin_install_capability"] == "python-distribution-v1"
    assert "wright-engineering==<version>" in native
    assert "wright-engineering" in runbook
    for command in COMMANDS:
        assert command in HELP
        assert f"/wright {command}" in native


def test_availability_and_platform_claims_follow_compatibility_evidence() -> None:
    compatibility = json.loads(
        (ROOT / "src/wright_engineering/compatibility.json").read_text(encoding="utf-8")
    )
    matrix = (ROOT / "docs/getting-started/install-matrix.md").read_text(
        encoding="utf-8"
    )
    prerequisites = (ROOT / "docs/getting-started/prerequisites.md").read_text(
        encoding="utf-8"
    )
    native = (ROOT / "docs/getting-started/hermes-plugin.md").read_text(
        encoding="utf-8"
    )
    assert compatibility["production_native_available"] is False
    assert compatibility["released_hermes_version"] is None
    assert "`production_native_available` is `false`" in matrix
    assert "no released Hermes version" in prerequisites
    assert "Do not advertise this path as released" in native
    for label in ("Windows 11", "Ubuntu", "macOS Sonoma"):
        assert label in prerequisites


def test_native_user_docs_contain_no_repository_install_instructions() -> None:
    native_docs = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in (
            "docs/getting-started/hermes-plugin.md",
            "docs/hermes-desktop-wright.md",
        )
    )
    for forbidden in (
        "git clone",
        "pip install -e",
        "uv tool install hermes-agent --with",
        "WRIGHT_REPO_DIR=",
        "npm run build",
    ):
        assert forbidden not in native_docs
