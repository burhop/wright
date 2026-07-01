from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def squashed(relative_path: str) -> str:
    return " ".join(read_text(relative_path).split())


def test_readme_front_loads_alpha_and_byo_ai_contract() -> None:
    readme = squashed("README.md").lower()

    assert "wright is alpha software" in readme
    assert "bring-your-own-ai" in readme
    assert "do not bundle an llm" in readme
    assert "mcp-specific host software" in readme
    assert "docker compose -f docker-compose.minimal.yml up -d --build" in readme
    assert "http://localhost:8080" in readme
    assert "bundled docker stack that includes standard open-source tools" not in readme
    assert "file://" not in read_text("README.md")


def test_docker_quickstart_documents_current_alpha_paths() -> None:
    quickstart = squashed("docs/getting-started/quickstart-docker.md")

    assert "docker compose -f docker-compose.minimal.yml up -d --build" in quickstart
    assert "http://localhost:8080" in quickstart
    assert "docker compose up -d --build" in quickstart
    assert "http://localhost:8000" in quickstart
    assert "host.docker.internal" in quickstart
    assert "0.0.0.0:8080:8000" in quickstart
    assert "linux/amd64" in quickstart
    assert "does not bundle MCP-specific host software" in quickstart
    assert "mcp-server-testing-process.md" in quickstart


def test_alpha_bug_template_collects_actionable_context() -> None:
    template = read_text(".github/ISSUE_TEMPLATE/bug_report.yml")
    config = read_text(".github/ISSUE_TEMPLATE/config.yml")

    for expected in [
        'labels: ["bug", "needs-triage", "alpha"]',
        "id: deployment-path",
        "id: image-tag-version",
        "id: commit-sha",
        "id: operating-system",
        "id: docker-version",
        "id: browser",
        "id: llm-provider-model",
        "id: hermes-version",
        "id: mcp-server",
        "id: logs",
        "id: screenshots",
        "I removed API keys",
    ]:
        assert expected in template

    assert "blank_issues_enabled: true" in config


def test_alpha_bug_template_commit_sha_is_optional() -> None:
    template = read_text(".github/ISSUE_TEMPLATE/bug_report.yml")
    commit_sha_block = template.split("id: commit-sha", 1)[1].split("  - type:", 1)[0]

    assert "label: Commit SHA" in commit_sha_block
    assert "required: false" in commit_sha_block
    assert "required: true" not in commit_sha_block


def test_pr_template_does_not_require_spec_kit_for_every_pr() -> None:
    template = read_text(".github/PULL_REQUEST_TEMPLATE.md")
    contributing = read_text("CONTRIBUTING.md")

    assert "Spec Kit artifacts" not in template
    assert "Feature changes should follow" in contributing
    assert (
        "Routine bug fixes, documentation edits, test-only changes, and CI maintenance"
        in contributing
    )


def test_dependabot_covers_root_and_frontend_npm_lockfiles() -> None:
    config = read_text(".github/dependabot.yml")

    assert 'package-ecosystem: "npm"\n    directory: "/"' in config
    assert 'package-ecosystem: "npm"\n    directory: "/apps/web"' in config


def test_windows_workflow_keeps_platform_checks_without_e2e_server_loop() -> None:
    workflow = read_text(".github/workflows/test-windows.yml")

    assert "Backend Tests (Windows)" in workflow
    assert "Frontend Tests (Windows)" in workflow
    assert "Playwright E2E (Windows)" not in workflow
    assert "Start backend server" not in workflow
    assert "curl.exe" not in workflow


def test_frontend_quality_runs_linux_playwright_e2e() -> None:
    workflow = read_text(".github/workflows/frontend-quality.yml")

    assert "playwright-e2e:" in workflow
    assert "runs-on: ubuntu-latest" in workflow
    assert "uv run uvicorn api.main:app" in workflow
    assert "http://127.0.0.1:8000/api/health" in workflow
    assert "npx playwright test" in workflow
    assert "Backend process exited before becoming ready" in workflow


def test_ci_runs_frontend_tests_build_and_correct_docker_smoke_process() -> None:
    frontend = read_text(".github/workflows/frontend-quality.yml")
    docker = read_text(".github/workflows/docker-build.yml")

    assert "npm run test --workspace=apps/web" in frontend
    assert "npm run build --workspace=apps/web" in frontend
    assert "hermes-gateway.*RUNNING" in docker
    assert "hermes-webui.*RUNNING" not in docker


def test_public_docker_docs_match_gateway_contract() -> None:
    dockerfile = read_text("docker/Dockerfile")
    docker_hub = squashed("docker/DOCKER_HUB_README.md")

    assert "Hermes gateway on :8642 internal" in dockerfile
    assert "bring-your-own-AI" in docker_hub
    assert "does not bundle MCP-specific host software" in docker_hub
    assert "ghcr.io/burhop/wright-agent:<tag>" in docker_hub
    assert "<dockerhub-username>/wright-agent:<tag>" in docker_hub
    assert "do not move `latest`" in docker_hub
    assert "Internal only" in docker_hub
    assert "`8642`" in docker_hub
