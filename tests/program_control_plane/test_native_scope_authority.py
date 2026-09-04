"""Standing milestone scope never becomes a fabricated exact approval."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from program_control.json_contracts import canonical_digest
from program_control.validation import _validate_native_scope_authority


ROOT = "docs/programs/engineering-process-platform"
RECORD = "evidence/authorizations/AUTH-EPP-N01-2026-001.json"


def documents(repository_root: Path) -> dict:
    return {
        f"{ROOT}/{relative}": json.loads(
            (repository_root / ROOT / relative).read_text(encoding="utf-8")
        )
        for relative in (RECORD, "schemas/scope-authorization.schema.json")
    }


def scope_state(docs: dict) -> dict:
    return {
        "current_feature": "EPP-N01",
        "revision": 93,
        "approval": {
            "authority_kind": "standing_user_scope",
            "status": "authorized_scope",
            "record": RECORD,
            "record_digest": canonical_digest(docs[f"{ROOT}/{RECORD}"]),
            "exact_subject_approval": False,
        },
    }


def test_recorded_instruction_supports_bounded_scope(repository_root: Path) -> None:
    docs = documents(repository_root)
    findings = []
    _validate_native_scope_authority(docs, ROOT, scope_state(docs), findings)
    assert findings == []


@pytest.mark.parametrize(
    "change",
    [
        "feature",
        "revision",
        "exact",
        "digest",
        "instruction",
        "scope",
        "human",
        "revoked",
    ],
)
def test_scope_cannot_rewrite_authority_or_grant_other_claims(
    repository_root: Path, change: str
) -> None:
    docs = copy.deepcopy(documents(repository_root))
    state = scope_state(docs)
    record = docs[f"{ROOT}/{RECORD}"]
    if change == "feature":
        state["current_feature"] = "EPP-F02"
    elif change == "revision":
        state["revision"] = 89
    elif change == "exact":
        state["approval"]["exact_subject_approval"] = True
    elif change == "digest":
        state["approval"]["record_digest"] = "0" * 64
    elif change == "instruction":
        record["instruction"] += " Allow publication."
    elif change == "scope":
        record["allowed_scopes"].append("publication")
    elif change == "human":
        record["human_review_evidence"] = True
    elif change == "revoked":
        record["revoked"] = True
    findings = []
    _validate_native_scope_authority(docs, ROOT, state, findings)
    assert [finding.code for finding in findings] == ["NATIVE_SCOPE_AUTHORITY_INVALID"]


def test_old_candidate_cannot_keep_changed_implementation_unleased(
    repository_root: Path,
) -> None:
    from datetime import datetime, timezone
    from program_control.git_subject import GitReader
    from program_control.validation import validate_roadmap_approval_and_lease

    reader = GitReader(repository_root)
    names = (
        "program-state.json",
        "roadmap.json",
        "decision-register.json",
        "risk-register.json",
        "lifecycle-policy.json",
        "gate-catalog.json",
        "work-registry.json",
    )
    docs = {
        f"{ROOT}/{name}": json.loads(
            (repository_root / ROOT / name).read_text(encoding="utf-8")
        )
        for name in names
    }
    # Exercise the closed-lease checkpoint independent of the current writer
    # state and whether CI checked out a branch or a detached candidate.
    state = json.loads(
        (repository_root / ROOT / "evidence/states/program-state-revision-0096.json")
        .read_text(encoding="utf-8")
    )
    docs[f"{ROOT}/program-state.json"] = state
    previous = reader.resolve_identity("7404a549ae244cc05d89e062c60276e8862f53c9", ROOT)
    state["scoped_checkpoint"].update(
        candidate_commit=previous.source_commit, candidate_tree=previous.source_tree
    )
    findings, _ = validate_roadmap_approval_and_lease(
        docs,
        ROOT,
        observed_at=datetime.now(timezone.utc),
        actual_branch="",
        worktree_id=repository_root.name,
        reader=reader,
        source_commit=reader.current_head(),
    )
    assert any(
        f.code == "LEASE_IDENTITY_MISMATCH"
        and f.invariant == "NATIVE_SCOPED_CANDIDATE_IDENTITY"
        for f in findings
    )
