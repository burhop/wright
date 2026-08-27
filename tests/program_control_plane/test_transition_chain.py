"""Closed legacy compatibility and v2 transition-chain contracts."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from program_control.git_subject import GitReader
from program_control.validation import _validate_state_chain, validate_legacy_profiles


PROGRAM_ROOT = "docs/programs/engineering-process-platform"
APPROVED_SUBJECT = "10d13cbeaa2d038744752e93713ab7671f17f7d4"


def load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


class MutatingReader:
    def __init__(self, delegate: GitReader, target: str) -> None:
        self.delegate = delegate
        self.target = target

    def blob(self, commit: str, path: str) -> bytes:
        raw = self.delegate.blob(commit, path)
        return raw + b" " if path == self.target else raw


def profile_set(repository_root: Path) -> dict:
    return load(
        repository_root
        / "specs/076-control-plane-validator/contracts/legacy-compatibility-profile.json"
    )


def codes(findings) -> set[str]:
    return {finding.code for finding in findings}


def test_exact_two_closed_profiles_validate_against_approval_subject(repository_root: Path) -> None:
    findings = validate_legacy_profiles(
        GitReader(repository_root),
        APPROVED_SUBJECT,
        PROGRAM_ROOT,
        profile_set(repository_root),
        observed_v1_revisions=range(1, 20),
        migration_count=1,
    )
    assert findings == []


@pytest.mark.parametrize(
    ("mutator", "expected"),
    [
        (lambda value: value["profiles"].append(copy.deepcopy(value["profiles"][0])), "LEGACY_PROFILE_COUNT"),
        (lambda value: value["profiles"][1].__setitem__("from_revision", 11), "LEGACY_PROFILE_RANGE"),
        (lambda value: value["profiles"][1]["states"][0].__setitem__("path", value["profiles"][0]["states"][0]["path"]), "LEGACY_PATH_DUPLICATE"),
        (lambda value: value["profiles"][0]["transitions"][0].__setitem__("raw_sha256", None), "LEGACY_RAW_RULE_INVALID"),
        (lambda value: value["profiles"][1]["successor"].__setitem__("maximum_count", 2), "LEGACY_SUCCESSOR_INVALID"),
    ],
)
def test_closed_profile_shape_rejects_expansion(repository_root: Path, mutator, expected: str) -> None:
    value = copy.deepcopy(profile_set(repository_root))
    mutator(value)
    findings = validate_legacy_profiles(
        GitReader(repository_root), APPROVED_SUBJECT, PROGRAM_ROOT, value
    )
    assert expected in codes(findings)


def test_future_v1_and_second_migration_are_rejected(repository_root: Path) -> None:
    findings = validate_legacy_profiles(
        GitReader(repository_root),
        APPROVED_SUBJECT,
        PROGRAM_ROOT,
        profile_set(repository_root),
        observed_v1_revisions=range(1, 21),
        migration_count=2,
    )
    assert {"LEGACY_FUTURE_RECORD", "LEGACY_MIGRATION_COUNT"}.issubset(codes(findings))


def test_changed_historical_transition_blob_is_rejected(repository_root: Path) -> None:
    reader = MutatingReader(
        GitReader(repository_root),
        f"{PROGRAM_ROOT}/evidence/transitions/TR-0017.json",
    )
    findings = validate_legacy_profiles(reader, APPROVED_SUBJECT, PROGRAM_ROOT, profile_set(repository_root))
    assert "LEGACY_BLOB_MISMATCH" in codes(findings)


def test_current_v2_chain_has_exact_legal_edges(repository_root: Path) -> None:
    root = repository_root / PROGRAM_ROOT
    documents = {
        f"{PROGRAM_ROOT}/{path.relative_to(root).as_posix()}": load(path)
        for directory in (root / "evidence/states", root / "evidence/transitions")
        for path in directory.glob("*.json")
    }
    documents[f"{PROGRAM_ROOT}/program-state.json"] = load(root / "program-state.json")
    documents[f"{PROGRAM_ROOT}/lifecycle-policy.json"] = load(root / "lifecycle-policy.json")
    findings = []
    _validate_state_chain(documents, PROGRAM_ROOT, findings)
    assert findings == []


def test_illegal_feature_edge_and_second_v2_migration_fail(repository_root: Path) -> None:
    root = repository_root / PROGRAM_ROOT
    documents = {
        f"{PROGRAM_ROOT}/{path.relative_to(root).as_posix()}": load(path)
        for directory in (root / "evidence/states", root / "evidence/transitions")
        for path in directory.glob("*.json")
    }
    documents[f"{PROGRAM_ROOT}/program-state.json"] = load(root / "program-state.json")
    documents[f"{PROGRAM_ROOT}/lifecycle-policy.json"] = load(root / "lifecycle-policy.json")
    documents[f"{PROGRAM_ROOT}/evidence/transitions/TR-0020.json"] = copy.deepcopy(
        documents[f"{PROGRAM_ROOT}/evidence/transitions/TR-0020.json"]
    )
    documents[f"{PROGRAM_ROOT}/evidence/transitions/TR-0020.json"]["to_state"] = "VERIFIED"
    duplicate = copy.deepcopy(documents[f"{PROGRAM_ROOT}/evidence/transitions/TR-0019.json"])
    duplicate["transition_id"] = "TR-0021"
    documents[f"{PROGRAM_ROOT}/evidence/transitions/TR-0021.json"] = duplicate
    findings = []
    _validate_state_chain(documents, PROGRAM_ROOT, findings)
    assert {"LIFECYCLE_EDGE_INVALID", "LEGACY_MIGRATION_COUNT"}.issubset(codes(findings))
