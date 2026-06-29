from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def squashed(relative_path: str) -> str:
    return " ".join(read_text(relative_path).split())


def test_agent_docker_architecture_uses_alpha_readiness_language() -> None:
    architecture = squashed("docs/agent-docker-architecture.md")

    assert "alpha-compatible, clash-free, and recoverable deployment" in architecture
    assert "production-ready" not in architecture.lower()


def test_wright_hermes_plugin_plan_uses_alpha_readiness_language() -> None:
    plan = squashed("docs/wright-hermes-plugin-plan.md")

    assert "Alpha-ready, community-shareable plugin" in plan
    assert "Production-ready" not in plan


def test_spec_tasks_record_legacy_plan_alpha_language_slice() -> None:
    tasks = read_text("specs/035-alpha-release-readiness/tasks.md")

    for expected in [
        "Phase 20: Legacy Plan Alpha Language",
        "[X] T076 Refresh legacy agent Docker architecture implementation note",
        "[X] T077 Refresh Wright Hermes plugin plan polish goal",
        "[X] T078 Add regression tests for legacy plan alpha language",
    ]:
        assert expected in tasks
