from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def squashed(relative_path: str) -> str:
    return " ".join(read_text(relative_path).split())


def test_ci_cd_docs_list_current_workflows_and_pr_gates() -> None:
    docs = squashed("docs/contributing/ci-cd-workflows.md")
    mkdocs = read_text("mkdocs.yml")

    for expected in [
        "python-quality.yml",
        "frontend-quality.yml",
        "public-alpha-safety.yml",
        "docker-build.yml",
        "docs-deploy.yml",
        "release.yml",
        "release-drafter.yml",
        "test-windows.yml",
        "uv sync --all-packages --all-groups",
        "uv run pytest",
        "npm run test --workspace=apps/web",
        "npm run build --workspace=apps/web",
        "mkdocs build --strict",
        "python scripts/check-public-alpha-leaks.py",
    ]:
        assert expected in docs

    assert "CI/CD Workflows: contributing/ci-cd-workflows.md" in mkdocs


def test_ci_cd_docs_match_docker_smoke_and_docs_release_contracts() -> None:
    docs = squashed("docs/contributing/ci-cd-workflows.md")

    for expected in [
        "does not publish public images",
        "wright-agent:<sha>",
        "placeholder `LLM_API_URL`, `LLM_API_KEY`, and `LLM_API_MODEL`",
        "`wright-api` and `hermes-gateway`",
        "Trivy",
        "exit code `0`",
        "docs workflow builds strictly on pull requests",
        "deploys GitHub Pages only for non-PR `main` builds",
    ]:
        assert expected in docs

    assert "hermes-webui" not in docs
    assert "pushes the image to Docker Hub with the `dev` tag" not in docs
    assert "pushes the image to Docker Hub with both the `latest`" not in docs


def test_ci_cd_docs_describe_ghcr_default_and_optional_docker_hub() -> None:
    docs = squashed("docs/contributing/ci-cd-workflows.md")
    release = read_text(".github/workflows/release.yml")

    for expected in [
        "GHCR as the default registry path",
        "ghcr.io/<owner>/wright-agent:<tag>",
        "`packages: write`",
        "Docker Hub publishing is optional",
        "`DOCKERHUB_USERNAME`",
        "`DOCKERHUB_TOKEN`",
        "marked as GitHub prereleases",
        "Stable tags update `latest`; prerelease tags do not update `latest`.",
        "docs/alpha-release-notes-template.md",
    ]:
        assert expected in docs

    assert "packages: write" in release
    assert "Log in to GHCR" in release
    assert "has_dockerhub=false" in release


def test_spec_tasks_record_ci_cd_docs_refresh_slice() -> None:
    tasks = read_text("specs/035-alpha-release-readiness/tasks.md")

    for expected in [
        "Phase 13: CI/CD Guide Refresh",
        "[X] T052 Refresh CI/CD workflow guide",
        "[X] T053 Document GHCR default, optional Docker Hub, and prerelease latest policy",
        "[X] T054 Add regression tests for CI/CD workflow docs",
    ]:
        assert expected in tasks
