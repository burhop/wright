from datetime import UTC, datetime
import json
from pathlib import Path

import pytest

from scripts.release.dependency_audit import (
    DependencyAuditError,
    evaluate_npm_audit,
    evaluate_pip_audit,
)


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


def test_current_npm_audit_exception_is_complete_and_unexpired(
    tmp_path: Path,
) -> None:
    report = tmp_path / "npm-audit.json"
    report.write_text(
        json.dumps(
            {
                "vulnerabilities": {
                    "react-router": {
                        "via": [
                            {
                                "dependency": "react-router",
                                "severity": "high",
                                "url": "https://github.com/advisories/GHSA-qwww-vcr4-c8h2",
                            }
                        ]
                    },
                    "react-router-dom": {
                        "via": ["react-router"],
                        "severity": "high",
                    },
                },
                "metadata": {
                    "vulnerabilities": {
                        "high": 2,
                        "critical": 0,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    evaluate_npm_audit(
        report,
        ROOT / ".github/dependency-audit-policy.json",
        now=datetime(2026, 7, 24, tzinfo=UTC),
    )


def test_unknown_npm_audit_finding_fails_closed(tmp_path: Path) -> None:
    report = tmp_path / "npm-audit.json"
    policy = tmp_path / "policy.json"
    report.write_text(
        json.dumps(
            {
                "vulnerabilities": {
                    "x": {
                        "via": [
                            {
                                "dependency": "x",
                                "severity": "critical",
                                "source": 123,
                            }
                        ]
                    }
                },
                "metadata": {
                    "vulnerabilities": {
                        "high": 0,
                        "critical": 1,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    policy.write_text(json.dumps({"exceptions": []}), encoding="utf-8")
    with pytest.raises(DependencyAuditError, match="123:x"):
        evaluate_npm_audit(report, policy)
