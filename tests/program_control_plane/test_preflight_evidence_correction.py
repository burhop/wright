"""Exact closed-profile tests for the EPP-F01 V9 preflight correction."""

from __future__ import annotations

import copy
import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from program_control import validation as validation_module
from program_control.git_subject import GitReader
from program_control.validation import validate_program


PROGRAM_ROOT = "docs/programs/engineering-process-platform"
CORRECTION_ID = "COR-EPP-F01-V9-PREFLIGHT-EVIDENCE-001"
CORRECTION_PATH = f"{PROGRAM_ROOT}/evidence/corrections/{CORRECTION_ID}.json"
APPROVAL_PATHS = (
    f"{PROGRAM_ROOT}/evidence/approvals/APR-EPP-F01-MC-009.json",
    f"{PROGRAM_ROOT}/evidence/approvals/APR-EPP-F01-IMPL-009.json",
)
DISCOVERY_PATH = f"{PROGRAM_ROOT}/evidence/verification/EPP-F01-V8-discovery.json"
TR0051_PATH = f"{PROGRAM_ROOT}/evidence/transitions/TR-0051.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def correction_inputs(repository_root: Path) -> tuple[dict, dict[str, dict]]:
    profile = load(repository_root / CORRECTION_PATH)
    approvals = {path: load(repository_root / path) for path in APPROVAL_PATHS}
    return profile, approvals


def validate(
    repository_root: Path, profile: dict, approvals: dict[str, dict], *, reader=None
):
    function = getattr(validation_module, "validate_preflight_evidence_correction")
    return function(
        reader or GitReader(repository_root),
        "HEAD",
        PROGRAM_ROOT,
        profile,
        approvals,
    )


def codes(findings) -> set[str]:
    return {finding.code for finding in findings}


def test_exact_v9_profile_resolves_only_two_original_findings(
    repository_root: Path,
) -> None:
    profile, approvals = correction_inputs(repository_root)
    original_profile = copy.deepcopy(profile)
    original_approvals = copy.deepcopy(approvals)

    findings, schema_targets, manifest_targets = validate(
        repository_root, profile, approvals
    )

    assert [(item.code, item.artifact, item.json_pointer) for item in findings] == [
        ("SCHEMA_REFERENCE_MISSING", DISCOVERY_PATH, "/$schema"),
        (
            "TRANSITION_MANIFEST_MISMATCH",
            TR0051_PATH,
            "/git/changed_paths_manifest",
        ),
    ]
    assert all(item.resolution_status == "resolved" for item in findings)
    assert all(item.correction_ref == CORRECTION_PATH for item in findings)
    assert all(
        "inspect the exact approved V9 preflight" in item.recovery for item in findings
    )
    assert schema_targets == frozenset({DISCOVERY_PATH})
    assert manifest_targets == frozenset({TR0051_PATH})
    assert profile == original_profile
    assert approvals == original_approvals


def _profile_mutations(head: str):
    return (
        (
            "wrong-source-commit",
            lambda value: value["source_checkpoint"].__setitem__(
                "git_commit", "0" * 40
            ),
        ),
        (
            "wrong-source-tree",
            lambda value: value["source_checkpoint"].__setitem__("git_tree", "0" * 40),
        ),
        (
            "wrong-source-program-tree",
            lambda value: value["source_checkpoint"].__setitem__(
                "program_tree", "0" * 40
            ),
        ),
        ("missing-claim", lambda value: value["claims"].pop()),
        (
            "extra-claim",
            lambda value: value["claims"].append(copy.deepcopy(value["claims"][0])),
        ),
        ("reordered-claims", lambda value: value["claims"].reverse()),
        (
            "wrong-artifact-path",
            lambda value: value["claims"][0].__setitem__(
                "artifact_path", f"{PROGRAM_ROOT}/program-state.json"
            ),
        ),
        (
            "wrong-transition-path",
            lambda value: value["claims"][1].__setitem__(
                "transition_path", f"{PROGRAM_ROOT}/evidence/transitions/TR-0050.json"
            ),
        ),
        (
            "wrong-schema-pointer",
            lambda value: value["claims"][0].__setitem__("json_pointer", "/schema"),
        ),
        (
            "wrong-manifest-pointer",
            lambda value: value["claims"][1].__setitem__(
                "json_pointer", "/git/changed_paths"
            ),
        ),
        (
            "wildcard-pointer",
            lambda value: value["claims"][1].__setitem__("json_pointer", "/git/*"),
        ),
        (
            "wrong-artifact-raw-sha",
            lambda value: value["claims"][0].__setitem__(
                "artifact_raw_sha256", "0" * 64
            ),
        ),
        (
            "wrong-artifact-blob",
            lambda value: value["claims"][0].__setitem__("artifact_git_blob", "0" * 40),
        ),
        (
            "wrong-transition-raw-sha",
            lambda value: value["claims"][1].__setitem__(
                "transition_raw_sha256", "0" * 64
            ),
        ),
        (
            "wrong-transition-blob",
            lambda value: value["claims"][1].__setitem__(
                "transition_git_blob", "0" * 40
            ),
        ),
        (
            "wrong-introducing-commit",
            lambda value: value["claims"][0].__setitem__("introducing_commit", head),
        ),
        (
            "wrong-introducing-tree",
            lambda value: value["claims"][1].__setitem__("introducing_tree", "0" * 40),
        ),
        (
            "wrong-introducing-program-tree",
            lambda value: value["claims"][1].__setitem__(
                "introducing_program_tree", "0" * 40
            ),
        ),
        (
            "wrong-recorded-count",
            lambda value: value["claims"][1].__setitem__("recorded_manifest_count", 34),
        ),
        (
            "wrong-unique-count",
            lambda value: value["claims"][1].__setitem__("recorded_unique_count", 34),
        ),
        (
            "wrong-recorded-digest",
            lambda value: value["claims"][1].__setitem__(
                "recorded_manifest_digest", "0" * 64
            ),
        ),
        (
            "wrong-sorted-digest",
            lambda value: value["claims"][1].__setitem__(
                "authoritative_sorted_manifest_digest", "0" * 64
            ),
        ),
        (
            "wrong-container-digest",
            lambda value: value["claims"][1].__setitem__(
                "container_changed_paths_digest", "0" * 64
            ),
        ),
        (
            "wrong-self-path",
            lambda value: value["claims"][1].__setitem__(
                "transition_self_path", TR0051_PATH + ".other"
            ),
        ),
        (
            "wrong-recorded-self-index",
            lambda value: value["claims"][1].__setitem__("recorded_self_path_index", 9),
        ),
        (
            "wrong-sorted-self-index",
            lambda value: value["claims"][1].__setitem__("sorted_self_path_index", 34),
        ),
        (
            "set-not-equal",
            lambda value: value["claims"][1].__setitem__("complete_set_equal", False),
        ),
        (
            "duplicate-present",
            lambda value: value["claims"][1].__setitem__("duplicates_present", True),
        ),
        (
            "missing-path",
            lambda value: value["claims"][1]["missing_paths"].append(TR0051_PATH),
        ),
        (
            "extra-path",
            lambda value: value["claims"][1]["extra_paths"].append("extra.json"),
        ),
        (
            "wrong-external-schema-path",
            lambda value: value["claims"][0].__setitem__(
                "external_schema_path",
                f"{PROGRAM_ROOT}/schemas/program-state.schema.json",
            ),
        ),
        (
            "wrong-planning-schema-path",
            lambda value: value["claims"][0].__setitem__(
                "planning_schema_path",
                "specs/076-control-plane-validator/contracts/program-state.schema.json",
            ),
        ),
        (
            "wrong-external-schema-id",
            lambda value: value["claims"][0].__setitem__(
                "external_schema_id", "https://wright.local/other.json"
            ),
        ),
        (
            "wrong-external-schema-sha",
            lambda value: value["claims"][0].__setitem__(
                "external_schema_raw_sha256", "0" * 64
            ),
        ),
        (
            "wrong-external-schema-blob",
            lambda value: value["claims"][0].__setitem__(
                "external_schema_git_blob", "0" * 40
            ),
        ),
        (
            "schema-inference",
            lambda value: value["resolution_semantics"].__setitem__(
                "no_generic_schema_or_manifest_exception", False
            ),
        ),
        (
            "projection-interference",
            lambda value: value["resolution_semantics"].__setitem__(
                "readiness_authority_benchmark_release_non_interference", False
            ),
        ),
        ("future-record", lambda value: value.__setitem__("accept_new_records", True)),
        (
            "correction-of-correction",
            lambda value: value["claims"][0].__setitem__(
                "artifact_path", CORRECTION_PATH
            ),
        ),
    )


def test_v9_profile_rejects_every_claim_identity_and_semantic_near_miss(
    repository_root: Path,
) -> None:
    profile, approvals = correction_inputs(repository_root)
    head = GitReader(repository_root).resolve_commit("HEAD")
    for label, mutate in _profile_mutations(head):
        candidate = copy.deepcopy(profile)
        mutate(candidate)
        findings, schema_targets, manifest_targets = validate(
            repository_root, candidate, approvals
        )
        original = [
            finding
            for finding in findings
            if finding.code
            in {"SCHEMA_REFERENCE_MISSING", "TRANSITION_MANIFEST_MISMATCH"}
        ]
        assert len(original) == 2, label
        assert all(finding.resolution_status == "unresolved" for finding in original), (
            label
        )
        assert "PREFLIGHT_EVIDENCE_CORRECTION_INVALID" in codes(findings), label
        assert schema_targets == frozenset(), label
        assert manifest_targets == frozenset(), label


@pytest.mark.parametrize(
    "mutation",
    [
        lambda approvals: approvals.pop(APPROVAL_PATHS[0]),
        lambda approvals: approvals.pop(APPROVAL_PATHS[1]),
        lambda approvals: approvals[APPROVAL_PATHS[0]]["subject"].__setitem__(
            "git_commit", "0" * 40
        ),
        lambda approvals: approvals[APPROVAL_PATHS[1]]["subject"]["artifact_digests"][
            0
        ].__setitem__("sha256", "0" * 64),
        lambda approvals: approvals[APPROVAL_PATHS[0]].__setitem__(
            "scope", "feature_implementation"
        ),
        lambda approvals: approvals[APPROVAL_PATHS[0]].__setitem__(
            "decision", "rejected"
        ),
        lambda approvals: approvals[APPROVAL_PATHS[0]].__setitem__(
            "expires_at", "2026-08-28T00:00:00Z"
        ),
        lambda approvals: approvals[APPROVAL_PATHS[0]]["revocation_events"].append(
            {"revoked_at": "2026-08-28T00:00:00Z"}
        ),
        lambda approvals: approvals[APPROVAL_PATHS[0]].__setitem__(
            "bundle_id", "APB-EPP-F01-OTHER"
        ),
    ],
)
def test_v9_profile_requires_exact_current_two_scope_authority(
    repository_root: Path, mutation
) -> None:
    profile, approvals = correction_inputs(repository_root)
    mutation(approvals)
    findings, schema_targets, manifest_targets = validate(
        repository_root, profile, approvals
    )
    assert "PREFLIGHT_EVIDENCE_CORRECTION_UNAUTHORIZED" in codes(findings)
    assert all(
        finding.resolution_status == "unresolved"
        for finding in findings
        if finding.code in {"SCHEMA_REFERENCE_MISSING", "TRANSITION_MANIFEST_MISMATCH"}
    )
    assert schema_targets == frozenset()
    assert manifest_targets == frozenset()


class BlobMutatingReader:
    def __init__(
        self, delegate: GitReader, target: str, replacement: bytes | None = None
    ):
        self.delegate = delegate
        self.target = target
        self.replacement = replacement

    def __getattr__(self, name):
        return getattr(self.delegate, name)

    def _mutate(self, path: str, raw: bytes) -> bytes:
        if path != self.target:
            return raw
        return self.replacement if self.replacement is not None else raw + b" "

    def blob(self, commit: str, path: str) -> bytes:
        return self._mutate(path, self.delegate.blob(commit, path))

    def read_blob_requests(self, requests):
        values = self.delegate.read_blob_requests(requests)
        return {key: self._mutate(key[1], raw) for key, raw in values.items()}

    def read_blobs(self, commit: str, paths):
        values = self.delegate.read_blobs(commit, paths)
        return {path: self._mutate(path, raw) for path, raw in values.items()}


@pytest.mark.parametrize(
    "target,replacement",
    [
        (DISCOVERY_PATH, None),
        (TR0051_PATH, None),
        (f"{PROGRAM_ROOT}/schemas/v8-discovery-evidence.schema.json", None),
        (
            "specs/076-control-plane-validator/contracts/v8-discovery-evidence.schema.json",
            None,
        ),
        (f"{PROGRAM_ROOT}/schemas/preflight-evidence-correction.schema.json", None),
        (
            "specs/076-control-plane-validator/contracts/preflight-evidence-correction.schema.json",
            None,
        ),
        (CORRECTION_PATH, None),
    ],
)
def test_v9_profile_recomputes_blobs_and_rejects_schema_divergence(
    repository_root: Path, target: str, replacement: bytes | None
) -> None:
    profile, approvals = correction_inputs(repository_root)
    reader = BlobMutatingReader(GitReader(repository_root), target, replacement)
    findings, schema_targets, manifest_targets = validate(
        repository_root, profile, approvals, reader=reader
    )
    assert "PREFLIGHT_EVIDENCE_CORRECTION_INVALID" in codes(findings)
    assert schema_targets == frozenset()
    assert manifest_targets == frozenset()


class NonAncestorReader:
    def __init__(self, delegate: GitReader):
        self.delegate = delegate

    def __getattr__(self, name):
        return getattr(self.delegate, name)

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        return False


def test_v9_profile_requires_strict_ancestry_and_supported_reader(
    repository_root: Path,
) -> None:
    profile, approvals = correction_inputs(repository_root)
    findings, schema_targets, manifest_targets = validate(
        repository_root,
        profile,
        approvals,
        reader=NonAncestorReader(GitReader(repository_root)),
    )
    assert "PREFLIGHT_EVIDENCE_CORRECTION_INVALID" in codes(findings)
    assert schema_targets == frozenset()
    assert manifest_targets == frozenset()


@pytest.mark.parametrize(
    "benchmark_summary",
    [
        {
            "counted": 0,
            "target": 100,
            "first_attempt_passed": 0,
            "eventual_passed": 0,
            "failed": 0,
            "blocked": 0,
            "stale": 0,
            "contaminated": 0,
            "not_tested": 100,
            "t0": 0,
            "t1": 0,
            "t2": 0,
            "t3": 0,
            "coverage_deficits": ["BENCHMARK_COVERAGE_EMPTY"],
            "oracle_deficits": ["BENCHMARK_ORACLES_ABSENT"],
            "artifact_deficits": ["BENCHMARK_ARTIFACTS_ABSENT"],
            "partition_deficits": ["BENCHMARK_PARTITIONS_ABSENT"],
            "freshness_deficits": ["BENCHMARK_EVIDENCE_ABSENT"],
        },
        {
            "counted": 4,
            "target": 100,
            "first_attempt_passed": 1,
            "eventual_passed": 2,
            "failed": 1,
            "blocked": 1,
            "stale": 0,
            "contaminated": 0,
            "not_tested": 96,
            "t0": 2,
            "t1": 1,
            "t2": 1,
            "t3": 0,
            "coverage_deficits": ["COVERAGE_REMAINS"],
            "oracle_deficits": [],
            "artifact_deficits": [],
            "partition_deficits": ["HOLDOUT_REMAINS"],
            "freshness_deficits": [],
        },
    ],
)
def test_v9_disposition_cannot_change_policy_readiness_benchmark_or_release(
    repository_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    benchmark_summary: dict,
) -> None:
    profile, _ = correction_inputs(repository_root)
    assert (
        profile["resolution_semantics"][
            "readiness_authority_benchmark_release_non_interference"
        ]
        is True
    )
    original = validation_module.validate_preflight_evidence_correction
    monkeypatch.setattr(
        validation_module,
        "derive_benchmark_summary",
        lambda *_args, **_kwargs: copy.deepcopy(benchmark_summary),
    )

    def run(*, correction_on: bool) -> dict:
        def disposition(*args, **kwargs):
            findings, schema_targets, manifest_targets = original(*args, **kwargs)
            if correction_on:
                return findings, schema_targets, manifest_targets
            unresolved = [
                replace(
                    finding,
                    severity="fatal",
                    resolution_status="unresolved",
                    correction_ref=None,
                )
                if finding.code
                in {"SCHEMA_REFERENCE_MISSING", "TRANSITION_MANIFEST_MISMATCH"}
                else finding
                for finding in findings
            ]
            return unresolved, frozenset(), frozenset()

        monkeypatch.setattr(
            validation_module,
            "validate_preflight_evidence_correction",
            disposition,
        )
        return validate_program(
            GitReader(repository_root),
            "HEAD",
            PROGRAM_ROOT,
            observed_at=datetime(2026, 8, 28, 12, 30, tzinfo=timezone.utc),
        ).report

    reader = GitReader(repository_root)
    source = reader.resolve_commit("HEAD")
    frozen_inputs = {
        "lifecycle_policy": reader.blob(
            source, f"{PROGRAM_ROOT}/lifecycle-policy.json"
        ),
        "dashboard": reader.blob(source, f"{PROGRAM_ROOT}/dashboard.json"),
        "coverage_matrix": reader.blob(
            source, f"{PROGRAM_ROOT}/benchmark-coverage.json"
        ),
    }
    correction_on = run(correction_on=True)
    correction_off = run(correction_on=False)

    def protected(report: dict) -> dict:
        return {
            "areas": report["areas"],
            "gate_rows": [
                gate for area in report["areas"].values() for gate in area["gates"]
            ],
            "benchmark_summary": report["benchmark_summary"],
            "roadmap_policy_result": {
                key: report["eligibility"][key]
                for key in ("roadmap_item", "allowed_actions")
            },
            "next_action": report["next_action"],
            "candidate_identity": report["subject"]["release_candidate"],
            "source_identity": {
                key: report["subject"][key]
                for key in ("source_commit", "source_tree", "program_tree")
            },
            "authoritative_input_manifest": report["subject"]["input_manifest"],
            "authoritative_input_manifest_digest": report["subject"][
                "input_manifest_digest"
            ],
            "approval_authority": report["release_approval"],
            "delivery": report["delivery"],
            "release_eligibility": report["release_eligible"],
        }

    assert protected(correction_on) == protected(correction_off)
    assert sum(len(area["gates"]) for area in correction_on["areas"].values()) == 34
    assert correction_on["benchmark_summary"] == benchmark_summary
    assert (
        reader.blob(source, f"{PROGRAM_ROOT}/lifecycle-policy.json")
        == frozen_inputs["lifecycle_policy"]
    )
    assert (
        reader.blob(source, f"{PROGRAM_ROOT}/dashboard.json")
        == frozen_inputs["dashboard"]
    )
    assert (
        reader.blob(source, f"{PROGRAM_ROOT}/benchmark-coverage.json")
        == frozen_inputs["coverage_matrix"]
    )
