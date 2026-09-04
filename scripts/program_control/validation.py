"""Semantic validation of committed program-control evidence."""

from __future__ import annotations

import copy
import posixpath
import re
import sys
from collections import defaultdict, deque
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from . import __version__
from .dashboard import (
    DashboardError,
    default_benchmark_summary,
    derive_areas,
    derive_benchmark_summary,
)
from .git_subject import HEX40, GitReader, GitSubjectError, normalize_repo_path
from .json_contracts import (
    ContractError,
    UnsupportedVersionError,
    canonical_digest,
    check_schema,
    exact_schema_instance,
    require_compatible_version,
    sha256_bytes,
    strict_loads,
    validate_schema,
)
from .model import Finding, ValidationResult


SAFE_CODE = re.compile(r"^[A-Z][A-Z0-9_-]{2,99}$")
LEGACY_STATE_PATH = re.compile(
    r"^evidence/states/program-state-revision-(?P<revision>[0-9]{4})\.json$"
)
LEGACY_TRANSITION_PATH = re.compile(
    r"^evidence/transitions/(?P<transition>TR-[0-9]{4})\.json$"
)
REQUIRED_JSON = (
    "program-state.json",
    "roadmap.json",
    "decision-register.json",
    "risk-register.json",
)
EPP_F01B_SCHEMA_ROUTED_DOCUMENTS = {
    "docs/programs/engineering-process-platform/work-registry.json": (
        "docs/programs/engineering-process-platform/schemas/work-registry.schema.json"
    ),
    "docs/programs/engineering-process-platform/use-case-registry.json": (
        "docs/programs/engineering-process-platform/schemas/use-case-registry.schema.json"
    ),
    "docs/programs/engineering-process-platform/test-run-ledger.json": (
        "docs/programs/engineering-process-platform/schemas/test-run-ledger.schema.json"
    ),
}


def _finding(
    code: str,
    severity: str,
    artifact: str,
    invariant: str,
    evidence: tuple[str, ...] = (),
    *,
    json_pointer: str | None = None,
    resolution_status: str = "unresolved",
    correction_ref: str | None = None,
) -> Finding:
    consequences = {
        "fatal": "The committed subject cannot be trusted.",
        "error": "The affected transition or action is not authorized.",
        "warning": "The evidence requires review before it can support a claim.",
        "info": "The observation does not block control-plane validation.",
    }
    recovery = {
        "SCHEMA_MAJOR_UNSUPPORTED": "Use an explicitly supported schema major or approve a migration.",
        "SCHEMA_MINOR_UNSUPPORTED": "Declare and test compatibility before accepting this minor version.",
        "JSON_DUPLICATE_KEY": "Remove the duplicate member and create new transition evidence.",
        "ROADMAP_CYCLE": "Break the dependency cycle and re-run analysis.",
        "APPROVAL_STALE": "Request a new approval for the exact unchanged subject.",
        "LEASE_IDENTITY_MISMATCH": "Reconcile the lease with the active feature and worktree.",
        "LEASE_GIT_IDENTITY_MISMATCH": "Correct the factual lease Git identity through an append-only governed repair.",
        "TRANSITION_ARTIFACT_DIGEST_MISMATCH": "Do not rewrite history; obtain approval for an append-only compatibility or repair rule.",
        "COMMITTED_IDENTITY_MISMATCH": "Do not rewrite history; inspect the exact approved correction evidence and recomputation.",
        "COMMITTED_IDENTITY_CORRECTION_INVALID": "Restore the exact closed correction profile or stop for a new material approval.",
        "COMMITTED_IDENTITY_CORRECTION_UNAUTHORIZED": "Provide the exact approved two-scope V4 authority bundle.",
        "TRANSITION_INPUT_ORIGIN_MISMATCH": "Do not rewrite history; inspect the exact approved TR-0027 input-origin disposition.",
        "TRANSITION_INPUT_CORRECTION_INVALID": "Restore the exact closed one-claim correction profile or stop for a new material approval.",
        "TRANSITION_INPUT_CORRECTION_UNAUTHORIZED": "Provide the exact approved two-scope V5 authority bundle.",
        "REPAIR_EVIDENCE_CAUSE_ID_MISMATCH": "Do not rewrite history; inspect the exact approved repair-evidence disposition.",
        "REPAIR_EVIDENCE_DIGEST_MISMATCH": "Do not rewrite history; inspect the exact approved repair-evidence disposition.",
        "REPAIR_EVIDENCE_CORRECTION_INVALID": "Restore the exact closed two-claim repair profile or stop for a new material approval.",
        "REPAIR_EVIDENCE_CORRECTION_UNAUTHORIZED": "Provide the exact approved two-scope V7 authority bundle.",
        "CHECKPOINT_OUTPUT_DIGEST_MISMATCH": "Do not rewrite history; inspect the exact approved V8 checkpoint-evidence disposition.",
        "CHECKPOINT_EVENT_RULE_MISMATCH": "Do not rewrite history; inspect the exact approved V8 checkpoint-evidence disposition.",
        "CHECKPOINT_EVIDENCE_CORRECTION_INVALID": "Restore the exact closed three-claim checkpoint profile or stop for a new material approval.",
        "CHECKPOINT_EVIDENCE_CORRECTION_UNAUTHORIZED": "Provide the exact approved two-scope V8 authority bundle.",
        "REV58_RAW_IDENTITY_REPAIR_INVALID": "Restore the exact authorized revision-58 raw-identity repair evidence or stop.",
        "F01B_ACTIVATION_CORRECTION_INVALID": "Restore the exact authorized three-claim TR-0070 correction or stop.",
        "F01B_LEASE_CHECKPOINT_CORRECTION_INVALID": "Restore the exact authorized revision-75 and TR-0074 three-claim correction or stop.",
    }.get(code, "Repair the smallest named invariant and rerun the validator.")
    return Finding(
        code=code if SAFE_CODE.fullmatch(code) else "INTERNAL_VALIDATION_FAILURE",
        severity=severity,
        artifact=artifact,
        invariant=invariant,
        evidence=evidence,
        consequence=consequences[severity],
        recovery=recovery,
        json_pointer=json_pointer,
        resolution_status=resolution_status,
        correction_ref=correction_ref,
    )


def _schema_path(document_path: str, schema_ref: str, program_root: str) -> str | None:
    if schema_ref.startswith("https://wright.local/programs/epp/"):
        return f"{program_root}/schemas/{schema_ref.rsplit('/', 1)[-1]}"
    if "://" in schema_ref:
        return None
    return normalize_repo_path(
        posixpath.normpath(posixpath.join(posixpath.dirname(document_path), schema_ref))
    )


def _enrich_input_manifest(
    reader: GitReader,
    commit: str,
    program_root: str,
    _base_manifest: Sequence[Mapping[str, str]],
    policy: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], str]:
    """Bind every program input to its first policy role and local schema identity."""
    return reader.authoritative_manifest(commit, program_root, policy)


def _validate_runtime_source_bundle(
    reader: GitReader,
    source_commit: str,
) -> tuple[list[dict[str, object]], str, list[Finding]]:
    """Bind loaded validator code and checkout state to the exact source bundle."""

    findings: list[Finding] = []
    try:
        manifest, digest = reader.source_bundle(source_commit)
        head_manifest, _ = reader.source_bundle(reader.current_head())
    except GitSubjectError:
        findings.append(
            _finding(
                "VALIDATOR_SOURCE_BUNDLE_INVALID",
                "fatal",
                "scripts/program_control",
                "CLOSED_SOURCE_BUNDLE",
            )
        )
        return [], "0" * 64, findings
    source_ids = {str(row["path"]): str(row["git_blob"]) for row in manifest}
    head_ids = {str(row["path"]): str(row["git_blob"]) for row in head_manifest}
    try:
        status_records = reader.status_for_paths(
            [
                "scripts/validate-engineering-process-program.py",
                "scripts/program_control",
            ]
        )
        dirty = [
            record
            for record in status_records
            if record.endswith(b".py")
            or b"scripts/validate-engineering-process-program.py" in record
        ]
    except GitSubjectError:
        dirty = [b"unresolved"]
    runtime_mismatch = source_ids != head_ids or bool(dirty)
    repository_root = reader.repo_root.resolve(strict=True)
    loaded_paths: set[str] = set()
    for name, module in sorted(sys.modules.items()):
        if name != "program_control" and not name.startswith("program_control."):
            continue
        module_file = getattr(module, "__file__", None)
        if not isinstance(module_file, str):
            runtime_mismatch = True
            continue
        try:
            relative = (
                Path(module_file).resolve(strict=True).relative_to(repository_root)
            )
            normalized = normalize_repo_path(relative.as_posix())
        except (OSError, ValueError, GitSubjectError):
            runtime_mismatch = True
            continue
        loaded_paths.add(normalized)
    if not loaded_paths.issubset(source_ids):
        runtime_mismatch = True
    if runtime_mismatch:
        findings.append(
            _finding(
                "VALIDATOR_RUNTIME_SUBJECT_MISMATCH",
                "fatal",
                "scripts/program_control",
                "RUNTIME_HEAD_SOURCE_BUNDLE_AND_LOADED_MODULES",
                (digest,),
            )
        )
    return manifest, digest, findings


def _load_json(
    reader: GitReader,
    commit: str,
    path: str,
    findings: list[Finding],
) -> Any | None:
    try:
        return strict_loads(reader.blob(commit, path))
    except ContractError as exc:
        code = (
            "JSON_DUPLICATE_KEY"
            if exc.__class__.__name__ == "DuplicateKeyError"
            else "JSON_INVALID"
        )
        findings.append(_finding(code, "fatal", path, "JSON_STRICT_PARSE"))
    except GitSubjectError:
        findings.append(
            _finding("ARTIFACT_MISSING", "fatal", path, "REQUIRED_ARTIFACT")
        )
    return None


def validate_legacy_profiles(
    reader: Any,
    approval_subject_commit: str,
    program_root: str,
    profile_set: Mapping[str, Any],
    *,
    observed_v1_revisions: Iterable[int] | None = None,
    migration_count: int = 1,
) -> list[Finding]:
    """Validate the only two accepted byte-bound v1 compatibility profiles."""

    findings: list[Finding] = []
    profiles = list(profile_set.get("profiles", []))
    if len(profiles) != 2:
        findings.append(
            _finding(
                "LEGACY_PROFILE_COUNT",
                "fatal",
                "lifecycle-policy.json",
                "EXACT_TWO_CLOSED_PROFILES",
            )
        )
    expected = (
        ("epp-bootstrap-v1-r1-r9", 1, 9, 1, 8),
        ("epp-bridge-v1-r10-r19", 10, 19, 9, 18),
    )
    all_paths: set[str] = set()
    state_digests: dict[int, str] = {}
    transition_rows: list[Mapping[str, Any]] = []
    for index, profile in enumerate(profiles[:2]):
        if not isinstance(profile, Mapping):
            findings.append(
                _finding(
                    "LEGACY_PROFILE_INVALID",
                    "fatal",
                    "lifecycle-policy.json",
                    "PROFILE_OBJECT",
                )
            )
            continue
        profile_id, first_state, last_state, first_transition, last_transition = (
            expected[index]
        )
        artifact = str(profile.get("profile_id", f"legacy-profile-{index}"))
        if (
            profile.get("profile_id") != profile_id
            or profile.get("from_revision") != first_state
            or profile.get("through_revision") != last_state
            or profile.get("schema_major") != 1
        ):
            findings.append(
                _finding(
                    "LEGACY_PROFILE_RANGE", "fatal", artifact, "CLOSED_PROFILE_RANGE"
                )
            )
        states = list(profile.get("states", []))
        if [row.get("revision") for row in states if isinstance(row, Mapping)] != list(
            range(first_state, last_state + 1)
        ):
            findings.append(
                _finding(
                    "LEGACY_PROFILE_RANGE", "fatal", artifact, "CONTIGUOUS_STATE_RANGE"
                )
            )
        transitions = list(profile.get("transitions", []))
        expected_ids = [
            f"TR-{number:04d}"
            for number in range(first_transition, last_transition + 1)
        ]
        if [
            row.get("transition_id") for row in transitions if isinstance(row, Mapping)
        ] != expected_ids:
            findings.append(
                _finding(
                    "LEGACY_PROFILE_RANGE",
                    "fatal",
                    artifact,
                    "CONTIGUOUS_TRANSITION_RANGE",
                )
            )
        # Both immutable profiles are materialized and byte-bound in the later
        # approved subject.  The first profile's fixed checkpoint identifies
        # its historical terminus; it is not a promise that the append-only
        # archive files had already been materialized in that older commit.
        effective_commit = approval_subject_commit
        if hasattr(reader, "read_blobs"):
            prefetch: list[str] = []
            for row in [*states, *transitions]:
                if not isinstance(row, Mapping):
                    continue
                try:
                    relative = normalize_repo_path(str(row.get("path")))
                except GitSubjectError:
                    continue
                prefetch.append(f"{program_root}/{relative}")
            reader.read_blobs(effective_commit, prefetch)
        for row in [*states, *transitions]:
            if not isinstance(row, Mapping):
                findings.append(
                    _finding(
                        "LEGACY_PROFILE_INVALID",
                        "fatal",
                        artifact,
                        "PROFILE_ROW_OBJECT",
                    )
                )
                continue
            profile_path_value = row.get("path")
            try:
                path = normalize_repo_path(str(profile_path_value))
            except GitSubjectError:
                findings.append(
                    _finding(
                        "LEGACY_PATH_UNSAFE",
                        "fatal",
                        artifact,
                        "NORMALIZED_PROFILE_PATH",
                    )
                )
                continue
            if path in all_paths:
                findings.append(
                    _finding(
                        "LEGACY_PATH_DUPLICATE",
                        "fatal",
                        artifact,
                        "UNIQUE_PROFILE_PATH",
                    )
                )
            all_paths.add(path)
            if "revision" in row:
                path_match = LEGACY_STATE_PATH.fullmatch(path)
                expected_revision = int(row.get("revision", -1))
                if (
                    path_match is None
                    or int(path_match.group("revision")) != expected_revision
                ):
                    findings.append(
                        _finding(
                            "LEGACY_PATH_MUTABLE",
                            "fatal",
                            path,
                            "IMMUTABLE_STATE_ARCHIVE_PATH",
                        )
                    )
            else:
                path_match = LEGACY_TRANSITION_PATH.fullmatch(path)
                if path_match is None or path_match.group("transition") != row.get(
                    "transition_id"
                ):
                    findings.append(
                        _finding(
                            "LEGACY_PATH_MUTABLE",
                            "fatal",
                            path,
                            "IMMUTABLE_TRANSITION_ARCHIVE_PATH",
                        )
                    )
            full_path = f"{program_root}/{path}"
            try:
                raw = reader.blob(effective_commit, full_path)
            except GitSubjectError:
                findings.append(
                    _finding(
                        "LEGACY_BLOB_MISSING", "fatal", path, "APPROVAL_SUBJECT_BLOB"
                    )
                )
                continue
            if "revision" in row:
                revision = int(row.get("revision", -1))
                state_digests[revision] = str(row.get("canonical_digest", ""))
                if sha256_bytes(raw) != row.get("raw_sha256"):
                    findings.append(
                        _finding(
                            "LEGACY_BLOB_MISMATCH", "fatal", path, "EXACT_STATE_BLOB"
                        )
                    )
                try:
                    if canonical_digest(strict_loads(raw)) != row.get(
                        "canonical_digest"
                    ):
                        findings.append(
                            _finding(
                                "STATE_DIGEST_MISMATCH",
                                "fatal",
                                path,
                                "LEGACY_CANONICAL_DIGEST",
                            )
                        )
                except ContractError:
                    findings.append(
                        _finding("JSON_INVALID", "fatal", path, "LEGACY_STATE_JSON")
                    )
            else:
                transition_rows.append(row)
                is_terminal_checkpoint = row.get("transition_id") == "TR-0018"
                expected_rule = (
                    "checkpoint_commit_blob"
                    if is_terminal_checkpoint
                    else "exact_blob_sha256"
                )
                if row.get("raw_sha256_rule") != expected_rule:
                    findings.append(
                        _finding(
                            "LEGACY_RAW_RULE_INVALID", "fatal", path, "CLOSED_RAW_RULE"
                        )
                    )
                if is_terminal_checkpoint:
                    if row.get("raw_sha256") is not None:
                        findings.append(
                            _finding(
                                "LEGACY_RAW_RULE_INVALID",
                                "fatal",
                                path,
                                "IMMUTABLE_NULL_CHECKPOINT",
                            )
                        )
                elif not isinstance(row.get("raw_sha256"), str):
                    findings.append(
                        _finding(
                            "LEGACY_RAW_RULE_INVALID",
                            "fatal",
                            path,
                            "EXACT_RAW_DIGEST_REQUIRED",
                        )
                    )
                elif sha256_bytes(raw) != row.get("raw_sha256"):
                    findings.append(
                        _finding(
                            "LEGACY_BLOB_MISMATCH",
                            "fatal",
                            path,
                            "EXACT_TRANSITION_BLOB",
                        )
                    )
                try:
                    transition_value = strict_loads(raw)
                except ContractError:
                    transition_value = None
                    findings.append(
                        _finding(
                            "JSON_INVALID", "fatal", path, "LEGACY_TRANSITION_JSON"
                        )
                    )
                compared_fields = (
                    "transition_id",
                    "prior_revision",
                    "new_revision",
                    "prior_state_digest",
                    "new_state_digest",
                )
                if not isinstance(transition_value, Mapping) or any(
                    transition_value.get(field) != row.get(field)
                    for field in compared_fields
                ):
                    findings.append(
                        _finding(
                            "LEGACY_TRANSITION_METADATA_MISMATCH",
                            "fatal",
                            path,
                            "PROFILE_TRANSITION_MATCHES_BLOB",
                        )
                    )
        if index == 0:
            expected_successor = {
                "kind": "closed_profile",
                "target_profile_id": "epp-bridge-v1-r10-r19",
                "first_transition_id": "TR-0009",
                "maximum_count": 1,
            }
            checkpoint_valid = (
                profile.get("checkpoint_commit")
                == "c46ea627a7403ff3e1ce3db6be3d1baeebebb377"
                and profile.get("checkpoint_commit_rule") == "fixed_commit"
            )
        else:
            expected_successor = {
                "kind": "schema_migration",
                "target_schema_version": "2.0",
                "event_kind": "lifecycle_transition",
                "maximum_count": 1,
            }
            checkpoint_valid = (
                profile.get("checkpoint_commit") is None
                and profile.get("checkpoint_commit_rule")
                == "exact_material_change_approval_subject"
            )
        if (
            profile.get("successor") != expected_successor
            or profile.get("accept_new_records") is not False
        ):
            findings.append(
                _finding(
                    "LEGACY_SUCCESSOR_INVALID",
                    "fatal",
                    artifact,
                    "SOLE_CLOSED_SUCCESSOR",
                )
            )
        if not checkpoint_valid:
            findings.append(
                _finding(
                    "LEGACY_CHECKPOINT_INVALID",
                    "fatal",
                    artifact,
                    "APPROVAL_SUBJECT_CHECKPOINT",
                )
            )
        expected_terminal = (
            ("PROGRAM_ACTIVE", "CLARIFIED")
            if index == 0
            else ("PROGRAM_ACTIVE", "IMPLEMENTATION_APPROVAL_PENDING")
        )
        if (
            profile.get("terminal_program_state"),
            profile.get("terminal_feature_state"),
        ) != expected_terminal or profile.get(
            "checkpoint_state_digest"
        ) != state_digests.get(last_state):
            findings.append(
                _finding(
                    "LEGACY_TERMINAL_MISMATCH",
                    "fatal",
                    artifact,
                    "CLOSED_TERMINAL_STATE",
                )
            )
    for row in transition_rows:
        prior_revision = row.get("prior_revision")
        new_revision = row.get("new_revision")
        if (
            not isinstance(prior_revision, int)
            or new_revision != prior_revision + 1
            or row.get("prior_state_digest") != state_digests.get(prior_revision)
            or row.get("new_state_digest") != state_digests.get(new_revision)
        ):
            findings.append(
                _finding(
                    "LEGACY_TRANSITION_METADATA_MISMATCH",
                    "fatal",
                    str(row.get("transition_id", "legacy-transition")),
                    "PROFILE_EDGE_MATCHES_STATES",
                )
            )
    if observed_v1_revisions is not None and any(
        revision > 19 for revision in observed_v1_revisions
    ):
        findings.append(
            _finding("LEGACY_FUTURE_RECORD", "fatal", "evidence/states", "NO_FUTURE_V1")
        )
    if migration_count != 1:
        findings.append(
            _finding(
                "LEGACY_MIGRATION_COUNT",
                "fatal",
                "evidence/transitions",
                "SOLE_V2_SUCCESSOR",
            )
        )
    return sorted(findings, key=Finding.sort_key)


CORRECTION_ID = "COR-EPP-F01-US1-COMMITTED-IDENTITY-001"
CORRECTION_SUBJECT = "88481d57f1258f59f303f507eafc4e352569bc11"
CORRECTION_SUBJECT_TREE = "17ebad227dd02f6b94fa99c006ea360c141a8cae"
CORRECTION_SUBJECT_PROGRAM_TREE = "a4fbe48595a52ffe6af408067bf4b1d63c660921"
CORRECTION_PROFILE_SHA256 = (
    "9bd3bab9215eefbfb951a0d8db8c613433002f1afc44b79cce6063de6e0ff27d"
)
CORRECTION_SCHEMA_SHA256 = (
    "e01b2eda036b69046912945b065c1a7d8aba2334991c37b48179132aedaddc7b"
)
CORRECTION_APPROVAL_PATHS = (
    "evidence/approvals/APR-EPP-F01-MC-004.json",
    "evidence/approvals/APR-EPP-F01-IMPL-004.json",
)
CORRECTION_APPROVAL_SHA256 = (
    "63b2c7b48acdd11c263d67b8079b56e686ae2e43c75f870a54eaca11c676a5ad",
    "2c5562011e62a7f0a6a357e5b654f322c50faeefe31672977ac6c1c939b2cc8e",
)

INPUT_ORIGIN_CORRECTION_ID = "COR-EPP-F01-US1-TR0027-INPUT-ORIGIN-001"
INPUT_ORIGIN_CORRECTION_SUBJECT = "2f53b49af92d4d6d6619903deec2521919758148"
INPUT_ORIGIN_CORRECTION_SUBJECT_TREE = "3bd726941aae300691482d0c35a4028029ccbe3f"
INPUT_ORIGIN_CORRECTION_SUBJECT_PROGRAM_TREE = (
    "f0163abcc74379407c96f10dacaa34c0883aa7a1"
)
INPUT_ORIGIN_CORRECTION_PROFILE_SHA256 = (
    "fdcee78163d218c8bbf3908c12fa09595c4d4984cc2d753487195177ebbda53d"
)
INPUT_ORIGIN_CORRECTION_SCHEMA_SHA256 = (
    "dc3f7d31eb7e43e7453ae9d7c0f060b0429f7a754618ead0f4ec6aa3aad2df5f"
)
INPUT_ORIGIN_CORRECTION_APPROVAL_PATHS = (
    "evidence/approvals/APR-EPP-F01-MC-005.json",
    "evidence/approvals/APR-EPP-F01-IMPL-005.json",
)
INPUT_ORIGIN_CORRECTION_APPROVAL_SHA256 = (
    "4b4b7f748c2adbb64eddedf75306a2aab694054a62c552699be9ea1ac9802c4d",
    "33a327cbc1b599976eabb3bcb86b2081580e8bcda17870fdd69e56e789d58c9e",
)
INPUT_ORIGIN_CORRECTION_PROFILE_BLOB = "752c57d14093763393db183f8c7ae16939a2c82d"
INPUT_ORIGIN_CORRECTION_SCHEMA_BLOB = "c781ec8fcae67dcb97cd38be625e44c9b5cd449f"
INPUT_ORIGIN_CORRECTION_APPROVAL_BLOBS = (
    "34b0c203db7ccb873c5c6bb6e49f9237a9ee4a05",
    "7f04dd7a6784bc68b77bebd9f576588fe53d1eab",
)
INPUT_ORIGIN_CORRECTION_APPROVAL_CONTAINER = "91fa3a9867d99f117ff9f41bbcac3d5d674f1f3b"
INPUT_ORIGIN_TARGET = (
    "docs/programs/engineering-process-platform/evidence/transitions/TR-0027.json",
    "/inputs/3",
)

REPAIR_CORRECTION_ID = "COR-EPP-F01-REPAIR-EVIDENCE-001"
REPAIR_CORRECTION_SUBJECT = "a2b9727a15c445875b2ef857f482bee31ccc594c"
REPAIR_CORRECTION_SUBJECT_TREE = "ee16d103c98c3d891d32c45b243a131dd0745527"
REPAIR_CORRECTION_SUBJECT_PROGRAM_TREE = "677f1ec8e895b6330941f8ab5afe92c5dadf980b"
REPAIR_CORRECTION_PROFILE_SHA256 = (
    "5df46132d8f8cf38a0c6a31fa03bc6363f5d222e3c71fe14c45bb9b9e51a1677"
)
REPAIR_CORRECTION_SCHEMA_SHA256 = (
    "50676373c395aed7534eff8b3001bc248346a3e184cf580eb6a6fd101cb43691"
)
REPAIR_CORRECTION_PROFILE_BLOB = "150a73292f33d6376bbcccda94a260e0dddaccdd"
REPAIR_CORRECTION_SCHEMA_BLOB = "0c60ffe2c66edf66f62e56f69d6ab0dca1411c1a"
REPAIR_CORRECTION_APPROVAL_PATHS = (
    "evidence/approvals/APR-EPP-F01-MC-007.json",
    "evidence/approvals/APR-EPP-F01-IMPL-007.json",
)
REPAIR_CORRECTION_APPROVAL_SHA256 = (
    "1b99586cd62f94d5007a4942d82b7b8b4e3ab617141e620ac76281e61ec43288",
    "03ddbdca2090956df4a27b39b6552ed4c438f0cbcd3919e31e2c93e24848b4b3",
)
REPAIR_CORRECTION_APPROVAL_BLOBS = (
    "bbf84a19a0c33fe2a1aa0de192306e8527d4fce5",
    "1ea770845521dd9bd2e009bf1388110206116d6e",
)
REPAIR_CORRECTION_APPROVAL_CONTAINER = "826760ea995cea2f639f6e291e25659a7ccf56c5"
REPAIR_CAUSE_TARGETS = frozenset(
    {
        (
            f"docs/programs/engineering-process-platform/evidence/states/"
            f"program-state-revision-{revision:04d}.json",
            "/active_mutating_lease/recovery/active_cause_id",
        )
        for revision in (45, 46)
    }
)
REPAIR_DIGEST_TARGET = (
    "docs/programs/engineering-process-platform/evidence/transitions/TR-0044.json",
    "/inputs/1/sha256",
)

CHECKPOINT_CORRECTION_ID = "COR-EPP-F01-T072-CHECKPOINT-EVIDENCE-001"
CHECKPOINT_CORRECTION_SUBJECT = "c12eb00308cb72d96977846c4ae876dc0baa7e7e"
CHECKPOINT_CORRECTION_SUBJECT_TREE = "7323b292d279fde752004bc744a2db850ab670d0"
CHECKPOINT_CORRECTION_SUBJECT_PROGRAM_TREE = "18e3d4ad3f33e244b1f9145b55b27f4e02d4b54b"
CHECKPOINT_CORRECTION_PROFILE_SHA256 = (
    "755aa27fb27b4d5eac1e04d07fa938b16f4c38e9be8d9d7de0bc8aed7b19d1d6"
)
CHECKPOINT_CORRECTION_SCHEMA_SHA256 = (
    "1728309b49889e6c2f8101f3a887575f7e9e8a833b5c28e3472cd242b03b1224"
)
CHECKPOINT_CORRECTION_PROFILE_BLOB = "cbd47bcf6a76dd2acacb3e8f6642e621e026c79f"
CHECKPOINT_CORRECTION_SCHEMA_BLOB = "01ae03ab695cf9cf01c16e5096c48183c4e73aa1"
CHECKPOINT_APPROVAL_CONTAINER = "9f30322859e8039863b47cdcb0e4c8f29354c9dc"
CHECKPOINT_APPROVAL_PATHS = (
    "evidence/approvals/APR-EPP-F01-MC-008.json",
    "evidence/approvals/APR-EPP-F01-IMPL-008.json",
)
CHECKPOINT_APPROVAL_SHA256 = (
    "eda16e8761139d1dd2235ef76a97aec852e200dc89de2acc07d6967d36294b6a",
    "9f0c787e5af074be036e9b10e8d726f017c609d7b9469f20a0c3e8bccf5eb9ce",
)
CHECKPOINT_APPROVAL_BLOBS = (
    "89dd452b6178fd23974321579b446d5403791e0b",
    "0853bd47ef86ecaa8cd872985054f7c95e7b1e2b",
)
CHECKPOINT_DIGEST_TARGETS = frozenset(
    {
        (
            "docs/programs/engineering-process-platform/evidence/transitions/TR-0047.json",
            "/outputs/0/sha256",
        ),
        (
            "docs/programs/engineering-process-platform/evidence/transitions/TR-0047.json",
            "/outputs/1/sha256",
        ),
    }
)
CHECKPOINT_EVENT_TARGETS = frozenset(
    {
        (
            "docs/programs/engineering-process-platform/evidence/transitions/TR-0050.json",
            "repair",
            "repair_checkpoint",
            "BLOCKED",
            "BLOCKED",
        )
    }
)

PREFLIGHT_CORRECTION_ID = "COR-EPP-F01-V9-PREFLIGHT-EVIDENCE-001"
PREFLIGHT_CORRECTION_SUBJECT = "d96e8b68c9fda08eea84065186452581727ec4fa"
PREFLIGHT_CORRECTION_SUBJECT_TREE = "d16d81afaabac73e4374ecb186089cb0a95dd1bc"
PREFLIGHT_CORRECTION_SUBJECT_PROGRAM_TREE = "ee2fbf3b1a15920701289a083431f0afd41ed4ec"
PREFLIGHT_CORRECTION_PROFILE_SHA256 = (
    "59c9344f14a99780bcd652e256343d105ed63199a8e1dcba1125267928669828"
)
PREFLIGHT_CORRECTION_SCHEMA_SHA256 = (
    "3199eaaaecdab8870233192b6aee86c6e95308e14a553649edb1069d1f9a90a1"
)
PREFLIGHT_CORRECTION_PROFILE_BLOB = "2c29673bf6fc13fd3c5b00cdb119be6d03b81149"
PREFLIGHT_CORRECTION_SCHEMA_BLOB = "71360494ad22a8278ac731127369b89f423eb20c"
PREFLIGHT_DISCOVERY_SCHEMA_SHA256 = (
    "33699e5ef2748b422d013679405f45d6df50ca98d418d9be4cf06b2f44301205"
)
PREFLIGHT_DISCOVERY_SCHEMA_BLOB = "c6662ccec460b8a89b9d52f810b90fdc3aa55b23"
PREFLIGHT_APPROVAL_CONTAINER = "1884de8ba69ca61c75cff305e06b994207ad0720"
PREFLIGHT_APPROVAL_PATHS = (
    "evidence/approvals/APR-EPP-F01-MC-009.json",
    "evidence/approvals/APR-EPP-F01-IMPL-009.json",
)
PREFLIGHT_APPROVAL_SHA256 = (
    "aef627acfda197661c96a8e15eabb7082a6ee74c2912332cf7ed1e3bb90565ee",
    "dda0972b8a13fa3fad63655698bfefbab54aa77aca054f7200c13dc730023575",
)
PREFLIGHT_APPROVAL_BLOBS = (
    "1c62eadc9a58026cbbf4fbe3ae02e108255d94e0",
    "8c58100084e018524288b76267cfb92e554abe3c",
)
PREFLIGHT_DISCOVERY_TARGET = (
    "docs/programs/engineering-process-platform/evidence/verification/"
    "EPP-F01-V8-discovery.json"
)
PREFLIGHT_MANIFEST_TARGET = (
    "docs/programs/engineering-process-platform/evidence/transitions/TR-0051.json"
)

REV58_REPAIR_EVIDENCE_ID = "VER-EPP-F01-REV58-RAW-IDENTITY-001"
REV58_REPAIR_SOURCE = "cf19f19b47484afb66a28bd3f93c041d86553c89"
REV58_REPAIR_SOURCE_TREE = "0df363d2dd89113dec0be9ad27ebbf5ce71ffbb4"
REV58_REPAIR_SOURCE_PROGRAM_TREE = "f07e575c1f00dd52c26d32028d7efa28c3c88f9f"
REV58_ARCHIVE_SHA_BEFORE = (
    "b4c54c2b6208f7ce8739cb8ad26eb7b0485a412a31bdaf40bafba5dc0608d9d6"
)
REV58_ARCHIVE_SHA_AFTER = (
    "0ba26ac9d9787ce84e626b6a4ddb937ddbd31e3c51c142bb6b1c89360b9f0a08"
)
REV58_ARCHIVE_BLOB_BEFORE = "598f9002a72d939a78f3ab971b8f89c713b53fbc"
REV58_ARCHIVE_BLOB_AFTER = "6c3c5466e068aa5d259d65181a3b0dd1683a8bfc"
REV58_TRANSITION_SHA = (
    "4c21b4ecfb2a65a61140c0bddd30a58d3dea77f071604bd6ca324f55a35948b7"
)
REV58_TRANSITION_BLOB = "1cce6965efe08a44ac9b8a1f4bf24b9b15cab885"
REV58_DIGEST_TARGET = (
    "docs/programs/engineering-process-platform/evidence/transitions/TR-0057.json",
    "/outputs/0/sha256",
)

F01B_ACTIVATION_CORRECTION_ID = "COR-EPP-F01B-ACTIVATION-RAW-IDENTITY-001"
F01B_ACTIVATION_SOURCE = "5c946828458b3ed5df6ec2c2e7b3601444264fee"
F01B_ACTIVATION_SOURCE_TREE = "b4fffe31c7d3e9bfd293c4adedb5794ae9a8a97a"
F01B_ACTIVATION_SOURCE_PROGRAM_TREE = "a3f8dcc9b4772e49374bba49cb2c219c4186874d"
F01B_ACTIVATION_TRANSITION_SHA = (
    "21417d4b0c1b0f0408518bef0f710b66053342f8ea66b9c19ee526b34379efa8"
)
F01B_ACTIVATION_TRANSITION_BLOB = "c84b3ef4d066f2198a7b753358600f8c4c6a499e"
F01B_ACTIVATION_DIGEST_TARGETS = frozenset(
    {
        (
            "docs/programs/engineering-process-platform/evidence/transitions/"
            "TR-0070.json",
            f"/outputs/{index}/sha256",
        )
        for index in (3, 4, 5)
    }
)
F01B_ACTIVATION_CLAIMS = (
    (
        "TR0070-LIFECYCLE-POLICY-OUTPUT-DIGEST-001",
        "/outputs/3/sha256",
        "docs/programs/engineering-process-platform/lifecycle-policy.json",
        "5d0d4f352883f040ab50bc3a986c9da09ec342a5",
        "7ec9663758b9096111032e0edb35938a7b35123ca3dbc2eaf0a822171a763d2c",
        "ee668c2e2495d399621515d3d649d094bd79a5e7f33709c0a1be3db0c7b08253",
    ),
    (
        "TR0070-PROGRAM-STATE-OUTPUT-DIGEST-001",
        "/outputs/4/sha256",
        "docs/programs/engineering-process-platform/program-state.json",
        "85cfa21e7058af01287fb13f98ea954440d7cc95",
        "22ce91626be2ff0d15a2aeb064208cdbe4041bb6faf17c98e07c317d380725d7",
        "ee8f9f5e69899e861a51894fc34356f33281454976b45d996564540c2072b967",
    ),
    (
        "TR0070-LEASE-TEST-OUTPUT-DIGEST-001",
        "/outputs/5/sha256",
        "tests/program_control_plane/test_contract_schemas.py",
        "8826ffd4db8f2de050ca02771af8dafa23031599",
        "2412b3c4d62baf60f7ab1178589d5aa0392e699693040d1bac8b06c48814f8c6",
        "2aba5e62e807dad3d8646da841500204d89075d3d7c253a75330629670d3f3d1",
    ),
)

F01B_LEASE_CHECKPOINT_SOURCE = "18635d6ba1d83cf68c80d1acf317497d95ec1c48"
F01B_LEASE_CHECKPOINT_SOURCE_TREE = "a5bed23ab3a05996f5124608a8d6cf6ef48abed8"
F01B_LEASE_CHECKPOINT_SOURCE_PROGRAM_TREE = "1b769f792c12ac946809d7e56038dde849c07a58"
F01B_LEASE_CHECKPOINT_TRANSITION_SHA = (
    "eb16d316403db35175b0bbf4b9259d91f6a967668ee1442ae094792cd7aa131c"
)
F01B_LEASE_CHECKPOINT_TRANSITION_BLOB = "689164ed6c150abca95553e2d733f89bdb100494"
F01B_LEASE_CHECKPOINT_STATE_SHA = (
    "8e39d8a9a7df71b4665bf96107838ce715ec86d948a0c9d432dccd233b3b7d53"
)
F01B_LEASE_CHECKPOINT_STATE_BLOB = "ac7b4e0bc2a1b43d93f4121675e5edf486279b92"
F01B_LEASE_CHECKPOINT_SCHEMA_TARGETS = frozenset(
    {
        "docs/programs/engineering-process-platform/evidence/states/"
        "program-state-revision-0075.json"
    }
)
F01B_LEASE_CHECKPOINT_DIGEST_TARGETS = frozenset(
    {
        (
            "docs/programs/engineering-process-platform/evidence/transitions/"
            "TR-0074.json",
            "/inputs/3/sha256",
        ),
        (
            "docs/programs/engineering-process-platform/evidence/transitions/"
            "TR-0074.json",
            "/inputs/4/sha256",
        ),
    }
)
F01B_LEASE_CHECKPOINT_RESTRICTION = (
    "The e83a78f8 requirements remain frozen. Allowed exceptions are TR-0073 "
    "lifecycle-limit projection, the specialized test-result/checkpoint-binding "
    "corrections through 1a2cebb4, task completion marks, acceptance evidence, "
    "and bounded implementation results."
)
F01B_LEASE_CHECKPOINT_ACTION = (
    "Append-only correction of revision 75's overlong path-restriction text and "
    "TR-0074 input digest claims 3 and 4, with no authority or scope change."
)


def _prefetch_closed_correction_blobs(
    reader: GitReader,
    current: str,
    root: str,
    documents: Mapping[str, Any],
) -> None:
    """Batch immutable correction inputs without changing fail-closed semantics."""

    requests: list[tuple[str, str]] = []
    closed = (
        (
            CORRECTION_SUBJECT,
            f"{root}/evidence/corrections/{CORRECTION_ID}.json",
            f"{root}/schemas/committed-identity-correction.schema.json",
            "specs/076-control-plane-validator/contracts/committed-identity-correction.schema.json",
        ),
        (
            INPUT_ORIGIN_CORRECTION_SUBJECT,
            f"{root}/evidence/corrections/{INPUT_ORIGIN_CORRECTION_ID}.json",
            f"{root}/schemas/transition-input-correction.schema.json",
            "specs/076-control-plane-validator/contracts/transition-input-correction.schema.json",
        ),
        (
            REPAIR_CORRECTION_SUBJECT,
            f"{root}/evidence/corrections/{REPAIR_CORRECTION_ID}.json",
            f"{root}/schemas/repair-evidence-correction.schema.json",
            "specs/076-control-plane-validator/contracts/repair-evidence-correction.schema.json",
        ),
        (
            CHECKPOINT_CORRECTION_SUBJECT,
            f"{root}/evidence/corrections/{CHECKPOINT_CORRECTION_ID}.json",
            f"{root}/schemas/checkpoint-evidence-correction.schema.json",
            "specs/076-control-plane-validator/contracts/checkpoint-evidence-correction.schema.json",
        ),
        (
            PREFLIGHT_CORRECTION_SUBJECT,
            f"{root}/evidence/corrections/{PREFLIGHT_CORRECTION_ID}.json",
            f"{root}/schemas/preflight-evidence-correction.schema.json",
            "specs/076-control-plane-validator/contracts/preflight-evidence-correction.schema.json",
        ),
    )
    for subject, profile_path, promoted_schema, planning_schema in closed:
        requests.extend(
            [
                (subject, profile_path),
                (subject, promoted_schema),
                (subject, planning_schema),
                (current, profile_path),
                (current, promoted_schema),
                (current, planning_schema),
            ]
        )
    approval_relatives = (
        *CORRECTION_APPROVAL_PATHS,
        *INPUT_ORIGIN_CORRECTION_APPROVAL_PATHS,
        *REPAIR_CORRECTION_APPROVAL_PATHS,
        *CHECKPOINT_APPROVAL_PATHS,
        *PREFLIGHT_APPROVAL_PATHS,
    )
    try:
        for relative in approval_relatives:
            approval = documents.get(f"{root}/{relative}")
            if not isinstance(approval, Mapping):
                continue
            subject = approval.get("subject", {})
            approved_commit = subject.get("git_commit")
            if not isinstance(approved_commit, str) or not HEX40.fullmatch(
                approved_commit
            ):
                continue
            for artifact in subject.get("artifact_digests", []):
                requests.append(
                    (
                        approved_commit,
                        normalize_repo_path(
                            posixpath.normpath(
                                posixpath.join(root, str(artifact["path"]))
                            )
                        ),
                    )
                )
        reader.read_blob_requests(requests)
    except (GitSubjectError, KeyError, TypeError):
        # Individual closed validators still report the exact bounded cause.
        return


def _pointer_value(document: Any, pointer: str) -> Any:
    """Resolve one strict RFC 6901 pointer without accepting wildcards or ranges."""

    if not pointer.startswith("/") or "*" in pointer or "[" in pointer:
        raise ValueError("unsafe JSON pointer")
    value = document
    for encoded in pointer[1:].split("/"):
        token = encoded.replace("~1", "/").replace("~0", "~")
        if isinstance(value, Mapping):
            value = value[token]
        elif isinstance(value, list) and token.isdigit():
            value = value[int(token)]
        else:
            raise ValueError("JSON pointer target is unavailable")
    return value


def _correction_claim_rows(
    profile: Mapping[str, Any],
) -> tuple[list[tuple[str, str, str, str, str]], frozenset[tuple[str, str]]]:
    """Return the closed 37 visible dispositions and six transition targets."""

    rows: list[tuple[str, str, str, str, str]] = []
    transition_targets: set[tuple[str, str]] = set()
    for claim in profile.get("transition_digest_claims", []):
        target = claim.get("target", {})
        artifact = str(target.get("artifact_path", "correction-target"))
        pointer = str(claim.get("json_pointer", ""))
        claim_id = str(claim.get("claim_id", "transition-claim"))
        recorded = str(claim.get("recorded_value", ""))
        authoritative = str(claim.get("authoritative_value", ""))
        rows.append((artifact, pointer, claim_id, recorded, authoritative))
        transition_targets.add((artifact, pointer))
    tree_resolution = profile.get("tree_resolution", {})
    recorded_tree = str(tree_resolution.get("recorded_value", ""))
    authoritative_tree = str(tree_resolution.get("authoritative_value", ""))
    for target in profile.get("historical_state_tree_claims", []):
        artifact = str(target.get("artifact_path", "correction-target"))
        revision = target.get("revision", "unknown")
        for pointer in target.get("json_pointers", []):
            rows.append(
                (
                    artifact,
                    str(pointer),
                    f"state-r{revision}",
                    recorded_tree,
                    authoritative_tree,
                )
            )
    return rows, frozenset(transition_targets)


def validate_committed_identity_correction(
    reader: GitReader,
    source_commit: str,
    program_root: str,
    profile: Mapping[str, Any],
    approvals: Mapping[str, Mapping[str, Any]],
) -> tuple[list[Finding], frozenset[tuple[str, str]]]:
    """Recompute the one approved, non-extensible committed-identity correction."""

    root = normalize_repo_path(program_root)
    correction_path = f"{root}/evidence/corrections/{CORRECTION_ID}.json"
    promoted_schema_path = f"{root}/schemas/committed-identity-correction.schema.json"
    planning_schema_path = (
        "specs/076-control-plane-validator/contracts/"
        "committed-identity-correction.schema.json"
    )
    profile_valid = True
    authority_valid = True
    golden: Mapping[str, Any] = {}
    current = ""

    try:
        current = reader.resolve_commit(source_commit)
        closed_blobs = reader.read_blob_requests(
            [
                (CORRECTION_SUBJECT, correction_path),
                (CORRECTION_SUBJECT, promoted_schema_path),
                (CORRECTION_SUBJECT, planning_schema_path),
                (current, correction_path),
                (current, promoted_schema_path),
                (current, planning_schema_path),
            ]
        )
        golden_raw = closed_blobs[(CORRECTION_SUBJECT, correction_path)]
        promoted_schema_raw = closed_blobs[(CORRECTION_SUBJECT, promoted_schema_path)]
        planning_schema_raw = closed_blobs[(CORRECTION_SUBJECT, planning_schema_path)]
        golden_value = strict_loads(golden_raw)
        promoted_schema = strict_loads(promoted_schema_raw)
        if not isinstance(golden_value, Mapping) or not isinstance(
            promoted_schema, Mapping
        ):
            raise ContractError("closed correction artifacts are not objects")
        golden = golden_value
        check_schema(promoted_schema)
        profile_valid = profile_valid and not validate_schema(promoted_schema, profile)
        profile_valid = profile_valid and not validate_schema(promoted_schema, golden)
        profile_valid = profile_valid and profile == golden
        profile_valid = profile_valid and (
            sha256_bytes(golden_raw) == CORRECTION_PROFILE_SHA256
            and sha256_bytes(promoted_schema_raw) == CORRECTION_SCHEMA_SHA256
            and promoted_schema_raw == planning_schema_raw
            and closed_blobs[(current, correction_path)] == golden_raw
            and closed_blobs[(current, promoted_schema_path)] == promoted_schema_raw
            and closed_blobs[(current, planning_schema_path)] == planning_schema_raw
        )
        correction_container = reader.containing_commit(current, correction_path)
        profile_valid = profile_valid and (
            correction_container == CORRECTION_SUBJECT
            and CORRECTION_SUBJECT != current
            and reader.is_ancestor(CORRECTION_SUBJECT, current)
        )
        correction_identity = reader.resolve_identity(CORRECTION_SUBJECT, root)
        profile_valid = profile_valid and (
            correction_identity.source_tree == CORRECTION_SUBJECT_TREE
            and correction_identity.program_tree == CORRECTION_SUBJECT_PROGRAM_TREE
        )
        checkpoint = golden.get("source_checkpoint", {})
        checkpoint_identity = reader.resolve_identity(
            str(checkpoint.get("git_commit")), root
        )
        profile_valid = profile_valid and (
            checkpoint_identity.source_tree == checkpoint.get("git_tree")
            and checkpoint_identity.program_tree == checkpoint.get("program_tree")
            and reader.is_ancestor(
                checkpoint_identity.source_commit, CORRECTION_SUBJECT
            )
            and checkpoint_identity.source_commit != CORRECTION_SUBJECT
        )
    except (ContractError, GitSubjectError, TypeError, ValueError):
        profile_valid = False

    # The approved subject is the source of the target set even when a caller
    # presents a mutated profile. This prevents omission from hiding findings.
    claim_rows, transition_targets = _correction_claim_rows(golden)
    if len(claim_rows) != 37 or len(transition_targets) != 6:
        profile_valid = False

    try:
        if not profile_valid:
            raise ValueError("presented correction does not match closed profile")
        transitions = list(golden.get("transition_digest_claims", []))
        states = list(golden.get("historical_state_tree_claims", []))
        tree_resolution = golden.get("tree_resolution", {})
        if len(transitions) != 6 or len(states) != 26:
            raise ValueError("closed target cardinality changed")
        target_paths = {str(row["target"]["artifact_path"]) for row in transitions} | {
            str(row["artifact_path"]) for row in states
        }
        additions = reader.added_path_commits(current, f"{root}/evidence")
        introducing_commits = {
            str(row["target"]["introducing_commit"]) for row in transitions
        } | {str(row["introducing_commit"]) for row in states}
        authoritative_commit = str(tree_resolution["authoritative_commit"])
        summaries = reader.commit_summaries(
            [*introducing_commits, authoritative_commit]
        )
        blob_requests: list[tuple[str, str]] = []
        object_requests: list[tuple[str, str]] = []
        for row in transitions:
            target = row["target"]
            introducing = str(target["introducing_commit"])
            path = str(target["artifact_path"])
            resolution = row["resolution"]
            resolved_subject = str(resolution["subject_commit"])
            resolved_path = str(resolution["artifact_path"])
            blob_requests.extend(
                [
                    (introducing, path),
                    (current, path),
                    (resolved_subject, resolved_path),
                ]
            )
            object_requests.extend(
                [(introducing, path), (resolved_subject, resolved_path)]
            )
        for row in states:
            introducing = str(row["introducing_commit"])
            path = str(row["artifact_path"])
            blob_requests.extend([(introducing, path), (current, path)])
            object_requests.append((introducing, path))
        blobs = reader.read_blob_requests(blob_requests)
        object_ids = reader.object_ids(object_requests)

        for row in transitions:
            target = row["target"]
            introducing = str(target["introducing_commit"])
            path = str(target["artifact_path"])
            raw = blobs[(introducing, path)]
            transition = strict_loads(raw)
            resolution = row["resolution"]
            resolved_subject = str(resolution["subject_commit"])
            resolved_path = str(resolution["artifact_path"])
            resolved_raw = blobs[(resolved_subject, resolved_path)]
            profile_valid = profile_valid and all(
                (
                    path in target_paths,
                    additions.get(path) == introducing,
                    summaries[introducing].get("tree") == target["introducing_tree"],
                    object_ids[(introducing, path)] == target["artifact_git_blob"],
                    sha256_bytes(raw) == target["artifact_raw_sha256"],
                    blobs[(current, path)] == raw,
                    _pointer_value(transition, str(row["json_pointer"]))
                    == row["recorded_value"],
                    resolved_subject == introducing,
                    object_ids[(resolved_subject, resolved_path)]
                    == resolution["artifact_git_blob"],
                    sha256_bytes(resolved_raw) == row["authoritative_value"],
                    row["recorded_value"] != row["authoritative_value"],
                    introducing != CORRECTION_SUBJECT,
                    reader.is_ancestor(introducing, CORRECTION_SUBJECT),
                )
            )

        authoritative_tree = summaries[authoritative_commit].get("tree")
        profile_valid = profile_valid and (
            authoritative_tree == tree_resolution.get("authoritative_value")
            and tree_resolution.get("recorded_value") != authoritative_tree
        )
        for row in states:
            introducing = str(row["introducing_commit"])
            path = str(row["artifact_path"])
            raw = blobs[(introducing, path)]
            state = strict_loads(raw)
            profile_valid = profile_valid and all(
                (
                    additions.get(path) == introducing,
                    summaries[introducing].get("tree") == row["introducing_tree"],
                    object_ids[(introducing, path)] == row["artifact_git_blob"],
                    sha256_bytes(raw) == row["artifact_raw_sha256"],
                    blobs[(current, path)] == raw,
                    canonical_digest(state) == row["canonical_state_digest"],
                    state.get("revision") == row["revision"],
                    introducing != CORRECTION_SUBJECT,
                    reader.is_ancestor(introducing, CORRECTION_SUBJECT),
                )
            )
            for pointer in row["json_pointers"]:
                parent = str(pointer).rsplit("/", 1)[0]
                profile_valid = profile_valid and (
                    _pointer_value(state, str(pointer))
                    == tree_resolution["recorded_value"]
                    and _pointer_value(state, f"{parent}/commit")
                    == authoritative_commit
                )
    except (ContractError, GitSubjectError, KeyError, TypeError, ValueError):
        profile_valid = False

    expected_full_paths = tuple(
        f"{root}/{relative}" for relative in CORRECTION_APPROVAL_PATHS
    )
    try:
        if set(approvals) != set(expected_full_paths):
            raise ValueError("approval path set changed")
        selected = [approvals[path] for path in expected_full_paths]
        approval_blob_requests: list[tuple[str, str]] = []
        for approval in selected:
            subject = approval.get("subject", {})
            approved_commit = subject.get("git_commit")
            if not isinstance(approved_commit, str):
                raise ValueError("approval subject is missing")
            for artifact in subject.get("artifact_digests", []):
                approval_blob_requests.append(
                    (
                        approved_commit,
                        normalize_repo_path(
                            posixpath.normpath(
                                posixpath.join(root, str(artifact["path"]))
                            )
                        ),
                    )
                )
        reader.read_blob_requests(approval_blob_requests)
        expected_subject = {
            "git_commit": CORRECTION_SUBJECT,
            "git_tree": CORRECTION_SUBJECT_TREE,
            "program_tree": CORRECTION_SUBJECT_PROGRAM_TREE,
        }
        expected_records = (
            ("APR-EPP-F01-MC-004", "material_change", "APR-EPP-F01-MC-003"),
            (
                "APR-EPP-F01-IMPL-004",
                "feature_implementation",
                "APR-EPP-F01-IMPL-003",
            ),
        )
        if selected[0].get("subject") != selected[1].get("subject"):
            raise ValueError("approval subjects differ")
        for path, approval, expected, expected_raw_sha256 in zip(
            expected_full_paths,
            selected,
            expected_records,
            CORRECTION_APPROVAL_SHA256,
            strict=True,
        ):
            approval_id, scope, superseded = expected
            subject = approval.get("subject", {})
            artifacts = subject.get("artifact_digests", [])
            profile_entries = [
                row
                for row in artifacts
                if row.get("path") == f"evidence/corrections/{CORRECTION_ID}.json"
            ]
            if not all(
                (
                    approval.get("approval_id") == approval_id,
                    approval.get("scope") == scope,
                    approval.get("program_id") == "EPP-2026",
                    approval.get("feature_id") == "EPP-F01",
                    approval.get("bundle_id") == "APB-EPP-F01-004",
                    approval.get("decision") == "approved",
                    approval.get("approved_at") == "2026-08-27T16:24:45Z",
                    approval.get("expires_at") is None,
                    approval.get("revocation_events") == [],
                    approval.get("supersedes") == [superseded],
                    all(
                        subject.get(key) == value
                        for key, value in expected_subject.items()
                    ),
                    len(artifacts) == 38,
                    len({row.get("path") for row in artifacts}) == 38,
                    profile_entries
                    == [
                        {
                            "path": f"evidence/corrections/{CORRECTION_ID}.json",
                            "sha256": CORRECTION_PROFILE_SHA256,
                        }
                    ],
                    strict_loads(reader.blob(current, path)) == approval,
                    sha256_bytes(reader.blob(current, path)) == expected_raw_sha256,
                    _verify_approval_artifacts(reader, current, approval, root),
                )
            ):
                raise ValueError("approval record is not the exact V4 bundle")
            container = reader.containing_commit(current, path)
            if not (
                container != CORRECTION_SUBJECT
                and reader.is_ancestor(CORRECTION_SUBJECT, container)
                and reader.is_ancestor(container, current)
                and reader.blob(current, path) == reader.blob(container, path)
            ):
                raise ValueError("approval history is not append-only after correction")
    except (GitSubjectError, KeyError, TypeError, ValueError):
        authority_valid = False

    resolved = profile_valid and authority_valid
    findings = [
        _finding(
            "COMMITTED_IDENTITY_MISMATCH",
            "info" if resolved else "fatal",
            artifact,
            "EXACT_APPROVED_COMMITTED_IDENTITY_DISPOSITION",
            (
                claim_id,
                f"recorded:{recorded}",
                f"authoritative:{authoritative}",
            ),
            json_pointer=pointer,
            resolution_status="resolved" if resolved else "unresolved",
            correction_ref=correction_path if resolved else None,
        )
        for artifact, pointer, claim_id, recorded, authoritative in claim_rows
    ]
    if not profile_valid:
        findings.append(
            _finding(
                "COMMITTED_IDENTITY_CORRECTION_INVALID",
                "fatal",
                correction_path,
                "CLOSED_37_CLAIM_GIT_RECOMPUTATION",
            )
        )
    if not authority_valid:
        findings.append(
            _finding(
                "COMMITTED_IDENTITY_CORRECTION_UNAUTHORIZED",
                "fatal",
                f"{root}/evidence/approvals",
                "EXACT_V4_TWO_SCOPE_AUTHORITY",
            )
        )
    return sorted(findings, key=Finding.sort_key), transition_targets


def validate_transition_input_origin_correction(
    reader: GitReader,
    source_commit: str,
    program_root: str,
    profile: Mapping[str, Any],
    approvals: Mapping[str, Mapping[str, Any]],
) -> tuple[list[Finding], frozenset[tuple[str, str]]]:
    """Recompute the one approved TR-0027 input-origin disposition."""

    root = normalize_repo_path(program_root)
    correction_path = f"{root}/evidence/corrections/{INPUT_ORIGIN_CORRECTION_ID}.json"
    promoted_schema_path = f"{root}/schemas/transition-input-correction.schema.json"
    planning_schema_path = (
        "specs/076-control-plane-validator/contracts/"
        "transition-input-correction.schema.json"
    )
    target = INPUT_ORIGIN_TARGET
    profile_valid = True
    authority_valid = True
    golden: Mapping[str, Any] = {}
    current = ""
    introductions: dict[str, str] = {}

    try:
        current = reader.resolve_commit(source_commit)
        introductions = reader.added_path_commits(current, f"{root}/evidence")
        closed_blobs = reader.read_blob_requests(
            [
                (INPUT_ORIGIN_CORRECTION_SUBJECT, correction_path),
                (INPUT_ORIGIN_CORRECTION_SUBJECT, promoted_schema_path),
                (INPUT_ORIGIN_CORRECTION_SUBJECT, planning_schema_path),
                (current, correction_path),
                (current, promoted_schema_path),
                (current, planning_schema_path),
            ]
        )
        golden_raw = closed_blobs[(INPUT_ORIGIN_CORRECTION_SUBJECT, correction_path)]
        promoted_schema_raw = closed_blobs[
            (INPUT_ORIGIN_CORRECTION_SUBJECT, promoted_schema_path)
        ]
        planning_schema_raw = closed_blobs[
            (INPUT_ORIGIN_CORRECTION_SUBJECT, planning_schema_path)
        ]
        closed_object_ids = reader.object_ids(
            [
                (INPUT_ORIGIN_CORRECTION_SUBJECT, correction_path),
                (INPUT_ORIGIN_CORRECTION_SUBJECT, promoted_schema_path),
                *[
                    (
                        INPUT_ORIGIN_CORRECTION_APPROVAL_CONTAINER,
                        f"{root}/{relative}",
                    )
                    for relative in INPUT_ORIGIN_CORRECTION_APPROVAL_PATHS
                ],
            ]
        )
        golden_value = strict_loads(golden_raw)
        promoted_schema = strict_loads(promoted_schema_raw)
        if not isinstance(golden_value, Mapping) or not isinstance(
            promoted_schema, Mapping
        ):
            raise ContractError("closed transition-input artifacts are not objects")
        golden = golden_value
        check_schema(promoted_schema)
        profile_valid = profile_valid and not validate_schema(promoted_schema, profile)
        profile_valid = profile_valid and not validate_schema(promoted_schema, golden)
        profile_valid = profile_valid and profile == golden
        profile_valid = profile_valid and (
            sha256_bytes(golden_raw) == INPUT_ORIGIN_CORRECTION_PROFILE_SHA256
            and sha256_bytes(promoted_schema_raw)
            == INPUT_ORIGIN_CORRECTION_SCHEMA_SHA256
            and promoted_schema_raw == planning_schema_raw
            and closed_blobs[(current, correction_path)] == golden_raw
            and closed_blobs[(current, promoted_schema_path)] == promoted_schema_raw
            and closed_blobs[(current, planning_schema_path)] == planning_schema_raw
            and closed_object_ids[(INPUT_ORIGIN_CORRECTION_SUBJECT, correction_path)]
            == INPUT_ORIGIN_CORRECTION_PROFILE_BLOB
            and closed_object_ids[
                (INPUT_ORIGIN_CORRECTION_SUBJECT, promoted_schema_path)
            ]
            == INPUT_ORIGIN_CORRECTION_SCHEMA_BLOB
        )
        identity = reader.resolve_identity(INPUT_ORIGIN_CORRECTION_SUBJECT, root)
        profile_valid = profile_valid and (
            identity.source_tree == INPUT_ORIGIN_CORRECTION_SUBJECT_TREE
            and identity.program_tree == INPUT_ORIGIN_CORRECTION_SUBJECT_PROGRAM_TREE
            and introductions.get(correction_path) == INPUT_ORIGIN_CORRECTION_SUBJECT
            and INPUT_ORIGIN_CORRECTION_SUBJECT != current
            and reader.is_ancestor(INPUT_ORIGIN_CORRECTION_SUBJECT, current)
        )
    except (ContractError, GitSubjectError, TypeError, ValueError):
        profile_valid = False

    try:
        if not profile_valid:
            raise ValueError("presented transition-input correction changed")
        claim = golden["claim"]
        transition_path = str(claim["transition_path"])
        approval_path = str(claim["approval_path"])
        declared_source = str(claim["declared_source_commit"])
        container = str(claim["container_commit"])
        if (transition_path, str(claim["json_pointer"])) != target:
            raise ValueError("closed correction target changed")
        transition_raw = reader.blob(container, transition_path)
        transition = strict_loads(transition_raw)
        approval_raw = reader.blob(container, approval_path)
        summaries = reader.commit_summaries([container])
        object_ids = reader.optional_object_ids(
            [
                (container, transition_path),
                (container, approval_path),
                (declared_source, approval_path),
            ]
        )
        approval_introduction = introductions.get(approval_path)
        transition_introduction = introductions.get(transition_path)
        source_absent = object_ids[(declared_source, approval_path)] is None
        input_row = _pointer_value(transition, str(claim["json_pointer"]))
        expected_relative_approval = posixpath.relpath(approval_path, root)
        manifest = transition.get("git", {}).get("changed_paths_manifest", [])
        profile_valid = profile_valid and all(
            (
                golden.get("expected_claim_count") == 1,
                claim.get("claim_id") == "IO-01",
                sha256_bytes(transition_raw) == claim["transition_raw_sha256"],
                object_ids[(container, transition_path)]
                == claim["transition_git_blob"],
                reader.blob(current, transition_path) == transition_raw,
                sha256_bytes(approval_raw) == claim["approval_raw_sha256"],
                object_ids[(container, approval_path)] == claim["approval_git_blob"],
                reader.blob(current, approval_path) == approval_raw,
                source_absent,
                summaries[container].get("parents") == [declared_source],
                approval_introduction == container,
                transition_introduction == container,
                summaries[container].get("tree") == claim["container_tree"],
                transition.get("git", {}).get("source_commit") == declared_source,
                isinstance(manifest, list),
                transition_path in manifest,
                approval_path in manifest,
                isinstance(input_row, Mapping),
                input_row.get("path") == expected_relative_approval,
                input_row.get("sha256") == claim["approval_raw_sha256"],
                input_row.get("schema_version") == "2.0",
                input_row.get("role") == "append_only_evidence",
                container != INPUT_ORIGIN_CORRECTION_SUBJECT,
                reader.is_ancestor(container, INPUT_ORIGIN_CORRECTION_SUBJECT),
            )
        )
    except (ContractError, GitSubjectError, KeyError, TypeError, ValueError):
        profile_valid = False

    expected_full_paths = tuple(
        f"{root}/{relative}" for relative in INPUT_ORIGIN_CORRECTION_APPROVAL_PATHS
    )
    try:
        if set(approvals) != set(expected_full_paths):
            raise ValueError("V5 approval path set changed")
        selected = [approvals[path] for path in expected_full_paths]
        approval_blob_requests: list[tuple[str, str]] = []
        for approval in selected:
            subject = approval.get("subject", {})
            approved_commit = subject.get("git_commit")
            if not isinstance(approved_commit, str):
                raise ValueError("V5 approval subject is missing")
            for artifact in subject.get("artifact_digests", []):
                approval_blob_requests.append(
                    (
                        approved_commit,
                        normalize_repo_path(
                            posixpath.normpath(
                                posixpath.join(root, str(artifact["path"]))
                            )
                        ),
                    )
                )
        reader.read_blob_requests(approval_blob_requests)
        expected_subject = {
            "git_commit": INPUT_ORIGIN_CORRECTION_SUBJECT,
            "git_tree": INPUT_ORIGIN_CORRECTION_SUBJECT_TREE,
            "program_tree": INPUT_ORIGIN_CORRECTION_SUBJECT_PROGRAM_TREE,
        }
        expected_records = (
            ("APR-EPP-F01-MC-005", "material_change", "APR-EPP-F01-MC-004"),
            (
                "APR-EPP-F01-IMPL-005",
                "feature_implementation",
                "APR-EPP-F01-IMPL-004",
            ),
        )
        if selected[0].get("subject") != selected[1].get("subject"):
            raise ValueError("V5 approval subjects differ")
        for path, approval, expected, expected_raw_sha256, expected_blob in zip(
            expected_full_paths,
            selected,
            expected_records,
            INPUT_ORIGIN_CORRECTION_APPROVAL_SHA256,
            INPUT_ORIGIN_CORRECTION_APPROVAL_BLOBS,
            strict=True,
        ):
            approval_id, scope, superseded = expected
            subject = approval.get("subject", {})
            artifacts = subject.get("artifact_digests", [])
            profile_entries = [
                row
                for row in artifacts
                if row.get("path")
                == f"evidence/corrections/{INPUT_ORIGIN_CORRECTION_ID}.json"
            ]
            if not all(
                (
                    approval.get("approval_id") == approval_id,
                    approval.get("scope") == scope,
                    approval.get("program_id") == "EPP-2026",
                    approval.get("feature_id") == "EPP-F01",
                    approval.get("bundle_id") == "APB-EPP-F01-005",
                    approval.get("decision") == "approved",
                    approval.get("approved_at") == "2026-08-27T19:02:07Z",
                    approval.get("expires_at") is None,
                    approval.get("revocation_events") == [],
                    approval.get("supersedes") == [superseded],
                    all(
                        subject.get(key) == value
                        for key, value in expected_subject.items()
                    ),
                    len(artifacts) == 32,
                    len({row.get("path") for row in artifacts}) == 32,
                    profile_entries
                    == [
                        {
                            "path": (
                                "evidence/corrections/"
                                f"{INPUT_ORIGIN_CORRECTION_ID}.json"
                            ),
                            "sha256": INPUT_ORIGIN_CORRECTION_PROFILE_SHA256,
                        }
                    ],
                    strict_loads(reader.blob(current, path)) == approval,
                    sha256_bytes(reader.blob(current, path)) == expected_raw_sha256,
                    closed_object_ids[
                        (INPUT_ORIGIN_CORRECTION_APPROVAL_CONTAINER, path)
                    ]
                    == expected_blob,
                    _verify_approval_artifacts(reader, current, approval, root),
                )
            ):
                raise ValueError("approval record is not the exact V5 bundle")
            approval_container = reader.containing_commit(current, path)
            if not (
                approval_container == INPUT_ORIGIN_CORRECTION_APPROVAL_CONTAINER
                and reader.is_ancestor(
                    INPUT_ORIGIN_CORRECTION_SUBJECT, approval_container
                )
                and reader.is_ancestor(approval_container, current)
                and reader.blob(current, path) == reader.blob(approval_container, path)
            ):
                raise ValueError("V5 approval history is not append-only")
    except (GitSubjectError, KeyError, TypeError, ValueError):
        authority_valid = False

    resolved = profile_valid and authority_valid
    findings = [
        _finding(
            "TRANSITION_INPUT_ORIGIN_MISMATCH",
            "info" if resolved else "fatal",
            target[0],
            "EXACT_APPROVED_TR0027_INPUT_ORIGIN_DISPOSITION",
            (
                "IO-01",
                "declared:source_input",
                "authoritative:container_added_evidence",
            ),
            json_pointer=target[1],
            resolution_status="resolved" if resolved else "unresolved",
            correction_ref=correction_path if resolved else None,
        )
    ]
    if not profile_valid:
        findings.append(
            _finding(
                "TRANSITION_INPUT_CORRECTION_INVALID",
                "fatal",
                correction_path,
                "CLOSED_ONE_CLAIM_GIT_RECOMPUTATION",
            )
        )
    if not authority_valid:
        findings.append(
            _finding(
                "TRANSITION_INPUT_CORRECTION_UNAUTHORIZED",
                "fatal",
                f"{root}/evidence/approvals",
                "EXACT_V5_TWO_SCOPE_AUTHORITY",
            )
        )
    targets = frozenset({target}) if resolved else frozenset()
    return sorted(findings, key=Finding.sort_key), targets


def validate_repair_evidence_correction(
    reader: GitReader,
    source_commit: str,
    program_root: str,
    profile: Mapping[str, Any],
    approvals: Mapping[str, Mapping[str, Any]],
) -> tuple[
    list[Finding],
    frozenset[str],
    frozenset[tuple[str, str]],
]:
    """Recompute the sole approved two-claim repair-evidence disposition."""

    root = normalize_repo_path(program_root)
    correction_path = f"{root}/evidence/corrections/{REPAIR_CORRECTION_ID}.json"
    promoted_schema_path = f"{root}/schemas/repair-evidence-correction.schema.json"
    planning_schema_path = (
        "specs/076-control-plane-validator/contracts/"
        "repair-evidence-correction.schema.json"
    )
    profile_valid = True
    authority_valid = True
    golden: Mapping[str, Any] = {}
    current = ""

    try:
        current = reader.resolve_commit(source_commit)
        closed_requests = [
            (REPAIR_CORRECTION_SUBJECT, correction_path),
            (REPAIR_CORRECTION_SUBJECT, promoted_schema_path),
            (REPAIR_CORRECTION_SUBJECT, planning_schema_path),
            (current, correction_path),
            (current, promoted_schema_path),
            (current, planning_schema_path),
        ]
        closed_blobs = reader.read_blob_requests(closed_requests)
        closed_facts = reader.blob_facts(closed_requests)
        golden_raw = closed_blobs[(REPAIR_CORRECTION_SUBJECT, correction_path)]
        promoted_schema_raw = closed_blobs[
            (REPAIR_CORRECTION_SUBJECT, promoted_schema_path)
        ]
        planning_schema_raw = closed_blobs[
            (REPAIR_CORRECTION_SUBJECT, planning_schema_path)
        ]
        golden_value = strict_loads(golden_raw)
        promoted_schema = strict_loads(promoted_schema_raw)
        if not isinstance(golden_value, Mapping) or not isinstance(
            promoted_schema, Mapping
        ):
            raise ContractError("closed repair correction artifacts are not objects")
        golden = golden_value
        check_schema(promoted_schema)
        profile_valid = profile_valid and exact_schema_instance(
            promoted_schema, profile, golden
        )
        profile_valid = profile_valid and (
            sha256_bytes(golden_raw) == REPAIR_CORRECTION_PROFILE_SHA256
            and sha256_bytes(promoted_schema_raw) == REPAIR_CORRECTION_SCHEMA_SHA256
            and promoted_schema_raw == planning_schema_raw
            and closed_facts[(REPAIR_CORRECTION_SUBJECT, correction_path)].git_blob
            == REPAIR_CORRECTION_PROFILE_BLOB
            and closed_facts[(REPAIR_CORRECTION_SUBJECT, promoted_schema_path)].git_blob
            == REPAIR_CORRECTION_SCHEMA_BLOB
            and closed_facts[(REPAIR_CORRECTION_SUBJECT, planning_schema_path)].git_blob
            == REPAIR_CORRECTION_SCHEMA_BLOB
            and closed_blobs[(current, correction_path)] == golden_raw
            and closed_blobs[(current, promoted_schema_path)] == promoted_schema_raw
            and closed_blobs[(current, planning_schema_path)] == planning_schema_raw
        )
        correction_identity = reader.resolve_identity(REPAIR_CORRECTION_SUBJECT, root)
        profile_valid = profile_valid and (
            correction_identity.source_tree == REPAIR_CORRECTION_SUBJECT_TREE
            and correction_identity.program_tree
            == REPAIR_CORRECTION_SUBJECT_PROGRAM_TREE
            and reader.containing_commit(current, correction_path)
            == REPAIR_CORRECTION_SUBJECT
            and REPAIR_CORRECTION_SUBJECT != current
            and reader.is_ancestor(REPAIR_CORRECTION_SUBJECT, current)
        )
        checkpoint = golden.get("source_checkpoint", {})
        checkpoint_identity = reader.resolve_identity(
            str(checkpoint.get("git_commit")), root
        )
        profile_valid = profile_valid and (
            checkpoint_identity.source_tree == checkpoint.get("git_tree")
            and checkpoint_identity.program_tree == checkpoint.get("program_tree")
            and checkpoint_identity.source_commit != REPAIR_CORRECTION_SUBJECT
            and reader.is_ancestor(
                checkpoint_identity.source_commit, REPAIR_CORRECTION_SUBJECT
            )
        )
    except (ContractError, GitSubjectError, KeyError, TypeError, ValueError):
        profile_valid = False

    claims = list(golden.get("claims", []))
    cause_claim = claims[0] if len(claims) >= 1 else {}
    digest_claim = claims[1] if len(claims) >= 2 else {}
    occurrences = list(cause_claim.get("occurrences", []))
    cause_rows = [
        (
            str(row.get("path", "repair-evidence-target")),
            str(row.get("json_pointer", "")),
            f"{cause_claim.get('claim_id', 'repair-cause')}:{index}",
            str(cause_claim.get("recorded_value", "")),
            str(cause_claim.get("authoritative_value", "")),
        )
        for index, row in enumerate(occurrences, start=1)
    ]
    digest_row = (
        str(digest_claim.get("transition_path", "repair-evidence-target")),
        str(digest_claim.get("json_pointer", "")),
        str(digest_claim.get("claim_id", "repair-digest")),
        str(digest_claim.get("recorded_value", "")),
        str(digest_claim.get("authoritative_value", "")),
    )
    if (
        len(claims) != 2
        or len(occurrences) != 2
        or golden.get("expected_claim_count") != 2
        or cause_claim.get("expected_occurrence_count") != 2
    ):
        profile_valid = False

    try:
        if not profile_valid:
            raise ValueError("presented repair correction changed")
        cause_targets = frozenset(
            (str(row["path"]), str(row["json_pointer"])) for row in occurrences
        )
        if cause_targets != REPAIR_CAUSE_TARGETS:
            raise ValueError("repair cause occurrence set changed")
        target_transition = str(digest_claim["transition_path"])
        target_pointer = str(digest_claim["json_pointer"])
        if (target_transition, target_pointer) != REPAIR_DIGEST_TARGET:
            raise ValueError("repair digest target changed")

        additions = reader.added_path_commits(current, f"{root}/evidence")
        introducing_commits = {
            str(row["introducing_commit"]) for row in occurrences
        } | {str(digest_claim["introducing_commit"])}
        summaries = reader.commit_summaries(introducing_commits)
        blob_requests: list[tuple[str, str]] = []
        for row in occurrences:
            introducing = str(row["introducing_commit"])
            path = str(row["path"])
            blob_requests.extend([(introducing, path), (current, path)])
        digest_introducing = str(digest_claim["introducing_commit"])
        blob_requests.extend(
            [
                (digest_introducing, target_transition),
                (current, target_transition),
            ]
        )
        transition_raw = reader.blob(digest_introducing, target_transition)
        transition = strict_loads(transition_raw)
        authoritative_artifact = digest_claim["authoritative_artifact"]
        authoritative_path = str(authoritative_artifact["path"])
        authoritative_subject = str(transition["git"]["source_commit"])
        blob_requests.extend(
            [
                (authoritative_subject, authoritative_path),
                (current, authoritative_path),
            ]
        )
        blobs = reader.read_blob_requests(blob_requests)
        facts = reader.blob_facts(blob_requests)

        for row in occurrences:
            introducing = str(row["introducing_commit"])
            path = str(row["path"])
            pointer = str(row["json_pointer"])
            raw = blobs[(introducing, path)]
            state = strict_loads(raw)
            fact = facts[(introducing, path)]
            profile_valid = profile_valid and all(
                (
                    additions.get(path) == introducing,
                    reader.containing_commit(current, path) == introducing,
                    summaries[introducing].get("tree") == row["introducing_tree"],
                    fact.git_blob == row["git_blob"],
                    fact.sha256 == row["raw_sha256"],
                    blobs[(current, path)] == raw,
                    canonical_digest(state) == row["canonical_state_digest"],
                    _pointer_value(state, pointer) == cause_claim["recorded_value"],
                    cause_claim["recorded_value"] != cause_claim["authoritative_value"],
                    introducing != REPAIR_CORRECTION_SUBJECT,
                    reader.is_ancestor(introducing, REPAIR_CORRECTION_SUBJECT),
                )
            )

        state_paths = [
            path
            for path in reader.list_files(current, f"{root}/evidence/states")
            if path.endswith(".json")
        ]
        state_blobs = reader.read_blobs(current, state_paths)
        observed_cause_targets: set[tuple[str, str]] = set()
        cause_pointer = str(occurrences[0]["json_pointer"])
        for path, raw in state_blobs.items():
            try:
                state = strict_loads(raw)
                if (
                    _pointer_value(state, cause_pointer)
                    == cause_claim["recorded_value"]
                ):
                    observed_cause_targets.add((path, cause_pointer))
            except (ContractError, KeyError, TypeError, ValueError):
                continue
        current_state = strict_loads(reader.blob(current, f"{root}/program-state.json"))
        try:
            current_cause = _pointer_value(current_state, cause_pointer)
        except (KeyError, TypeError, ValueError):
            current_cause = None
        profile_valid = profile_valid and (
            frozenset(observed_cause_targets) == cause_targets
            and current_cause != cause_claim["recorded_value"]
        )

        transition_fact = facts[(digest_introducing, target_transition)]
        authoritative_fact = facts[(authoritative_subject, authoritative_path)]
        profile_valid = profile_valid and all(
            (
                additions.get(target_transition) == digest_introducing,
                reader.containing_commit(current, target_transition)
                == digest_introducing,
                summaries[digest_introducing].get("tree")
                == digest_claim["introducing_tree"],
                transition_fact.git_blob == digest_claim["transition_git_blob"],
                transition_fact.sha256 == digest_claim["transition_raw_sha256"],
                blobs[(current, target_transition)] == transition_raw,
                _pointer_value(transition, target_pointer)
                == digest_claim["recorded_value"],
                len(str(digest_claim["recorded_value"])) == 63,
                authoritative_fact.git_blob == authoritative_artifact["git_blob"],
                authoritative_fact.sha256 == authoritative_artifact["raw_sha256"],
                authoritative_fact.sha256 == digest_claim["authoritative_value"],
                blobs[(current, authoritative_path)]
                == blobs[(authoritative_subject, authoritative_path)],
                digest_claim["recorded_value"] != digest_claim["authoritative_value"],
                authoritative_subject != REPAIR_CORRECTION_SUBJECT,
                reader.is_ancestor(authoritative_subject, REPAIR_CORRECTION_SUBJECT),
                digest_introducing != REPAIR_CORRECTION_SUBJECT,
                reader.is_ancestor(digest_introducing, REPAIR_CORRECTION_SUBJECT),
            )
        )
    except (ContractError, GitSubjectError, KeyError, TypeError, ValueError):
        profile_valid = False

    expected_full_paths = tuple(
        f"{root}/{relative}" for relative in REPAIR_CORRECTION_APPROVAL_PATHS
    )
    try:
        if set(approvals) != set(expected_full_paths):
            raise ValueError("V7 approval path set changed")
        selected = [approvals[path] for path in expected_full_paths]
        if selected[0].get("subject") != selected[1].get("subject"):
            raise ValueError("V7 approval subjects differ")
        expected_subject = {
            "git_commit": REPAIR_CORRECTION_SUBJECT,
            "git_tree": REPAIR_CORRECTION_SUBJECT_TREE,
            "program_tree": REPAIR_CORRECTION_SUBJECT_PROGRAM_TREE,
        }
        expected_records = (
            ("APR-EPP-F01-MC-007", "material_change", "APR-EPP-F01-MC-006"),
            (
                "APR-EPP-F01-IMPL-007",
                "feature_implementation",
                "APR-EPP-F01-IMPL-006",
            ),
        )
        approval_container_summary = reader.commit_summaries(
            [REPAIR_CORRECTION_APPROVAL_CONTAINER]
        )[REPAIR_CORRECTION_APPROVAL_CONTAINER]
        approval_requests = [
            (REPAIR_CORRECTION_APPROVAL_CONTAINER, path) for path in expected_full_paths
        ] + [(current, path) for path in expected_full_paths]
        approval_blobs = reader.read_blob_requests(approval_requests)
        approval_facts = reader.blob_facts(approval_requests)
        for path, approval, expected, expected_sha, expected_blob in zip(
            expected_full_paths,
            selected,
            expected_records,
            REPAIR_CORRECTION_APPROVAL_SHA256,
            REPAIR_CORRECTION_APPROVAL_BLOBS,
            strict=True,
        ):
            approval_id, scope, superseded = expected
            subject = approval.get("subject", {})
            artifacts = subject.get("artifact_digests", [])
            profile_entries = [
                row
                for row in artifacts
                if row.get("path")
                == f"evidence/corrections/{REPAIR_CORRECTION_ID}.json"
            ]
            if not all(
                (
                    approval.get("approval_id") == approval_id,
                    approval.get("scope") == scope,
                    approval.get("program_id") == "EPP-2026",
                    approval.get("feature_id") == "EPP-F01",
                    approval.get("bundle_id") == "APB-EPP-F01-007",
                    approval.get("decision") == "approved_with_conditions",
                    approval.get("approved_at") == "2026-08-27T23:30:50Z",
                    approval.get("expires_at") is None,
                    approval.get("revocation_events") == [],
                    approval.get("supersedes") == [superseded],
                    all(
                        subject.get(key) == value
                        for key, value in expected_subject.items()
                    ),
                    len(artifacts) == 31,
                    len({row.get("path") for row in artifacts}) == 31,
                    profile_entries
                    == [
                        {
                            "path": (
                                f"evidence/corrections/{REPAIR_CORRECTION_ID}.json"
                            ),
                            "sha256": REPAIR_CORRECTION_PROFILE_SHA256,
                        }
                    ],
                    strict_loads(approval_blobs[(current, path)]) == approval,
                    approval_blobs[(current, path)]
                    == approval_blobs[(REPAIR_CORRECTION_APPROVAL_CONTAINER, path)],
                    approval_facts[(REPAIR_CORRECTION_APPROVAL_CONTAINER, path)].sha256
                    == expected_sha,
                    approval_facts[
                        (REPAIR_CORRECTION_APPROVAL_CONTAINER, path)
                    ].git_blob
                    == expected_blob,
                    _verify_approval_artifacts(reader, current, approval, root),
                    reader.containing_commit(current, path)
                    == REPAIR_CORRECTION_APPROVAL_CONTAINER,
                )
            ):
                raise ValueError("approval record is not the exact V7 bundle")
        if not (
            approval_container_summary.get("parents") == [REPAIR_CORRECTION_SUBJECT]
            and reader.is_ancestor(REPAIR_CORRECTION_APPROVAL_CONTAINER, current)
        ):
            raise ValueError("V7 approval history is not append-only")
    except (ContractError, GitSubjectError, KeyError, TypeError, ValueError):
        authority_valid = False

    resolved = profile_valid and authority_valid
    findings = [
        _finding(
            "REPAIR_EVIDENCE_CAUSE_ID_MISMATCH",
            "info" if resolved else "fatal",
            artifact,
            "EXACT_APPROVED_REPAIR_CAUSE_ID_DISPOSITION",
            (
                claim_id,
                f"recorded:{recorded}",
                f"authoritative:{authoritative}",
            ),
            json_pointer=pointer,
            resolution_status="resolved" if resolved else "unresolved",
            correction_ref=correction_path if resolved else None,
        )
        for artifact, pointer, claim_id, recorded, authoritative in cause_rows
    ]
    findings.append(
        _finding(
            "REPAIR_EVIDENCE_DIGEST_MISMATCH",
            "info" if resolved else "fatal",
            digest_row[0],
            "EXACT_APPROVED_REPAIR_DIGEST_DISPOSITION",
            (
                digest_row[2],
                f"recorded:{digest_row[3]}",
                f"authoritative:{digest_row[4]}",
            ),
            json_pointer=digest_row[1],
            resolution_status="resolved" if resolved else "unresolved",
            correction_ref=correction_path if resolved else None,
        )
    )
    if not profile_valid:
        findings.append(
            _finding(
                "REPAIR_EVIDENCE_CORRECTION_INVALID",
                "fatal",
                correction_path,
                "CLOSED_TWO_CLAIM_GIT_RECOMPUTATION",
            )
        )
    if not authority_valid:
        findings.append(
            _finding(
                "REPAIR_EVIDENCE_CORRECTION_UNAUTHORIZED",
                "fatal",
                f"{root}/evidence/approvals",
                "EXACT_V7_TWO_SCOPE_AUTHORITY",
            )
        )
    schema_targets = (
        frozenset(
            {
                *(artifact for artifact, _pointer in REPAIR_CAUSE_TARGETS),
                REPAIR_DIGEST_TARGET[0],
            }
        )
        if resolved
        else frozenset()
    )
    digest_targets = frozenset({REPAIR_DIGEST_TARGET}) if resolved else frozenset()
    return (
        sorted(findings, key=Finding.sort_key),
        schema_targets,
        digest_targets,
    )


def validate_checkpoint_evidence_correction(
    reader: GitReader,
    source_commit: str,
    program_root: str,
    profile: Mapping[str, Any],
    approvals: Mapping[str, Mapping[str, Any]],
) -> tuple[
    list[Finding],
    frozenset[tuple[str, str]],
    frozenset[tuple[str, str, str, str, str]],
]:
    """Recompute only the approved three-claim V8 checkpoint disposition."""

    root = normalize_repo_path(program_root)
    correction_path = f"{root}/evidence/corrections/{CHECKPOINT_CORRECTION_ID}.json"
    promoted_schema_path = f"{root}/schemas/checkpoint-evidence-correction.schema.json"
    planning_schema_path = (
        "specs/076-control-plane-validator/contracts/"
        "checkpoint-evidence-correction.schema.json"
    )
    profile_valid = True
    authority_valid = True
    golden: Mapping[str, Any] = {}
    current = ""

    try:
        current = reader.resolve_commit(source_commit)
        closed_paths = (correction_path, promoted_schema_path, planning_schema_path)
        requests = [
            (commit, path)
            for commit in (CHECKPOINT_CORRECTION_SUBJECT, current)
            for path in closed_paths
        ]
        blobs = reader.read_blob_requests(requests)
        facts = reader.blob_facts(requests)
        golden_raw = blobs[(CHECKPOINT_CORRECTION_SUBJECT, correction_path)]
        promoted_raw = blobs[(CHECKPOINT_CORRECTION_SUBJECT, promoted_schema_path)]
        planning_raw = blobs[(CHECKPOINT_CORRECTION_SUBJECT, planning_schema_path)]
        golden_value = strict_loads(golden_raw)
        promoted_schema = strict_loads(promoted_raw)
        if not isinstance(golden_value, Mapping) or not isinstance(
            promoted_schema, Mapping
        ):
            raise ContractError("V8 closed artifacts are not objects")
        golden = golden_value
        check_schema(promoted_schema)
        correction_identity = reader.resolve_identity(
            CHECKPOINT_CORRECTION_SUBJECT, root
        )
        checkpoint = golden.get("source_checkpoint", {})
        checkpoint_identity = reader.resolve_identity(
            str(checkpoint.get("git_commit")), root
        )
        profile_valid = all(
            (
                exact_schema_instance(promoted_schema, profile, golden),
                sha256_bytes(golden_raw) == CHECKPOINT_CORRECTION_PROFILE_SHA256,
                sha256_bytes(promoted_raw) == CHECKPOINT_CORRECTION_SCHEMA_SHA256,
                promoted_raw == planning_raw,
                facts[(CHECKPOINT_CORRECTION_SUBJECT, correction_path)].git_blob
                == CHECKPOINT_CORRECTION_PROFILE_BLOB,
                facts[(CHECKPOINT_CORRECTION_SUBJECT, promoted_schema_path)].git_blob
                == CHECKPOINT_CORRECTION_SCHEMA_BLOB,
                facts[(CHECKPOINT_CORRECTION_SUBJECT, planning_schema_path)].git_blob
                == CHECKPOINT_CORRECTION_SCHEMA_BLOB,
                all(
                    blobs[(current, path)]
                    == blobs[(CHECKPOINT_CORRECTION_SUBJECT, path)]
                    for path in closed_paths
                ),
                correction_identity.source_tree == CHECKPOINT_CORRECTION_SUBJECT_TREE,
                correction_identity.program_tree
                == CHECKPOINT_CORRECTION_SUBJECT_PROGRAM_TREE,
                reader.containing_commit(current, correction_path)
                == CHECKPOINT_CORRECTION_SUBJECT,
                current != CHECKPOINT_CORRECTION_SUBJECT,
                reader.is_ancestor(CHECKPOINT_CORRECTION_SUBJECT, current),
                checkpoint_identity.source_tree == checkpoint.get("git_tree"),
                checkpoint_identity.program_tree == checkpoint.get("program_tree"),
                checkpoint_identity.source_commit != CHECKPOINT_CORRECTION_SUBJECT,
                reader.is_ancestor(
                    checkpoint_identity.source_commit, CHECKPOINT_CORRECTION_SUBJECT
                ),
            )
        )
    except (ContractError, GitSubjectError, KeyError, TypeError, ValueError):
        profile_valid = False

    claims = list(golden.get("claims", []))
    digest_claims = claims[:2]
    event_claim = claims[2] if len(claims) > 2 else {}
    try:
        if not profile_valid or len(claims) != 3:
            raise ValueError("presented checkpoint correction changed")
        digest_targets = frozenset(
            (str(claim["transition_path"]), str(claim["json_pointer"]))
            for claim in digest_claims
        )
        authoritative = event_claim["authoritative_tuple"]
        event_targets = frozenset(
            {
                (
                    str(event_claim["transition_path"]),
                    str(authoritative["state_domain"]),
                    str(authoritative["event_kind"]),
                    str(authoritative["from_state"]),
                    str(authoritative["to_state"]),
                )
            }
        )
        if digest_targets != CHECKPOINT_DIGEST_TARGETS:
            raise ValueError("V8 digest target set changed")
        if event_targets != CHECKPOINT_EVENT_TARGETS:
            raise ValueError("V8 event target set changed")

        target_requests: list[tuple[str, str]] = []
        introducing_commits: set[str] = set()
        for claim in digest_claims:
            introducing = str(claim["introducing_commit"])
            transition_path = str(claim["transition_path"])
            artifact_path = str(claim["artifact_path"])
            introducing_commits.add(introducing)
            target_requests.extend(
                [
                    (introducing, transition_path),
                    (current, transition_path),
                    (introducing, artifact_path),
                ]
            )
        event_introducing = str(event_claim["introducing_commit"])
        event_path = str(event_claim["transition_path"])
        introducing_commits.add(event_introducing)
        target_requests.extend([(event_introducing, event_path), (current, event_path)])
        target_blobs = reader.read_blob_requests(target_requests)
        target_facts = reader.blob_facts(target_requests)
        summaries = reader.commit_summaries(introducing_commits)

        for claim in digest_claims:
            introducing = str(claim["introducing_commit"])
            transition_path = str(claim["transition_path"])
            artifact_path = str(claim["artifact_path"])
            transition_raw = target_blobs[(introducing, transition_path)]
            transition = strict_loads(transition_raw)
            transition_fact = target_facts[(introducing, transition_path)]
            artifact_fact = target_facts[(introducing, artifact_path)]
            source_identity = reader.resolve_identity(str(claim["source_commit"]), root)
            introducing_identity = reader.resolve_identity(introducing, root)
            profile_valid = profile_valid and all(
                (
                    source_identity.source_tree == claim["source_tree"],
                    source_identity.program_tree == claim["source_program_tree"],
                    introducing_identity.source_tree == claim["introducing_tree"],
                    introducing_identity.program_tree
                    == claim["introducing_program_tree"],
                    summaries[introducing].get("parents")
                    == [str(claim["source_commit"])],
                    reader.containing_commit(current, transition_path) == introducing,
                    transition_fact.git_blob == claim["transition_git_blob"],
                    transition_fact.sha256 == claim["transition_raw_sha256"],
                    target_blobs[(current, transition_path)] == transition_raw,
                    _pointer_value(transition, str(claim["json_pointer"]))
                    == claim["recorded_value"],
                    artifact_fact.git_blob == claim["artifact_git_blob"],
                    artifact_fact.sha256 == claim["authoritative_value"],
                    claim["recorded_value"] != claim["authoritative_value"],
                    introducing != CHECKPOINT_CORRECTION_SUBJECT,
                    reader.is_ancestor(introducing, CHECKPOINT_CORRECTION_SUBJECT),
                )
            )

        event_raw = target_blobs[(event_introducing, event_path)]
        event_transition = strict_loads(event_raw)
        event_fact = target_facts[(event_introducing, event_path)]
        recorded = event_claim["recorded_tuple"]
        source_identity = reader.resolve_identity(
            str(event_claim["source_commit"]), root
        )
        introducing_identity = reader.resolve_identity(event_introducing, root)
        policy = strict_loads(reader.blob(current, f"{root}/lifecycle-policy.json"))
        repair_rules = [
            row
            for row in policy.get("event_rules", [])
            if row.get("state_domain") == authoritative["state_domain"]
            and row.get("event_kind") == authoritative["event_kind"]
        ]
        profile_valid = profile_valid and all(
            (
                source_identity.source_tree == event_claim["source_tree"],
                source_identity.program_tree == event_claim["source_program_tree"],
                introducing_identity.source_tree == event_claim["introducing_tree"],
                introducing_identity.program_tree
                == event_claim["introducing_program_tree"],
                summaries[event_introducing].get("parents")
                == [str(event_claim["source_commit"])],
                reader.containing_commit(current, event_path) == event_introducing,
                event_fact.git_blob == event_claim["transition_git_blob"],
                event_fact.sha256 == event_claim["transition_raw_sha256"],
                target_blobs[(current, event_path)] == event_raw,
                all(
                    event_transition.get(key) == value
                    for key, value in recorded.items()
                ),
                recorded != authoritative,
                len(repair_rules) == 1,
                repair_rules[0].get("may_preserve_state") is True,
                repair_rules[0].get("required_evidence")
                == list(event_claim["required_evidence_mapping"]),
                event_introducing != CHECKPOINT_CORRECTION_SUBJECT,
                reader.is_ancestor(event_introducing, CHECKPOINT_CORRECTION_SUBJECT),
            )
        )
    except (ContractError, GitSubjectError, KeyError, TypeError, ValueError):
        profile_valid = False

    expected_paths = tuple(f"{root}/{path}" for path in CHECKPOINT_APPROVAL_PATHS)
    try:
        if set(approvals) != set(expected_paths):
            raise ValueError("V8 approval path set changed")
        approval_requests = [
            (commit, path)
            for commit in (CHECKPOINT_APPROVAL_CONTAINER, current)
            for path in expected_paths
        ]
        approval_blobs = reader.read_blob_requests(approval_requests)
        approval_facts = reader.blob_facts(approval_requests)
        summary = reader.commit_summaries([CHECKPOINT_APPROVAL_CONTAINER])[
            CHECKPOINT_APPROVAL_CONTAINER
        ]
        for path, expected_sha, expected_blob in zip(
            expected_paths,
            CHECKPOINT_APPROVAL_SHA256,
            CHECKPOINT_APPROVAL_BLOBS,
            strict=True,
        ):
            approval = approvals[path]
            fixed_raw = approval_blobs[(CHECKPOINT_APPROVAL_CONTAINER, path)]
            if not all(
                (
                    strict_loads(fixed_raw) == approval,
                    approval_blobs[(current, path)] == fixed_raw,
                    approval_facts[(CHECKPOINT_APPROVAL_CONTAINER, path)].sha256
                    == expected_sha,
                    approval_facts[(CHECKPOINT_APPROVAL_CONTAINER, path)].git_blob
                    == expected_blob,
                    reader.containing_commit(current, path)
                    == CHECKPOINT_APPROVAL_CONTAINER,
                    _verify_approval_artifacts(reader, current, approval, root),
                )
            ):
                raise ValueError("approval record is not the exact V8 bundle")
        selected = [approvals[path] for path in expected_paths]
        if not all(
            (
                selected[0].get("scope") == "material_change",
                selected[1].get("scope") == "feature_implementation",
                selected[0].get("subject") == selected[1].get("subject"),
                selected[0].get("subject", {}).get("git_commit")
                == CHECKPOINT_CORRECTION_SUBJECT,
                summary.get("parents") == [CHECKPOINT_CORRECTION_SUBJECT],
                CHECKPOINT_APPROVAL_CONTAINER != current,
                reader.is_ancestor(CHECKPOINT_APPROVAL_CONTAINER, current),
            )
        ):
            raise ValueError("V8 approval history is not append-only")
    except (ContractError, GitSubjectError, KeyError, TypeError, ValueError):
        authority_valid = False

    resolved = profile_valid and authority_valid
    findings = [
        *[
            _finding(
                "CHECKPOINT_OUTPUT_DIGEST_MISMATCH",
                "info" if resolved else "fatal",
                str(claim.get("transition_path", correction_path)),
                "EXACT_APPROVED_V8_CHECKPOINT_DISPOSITION",
                json_pointer=str(claim.get("json_pointer", "")),
                resolution_status="resolved" if resolved else "unresolved",
                correction_ref=correction_path if resolved else None,
            )
            for claim in digest_claims
        ],
        _finding(
            "CHECKPOINT_EVENT_RULE_MISMATCH",
            "info" if resolved else "fatal",
            str(event_claim.get("transition_path", correction_path)),
            "EXACT_APPROVED_V8_CHECKPOINT_DISPOSITION",
            json_pointer="/state_domain",
            resolution_status="resolved" if resolved else "unresolved",
            correction_ref=correction_path if resolved else None,
        ),
    ]
    if not profile_valid:
        findings.append(
            _finding(
                "CHECKPOINT_EVIDENCE_CORRECTION_INVALID",
                "fatal",
                correction_path,
                "CLOSED_THREE_CLAIM_GIT_RECOMPUTATION",
            )
        )
    if not authority_valid:
        findings.append(
            _finding(
                "CHECKPOINT_EVIDENCE_CORRECTION_UNAUTHORIZED",
                "fatal",
                f"{root}/evidence/approvals",
                "EXACT_V8_TWO_SCOPE_AUTHORITY",
            )
        )
    return (
        sorted(findings, key=Finding.sort_key),
        CHECKPOINT_DIGEST_TARGETS if resolved else frozenset(),
        CHECKPOINT_EVENT_TARGETS if resolved else frozenset(),
    )


def _preflight_original_finding(
    code: str,
    artifact: str,
    pointer: str,
    correction_path: str,
    resolved: bool,
) -> Finding:
    finding = _finding(
        code,
        "info" if resolved else "fatal",
        artifact,
        "EXACT_APPROVED_V9_PREFLIGHT_DISPOSITION",
        json_pointer=pointer,
        resolution_status="resolved" if resolved else "unresolved",
        correction_ref=correction_path if resolved else None,
    )
    return replace(
        finding,
        recovery=(
            "Do not rewrite history; inspect the exact approved V9 preflight "
            "correction and its bounded recomputation."
        ),
    )


def validate_preflight_evidence_correction(
    reader: GitReader,
    source_commit: str,
    program_root: str,
    profile: Mapping[str, Any],
    approvals: Mapping[str, Mapping[str, Any]],
) -> tuple[list[Finding], frozenset[str], frozenset[str]]:
    """Recompute only the approved two-claim V9 preflight disposition."""

    root = normalize_repo_path(program_root)
    correction_path = f"{root}/evidence/corrections/{PREFLIGHT_CORRECTION_ID}.json"
    promoted_schema_path = f"{root}/schemas/preflight-evidence-correction.schema.json"
    planning_schema_path = (
        "specs/076-control-plane-validator/contracts/"
        "preflight-evidence-correction.schema.json"
    )
    discovery_schema_path = f"{root}/schemas/v8-discovery-evidence.schema.json"
    discovery_planning_schema_path = (
        "specs/076-control-plane-validator/contracts/v8-discovery-evidence.schema.json"
    )
    profile_valid = True
    authority_valid = True
    golden: Mapping[str, Any] = {}
    current = ""

    try:
        current = reader.resolve_commit(source_commit)
        closed_paths = (
            correction_path,
            promoted_schema_path,
            planning_schema_path,
            discovery_schema_path,
            discovery_planning_schema_path,
        )
        requests = [
            (commit, path)
            for commit in (PREFLIGHT_CORRECTION_SUBJECT, current)
            for path in closed_paths
        ]
        blobs = reader.read_blob_requests(requests)
        facts = reader.blob_facts(requests)
        golden_raw = blobs[(PREFLIGHT_CORRECTION_SUBJECT, correction_path)]
        promoted_raw = blobs[(PREFLIGHT_CORRECTION_SUBJECT, promoted_schema_path)]
        planning_raw = blobs[(PREFLIGHT_CORRECTION_SUBJECT, planning_schema_path)]
        discovery_schema_raw = blobs[
            (PREFLIGHT_CORRECTION_SUBJECT, discovery_schema_path)
        ]
        discovery_planning_raw = blobs[
            (PREFLIGHT_CORRECTION_SUBJECT, discovery_planning_schema_path)
        ]
        golden_value = strict_loads(golden_raw)
        promoted_schema = strict_loads(promoted_raw)
        discovery_schema = strict_loads(discovery_schema_raw)
        if not all(
            isinstance(value, Mapping)
            for value in (golden_value, promoted_schema, discovery_schema)
        ):
            raise ContractError("V9 closed artifacts are not objects")
        golden = golden_value
        check_schema(promoted_schema)
        check_schema(discovery_schema)
        correction_identity = reader.resolve_identity(
            PREFLIGHT_CORRECTION_SUBJECT, root
        )
        profile_valid = profile_valid and all(
            (
                exact_schema_instance(promoted_schema, profile, golden),
                sha256_bytes(golden_raw) == PREFLIGHT_CORRECTION_PROFILE_SHA256,
                sha256_bytes(promoted_raw) == PREFLIGHT_CORRECTION_SCHEMA_SHA256,
                promoted_raw == planning_raw,
                sha256_bytes(discovery_schema_raw) == PREFLIGHT_DISCOVERY_SCHEMA_SHA256,
                discovery_schema_raw == discovery_planning_raw,
                facts[(PREFLIGHT_CORRECTION_SUBJECT, correction_path)].git_blob
                == PREFLIGHT_CORRECTION_PROFILE_BLOB,
                facts[(PREFLIGHT_CORRECTION_SUBJECT, promoted_schema_path)].git_blob
                == PREFLIGHT_CORRECTION_SCHEMA_BLOB,
                facts[(PREFLIGHT_CORRECTION_SUBJECT, planning_schema_path)].git_blob
                == PREFLIGHT_CORRECTION_SCHEMA_BLOB,
                facts[(PREFLIGHT_CORRECTION_SUBJECT, discovery_schema_path)].git_blob
                == PREFLIGHT_DISCOVERY_SCHEMA_BLOB,
                facts[
                    (PREFLIGHT_CORRECTION_SUBJECT, discovery_planning_schema_path)
                ].git_blob
                == PREFLIGHT_DISCOVERY_SCHEMA_BLOB,
                all(
                    blobs[(current, path)]
                    == blobs[(PREFLIGHT_CORRECTION_SUBJECT, path)]
                    for path in closed_paths
                ),
                correction_identity.source_tree == PREFLIGHT_CORRECTION_SUBJECT_TREE,
                correction_identity.program_tree
                == PREFLIGHT_CORRECTION_SUBJECT_PROGRAM_TREE,
                reader.containing_commit(current, correction_path)
                == PREFLIGHT_CORRECTION_SUBJECT,
                current != PREFLIGHT_CORRECTION_SUBJECT,
                reader.is_ancestor(PREFLIGHT_CORRECTION_SUBJECT, current),
            )
        )
        checkpoint = golden.get("source_checkpoint", {})
        checkpoint_identity = reader.resolve_identity(
            str(checkpoint.get("git_commit")), root
        )
        profile_valid = profile_valid and all(
            (
                checkpoint_identity.source_tree == checkpoint.get("git_tree"),
                checkpoint_identity.program_tree == checkpoint.get("program_tree"),
                checkpoint_identity.source_commit != PREFLIGHT_CORRECTION_SUBJECT,
                reader.is_ancestor(
                    checkpoint_identity.source_commit, PREFLIGHT_CORRECTION_SUBJECT
                ),
            )
        )
    except (ContractError, GitSubjectError, KeyError, TypeError, ValueError):
        profile_valid = False

    claims = list(golden.get("claims", []))
    discovery_claim = claims[0] if len(claims) > 0 else {}
    manifest_claim = claims[1] if len(claims) > 1 else {}
    if len(claims) != 2 or golden.get("expected_claim_count") != 2:
        profile_valid = False

    try:
        introducing = str(discovery_claim["introducing_commit"])
        manifest_introducing = str(manifest_claim["introducing_commit"])
        if introducing != manifest_introducing:
            raise ValueError("V9 target introductions differ")
        summaries = reader.commit_summaries([introducing])
        introducing_identity = reader.resolve_identity(introducing, root)
        additions = reader.added_path_commits(current, f"{root}/evidence")
        target_requests = [
            (introducing, PREFLIGHT_DISCOVERY_TARGET),
            (current, PREFLIGHT_DISCOVERY_TARGET),
            (manifest_introducing, PREFLIGHT_MANIFEST_TARGET),
            (current, PREFLIGHT_MANIFEST_TARGET),
            (PREFLIGHT_CORRECTION_SUBJECT, discovery_schema_path),
        ]
        target_blobs = reader.read_blob_requests(target_requests)
        target_facts = reader.blob_facts(target_requests)
        discovery_raw = target_blobs[(introducing, PREFLIGHT_DISCOVERY_TARGET)]
        transition_raw = target_blobs[(manifest_introducing, PREFLIGHT_MANIFEST_TARGET)]
        discovery_value = strict_loads(discovery_raw)
        transition = strict_loads(transition_raw)
        external_schema = strict_loads(
            target_blobs[(PREFLIGHT_CORRECTION_SUBJECT, discovery_schema_path)]
        )
        recorded_manifest = transition["git"]["changed_paths_manifest"]
        if not isinstance(recorded_manifest, list):
            raise ContractError("TR-0051 manifest is not a list")
        container_value = summaries[manifest_introducing].get("paths")
        if not isinstance(container_value, list) or not all(
            isinstance(path, str) for path in container_value
        ):
            raise ContractError("TR-0051 container path set is invalid")
        container_paths = [str(path) for path in container_value]
        sorted_manifest = sorted(recorded_manifest)
        discovery_fact = target_facts[(introducing, PREFLIGHT_DISCOVERY_TARGET)]
        transition_fact = target_facts[
            (manifest_introducing, PREFLIGHT_MANIFEST_TARGET)
        ]
        profile_valid = profile_valid and all(
            (
                introducing_identity.source_tree == discovery_claim["introducing_tree"],
                introducing_identity.program_tree
                == discovery_claim["introducing_program_tree"],
                introducing_identity.source_tree == manifest_claim["introducing_tree"],
                introducing_identity.program_tree
                == manifest_claim["introducing_program_tree"],
                additions.get(PREFLIGHT_DISCOVERY_TARGET) == introducing,
                additions.get(PREFLIGHT_MANIFEST_TARGET) == manifest_introducing,
                reader.containing_commit(current, PREFLIGHT_DISCOVERY_TARGET)
                == introducing,
                reader.containing_commit(current, PREFLIGHT_MANIFEST_TARGET)
                == manifest_introducing,
                sha256_bytes(discovery_raw) == discovery_claim["artifact_raw_sha256"],
                discovery_fact.git_blob == discovery_claim["artifact_git_blob"],
                sha256_bytes(transition_raw) == manifest_claim["transition_raw_sha256"],
                transition_fact.git_blob == manifest_claim["transition_git_blob"],
                target_blobs[(current, PREFLIGHT_DISCOVERY_TARGET)] == discovery_raw,
                target_blobs[(current, PREFLIGHT_MANIFEST_TARGET)] == transition_raw,
                discovery_claim["artifact_path"] == PREFLIGHT_DISCOVERY_TARGET,
                manifest_claim["transition_path"] == PREFLIGHT_MANIFEST_TARGET,
                discovery_claim["json_pointer"] == "/$schema",
                discovery_claim["recorded_presence"] is False,
                "$schema" not in discovery_value,
                not validate_schema(external_schema, discovery_value),
                discovery_claim["external_schema_path"] == discovery_schema_path,
                discovery_claim["planning_schema_path"]
                == discovery_planning_schema_path,
                discovery_claim["external_schema_id"] == external_schema.get("$id"),
                discovery_claim["external_schema_raw_sha256"]
                == PREFLIGHT_DISCOVERY_SCHEMA_SHA256,
                discovery_claim["external_schema_git_blob"]
                == PREFLIGHT_DISCOVERY_SCHEMA_BLOB,
                manifest_claim["json_pointer"] == "/git/changed_paths_manifest",
                manifest_claim["recorded_manifest_count"] == len(recorded_manifest),
                manifest_claim["recorded_unique_count"] == len(set(recorded_manifest)),
                manifest_claim["recorded_manifest_digest"]
                == canonical_digest(recorded_manifest),
                manifest_claim["authoritative_sorted_manifest_digest"]
                == canonical_digest(sorted_manifest),
                manifest_claim["container_changed_paths_digest"]
                == canonical_digest(container_paths),
                recorded_manifest != sorted_manifest,
                sorted_manifest == container_paths,
                len(recorded_manifest) == len(set(recorded_manifest)) == 35,
                set(recorded_manifest) == set(container_paths),
                manifest_claim["transition_self_path"] == PREFLIGHT_MANIFEST_TARGET,
                manifest_claim["recorded_self_path_index"]
                == recorded_manifest.index(PREFLIGHT_MANIFEST_TARGET),
                manifest_claim["sorted_self_path_index"]
                == sorted_manifest.index(PREFLIGHT_MANIFEST_TARGET),
                manifest_claim["complete_set_equal"] is True,
                manifest_claim["duplicates_present"] is False,
                manifest_claim["missing_paths"] == [],
                manifest_claim["extra_paths"] == [],
                introducing != PREFLIGHT_CORRECTION_SUBJECT,
                reader.is_ancestor(introducing, PREFLIGHT_CORRECTION_SUBJECT),
            )
        )
    except (ContractError, GitSubjectError, KeyError, TypeError, ValueError):
        profile_valid = False

    expected_paths = tuple(f"{root}/{path}" for path in PREFLIGHT_APPROVAL_PATHS)
    try:
        if set(approvals) != set(expected_paths):
            raise ValueError("V9 approval path set changed")
        selected = [approvals[path] for path in expected_paths]
        if selected[0].get("subject") != selected[1].get("subject"):
            raise ValueError("V9 approval subjects differ")
        expected_records = (
            ("APR-EPP-F01-MC-009", "material_change", "APR-EPP-F01-MC-008"),
            (
                "APR-EPP-F01-IMPL-009",
                "feature_implementation",
                "APR-EPP-F01-IMPL-008",
            ),
        )
        approval_summary = reader.commit_summaries([PREFLIGHT_APPROVAL_CONTAINER])[
            PREFLIGHT_APPROVAL_CONTAINER
        ]
        approval_requests = [
            (commit, path)
            for commit in (PREFLIGHT_APPROVAL_CONTAINER, current)
            for path in expected_paths
        ]
        approval_blobs = reader.read_blob_requests(approval_requests)
        approval_facts = reader.blob_facts(approval_requests)
        for path, approval, expected, expected_sha, expected_blob in zip(
            expected_paths,
            selected,
            expected_records,
            PREFLIGHT_APPROVAL_SHA256,
            PREFLIGHT_APPROVAL_BLOBS,
            strict=True,
        ):
            approval_id, scope, superseded = expected
            subject = approval.get("subject", {})
            artifacts = subject.get("artifact_digests", [])
            if not all(
                (
                    approval.get("approval_id") == approval_id,
                    approval.get("scope") == scope,
                    approval.get("program_id") == "EPP-2026",
                    approval.get("feature_id") == "EPP-F01",
                    approval.get("bundle_id") == "APB-EPP-F01-009",
                    approval.get("decision") == "approved_with_conditions",
                    approval.get("approved_at") == "2026-08-28T12:15:45Z",
                    approval.get("expires_at") is None,
                    approval.get("revocation_events") == [],
                    approval.get("supersedes") == [superseded],
                    subject.get("git_commit") == PREFLIGHT_CORRECTION_SUBJECT,
                    subject.get("git_tree") == PREFLIGHT_CORRECTION_SUBJECT_TREE,
                    subject.get("program_tree")
                    == PREFLIGHT_CORRECTION_SUBJECT_PROGRAM_TREE,
                    len(artifacts) == 31,
                    len({row.get("path") for row in artifacts}) == 31,
                    strict_loads(approval_blobs[(current, path)]) == approval,
                    approval_blobs[(current, path)]
                    == approval_blobs[(PREFLIGHT_APPROVAL_CONTAINER, path)],
                    approval_facts[(PREFLIGHT_APPROVAL_CONTAINER, path)].sha256
                    == expected_sha,
                    approval_facts[(PREFLIGHT_APPROVAL_CONTAINER, path)].git_blob
                    == expected_blob,
                    _verify_approval_artifacts(reader, current, approval, root),
                    reader.containing_commit(current, path)
                    == PREFLIGHT_APPROVAL_CONTAINER,
                )
            ):
                raise ValueError("approval record is not the exact V9 bundle")
        if not (
            approval_summary.get("parents") == [PREFLIGHT_CORRECTION_SUBJECT]
            and PREFLIGHT_APPROVAL_CONTAINER != current
            and reader.is_ancestor(PREFLIGHT_APPROVAL_CONTAINER, current)
        ):
            raise ValueError("V9 approval history is not append-only")
    except (ContractError, GitSubjectError, KeyError, TypeError, ValueError):
        authority_valid = False

    resolved = profile_valid and authority_valid
    findings = [
        _preflight_original_finding(
            "SCHEMA_REFERENCE_MISSING",
            PREFLIGHT_DISCOVERY_TARGET,
            "/$schema",
            correction_path,
            resolved,
        ),
        _preflight_original_finding(
            "TRANSITION_MANIFEST_MISMATCH",
            PREFLIGHT_MANIFEST_TARGET,
            "/git/changed_paths_manifest",
            correction_path,
            resolved,
        ),
    ]
    if not profile_valid:
        findings.append(
            _finding(
                "PREFLIGHT_EVIDENCE_CORRECTION_INVALID",
                "fatal",
                correction_path,
                "CLOSED_TWO_CLAIM_GIT_RECOMPUTATION",
            )
        )
    if not authority_valid:
        findings.append(
            _finding(
                "PREFLIGHT_EVIDENCE_CORRECTION_UNAUTHORIZED",
                "fatal",
                f"{root}/evidence/approvals",
                "EXACT_V9_TWO_SCOPE_AUTHORITY",
            )
        )
    schema_targets = (
        frozenset({PREFLIGHT_DISCOVERY_TARGET}) if resolved else frozenset()
    )
    manifest_targets = (
        frozenset({PREFLIGHT_MANIFEST_TARGET}) if resolved else frozenset()
    )
    return sorted(findings, key=Finding.sort_key), schema_targets, manifest_targets


def _validate_documents(
    reader: GitReader,
    commit: str,
    program_root: str,
    manifest: list[dict[str, str]],
    findings: list[Finding],
) -> dict[str, Any]:
    documents: dict[str, Any] = {}
    paths = [
        item["path"]
        for item in manifest
        if item["path"].startswith(f"{program_root}/")
        and item["path"].endswith(".json")
    ]
    for path in paths:
        value = _load_json(reader, commit, path, findings)
        if value is not None:
            documents[path] = value
    for relative in REQUIRED_JSON:
        path = f"{program_root}/{relative}"
        if path not in documents:
            findings.append(
                _finding(
                    "ARTIFACT_MISSING", "fatal", path, "CONTROL_PLANE_REQUIRED_SET"
                )
            )
    for path, value in sorted(documents.items()):
        if "/schemas/" in path:
            if isinstance(value, dict):
                try:
                    check_schema(value)
                except ContractError:
                    findings.append(
                        _finding(
                            "SCHEMA_META_INVALID", "fatal", path, "DRAFT_2020_12_META"
                        )
                    )
            continue
        if not isinstance(value, dict):
            findings.append(
                _finding("JSON_TOP_LEVEL_INVALID", "fatal", path, "OBJECT_REQUIRED")
            )
            continue
        routed_schema_path = EPP_F01B_SCHEMA_ROUTED_DOCUMENTS.get(path)
        if routed_schema_path is not None:
            schema = documents.get(routed_schema_path)
            if not isinstance(schema, dict):
                findings.append(
                    _finding(
                        "SCHEMA_REFERENCE_MISSING",
                        "fatal",
                        path,
                        "FROZEN_EPP_F01B_SCHEMA_ROUTE",
                    )
                )
            elif validate_schema(schema, value):
                findings.append(
                    _finding(
                        "SCHEMA_VALIDATION_FAILED",
                        "fatal",
                        path,
                        "FROZEN_EPP_F01B_SCHEMA_INSTANCE",
                    )
                )
            continue
        version = value.get("schema_version")
        if version is not None:
            try:
                require_compatible_version(version)
            except UnsupportedVersionError as exc:
                findings.append(
                    _finding(exc.kind, "fatal", path, "EXPLICIT_COMPATIBILITY")
                )
                continue
        schema_ref = value.get("$schema")
        if not isinstance(schema_ref, str):
            findings.append(
                _finding("SCHEMA_REFERENCE_MISSING", "fatal", path, "SCHEMA_REFERENCE")
            )
            continue
        resolved = _schema_path(path, schema_ref, program_root)
        schema = documents.get(resolved or "")
        if not isinstance(schema, dict):
            findings.append(
                _finding("SCHEMA_REFERENCE_MISSING", "fatal", path, "SCHEMA_REFERENCE")
            )
            continue
        schema_version = (
            schema.get("properties", {}).get("schema_version", {}).get("const")
        )
        if (
            version == "1.0"
            and schema_version == "2.0"
            and ("/evidence/states/" in path or "/evidence/transitions/" in path)
        ):
            continue
        if validate_schema(schema, value):
            findings.append(
                _finding("SCHEMA_VALIDATION_FAILED", "fatal", path, "SCHEMA_INSTANCE")
            )
    return documents


def _artifact_repo_path(program_root: str, relative: object) -> str:
    if not isinstance(relative, str):
        raise GitSubjectError("artifact path is not a string")
    joined = posixpath.normpath(posixpath.join(program_root, relative))
    return normalize_repo_path(joined)


def _validate_transition_history(
    reader: GitReader,
    source_commit: str,
    transitions: Sequence[Mapping[str, Any]],
    program_root: str,
    findings: list[Finding],
    corrected_input_targets: frozenset[tuple[str, str]] = frozenset(),
    corrected_digest_targets: frozenset[tuple[str, str]] = frozenset(),
    corrected_manifest_targets: frozenset[str] = frozenset(),
) -> None:
    """Bind every v2 transition to immutable raw bytes and its complete Git edge."""

    current = reader.resolve_commit(source_commit)
    if not corrected_input_targets.issubset({INPUT_ORIGIN_TARGET}):
        findings.append(
            _finding(
                "TRANSITION_INPUT_CORRECTION_INVALID",
                "fatal",
                f"{program_root}/evidence/corrections",
                "NO_GENERIC_INPUT_ORIGIN_BYPASS",
            )
        )
        corrected_input_targets = frozenset()
    if not corrected_digest_targets.issubset(
        {
            REPAIR_DIGEST_TARGET,
            *CHECKPOINT_DIGEST_TARGETS,
            REV58_DIGEST_TARGET,
            *F01B_ACTIVATION_DIGEST_TARGETS,
            *F01B_LEASE_CHECKPOINT_DIGEST_TARGETS,
        }
    ):
        findings.append(
            _finding(
                "REPAIR_EVIDENCE_CORRECTION_INVALID",
                "fatal",
                f"{program_root}/evidence/corrections",
                "NO_GENERIC_TRANSITION_DIGEST_BYPASS",
            )
        )
        corrected_digest_targets = frozenset()
    if not corrected_manifest_targets.issubset({PREFLIGHT_MANIFEST_TARGET}):
        findings.append(
            _finding(
                "PREFLIGHT_EVIDENCE_CORRECTION_INVALID",
                "fatal",
                f"{program_root}/evidence/corrections",
                "NO_GENERIC_TRANSITION_MANIFEST_BYPASS",
            )
        )
        corrected_manifest_targets = frozenset()
    v2 = [row for row in transitions if row.get("schema_version") == "2.0"]
    if not v2:
        return
    transition_root = f"{program_root}/evidence/transitions"
    try:
        additions = reader.added_path_commits(current, transition_root)
        paths = {
            str(
                row.get("transition_id")
            ): f"{transition_root}/{row.get('transition_id')}.json"
            for row in v2
        }
        containers = {
            transition_id: additions[path] for transition_id, path in paths.items()
        }
        source_commits = {str(row.get("git", {}).get("source_commit")) for row in v2}
        if any(not HEX40.fullmatch(commit) for commit in source_commits):
            raise GitSubjectError("transition source identity is invalid")
        summaries = reader.commit_summaries([*containers.values(), *source_commits])
        program_trees = reader.object_ids(
            (commit, program_root) for commit in source_commits
        )
        requests: list[tuple[str, str]] = []
        for row in v2:
            transition_id = str(row.get("transition_id"))
            source = str(row["git"]["source_commit"])
            container = containers[transition_id]
            transition_path = paths[transition_id]
            requests.extend([(current, transition_path), (container, transition_path)])
            for index, artifact in enumerate(row.get("inputs", [])):
                input_target = (transition_path, f"/inputs/{index}")
                if (
                    input_target == INPUT_ORIGIN_TARGET
                    and input_target in corrected_input_targets
                ):
                    continue
                requests.append(
                    (source, _artifact_repo_path(program_root, artifact.get("path")))
                )
            for artifact in row.get("outputs", []):
                requests.append(
                    (container, _artifact_repo_path(program_root, artifact.get("path")))
                )
        blobs = reader.read_blob_requests(requests)
    except (GitSubjectError, KeyError, TypeError):
        findings.append(
            _finding(
                "TRANSITION_HISTORY_UNRESOLVED",
                "fatal",
                transition_root,
                "APPEND_ONLY_GIT_HISTORY",
            )
        )
        return

    for row in v2:
        transition_id = str(row.get("transition_id"))
        artifact = f"{transition_root}/{transition_id}.json"
        git_record = row.get("git")
        if not isinstance(git_record, Mapping):
            continue
        source = str(git_record.get("source_commit"))
        container = containers[transition_id]
        source_summary = summaries[source]
        container_summary = summaries[container]
        manifest = git_record.get("changed_paths_manifest")
        actual_paths = set(cast(list[str], container_summary.get("paths", [])))
        declared_paths = set(manifest) if isinstance(manifest, list) else set()
        # The transition path is already bound by transition_path and its unique
        # introducing commit, so the two historically used complete encodings
        # (explicit self path or implicit self path) are semantically identical.
        declared_complete = declared_paths | {artifact}
        history_invalid = (
            container_summary.get("parents") != [source]
            or git_record.get("source_tree") != source_summary.get("tree")
            or git_record.get("source_program_tree")
            != program_trees.get((source, program_root))
            or git_record.get("containing_commit") is not None
            or git_record.get("containing_commit_rule") != "transition_blob_container"
            or not isinstance(manifest, list)
            or (
                manifest != sorted(declared_paths)
                and artifact not in corrected_manifest_targets
            )
            or declared_complete != actual_paths
            or git_record.get("transition_path")
            != f"evidence/transitions/{transition_id}.json"
        )
        if history_invalid:
            findings.append(
                _finding(
                    "TRANSITION_MANIFEST_MISMATCH",
                    "fatal",
                    artifact,
                    "EXACT_SOURCE_CONTAINER_AND_CHANGED_PATHS",
                )
            )
        if blobs[(current, artifact)] != blobs[(container, artifact)]:
            findings.append(
                _finding(
                    "TRANSITION_BLOB_CHANGED",
                    "fatal",
                    artifact,
                    "APPEND_ONLY_RAW_BYTES",
                )
            )
        for kind, commit in (("inputs", source), ("outputs", container)):
            for index, item in enumerate(row.get(kind, [])):
                target = (artifact, f"/{kind}/{index}")
                if (
                    kind == "inputs"
                    and target == INPUT_ORIGIN_TARGET
                    and target in corrected_input_targets
                ):
                    # This one immutable historical row is evaluated only by
                    # the exact closed correction proof. It is never a generic
                    # exception for another transition, pointer, or artifact.
                    continue
                try:
                    path = _artifact_repo_path(program_root, item.get("path"))
                    raw = blobs[(commit, path)]
                except (GitSubjectError, KeyError, TypeError):
                    findings.append(
                        _finding(
                            "TRANSITION_ARTIFACT_MISSING",
                            "fatal",
                            artifact,
                            "COMMITTED_INPUT_OUTPUT",
                        )
                    )
                    continue
                actual_digest = sha256_bytes(raw)
                digest_target = (artifact, f"/{kind}/{index}/sha256")
                if (
                    actual_digest != item.get("sha256")
                    and digest_target not in corrected_digest_targets
                ):
                    findings.append(
                        _finding(
                            "TRANSITION_ARTIFACT_DIGEST_MISMATCH",
                            "fatal",
                            artifact,
                            "RAW_BLOB_SHA256",
                            (
                                kind,
                                path,
                                f"expected:{item.get('sha256')}",
                                f"actual:{actual_digest}",
                            ),
                            json_pointer=f"/{kind}/{index}/sha256",
                        )
                    )


def validate_rev58_raw_identity_repair(
    reader: GitReader,
    current: str,
    program_root: str,
    evidence: Mapping[str, Any],
) -> tuple[list[Finding], frozenset[tuple[str, str]]]:
    """Recognize only the user-authorized revision-58 one-byte repair."""

    archive_path = f"{program_root}/evidence/states/program-state-revision-0058.json"
    current_state_path = f"{program_root}/program-state.json"
    transition_path = f"{program_root}/evidence/transitions/TR-0057.json"
    evidence_path = (
        f"{program_root}/evidence/verification/{REV58_REPAIR_EVIDENCE_ID}.json"
    )
    target = (transition_path, "/outputs/0/sha256")
    valid = True
    try:
        source_identity = reader.resolve_identity(REV58_REPAIR_SOURCE, program_root)
        subject = evidence.get("subject", {})
        actor = evidence.get("actor", {})
        artifacts = subject.get("artifact_digests", [])
        expected_artifacts = [
            {"path": archive_path, "sha256": REV58_ARCHIVE_SHA_BEFORE},
            {"path": transition_path, "sha256": REV58_TRANSITION_SHA},
        ]
        valid = valid and all(
            (
                evidence.get("evidence_id") == REV58_REPAIR_EVIDENCE_ID,
                evidence.get("kind") == "author",
                evidence.get("verdict") == "passed",
                actor.get("role") == "coordinator",
                actor.get("independent") is False,
                subject.get("git_commit") == REV58_REPAIR_SOURCE,
                subject.get("git_tree") == REV58_REPAIR_SOURCE_TREE,
                source_identity.source_tree == REV58_REPAIR_SOURCE_TREE,
                source_identity.program_tree == REV58_REPAIR_SOURCE_PROGRAM_TREE,
                artifacts == expected_artifacts,
                reader.is_ancestor(REV58_REPAIR_SOURCE, current),
                current != REV58_REPAIR_SOURCE,
            )
        )
        blobs = reader.read_blob_requests(
            [
                (REV58_REPAIR_SOURCE, archive_path),
                (REV58_REPAIR_SOURCE, transition_path),
                (current, archive_path),
                (current, current_state_path),
                (current, transition_path),
            ]
        )
        object_ids = reader.object_ids(
            [
                (REV58_REPAIR_SOURCE, archive_path),
                (REV58_REPAIR_SOURCE, transition_path),
                (current, archive_path),
                (current, transition_path),
            ]
        )
        before_archive = blobs[(REV58_REPAIR_SOURCE, archive_path)]
        before_transition = blobs[(REV58_REPAIR_SOURCE, transition_path)]
        after_archive = blobs[(current, archive_path)]
        after_current = blobs[(current, current_state_path)]
        after_transition = blobs[(current, transition_path)]
        transition = strict_loads(after_transition)
        before_state = strict_loads(before_archive)
        after_state = strict_loads(after_archive)
        current_state = strict_loads(after_current)
        current_revision = int(current_state.get("revision", -1))
        current_pointer_valid = after_archive == after_current
        if current_revision > 58:
            chain_valid = True
            successor_requests: list[tuple[str, str]] = []
            for revision in range(59, current_revision + 1):
                successor_requests.extend(
                    [
                        (
                            current,
                            f"{program_root}/evidence/states/"
                            f"program-state-revision-{revision:04d}.json",
                        ),
                        (
                            current,
                            f"{program_root}/evidence/transitions/"
                            f"TR-{revision - 1:04d}.json",
                        ),
                    ]
                )
            successor_blobs = reader.read_blob_requests(successor_requests)
            successor_states: dict[int, Mapping[str, Any]] = {58: after_state}
            for revision in range(59, current_revision + 1):
                state_key = (
                    current,
                    f"{program_root}/evidence/states/"
                    f"program-state-revision-{revision:04d}.json",
                )
                transition_key = (
                    current,
                    f"{program_root}/evidence/transitions/TR-{revision - 1:04d}.json",
                )
                successor_state = strict_loads(successor_blobs[state_key])
                successor_transition = strict_loads(successor_blobs[transition_key])
                prior_state = successor_states[revision - 1]
                chain_valid = chain_valid and all(
                    (
                        successor_state.get("schema_version") == "2.0",
                        successor_state.get("program_id") == "EPP-2026",
                        successor_state.get("revision") == revision,
                        successor_transition.get("transition_id")
                        == f"TR-{revision - 1:04d}",
                        successor_transition.get("prior_revision") == revision - 1,
                        successor_transition.get("new_revision") == revision,
                        successor_transition.get("prior_state_digest")
                        == canonical_digest(prior_state),
                        successor_transition.get("new_state_digest")
                        == canonical_digest(successor_state),
                    )
                )
                if not chain_valid:
                    break
                successor_states[revision] = successor_state
            current_archive_key = (
                current,
                f"{program_root}/evidence/states/"
                f"program-state-revision-{current_revision:04d}.json",
            )
            current_pointer_valid = (
                chain_valid and after_current == successor_blobs[current_archive_key]
            )
        valid = valid and all(
            (
                sha256_bytes(before_archive) == REV58_ARCHIVE_SHA_BEFORE,
                object_ids[(REV58_REPAIR_SOURCE, archive_path)]
                == REV58_ARCHIVE_BLOB_BEFORE,
                sha256_bytes(before_transition) == REV58_TRANSITION_SHA,
                object_ids[(REV58_REPAIR_SOURCE, transition_path)]
                == REV58_TRANSITION_BLOB,
                after_transition == before_transition,
                object_ids[(current, transition_path)] == REV58_TRANSITION_BLOB,
                _pointer_value(transition, "/outputs/0/sha256")
                == REV58_ARCHIVE_SHA_BEFORE,
                sha256_bytes(after_archive) == REV58_ARCHIVE_SHA_AFTER,
                object_ids[(current, archive_path)] == REV58_ARCHIVE_BLOB_AFTER,
                current_pointer_valid,
                before_state == after_state,
                canonical_digest(before_state) == canonical_digest(after_state),
                after_state.get("revision") == 58,
                before_archive.endswith(b"\n\n"),
                not after_archive.endswith((b"\n\n", b"\r\n\r\n")),
            )
        )
        checks = evidence.get("checks", [])
        findings = evidence.get("findings", [])
        valid = valid and (
            [row.get("check_id") for row in checks]
            == ["REV58-RAW-IDENTITY", "REV58-REPAIR-BOUNDARY"]
            and [row.get("result") for row in checks] == ["passed", "passed"]
            and [row.get("code") for row in findings] == ["REV58_RAW_IDENTITY_REPAIRED"]
        )
    except (ContractError, GitSubjectError, KeyError, TypeError, ValueError):
        valid = False

    if valid:
        return [], frozenset({target})
    return [
        _finding(
            "REV58_RAW_IDENTITY_REPAIR_INVALID",
            "fatal",
            evidence_path,
            "EXACT_SINGLE_CLAIM_REPAIR",
        )
    ], frozenset()


def validate_f01b_activation_evidence_correction(
    reader: GitReader,
    current: str,
    program_root: str,
    profile: Mapping[str, Any],
) -> tuple[list[Finding], frozenset[tuple[str, str]]]:
    """Recognize only the three authorized TR-0070 Git-normalized digests."""

    correction_path = (
        f"{program_root}/evidence/corrections/{F01B_ACTIVATION_CORRECTION_ID}.json"
    )
    transition_path = f"{program_root}/evidence/transitions/TR-0070.json"
    valid = True
    try:
        current_commit = reader.resolve_commit(current)
        source_identity = reader.resolve_identity(F01B_ACTIVATION_SOURCE, program_root)
        claims = list(profile.get("claims", []))
        valid = valid and all(
            (
                profile.get("$schema")
                == "../../schemas/f01b-activation-correction.schema.json",
                profile.get("schema_version") == "1.0",
                profile.get("correction_id") == F01B_ACTIVATION_CORRECTION_ID,
                profile.get("program_id") == "EPP-2026",
                profile.get("feature_id") == "EPP-F01B",
                profile.get("stable_cause_id")
                == "EPP-F01B-FEATURE-NEUTRAL-ACTIVATION-001",
                profile.get("source_checkpoint")
                == {
                    "git_commit": F01B_ACTIVATION_SOURCE,
                    "git_tree": F01B_ACTIVATION_SOURCE_TREE,
                    "program_tree": F01B_ACTIVATION_SOURCE_PROGRAM_TREE,
                },
                profile.get("accept_new_records") is False,
                profile.get("expected_claim_count") == 3,
                len(claims) == 3,
                source_identity.source_tree == F01B_ACTIVATION_SOURCE_TREE,
                source_identity.program_tree == F01B_ACTIVATION_SOURCE_PROGRAM_TREE,
                reader.is_ancestor(F01B_ACTIVATION_SOURCE, current_commit),
            )
        )

        transition_raw = reader.blob(F01B_ACTIVATION_SOURCE, transition_path)
        transition = strict_loads(transition_raw)
        transition_blob = reader.object_ids(
            [(F01B_ACTIVATION_SOURCE, transition_path)]
        )[(F01B_ACTIVATION_SOURCE, transition_path)]
        valid = valid and all(
            (
                sha256_bytes(transition_raw) == F01B_ACTIVATION_TRANSITION_SHA,
                transition_blob == F01B_ACTIVATION_TRANSITION_BLOB,
                reader.blob(current_commit, transition_path) == transition_raw,
                reader.containing_commit(current_commit, transition_path)
                == F01B_ACTIVATION_SOURCE,
            )
        )

        observed_pointers: set[str] = set()
        for claim, expected in zip(claims, F01B_ACTIVATION_CLAIMS, strict=True):
            claim_id, pointer, artifact_path, git_blob, recorded, authoritative = (
                expected
            )
            observed_pointers.add(str(claim.get("json_pointer", "")))
            artifact_raw = reader.blob(F01B_ACTIVATION_SOURCE, artifact_path)
            artifact_object = reader.object_ids(
                [(F01B_ACTIVATION_SOURCE, artifact_path)]
            )[(F01B_ACTIVATION_SOURCE, artifact_path)]
            valid = valid and all(
                (
                    claim.get("claim_id") == claim_id,
                    claim.get("classification")
                    == "checkout_bytes_recorded_as_committed_digest",
                    claim.get("transition_path") == transition_path,
                    claim.get("transition_raw_sha256")
                    == F01B_ACTIVATION_TRANSITION_SHA,
                    claim.get("transition_git_blob") == F01B_ACTIVATION_TRANSITION_BLOB,
                    claim.get("introducing_commit") == F01B_ACTIVATION_SOURCE,
                    claim.get("introducing_tree") == F01B_ACTIVATION_SOURCE_TREE,
                    claim.get("introducing_program_tree")
                    == F01B_ACTIVATION_SOURCE_PROGRAM_TREE,
                    claim.get("json_pointer") == pointer,
                    claim.get("artifact_path") == artifact_path,
                    claim.get("artifact_git_blob") == git_blob,
                    claim.get("recorded_value") == recorded,
                    claim.get("authoritative_value") == authoritative,
                    _pointer_value(transition, pointer) == recorded,
                    recorded != authoritative,
                    artifact_object == git_blob,
                    sha256_bytes(artifact_raw) == authoritative,
                )
            )
        valid = valid and observed_pointers == {
            row[1] for row in F01B_ACTIVATION_CLAIMS
        }
        valid = valid and profile.get("forbidden_target_classes") == [
            "any TR-0070 path or pointer other than outputs 3 4 and 5 sha256",
            "any transition other than TR-0070",
            "approval authority or frozen EPP-F01B product contract",
            "readiness benchmark dependency candidate delivery publication or release",
            "generic waiver wildcard future record or correction-of-correction target",
        ]
        valid = valid and profile.get("resolution_semantics") == {
            "effect": "three_historical_TR0070_output_digest_findings_only",
            "original_transition_immutable": True,
            "validator_recomputes_git_normalized_blob_bytes": True,
            "all_claims_required": True,
            "no_product_or_policy_broadening": True,
            "readiness_authority_benchmark_release_non_interference": True,
        }
        valid = valid and profile.get("authority") == {
            "authorization_kind": "direct_user_instruction",
            "authorized_at": "2026-08-28",
            "transition": "TR-0071",
            "revision": 72,
        }
    except (ContractError, GitSubjectError, KeyError, TypeError, ValueError):
        valid = False

    if valid:
        return [], F01B_ACTIVATION_DIGEST_TARGETS
    return [
        _finding(
            "F01B_ACTIVATION_CORRECTION_INVALID",
            "fatal",
            correction_path,
            "EXACT_THREE_CLAIM_GIT_NORMALIZED_RECOMPUTATION",
        )
    ], frozenset()


def validate_f01b_lease_checkpoint_correction(
    reader: GitReader,
    current: str,
    program_root: str,
    transition: Mapping[str, Any],
    successor_state: Mapping[str, Any],
) -> tuple[list[Finding], frozenset[str], frozenset[tuple[str, str]]]:
    """Recognize only the revision-75 length and two TR-0074 digest claims."""

    correction_path = f"{program_root}/evidence/transitions/TR-0075.json"
    source_transition_path = f"{program_root}/evidence/transitions/TR-0074.json"
    source_state_path = (
        f"{program_root}/evidence/states/program-state-revision-0075.json"
    )
    task_path = "specs/077-browser-program-status/tasks.md"
    quickstart_path = "specs/077-browser-program-status/quickstart.md"
    valid = True
    try:
        current_commit = reader.resolve_commit(current)
        source_identity = reader.resolve_identity(
            F01B_LEASE_CHECKPOINT_SOURCE, program_root
        )
        source_transition_raw = reader.blob(
            F01B_LEASE_CHECKPOINT_SOURCE, source_transition_path
        )
        source_transition = strict_loads(source_transition_raw)
        source_transition_blob = reader.object_ids(
            [(F01B_LEASE_CHECKPOINT_SOURCE, source_transition_path)]
        )[(F01B_LEASE_CHECKPOINT_SOURCE, source_transition_path)]
        source_state_raw = reader.blob(F01B_LEASE_CHECKPOINT_SOURCE, source_state_path)
        source_state = strict_loads(source_state_raw)
        source_state_blob = reader.object_ids(
            [(F01B_LEASE_CHECKPOINT_SOURCE, source_state_path)]
        )[(F01B_LEASE_CHECKPOINT_SOURCE, source_state_path)]

        expected_state = copy.deepcopy(source_state)
        expected_state["revision"] = 76
        expected_state["active_mutating_lease"]["path_restrictions"][0][
            "restriction"
        ] = F01B_LEASE_CHECKPOINT_RESTRICTION
        expected_state["active_mutating_lease"]["recovery"]["last_audit_transition"] = (
            "TR-0075"
        )
        expected_state["active_mutating_lease"]["recovery"]["rollback_state"] = (
            "evidence/states/program-state-revision-0075.json"
        )
        expected_state["last_transition"] = "TR-0075"

        correction_successor_state = successor_state
        if successor_state.get("revision") != 76:
            successor_archive_path = (
                f"{program_root}/evidence/states/program-state-revision-0076.json"
            )
            correction_successor_state = strict_loads(
                reader.blob(current_commit, successor_archive_path)
            )
            protected_lease_fields = (
                "feature_id",
                "branch",
                "worktree_id",
                "dev_baseline",
                "worktree_start",
                "holder_role",
                "lease_mode",
                "allowed_paths",
                "path_restrictions",
                "allowed_actions",
            )
            current_lease = successor_state.get("active_mutating_lease")
            expected_lease = expected_state["active_mutating_lease"]
            if current_lease is None:
                valid = valid and successor_state.get("feature_state") in {
                    "BLOCKED",
                    "CANDIDATE_FROZEN",
                    "INDEPENDENTLY_VERIFIED",
                    "PUSH_AUTHORIZATION_PENDING",
                    "PR_READY",
                    "DEV_MERGE_READY",
                    "DEV_INTEGRATED",
                    "DEV_DEPLOYMENT_VERIFIED",
                    "ROLLED_BACK",
                    "STOPPED",
                }
            elif isinstance(current_lease, Mapping):
                same_f01b_lease = all(
                    current_lease.get(field) == expected_lease.get(field)
                    for field in protected_lease_fields
                )
                exact_f02_successor = all(
                    (
                        successor_state.get("revision", 0) > 79,
                        successor_state.get("current_feature") == "EPP-F02",
                        successor_state.get("feature_state")
                        in {
                            "IMPLEMENTATION_APPROVAL_PENDING",
                            "IMPLEMENTATION_AUTHORIZED",
                        },
                        current_lease.get("feature_id") == "EPP-F02",
                        current_lease.get("dev_baseline")
                        == {
                            "commit": "e9dd5c38026d0b1b5b165ee803fe082068ecc128",
                            "tree": "d7e2ddf8228263478475019099f424a91c3b96c2",
                        },
                        current_lease.get("worktree_start")
                        == {
                            "commit": "fd93daf6d5826da436f394ab1afb9298f5e8a32b",
                            "tree": "38cbb5c63b1f11303b6c9569de0c3c0e6f9b0b93",
                        },
                    )
                )
                # The old correction remains bound to revision 76. A later
                # native lease is independently governed by its standing scope
                # and the ordinary lease checks; it cannot rewrite that proof.
                native_successor = (
                    successor_state.get("revision", 0) >= 93
                    and successor_state.get("current_feature") == "EPP-N01"
                    and current_lease.get("feature_id") == "EPP-N01"
                    and successor_state.get("approval", {}).get("authority_kind")
                    == "standing_user_scope"
                    and successor_state.get("approval", {}).get("record")
                    == "evidence/authorizations/AUTH-EPP-N01-2026-001.json"
                )
                valid = valid and all(
                    (
                        isinstance(successor_state.get("revision"), int),
                        successor_state.get("revision", 0) > 76,
                        same_f01b_lease or exact_f02_successor or native_successor,
                    )
                )
            else:
                valid = False

        claims = {
            "/inputs/3/sha256": (
                task_path,
                "47467024581fcc42c7ab96a3008cd0939fd516036a7a788df91f8502fc27603b",
                "a4d8abc71839b21a4ff2cb526c491b06843e04c35ba0e6aa7dbeb2920f69d2d7",
                "11edaff8247a8b3ca31c3eac5b2482a88f6807c9",
            ),
            "/inputs/4/sha256": (
                quickstart_path,
                "97cb663b2c6eda98886a9ae57e62743b2c073812f22936208b041d52466528f8",
                "85f4604d4df525c693c34ec94b4181b298375c82b474315ee94fbea84a85aba5",
                "4be35f174b774a86490fdc8cec3c421203bd4934",
            ),
        }
        for pointer, (
            artifact_path,
            recorded,
            authoritative,
            git_blob,
        ) in claims.items():
            artifact_raw = reader.blob(F01B_LEASE_CHECKPOINT_SOURCE, artifact_path)
            artifact_object = reader.object_ids(
                [(F01B_LEASE_CHECKPOINT_SOURCE, artifact_path)]
            )[(F01B_LEASE_CHECKPOINT_SOURCE, artifact_path)]
            valid = valid and all(
                (
                    _pointer_value(source_transition, pointer) == recorded,
                    sha256_bytes(artifact_raw) == authoritative,
                    artifact_object == git_blob,
                    recorded != authoritative,
                )
            )

        expected_changed_paths = {
            "docs/programs/engineering-process-platform/evidence/states/program-state-revision-0076.json",
            "docs/programs/engineering-process-platform/evidence/transitions/TR-0075.json",
            "docs/programs/engineering-process-platform/program-state.json",
            "scripts/program_control/validation.py",
            "tests/program_control_plane/test_transition_chain.py",
        }
        valid = valid and all(
            (
                source_identity.source_tree == F01B_LEASE_CHECKPOINT_SOURCE_TREE,
                source_identity.program_tree
                == F01B_LEASE_CHECKPOINT_SOURCE_PROGRAM_TREE,
                reader.is_ancestor(F01B_LEASE_CHECKPOINT_SOURCE, current_commit),
                sha256_bytes(source_transition_raw)
                == F01B_LEASE_CHECKPOINT_TRANSITION_SHA,
                source_transition_blob == F01B_LEASE_CHECKPOINT_TRANSITION_BLOB,
                reader.blob(current_commit, source_transition_path)
                == source_transition_raw,
                sha256_bytes(source_state_raw) == F01B_LEASE_CHECKPOINT_STATE_SHA,
                source_state_blob == F01B_LEASE_CHECKPOINT_STATE_BLOB,
                reader.blob(current_commit, source_state_path) == source_state_raw,
                len(
                    source_state["active_mutating_lease"]["path_restrictions"][0][
                        "restriction"
                    ]
                )
                > 300,
                len(F01B_LEASE_CHECKPOINT_RESTRICTION) <= 300,
                correction_successor_state == expected_state,
                transition.get("schema_version") == "2.0",
                transition.get("transition_id") == "TR-0075",
                transition.get("program_id") == "EPP-2026",
                transition.get("feature_id") == "EPP-F01B",
                transition.get("state_domain") == "repair",
                transition.get("event_kind") == "repair_checkpoint",
                transition.get("from_state") == "IMPLEMENTATION_AUTHORIZED",
                transition.get("to_state") == "IMPLEMENTATION_AUTHORIZED",
                transition.get("prior_revision") == 75,
                transition.get("new_revision") == 76,
                transition.get("action") == F01B_LEASE_CHECKPOINT_ACTION,
                transition.get("git", {}).get("source_commit")
                == F01B_LEASE_CHECKPOINT_SOURCE,
                transition.get("git", {}).get("source_tree")
                == F01B_LEASE_CHECKPOINT_SOURCE_TREE,
                transition.get("git", {}).get("source_program_tree")
                == F01B_LEASE_CHECKPOINT_SOURCE_PROGRAM_TREE,
                set(transition.get("git", {}).get("changed_paths_manifest", []))
                == expected_changed_paths,
                transition.get("repair")
                == {
                    "stable_cause_id": "EPP-F01B-LEASE-CHECKPOINT-EVIDENCE-001",
                    "attempt": 1,
                    "maximum": 2,
                    "remaining": 1,
                },
                transition.get("next_action") == "START_CURRENT_FEATURE_IMPLEMENTATION",
            )
        )
    except (ContractError, GitSubjectError, KeyError, TypeError, ValueError):
        valid = False

    if valid:
        return (
            [],
            F01B_LEASE_CHECKPOINT_SCHEMA_TARGETS,
            F01B_LEASE_CHECKPOINT_DIGEST_TARGETS,
        )
    return (
        [
            _finding(
                "F01B_LEASE_CHECKPOINT_CORRECTION_INVALID",
                "fatal",
                correction_path,
                "EXACT_REV75_AND_TR0074_THREE_CLAIM_CORRECTION",
            )
        ],
        frozenset(),
        frozenset(),
    )


def _validate_state_chain(
    documents: Mapping[str, Any],
    program_root: str,
    findings: list[Finding],
    *,
    reader: GitReader | None = None,
    source_commit: str | None = None,
    corrected_input_targets: frozenset[tuple[str, str]] = frozenset(),
    corrected_digest_targets: frozenset[tuple[str, str]] = frozenset(),
    corrected_manifest_targets: frozenset[str] = frozenset(),
    corrected_event_targets: frozenset[tuple[str, str, str, str, str]] = frozenset(),
) -> None:
    state_path = f"{program_root}/program-state.json"
    current = documents.get(state_path)
    if not isinstance(current, dict):
        return
    states: dict[int, dict[str, Any]] = {}
    prefix = f"{program_root}/evidence/states/program-state-revision-"
    for path, value in documents.items():
        if path.startswith(prefix) and isinstance(value, dict):
            revision = int(path.removeprefix(prefix).removesuffix(".json"))
            if revision in states and states[revision] != value:
                findings.append(
                    _finding(
                        "STATE_ARCHIVE_MISMATCH", "fatal", path, "UNIQUE_REVISION_BYTES"
                    )
                )
            states[revision] = value
    current_revision = int(current.get("revision", -1))
    if current_revision in states and states[current_revision] != current:
        findings.append(
            _finding(
                "STATE_ARCHIVE_MISMATCH",
                "fatal",
                state_path,
                "CURRENT_ARCHIVE_IDENTITY",
            )
        )
    states[current_revision] = current
    revisions = sorted(states)
    if revisions and revisions != list(range(revisions[0], revisions[-1] + 1)):
        findings.append(
            _finding("STATE_REVISION_GAP", "fatal", state_path, "MONOTONIC_REVISION")
        )
    transitions = [
        value
        for path, value in sorted(documents.items())
        if f"{program_root}/evidence/transitions/TR-" in path
        and isinstance(value, dict)
    ]
    if reader is not None and source_commit is not None:
        _validate_transition_history(
            reader,
            source_commit,
            transitions,
            program_root,
            findings,
            corrected_input_targets,
            corrected_digest_targets,
            corrected_manifest_targets,
        )
    policy_value = documents.get(f"{program_root}/lifecycle-policy.json")
    policy = policy_value if isinstance(policy_value, Mapping) else {}
    program_edges = {
        (str(row.get("from")), str(row.get("to")))
        for row in policy.get("program_edges", [])
        if isinstance(row, Mapping)
    }
    feature_edges = {
        (str(row.get("from")), str(row.get("to")))
        for row in policy.get("feature_edges", [])
        if isinstance(row, Mapping)
    }
    event_rules = {
        (str(row.get("event_kind")), str(row.get("state_domain"))): row
        for row in policy.get("event_rules", [])
        if isinstance(row, Mapping)
    }
    if not corrected_event_targets.issubset(CHECKPOINT_EVENT_TARGETS):
        findings.append(
            _finding(
                "CHECKPOINT_EVIDENCE_CORRECTION_INVALID",
                "fatal",
                f"{program_root}/evidence/corrections",
                "NO_GENERIC_EVENT_RULE_BYPASS",
            )
        )
        corrected_event_targets = frozenset()
    seen_ids: set[str] = set()
    migration_count = 0
    for transition in transitions:
        transition_id = transition.get("transition_id")
        if not isinstance(transition_id, str) or transition_id in seen_ids:
            findings.append(
                _finding(
                    "TRANSITION_ID_INVALID",
                    "fatal",
                    "evidence/transitions",
                    "APPEND_ONLY_ID",
                )
            )
            continue
        seen_ids.add(transition_id)
        prior_revision = transition.get("prior_revision")
        new_revision = transition.get("new_revision")
        if not isinstance(prior_revision, int) or new_revision != prior_revision + 1:
            findings.append(
                _finding(
                    "TRANSITION_REVISION_INVALID",
                    "fatal",
                    transition_id,
                    "REVISION_INCREMENT",
                )
            )
            continue
        prior = states.get(prior_revision)
        new = states.get(new_revision)
        if prior is not None and canonical_digest(prior) != transition.get(
            "prior_state_digest"
        ):
            findings.append(
                _finding(
                    "STATE_DIGEST_MISMATCH",
                    "fatal",
                    transition_id,
                    "PRIOR_STATE_DIGEST",
                )
            )
        if new is not None and canonical_digest(new) != transition.get(
            "new_state_digest"
        ):
            findings.append(
                _finding(
                    "STATE_DIGEST_MISMATCH", "fatal", transition_id, "NEW_STATE_DIGEST"
                )
            )
        if transition.get("schema_version") == "2.0":
            authority = transition.get("authority")
            if (
                isinstance(authority, Mapping)
                and authority.get("authority_kind") == "standing_user_scope"
            ):
                _validate_native_scope_authority(
                    documents, program_root,
                    {"current_feature": transition.get("feature_id"),
                     "revision": new_revision, "approval": authority},
                    findings,
                )
            domain = transition.get("state_domain")
            event = transition.get("event_kind")
            pair = (str(transition.get("from_state")), str(transition.get("to_state")))
            event_target = (
                f"{program_root}/evidence/transitions/{transition_id}.json",
                "repair",
                str(event),
                pair[0],
                pair[1],
            )
            if event_target in corrected_event_targets:
                domain = "repair"
            event_rule = event_rules.get((str(event), str(domain)))
            if event_rule is None or (
                event_rule.get("may_preserve_state") is False and pair[0] == pair[1]
            ):
                findings.append(
                    _finding(
                        "EVENT_RULE_INVALID",
                        "fatal",
                        transition_id,
                        "DECLARED_DOMAIN_EVENT_RULE",
                    )
                )
            if event == "lifecycle_transition":
                allowed = (
                    program_edges
                    if domain == "program"
                    else feature_edges
                    if domain == "feature"
                    else set()
                )
                if pair not in allowed:
                    findings.append(
                        _finding(
                            "LIFECYCLE_EDGE_INVALID",
                            "fatal",
                            transition_id,
                            "POLICY_EDGE",
                        )
                    )
            if isinstance(prior, Mapping) and isinstance(new, Mapping):
                if (
                    prior.get("schema_version") == "1.0"
                    and new.get("schema_version") == "2.0"
                ):
                    migration_count += 1
            git_record = transition.get("git")
            if not isinstance(git_record, Mapping):
                findings.append(
                    _finding(
                        "TRANSITION_MANIFEST_INVALID",
                        "fatal",
                        transition_id,
                        "COMPLETE_CHANGED_PATH_MANIFEST",
                    )
                )
            else:
                manifest = git_record.get("changed_paths_manifest", [])
                if not isinstance(manifest, list) or len(manifest) != len(
                    set(manifest)
                ):
                    findings.append(
                        _finding(
                            "TRANSITION_MANIFEST_INVALID",
                            "fatal",
                            transition_id,
                            "UNIQUE_CHANGED_PATHS",
                        )
                    )
                else:
                    for path in manifest:
                        try:
                            normalize_repo_path(str(path))
                        except GitSubjectError:
                            findings.append(
                                _finding(
                                    "TRANSITION_MANIFEST_INVALID",
                                    "fatal",
                                    transition_id,
                                    "SAFE_CHANGED_PATH",
                                )
                            )
                            break
    if (
        any(state.get("schema_version") == "2.0" for state in states.values())
        and migration_count != 1
    ):
        findings.append(
            _finding(
                "LEGACY_MIGRATION_COUNT",
                "fatal",
                "evidence/transitions",
                "SOLE_V2_SUCCESSOR",
            )
        )
    last = current.get("last_transition")
    if last is not None and last not in seen_ids:
        findings.append(
            _finding(
                "TRANSITION_REFERENCE_MISSING",
                "fatal",
                state_path,
                "LAST_TRANSITION_EXISTS",
            )
        )


def _roadmap_order(items: list[dict[str, Any]], findings: list[Finding]) -> list[str]:
    by_id = {str(item.get("id")): item for item in items}
    if len(by_id) != len(items):
        findings.append(
            _finding("ROADMAP_ID_DUPLICATE", "fatal", "roadmap.json", "UNIQUE_ITEM_ID")
        )
        return []
    indegree = {item_id: 0 for item_id in by_id}
    children: dict[str, list[str]] = defaultdict(list)
    for item_id, item in by_id.items():
        for dependency in item.get("depends_on", []):
            if dependency not in by_id:
                findings.append(
                    _finding(
                        "ROADMAP_DEPENDENCY_MISSING",
                        "fatal",
                        "roadmap.json",
                        "DEPENDENCY_EXISTS",
                    )
                )
                continue
            indegree[item_id] += 1
            children[dependency].append(item_id)
    queue = deque(
        sorted(item_id for item_id, degree in indegree.items() if degree == 0)
    )
    ordered: list[str] = []
    while queue:
        item_id = queue.popleft()
        ordered.append(item_id)
        for child in sorted(children[item_id]):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if len(ordered) != len(items):
        findings.append(
            _finding("ROADMAP_CYCLE", "fatal", "roadmap.json", "ACYCLIC_DEPENDENCIES")
        )
    return ordered


def _parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def evaluate_approval_history(
    approvals: Sequence[Mapping[str, Any]],
    *,
    required_scopes: Sequence[str],
    exact_subject: Mapping[str, Any],
    observed_at: datetime,
) -> tuple[list[Finding], list[Mapping[str, Any]]]:
    """Resolve one current append-only approval per required scope."""

    findings: list[Finding] = []
    selected: list[Mapping[str, Any]] = []
    now = observed_at.astimezone(timezone.utc)
    for scope in required_scopes:
        candidates = [row for row in approvals if row.get("scope") == scope]
        if not candidates:
            findings.append(
                _finding(
                    "APPROVAL_SCOPE_MISSING",
                    "fatal",
                    "evidence/approvals",
                    "REQUIRED_SCOPE",
                )
            )
            continue
        approval = sorted(candidates, key=lambda row: str(row.get("approved_at", "")))[
            -1
        ]
        selected.append(approval)
        artifact = str(approval.get("approval_id", "approval"))
        if approval.get("subject") != exact_subject:
            findings.append(
                _finding(
                    "APPROVAL_SUBJECT_MISMATCH",
                    "fatal",
                    artifact,
                    "EXACT_SHARED_SUBJECT",
                )
            )
        revoked = approval.get("revoked") is True or bool(
            approval.get("revocation_events")
        )
        if revoked:
            findings.append(
                _finding(
                    "APPROVAL_REVOKED", "fatal", artifact, "APPEND_ONLY_REVOCATION"
                )
            )
        expiry = _parse_utc(approval.get("expires_at"))
        if expiry is not None and expiry < now:
            findings.append(
                _finding("APPROVAL_EXPIRED", "fatal", artifact, "APPROVAL_FRESHNESS")
            )
        decision = approval.get("decision")
        conditions = approval.get("conditions")
        if decision not in {"approved", "approved_with_conditions"} or (
            decision == "approved_with_conditions" and not conditions
        ):
            findings.append(
                _finding(
                    "APPROVAL_NOT_CURRENT", "fatal", artifact, "UNCONDITIONAL_APPROVAL"
                )
            )
    return sorted(findings, key=Finding.sort_key), selected


def validate_roadmap_approval_and_lease(
    documents: Mapping[str, Any],
    program_root: str,
    *,
    observed_at: datetime,
    actual_branch: str,
    worktree_id: str,
    reader: GitReader | None = None,
    source_commit: str | None = None,
) -> tuple[list[Finding], str | None]:
    """Validate roadmap selection, structured dates, pointer, WIP, and lease identity."""

    findings: list[Finding] = []
    roadmap = documents.get(f"{program_root}/roadmap.json")
    state = documents.get(f"{program_root}/program-state.json")
    policy = documents.get(f"{program_root}/lifecycle-policy.json")
    if not isinstance(roadmap, Mapping) or not isinstance(state, Mapping):
        findings.append(
            _finding(
                "CONTROL_PLANE_INVALID",
                "fatal",
                "program-state.json",
                "ROADMAP_AND_STATE",
            )
        )
        return findings, None
    items = [
        dict(item) for item in roadmap.get("items", []) if isinstance(item, Mapping)
    ]
    _roadmap_order(items, findings)
    by_id = {str(item.get("id")): item for item in items}
    active = [item for item in items if item.get("status") == "active"]
    feature_state = state.get("feature_state")
    current_feature = state.get("current_feature")
    current_item = by_id.get(str(current_feature))
    blocked_control = feature_state == "BLOCKED"
    if (blocked_control and active) or (not blocked_control and len(active) != 1):
        findings.append(
            _finding(
                "WIP_LIMIT_EXCEEDED", "fatal", "roadmap.json", "ONE_ACTIVE_FEATURE"
            )
        )
    if (
        current_item is None
        or (blocked_control and current_item.get("status") != "blocked")
        or (
            not blocked_control
            and (len(active) != 1 or active[0].get("id") != current_feature)
        )
    ):
        findings.append(
            _finding(
                "LEASE_IDENTITY_MISMATCH",
                "fatal",
                "program-state.json",
                "ACTIVE_FEATURE_POINTER",
            )
        )
    if current_item is not None and any(
        by_id.get(str(dependency), {}).get("status") != "complete"
        for dependency in current_item.get("depends_on", [])
    ):
        findings.append(
            _finding(
                "ROADMAP_DEPENDENCY_INCOMPLETE",
                "fatal",
                "roadmap.json",
                "ACTIVE_DEPENDENCIES_COMPLETE",
            )
        )
    decision_doc = documents.get(f"{program_root}/decision-register.json")
    decision_rows = (
        decision_doc.get("records", []) if isinstance(decision_doc, Mapping) else []
    )
    decision_by_id = {
        str(row.get("id")): row for row in decision_rows if isinstance(row, Mapping)
    }
    risk_doc = documents.get(f"{program_root}/risk-register.json")
    risk_ids = {
        str(row.get("id"))
        for row in (risk_doc.get("risks", []) if isinstance(risk_doc, Mapping) else [])
        if isinstance(row, Mapping)
    }
    gate_doc = documents.get(f"{program_root}/gate-catalog.json")
    gate_ids = {
        str(row.get("id"))
        for row in (gate_doc.get("gates", []) if isinstance(gate_doc, Mapping) else [])
        if isinstance(row, Mapping)
    }
    for item in items:
        for decision_id in item.get("blocking_decisions", []):
            if decision_id not in decision_by_id:
                findings.append(
                    _finding(
                        "ROADMAP_DECISION_REFERENCE_INVALID",
                        "fatal",
                        "roadmap.json",
                        "BLOCKING_DECISION_EXISTS",
                    )
                )
        if gate_ids and any(
            gate_id not in gate_ids for gate_id in item.get("gate_impacts", [])
        ):
            findings.append(
                _finding(
                    "ROADMAP_GATE_REFERENCE_INVALID",
                    "fatal",
                    "roadmap.json",
                    "GATE_IMPACT_EXISTS",
                )
            )
    if current_item is not None and any(
        decision_by_id.get(str(decision_id), {}).get("status")
        not in {"decided", "superseded"}
        for decision_id in current_item.get("blocking_decisions", [])
    ):
        findings.append(
            _finding(
                "ROADMAP_BLOCKING_DECISION_OPEN",
                "fatal",
                "roadmap.json",
                "ACTIVE_ITEM_DECISIONS_RESOLVED",
            )
        )
    if not active and current_feature is None:
        eligible = [
            item
            for item in items
            if item.get("status") == "proposed"
            and all(
                by_id.get(str(dependency), {}).get("status") == "complete"
                for dependency in item.get("depends_on", [])
            )
            and all(
                decision_by_id.get(str(decision_id), {}).get("status")
                in {"decided", "superseded"}
                for decision_id in item.get("blocking_decisions", [])
            )
        ]
        if eligible:
            best = min(int(item.get("priority", 2**31)) for item in eligible)
            if sum(int(item.get("priority", 2**31)) == best for item in eligible) != 1:
                findings.append(
                    _finding(
                        "ROADMAP_ELIGIBILITY_AMBIGUOUS",
                        "fatal",
                        "roadmap.json",
                        "DEPENDENCY_PRIORITY_TIE_BREAK",
                    )
                )
    for area in state.get("readiness", {}).values():
        if not isinstance(area, Mapping):
            continue
        for blocker in area.get("blockers", []):
            match = re.match(r"^(DEC-P0-[0-9]{3}|RISK-[0-9]{3})(?::|$)", str(blocker))
            if (
                match
                and match.group(1) not in decision_by_id
                and match.group(1) not in risk_ids
            ):
                findings.append(
                    _finding(
                        "CONTROL_REFERENCE_INVALID",
                        "fatal",
                        "program-state.json",
                        "DECISION_OR_RISK_EXISTS",
                    )
                )
    lease = state.get("active_mutating_lease")
    lease_closed = feature_state in {
        "BLOCKED",
        "CANDIDATE_FROZEN",
        "INDEPENDENTLY_VERIFIED",
        "PUSH_AUTHORIZATION_PENDING",
        "PR_READY",
        "DEV_MERGE_READY",
        "DEV_INTEGRATED",
        "DEV_DEPLOYMENT_VERIFIED",
        "ROLLED_BACK",
        "STOPPED",
    }
    if lease_closed and lease is not None:
        findings.append(
            _finding(
                "LEASE_IDENTITY_MISMATCH",
                "fatal",
                "program-state.json",
                "NON_MUTATING_STATE_HAS_NO_LEASE",
            )
        )
    elif not lease_closed and (
        not isinstance(lease, Mapping) or lease.get("feature_id") != current_feature
    ):
        findings.append(
            _finding(
                "LEASE_IDENTITY_MISMATCH",
                "fatal",
                "program-state.json",
                "LEASE_FEATURE_MATCH",
            )
        )
    elif isinstance(lease, Mapping):
        expiry = _parse_utc(lease.get("expires_at"))
        acquired = _parse_utc(lease.get("acquired_at"))
        if (
            expiry is None
            or acquired is None
            or expiry <= acquired
            or expiry < observed_at.astimezone(timezone.utc)
        ):
            findings.append(
                _finding(
                    "LEASE_EXPIRED", "fatal", "program-state.json", "LEASE_TIME_WINDOW"
                )
            )
        if lease.get("branch") != actual_branch:
            findings.append(
                _finding(
                    "LEASE_BRANCH_MISMATCH",
                    "fatal",
                    "program-state.json",
                    "ACTUAL_BRANCH",
                )
            )
        if lease.get("worktree_id") != worktree_id:
            findings.append(
                _finding(
                    "LEASE_WORKTREE_MISMATCH",
                    "fatal",
                    "program-state.json",
                    "ACTUAL_WORKTREE",
                )
            )
        if reader is not None and source_commit is not None:
            try:
                start = lease.get("worktree_start", {}).get("commit")
                start_tree = lease.get("worktree_start", {}).get("tree")
                baseline = lease.get("dev_baseline", {})
                baseline_commit = baseline.get("commit")
                if not isinstance(start, str) or not isinstance(baseline_commit, str):
                    raise GitSubjectError("lease Git identity is missing")
                summaries = reader.commit_summaries([start, baseline_commit])
                actual_start_tree = str(summaries[start].get("tree"))
                actual_baseline_tree = str(summaries[baseline_commit].get("tree"))
                ancestor = reader.is_ancestor(start, source_commit)
                if (
                    actual_start_tree != start_tree
                    or not ancestor
                    or actual_baseline_tree != baseline.get("tree")
                ):
                    raise GitSubjectError("lease Git identity is invalid")
            except (AttributeError, GitSubjectError):
                findings.append(
                    _finding(
                        "LEASE_GIT_IDENTITY_MISMATCH",
                        "fatal",
                        "program-state.json",
                        "WORKTREE_START_AND_BASELINE",
                        (
                            f"worktree_start:{start if isinstance(start, str) else 'invalid'}",
                            f"expected_start_tree:{start_tree if isinstance(start_tree, str) else 'invalid'}",
                            f"actual_start_tree:{locals().get('actual_start_tree', 'unresolved')}",
                            f"baseline:{baseline_commit if isinstance(baseline_commit, str) else 'invalid'}",
                            f"expected_baseline_tree:{baseline.get('tree') if isinstance(baseline, Mapping) else 'invalid'}",
                            f"actual_baseline_tree:{locals().get('actual_baseline_tree', 'unresolved')}",
                        ),
                    )
                )
        for path in lease.get("allowed_paths", []):
            try:
                normalize_repo_path(str(path))
            except GitSubjectError:
                findings.append(
                    _finding(
                        "LEASE_PATH_UNSAFE",
                        "fatal",
                        "program-state.json",
                        "NORMALIZED_ALLOWED_PATH",
                    )
                )
                break
        local_actions = {
            "inspect",
            "edit_allowlisted_paths",
            "run_deterministic_checks",
            "create_local_artifacts",
            "create_local_commits",
        }
        if not set(lease.get("allowed_actions", [])).issubset(local_actions):
            findings.append(
                _finding(
                    "LEASE_ACTION_UNAUTHORIZED",
                    "fatal",
                    "program-state.json",
                    "LOCAL_ACTION_VOCABULARY",
                )
            )
    decisions = documents.get(f"{program_root}/decision-register.json")
    if isinstance(decisions, Mapping):
        for row in decisions.get("records", []):
            if not isinstance(row, Mapping) or row.get("status") in {
                "decided",
                "superseded",
                "rejected",
            }:
                continue
            due = row.get("due")
            due_at = _parse_utc(due.get("due_at")) if isinstance(due, Mapping) else None
            if due_at is not None and due_at < observed_at.astimezone(timezone.utc):
                findings.append(
                    _finding(
                        "DECISION_OVERDUE",
                        "fatal",
                        str(row.get("id")),
                        "STRUCTURED_DUE_DATE",
                    )
                )
    risks = documents.get(f"{program_root}/risk-register.json")
    if isinstance(risks, Mapping):
        for row in risks.get("risks", []):
            if not isinstance(row, Mapping) or row.get("status") == "closed":
                continue
            review = row.get("review")
            due_at = (
                _parse_utc(review.get("due_at"))
                if isinstance(review, Mapping)
                else None
            )
            if due_at is not None and due_at < observed_at.astimezone(timezone.utc):
                findings.append(
                    _finding(
                        "RISK_REVIEW_OVERDUE",
                        "fatal",
                        str(row.get("id")),
                        "STRUCTURED_REVIEW_DATE",
                    )
                )
    actions = state.get("next_eligible_actions", [])
    action = (
        str(actions[0].get("action"))
        if len(actions) == 1 and isinstance(actions[0], Mapping)
        else None
    )
    if action is None:
        findings.append(
            _finding(
                "NEXT_ACTION_AMBIGUOUS",
                "fatal",
                "program-state.json",
                "SOLE_NEXT_ACTION",
            )
        )
    if isinstance(policy, Mapping) and action is not None:
        matching = [
            row
            for row in policy.get("action_rules", [])
            if isinstance(row, Mapping)
            and row.get("program_state") == state.get("state")
            and row.get("feature_state") == state.get("feature_state")
            and row.get("action") == action
        ]
        declared_human = (
            actions[0].get("requires_human_approval")
            if len(actions) == 1 and isinstance(actions[0], Mapping)
            else None
        )
        if (
            len(matching) != 1
            or matching[0].get("requires_human_approval") != declared_human
        ):
            findings.append(
                _finding(
                    "ACTION_POLICY_MISMATCH",
                    "fatal",
                    "program-state.json",
                    "POLICY_DERIVED_ACTION",
                )
            )
    findings = [
        replace(finding, artifact=f"{program_root}/{finding.artifact}")
        if finding.artifact in {"program-state.json", "roadmap.json"}
        else finding
        for finding in findings
    ]
    return sorted(findings, key=Finding.sort_key), action


def _validate_roadmap_and_lease(
    documents: Mapping[str, Any],
    program_root: str,
    findings: list[Finding],
) -> tuple[str | None, list[str], list[str]]:
    roadmap = documents.get(f"{program_root}/roadmap.json")
    state = documents.get(f"{program_root}/program-state.json")
    if not isinstance(roadmap, dict) or not isinstance(state, dict):
        return None, [], ["CONTROL_PLANE_INVALID"]
    items = [item for item in roadmap.get("items", []) if isinstance(item, dict)]
    _roadmap_order(items, findings)
    active = [item for item in items if item.get("status") == "active"]
    if len(active) > 1:
        findings.append(
            _finding(
                "WIP_LIMIT_EXCEEDED", "fatal", "roadmap.json", "ONE_ACTIVE_FEATURE"
            )
        )
    current_feature = state.get("current_feature")
    if active and active[0].get("id") != current_feature:
        findings.append(
            _finding(
                "LEASE_IDENTITY_MISMATCH",
                "fatal",
                "program-state.json",
                "ACTIVE_FEATURE_MATCH",
            )
        )
    lease = state.get("active_mutating_lease")
    lease_closed = state.get("feature_state") in {
        "BLOCKED",
        "CANDIDATE_FROZEN",
        "INDEPENDENTLY_VERIFIED",
        "PUSH_AUTHORIZATION_PENDING",
        "PR_READY",
        "DEV_MERGE_READY",
        "DEV_INTEGRATED",
        "DEV_DEPLOYMENT_VERIFIED",
        "ROLLED_BACK",
        "STOPPED",
    }
    if (
        current_feature
        and not lease_closed
        and (not isinstance(lease, dict) or lease.get("feature_id") != current_feature)
    ):
        findings.append(
            _finding(
                "LEASE_IDENTITY_MISMATCH",
                "fatal",
                "program-state.json",
                "LEASE_FEATURE_MATCH",
            )
        )
    next_actions = state.get("next_eligible_actions", [])
    if len(next_actions) != 1:
        findings.append(
            _finding(
                "NEXT_ACTION_AMBIGUOUS",
                "fatal",
                "program-state.json",
                "SOLE_NEXT_ACTION",
            )
        )
        return (
            str(current_feature) if current_feature else None,
            [],
            ["NEXT_ACTION_AMBIGUOUS"],
        )
    action = next_actions[0]
    return (
        str(current_feature) if current_feature else None,
        [str(action.get("action"))],
        [],
    )


def _verify_approval_artifacts(
    reader: GitReader,
    _source_commit: str,
    approval: Mapping[str, Any],
    program_root: str,
) -> bool:
    subject = approval.get("subject")
    if not isinstance(subject, dict):
        return False
    approved_commit = subject.get("git_commit")
    if not isinstance(approved_commit, str):
        return False
    resolved: list[tuple[Mapping[str, Any], str]] = []
    for artifact in subject.get("artifact_digests", []):
        if not isinstance(artifact, dict):
            return False
        try:
            path = normalize_repo_path(
                posixpath.normpath(posixpath.join(program_root, str(artifact["path"])))
            )
        except (GitSubjectError, KeyError):
            return False
        resolved.append((artifact, path))
    try:
        blobs = reader.read_blobs(approved_commit, [path for _, path in resolved])
    except GitSubjectError:
        return False
    for artifact, path in resolved:
        raw = blobs[path]
        if sha256_bytes(raw) != artifact.get("sha256"):
            return False
    return True


def _validate_current_authority(
    reader: GitReader,
    documents: Mapping[str, Any],
    program_root: str,
    observed_at: datetime,
    findings: list[Finding],
) -> None:
    """Resolve the state's exact two-record implementation authority bundle."""

    state = documents.get(f"{program_root}/program-state.json")
    if not isinstance(state, Mapping):
        return
    approval_state = state.get("approval")
    if (
        isinstance(approval_state, Mapping)
        and approval_state.get("authority_kind") == "standing_user_scope"
    ):
        _validate_native_scope_authority(documents, program_root, state, findings)
        return
    required = (
        approval_state.get("required_records", [])
        if isinstance(approval_state, Mapping)
        else []
    )
    if len(required) != 2 or len(set(required)) != 2:
        findings.append(
            _finding(
                "APPROVAL_BUNDLE_INVALID",
                "fatal",
                "program-state.json",
                "EXACT_TWO_SCOPE_BUNDLE",
            )
        )
        return
    if (
        isinstance(approval_state, Mapping)
        and approval_state.get("status") == "pending"
    ):
        if approval_state.get("record") is not None:
            findings.append(
                _finding(
                    "APPROVAL_BUNDLE_INVALID",
                    "fatal",
                    "program-state.json",
                    "PENDING_APPROVAL_HAS_NO_RECORD",
                )
            )
        return
    approvals: list[Mapping[str, Any]] = []
    for relative in required:
        try:
            path = f"{program_root}/{normalize_repo_path(str(relative))}"
        except GitSubjectError:
            path = ""
        value = documents.get(path)
        if not isinstance(value, Mapping):
            findings.append(
                _finding(
                    "APPROVAL_RECORD_MISSING",
                    "fatal",
                    "program-state.json",
                    "REQUIRED_APPROVAL_RECORD",
                )
            )
        else:
            approvals.append(value)
    if len(approvals) != 2:
        return
    subject = approvals[0].get("subject")
    if not isinstance(subject, Mapping):
        findings.append(
            _finding(
                "APPROVAL_SUBJECT_MISMATCH",
                "fatal",
                "evidence/approvals",
                "EXACT_SHARED_SUBJECT",
            )
        )
        return
    history_findings, selected = evaluate_approval_history(
        approvals,
        required_scopes=("material_change", "feature_implementation"),
        exact_subject=subject,
        observed_at=observed_at,
    )
    findings.extend(history_findings)
    if (
        len(selected) != 2
        or len({row.get("bundle_id") for row in selected}) != 1
        or any(
            row.get("feature_id") != state.get("current_feature") for row in selected
        )
    ):
        findings.append(
            _finding(
                "APPROVAL_BUNDLE_INVALID",
                "fatal",
                "evidence/approvals",
                "SAME_FEATURE_AND_BUNDLE",
            )
        )
    try:
        approved = reader.resolve_identity(str(subject.get("git_commit")), program_root)
        if approved.source_tree != subject.get(
            "git_tree"
        ) or approved.program_tree != subject.get("program_tree"):
            raise GitSubjectError("approval subject tree mismatch")
    except GitSubjectError:
        findings.append(
            _finding(
                "APPROVAL_SUBJECT_MISMATCH",
                "fatal",
                "evidence/approvals",
                "COMMIT_TREE_PROGRAM_TREE",
            )
        )
    for approval in selected:
        if not _verify_approval_artifacts(reader, "", approval, program_root):
            findings.append(
                _finding(
                    "APPROVAL_STALE",
                    "fatal",
                    str(approval.get("approval_id", "approval")),
                    "ARTIFACT_DIGESTS",
                )
            )


def _validate_native_scope_authority(
    documents: Mapping[str, Any],
    program_root: str,
    state: Mapping[str, Any],
    findings: list[Finding],
) -> None:
    """Recognize the recorded native scope without inventing exact approval."""

    approval = state.get("approval", {})
    path = f"{program_root}/evidence/authorizations/AUTH-EPP-N01-2026-001.json"
    record = documents.get(path)
    schema = documents.get(f"{program_root}/schemas/scope-authorization.schema.json")
    valid = (
        isinstance(approval, Mapping)
        and isinstance(record, Mapping)
        and isinstance(schema, Mapping)
        and not validate_schema(schema, record)
        and state.get("current_feature") == "EPP-N01"
        and isinstance(state.get("revision"), int)
        and state["revision"] >= 93
        and approval.get("status") == "authorized_scope"
        and approval.get("record")
        == "evidence/authorizations/AUTH-EPP-N01-2026-001.json"
        and approval.get("exact_subject_approval") is False
    )
    if valid:
        assert isinstance(record, Mapping)
        valid = (
            record.get("revoked") is False
            and record.get("exact_subject_approval") is False
            and record.get("human_review_evidence") is False
            and approval.get("record_digest") == canonical_digest(record)
            and isinstance(record.get("instruction"), str)
            and sha256_bytes(record["instruction"].encode("utf-8"))
            == record.get("instruction_sha256")
        )
    if not valid:
        findings.append(
            _finding(
                "NATIVE_SCOPE_AUTHORITY_INVALID", "fatal", path,
                "RECORDED_NATIVE_SCOPE_NOT_EXACT_APPROVAL",
            )
        )


def _release_approval(
    reader: GitReader,
    commit: str,
    documents: Mapping[str, Any],
    program_root: str,
    candidate: Mapping[str, Any] | None,
    findings: list[Finding],
    observed_at: datetime,
) -> dict[str, Any]:
    approvals = [
        value
        for path, value in documents.items()
        if f"{program_root}/evidence/approvals/" in path and isinstance(value, dict)
    ]
    current_by_boundary: dict[tuple[str | None, str], dict[str, Any]] = {}
    for approval in approvals:
        feature_id = approval.get("feature_id")
        approval_id = str(approval.get("approval_id", ""))
        if feature_id is None and approval_id.startswith("APR-EPP-F01-"):
            feature_id = "EPP-F01"
        key = (
            str(feature_id) if feature_id is not None else None,
            str(approval.get("scope")),
        )
        existing = current_by_boundary.get(key)
        if existing is None or str(approval.get("approved_at", "")) > str(
            existing.get("approved_at", "")
        ):
            current_by_boundary[key] = approval
    for approval in current_by_boundary.values():
        if approval.get("decision") == "approved" and not _verify_approval_artifacts(
            reader, commit, approval, program_root
        ):
            findings.append(
                _finding(
                    "APPROVAL_STALE", "fatal", "evidence/approvals", "ARTIFACT_DIGESTS"
                )
            )
    release = [approval for approval in approvals if approval.get("scope") == "release"]
    if not release:
        return {"status": "absent", "approval_id": None, "subject_matches": False}
    approval = sorted(release, key=lambda row: str(row.get("approved_at", "")))[-1]
    subject = approval.get("subject", {})
    subject_artifacts = sorted(
        (
            str(row.get("path")),
            str(row.get("sha256")),
        )
        for row in subject.get("artifact_digests", [])
        if isinstance(row, Mapping)
    )
    candidate_artifacts = sorted(
        (
            str(row.get("path")),
            str(row.get("sha256")),
        )
        for row in (candidate or {}).get("artifact_digests", [])
        if isinstance(row, Mapping)
    )
    matches = bool(
        candidate
        and subject.get("git_commit") == candidate.get("git_commit")
        and subject.get("git_tree") == candidate.get("git_tree")
        and subject_artifacts == candidate_artifacts
    )
    revoked = approval.get("revoked") is True or bool(approval.get("revocation_events"))
    expires_at = approval.get("expires_at")
    expired = bool(
        expires_at
        and datetime.fromisoformat(str(expires_at).replace("Z", "+00:00")) < observed_at
    )
    if revoked:
        status = "revoked"
    elif expired:
        status = "stale"
    elif not matches:
        status = "stale"
    else:
        status = str(approval.get("decision", "pending"))
    return {
        "status": status,
        "approval_id": approval.get("approval_id"),
        "subject_matches": matches,
    }


def _empty_areas() -> dict[str, dict[str, Any]]:
    counts = {
        "product_readiness": 11,
        "benchmark_readiness": 8,
        "commercial_readiness": 8,
        "program_health": 7,
    }
    return {
        area: {
            "status": "not_started",
            "passed_gates": 0,
            "required_gates": count,
            "gates": [],
            "blockers": ["GATE_CATALOG_UNAVAILABLE"],
            "evidence": [],
            "fresh": False,
            "last_success_at": None,
        }
        for area, count in counts.items()
    }


def _resolve_container_and_delivery(
    reader: GitReader,
    source_commit: str,
    program_root: str,
    *,
    container: str | None,
    delivery: str | None,
    findings: list[Finding],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Resolve only explicit C/D or the one constrained HEAD-as-C case."""

    dashboard_path = f"{program_root}/dashboard.json"
    delivery_path = (
        f"{program_root}/evidence/verification/EPP-F01-dashboard-delivery.json"
    )
    container_resolution = "absent"
    container_commit: str | None = None
    if container is not None:
        container_resolution = "explicit"
        try:
            container_commit = reader.resolve_commit(container)
        except GitSubjectError:
            container_resolution = "unresolved"
    else:
        try:
            head = reader.current_head()
            if head != source_commit:
                if reader.first_parent(head) == source_commit and reader.diff_paths(
                    source_commit, head
                ) == [dashboard_path]:
                    container_resolution = "inferred_head"
                    container_commit = head
                else:
                    container_resolution = "unresolved"
        except GitSubjectError:
            container_resolution = "unresolved"
    if container_resolution in {"explicit", "inferred_head"}:
        try:
            assert container_commit is not None
            if reader.first_parent(
                container_commit
            ) != source_commit or reader.diff_paths(
                source_commit, container_commit
            ) != [dashboard_path]:
                raise GitSubjectError("container relation is invalid")
            reader.blob(container_commit, dashboard_path)
        except (AssertionError, GitSubjectError):
            container_resolution = "unresolved"
            container_commit = None
    if container_resolution == "unresolved":
        findings.append(
            _finding(
                "DASHBOARD_CONTAINER_MISMATCH",
                "fatal",
                dashboard_path,
                "EXPLICIT_OR_CONSTRAINED_HEAD_CONTAINER",
            )
        )

    delivery_resolution = "absent"
    delivery_commit: str | None = None
    evidence_record: dict[str, str] | None = None
    delivery_valid = False
    if delivery is not None:
        if container_commit is None:
            delivery_resolution = "unresolved"
            findings.append(
                _finding(
                    "DASHBOARD_DELIVERY_UNRESOLVED",
                    "fatal",
                    delivery_path,
                    "DELIVERY_REQUIRES_RESOLVED_CONTAINER",
                )
            )
        else:
            delivery_resolution = "explicit"
            try:
                delivery_commit = reader.resolve_commit(delivery)
                if reader.first_parent(
                    delivery_commit
                ) != container_commit or reader.diff_paths(
                    container_commit, delivery_commit
                ) != [delivery_path]:
                    raise GitSubjectError("delivery relation is invalid")
                raw = reader.blob(delivery_commit, delivery_path)
                value = strict_loads(raw)
                schema = strict_loads(
                    reader.blob(
                        source_commit,
                        f"{program_root}/schemas/verification-evidence.schema.json",
                    )
                )
                relation = (
                    value.get("delivery_relation")
                    if isinstance(value, Mapping)
                    else None
                )
                dashboard_raw = reader.blob(container_commit, dashboard_path)
                if (
                    not isinstance(value, Mapping)
                    or not isinstance(schema, Mapping)
                    or validate_schema(schema, value)
                    or value.get("kind") != "delivery"
                    or value.get("verdict") != "passed"
                    or value.get("actor", {}).get("role") != "independent_verifier"
                    or value.get("actor", {}).get("independent") is not True
                    or not isinstance(relation, Mapping)
                    or relation.get("source_commit") != source_commit
                    or relation.get("container_commit") != container_commit
                    or relation.get("dashboard", {}).get("sha256")
                    != sha256_bytes(dashboard_raw)
                ):
                    raise ContractError("delivery evidence is invalid")
                evidence_record = {
                    "path": delivery_path,
                    "sha256": sha256_bytes(raw),
                    "git_blob": reader.blob_id(delivery_commit, delivery_path),
                }
                delivery_valid = True
            except (ContractError, GitSubjectError):
                delivery_resolution = "unresolved"
                delivery_commit = None
                findings.append(
                    _finding(
                        "DASHBOARD_DELIVERY_RELATION_INVALID",
                        "fatal",
                        delivery_path,
                        "EXPLICIT_INDEPENDENT_DELIVERY_RELATION",
                    )
                )

    status = (
        "committed_valid"
        if delivery_valid
        else "failed"
        if container_resolution == "unresolved" or delivery_resolution == "unresolved"
        else "candidate_not_evidence"
        if container_commit is not None
        else "not_requested"
    )
    subject_fields = {
        "container_resolution": container_resolution,
        "container_commit": container_commit,
        "delivery_resolution": delivery_resolution,
        "delivery_commit": delivery_commit,
    }
    envelope = {
        "mode": "validate",
        "status": status,
        "target_changed": False,
        "prior_snapshot_preserved": True,
        **subject_fields,
        "evidence_record": evidence_record,
    }
    return subject_fields, envelope


def validate_program(
    reader: GitReader,
    source: str = "HEAD",
    program_root: str = "docs/programs/engineering-process-platform",
    *,
    container: str | None = None,
    delivery: str | None = None,
    observed_at: datetime | None = None,
) -> ValidationResult:
    """Validate a committed subject without mutating the repository."""

    now = observed_at or datetime.now(timezone.utc)
    timestamp = now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    root = normalize_repo_path(program_root)
    findings: list[Finding] = []
    try:
        identity = reader.resolve_identity(source, root)
        policy = strict_loads(
            reader.blob(identity.source_commit, f"{root}/lifecycle-policy.json")
        )
        if not isinstance(policy, Mapping):
            raise ContractError("lifecycle policy must be an object")
        manifest, manifest_digest = _enrich_input_manifest(
            reader, identity.source_commit, root, (), policy
        )
    except GitSubjectError:
        findings.append(
            _finding("SUBJECT_UNRESOLVED", "fatal", "git-subject", "EXACT_COMMIT_TREE")
        )
        report = _unresolved_report(timestamp, findings)
        return ValidationResult(report=report, findings=findings, exit_code=2)
    except ContractError:
        findings.append(
            _finding(
                "JSON_INVALID",
                "fatal",
                f"{root}/lifecycle-policy.json",
                "INPUT_MANIFEST_POLICY",
            )
        )
        report = _unresolved_report(timestamp, findings)
        return ValidationResult(report=report, findings=findings, exit_code=3)
    bundle_manifest, bundle_digest, bundle_findings = _validate_runtime_source_bundle(
        reader, identity.source_commit
    )
    findings.extend(bundle_findings)
    subject_delivery, delivery_envelope = _resolve_container_and_delivery(
        reader,
        identity.source_commit,
        root,
        container=container,
        delivery=delivery,
        findings=findings,
    )
    documents = _validate_documents(
        reader, identity.source_commit, root, manifest, findings
    )
    _prefetch_closed_correction_blobs(reader, identity.source_commit, root, documents)
    input_correction_path = (
        f"{root}/evidence/corrections/{INPUT_ORIGIN_CORRECTION_ID}.json"
    )
    input_correction = documents.get(input_correction_path)
    tr0027 = documents.get(INPUT_ORIGIN_TARGET[0])
    corrected_input_targets: frozenset[tuple[str, str]] = frozenset()
    if isinstance(input_correction, Mapping) or isinstance(tr0027, Mapping):
        input_approval_documents = {
            f"{root}/{relative}": value
            for relative in INPUT_ORIGIN_CORRECTION_APPROVAL_PATHS
            if isinstance((value := documents.get(f"{root}/{relative}")), Mapping)
        }
        input_correction_findings, corrected_input_targets = (
            validate_transition_input_origin_correction(
                reader,
                identity.source_commit,
                root,
                input_correction if isinstance(input_correction, Mapping) else {},
                input_approval_documents,
            )
        )
        findings.extend(input_correction_findings)
    repair_correction_path = f"{root}/evidence/corrections/{REPAIR_CORRECTION_ID}.json"
    repair_correction = documents.get(repair_correction_path)
    corrected_schema_targets: frozenset[str] = frozenset()
    corrected_digest_targets: frozenset[tuple[str, str]] = frozenset()
    corrected_event_targets: frozenset[tuple[str, str, str, str, str]] = frozenset()
    if isinstance(repair_correction, Mapping):
        repair_approval_documents = {
            f"{root}/{relative}": value
            for relative in REPAIR_CORRECTION_APPROVAL_PATHS
            if isinstance((value := documents.get(f"{root}/{relative}")), Mapping)
        }
        (
            repair_findings,
            corrected_schema_targets,
            corrected_digest_targets,
        ) = validate_repair_evidence_correction(
            reader,
            identity.source_commit,
            root,
            repair_correction,
            repair_approval_documents,
        )
        findings = [
            finding
            for finding in findings
            if not (
                finding.code == "SCHEMA_VALIDATION_FAILED"
                and finding.artifact in corrected_schema_targets
            )
        ]
        findings.extend(repair_findings)
    checkpoint_correction_path = (
        f"{root}/evidence/corrections/{CHECKPOINT_CORRECTION_ID}.json"
    )
    checkpoint_correction = documents.get(checkpoint_correction_path)
    if isinstance(checkpoint_correction, Mapping):
        checkpoint_approval_documents = {
            f"{root}/{relative}": value
            for relative in CHECKPOINT_APPROVAL_PATHS
            if isinstance((value := documents.get(f"{root}/{relative}")), Mapping)
        }
        (
            checkpoint_findings,
            checkpoint_digest_targets,
            corrected_event_targets,
        ) = validate_checkpoint_evidence_correction(
            reader,
            identity.source_commit,
            root,
            checkpoint_correction,
            checkpoint_approval_documents,
        )
        corrected_digest_targets = frozenset(
            {*corrected_digest_targets, *checkpoint_digest_targets}
        )
        findings.extend(checkpoint_findings)
    preflight_correction_path = (
        f"{root}/evidence/corrections/{PREFLIGHT_CORRECTION_ID}.json"
    )
    preflight_correction = documents.get(preflight_correction_path)
    corrected_manifest_targets: frozenset[str] = frozenset()
    if isinstance(preflight_correction, Mapping):
        preflight_approval_documents = {
            f"{root}/{relative}": value
            for relative in PREFLIGHT_APPROVAL_PATHS
            if isinstance((value := documents.get(f"{root}/{relative}")), Mapping)
        }
        (
            preflight_findings,
            preflight_schema_targets,
            corrected_manifest_targets,
        ) = validate_preflight_evidence_correction(
            reader,
            identity.source_commit,
            root,
            preflight_correction,
            preflight_approval_documents,
        )
        findings = [
            finding
            for finding in findings
            if not (
                finding.code == "SCHEMA_REFERENCE_MISSING"
                and finding.artifact in preflight_schema_targets
            )
        ]
        findings.extend(preflight_findings)
    rev58_repair_path = f"{root}/evidence/verification/{REV58_REPAIR_EVIDENCE_ID}.json"
    rev58_repair = documents.get(rev58_repair_path)
    if isinstance(rev58_repair, Mapping):
        rev58_findings, rev58_digest_targets = validate_rev58_raw_identity_repair(
            reader,
            identity.source_commit,
            root,
            rev58_repair,
        )
        corrected_digest_targets = frozenset(
            {*corrected_digest_targets, *rev58_digest_targets}
        )
        findings.extend(rev58_findings)
    f01b_activation_correction_path = (
        f"{root}/evidence/corrections/{F01B_ACTIVATION_CORRECTION_ID}.json"
    )
    f01b_activation_correction = documents.get(f01b_activation_correction_path)
    if isinstance(f01b_activation_correction, Mapping):
        activation_findings, activation_digest_targets = (
            validate_f01b_activation_evidence_correction(
                reader,
                identity.source_commit,
                root,
                f01b_activation_correction,
            )
        )
        corrected_digest_targets = frozenset(
            {*corrected_digest_targets, *activation_digest_targets}
        )
        findings.extend(activation_findings)
    lease_checkpoint_transition = documents.get(
        f"{root}/evidence/transitions/TR-0075.json"
    )
    successor_state = documents.get(f"{root}/program-state.json")
    if isinstance(lease_checkpoint_transition, Mapping) and isinstance(
        successor_state, Mapping
    ):
        (
            lease_checkpoint_findings,
            lease_checkpoint_schema_targets,
            lease_checkpoint_digest_targets,
        ) = validate_f01b_lease_checkpoint_correction(
            reader,
            identity.source_commit,
            root,
            lease_checkpoint_transition,
            successor_state,
        )
        corrected_schema_targets = frozenset(
            {*corrected_schema_targets, *lease_checkpoint_schema_targets}
        )
        corrected_digest_targets = frozenset(
            {*corrected_digest_targets, *lease_checkpoint_digest_targets}
        )
        findings = [
            finding
            for finding in findings
            if not (
                finding.code == "SCHEMA_VALIDATION_FAILED"
                and finding.artifact in lease_checkpoint_schema_targets
            )
        ]
        findings.extend(lease_checkpoint_findings)
    _validate_state_chain(
        documents,
        root,
        findings,
        reader=reader,
        source_commit=identity.source_commit,
        corrected_input_targets=corrected_input_targets,
        corrected_digest_targets=corrected_digest_targets,
        corrected_manifest_targets=corrected_manifest_targets,
        corrected_event_targets=corrected_event_targets,
    )
    correction_path = f"{root}/evidence/corrections/{CORRECTION_ID}.json"
    correction = documents.get(correction_path)
    if isinstance(correction, Mapping):
        approval_documents = {
            f"{root}/{relative}": value
            for relative in CORRECTION_APPROVAL_PATHS
            if isinstance((value := documents.get(f"{root}/{relative}")), Mapping)
        }
        correction_findings, corrected_transition_targets = (
            validate_committed_identity_correction(
                reader,
                identity.source_commit,
                root,
                correction,
                approval_documents,
            )
        )
        findings = [
            finding
            for finding in findings
            if not (
                finding.code == "TRANSITION_ARTIFACT_DIGEST_MISMATCH"
                and (finding.artifact, finding.json_pointer)
                in corrected_transition_targets
            )
        ]
        findings.extend(correction_findings)
    try:
        actual_branch = reader.current_branch()
    except GitSubjectError:
        actual_branch = ""
        findings.append(
            _finding(
                "CHECKOUT_BRANCH_UNRESOLVED",
                "fatal",
                "git-subject",
                "ATTACHED_FEATURE_BRANCH",
            )
        )
    roadmap_findings, action = validate_roadmap_approval_and_lease(
        documents,
        root,
        observed_at=now,
        actual_branch=actual_branch,
        worktree_id=reader.repo_root.name,
        reader=reader,
        source_commit=identity.source_commit,
    )
    findings.extend(roadmap_findings)
    state_value = documents.get(f"{root}/program-state.json")
    roadmap_item = (
        str(state_value.get("current_feature"))
        if isinstance(state_value, Mapping) and state_value.get("current_feature")
        else None
    )
    actions = [action] if action is not None else []
    eligibility_blockers = [item.code for item in roadmap_findings]
    _validate_current_authority(reader, documents, root, now, findings)
    catalog = documents.get(f"{root}/gate-catalog.json")
    evidence = documents.get(f"{root}/gate-evidence.json")
    candidate = evidence.get("subject") if isinstance(evidence, dict) else None
    manifest_by_path = {str(row.get("path")): row for row in manifest}
    enriched_candidate = None
    if isinstance(candidate, Mapping):
        enriched_candidate = {
            "kind": candidate.get("kind"),
            "git_commit": candidate.get("git_commit"),
            "git_tree": candidate.get("git_tree"),
            "artifact_digests": [
                {
                    "path": artifact.get("path"),
                    "sha256": artifact.get("sha256"),
                    "git_blob": manifest_by_path.get(
                        normalize_repo_path(
                            posixpath.normpath(
                                posixpath.join(root, str(artifact.get("path")))
                            )
                        ),
                        {},
                    ).get("git_blob", "0" * 40),
                }
                for artifact in candidate.get("artifact_digests", [])
                if isinstance(artifact, Mapping)
            ],
        }
    if isinstance(catalog, dict) and isinstance(evidence, dict):
        try:
            catalog_path = f"{root}/gate-catalog.json"
            areas = derive_areas(
                catalog,
                evidence,
                now,
                source_manifest=manifest,
                candidate=candidate,
                catalog_digest=manifest_by_path.get(catalog_path, {}).get("sha256"),
                source_documents=documents,
            )
        except DashboardError as exc:
            findings.append(
                _finding(exc.code, "fatal", "gate-catalog.json", "GATE_PROJECTION")
            )
            areas = _empty_areas()
    else:
        areas = _empty_areas()
        findings.append(
            _finding(
                "GATE_CATALOG_MISSING",
                "fatal",
                "gate-catalog.json",
                "MACHINE_GATE_SOURCE",
            )
        )
    approval = _release_approval(
        reader, identity.source_commit, documents, root, candidate, findings, now
    )
    benchmark_cases = [
        value
        for value in documents.values()
        if isinstance(value, Mapping)
        and str(value.get("$schema", "")).endswith("benchmark-case.schema.json")
    ]
    benchmark_evidence = [
        value
        for value in documents.values()
        if isinstance(value, Mapping)
        and str(value.get("$schema", "")).endswith("benchmark-evidence.schema.json")
    ]
    benchmark = derive_benchmark_summary(benchmark_cases, benchmark_evidence, now)
    fatal_or_error = [
        item
        for item in findings
        if item.severity in {"fatal", "error"} and item.resolution_status != "resolved"
    ]
    verdict = "failed" if fatal_or_error else "passed"
    next_action = None
    if verdict == "passed" and len(actions) == 1:
        state = documents.get(f"{root}/program-state.json", {})
        action_row = state.get("next_eligible_actions", [{}])[0]
        next_action = {
            "action": actions[0],
            "requires_human_approval": bool(action_row.get("requires_human_approval")),
            "reason": "The committed control plane proves one eligible action.",
        }
    release_eligible = bool(
        all(areas[area]["status"] == "passed" for area in areas)
        and approval["status"] == "approved"
        and approval["subject_matches"]
    )
    checkout = reader.worktree_observation()
    report = {
        "$schema": "./schemas/validation-report.schema.json",
        "schema_version": "1.0",
        "program_id": "EPP-2026",
        "validator": {
            "version": __version__,
            "bundle_manifest_digest": bundle_digest,
            "bundle_manifest": bundle_manifest,
        },
        "observed_at": timestamp,
        "subject": {
            "resolution_status": "resolved",
            "source_commit": identity.source_commit,
            "source_tree": identity.source_tree,
            "program_tree": identity.program_tree,
            **subject_delivery,
            "release_candidate": enriched_candidate,
            "worktree_clean": checkout["dirty_path_count"] == 0,
            "checkout_representation": checkout,
            "input_manifest_digest": manifest_digest,
            "input_manifest": manifest,
        },
        "verdict": verdict,
        "checks": [
            {"id": "SUBJECT_IDENTITY", "result": "passed"},
            {
                "id": "JSON_AND_SCHEMAS",
                "result": "failed" if fatal_or_error else "passed",
            },
            {
                "id": "PROGRAM_SEMANTICS",
                "result": "failed" if fatal_or_error else "passed",
            },
        ],
        "findings": [item.as_dict() for item in sorted(findings, key=Finding.sort_key)],
        "eligibility": {
            "roadmap_item": roadmap_item,
            "allowed_actions": actions if verdict == "passed" else [],
            "blockers": sorted(
                set(eligibility_blockers + [item.code for item in fatal_or_error])
            ),
        },
        "areas": areas,
        "benchmark_summary": benchmark,
        "release_approval": approval,
        "release_eligible": release_eligible,
        "delivery": delivery_envelope,
        "next_action": next_action,
    }
    if verdict == "passed":
        exit_code = 0
    elif any(
        item.code.startswith("SCHEMA_") and "UNSUPPORTED" in item.code
        for item in findings
    ):
        exit_code = 6
    elif any(
        item.code.startswith(("JSON_", "SCHEMA_"))
        or item.code in {"ARTIFACT_MISSING", "JSON_TOP_LEVEL_INVALID"}
        for item in findings
    ):
        exit_code = 3
    else:
        exit_code = 4
    data_cutoff = (
        str(evidence.get("data_cutoff"))
        if isinstance(evidence, Mapping) and evidence.get("data_cutoff")
        else timestamp
    )
    return ValidationResult(
        report=report,
        findings=findings,
        exit_code=exit_code,
        dashboard_data_cutoff=data_cutoff,
    )


def _unresolved_report(timestamp: str, findings: list[Finding]) -> dict[str, Any]:
    return {
        "$schema": "./schemas/validation-report.schema.json",
        "schema_version": "1.0",
        "program_id": "EPP-2026",
        "validator": {
            "version": __version__,
            "bundle_manifest_digest": "0" * 64,
            "bundle_manifest": [],
        },
        "observed_at": timestamp,
        "subject": {
            "resolution_status": "unresolved",
            "source_commit": None,
            "source_tree": None,
            "program_tree": None,
            "container_resolution": "unresolved",
            "container_commit": None,
            "delivery_resolution": "unresolved",
            "delivery_commit": None,
            "release_candidate": None,
            "worktree_clean": False,
            "checkout_representation": {
                "platform": "unknown",
                "autocrlf": "unknown",
                "dirty_path_count": 0,
            },
            "input_manifest_digest": None,
            "input_manifest": [],
        },
        "verdict": "failed",
        "checks": [{"id": "SUBJECT_IDENTITY", "result": "failed"}],
        "findings": [item.as_dict() for item in findings],
        "eligibility": {
            "roadmap_item": None,
            "allowed_actions": [],
            "blockers": ["SUBJECT_UNRESOLVED"],
        },
        "areas": _empty_areas(),
        "benchmark_summary": default_benchmark_summary(),
        "release_approval": {
            "status": "absent",
            "approval_id": None,
            "subject_matches": False,
        },
        "release_eligible": False,
        "delivery": {
            "mode": "validate",
            "status": "failed",
            "target_changed": False,
            "prior_snapshot_preserved": True,
            "container_resolution": "unresolved",
            "container_commit": None,
            "delivery_resolution": "unresolved",
            "delivery_commit": None,
            "evidence_record": None,
        },
        "next_action": None,
    }
