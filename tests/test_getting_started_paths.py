from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def squashed(relative_path: str) -> str:
    return " ".join(read_text(relative_path).split())


def test_getting_started_nav_publishes_all_supported_alpha_paths() -> None:
    mkdocs = read_text("mkdocs.yml")
    overview = read_text("docs/getting-started/overview.md")

    for expected in [
        "Docker Appliance: getting-started/quickstart-docker.md",
        "PC Local Setup: getting-started/quickstart-local.md",
        "GB10 and DGX Workstations: getting-started/workstation-gb10-dgx.md",
        "Existing Hermes Plugin: getting-started/hermes-plugin.md",
        "[Quick Start: PC Local Setup](quickstart-local.md)",
        "[Quick Start: GB10 and DGX Workstations](workstation-gb10-dgx.md)",
        "[Quick Start: Existing Hermes Plugin](hermes-plugin.md)",
    ]:
        assert expected in mkdocs or expected in overview


def test_pc_local_quickstart_matches_current_workspace_commands() -> None:
    quickstart = squashed("docs/getting-started/quickstart-local.md")

    for expected in [
        "Wright is alpha software and bring-your-own-AI",
        "uv sync --all-packages --all-groups",
        "npm ci",
        "uv run uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload",
        "npm run dev --workspace=apps/web -- --host 127.0.0.1",
        "LLM_API_URL",
        "LLM_API_KEY",
        "LLM_API_MODEL",
        "uv run --with mkdocs-material mkdocs build --strict",
        "tests/test_getting_started_paths.py",
        "MCP server testing process",
    ]:
        assert expected in quickstart

    for stale in [
        "generativelanguage.googleapis.com",
        "gemini-3.5-flash",
        "source .venv/bin/activate",
        "uvicorn apps.api.main:app",
        "npm install",
        "npm run dev The React dashboard",
    ]:
        assert stale not in quickstart


def test_workstation_path_keeps_gpu_and_mcp_boundaries_explicit() -> None:
    workstation = squashed("docs/getting-started/workstation-gb10-dgx.md")

    for expected in [
        "NVIDIA GB10",
        "DGX Spark-style",
        "bring-your-own-AI",
        "host.docker.internal",
        "linux/amd64",
        "linux/arm64",
        "NVIDIA Container Toolkit",
        "--gpus all",
        "Do not add MCP-specific host software to the base Docker image",
        "mcp-server-setup-recipes.md",
    ]:
        assert expected in workstation


def test_hermes_plugin_path_documents_existing_hermes_flow() -> None:
    hermes = squashed("docs/getting-started/hermes-plugin.md")

    for expected in [
        "uv tool install hermes-agent --with ./hermes-plugin-wright/",
        "pip install -e ./hermes-plugin-wright",
        "API_SERVER_PORT=8642",
        "HERMES_API_BASE_URL",
        "LLM_API_URL",
        "/wright start",
        "/wright status",
        "/wright catalog cad",
        "../hermes-desktop-wright.md",
        "bring-your-own-AI",
    ]:
        assert expected in hermes


def test_spec_tasks_record_install_path_documentation_slice() -> None:
    tasks = read_text("specs/035-alpha-release-readiness/tasks.md")

    for expected in [
        "Phase 11: Concrete Install Path Documentation",
        "[X] T043 Replace local quickstart with PC-local alpha setup",
        "[X] T044 Add GB10/DGX workstation install path",
        "[X] T045 Add existing Hermes plugin install path",
        "[X] T046 Publish install paths in MkDocs nav and overview",
        "[X] T047 Add regression tests for getting-started install paths",
    ]:
        assert expected in tasks
