"""Semantic validation of committed program-control evidence."""

from __future__ import annotations

import posixpath
import re
import sys
from collections import defaultdict, deque
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timezone
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any

from . import __version__
from .dashboard import DashboardError, default_benchmark_summary, derive_areas
from .git_subject import HEX40, GitReader, GitSubjectError, normalize_repo_path
from .json_contracts import (
    ContractError,
    UnsupportedVersionError,
    canonical_digest,
    check_schema,
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


def _finding(
    code: str,
    severity: str,
    artifact: str,
    invariant: str,
    evidence: tuple[str, ...] = (),
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
    }.get(code, "Repair the smallest named invariant and rerun the validator.")
    return Finding(
        code=code if SAFE_CODE.fullmatch(code) else "INTERNAL_VALIDATION_FAILURE",
        severity=severity,
        artifact=artifact,
        invariant=invariant,
        evidence=evidence,
        consequence=consequences[severity],
        recovery=recovery,
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

    role_rows = [
        row for row in policy.get("path_roles", []) if isinstance(row, Mapping)
    ]
    excluded = {
        f"{program_root}/dashboard.json",
        f"{program_root}/evidence/verification/EPP-F01-dashboard-delivery.json",
    }
    tree_rows = reader.tree_entries(commit, "")
    selected: list[tuple[dict[str, str], Mapping[str, Any]]] = []
    for tree_row in tree_rows:
        path = tree_row["path"]
        role = next(
            (
                row
                for row in role_rows
                if fnmatchcase(path, str(row.get("pattern", "")))
            ),
            None,
        )
        if (
            role is None
            or path in excluded
            or role.get("role") == "generated_projection"
        ):
            continue
        if tree_row["type"] != "blob" or tree_row["mode"] not in {"100644", "100755"}:
            raise GitSubjectError("authoritative input is not a regular blob")
        selected.append((tree_row, role))
    by_path = {row["path"]: row for row, _ in selected}
    role_by_path = {row["path"]: role for row, role in selected}
    blobs = reader.read_blobs(commit, by_path)
    parsed: dict[str, Any] = {}
    for path, raw in blobs.items():
        if path.endswith(".json"):
            try:
                parsed[path] = strict_loads(raw)
            except ContractError:
                parsed[path] = None
    enriched: list[dict[str, Any]] = []
    for path in sorted(by_path):
        role = str(role_by_path[path].get("role"))
        value = parsed.get(path)
        schema_id: str | None = None
        schema_version: str | None = None
        if isinstance(value, Mapping):
            version = value.get("schema_version")
            schema_version = str(version) if isinstance(version, str) else None
            if "/schemas/" in path and isinstance(value.get("$id"), str):
                schema_id = str(value["$id"])
            elif isinstance(value.get("$schema"), str):
                schema_ref = str(value["$schema"])
                resolved = _schema_path(path, schema_ref, program_root)
                schema_value = parsed.get(resolved or "")
                schema_id = (
                    str(schema_value.get("$id"))
                    if isinstance(schema_value, Mapping)
                    and isinstance(schema_value.get("$id"), str)
                    else schema_ref
                )
        source = by_path[path]
        enriched.append(
            {
                "path": path,
                "role": role,
                "sha256": sha256_bytes(blobs[path]),
                "git_blob": source["git_blob"],
                "schema_id": schema_id,
                "schema_version": schema_version,
            }
        )
    return enriched, canonical_digest(enriched)


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
        dirty = reader.status_for_paths(
            [
                "scripts/validate-engineering-process-program.py",
                "scripts/program_control",
            ]
        )
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
            relative = row.get("path")
            try:
                path = normalize_repo_path(str(relative))
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
) -> None:
    """Bind every v2 transition to immutable raw bytes and its complete Git edge."""

    current = reader.resolve_commit(source_commit)
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
            for artifact in row.get("inputs", []):
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
        actual_paths = set(container_summary.get("paths", []))
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
            or manifest != sorted(declared_paths)
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
            for item in row.get(kind, []):
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
                if sha256_bytes(raw) != item.get("sha256"):
                    findings.append(
                        _finding(
                            "TRANSITION_ARTIFACT_DIGEST_MISMATCH",
                            "fatal",
                            artifact,
                            "RAW_BLOB_SHA256",
                        )
                    )


def _validate_state_chain(
    documents: Mapping[str, Any],
    program_root: str,
    findings: list[Finding],
    *,
    reader: GitReader | None = None,
    source_commit: str | None = None,
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
            reader, source_commit, transitions, program_root, findings
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
            domain = transition.get("state_domain")
            event = transition.get("event_kind")
            pair = (str(transition.get("from_state")), str(transition.get("to_state")))
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
    if len(active) != 1:
        findings.append(
            _finding(
                "WIP_LIMIT_EXCEEDED", "fatal", "roadmap.json", "ONE_ACTIVE_FEATURE"
            )
        )
    current_feature = state.get("current_feature")
    if len(active) != 1 or active[0].get("id") != current_feature:
        findings.append(
            _finding(
                "LEASE_IDENTITY_MISMATCH",
                "fatal",
                "program-state.json",
                "ACTIVE_FEATURE_POINTER",
            )
        )
    if len(active) == 1 and any(
        by_id.get(str(dependency), {}).get("status") != "complete"
        for dependency in active[0].get("depends_on", [])
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
    if len(active) == 1 and any(
        decision_by_id.get(str(decision_id), {}).get("status")
        not in {"decided", "superseded"}
        for decision_id in active[0].get("blocking_decisions", [])
    ):
        findings.append(
            _finding(
                "ROADMAP_BLOCKING_DECISION_OPEN",
                "fatal",
                "roadmap.json",
                "ACTIVE_ITEM_DECISIONS_RESOLVED",
            )
        )
    if not active:
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
    if not isinstance(lease, Mapping) or lease.get("feature_id") != current_feature:
        findings.append(
            _finding(
                "LEASE_IDENTITY_MISMATCH",
                "fatal",
                "program-state.json",
                "LEASE_FEATURE_MATCH",
            )
        )
    else:
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
                if (
                    summaries[start].get("tree") != start_tree
                    or not reader.is_ancestor(start, source_commit)
                    or summaries[baseline_commit].get("tree") != baseline.get("tree")
                ):
                    raise GitSubjectError("lease Git identity is invalid")
            except (AttributeError, GitSubjectError):
                findings.append(
                    _finding(
                        "LEASE_GIT_IDENTITY_MISMATCH",
                        "fatal",
                        "program-state.json",
                        "WORKTREE_START_AND_BASELINE",
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
    if current_feature and (
        not isinstance(lease, dict) or lease.get("feature_id") != current_feature
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


def _release_approval(
    reader: GitReader,
    commit: str,
    documents: Mapping[str, Any],
    program_root: str,
    candidate: Mapping[str, Any] | None,
    findings: list[Finding],
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
    matches = bool(
        candidate
        and subject.get("git_commit") == candidate.get("git_commit")
        and subject.get("git_tree") == candidate.get("git_tree")
    )
    if approval.get("revoked"):
        status = "revoked"
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
    _validate_state_chain(
        documents,
        root,
        findings,
        reader=reader,
        source_commit=identity.source_commit,
    )
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
    if isinstance(catalog, dict) and isinstance(evidence, dict):
        try:
            areas = derive_areas(catalog, evidence, now)
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
        reader, identity.source_commit, documents, root, candidate, findings
    )
    dashboard_seed = documents.get(f"{root}/dashboard.json")
    benchmark = default_benchmark_summary(
        dashboard_seed.get("benchmark_summary")
        if isinstance(dashboard_seed, dict)
        else None
    )
    fatal_or_error = [item for item in findings if item.severity in {"fatal", "error"}]
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
            "release_candidate": candidate,
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
    return ValidationResult(report=report, findings=findings, exit_code=exit_code)


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
