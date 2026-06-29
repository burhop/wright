from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_original_alpha_prompt_is_archived_with_spec_artifacts() -> None:
    prompt_path = ROOT / "specs/035-alpha-release-readiness/alpha-release-readiness-prompt.md"

    assert prompt_path.exists()
    assert not (ROOT / "docs/alpha-release-readiness-prompt.md").exists()

    prompt = prompt_path.read_text(encoding="utf-8")
    assert "Wright Alpha Release Readiness Prompt" in prompt
    assert "first public alpha release" in prompt
    assert "MCP-specific host software" in prompt


def test_spec_tasks_record_final_wrapup_slice() -> None:
    tasks = read_text("specs/035-alpha-release-readiness/tasks.md")

    for expected in [
        "Phase 21: Final Wrap-Up and Manual Test Prep",
        "[X] T079 Archive original alpha release readiness prompt",
        "[X] T080 Add regression tests for prompt archive location",
        "[X] T081 Run final automated gates before manual file testing",
    ]:
        assert expected in tasks
