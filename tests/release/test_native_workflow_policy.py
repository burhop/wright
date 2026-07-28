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


def test_production_release_keeps_native_docker_docs_and_release_terminal() -> None:
    release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    assert "native-published-lifecycle" in release
    assert "activate-stable-hermes-channel" in release
    assert "mirror-dockerhub" in release
    assert "deploy-versioned-docs" in release
    assert "publish-github-release-last" in release
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


def test_git_plugin_mirror_is_explicitly_legacy_and_not_release_evidence() -> None:
    mirror = (ROOT / ".github/workflows/sync-hermes-plugin-mirror.yml").read_text(
        encoding="utf-8"
    )
    release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    assert "LEGACY_MIGRATION_ONLY" in mirror
    assert "never native release evidence" in mirror
    assert "sync-hermes-plugin-mirror" not in release


def test_merge_gates_have_mandatory_native_acceptance_without_skip_flag() -> None:
    dev = (ROOT / "scripts/check-dev-merge.sh").read_text(encoding="utf-8")
    prod = (ROOT / "scripts/check-prod-merge.sh").read_text(encoding="utf-8")
    contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "tests/native_runtime" in dev
    assert "validate_native_distribution" in dev
    assert "require_released_package_capability" in prod
    assert "test_native_release_evidence.py" in prod
    assert "SKIP_NATIVE" not in dev + prod
    assert "no skip flag" in contributing
