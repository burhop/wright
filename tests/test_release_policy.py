from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_release_workflow_marks_alpha_beta_rc_as_prereleases() -> None:
    workflow = read_text(".github/workflows/release.yml")

    assert "Classify Release Tag" in workflow
    assert "is_prerelease=$IS_PRERELEASE" in workflow
    assert "-(alpha|beta|rc)" in workflow
    assert "prerelease: ${{ steps.tag.outputs.is_prerelease == 'true' }}" in workflow


def test_release_workflow_does_not_push_latest_for_prereleases() -> None:
    workflow = read_text(".github/workflows/release.yml")

    assert "docker_tags<<EOF" in workflow
    assert "wright-agent:${TAG_NAME}" in workflow
    assert 'if [[ "$IS_PRERELEASE" != "true" ]]; then' in workflow
    assert "wright-agent:latest" in workflow
    assert "tags: ${{ steps.tag.outputs.docker_tags }}" in workflow


def test_versioning_documents_alpha_tag_and_latest_policy() -> None:
    versioning = read_text("docs/versioning.md")
    versioning_squashed = " ".join(versioning.split())

    for expected in [
        "v0.1.0-alpha.1",
        "v0.1.0-beta.1",
        "v0.1.0-rc.1",
        "Prerelease tags containing `-alpha`, `-beta`, or `-rc` do not update `latest`.",
        "marked as GitHub prereleases",
        "bring-your-own-AI",
        "Docker smoke results",
        "skipped MCP validation",
    ]:
        assert expected in versioning_squashed
