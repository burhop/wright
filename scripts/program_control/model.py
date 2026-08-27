"""Small deterministic result types shared by the validator and dashboard."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SEVERITY_RANK = {"fatal": 0, "error": 1, "warning": 2, "info": 3}


@dataclass(frozen=True)
class Finding:
    """A bounded, support-safe validation finding."""

    code: str
    severity: str
    artifact: str
    invariant: str
    evidence: tuple[str, ...]
    consequence: str
    recovery: str
    json_pointer: str | None = None
    resolution_status: str = "unresolved"
    correction_ref: str | None = None

    def sort_key(self) -> tuple[int, str, str, str, str]:
        return (
            SEVERITY_RANK.get(self.severity, 99),
            self.code,
            self.artifact,
            self.json_pointer or "",
            self.invariant,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "artifact": self.artifact,
            "json_pointer": self.json_pointer,
            "invariant": self.invariant,
            "evidence": list(self.evidence[:20]),
            "consequence": self.consequence,
            "recovery": self.recovery,
            "resolution_status": self.resolution_status,
            "correction_ref": self.correction_ref,
        }


@dataclass
class ValidationResult:
    """One semantic model rendered by both text and JSON output."""

    report: dict[str, Any]
    findings: list[Finding] = field(default_factory=list)
    exit_code: int = 0

    def sorted_findings(self) -> list[Finding]:
        return sorted(self.findings, key=Finding.sort_key)
