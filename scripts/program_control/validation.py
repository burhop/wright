"""Semantic validation of committed program-control evidence."""

from __future__ import annotations

import posixpath
import re
from collections import defaultdict, deque
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from . import __version__
from .dashboard import DashboardError, default_benchmark_summary, derive_areas
from .git_subject import GitReader, GitSubjectError, normalize_repo_path
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
    return normalize_repo_path(posixpath.normpath(posixpath.join(posixpath.dirname(document_path), schema_ref)))


def _load_json(
    reader: GitReader,
    commit: str,
    path: str,
    findings: list[Finding],
) -> Any | None:
    try:
        return strict_loads(reader.blob(commit, path))
    except ContractError as exc:
        code = "JSON_DUPLICATE_KEY" if exc.__class__.__name__ == "DuplicateKeyError" else "JSON_INVALID"
        findings.append(_finding(code, "fatal", path, "JSON_STRICT_PARSE"))
    except GitSubjectError:
        findings.append(_finding("ARTIFACT_MISSING", "fatal", path, "REQUIRED_ARTIFACT"))
    return None


def _validate_documents(
    reader: GitReader,
    commit: str,
    program_root: str,
    manifest: list[dict[str, str]],
    findings: list[Finding],
) -> dict[str, Any]:
    documents: dict[str, Any] = {}
    paths = [item["path"] for item in manifest if item["path"].endswith(".json")]
    for path in paths:
        value = _load_json(reader, commit, path, findings)
        if value is not None:
            documents[path] = value
    for relative in REQUIRED_JSON:
        path = f"{program_root}/{relative}"
        if path not in documents:
            findings.append(_finding("ARTIFACT_MISSING", "fatal", path, "CONTROL_PLANE_REQUIRED_SET"))
    for path, value in sorted(documents.items()):
        if "/schemas/" in path:
            if isinstance(value, dict):
                try:
                    check_schema(value)
                except ContractError:
                    findings.append(_finding("SCHEMA_META_INVALID", "fatal", path, "DRAFT_2020_12_META"))
            continue
        if not isinstance(value, dict):
            findings.append(_finding("JSON_TOP_LEVEL_INVALID", "fatal", path, "OBJECT_REQUIRED"))
            continue
        version = value.get("schema_version")
        if version is not None:
            try:
                require_compatible_version(version)
            except UnsupportedVersionError as exc:
                findings.append(_finding(exc.kind, "fatal", path, "EXPLICIT_COMPATIBILITY"))
                continue
        schema_ref = value.get("$schema")
        if not isinstance(schema_ref, str):
            findings.append(_finding("SCHEMA_REFERENCE_MISSING", "fatal", path, "SCHEMA_REFERENCE"))
            continue
        resolved = _schema_path(path, schema_ref, program_root)
        schema = documents.get(resolved or "")
        if not isinstance(schema, dict):
            findings.append(_finding("SCHEMA_REFERENCE_MISSING", "fatal", path, "SCHEMA_REFERENCE"))
            continue
        schema_version = schema.get("properties", {}).get("schema_version", {}).get("const")
        if version == "1.0" and schema_version == "2.0" and (
            "/evidence/states/" in path or "/evidence/transitions/" in path
        ):
            continue
        if validate_schema(schema, value):
            findings.append(_finding("SCHEMA_VALIDATION_FAILED", "fatal", path, "SCHEMA_INSTANCE"))
    return documents


def _validate_state_chain(
    documents: Mapping[str, Any],
    program_root: str,
    findings: list[Finding],
) -> None:
    state_path = f"{program_root}/program-state.json"
    current = documents.get(state_path)
    if not isinstance(current, dict):
        return
    states: dict[int, dict[str, Any]] = {}
    prefix = f"{program_root}/evidence/states/program-state-revision-"
    for path, value in documents.items():
        if path.startswith(prefix) and isinstance(value, dict):
            states[int(path.removeprefix(prefix).removesuffix(".json"))] = value
    states[int(current.get("revision", -1))] = current
    revisions = sorted(states)
    if revisions and revisions != list(range(revisions[0], revisions[-1] + 1)):
        findings.append(_finding("STATE_REVISION_GAP", "fatal", state_path, "MONOTONIC_REVISION"))
    transitions = [
        value
        for path, value in sorted(documents.items())
        if f"{program_root}/evidence/transitions/TR-" in path and isinstance(value, dict)
    ]
    seen_ids: set[str] = set()
    for transition in transitions:
        transition_id = transition.get("transition_id")
        if not isinstance(transition_id, str) or transition_id in seen_ids:
            findings.append(_finding("TRANSITION_ID_INVALID", "fatal", "evidence/transitions", "APPEND_ONLY_ID"))
            continue
        seen_ids.add(transition_id)
        prior_revision = transition.get("prior_revision")
        new_revision = transition.get("new_revision")
        if not isinstance(prior_revision, int) or new_revision != prior_revision + 1:
            findings.append(_finding("TRANSITION_REVISION_INVALID", "fatal", transition_id, "REVISION_INCREMENT"))
            continue
        prior = states.get(prior_revision)
        new = states.get(new_revision)
        if prior is not None and canonical_digest(prior) != transition.get("prior_state_digest"):
            findings.append(_finding("STATE_DIGEST_MISMATCH", "fatal", transition_id, "PRIOR_STATE_DIGEST"))
        if new is not None and canonical_digest(new) != transition.get("new_state_digest"):
            findings.append(_finding("STATE_DIGEST_MISMATCH", "fatal", transition_id, "NEW_STATE_DIGEST"))
    last = current.get("last_transition")
    if last is not None and last not in seen_ids:
        findings.append(_finding("TRANSITION_REFERENCE_MISSING", "fatal", state_path, "LAST_TRANSITION_EXISTS"))


def _roadmap_order(items: list[dict[str, Any]], findings: list[Finding]) -> list[str]:
    by_id = {str(item.get("id")): item for item in items}
    if len(by_id) != len(items):
        findings.append(_finding("ROADMAP_ID_DUPLICATE", "fatal", "roadmap.json", "UNIQUE_ITEM_ID"))
        return []
    indegree = {item_id: 0 for item_id in by_id}
    children: dict[str, list[str]] = defaultdict(list)
    for item_id, item in by_id.items():
        for dependency in item.get("depends_on", []):
            if dependency not in by_id:
                findings.append(_finding("ROADMAP_DEPENDENCY_MISSING", "fatal", "roadmap.json", "DEPENDENCY_EXISTS"))
                continue
            indegree[item_id] += 1
            children[dependency].append(item_id)
    queue = deque(sorted(item_id for item_id, degree in indegree.items() if degree == 0))
    ordered: list[str] = []
    while queue:
        item_id = queue.popleft()
        ordered.append(item_id)
        for child in sorted(children[item_id]):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if len(ordered) != len(items):
        findings.append(_finding("ROADMAP_CYCLE", "fatal", "roadmap.json", "ACYCLIC_DEPENDENCIES"))
    return ordered


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
        findings.append(_finding("WIP_LIMIT_EXCEEDED", "fatal", "roadmap.json", "ONE_ACTIVE_FEATURE"))
    current_feature = state.get("current_feature")
    if active and active[0].get("id") != current_feature:
        findings.append(_finding("LEASE_IDENTITY_MISMATCH", "fatal", "program-state.json", "ACTIVE_FEATURE_MATCH"))
    lease = state.get("active_mutating_lease")
    if current_feature and (not isinstance(lease, dict) or lease.get("feature_id") != current_feature):
        findings.append(_finding("LEASE_IDENTITY_MISMATCH", "fatal", "program-state.json", "LEASE_FEATURE_MATCH"))
    next_actions = state.get("next_eligible_actions", [])
    if len(next_actions) != 1:
        findings.append(_finding("NEXT_ACTION_AMBIGUOUS", "fatal", "program-state.json", "SOLE_NEXT_ACTION"))
        return str(current_feature) if current_feature else None, [], ["NEXT_ACTION_AMBIGUOUS"]
    action = next_actions[0]
    return (
        str(current_feature) if current_feature else None,
        [str(action.get("action"))],
        [],
    )


def _verify_approval_artifacts(
    reader: GitReader,
    source_commit: str,
    approval: Mapping[str, Any],
    program_root: str,
) -> bool:
    subject = approval.get("subject")
    if not isinstance(subject, dict):
        return False
    approved_commit = subject.get("git_commit")
    if not isinstance(approved_commit, str):
        return False
    for artifact in subject.get("artifact_digests", []):
        if not isinstance(artifact, dict):
            return False
        try:
            path = normalize_repo_path(posixpath.normpath(posixpath.join(program_root, str(artifact["path"]))))
            try:
                raw = reader.blob(approved_commit, path)
            except GitSubjectError:
                raw = reader.blob(source_commit, path)
        except (GitSubjectError, KeyError):
            return False
        if sha256_bytes(raw) != artifact.get("sha256"):
            return False
    return True


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
    for approval in approvals:
        if approval.get("decision") == "approved" and not _verify_approval_artifacts(
            reader, commit, approval, program_root
        ):
            findings.append(_finding("APPROVAL_STALE", "fatal", "evidence/approvals", "ARTIFACT_DIGESTS"))
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
    return {"status": status, "approval_id": approval.get("approval_id"), "subject_matches": matches}


def _empty_areas() -> dict[str, dict[str, Any]]:
    counts = {"product_readiness": 11, "benchmark_readiness": 8, "commercial_readiness": 8, "program_health": 7}
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


def validate_program(
    reader: GitReader,
    source: str = "HEAD",
    program_root: str = "docs/programs/engineering-process-platform",
    *,
    observed_at: datetime | None = None,
) -> ValidationResult:
    """Validate a committed subject without mutating the repository."""

    now = observed_at or datetime.now(timezone.utc)
    timestamp = now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    root = normalize_repo_path(program_root)
    findings: list[Finding] = []
    try:
        identity = reader.resolve_identity(source, root)
        manifest, manifest_digest = reader.manifest(identity.source_commit, root)
    except GitSubjectError:
        findings.append(_finding("SUBJECT_UNRESOLVED", "fatal", "git-subject", "EXACT_COMMIT_TREE"))
        report = _unresolved_report(timestamp, findings)
        return ValidationResult(report=report, findings=findings, exit_code=2)
    documents = _validate_documents(reader, identity.source_commit, root, manifest, findings)
    _validate_state_chain(documents, root, findings)
    roadmap_item, actions, eligibility_blockers = _validate_roadmap_and_lease(documents, root, findings)
    catalog = documents.get(f"{root}/gate-catalog.json")
    evidence = documents.get(f"{root}/gate-evidence.json")
    candidate = evidence.get("subject") if isinstance(evidence, dict) else None
    if isinstance(catalog, dict) and isinstance(evidence, dict):
        try:
            areas = derive_areas(catalog, evidence, now)
        except DashboardError as exc:
            findings.append(_finding(exc.code, "fatal", "gate-catalog.json", "GATE_PROJECTION"))
            areas = _empty_areas()
    else:
        areas = _empty_areas()
        findings.append(_finding("GATE_CATALOG_MISSING", "fatal", "gate-catalog.json", "MACHINE_GATE_SOURCE"))
    approval = _release_approval(reader, identity.source_commit, documents, root, candidate, findings)
    dashboard_seed = documents.get(f"{root}/dashboard.json")
    benchmark = default_benchmark_summary(
        dashboard_seed.get("benchmark_summary") if isinstance(dashboard_seed, dict) else None
    )
    generator_path = "scripts/validate-engineering-process-program.py"
    try:
        generator_digest = sha256_bytes(reader.blob(identity.source_commit, generator_path))
    except GitSubjectError:
        generator_digest = "0" * 64
        findings.append(_finding("GENERATOR_BLOB_MISSING", "fatal", generator_path, "GENERATOR_IDENTITY"))
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
    report = {
        "$schema": "./schemas/validation-report.schema.json",
        "schema_version": "1.0",
        "program_id": "EPP-2026",
        "validator": {"version": __version__, "blob_sha256": generator_digest},
        "observed_at": timestamp,
        "subject": {
            "resolution_status": "resolved",
            "source_commit": identity.source_commit,
            "source_tree": identity.source_tree,
            "program_tree": identity.program_tree,
            "container_commit": None,
            "release_candidate": candidate,
            "worktree_clean": reader.worktree_observation()["dirty_path_count"] == 0,
            "checkout_representation": reader.worktree_observation(),
            "input_manifest_digest": manifest_digest,
            "input_manifest": manifest,
        },
        "verdict": verdict,
        "checks": [
            {"id": "SUBJECT_IDENTITY", "result": "passed"},
            {"id": "JSON_AND_SCHEMAS", "result": "failed" if fatal_or_error else "passed"},
            {"id": "PROGRAM_SEMANTICS", "result": "failed" if fatal_or_error else "passed"},
        ],
        "findings": [item.as_dict() for item in sorted(findings, key=Finding.sort_key)],
        "eligibility": {
            "roadmap_item": roadmap_item,
            "allowed_actions": actions if verdict == "passed" else [],
            "blockers": sorted(set(eligibility_blockers + [item.code for item in fatal_or_error])),
        },
        "areas": areas,
        "benchmark_summary": benchmark,
        "release_approval": approval,
        "release_eligible": release_eligible,
        "delivery": {
            "mode": "validate",
            "status": "not_requested",
            "target_changed": False,
            "prior_snapshot_preserved": True,
        },
        "next_action": next_action,
    }
    exit_code = 0 if verdict == "passed" else (6 if any(item.code.startswith("SCHEMA_") and "UNSUPPORTED" in item.code for item in findings) else 3)
    return ValidationResult(report=report, findings=findings, exit_code=exit_code)


def _unresolved_report(timestamp: str, findings: list[Finding]) -> dict[str, Any]:
    return {
        "$schema": "./schemas/validation-report.schema.json",
        "schema_version": "1.0",
        "program_id": "EPP-2026",
        "validator": {"version": __version__, "blob_sha256": "0" * 64},
        "observed_at": timestamp,
        "subject": {
            "resolution_status": "unresolved",
            "source_commit": None,
            "source_tree": None,
            "program_tree": None,
            "container_commit": None,
            "release_candidate": None,
            "worktree_clean": False,
            "checkout_representation": {"platform": "unknown", "autocrlf": "unknown", "dirty_path_count": 0},
            "input_manifest_digest": None,
            "input_manifest": [],
        },
        "verdict": "failed",
        "checks": [{"id": "SUBJECT_IDENTITY", "result": "failed"}],
        "findings": [item.as_dict() for item in findings],
        "eligibility": {"roadmap_item": None, "allowed_actions": [], "blockers": ["SUBJECT_UNRESOLVED"]},
        "areas": _empty_areas(),
        "benchmark_summary": default_benchmark_summary(),
        "release_approval": {"status": "absent", "approval_id": None, "subject_matches": False},
        "release_eligible": False,
        "delivery": {"mode": "validate", "status": "not_requested", "target_changed": False, "prior_snapshot_preserved": True},
        "next_action": None,
    }
