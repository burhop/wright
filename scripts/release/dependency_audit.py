from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path


class DependencyAuditError(ValueError):
    """Raised when dependency vulnerabilities lack an active exception."""


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
                violations.append(f"{vulnerability_id}:{package}")
                continue
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
            expiry = datetime.fromisoformat(
                str(match["expires_at"]).replace("Z", "+00:00")
            )
            if expiry <= current:
                raise DependencyAuditError(
                    f"dependency audit exception expired: {vulnerability_id}:{package}"
                )
    if violations:
        raise DependencyAuditError(
            "unexcepted dependency vulnerabilities: " + ", ".join(violations)
        )
