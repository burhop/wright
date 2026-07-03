from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def squashed(relative_path: str) -> str:
    return " ".join(read_text(relative_path).split())


def assert_no_stale_appliance_claims(text: str) -> None:
    normalized = text.lower()
    for stale in [
        "engineering ai-in-a-box",
        "standalone engineering ai-in-a-box",
        "thick base / thin code",
        "dockerfile.base",
        "complete, standalone",
        "100% offline security",
        "100% reliability",
        "local workspace, data vault, and logs",
    ]:
        assert stale not in normalized


def test_docs_homepage_front_loads_alpha_byo_ai_contract() -> None:
    home = squashed("docs/index.md")

    for expected in [
        "Wright is alpha software",
        "bring-your-own-AI",
        "does not bundle an LLM",
        "docker-compose.minimal.yml",
        "http://localhost:8080",
        "selected MCP host software",
        "docs/mcp-catalog/mcp-server-testing-process.md",
    ]:
        assert expected in home

    assert_no_stale_appliance_claims(home)


def test_readme_uses_current_workspace_artifact_surface() -> None:
    readme = squashed("README.md")

    for expected in [
        "Workspace Artifacts",
        "workspace volume or checkout you control",
        "SQLite and local workspace files",
        "Placeholder package for future storage extraction",
    ]:
        assert expected in readme

    for stale in [
        "### File Vault",
        "screenshot_file_vault.png",
        "SQLite, LanceDB, File Vault",
        "SQLite, LanceDB, and filesystem vault",
    ]:
        assert stale not in readme


def test_getting_started_overview_uses_supported_alpha_paths() -> None:
    overview = squashed("docs/getting-started/overview.md")

    for expected in [
        "Wright is alpha software and bring-your-own-AI",
        "does not bundle an LLM",
        "Choose Your Alpha Path",
        "Docker appliance",
        "PC local setup",
        "GB10/DGX workstation",
        "Existing Hermes plugin",
        "selected MCP host dependencies",
        "MCP-specific host software",
    ]:
        assert expected in overview

    assert_no_stale_appliance_claims(overview)


def test_technical_analysis_matches_current_container_and_ai_boundaries() -> None:
    analysis = squashed("docs/technical_analysis.md")

    for expected in [
        "public-alpha",
        "bring-your-own-AI",
        "Docker image does not bundle an LLM",
        "selected MCP host dependencies",
        "docker-compose.minimal.yml",
        "http://localhost:8080",
        "docs/mcp-catalog/mcp-server-testing-process.md",
    ]:
        assert expected in analysis

    assert_no_stale_appliance_claims(analysis)


def test_spec_tasks_record_docs_home_overview_alpha_slice() -> None:
    tasks = read_text("specs/035-alpha-release-readiness/tasks.md")

    for expected in [
        "Phase 19: Docs Home and Overview Alpha Contract",
        "[X] T071 Refresh docs homepage",
        "[X] T072 Refresh getting-started overview",
        "[X] T073 Refresh technical analysis container strategy",
        "[X] T074 Remove stale engineering AI-in-a-box and thick-base claims",
        "[X] T075 Add regression tests for docs home and overview alpha contract",
    ]:
        assert expected in tasks
