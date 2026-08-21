from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = "docs/contributing/dev-push-runbook.md"


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_dev_push_runbook_is_mandatory_at_every_entry_point() -> None:
    assert (ROOT / RUNBOOK).is_file()
    assert "contributing/dev-push-runbook.md" in _read("mkdocs.yml")
    for relative_path in (
        "AGENTS.md",
        "docs/contributing/pull-requests.md",
        "scripts/check-dev-push.sh",
        "scripts/check-dev-push.ps1",
        "scripts/check-dev-merge.sh",
        "scripts/check-dev-merge.ps1",
    ):
        expected_reference = (
            "dev-push-runbook.md"
            if relative_path.startswith("docs/contributing/")
            else RUNBOOK
        )
        assert expected_reference in _read(relative_path), relative_path


def test_fast_gate_contains_the_frontend_ci_contract() -> None:
    gate = _read("scripts/check-dev-push.sh")
    for command in (
        "npx -w apps/web eslint .",
        "npx prettier --check apps/web/",
        "npx tsc --noEmit -p apps/web/tsconfig.app.json",
        "npm run test --workspace=apps/web",
        "npm run build --workspace=apps/web",
    ):
        assert command in gate


def test_fast_gate_uses_impacted_tests_and_includes_untracked_files() -> None:
    gate = _read("scripts/check-dev-push.sh")

    assert "git ls-files --others --exclude-standard" in gate
    assert "symbolic-full-name '@{u}'" in gate
    assert "Selected scopes:" in gate
    assert 'npm run test --workspace=apps/web -- --changed "$BASE_REF"' in gate
    assert 'npx playwright test "${PLAYWRIGHT_TARGETS[@]}"' in gate
    assert "--project=chromium" in gate
    assert "tests/ui-integration/navigation.spec.ts" in gate
    assert "tests/ui-integration/workspace-surfaces/focus-layout.spec.ts" in gate
    assert "tests/ui-integration/workspace-surfaces/rivet-run-inspector.spec.ts" in gate


def test_browser_gate_uses_isolated_configurable_ports() -> None:
    push_gate = _read("scripts/check-dev-push.sh")
    merge_gate = _read("scripts/check-dev-merge.sh")
    playwright = _read("playwright.config.ts")
    vite = _read("apps/web/vite.config.ts")

    assert "WRIGHT_GATE_API_PORT" in push_gate
    assert "WRIGHT_GATE_UI_PORT" in push_gate
    assert '"$GATE_PYTHON" -m uvicorn api.main:app' in push_gate
    assert '"$GATE_PYTHON" -m uvicorn api.main:app' in merge_gate
    assert "UV_PROJECT_ENVIRONMENT" in push_gate
    assert "WRIGHT_GATE_API_PORT" in merge_gate
    assert "WRIGHT_GATE_UI_PORT" in merge_gate
    assert "UV_PROJECT_ENVIRONMENT" in merge_gate
    assert "WRIGHT_PLAYWRIGHT_PORT" in playwright
    assert "WRIGHT_WEB_API_PROXY_TARGET" in vite
    assert "/.venv-dev-gate/" in _read(".gitignore")


def test_frontend_ci_reports_unit_and_browser_failures_in_parallel() -> None:
    workflow = _read(".github/workflows/frontend-quality.yml")

    assert "needs: frontend-quality" not in workflow
    assert "cancel-in-progress: true" in workflow
