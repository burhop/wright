from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_release_workflow_marks_alpha_beta_rc_as_prereleases() -> None:
    workflow = read_text(".github/workflows/release.yml")

    assert "packages: write" in workflow
    assert "DOCKERHUB_USERNAME: ${{ secrets.DOCKERHUB_USERNAME }}" in workflow
    assert "DOCKERHUB_TOKEN: ${{ secrets.DOCKERHUB_TOKEN }}" in workflow
    assert "Classify Release Tag" in workflow
    assert "is_prerelease=$IS_PRERELEASE" in workflow
    assert "has_dockerhub=false" in workflow
    assert "-(alpha|beta|rc)" in workflow
    assert "prerelease: ${{ steps.tag.outputs.is_prerelease == 'true' }}" in workflow


def test_release_workflow_does_not_push_latest_for_prereleases() -> None:
    workflow = read_text(".github/workflows/release.yml")

    assert "if: ${{ env.DOCKERHUB_USERNAME != '' && env.DOCKERHUB_TOKEN != '' }}" in workflow
    assert "Log in to GHCR" in workflow
    assert "registry: ghcr.io" in workflow
    assert "password: ${{ secrets.GITHUB_TOKEN }}" in workflow
    assert "docker_tags<<EOF" in workflow
    assert "wright-agent:${TAG_NAME}" in workflow
    assert "ghcr.io/${GHCR_OWNER_LC}/wright-agent:${TAG_NAME}" in workflow
    assert 'if [[ "$HAS_DOCKERHUB" == "true" ]]; then' in workflow
    assert 'if [[ "$IS_PRERELEASE" != "true" ]]; then' in workflow
    assert "wright-agent:latest" in workflow
    assert "ghcr.io/${GHCR_OWNER_LC}/wright-agent:latest" in workflow
    assert "tags: ${{ steps.tag.outputs.docker_tags }}" in workflow
    assert "if: ${{ steps.tag.outputs.has_dockerhub == 'true' }}" in workflow


def test_versioning_documents_alpha_tag_and_latest_policy() -> None:
    versioning = read_text("docs/versioning.md")
    versioning_squashed = " ".join(versioning.split())

    for expected in [
        "v0.1.0-alpha.1",
        "v0.1.0-beta.1",
        "v0.1.0-rc.1",
        "Prerelease tags containing `-alpha`, `-beta`, or `-rc` do not update `latest`.",
        "marked as GitHub prereleases",
        "always pushed to GHCR",
        "pushed to Docker Hub when `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` are configured",
        "ghcr.io/burhop/wright-agent:<tag>",
        "<dockerhub-username>/wright-agent:<tag>` when Docker Hub credentials are configured",
        "bring-your-own-AI",
        "Docker smoke results",
        "skipped MCP validation",
    ]:
        assert expected in versioning_squashed
