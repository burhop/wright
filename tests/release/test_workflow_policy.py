from pathlib import Path

from scripts.release.workflow_policy import validate_scoped_workflows


ROOT = Path(__file__).resolve().parents[2]


def test_all_workflow_actions_are_pinned_to_full_commit_shas() -> None:
    validate_scoped_workflows(ROOT)


def test_release_builds_each_subject_once_and_publishes_release_last() -> None:
    release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    python_publish = (ROOT / ".github/workflows/publish-python-packages.yml").read_text(
        encoding="utf-8"
    )
    docker = (ROOT / ".github/workflows/docker-build.yml").read_text(encoding="utf-8")
    assert release.count("scripts/build-python-distributions.sh") == 1
    assert "scripts/build-python-distributions.sh" not in python_publish
    assert docker.count("docker/build-push-action@") == 1
    assert "docker/build-push-action@" not in release
    assert "Publish GitHub Release only after every verification" in release
    assert (
        "needs: [preflight-and-python-build, post-publish-verification, deploy-versioned-docs]"
        in release
    )
    assert "uses: ./.github/workflows/docs-deploy.yml" in release
    assert "TestPyPI" in python_publish
    assert python_publish.index("publish-testpypi:") < python_publish.index(
        "publish-pypi:"
    )


def test_release_rehearsal_has_no_publish_jobs() -> None:
    release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    assert "rehearsal != 'true'" in release
    assert "Prove terminal dry-run with no public mutation" in release
