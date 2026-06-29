from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_docs_workflow_builds_strictly_on_pull_requests() -> None:
    workflow = read_text(".github/workflows/docs-deploy.yml")

    assert "pull_request:" in workflow
    assert "- main" in workflow
    assert "- dev" in workflow
    assert "mkdocs build --strict" in workflow
    assert "needs: build" in workflow
    assert "github.event_name != 'pull_request'" in workflow
    assert "github.ref == 'refs/heads/main'" in workflow


def test_public_launch_checklist_covers_release_blockers() -> None:
    checklist = read_text("docs/public-launch-checklist.md")
    checklist_lower = checklist.lower()

    for expected in [
        "working-tree secret scan",
        "history secret scan",
        "gitleaks",
        "trufflehog",
        "uv run pytest",
        "npm run test --workspace=apps/web",
        "npm run build --workspace=apps/web",
        "mkdocs build --strict",
        "Docker appliance smoke test",
        "GHCR",
        "Docker Hub",
        "packages: write",
        "Docker Hub credentials",
        "linux/amd64",
        "linux/arm64",
        "bring-your-own-AI",
        "MCP-specific host software",
        "marked prerelease",
    ]:
        assert expected in checklist

    assert "branch protection" in checklist_lower


def test_launch_checklist_is_published_and_release_gate_is_documented() -> None:
    mkdocs = read_text("mkdocs.yml")
    testing = read_text("docs/contributing/testing.md")

    assert "Public Launch Checklist: public-launch-checklist.md" in mkdocs
    assert "uv run --with mkdocs-material mkdocs build --strict" in testing


def test_docs_links_that_broke_strict_build_are_no_longer_doc_relative() -> None:
    deployment = read_text("docs/deployment-configurations.md")
    plan = read_text("docs/wright-hermes-plugin-plan.md")
    blog = read_text("docs/blog/introducing-wright.md")

    for stale_link in [
        "(../apps/api/src/api/main.py)",
        "(../docker/entrypoint.sh)",
        "(../hermes-plugin-wright/pyproject.toml)",
        "(../hermes-plugin-wright/commands.py)",
    ]:
        assert stale_link not in deployment

    assert "(../specs/026-mcp-credential-setup/plan.md)" not in plan
    assert "(CONTRIBUTING.md)" not in blog
    assert "https://github.com/burhop/wright/blob/main" in deployment
    assert "https://github.com/burhop/wright/blob/main" in plan
    assert "https://github.com/burhop/wright/blob/main/CONTRIBUTING.md" in blog
