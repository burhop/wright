"""Retain a recorded full qualification for a bounded CI-readiness correction."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from .workflow_policy import WorkflowPolicyError


WORKFLOWS = {
    ".github/workflows/test-windows.yml",
    ".github/workflows/python-quality.yml",
    ".github/workflows/native-hermes-pr.yml",
    ".github/workflows/performance-observability.yml",
    ".github/workflows/release.yml",
}
POLICY_FILES = {
    "scripts/release/ci_correction.py",
    "scripts/release/workflow_policy.py",
    "scripts/check-dev-push.sh",
    "tests/release/test_ci_correction.py",
    "tests/release/test_workflow_policy.py",
    "tests/release/test_dev_push_process.py",
    "packages/workspace_service/tests/test_process_ui_build.py",
    "docs/contributing/dev-push-runbook.md",
}
SETUP_STEPS = (
    "      - name: Enable long Git paths on Windows\n"
    "        if: runner.os == 'Windows'\n"
    "        shell: pwsh\n"
    "        run: git config --global core.longpaths true\n",
    "      - name: Set up Node.js 22\n"
    "        uses: actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0\n"
    "        with:\n"
    "          node-version: 22\n"
    '          cache: "npm"\n',
    "      - name: Install locked interface compiler dependencies\n"
    "        run: npm ci\n",
    "      - name: Verify fixed interface compiler readiness\n"
    "        run: >-\n"
    "          uv run python -c \"from pathlib import Path; import shutil; from workspace_service.process_interfaces.build import BuildToolchain; root=Path.cwd(); BuildToolchain(Path(shutil.which('node') or ''), root, root / 'packages/process_client', root / 'packages/ui_kit').describe()\"\n",
)


def without_readiness_steps(text: str) -> str:
    for step in SETUP_STEPS:
        text = text.replace(step, "")
    return text


def validate_changes(changes: dict[str, tuple[str, str]]) -> None:
    if not changes or not (changes.keys() & WORKFLOWS):
        raise WorkflowPolicyError("CI correction requires a workflow readiness change")
    for path, (before, after) in changes.items():
        if path not in WORKFLOWS | POLICY_FILES:
            raise WorkflowPolicyError(f"CI correction rejects changed input: {path}")
        if path in WORKFLOWS and without_readiness_steps(
            before
        ) != without_readiness_steps(after):
            raise WorkflowPolicyError(
                f"CI correction rejects non-readiness workflow change: {path}"
            )


def validate_receipt(path: Path, base: str) -> dict:
    receipt = json.loads(path.read_text(encoding="utf-8-sig"))
    if (
        receipt.get("exit_code") != 0
        or receipt.get("head") != base
        or receipt.get("head_after") != base
        or receipt.get("gate")
        not in {"scripts/check-dev-merge.ps1", "scripts/check-dev-merge.sh"}
    ):
        raise WorkflowPolicyError(
            "CI correction requires a green full gate for the exact base"
        )
    log_hash = hashlib.sha256(Path(receipt["log"]).read_bytes()).hexdigest()
    if log_hash != receipt.get("log_sha256"):
        raise WorkflowPolicyError("CI correction full-gate log identity does not match")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    def git(*values: str) -> str:
        return subprocess.check_output(
            ["git", "-c", "core.longpaths=true", *values], text=True
        ).strip()

    base = git("rev-parse", "--verify", f"{args.base}^{{commit}}")
    if git("status", "--porcelain"):
        raise WorkflowPolicyError("CI correction requires a clean committed worktree")
    if base != git("rev-parse", "@{u}^{commit}"):
        raise WorkflowPolicyError(
            "CI correction base must equal the current pushed tip"
        )
    if git("rev-list", "--count", f"{base}..HEAD") != "1":
        raise WorkflowPolicyError(
            "CI correction requires exactly one descendant commit"
        )
    subprocess.check_call(["git", "merge-base", "--is-ancestor", base, "HEAD"])
    paths = git("diff", "--name-only", f"{base}..HEAD").splitlines()
    changes = {}
    for path in paths:
        before = subprocess.run(
            ["git", "show", f"{base}:{path}"], capture_output=True, text=True
        )
        changes[path] = (
            before.stdout if before.returncode == 0 else "",
            Path(path).read_text(encoding="utf-8"),
        )
    validate_changes(changes)
    receipt = validate_receipt(args.receipt, base)
    print(
        json.dumps(
            {
                "qualification": "retained full gate plus affected correction checks",
                "base": base,
                "head": git("rev-parse", "HEAD"),
                "full_gate_run": receipt["run_id"],
                "changed": paths,
            }
        )
    )


if __name__ == "__main__":
    main()
