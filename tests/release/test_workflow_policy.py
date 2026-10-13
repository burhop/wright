from pathlib import Path

import pytest

from scripts.release.workflow_policy import (
    WorkflowPolicyError,
    validate_checkout_readiness,
    validate_scoped_workflows,
)


ROOT = Path(__file__).resolve().parents[2]


def test_all_workflow_actions_are_pinned_to_full_commit_shas() -> None:
    validate_scoped_workflows(ROOT)


BOOTSTRAP = (
    "      - name: Enable long Git paths on Windows\n"
    "        if: runner.os == 'Windows'\n"
    "        shell: pwsh\n"
    "        run: git config --global core.longpaths true\n"
)
CHECKOUT = "      - uses: actions/checkout@" + "a" * 40 + "\n"


@pytest.mark.parametrize("runner", ["windows-latest", "${{ matrix.os }}"])
@pytest.mark.parametrize("late", [False, True])
def test_windows_checkout_rejects_absent_or_late_setup(tmp_path, runner, late):
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "jobs:\n  test:\n    strategy:\n      matrix:\n        os: [ubuntu-latest, windows-latest]\n"
        f"    runs-on: {runner}\n    steps:\n" + CHECKOUT + (BOOTSTRAP if late else ""),
        encoding="utf-8",
    )
    with pytest.raises(WorkflowPolicyError, match="before Windows checkout"):
        validate_checkout_readiness(workflow)


def test_matrix_setup_is_checked_per_job_not_borrowed_from_another_job(tmp_path):
    workflow = tmp_path / "workflow.yml"
    ready = "  ready:\n    runs-on: windows-latest\n    steps:\n" + BOOTSTRAP + CHECKOUT
    unready = "  unready:\n    runs-on: windows-latest\n    steps:\n" + CHECKOUT
    workflow.write_text("jobs:\n" + ready, encoding="utf-8")
    validate_checkout_readiness(workflow)
    workflow.write_text("jobs:\n" + ready + unready, encoding="utf-8")
    with pytest.raises(WorkflowPolicyError, match="unready"):
        validate_checkout_readiness(workflow)


def test_backend_python_dependencies_do_not_establish_compiler_readiness(tmp_path):
    workflow = tmp_path / "workflow.yml"
    workflow.write_text(
        "jobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n"
        + CHECKOUT
        + "      - name: Install Python dependencies\n        run: uv sync --all-packages --all-groups\n"
        + "      - name: Run Tests with pytest\n        run: uv run pytest packages/workspace_service/tests\n",
        encoding="utf-8",
    )
    with pytest.raises(WorkflowPolicyError, match="compiler readiness"):
        validate_checkout_readiness(workflow)


def test_release_builds_each_subject_once_and_publishes_release_last() -> None:
    release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    docker = (ROOT / ".github/workflows/docker-build.yml").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    prod_gate = (ROOT / "scripts/check-prod-merge.sh").read_text(encoding="utf-8")
    assert release.count("scripts/build-python-distributions.sh") == 1
    assert "check-wheel-contents==0.6.3" in release
    assert "check-wheel-contents==0.6.3" in prod_gate
    assert "[tool.check-wheel-contents]\n" in pyproject
    assert 'ignore = ["W009"]' in pyproject
    assert docker.count("docker/build-push-action@") == 1
    assert "docker/build-push-action@" not in release
    assert "Publish GitHub Release only after every verification" in release
    assert (
        "needs: [preflight-and-python-build, post-publish-verification, native-published-lifecycle, mirror-dockerhub, deploy-versioned-docs]"
        in release
    )
    assert "engineering-tools-image-family:" in release
    assert "uses: ./.github/workflows/docker-image-family.yml" in release
    assert "engineering-tools-image-family, verify-pypi" in release
    assert "uses: ./.github/workflows/docs-deploy.yml" in release
    assert "TestPyPI" in release
    assert release.index("publish-testpypi:") < release.index("publish-pypi:")


def test_release_rehearsal_has_no_publish_jobs() -> None:
    release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    assert "rehearsal != 'true'" in release
    assert "Prove terminal dry-run with no public mutation" in release
    assert release.count("uses: astral-sh/setup-uv@") == 2
    assert release.count('version: "0.9.26"') >= 2


def test_production_release_requires_and_verifies_docker_hub() -> None:
    release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")

    assert "Require Docker Hub release credentials" in release
    assert "DOCKERHUB_USERNAME is required for every production release" in release
    assert "DOCKERHUB_TOKEN is required for every production release" in release
    assert "must contain the raw one-time dckr_pat_ value" in release
    assert "Classify optional mirror" not in release
    assert "configured=false" not in release
    assert "Copy and verify the same manifest in Docker Hub" in release
    assert 'docker buildx imagetools create --tag "$DEST_LATEST" "$SOURCE"' in release
    assert "Independently verify required public Docker Hub tags" in release
    assert '--promotion-destination "docker.io/${{ env.DOCKERHUB_IMAGE }}"' in release
    assert "--approval dockerhub" in release


def test_docker_hub_recovery_never_rebuilds_or_republishes_python() -> None:
    recovery = (ROOT / ".github/workflows/recover-dockerhub-release.yml").read_text(
        encoding="utf-8"
    )

    assert "environment: dockerhub" in recovery
    assert "Run Docker Hub recovery only from the reviewed main branch" in recovery
    assert "scripts/validate-dockerhub-recovery.py" in recovery
    assert "gh release download" in recovery
    assert "docker buildx imagetools create" in recovery
    assert "dockerhub-recovery-${TAG#v}-${GITHUB_RUN_ID}.json" in recovery
    assert "retention-days: 90" in recovery
    assert "Expected finalized GitHub Release $TAG to be immutable" in recovery
    assert "The finalized GitHub Release is immutable" in recovery
    assert "gh release upload" not in recovery
    assert "docker/build-push-action@" not in recovery
    assert "gh-action-pypi-publish@" not in recovery
