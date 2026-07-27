from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_release_workflow_marks_alpha_beta_rc_as_prereleases() -> None:
    workflow = read_text(".github/workflows/release.yml")

    assert "packages: write" in workflow
    assert "environment: release" in workflow
    assert "environment: dockerhub" in workflow
    assert "rehearsal=$REHEARSAL" in workflow
    assert "-(alpha|beta|rc)" in workflow
    assert (
        "prerelease: ${{ needs.preflight-and-python-build.outputs.prerelease == 'true' }}"
        in workflow
    )
    assert "Publish GitHub Release only after every verification" in workflow


def test_release_workflow_does_not_push_latest_for_prereleases() -> None:
    workflow = read_text(".github/workflows/release.yml")

    assert "Promote tested digest without rebuilding" in workflow
    assert 'if [[ "$PRERELEASE" != true ]]; then' in workflow
    assert (
        'docker buildx imagetools create --tag "$IMAGE:latest" "$IMAGE@$DIGEST"'
        in workflow
    )
    assert "Copy and verify the same manifest" in workflow
    assert 'docker buildx imagetools create --tag "$DEST" "$SOURCE"' in workflow
    assert "docker/build-push-action@" not in workflow


def test_versioning_documents_alpha_tag_and_latest_policy() -> None:
    versioning = read_text("docs/versioning.md")
    versioning_squashed = " ".join(versioning.split())

    for expected in [
        "v0.1.0-alpha.1",
        "v0.1.0-beta.1",
        "v0.1.0-rc.1",
        "Prerelease tags containing `-alpha`, `-beta`, or `-rc` do not update `latest`.",
        "GitHub Release, which is published last",
        "tested OCI digest is promoted in GHCR",
        "optionally copied byte-identically to Docker Hub",
        "ghcr.io/burhop/wright:<tag>",
        "burhop/wright:<tag>` when Docker Hub credentials are configured",
        "bring-your-own-AI",
        "Docker smoke results",
        "SBOM/provenance status",
        "skipped MCP validation",
        "docs/alpha-release-notes-template.md",
        "rehearsal or static workflow check is not a successful production release",
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
