"""Closed legacy compatibility and v2 transition-chain contracts."""

from __future__ import annotations

import copy
import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from program_control import validation as validation_module
from program_control.git_subject import GitReader
from program_control.dashboard import derive_areas
from program_control.json_contracts import canonical_digest, sha256_bytes
from program_control.validation import (
    _validate_state_chain,
    _validate_transition_history,
    validate_committed_identity_correction,
    validate_legacy_profiles,
)


PROGRAM_ROOT = "docs/programs/engineering-process-platform"
APPROVED_SUBJECT = "10d13cbeaa2d038744752e93713ab7671f17f7d4"
CORRECTION_SUBJECT = "88481d57f1258f59f303f507eafc4e352569bc11"
CORRECTION_ID = "COR-EPP-F01-US1-COMMITTED-IDENTITY-001"
CORRECTION_PATH = f"{PROGRAM_ROOT}/evidence/corrections/{CORRECTION_ID}.json"
APPROVAL_PATHS = (
    f"{PROGRAM_ROOT}/evidence/approvals/APR-EPP-F01-MC-004.json",
    f"{PROGRAM_ROOT}/evidence/approvals/APR-EPP-F01-IMPL-004.json",
)
REPAIR_CORRECTION_ID = "COR-EPP-F01-REPAIR-EVIDENCE-001"
REPAIR_CORRECTION_PATH = (
    f"{PROGRAM_ROOT}/evidence/corrections/{REPAIR_CORRECTION_ID}.json"
)
REPAIR_APPROVAL_PATHS = (
    f"{PROGRAM_ROOT}/evidence/approvals/APR-EPP-F01-MC-007.json",
    f"{PROGRAM_ROOT}/evidence/approvals/APR-EPP-F01-IMPL-007.json",
)
CHECKPOINT_CORRECTION_ID = "COR-EPP-F01-T072-CHECKPOINT-EVIDENCE-001"
CHECKPOINT_CORRECTION_PATH = (
    f"{PROGRAM_ROOT}/evidence/corrections/{CHECKPOINT_CORRECTION_ID}.json"
)
CHECKPOINT_APPROVAL_PATHS = (
    f"{PROGRAM_ROOT}/evidence/approvals/APR-EPP-F01-MC-008.json",
    f"{PROGRAM_ROOT}/evidence/approvals/APR-EPP-F01-IMPL-008.json",
)
CHECKPOINT_DIGEST_TARGETS = frozenset(
    {
        (
            f"{PROGRAM_ROOT}/evidence/transitions/TR-0047.json",
            "/outputs/0/sha256",
        ),
        (
            f"{PROGRAM_ROOT}/evidence/transitions/TR-0047.json",
            "/outputs/1/sha256",
        ),
    }
)
CHECKPOINT_EVENT_TARGETS = frozenset(
    {
        (
            f"{PROGRAM_ROOT}/evidence/transitions/TR-0050.json",
            "repair",
            "repair_checkpoint",
            "BLOCKED",
            "BLOCKED",
        )
    }
)
ACTIVATION_CORRECTION_ID = "COR-EPP-F01B-ACTIVATION-RAW-IDENTITY-001"
ACTIVATION_CORRECTION_PATH = (
    f"{PROGRAM_ROOT}/evidence/corrections/{ACTIVATION_CORRECTION_ID}.json"
)
ACTIVATION_DIGEST_TARGETS = frozenset(
    {
        (
            f"{PROGRAM_ROOT}/evidence/transitions/TR-0070.json",
            f"/outputs/{index}/sha256",
        )
        for index in (3, 4, 5)
    }
)
LEASE_CHECKPOINT_SCHEMA_TARGETS = frozenset(
    {f"{PROGRAM_ROOT}/evidence/states/program-state-revision-0075.json"}
)
LEASE_CHECKPOINT_DIGEST_TARGETS = frozenset(
    {
        (
            f"{PROGRAM_ROOT}/evidence/transitions/TR-0074.json",
            "/inputs/3/sha256",
        ),
        (
            f"{PROGRAM_ROOT}/evidence/transitions/TR-0074.json",
            "/inputs/4/sha256",
        ),
    }
)


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


def correction_inputs(repository_root: Path) -> tuple[dict, dict[str, dict]]:
    profile = load(repository_root / CORRECTION_PATH)
    approvals = {path: load(repository_root / path) for path in APPROVAL_PATHS}
    return profile, approvals


def repair_correction_inputs(
    repository_root: Path,
) -> tuple[dict, dict[str, dict]]:
    profile = load(repository_root / REPAIR_CORRECTION_PATH)
    approvals = {path: load(repository_root / path) for path in REPAIR_APPROVAL_PATHS}
    return profile, approvals


def checkpoint_correction_inputs(
    repository_root: Path,
) -> tuple[dict, dict[str, dict]]:
    profile = load(repository_root / CHECKPOINT_CORRECTION_PATH)
    approvals = {
        path: load(repository_root / path) for path in CHECKPOINT_APPROVAL_PATHS
    }
    return profile, approvals


def activation_correction_input(repository_root: Path) -> dict:
    return load(repository_root / ACTIVATION_CORRECTION_PATH)


def test_exact_f01b_activation_correction_recomputes_three_git_normalized_claims(
    repository_root: Path,
) -> None:
    profile = activation_correction_input(repository_root)
    original_profile = copy.deepcopy(profile)

    findings, digest_targets = (
        validation_module.validate_f01b_activation_evidence_correction(
            GitReader(repository_root), "HEAD", PROGRAM_ROOT, profile
        )
    )

    assert findings == []
    assert digest_targets == ACTIVATION_DIGEST_TARGETS
    assert profile == original_profile


def test_f01b_activation_correction_rejects_any_target_expansion(
    repository_root: Path,
) -> None:
    profile = activation_correction_input(repository_root)
    mutated = copy.deepcopy(profile)
    mutated["claims"][0]["json_pointer"] = "/outputs/2/sha256"

    findings, digest_targets = (
        validation_module.validate_f01b_activation_evidence_correction(
            GitReader(repository_root), "HEAD", PROGRAM_ROOT, mutated
        )
    )

    assert codes(findings) == {"F01B_ACTIVATION_CORRECTION_INVALID"}
    assert digest_targets == frozenset()


def test_exact_f01b_lease_checkpoint_correction_closes_only_three_claims(
    repository_root: Path,
) -> None:
    transition = load(
        repository_root / PROGRAM_ROOT / "evidence/transitions/TR-0075.json"
    )
    successor_state = load(repository_root / PROGRAM_ROOT / "program-state.json")

    findings, schema_targets, digest_targets = (
        validation_module.validate_f01b_lease_checkpoint_correction(
            GitReader(repository_root),
            "HEAD",
            PROGRAM_ROOT,
            transition,
            successor_state,
        )
    )

    assert findings == []
    assert schema_targets == LEASE_CHECKPOINT_SCHEMA_TARGETS
    assert digest_targets == LEASE_CHECKPOINT_DIGEST_TARGETS


@pytest.mark.parametrize("target", ["transition", "successor"])
def test_f01b_lease_checkpoint_correction_rejects_scope_expansion(
    repository_root: Path,
    target: str,
) -> None:
    transition = load(
        repository_root / PROGRAM_ROOT / "evidence/transitions/TR-0075.json"
    )
    successor_state = load(repository_root / PROGRAM_ROOT / "program-state.json")
    if target == "transition":
        transition["action"] += " and widen authority"
    else:
        successor_state["active_mutating_lease"]["allowed_paths"].append(
            "src/unapproved/**"
        )

    findings, schema_targets, digest_targets = (
        validation_module.validate_f01b_lease_checkpoint_correction(
            GitReader(repository_root),
            "HEAD",
            PROGRAM_ROOT,
            transition,
            successor_state,
        )
    )

    assert codes(findings) == {"F01B_LEASE_CHECKPOINT_CORRECTION_INVALID"}
    assert schema_targets == frozenset()
    assert digest_targets == frozenset()


def test_exact_repair_evidence_correction_recomputes_two_claims_and_occurrences(
    repository_root: Path,
) -> None:
    profile, approvals = repair_correction_inputs(repository_root)
    original_profile = copy.deepcopy(profile)
    original_approvals = copy.deepcopy(approvals)
    findings, schema_targets, digest_targets = (
        validation_module.validate_repair_evidence_correction(
            GitReader(repository_root), "HEAD", PROGRAM_ROOT, profile, approvals
        )
    )
    cause_findings = [
        finding
        for finding in findings
        if finding.code == "REPAIR_EVIDENCE_CAUSE_ID_MISMATCH"
    ]
    digest_findings = [
        finding
        for finding in findings
        if finding.code == "REPAIR_EVIDENCE_DIGEST_MISMATCH"
    ]
    assert len(cause_findings) == 2
    assert len(digest_findings) == 1
    assert all(finding.resolution_status == "resolved" for finding in findings)
    assert all(finding.correction_ref == REPAIR_CORRECTION_PATH for finding in findings)
    assert schema_targets == frozenset(
        {
            f"{PROGRAM_ROOT}/evidence/states/program-state-revision-0045.json",
            f"{PROGRAM_ROOT}/evidence/states/program-state-revision-0046.json",
            f"{PROGRAM_ROOT}/evidence/transitions/TR-0044.json",
        }
    )
    assert digest_targets == frozenset(
        {
            (
                f"{PROGRAM_ROOT}/evidence/transitions/TR-0044.json",
                "/inputs/1/sha256",
            )
        }
    )
    assert profile == original_profile
    assert approvals == original_approvals


def test_repair_evidence_correction_rejects_closed_profile_mutations(
    repository_root: Path,
) -> None:
    profile, approvals = repair_correction_inputs(repository_root)
    head = GitReader(repository_root).resolve_commit("HEAD")
    mutations = (
        ("omitted", lambda value: value["claims"].pop()),
        (
            "omitted-occurrence",
            lambda value: value["claims"][0]["occurrences"].pop(),
        ),
        (
            "added",
            lambda value: value["claims"].append(copy.deepcopy(value["claims"][0])),
        ),
        (
            "added-occurrence",
            lambda value: value["claims"][0]["occurrences"].append(
                copy.deepcopy(value["claims"][0]["occurrences"][0])
            ),
        ),
        (
            "substituted",
            lambda value: value["claims"][0].__setitem__(
                "claim_id", "REPAIR-CAUSE-ID-002"
            ),
        ),
        (
            "reordered",
            lambda value: value["claims"].__setitem__(
                slice(0, 2), value["claims"][:2][::-1]
            ),
        ),
        (
            "reordered-occurrences",
            lambda value: value["claims"][0]["occurrences"].__setitem__(
                slice(0, 2), value["claims"][0]["occurrences"][:2][::-1]
            ),
        ),
        (
            "relocated",
            lambda value: value["claims"][0]["occurrences"][0].__setitem__(
                "path",
                f"{PROGRAM_ROOT}/evidence/states/program-state-revision-0044.json",
            ),
        ),
        (
            "wrong-identity",
            lambda value: value["claims"][0]["occurrences"][0].__setitem__(
                "git_blob", "0" * 40
            ),
        ),
        (
            "wrong-raw-identity",
            lambda value: value["claims"][0]["occurrences"][0].__setitem__(
                "raw_sha256", "0" * 64
            ),
        ),
        (
            "wrong-canonical-identity",
            lambda value: value["claims"][0]["occurrences"][0].__setitem__(
                "canonical_state_digest", "0" * 64
            ),
        ),
        (
            "wrong-pointer",
            lambda value: value["claims"][1].__setitem__(
                "json_pointer", "/inputs/0/sha256"
            ),
        ),
        (
            "relocated-transition",
            lambda value: value["claims"][1].__setitem__(
                "transition_path",
                f"{PROGRAM_ROOT}/evidence/transitions/TR-0043.json",
            ),
        ),
        (
            "wrong-digest",
            lambda value: value["claims"][1].__setitem__(
                "authoritative_value", "0" * 64
            ),
        ),
        (
            "wrong-origin",
            lambda value: value["claims"][0]["occurrences"][0].__setitem__(
                "introducing_commit", head
            ),
        ),
        (
            "current-state",
            lambda value: value["claims"][0]["occurrences"][0].__setitem__(
                "path", f"{PROGRAM_ROOT}/program-state.json"
            ),
        ),
        (
            "wildcard",
            lambda value: value["claims"][0]["occurrences"][0].__setitem__(
                "json_pointer", "/active_mutating_lease/recovery/*"
            ),
        ),
        (
            "range",
            lambda value: value["claims"][0]["occurrences"][0].__setitem__(
                "json_pointer",
                "/active_mutating_lease/recovery/[active_cause_id]",
            ),
        ),
        (
            "future",
            lambda value: value["claims"][1].__setitem__("introducing_commit", head),
        ),
        (
            "new-record",
            lambda value: value.__setitem__("accept_new_records", True),
        ),
        (
            "correction-of-correction",
            lambda value: value["claims"][0]["occurrences"][0].__setitem__(
                "path", REPAIR_CORRECTION_PATH
            ),
        ),
        (
            "projection-interference",
            lambda value: value["unchanged_projection_fields"].append(
                "hand_set_readiness"
            ),
        ),
    )
    reader = GitReader(repository_root)
    for label, mutate in mutations:
        candidate = copy.deepcopy(profile)
        mutate(candidate)
        findings, schema_targets, digest_targets = (
            validation_module.validate_repair_evidence_correction(
                reader, "HEAD", PROGRAM_ROOT, candidate, approvals
            )
        )
        mismatch_findings = [
            finding
            for finding in findings
            if finding.code
            in {
                "REPAIR_EVIDENCE_CAUSE_ID_MISMATCH",
                "REPAIR_EVIDENCE_DIGEST_MISMATCH",
            }
        ]
        assert len(mismatch_findings) == 3, label
        assert all(
            finding.resolution_status == "unresolved" for finding in mismatch_findings
        ), label
        assert {
            "REPAIR_EVIDENCE_CORRECTION_INVALID",
            "REPAIR_EVIDENCE_CORRECTION_UNAUTHORIZED",
        } & {finding.code for finding in findings}, label
        assert schema_targets == frozenset(), label
        assert digest_targets == frozenset(), label


def test_repair_evidence_correction_requires_exact_v7_authority(
    repository_root: Path,
) -> None:
    profile, approvals = repair_correction_inputs(repository_root)
    approvals.pop(REPAIR_APPROVAL_PATHS[1])
    findings, schema_targets, digest_targets = (
        validation_module.validate_repair_evidence_correction(
            GitReader(repository_root), "HEAD", PROGRAM_ROOT, profile, approvals
        )
    )
    assert "REPAIR_EVIDENCE_CORRECTION_UNAUTHORIZED" in codes(findings)
    assert all(
        finding.resolution_status == "unresolved"
        for finding in findings
        if finding.code
        in {
            "REPAIR_EVIDENCE_CAUSE_ID_MISMATCH",
            "REPAIR_EVIDENCE_DIGEST_MISMATCH",
        }
    )
    assert schema_targets == frozenset()
    assert digest_targets == frozenset()


class RepairBlobMutatingReader:
    def __init__(self, delegate: GitReader, target: str) -> None:
        self.delegate = delegate
        self.target = target

    def __getattr__(self, name):
        return getattr(self.delegate, name)

    def _mutate(self, path: str, raw: bytes) -> bytes:
        return raw + b" " if path == self.target else raw

    def blob(self, commit: str, path: str) -> bytes:
        return self._mutate(path, self.delegate.blob(commit, path))

    def read_blob_requests(self, requests):
        values = self.delegate.read_blob_requests(requests)
        return {key: self._mutate(key[1], raw) for key, raw in values.items()}

    def read_blobs(self, commit: str, paths):
        values = self.delegate.read_blobs(commit, paths)
        return {path: self._mutate(path, raw) for path, raw in values.items()}

    def blob_facts(self, requests):
        facts = self.delegate.blob_facts(requests)
        return {
            key: (
                replace(
                    fact,
                    sha256=sha256_bytes(
                        self._mutate(fact.path, self.delegate.blob(*key))
                    ),
                )
                if fact.path == self.target
                else fact
            )
            for key, fact in facts.items()
        }


@pytest.mark.parametrize(
    "target",
    [
        f"{PROGRAM_ROOT}/evidence/states/program-state-revision-0045.json",
        f"{PROGRAM_ROOT}/evidence/transitions/TR-0044.json",
        f"{PROGRAM_ROOT}/evidence/transitions/TR-0043.json",
    ],
)
def test_repair_evidence_correction_recomputes_live_git_blobs(
    repository_root: Path,
    target: str,
) -> None:
    profile, approvals = repair_correction_inputs(repository_root)
    findings, schema_targets, digest_targets = (
        validation_module.validate_repair_evidence_correction(
            RepairBlobMutatingReader(GitReader(repository_root), target),
            "HEAD",
            PROGRAM_ROOT,
            profile,
            approvals,
        )
    )
    assert "REPAIR_EVIDENCE_CORRECTION_INVALID" in codes(findings)
    assert schema_targets == frozenset()
    assert digest_targets == frozenset()
    assert all(
        finding.resolution_status == "unresolved"
        for finding in findings
        if finding.code
        in {
            "REPAIR_EVIDENCE_CAUSE_ID_MISMATCH",
            "REPAIR_EVIDENCE_DIGEST_MISMATCH",
        }
    )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda approvals: approvals.pop(REPAIR_APPROVAL_PATHS[0]),
        lambda approvals: approvals.pop(REPAIR_APPROVAL_PATHS[1]),
        lambda approvals: approvals[REPAIR_APPROVAL_PATHS[0]]["subject"].__setitem__(
            "git_commit", "0" * 40
        ),
        lambda approvals: approvals[REPAIR_APPROVAL_PATHS[0]]["subject"][
            "artifact_digests"
        ][5].__setitem__("sha256", "0" * 64),
        lambda approvals: approvals[REPAIR_APPROVAL_PATHS[0]].__setitem__(
            "decision", "rejected"
        ),
        lambda approvals: approvals[REPAIR_APPROVAL_PATHS[0]].__setitem__(
            "expires_at", "2026-08-28T00:00:00Z"
        ),
        lambda approvals: approvals[REPAIR_APPROVAL_PATHS[0]][
            "revocation_events"
        ].append({"revoked_at": "2026-08-28T00:00:00Z"}),
        lambda approvals: approvals[REPAIR_APPROVAL_PATHS[0]]["conditions"].append(
            "extra authority"
        ),
    ],
)
def test_repair_evidence_correction_rejects_v7_authority_variants(
    repository_root: Path,
    mutation,
) -> None:
    profile, approvals = repair_correction_inputs(repository_root)
    mutation(approvals)
    findings, schema_targets, digest_targets = (
        validation_module.validate_repair_evidence_correction(
            GitReader(repository_root), "HEAD", PROGRAM_ROOT, profile, approvals
        )
    )
    assert "REPAIR_EVIDENCE_CORRECTION_UNAUTHORIZED" in codes(findings)
    assert "REPAIR_EVIDENCE_CORRECTION_INVALID" not in codes(findings)
    assert schema_targets == frozenset()
    assert digest_targets == frozenset()


def test_exact_checkpoint_evidence_correction_recomputes_three_of_three(
    repository_root: Path,
) -> None:
    profile, approvals = checkpoint_correction_inputs(repository_root)
    original_profile = copy.deepcopy(profile)
    original_approvals = copy.deepcopy(approvals)

    findings, digest_targets, event_targets = (
        validation_module.validate_checkpoint_evidence_correction(
            GitReader(repository_root), "HEAD", PROGRAM_ROOT, profile, approvals
        )
    )

    digest_findings = [
        finding
        for finding in findings
        if finding.code == "CHECKPOINT_OUTPUT_DIGEST_MISMATCH"
    ]
    event_findings = [
        finding
        for finding in findings
        if finding.code == "CHECKPOINT_EVENT_RULE_MISMATCH"
    ]
    assert len(digest_findings) == 2
    assert len(event_findings) == 1
    assert all(finding.resolution_status == "resolved" for finding in findings)
    assert all(
        finding.correction_ref == CHECKPOINT_CORRECTION_PATH for finding in findings
    )
    assert digest_targets == CHECKPOINT_DIGEST_TARGETS
    assert event_targets == CHECKPOINT_EVENT_TARGETS
    assert profile == original_profile
    assert approvals == original_approvals


def test_checkpoint_evidence_correction_rejects_every_near_miss(
    repository_root: Path,
) -> None:
    profile, approvals = checkpoint_correction_inputs(repository_root)
    head = GitReader(repository_root).resolve_commit("HEAD")
    mutations = (
        ("omission", lambda value: value["claims"].pop()),
        (
            "addition",
            lambda value: value["claims"].append(copy.deepcopy(value["claims"][0])),
        ),
        (
            "substitution",
            lambda value: value["claims"][0].__setitem__("claim_id", "OTHER"),
        ),
        (
            "ordering",
            lambda value: value["claims"].__setitem__(
                slice(0, 2), value["claims"][:2][::-1]
            ),
        ),
        (
            "path",
            lambda value: value["claims"][0].__setitem__(
                "artifact_path", f"{PROGRAM_ROOT}/gates.md"
            ),
        ),
        (
            "pointer",
            lambda value: value["claims"][0].__setitem__(
                "json_pointer", "/outputs/2/sha256"
            ),
        ),
        (
            "blob",
            lambda value: value["claims"][1].__setitem__("artifact_git_blob", "0" * 40),
        ),
        (
            "transition-blob",
            lambda value: value["claims"][2].__setitem__(
                "transition_git_blob", "0" * 40
            ),
        ),
        (
            "container",
            lambda value: value["claims"][0].__setitem__("introducing_commit", head),
        ),
        (
            "event",
            lambda value: value["claims"][2]["authoritative_tuple"].__setitem__(
                "event_kind", "verification"
            ),
        ),
        (
            "domain",
            lambda value: value["claims"][2]["authoritative_tuple"].__setitem__(
                "state_domain", "feature"
            ),
        ),
        (
            "from-state",
            lambda value: value["claims"][2]["authoritative_tuple"].__setitem__(
                "from_state", "IMPLEMENTING"
            ),
        ),
        (
            "to-state",
            lambda value: value["claims"][2]["authoritative_tuple"].__setitem__(
                "to_state", "IMPLEMENTING"
            ),
        ),
        (
            "evidence-map",
            lambda value: value["claims"][2]["required_evidence_mapping"][
                "REPAIR_ATTEMPT"
            ].pop(),
        ),
        (
            "current",
            lambda value: value["claims"][0].__setitem__(
                "artifact_path", f"{PROGRAM_ROOT}/program-state.json"
            ),
        ),
        (
            "future",
            lambda value: value["claims"][2].__setitem__("introducing_commit", head),
        ),
        (
            "wildcard",
            lambda value: value["claims"][0].__setitem__(
                "json_pointer", "/outputs/*/sha256"
            ),
        ),
        (
            "correction-of-correction",
            lambda value: value["claims"][0].__setitem__(
                "transition_path", CHECKPOINT_CORRECTION_PATH
            ),
        ),
        (
            "new-record",
            lambda value: value.__setitem__("accept_new_records", True),
        ),
        (
            "projection-interference",
            lambda value: value["resolution_semantics"].__setitem__(
                "readiness_authority_benchmark_release_non_interference", False
            ),
        ),
    )
    reader = GitReader(repository_root)
    for label, mutate in mutations:
        candidate = copy.deepcopy(profile)
        mutate(candidate)
        findings, digest_targets, event_targets = (
            validation_module.validate_checkpoint_evidence_correction(
                reader, "HEAD", PROGRAM_ROOT, candidate, approvals
            )
        )
        mismatch_findings = [
            finding
            for finding in findings
            if finding.code
            in {
                "CHECKPOINT_OUTPUT_DIGEST_MISMATCH",
                "CHECKPOINT_EVENT_RULE_MISMATCH",
            }
        ]
        assert len(mismatch_findings) == 3, label
        assert all(
            finding.resolution_status == "unresolved" for finding in mismatch_findings
        ), label
        assert "CHECKPOINT_EVIDENCE_CORRECTION_INVALID" in codes(findings), label
        assert digest_targets == frozenset(), label
        assert event_targets == frozenset(), label


@pytest.mark.parametrize(
    "target",
    [
        f"{PROGRAM_ROOT}/evidence/transitions/TR-0047.json",
        f"{PROGRAM_ROOT}/README.md",
        f"{PROGRAM_ROOT}/approval.md",
        f"{PROGRAM_ROOT}/evidence/transitions/TR-0050.json",
    ],
)
def test_checkpoint_evidence_correction_recomputes_committed_git_blobs(
    repository_root: Path,
    target: str,
) -> None:
    profile, approvals = checkpoint_correction_inputs(repository_root)
    findings, digest_targets, event_targets = (
        validation_module.validate_checkpoint_evidence_correction(
            RepairBlobMutatingReader(GitReader(repository_root), target),
            "HEAD",
            PROGRAM_ROOT,
            profile,
            approvals,
        )
    )
    assert "CHECKPOINT_EVIDENCE_CORRECTION_INVALID" in codes(findings)
    assert digest_targets == frozenset()
    assert event_targets == frozenset()


@pytest.mark.parametrize(
    "mutation",
    [
        lambda approvals: approvals.pop(CHECKPOINT_APPROVAL_PATHS[0]),
        lambda approvals: approvals.pop(CHECKPOINT_APPROVAL_PATHS[1]),
        lambda approvals: approvals[CHECKPOINT_APPROVAL_PATHS[0]][
            "subject"
        ].__setitem__("git_commit", "0" * 40),
        lambda approvals: approvals[CHECKPOINT_APPROVAL_PATHS[0]]["subject"][
            "artifact_digests"
        ][0].__setitem__("sha256", "0" * 64),
        lambda approvals: approvals[CHECKPOINT_APPROVAL_PATHS[0]].__setitem__(
            "decision", "rejected"
        ),
        lambda approvals: approvals[CHECKPOINT_APPROVAL_PATHS[0]][
            "revocation_events"
        ].append({"revoked_at": "2026-08-28T10:00:00Z"}),
        lambda approvals: approvals[CHECKPOINT_APPROVAL_PATHS[0]]["conditions"].append(
            "extra authority"
        ),
    ],
)
def test_checkpoint_evidence_correction_requires_exact_v8_authority(
    repository_root: Path,
    mutation,
) -> None:
    profile, approvals = checkpoint_correction_inputs(repository_root)
    mutation(approvals)
    findings, digest_targets, event_targets = (
        validation_module.validate_checkpoint_evidence_correction(
            GitReader(repository_root), "HEAD", PROGRAM_ROOT, profile, approvals
        )
    )
    assert "CHECKPOINT_EVIDENCE_CORRECTION_UNAUTHORIZED" in codes(findings)
    assert digest_targets == frozenset()
    assert event_targets == frozenset()


def test_exact_committed_identity_correction_recomputes_37_of_37(
    repository_root: Path,
) -> None:
    profile, approvals = correction_inputs(repository_root)
    original_profile = copy.deepcopy(profile)
    original_approvals = copy.deepcopy(approvals)
    findings, transition_targets = validate_committed_identity_correction(
        GitReader(repository_root),
        "HEAD",
        PROGRAM_ROOT,
        profile,
        approvals,
    )
    mismatches = [
        finding for finding in findings if finding.code == "COMMITTED_IDENTITY_MISMATCH"
    ]
    assert len(mismatches) == 37
    assert all(finding.resolution_status == "resolved" for finding in mismatches)
    assert all(finding.correction_ref == CORRECTION_PATH for finding in mismatches)
    assert len(transition_targets) == 6
    assert "COMMITTED_IDENTITY_CORRECTION_INVALID" not in codes(findings)
    assert "COMMITTED_IDENTITY_CORRECTION_UNAUTHORIZED" not in codes(findings)
    assert profile == original_profile
    assert approvals == original_approvals


@pytest.mark.parametrize(
    "mutator",
    [
        lambda profile: profile["transition_digest_claims"].pop(),
        lambda profile: profile["historical_state_tree_claims"].append(
            copy.deepcopy(profile["historical_state_tree_claims"][0])
        ),
        lambda profile: profile["transition_digest_claims"][0].__setitem__(
            "json_pointer", "/outputs/*/sha256"
        ),
        lambda profile: profile["historical_state_tree_claims"][0][
            "json_pointers"
        ].append("/readiness/product/status"),
        lambda profile: profile["historical_state_tree_claims"][0].__setitem__(
            "introducing_commit", CORRECTION_SUBJECT
        ),
    ],
)
def test_committed_identity_correction_rejects_any_target_set_or_identity_change(
    repository_root: Path, mutator
) -> None:
    profile, approvals = correction_inputs(repository_root)
    mutator(profile)
    findings, transition_targets = validate_committed_identity_correction(
        GitReader(repository_root), "HEAD", PROGRAM_ROOT, profile, approvals
    )
    mismatches = [
        finding for finding in findings if finding.code == "COMMITTED_IDENTITY_MISMATCH"
    ]
    assert len(mismatches) == 37
    assert all(finding.resolution_status == "unresolved" for finding in mismatches)
    assert "COMMITTED_IDENTITY_CORRECTION_INVALID" in codes(findings)
    assert len(transition_targets) == 6


def test_committed_identity_correction_requires_exact_v4_bundle(
    repository_root: Path,
) -> None:
    profile, approvals = correction_inputs(repository_root)
    approvals.pop(APPROVAL_PATHS[1])
    findings, _ = validate_committed_identity_correction(
        GitReader(repository_root), "HEAD", PROGRAM_ROOT, profile, approvals
    )
    assert "COMMITTED_IDENTITY_CORRECTION_UNAUTHORIZED" in codes(findings)
    assert all(
        finding.resolution_status == "unresolved"
        for finding in findings
        if finding.code == "COMMITTED_IDENTITY_MISMATCH"
    )


def test_committed_identity_correction_rejects_every_closed_target_class(
    repository_root: Path,
) -> None:
    profile, approvals = correction_inputs(repository_root)
    head = GitReader(repository_root).resolve_commit("HEAD")
    mutations = (
        (
            "added",
            lambda value: value["transition_digest_claims"].append(
                copy.deepcopy(value["transition_digest_claims"][0])
            ),
        ),
        ("omitted", lambda value: value["historical_state_tree_claims"].pop()),
        (
            "reordered",
            lambda value: value["transition_digest_claims"].__setitem__(
                slice(0, 2), value["transition_digest_claims"][:2][::-1]
            ),
        ),
        (
            "substituted",
            lambda value: value["transition_digest_claims"][0]["target"].__setitem__(
                "artifact_path",
                value["transition_digest_claims"][4]["target"]["artifact_path"],
            ),
        ),
        (
            "wildcard",
            lambda value: value["transition_digest_claims"][0].__setitem__(
                "json_pointer", "/outputs/*/sha256"
            ),
        ),
        (
            "range",
            lambda value: value["transition_digest_claims"][0].__setitem__(
                "json_pointer", "/outputs/0-2/sha256"
            ),
        ),
        (
            "same",
            lambda value: value["transition_digest_claims"][0]["target"].__setitem__(
                "introducing_commit", CORRECTION_SUBJECT
            ),
        ),
        (
            "future",
            lambda value: value["transition_digest_claims"][0]["target"].__setitem__(
                "introducing_commit", head
            ),
        ),
        (
            "correction",
            lambda value: value["transition_digest_claims"][0]["target"].__setitem__(
                "artifact_path", CORRECTION_PATH
            ),
        ),
        (
            "authority",
            lambda value: value["transition_digest_claims"][0]["target"].__setitem__(
                "artifact_path", APPROVAL_PATHS[0]
            ),
        ),
        (
            "readiness",
            lambda value: value["transition_digest_claims"][0]["target"].__setitem__(
                "artifact_path", f"{PROGRAM_ROOT}/gate-evidence.json"
            ),
        ),
        (
            "gate",
            lambda value: value["transition_digest_claims"][0]["target"].__setitem__(
                "artifact_path", f"{PROGRAM_ROOT}/gate-catalog.json"
            ),
        ),
        (
            "benchmark",
            lambda value: value["transition_digest_claims"][0]["target"].__setitem__(
                "artifact_path", f"{PROGRAM_ROOT}/benchmark/coverage-matrix.json"
            ),
        ),
        (
            "freshness",
            lambda value: value["transition_digest_claims"][0].__setitem__(
                "json_pointer", "/freshness/status"
            ),
        ),
        (
            "candidate",
            lambda value: value["transition_digest_claims"][0].__setitem__(
                "json_pointer", "/subject/git_commit"
            ),
        ),
        (
            "release",
            lambda value: value["transition_digest_claims"][0]["target"].__setitem__(
                "artifact_path", f"{PROGRAM_ROOT}/evidence/approvals/release.json"
            ),
        ),
    )
    reader = GitReader(repository_root)
    for label, mutate in mutations:
        candidate = copy.deepcopy(profile)
        mutate(candidate)
        findings, targets = validate_committed_identity_correction(
            reader, "HEAD", PROGRAM_ROOT, candidate, approvals
        )
        mismatches = [
            finding
            for finding in findings
            if finding.code == "COMMITTED_IDENTITY_MISMATCH"
        ]
        assert len(mismatches) == 37, label
        assert all(
            finding.resolution_status == "unresolved" for finding in mismatches
        ), label
        assert "COMMITTED_IDENTITY_CORRECTION_INVALID" in codes(findings), label
        assert len(targets) == 6, label


def test_committed_identity_correction_rejects_identity_substitutions(
    repository_root: Path,
) -> None:
    profile, approvals = correction_inputs(repository_root)
    mutations = (
        lambda value: value["transition_digest_claims"][0]["target"].__setitem__(
            "artifact_raw_sha256", "0" * 64
        ),
        lambda value: value["transition_digest_claims"][0]["target"].__setitem__(
            "artifact_git_blob", "0" * 40
        ),
        lambda value: value["transition_digest_claims"][0]["target"].__setitem__(
            "introducing_tree", "0" * 40
        ),
        lambda value: value["transition_digest_claims"][0].__setitem__(
            "recorded_value", "0" * 64
        ),
        lambda value: value["transition_digest_claims"][0].__setitem__(
            "authoritative_value", "0" * 64
        ),
        lambda value: value["historical_state_tree_claims"][0].__setitem__(
            "canonical_state_digest", "0" * 64
        ),
        lambda value: value["tree_resolution"].__setitem__(
            "authoritative_value", "0" * 40
        ),
    )
    reader = GitReader(repository_root)
    for mutate in mutations:
        candidate = copy.deepcopy(profile)
        mutate(candidate)
        findings, _ = validate_committed_identity_correction(
            reader, "HEAD", PROGRAM_ROOT, candidate, approvals
        )
        assert "COMMITTED_IDENTITY_CORRECTION_INVALID" in codes(findings)
        assert (
            sum(finding.code == "COMMITTED_IDENTITY_MISMATCH" for finding in findings)
            == 37
        )


def test_committed_identity_correction_rejects_v4_authority_variants(
    repository_root: Path,
) -> None:
    profile, approvals = correction_inputs(repository_root)
    mutations = (
        lambda value: value[APPROVAL_PATHS[0]].__setitem__("scope", "release"),
        lambda value: value[APPROVAL_PATHS[0]].__setitem__(
            "bundle_id", "APB-EPP-F01-005"
        ),
        lambda value: value[APPROVAL_PATHS[0]]["subject"].__setitem__(
            "git_commit", "0" * 40
        ),
        lambda value: value[APPROVAL_PATHS[0]]["subject"]["artifact_digests"][
            8
        ].__setitem__("sha256", "0" * 64),
        lambda value: value[APPROVAL_PATHS[0]].__setitem__(
            "expires_at", "2026-08-27T16:24:46Z"
        ),
        lambda value: value[APPROVAL_PATHS[0]]["revocation_events"].append(
            {"revoked_at": "2026-08-27T16:24:46Z"}
        ),
        lambda value: value[APPROVAL_PATHS[0]].__setitem__(
            "conditions", ["Benchmark execution authorized"]
        ),
        lambda value: value[APPROVAL_PATHS[0]].__setitem__(
            "approver", "substituted approver"
        ),
        lambda value: value[APPROVAL_PATHS[0]].__setitem__(
            "review", {"due_at": None, "last_reviewed_at": None}
        ),
    )
    reader = GitReader(repository_root)
    for mutate in mutations:
        candidate = copy.deepcopy(approvals)
        mutate(candidate)
        findings, _ = validate_committed_identity_correction(
            reader, "HEAD", PROGRAM_ROOT, profile, candidate
        )
        assert "COMMITTED_IDENTITY_CORRECTION_UNAUTHORIZED" in codes(findings)
        assert all(
            finding.resolution_status == "unresolved"
            for finding in findings
            if finding.code == "COMMITTED_IDENTITY_MISMATCH"
        )


def test_committed_identity_correction_rejects_valid_digest_manifest_substitution(
    repository_root: Path,
) -> None:
    profile, approvals = correction_inputs(repository_root)
    reader = GitReader(repository_root)
    substitute_path = "benchmark-coverage.json"
    substitute_digest = sha256_bytes(
        reader.blob(CORRECTION_SUBJECT, f"{PROGRAM_ROOT}/{substitute_path}")
    )
    candidate = copy.deepcopy(approvals)
    for approval in candidate.values():
        approval["subject"]["artifact_digests"][0] = {
            "path": substitute_path,
            "sha256": substitute_digest,
        }
        approval["conditions"] = ["Benchmark execution authorized"]
    findings, _ = validate_committed_identity_correction(
        reader, "HEAD", PROGRAM_ROOT, profile, candidate
    )
    assert "COMMITTED_IDENTITY_CORRECTION_UNAUTHORIZED" in codes(findings)
    assert all(
        finding.resolution_status == "unresolved"
        for finding in findings
        if finding.code == "COMMITTED_IDENTITY_MISMATCH"
    )


def test_committed_identity_correction_is_readiness_neutral(
    repository_root: Path,
) -> None:
    profile, approvals = correction_inputs(repository_root)
    catalog = load(repository_root / PROGRAM_ROOT / "gate-catalog.json")
    evidence = load(repository_root / PROGRAM_ROOT / "gate-evidence.json")
    assert isinstance(catalog, dict)
    assert isinstance(evidence, dict)
    original_catalog = copy.deepcopy(catalog)
    original_evidence = copy.deepcopy(evidence)
    observed = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)
    areas_before = derive_areas(catalog, evidence, observed)
    findings, _ = validate_committed_identity_correction(
        GitReader(repository_root), "HEAD", PROGRAM_ROOT, profile, approvals
    )
    areas_after = derive_areas(catalog, evidence, observed)
    assert areas_after == areas_before
    assert catalog == original_catalog
    assert evidence == original_evidence
    assert all(
        "/evidence/transitions/" in finding.artifact
        or "/evidence/states/" in finding.artifact
        for finding in findings
    )


def test_exact_two_closed_profiles_validate_against_approval_subject(
    repository_root: Path,
) -> None:
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
        (lambda value: value["profiles"].pop(), "LEGACY_PROFILE_COUNT"),
        (
            lambda value: value["profiles"].append(copy.deepcopy(value["profiles"][0])),
            "LEGACY_PROFILE_COUNT",
        ),
        (
            lambda value: value["profiles"][1].__setitem__("from_revision", 11),
            "LEGACY_PROFILE_RANGE",
        ),
        (lambda value: value["profiles"][1]["states"].pop(3), "LEGACY_PROFILE_RANGE"),
        (
            lambda value: value["profiles"][1]["transitions"].pop(3),
            "LEGACY_PROFILE_RANGE",
        ),
        (
            lambda value: value["profiles"][1]["states"][0].__setitem__(
                "path", value["profiles"][0]["states"][0]["path"]
            ),
            "LEGACY_PATH_DUPLICATE",
        ),
        (
            lambda value: value["profiles"][1]["states"][0].__setitem__(
                "path", "program-state.json"
            ),
            "LEGACY_PATH_MUTABLE",
        ),
        (
            lambda value: value["profiles"][0]["transitions"][0].__setitem__(
                "raw_sha256", None
            ),
            "LEGACY_RAW_RULE_INVALID",
        ),
        (
            lambda value: value["profiles"][1]["transitions"][-1].__setitem__(
                "raw_sha256", "0" * 64
            ),
            "LEGACY_RAW_RULE_INVALID",
        ),
        (
            lambda value: value["profiles"][1]["transitions"][0].__setitem__(
                "prior_state_digest", "0" * 64
            ),
            "LEGACY_TRANSITION_METADATA_MISMATCH",
        ),
        (
            lambda value: value["profiles"][1].__setitem__(
                "checkpoint_commit", APPROVED_SUBJECT
            ),
            "LEGACY_CHECKPOINT_INVALID",
        ),
        (
            lambda value: value["profiles"][1].__setitem__(
                "terminal_feature_state", "IMPLEMENTING"
            ),
            "LEGACY_TERMINAL_MISMATCH",
        ),
        (
            lambda value: value["profiles"][1]["successor"].__setitem__(
                "maximum_count", 2
            ),
            "LEGACY_SUCCESSOR_INVALID",
        ),
    ],
)
def test_closed_profile_shape_rejects_expansion(
    repository_root: Path, mutator, expected: str
) -> None:
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
    findings = validate_legacy_profiles(
        reader, APPROVED_SUBJECT, PROGRAM_ROOT, profile_set(repository_root)
    )
    assert "LEGACY_BLOB_MISMATCH" in codes(findings)


def test_current_v2_chain_has_exact_legal_edges(repository_root: Path) -> None:
    root = repository_root / PROGRAM_ROOT
    documents = {
        f"{PROGRAM_ROOT}/{path.relative_to(root).as_posix()}": load(path)
        for directory in (root / "evidence/states", root / "evidence/transitions")
        for path in directory.glob("*.json")
    }
    documents[f"{PROGRAM_ROOT}/program-state.json"] = load(root / "program-state.json")
    documents[f"{PROGRAM_ROOT}/lifecycle-policy.json"] = load(
        root / "lifecycle-policy.json"
    )
    findings = []
    _validate_state_chain(
        documents,
        PROGRAM_ROOT,
        findings,
        corrected_event_targets=CHECKPOINT_EVENT_TARGETS,
    )
    assert findings == []


def test_illegal_feature_edge_and_second_v2_migration_fail(
    repository_root: Path,
) -> None:
    root = repository_root / PROGRAM_ROOT
    documents = {
        f"{PROGRAM_ROOT}/{path.relative_to(root).as_posix()}": load(path)
        for directory in (root / "evidence/states", root / "evidence/transitions")
        for path in directory.glob("*.json")
    }
    documents[f"{PROGRAM_ROOT}/program-state.json"] = load(root / "program-state.json")
    documents[f"{PROGRAM_ROOT}/lifecycle-policy.json"] = load(
        root / "lifecycle-policy.json"
    )
    documents[f"{PROGRAM_ROOT}/evidence/transitions/TR-0020.json"] = copy.deepcopy(
        documents[f"{PROGRAM_ROOT}/evidence/transitions/TR-0020.json"]
    )
    documents[f"{PROGRAM_ROOT}/evidence/transitions/TR-0020.json"]["to_state"] = (
        "VERIFIED"
    )
    duplicate = copy.deepcopy(
        documents[f"{PROGRAM_ROOT}/evidence/transitions/TR-0019.json"]
    )
    duplicate["transition_id"] = "TR-0021"
    documents[f"{PROGRAM_ROOT}/evidence/transitions/TR-0021.json"] = duplicate
    findings = []
    _validate_state_chain(documents, PROGRAM_ROOT, findings)
    assert {"LIFECYCLE_EDGE_INVALID", "LEGACY_MIGRATION_COUNT"}.issubset(
        codes(findings)
    )


def _committed_v2_transition(git_builder) -> tuple[GitReader, str, dict]:
    prior = {"schema_version": "2.0", "revision": 1, "state": "PROGRAM_ACTIVE"}
    prior_raw = (json.dumps(prior, sort_keys=True) + "\n").encode()
    prior_path = f"{PROGRAM_ROOT}/evidence/states/program-state-revision-0001.json"
    git_builder.write_bytes(prior_path, prior_raw)
    source = git_builder.commit("source")
    source_tree = git_builder.git_output("show", "-s", "--format=%T", source)
    source_program_tree = git_builder.git_output(
        "rev-parse", f"{source}:{PROGRAM_ROOT}"
    )

    new = {"schema_version": "2.0", "revision": 2, "state": "PROGRAM_ACTIVE"}
    new_raw = (json.dumps(new, sort_keys=True) + "\n").encode()
    new_path = f"{PROGRAM_ROOT}/evidence/states/program-state-revision-0002.json"
    transition_path = f"{PROGRAM_ROOT}/evidence/transitions/TR-0001.json"
    transition = {
        "schema_version": "2.0",
        "transition_id": "TR-0001",
        "prior_revision": 1,
        "new_revision": 2,
        "prior_state_digest": canonical_digest(prior),
        "new_state_digest": canonical_digest(new),
        "git": {
            "source_commit": source,
            "source_tree": source_tree,
            "source_program_tree": source_program_tree,
            "containing_commit": None,
            "containing_commit_rule": "transition_blob_container",
            "changed_paths_manifest": sorted([new_path, transition_path]),
            "transition_path": "evidence/transitions/TR-0001.json",
        },
        "inputs": [
            {
                "path": "evidence/states/program-state-revision-0001.json",
                "sha256": sha256_bytes(prior_raw),
            }
        ],
        "outputs": [
            {
                "path": "evidence/states/program-state-revision-0002.json",
                "sha256": sha256_bytes(new_raw),
            }
        ],
    }
    git_builder.write_bytes(new_path, new_raw)
    git_builder.write_json(transition_path, transition)
    container = git_builder.commit("transition")
    return GitReader(git_builder.root), container, transition


def test_v2_transition_binds_exact_source_container_manifest_and_digests(
    git_builder,
) -> None:
    reader, container, transition = _committed_v2_transition(git_builder)
    findings = []
    _validate_transition_history(
        reader, container, [transition], PROGRAM_ROOT, findings
    )
    assert findings == []


def test_v2_transition_rejects_incomplete_manifest_and_raw_digest_drift(
    git_builder,
) -> None:
    reader, container, transition = _committed_v2_transition(git_builder)
    transition = copy.deepcopy(transition)
    transition["git"]["changed_paths_manifest"].pop(0)
    transition["outputs"][0]["sha256"] = "0" * 64
    findings = []
    _validate_transition_history(
        reader, container, [transition], PROGRAM_ROOT, findings
    )
    assert {
        "TRANSITION_MANIFEST_MISMATCH",
        "TRANSITION_ARTIFACT_DIGEST_MISMATCH",
    }.issubset(codes(findings))


def test_v2_transition_blob_is_append_only_after_its_container(git_builder) -> None:
    reader, _, transition = _committed_v2_transition(git_builder)
    path = f"{PROGRAM_ROOT}/evidence/transitions/TR-0001.json"
    target = git_builder.root / path
    target.write_bytes(target.read_bytes() + b" ")
    current = git_builder.commit("illegal transition rewrite")
    findings = []
    _validate_transition_history(reader, current, [transition], PROGRAM_ROOT, findings)
    assert "TRANSITION_BLOB_CHANGED" in codes(findings)
