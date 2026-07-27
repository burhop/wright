from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RecoveryAction(StrEnum):
    RESUME = "resume"
    NEW_PATCH = "new_patch"
    YANK = "yank"
    QUARANTINE = "quarantine"
    RESTORE_ALIAS = "restore_alias"
    HOLD_DRAFT = "hold_draft"


@dataclass(frozen=True, slots=True)
class RecoveryDecision:
    action: RecoveryAction
    reason: str
    immutable_subject_unchanged: bool = True


def retry_decision(expected_subject: str, observed_subject: str) -> RecoveryDecision:
    if expected_subject == observed_subject:
        return RecoveryDecision(RecoveryAction.RESUME, "recorded subject is identical")
    return RecoveryDecision(
        RecoveryAction.NEW_PATCH,
        "subject conflict: immutable release files must not be replaced",
    )


def restore_alias_decision(
    target_digest: str, verified_digests: set[str]
) -> RecoveryDecision:
    if target_digest not in verified_digests:
        raise ValueError("mutable aliases may target only a previously verified digest")
    return RecoveryDecision(
        RecoveryAction.RESTORE_ALIAS, "restore last verified digest"
    )
