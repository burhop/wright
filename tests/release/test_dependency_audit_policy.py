from datetime import UTC, datetime
import json
from pathlib import Path

import pytest

from scripts.release.dependency_audit import DependencyAuditError, evaluate_pip_audit


ROOT = Path(__file__).resolve().parents[2]


def test_current_dependency_audit_exception_is_complete_and_unexpired(
    tmp_path: Path,
) -> None:
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps(
            {
                "dependencies": [
                    {
                        "name": "ecdsa",
                        "vulns": [{"id": "PYSEC-2026-1325"}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    evaluate_pip_audit(
        report,
        ROOT / ".github/dependency-audit-policy.json",
        now=datetime(2026, 7, 12, tzinfo=UTC),
    )


def test_unknown_or_expired_dependency_finding_fails_closed(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    policy = tmp_path / "policy.json"
    report.write_text(
        json.dumps({"dependencies": [{"name": "x", "vulns": [{"id": "CVE-X"}]}]}),
        encoding="utf-8",
    )
    policy.write_text(json.dumps({"exceptions": []}), encoding="utf-8")
    with pytest.raises(DependencyAuditError, match="CVE-X"):
        evaluate_pip_audit(report, policy)
