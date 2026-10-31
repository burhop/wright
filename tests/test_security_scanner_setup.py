from pathlib import Path
import os
import shlex
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


@pytest.mark.skipif(
    os.name == "nt", reason="Exercises the Unix linked-worktree scanner"
)
def test_linked_worktree_history_scan_includes_cached_remote_refs(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()

    def git(*args: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(repository), *args], text=True, stderr=subprocess.DEVNULL
        ).strip()

    git("init", "-q")
    git("config", "user.name", "Scanner test")
    git("config", "user.email", "scanner@example.invalid")
    scripts = repository / "scripts"
    scripts.mkdir()
    shutil.copy(ROOT / "scripts/security-scan.sh", scripts / "security-scan.sh")
    (scripts / "check-public-alpha-leaks.py").write_text("pass\n", encoding="utf-8")
    git("add", "scripts")
    git("commit", "-qm", "candidate")
    candidate = git("rev-parse", "HEAD")
    (repository / "remote-only.txt").write_text("remote history\n", encoding="utf-8")
    git("add", "remote-only.txt")
    git("commit", "-qm", "remote-only")
    remote = git("rev-parse", "HEAD")
    git("update-ref", "refs/remotes/origin/other", remote)
    worktree = tmp_path / "worktree"
    git("worktree", "add", "-q", "--detach", str(worktree), candidate)

    binary = tmp_path / "bin"
    binary.mkdir()
    docker = binary / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'while [ "$1" != "-v" ]; do shift; done\n'
        "shift\n"
        "scan_root=${1%:/repo}\n"
        'git -C "$scan_root" rev-parse --verify refs/remotes/scan-origin/other > "$SCAN_MARKER"\n',
        encoding="utf-8",
    )
    docker.chmod(0o755)
    marker = tmp_path / "observed-remote"
    env = {
        **os.environ,
        "PATH": f"{binary}{os.pathsep}{os.environ['PATH']}",
        "SCAN_MARKER": str(marker),
    }
    subprocess.run(
        ["bash", str(worktree / "scripts/security-scan.sh"), "--skip-trufflehog"],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )
    assert marker.read_text(encoding="utf-8").strip() == remote


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


def test_public_alpha_safety_audits_locked_runtime_before_policy_evaluation() -> None:
    workflow = read_text(".github/workflows/public-alpha-safety.yml")
    commands = [line.strip() for line in workflow.splitlines()]
    audit_index = next(
        index
        for index, command in enumerate(commands)
        if command.startswith("uv run ") and "pip-audit" in command
    )
    audit = shlex.split(commands[audit_index])
    options = audit[2 : audit.index("--with")]

    assert "--locked" in options
    assert "--extra" in options
    assert options[options.index("--extra") + 1] == "runtime"
    assert audit[audit.index("--with") + 1 : -2] == [
        "pip-audit",
        "pip-audit",
        "--format",
        "json",
        "--output",
        "pip-audit.json",
    ]
    # Findings produce a nonzero audit exit; the policy evaluator must still run
    # and its own failure must remain blocking.
    assert audit[-2:] == ["||", "true"]
    evaluator = shlex.split(commands[audit_index + 1])
    assert evaluator[:2] == ["python", "-c"]
    assert len(evaluator) == 3
    assert (
        "evaluate_pip_audit(Path('pip-audit.json'), "
        "Path('.github/dependency-audit-policy.json'))"
    ) in evaluator[2]


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

    assert 'DOCKER_ROOT_DIR="$(cygpath -w "$ROOT_DIR")"' in bash_script
    assert "MSYS_NO_PATHCONV=1 docker run" in bash_script
    assert '-v "$DOCKER_SCAN_ROOT_DIR:/repo"' in bash_script
    assert '[ -f "$ROOT_DIR/.git" ]' in bash_script
    assert "git clone --no-hardlinks --no-checkout" in bash_script
    assert "rev-list --count HEAD" in bash_script
    assert "refusing a false-green scan" in bash_script

    assert (
        'Test-Path -LiteralPath (Join-Path $RootDir ".git") -PathType Leaf'
        in powershell_script
    )
    assert "git clone --no-hardlinks --no-checkout" in powershell_script
    assert "rev-list --count HEAD" in powershell_script
    assert (
        "Remove-Item -LiteralPath $TemporaryScanParent -Recurse -Force"
        in powershell_script
    )

    assert "scripts/security-scan.sh --include-untracked" in alpha_bash
    assert "scripts/security-scan.ps1 -IncludeUntracked" in alpha_powershell
    assert "git diff --check" in alpha_bash
    assert "git diff --check" in alpha_powershell
    assert "docker-smoke-test.sh" in alpha_bash
    assert "docker-smoke-test.sh" in alpha_powershell


def test_gitleaks_config_keeps_allowlists_narrow() -> None:
    config = read_text(".gitleaks.toml")

    assert "[extend]" in config
    assert "useDefault = true" in config
    assert "Historical Onshape credential examples" in config
    assert "specs/026-mcp-credential-setup/data-model\\.md" in config
    assert 'targetRules = ["generic-api-key"]' in config
    assert 'condition = "AND"' in config
    assert 'regexTarget = "match"' in config
    assert '''run_key"\\s*:\\s*"[0-9a-f]{64}"''' in config
    assert config.count("test-run-ledger\\.json") == 1
    assert config.count("test_program_status\\.py") == 1
    assert config.count("static/program-status/current\\.json") == 1
    assert '''"[0-9a-f]{32,}"''' not in config
    assert config.count("c401712b5f6f30dc6c0685bbd4ae3ddc5cabdeba") == 1
    assert config.count("a48069a97477b58c2debf8029455291eee5af5d3") == 1
    assert config.count("80e7e19d53e42c6c01990731d7cc111cef3009d8") == 1
    assert config.count("playwright-list\\.json\\.txt") == 1
    assert config.count("TR-0091\\.json") == 1
    assert """^WRIGHT_API_TOKEN": "[0-9a-f]{64}"$""" in config
    assert """^api_body_sha256:[0-9a-f]{64}"$""" in config
    assert "^JIG03-KEEPOUTS$" in config
    assert (
        "^packages/workspace_service/src/workspace_service/process_validation/profiles/parametric-drill-jig-03\\.json$"
        in config
    )
    assert "Historical mass-example snapshot tokens" in config
    assert "Historical concept-example snapshot tokens" in config


def test_program_status_gitleaks_allowlist_has_scanner_backed_negative_control() -> (
    None
):
    contract = read_text("scripts/test-gitleaks-program-status-allowlist.sh")
    push = read_text("scripts/check-dev-push.sh")

    assert "ghcr.io/gitleaks/gitleaks:v8.30.1" in contract
    assert '"run_key"' in contract
    assert '"api_key"' in contract
    assert "failed to detect a second API-key match" in contract
    assert "longer than one SHA-256 identity" in contract
    assert "test-gitleaks-program-status-allowlist.sh" in push
    assert "scripts/security-scan.sh --include-untracked --skip-trufflehog" in push
    assert "GitHub security CI remains authoritative" in push
    rule_start = push.index("    scripts/test-gitleaks-program-status-allowlist.sh)")
    rule_scope = push[rule_start : push.index(";;", rule_start)]
    assert "CHECK_GITLEAKS=1" in rule_scope
    assert "tests/test_security_scanner_setup.py" in rule_scope
    history_start = push.index("    scripts/security-scan.*)")
    history_scope = push[history_start : push.index(";;", history_start)]
    assert "CHECK_GITLEAKS_HISTORY=1" in history_scope
    assert "tests/test_security_scanner_setup.py" in history_scope


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


def test_process_evidence_exceptions_pin_exact_rule_path_field_and_value() -> None:
    import json
    import re
    import tomllib

    config = tomllib.loads(read_text(".gitleaks.toml"))
    entries = json.loads(
        read_text("tests/fixtures/security/process-interface-public-identities.json")
    )["entries"]
    allowances = [
        item
        for item in config["allowlists"]
        if item["description"].startswith(
            "User-approved Feature 083 public evidence identities"
        )
    ]
    assert len(entries) == 47
    assert len(allowances) == 32
    for allowance in allowances:
        assert allowance["targetRules"] == ["generic-api-key"]
        assert allowance["condition"] == "AND"
        assert allowance["regexTarget"] == "match"
        assert len(allowance["paths"]) == 1
        expected = [
            e
            for e in entries
            if allowance["paths"] == ["^" + re.escape(e["path"]) + "$"]
        ]
        assert expected
        assert set(allowance["regexes"]) == {
            "^" + re.escape(e["match"]) + "$" for e in expected
        }


@pytest.mark.parametrize(
    "scanner_script", ["scripts/security-scan.sh", "scripts/security-scan.ps1"]
)
def test_linked_worktree_history_clone_contains_only_candidate_ancestry(
    tmp_path, scanner_script
):
    if not shutil.which("git"):
        pytest.skip("Git is required for the real worktree history boundary")
    repository = tmp_path / "source repository"
    repository.mkdir()

    def git(*args, cwd=repository):
        return subprocess.check_output(
            [
                "git",
                "-c",
                "user.name=History fixture",
                "-c",
                "user.email=fixture@example.invalid",
                *args,
            ],
            cwd=cwd,
            text=True,
            stderr=subprocess.PIPE,
        ).strip()

    git("init", "-b", "base")
    (repository / "base.txt").write_text("base")
    git("add", ".")
    git("commit", "-m", "Base")
    git("checkout", "-b", "merged-work")
    (repository / "merged.txt").write_text("merged ancestor")
    git("add", ".")
    git("commit", "-m", "Merged work")
    merged = git("rev-parse", "HEAD")
    git("checkout", "base")
    git("checkout", "-b", "candidate")
    (repository / "candidate.txt").write_text("candidate")
    git("add", ".")
    git("commit", "-m", "Candidate work")
    git("merge", "--no-ff", "merged-work", "-m", "Accepted merged work")
    head = git("rev-parse", "HEAD")
    expected = set(git("rev-list", "HEAD").splitlines())
    assert merged in expected
    git("checkout", "-b", "unrelated", "base")
    (repository / "unrelated.txt").write_text("independent workstream")
    git("add", ".")
    git("commit", "-m", "Unrelated local work")
    unrelated = git("rev-parse", "HEAD")
    git("tag", "unrelated-only")
    worktree = tmp_path / "candidate worktree"
    git("worktree", "add", str(worktree), "candidate")

    # Exercise each script's real clone flags with a main checkout on another
    # branch, an off-branch tag, and a candidate that includes a merged ancestor.
    line = next(
        line
        for line in read_text(scanner_script).splitlines()
        if line.strip().startswith("git clone ")
    )
    flags = []
    for token in shlex.split(line.strip())[2:]:
        if token.startswith("$"):
            break
        flags.append(token)
    clone = tmp_path / "scan clone"
    git("clone", *flags, str(worktree), str(clone))
    git("checkout", "--detach", head, cwd=clone)
    observed = set(git("rev-list", "--all", cwd=clone).splitlines())
    assert observed == expected
    assert merged in observed
    assert unrelated not in observed
