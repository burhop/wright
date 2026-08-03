from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]


def test_production_dockerfile_uses_pinned_architecture_inputs() -> None:
    dockerfile = (ROOT / "docker/Dockerfile").read_text(encoding="utf-8")
    from_lines = [line for line in dockerfile.splitlines() if line.startswith("FROM ")]
    assert from_lines
    for line in from_lines:
        if line != "FROM hermes-base":
            assert "@sha256:" in line, line
    assert "node:26.5.1-slim@sha256:" in dockerfile
    assert "python:3.13.13-slim@sha256:" in dockerfile
    assert "uv:0.9.26@sha256:" in dockerfile
    assert "micromamba_arch=\"linux-64\"" in dockerfile
    assert "micromamba_arch=\"linux-aarch64\"" in dockerfile
    assert re.search(r"ARG MICROMAMBA_AMD64_SHA256=[0-9a-f]{64}", dockerfile)
    assert re.search(r"ARG MICROMAMBA_ARM64_SHA256=[0-9a-f]{64}", dockerfile)
    assert "sha256sum --check --strict" in dockerfile
    assert "apt-get upgrade" not in dockerfile
    assert ":latest" not in "\n".join(from_lines)


def test_oci_workflow_scans_smokes_and_attests_same_digest_without_rebuild() -> None:
    workflow = (ROOT / ".github/workflows/docker-build.yml").read_text(encoding="utf-8")
    release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    assert workflow.count("docker/build-push-action@") == 1
    assert "load: ${{ ! inputs.push-candidate }}" in workflow
    assert (
        "provenance: ${{ inputs.push-candidate && 'mode=max' || 'false' }}" in workflow
    )
    assert "sbom: ${{ inputs.push-candidate }}" in workflow
    assert "WRIGHT_DOCKER_SKIP_BUILD=1" in workflow
    assert "steps.build.outputs.digest" in workflow
    assert "evaluate_report" in workflow
    assert "subject-digest: ${{ steps.build.outputs.digest }}" in workflow
    assert "docker/build-push-action@" not in release
    assert (
        'docker buildx imagetools create --tag "$IMAGE:$TAG" "$IMAGE@$DIGEST"'
        in release
    )
    assert 'docker buildx imagetools create --tag "$DEST_VERSION" "$SOURCE"' in release
