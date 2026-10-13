import hashlib
import json
import subprocess
import sys

import pytest

from scripts.release.ci_correction import (
    SETUP_STEPS,
    main,
    validate_changes,
    validate_receipt,
)
from scripts.release.workflow_policy import WorkflowPolicyError


def test_only_readiness_additions_retain_the_workflow_body():
    before = "jobs:\n  test:\n    steps:\n      - run: pytest all_tests\n"
    after = before.replace("    steps:\n", "    steps:\n" + SETUP_STEPS[0])
    validate_changes({".github/workflows/test-windows.yml": (before, after)})
    with pytest.raises(WorkflowPolicyError, match="non-readiness"):
        validate_changes(
            {
                ".github/workflows/test-windows.yml": (
                    before,
                    after.replace("all_tests", "one_test"),
                )
            }
        )
    with pytest.raises(WorkflowPolicyError, match="non-readiness"):
        validate_changes(
            {
                ".github/workflows/test-windows.yml": (
                    before,
                    after.replace("longpaths true", "longpaths false"),
                )
            }
        )


@pytest.mark.parametrize(
    "path",
    [
        "apps/api/src/api/main.py",
        "package-lock.json",
        "docker/Dockerfile",
        "pyproject.toml",
        "packages/workspace_service/src/workspace_service/process_interfaces/build.py",
        ".github/workflows/docker-build.yml",
    ],
)
def test_product_dependency_packaging_and_publication_changes_are_rejected(path):
    with pytest.raises(WorkflowPolicyError, match="rejects changed input"):
        validate_changes(
            {
                ".github/workflows/test-windows.yml": ("", SETUP_STEPS[0]),
                path: ("old", "new"),
            }
        )


def test_retained_receipt_requires_success_exact_identity_and_unchanged_log(tmp_path):
    log = tmp_path / "gate.log"
    log.write_bytes(b"gate output\n")
    base = "a" * 40
    receipt = {
        "exit_code": 0,
        "head": base,
        "head_after": base,
        "gate": "scripts/check-dev-merge.ps1",
        "log": str(log),
        "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
    }
    path = tmp_path / "receipt.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    validate_receipt(path, base)
    with pytest.raises(WorkflowPolicyError, match="exact base"):
        validate_receipt(path, "b" * 40)
    receipt["exit_code"] = 1
    path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(WorkflowPolicyError, match="green full gate"):
        validate_receipt(path, base)
    receipt["exit_code"] = 0
    path.write_text(json.dumps(receipt), encoding="utf-8")
    log.write_bytes(b"replaced output\n")
    with pytest.raises(WorkflowPolicyError, match="log identity"):
        validate_receipt(path, base)


def test_real_git_scope_requires_clean_single_commit_on_the_pushed_base(
    tmp_path, monkeypatch
):
    repo = tmp_path / "checkout"
    repo.mkdir()
    monkeypatch.chdir(repo)

    def git(*args):
        return subprocess.check_output(
            ["git", *args], text=True, stderr=subprocess.STDOUT
        ).strip()

    git("init", "-b", "codex/fix")
    git("config", "user.name", "Test")
    git("config", "user.email", "test@example.invalid")
    workflow = repo / ".github/workflows/test-windows.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        "jobs:\n  test:\n    steps:\n      - run: pytest all_tests\n", encoding="utf-8"
    )
    git("add", ".github/workflows/test-windows.yml")
    git("commit", "-m", "Qualified baseline")
    base = git("rev-parse", "HEAD")
    git("remote", "add", "origin", ".")
    git("update-ref", "refs/remotes/origin/codex/fix", base)
    git("branch", "--set-upstream-to=origin/codex/fix")
    workflow.write_text(
        workflow.read_text(encoding="utf-8").replace(
            "    steps:\n", "    steps:\n" + SETUP_STEPS[0]
        ),
        encoding="utf-8",
    )
    git("add", ".github/workflows/test-windows.yml")
    git("commit", "-m", "Readiness correction")
    log = tmp_path / "gate.log"
    log.write_bytes(b"qualified output")
    receipt = tmp_path / "receipt.json"
    receipt.write_text(
        json.dumps(
            {
                "exit_code": 0,
                "head": base,
                "head_after": base,
                "gate": "scripts/check-dev-merge.ps1",
                "log": str(log),
                "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
                "run_id": "qualified-test",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys, "argv", ["ci_correction", "--base", base, "--receipt", str(receipt)]
    )
    main()
    dirty = repo / "unreviewed.txt"
    dirty.write_text("dirty", encoding="utf-8")
    with pytest.raises(WorkflowPolicyError, match="clean committed"):
        main()
    git("add", "unreviewed.txt")
    git("commit", "-m", "Second correction")
    with pytest.raises(WorkflowPolicyError, match="exactly one"):
        main()
