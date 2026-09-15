"""Versioned, provider-neutral checks over actual engineering result evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from core.tracing import traced


@dataclass(frozen=True, slots=True)
class EngineeringAssertionResult:
    assertion_id: str
    version: str
    state: str
    expected: Any
    observed: Any
    units: str | None
    evidence: tuple[str, ...]
    correction: str | None = None


@traced("workspace.workflow_engineering_assertion.evaluate")
def evaluate_assertion(
    assertion_id: str,
    *,
    observed: Any,
    expected: Any,
    predicate: Callable[[Any], bool],
    evidence: tuple[str, ...],
    units: str | None = None,
    correction: str,
    version: str = "1.0.0",
) -> EngineeringAssertionResult:
    if not evidence:
        return EngineeringAssertionResult(
            assertion_id,
            version,
            "inconclusive",
            expected,
            observed,
            units,
            (),
            "Provide evidence from the exact output before evaluating this result.",
        )
    try:
        passed = predicate(observed)
    except (TypeError, ValueError, ArithmeticError):
        passed = False
    return EngineeringAssertionResult(
        assertion_id,
        version,
        "pass" if passed else "fail",
        expected,
        observed,
        units,
        evidence,
        None if passed else correction,
    )


def all_pass(results: tuple[EngineeringAssertionResult, ...]) -> bool:
    return bool(results) and all(result.state == "pass" for result in results)
