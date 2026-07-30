from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_native_pr_workflow_has_no_publication_authority_or_stable_mutation() -> None:
    workflow = (ROOT / ".github/workflows/native-hermes-pr.yml").read_text(
        encoding="utf-8"
    )
    assert "permissions:\n  contents: read" in workflow
    assert "id-token: write" not in workflow
    assert "packages: write" not in workflow
    assert "gh-action-pypi-publish" not in workflow
    assert "docker/login-action" not in workflow
    assert "stable Hermes channel" not in workflow
    assert "softprops/action-gh-release" not in workflow


def test_native_candidate_builds_once_and_runs_every_claimed_platform() -> None:
    workflow = (ROOT / ".github/workflows/native-hermes-pr.yml").read_text(
        encoding="utf-8"
    )
    assert workflow.count("scripts/build-native-runtime.py") == 1
    assert "ubuntu-24.04" in workflow
    assert "windows-latest" in workflow
    assert "macos-14" in workflow
    assert "native-base-platform-matrix" in workflow
    assert "native-lifecycle-contract" in workflow
    assert "native-candidate-required" in workflow
    assert "--wheelhouse dist/platform-wheelhouse" in workflow
    assert "--hermes-home" in workflow
    assert "--plugin-source hermes-plugin-wright" in workflow
    platform_matrix = workflow[
        workflow.index("native-base-platform-matrix:") : workflow.index(
            "native-lifecycle-contract:"
        )
    ]
    assert "--runtime-smoke" in platform_matrix
    assert "--base-only" not in platform_matrix
    assert "hermes-agent==0.19.0" in workflow
    lifecycle = workflow[workflow.index("native-lifecycle-contract:") :]
    assert '"mcp>=1.27.2,<2"' in lifecycle


def test_production_release_keeps_native_docker_docs_and_release_terminal() -> None:
    release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    assert "native-published-lifecycle" in release
    assert "verify-manager-adapters" in release
    assert "hermes-git-plugin-v1" in release
    assert "manager-adapter-evidence" in release
    assert "mirror-dockerhub" in release
    assert "deploy-versioned-docs" in release
    assert "publish-github-release-last" in release
    assert "Verify stable Hermes adapter install branch" in release
    assert "default_ref" in release
    assert "refs/heads/main" in release
    release_last = release[release.index("publish-github-release-last:") :]
    assert "native-published-lifecycle" in release_last
    assert "mirror-dockerhub" in release_last
    assert "deploy-versioned-docs" in release_last


def test_ordinary_python_and_windows_workflows_include_native_contracts() -> None:
    python = (ROOT / ".github/workflows/python-quality.yml").read_text(encoding="utf-8")
    windows = (ROOT / ".github/workflows/test-windows.yml").read_text(encoding="utf-8")
    assert "tests/native_runtime" in python
    assert "test_native_workflow_policy.py" in python
    assert "tests/native_runtime" in windows


def test_git_plugin_mirror_is_production_adapter_but_not_runtime_evidence() -> None:
    mirror = (ROOT / ".github/workflows/sync-hermes-plugin-mirror.yml").read_text(
        encoding="utf-8"
    )
    release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    assert "PRODUCTION_HERMES_ADAPTER" in mirror
    assert "does not replace" in mirror
    assert "hermes-plugin-wright" in release


def test_merge_gates_have_mandatory_native_acceptance_without_skip_flag() -> None:
    dev = (ROOT / "scripts/check-dev-merge.sh").read_text(encoding="utf-8")
    prod = (ROOT / "scripts/check-prod-merge.sh").read_text(encoding="utf-8")
    contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "tests/native_runtime" in dev
    assert "validate_native_distribution" in dev
    assert "require_released_git_plugin_interface" in prod
    assert "test_native_release_evidence.py" in prod
    assert "scripts/sync-hermes-plugin-mirror.sh" in prod
    assert "scripts/validate-hermes-plugin-mirror.sh" in prod
    assert "scripts/test-hermes-plugin-install.sh" in prod
    assert "scripts/test-hermes-plugin-update.sh" in prod
    assert "scripts/test-hermes-plugin-uninstall.sh" in prod
    assert "adapter_default_ref" in prod
    assert "refs/heads/main" in prod
    assert "default branch" in contributing
    assert "run make" not in prod
    assert "SKIP_NATIVE" not in dev + prod
    assert "no skip flag" in contributing


def test_docker_smoke_prefers_project_python_over_windows_store_alias() -> None:
    smoke = (ROOT / "scripts/docker-smoke-test.sh").read_text(encoding="utf-8")
    uv_python = "elif command -v uv"
    python3_fallback = "elif command -v python3"
    assert uv_python in smoke
    assert python3_fallback in smoke
    assert smoke.index(uv_python) < smoke.index(python3_fallback)
    assert "PYTHON_CMD=(uv run --no-sync python)" in smoke
