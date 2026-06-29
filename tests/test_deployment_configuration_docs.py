from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def squashed(relative_path: str) -> str:
    return " ".join(read_text(relative_path).split())


def test_deployment_config_docker_appliance_states_alpha_boundaries() -> None:
    docs = squashed("docs/deployment-configurations.md")

    for expected in [
        "does not bundle an LLM",
        "MCP-specific host software",
        "install selected MCP host dependencies only",
        "Selected MCP Host Software",
        "installed per selected MCP validation only",
        "MCP host dependencies",
        "Not bundled in the base image",
    ]:
        assert expected in docs

    for stale in [
        "image bundles **everything**",
        "CAD Runtimes",
        "**CAD** | OpenSCAD",
        "**CAD** | FreeCAD",
        "Bundled in image",
        "AppImage in image",
    ]:
        assert stale not in docs


def test_deployment_config_uses_current_docker_run_and_upgrade_paths() -> None:
    docs = squashed("docs/deployment-configurations.md")

    for expected in [
        "docker compose -f docker-compose.minimal.yml up -d --build",
        "docker compose up -d --build",
        "http://localhost:8080",
        "http://localhost:8000",
        "LLM_API_URL=http://host.docker.internal:8000/v1",
        "host.docker.internal:host-gateway",
        "**8080** | Minimal compose host port",
        "**8000** | Full compose host port",
        "docker pull ghcr.io/burhop/wright-agent:<tag>",
        "docker compose -f docker-compose.minimal.yml down",
    ]:
        assert expected in docs

    for stale in [
        "docker pull ghcr.io/burhop/wright:latest",
        "docker stop wright && docker rm wright",
        "wright-appliance:latest # Run (minimal)",
    ]:
        assert stale not in docs


def test_spec_tasks_record_deployment_configuration_docs_slice() -> None:
    tasks = read_text("specs/035-alpha-release-readiness/tasks.md")

    for expected in [
        "Phase 14: Deployment Configuration Truth Check",
        "[X] T055 Align deployment configuration Docker appliance section",
        "[X] T056 Update deployment run, port, and upgrade examples",
        "[X] T057 Add regression tests for deployment configuration docs",
    ]:
        assert expected in tasks
