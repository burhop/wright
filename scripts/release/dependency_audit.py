from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path


class DependencyAuditError(ValueError):
    """Raised when dependency vulnerabilities lack an active exception."""


def _require_active_exception(
    exceptions: list[dict[str, object]],
    vulnerability_id: str,
    package: str,
    current: datetime,
) -> bool:
    match = next(
        (
            item
            for item in exceptions
            if item.get("vulnerability_id") == vulnerability_id
            and item.get("package") == package
        ),
        None,
    )
    if match is None:
        return False
    required = {
        "owner",
        "rationale",
        "compensating_control",
        "approved_by",
        "expires_at",
    }
    if not all(str(match.get(key, "")).strip() for key in required):
        raise DependencyAuditError(
            f"dependency audit exception is incomplete: {vulnerability_id}:{package}"
        )
    expiry = datetime.fromisoformat(str(match["expires_at"]).replace("Z", "+00:00"))
    if expiry <= current:
        raise DependencyAuditError(
            f"dependency audit exception expired: {vulnerability_id}:{package}"
        )
    return True


def evaluate_pip_audit(
    report_path: Path, policy_path: Path, *, now: datetime | None = None
) -> None:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    current = now or datetime.now(UTC)
    exceptions = policy.get("exceptions", [])
    violations: list[str] = []
    for dependency in report.get("dependencies", []):
        package = dependency.get("name")
        for vulnerability in dependency.get("vulns", []):
            vulnerability_id = vulnerability.get("id")
            if not _require_active_exception(
                exceptions, vulnerability_id, package, current
            ):
                violations.append(f"{vulnerability_id}:{package}")
    if violations:
        raise DependencyAuditError(
            "unexcepted dependency vulnerabilities: " + ", ".join(violations)
        )


def evaluate_npm_audit(
    report_path: Path, policy_path: Path, *, now: datetime | None = None
) -> None:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    current = now or datetime.now(UTC)
    exceptions = policy.get("exceptions", [])
    violations: list[str] = []
    findings = 0

    for package, result in report.get("vulnerabilities", {}).items():
        for vulnerability in result.get("via", []):
            if not isinstance(vulnerability, dict):
                continue
            if vulnerability.get("severity") not in {"high", "critical"}:
                continue
            findings += 1
            url = str(vulnerability.get("url", ""))
            vulnerability_id = (
                url.rsplit("/", maxsplit=1)[-1]
                if url
                else str(vulnerability.get("source", "unknown"))
            )
            affected_package = str(vulnerability.get("dependency") or package)
            if not _require_active_exception(
                exceptions, vulnerability_id, affected_package, current
            ):
                violations.append(f"{vulnerability_id}:{affected_package}")

    metadata = report.get("metadata", {}).get("vulnerabilities", {})
    reported_blocking = int(metadata.get("high", 0)) + int(metadata.get("critical", 0))
    if reported_blocking and not findings:
        raise DependencyAuditError(
            "npm audit reported high or critical vulnerabilities without "
            "machine-readable advisory details"
        )
    if violations:
        raise DependencyAuditError(
            "unexcepted dependency vulnerabilities: " + ", ".join(violations)
        )
