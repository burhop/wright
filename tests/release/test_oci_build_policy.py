from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]


def test_production_dockerfile_uses_pinned_amd64_inputs() -> None:
    dockerfile = (ROOT / "docker/Dockerfile").read_text(encoding="utf-8")
    from_lines = [line for line in dockerfile.splitlines() if line.startswith("FROM ")]
    assert from_lines
    for line in from_lines:
        if line != "FROM hermes-base":
            assert "@sha256:" in line, line
    assert "node:24.17.0-slim@sha256:" in dockerfile
    assert "python:3.13.11-slim@sha256:" in dockerfile
    assert "uv:0.9.26@sha256:" in dockerfile
    assert "/micromamba/linux-64/${MICROMAMBA_VERSION}" in dockerfile
    assert re.search(r"ARG MICROMAMBA_SHA256=[0-9a-f]{64}", dockerfile)
    assert "sha256sum --check --strict" in dockerfile
    assert 'test "${TARGETARCH:-amd64}" = "amd64"' in dockerfile
    assert "apt-get upgrade" not in dockerfile
    assert ":latest" not in "\n".join(from_lines)


def test_oci_workflow_scans_smokes_and_attests_same_digest_without_rebuild() -> None:
    workflow = (ROOT / ".github/workflows/docker-build.yml").read_text(encoding="utf-8")
    release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    assert workflow.count("docker/build-push-action@") == 1
    assert "WRIGHT_DOCKER_SKIP_BUILD=1" in workflow
    assert "steps.build.outputs.digest" in workflow
    assert "evaluate_report" in workflow
    assert "subject-digest: ${{ steps.build.outputs.digest }}" in workflow
    assert "docker/build-push-action@" not in release
    assert (
        'docker buildx imagetools create --tag "$IMAGE:$TAG" "$IMAGE@$DIGEST"'
        in release
    )
    assert 'docker buildx imagetools create --tag "$DEST" "$SOURCE"' in release
