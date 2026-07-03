from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def squashed(relative_path: str) -> str:
    return " ".join(read_text(relative_path).split())


def test_release_engineering_brief_matches_alpha_release_policy() -> None:
    brief = squashed("docs/community-features/015-release-engineering.md")

    for expected in [
        "public alpha",
        "not imply production readiness",
        "v0.1.0-alpha.1",
        "docs/alpha-release-notes-template.md",
        "ghcr.io/<owner>/wright:<tag>",
        "burhop/wright:<tag>",
        "Docker Hub publishing must remain optional",
        "latest is stable-only",
        "bring-your-own-AI",
        "MCP-specific host software",
    ]:
        assert expected in brief

    for stale in [
        "production-ready",
        "Push the versioned Docker image to Docker Hub",
        "burhop/wright:vX.Y.Z",
        "burhop/wright:latest",
        "On `dev` push: tag as `burhop/wright:dev`",
    ]:
        assert stale not in brief


def test_docker_distribution_brief_matches_registry_and_dependency_policy() -> None:
    brief = squashed("docs/community-features/017-docker-distribution.md")

    for expected in [
        "GHCR is the default registry path",
        "Docker Hub remains optional",
        "ghcr.io/burhop/wright:<tag>",
        "burhop/wright:<tag>",
        "docker-compose.minimal.yml",
        "http://localhost:8080",
        "Hermes gateway port `8642` stays internal",
        "Trivy",
        "exit-code: '0'",
        "linux/amd64",
        "linux/arm64",
        "NVIDIA Container Toolkit",
        "--gpus all",
        "Do not add MCP-specific host software to the base image",
        "Prerelease tags must not move `latest`",
    ]:
        assert expected in brief

    for stale in [
        "meets the standards of well-maintained Docker Hub projects",
        "Port reference (8080 external, 8000 internal API, 8788 internal agent)",
        "Docker Hub vulnerability scanning",
        "current target is amd64-only (Dell DGX Spark)",
        "OpenSCAD, CUDA in future",
    ]:
        assert stale not in brief


def test_spec_tasks_record_community_feature_docs_slice() -> None:
    tasks = read_text("specs/035-alpha-release-readiness/tasks.md")

    for expected in [
        "Phase 15: Community Feature Brief Truth Check",
        "[X] T058 Refresh release-engineering community feature brief",
        "[X] T059 Refresh Docker distribution community feature brief",
        "[X] T060 Add regression tests for community feature briefs",
    ]:
        assert expected in tasks
