from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def squashed(relative_path: str) -> str:
    return " ".join(read_text(relative_path).split())


def test_intro_blog_states_alpha_byo_ai_and_dependency_boundaries() -> None:
    blog = squashed("docs/blog/introducing-wright.md")

    for expected in [
        "public-alpha software and bring-your-own-AI",
        "does not bundle an LLM",
        "MCP-specific host software",
        "selected MCP servers",
        "clean-container process",
        "docs/mcp-catalog/mcp-server-testing-process.md",
        "does not preload every possible CAD, CAE, CAM",
    ]:
        assert expected in blog


def test_intro_blog_uses_current_docker_quickstart() -> None:
    blog = squashed("docs/blog/introducing-wright.md")

    for expected in [
        "cp docker/.env.example docker/.env",
        "LLM_API_URL",
        "LLM_API_KEY",
        "LLM_API_MODEL",
        "docker compose -f docker-compose.minimal.yml up -d --build",
        "http://localhost:8080",
        "host.docker.internal",
        "docs/getting-started/overview.md",
    ]:
        assert expected in blog

    for stale in [
        "make docker-build && docker compose up",
        "Edit docker/.env and set your API keys",
        "Wright guarantees",
        "mathematically sound and compile correctly",
        "full Wright stack",
    ]:
        assert stale not in blog


def test_spec_tasks_record_intro_blog_alpha_docs_slice() -> None:
    tasks = read_text("specs/035-alpha-release-readiness/tasks.md")

    for expected in [
        "Phase 17: Intro Blog Alpha Contract",
        "[X] T064 Refresh introductory blog alpha/BYO-AI language",
        "[X] T065 Update introductory blog Docker quickstart",
        "[X] T066 Add regression tests for introductory blog alpha docs",
    ]:
        assert expected in tasks
