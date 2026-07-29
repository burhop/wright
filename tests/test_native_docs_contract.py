from __future__ import annotations

import json
import importlib.util
from pathlib import Path
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def _load_adapter_commands():
    helper_path = ROOT / "tests/native_runtime/adapter_support.py"
    spec = importlib.util.spec_from_file_location(
        "wright_native_docs_adapter_support", helper_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("adapter_support_load_failed")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.load_adapter_commands()


HELP = _load_adapter_commands().WRIGHT_HELP_TEXT
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
    assert project["version"] == compatibility["runtime_version"]
    assert "hermes_agent.plugins" not in project.get("entry-points", {})
    assert project["optional-dependencies"]["runtime"]
    assert compatibility["manager_protocols"]["hermes"]["install_interface"] == "git"
    assert compatibility["manager_protocols"]["codex"]["adapter_protocol"] == "mcp-v1"
    assert "hermes plugins install" in native
    assert "wright-engineering" in runbook
    for command in COMMANDS:
        assert command in HELP
        assert f"/wright {command}" in native


def test_platform_and_manager_claims_follow_compatibility_evidence() -> None:
    compatibility = json.loads(
        (ROOT / "src/wright_engineering/compatibility.json").read_text(encoding="utf-8")
    )
    matrix = (ROOT / "docs/getting-started/install-matrix.md").read_text(
        encoding="utf-8"
    )
    prerequisites = (ROOT / "docs/getting-started/prerequisites.md").read_text(
        encoding="utf-8"
    )
    assert compatibility["contract_version"] == 2
    assert set(compatibility["manager_protocols"]) >= {"hermes", "codex"}
    for label in ("Hermes", "Codex", "OpenClaw", "Docker"):
        assert label in matrix
    for label in ("Windows 11", "Ubuntu", "macOS Sonoma"):
        assert label in prerequisites


def test_native_user_docs_contain_no_repository_install_instructions() -> None:
    native_docs = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in (
            "docs/getting-started/hermes-plugin.md",
            "docs/getting-started/codex.md",
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


def test_manager_examples_use_real_secret_safe_profile_shapes() -> None:
    codex = tomllib.loads(
        (ROOT / "integrations/codex/config.toml.example").read_text(encoding="utf-8")
    )["mcp_servers"]["wright"]
    assert codex["command"] == "wright"
    assert codex["args"][:3] == ["mcp", "serve", "--stdio"]
    assert "WRIGHT_API_TOKEN" not in json.dumps(codex)
