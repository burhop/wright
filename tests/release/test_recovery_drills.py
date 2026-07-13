import pytest

from scripts.release.recovery import (
    RecoveryAction,
    restore_alias_decision,
    retry_decision,
)


def test_identical_retry_resumes_and_conflict_requires_patch() -> None:
    assert retry_decision("sha256:a", "sha256:a").action is RecoveryAction.RESUME
    conflict = retry_decision("sha256:a", "sha256:b")
    assert conflict.action is RecoveryAction.NEW_PATCH
    assert conflict.immutable_subject_unchanged


def test_alias_restore_requires_previously_verified_digest() -> None:
    digest = "sha256:" + "a" * 64
    assert (
        restore_alias_decision(digest, {digest}).action is RecoveryAction.RESTORE_ALIAS
    )
    with pytest.raises(ValueError, match="verified"):
        restore_alias_decision("sha256:" + "b" * 64, {digest})
