from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def squashed(relative_path: str) -> str:
    return " ".join(read_text(relative_path).split())


def test_public_alpha_safety_runs_gitleaks_and_trufflehog() -> None:
    workflow = read_text(".github/workflows/public-alpha-safety.yml")

    for expected in [
        "fetch-depth: 0",
        "python scripts/check-public-alpha-leaks.py",
        "ghcr.io/gitleaks/gitleaks:v8.30.1",
        "git /repo",
        "--config /repo/.gitleaks.toml",
        "ghcr.io/trufflesecurity/trufflehog:3.95.7",
        "git file:///repo",
        "--results=verified,unknown",
        "--exclude-globs=uv.lock,package-lock.json",
    ]:
        assert expected in workflow


def test_security_scan_scripts_use_pinned_scanner_images() -> None:
    bash_script = read_text("scripts/security-scan.sh")
    powershell_script = read_text("scripts/security-scan.ps1")
    alpha_bash = read_text("scripts/alpha-release-check.sh")
    alpha_powershell = read_text("scripts/alpha-release-check.ps1")

    for script in [bash_script, powershell_script]:
        assert "ghcr.io/gitleaks/gitleaks:v8.30.1" in script
        assert "ghcr.io/trufflesecurity/trufflehog:3.95.7" in script
        assert "check-public-alpha-leaks.py" in script
        assert ".gitleaks.toml" in script

    assert "scripts/security-scan.sh --include-untracked" in alpha_bash
    assert "scripts/security-scan.ps1 -IncludeUntracked" in alpha_powershell
    assert "git diff --check" in alpha_bash
    assert "git diff --check" in alpha_powershell
    assert "docker-smoke-test.sh" in alpha_bash
    assert "docker-smoke-test.sh" in alpha_powershell


def test_gitleaks_config_keeps_placeholder_allowlist_narrow() -> None:
    config = read_text(".gitleaks.toml")

    assert "[extend]" in config
    assert "useDefault = true" in config
    assert "Historical Onshape credential examples" in config
    assert "specs/026-mcp-credential-setup/data-model\\.md" in config
    assert "generic-api-key" not in config


def test_docs_and_makefile_expose_local_alpha_gate() -> None:
    checklist = read_text("docs/public-launch-checklist.md")
    ci_docs = squashed("docs/contributing/ci-cd-workflows.md")
    testing = squashed("docs/contributing/testing.md")
    scripts = read_text("scripts/README.md")
    makefile = read_text("Makefile")

    for expected in [
        "scripts/security-scan.ps1 -IncludeUntracked",
        "scripts/security-scan.sh --include-untracked",
        "scripts/alpha-release-check.ps1",
        "scripts/alpha-release-check.sh",
        "make alpha-release-check",
    ]:
        assert expected in checklist
        assert expected in ci_docs or expected in testing or expected in scripts

    assert "alpha-release-check:" in makefile
    assert "security-scan:" in makefile
    assert "docker-smoke:" in makefile


def test_spec_tasks_record_security_scanner_setup_slice() -> None:
    tasks = read_text("specs/035-alpha-release-readiness/tasks.md")

    for expected in [
        "Phase 22: Dedicated Secret Scanners and Local CI Gate",
        "[X] T082 Add Gitleaks and TruffleHog security scanning to CI",
        "[X] T083 Add local security scan wrappers",
        "[X] T084 Add Gitleaks configuration for documented placeholders",
        "[X] T085 Add local alpha release check target",
        "[X] T086 Add regression tests for scanner setup",
    ]:
        assert expected in tasks
