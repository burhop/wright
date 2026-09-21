"""Run the CI Python dependency audit before local candidate validation."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile

from scripts.release.dependency_audit import DependencyAuditError, evaluate_pip_audit


def audit(root: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="wright-dependency-audit-") as directory:
        report = Path(directory) / "pip-audit.json"
        result = subprocess.run(
            [
                "uv",
                "run",
                "--locked",
                "--extra",
                "runtime",
                "--with",
                "pip-audit",
                "pip-audit",
                "--format",
                "json",
                "--output",
                str(report),
            ],
            cwd=root,
            check=False,
        )
        # pip-audit uses 1 for findings. Missing/malformed reports and tool errors
        # must fail, rather than look like an empty vulnerability inventory.
        if result.returncode not in {0, 1} or not report.is_file():
            raise DependencyAuditError(
                "Python dependency audit did not produce a report"
            )
        data = json.loads(report.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("dependencies"), list):
            raise DependencyAuditError("Invalid Python dependency audit report")
        if not data["dependencies"]:
            raise DependencyAuditError("Python dependency audit inventory is empty")
        if result.returncode and not any(d.get("vulns") for d in data["dependencies"]):
            raise DependencyAuditError(
                "Python dependency audit failed without findings"
            )
        evaluate_pip_audit(report, root / ".github/dependency-audit-policy.json")


if __name__ == "__main__":
    audit(Path(__file__).resolve().parents[2])
