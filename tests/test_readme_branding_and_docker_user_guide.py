from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def squashed(relative_path: str) -> str:
    return " ".join(read_text(relative_path).split())


def test_readme_branding_brief_matches_public_alpha_contract() -> None:
    brief = squashed("docs/community-features/012-readme-branding.md")

    for expected in [
        "Wright is alpha software",
        "bring-your-own-AI",
        "does not bundle an LLM",
        "docker compose -f docker-compose.minimal.yml up -d --build",
        "http://localhost:8080",
        "GHCR is the default registry path",
        "Docker Hub remains optional",
        "MCP-specific host software",
        "docs/mcp-catalog/mcp-server-testing-process.md",
    ]:
        assert expected in brief

    for stale in [
        "make docker-build && docker compose up",
        "100% Local",
        "No Cloud Required",
        "full-stack appliance",
        "converts visitors into users and contributors within 30 seconds",
    ]:
        assert stale not in brief


def test_docker_user_guide_matches_current_appliance_filesystem_contract() -> None:
    guide = squashed("docs/user-guide/docker.md")

    for expected in [
        "public-alpha Docker appliance",
        "does not bundle an LLM",
        "docker-compose.minimal.yml",
        "127.0.0.1:8080:8000",
        "http://localhost:8080",
        "host.docker.internal",
        "wright_home",
        "docker compose -f docker-compose.minimal.yml down -v",
        "MCP-specific host software",
        "do not add MCP-specific host software to the base image",
        "docs/mcp-catalog/mcp-server-testing-process.md",
    ]:
        assert expected in guide

    guide_lower = guide.lower()
    for stale in [
        "Thick Base / Thin Code",
        "Dockerfile.base",
        "standalone engineering AI-in-a-box",
        "bundled LLM",
        "production-ready",
    ]:
        assert stale.lower() not in guide_lower


def test_spec_tasks_record_readme_branding_and_docker_user_guide_slice() -> None:
    tasks = read_text("specs/035-alpha-release-readiness/tasks.md")

    for expected in [
        "Phase 18: README Branding and Docker User Guide Truth Check",
        "[X] T067 Refresh README branding feature brief",
        "[X] T068 Refresh Docker user guide",
        "[X] T069 Remove stale thick-base and one-command Docker launch guidance",
        "[X] T070 Add regression tests for README branding and Docker user guide docs",
    ]:
        assert expected in tasks
