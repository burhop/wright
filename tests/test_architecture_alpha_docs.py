from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def squashed(relative_path: str) -> str:
    return " ".join(read_text(relative_path).split())


def test_project_structure_container_strategy_matches_alpha_appliance_contract() -> None:
    project = squashed("docs/architecture/project-structure.md")

    for expected in [
        "does not bundle an LLM",
        "MCP-specific host software",
        "docker/Dockerfile",
        "docker-compose.minimal.yml",
        "http://localhost:8080",
        "Selected MCP dependencies",
        "docs/mcp-catalog/mcp-server-testing-process.md",
        "do not add MCP-specific host software to the base image",
    ]:
        assert expected in project

    for stale in [
        "Thick Base / Thin Code",
        "Dockerfile.base",
        "massive, system-level dependencies",
        "NVIDIA CUDA runtimes, PyTorch, FreeCAD",
        "CalculiX (FEA solver), and OpenSCAD",
    ]:
        assert stale not in project


def test_system_overview_states_byo_ai_and_selected_tool_boundaries() -> None:
    overview = squashed("docs/architecture/system-overview.md")

    for expected in [
        "Wright is alpha software and bring-your-own-AI",
        "does not bundle an LLM",
        "MCP-specific host software",
        "LLM_API_URL",
        "GB10",
        "NVIDIA DGX Spark-style workstation",
        "Selected MCP Toolchains",
        "selected MCP host dependencies",
        "not self-contained for every CAD, CAE, CAM, or AI workflow",
    ]:
        assert expected in overview

    for stale in [
        "complete, standalone",
        "Standalone Engineering AI-in-a-Box",
        "Local & Proprietary Toolchains: Siemens, PTC, Autodesk, Dassault, FreeCAD",
        "self-contained, powerful engineering sandbox",
    ]:
        assert stale not in overview


def test_spec_tasks_record_architecture_alpha_docs_slice() -> None:
    tasks = read_text("specs/035-alpha-release-readiness/tasks.md")

    for expected in [
        "Phase 16: Architecture Alpha Contract Docs",
        "[X] T061 Update project-structure container strategy",
        "[X] T062 Update system overview BYO-AI and selected MCP boundaries",
        "[X] T063 Add regression tests for architecture alpha docs",
    ]:
        assert expected in tasks
