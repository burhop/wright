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
    assert "wright:${TAG_NAME}" in workflow
    assert "ghcr.io/${GHCR_OWNER_LC}/wright:${TAG_NAME}" in workflow
    assert 'if [[ "$HAS_DOCKERHUB" == "true" ]]; then' in workflow
    assert 'if [[ "$IS_PRERELEASE" != "true" ]]; then' in workflow
    assert "wright:latest" in workflow
    assert "ghcr.io/${GHCR_OWNER_LC}/wright:latest" in workflow
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
        "ghcr.io/burhop/wright:<tag>",
        "burhop/wright:<tag>` when Docker Hub credentials are configured",
        "bring-your-own-AI",
        "Docker smoke results",
        "SBOM/provenance status",
        "skipped MCP validation",
        "docs/alpha-release-notes-template.md",
    ]:
        assert expected in versioning_squashed


def test_alpha_release_notes_template_requires_manual_gate_status() -> None:
    template = read_text("docs/alpha-release-notes-template.md")
    template_squashed = " ".join(template.split())
    checklist = read_text("docs/public-launch-checklist.md")
    mkdocs = read_text("mkdocs.yml")

    for expected in [
        "Wright is bring-your-own-AI",
        "does not bundle an LLM",
        "GHCR: `ghcr.io/burhop/wright:<tag>`",
        "Docker Hub: `burhop/wright:<tag>`",
        "`latest` updated: `yes` for stable tags only",
        "Docker appliance smoke test",
        "History secret scan",
        "SBOM/provenance",
        "deferred for this alpha",
        "`linux/amd64`",
        "`linux/arm64`",
        "NVIDIA Container Toolkit / `--gpus all`",
        "Skipped MCP validation",
        "docs/mcp-catalog/mcp-server-testing-process.md",
        "Hermes Desktop Linux container images",
    ]:
        assert expected in template_squashed

    assert "docs/alpha-release-notes-template.md" in checklist
    assert "Alpha Release Notes Template: alpha-release-notes-template.md" in mkdocs
