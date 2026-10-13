"""Run CI's Node dependency audit against the workspace lockfile."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from scripts.release.dependency_audit import DependencyAuditError, evaluate_npm_audit


def audit(root: Path) -> None:
    npm = shutil.which("npm")
    if npm is None:
        raise DependencyAuditError("Node dependency audit requires npm")
    with tempfile.TemporaryDirectory(prefix="wright-node-audit-") as directory:
        report = Path(directory) / "npm-audit.json"
        with report.open("w", encoding="utf-8") as output:
            result = subprocess.run(
                [npm, "audit", "--json", "--audit-level=high"],
                cwd=root,
                check=False,
                stdout=output,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
        if result.returncode not in {0, 1}:
            raise DependencyAuditError("Node dependency audit command failed")
        try:
            data = json.loads(report.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            raise DependencyAuditError("Invalid Node dependency audit report") from exc
        if (
            not isinstance(data, dict)
            or "error" in data
            or not isinstance(data.get("vulnerabilities"), dict)
            or not isinstance(data.get("metadata"), dict)
        ):
            raise DependencyAuditError("Invalid Node dependency audit report")
        inventory = data["metadata"].get("dependencies", {})
        total = inventory.get("total") if isinstance(inventory, dict) else None
        if type(total) is not int or total <= 0:
            raise DependencyAuditError("Node dependency audit inventory is empty")
        counts = data["metadata"].get("vulnerabilities")
        if not isinstance(counts, dict) or any(
            type(counts.get(severity)) is not int or counts[severity] < 0
            for severity in ("high", "critical")
        ):
            raise DependencyAuditError("Invalid Node dependency audit severity counts")
        if result.returncode and not data["vulnerabilities"]:
            raise DependencyAuditError("Node dependency audit failed without findings")
        evaluate_npm_audit(report, root / ".github/dependency-audit-policy.json")


if __name__ == "__main__":
    audit(Path(__file__).resolve().parents[2])
