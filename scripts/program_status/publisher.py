"""Build and atomically install a validated program-status bundle from Git."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

from jsonschema import Draft202012Validator, FormatChecker  # type: ignore[import-untyped]
from referencing import Registry, Resource


LOGGER = logging.getLogger(__name__)
SCHEMA_VERSION: Final = "1.0.0"
CURRENT_FILENAME: Final = "current.json"
PUBLISHER_FILENAME: Final = "publisher.json"
PROGRAM_ROOT: Final = "docs/programs/engineering-process-platform"
DASHBOARD_PATH: Final = f"{PROGRAM_ROOT}/dashboard.json"
STATE_PATH: Final = f"{PROGRAM_ROOT}/program-state.json"
LIFECYCLE_PATH: Final = f"{PROGRAM_ROOT}/lifecycle-policy.json"
WORK_REGISTRY_PATH: Final = f"{PROGRAM_ROOT}/work-registry.json"
USE_CASE_REGISTRY_PATH: Final = f"{PROGRAM_ROOT}/use-case-registry.json"
TEST_LEDGER_PATH: Final = f"{PROGRAM_ROOT}/test-run-ledger.json"
CUSTOMER_CATALOG_PATH: Final = f"{PROGRAM_ROOT}/customer-process-user-stories.md"
SOURCE_CATALOG_PATH: Final = (
    "specs/077-browser-program-status/contracts/program-status-source-catalog.json"
)
BUNDLE_SCHEMA_PATH: Final = (
    "specs/077-browser-program-status/contracts/program-status-bundle.schema.json"
)
DASHBOARD_SCHEMA_PATH: Final = f"{PROGRAM_ROOT}/schemas/dashboard.schema.json"
TASK_RE = re.compile(r"^- \[(?P<done>[ xX])\] (?P<id>T[0-9]{3})\b", re.MULTILINE)
STORY_RE = re.compile(r"\bEPP-US-(?P<number>[0-9]{3})\b")


class ProgramStatusPublishError(RuntimeError):
    """Typed failure raised when a candidate cannot be safely published."""

    def __init__(self, code: str, message: str, recovery_class: str) -> None:
        super().__init__(message)
        self.code = code
        self.recovery_class = recovery_class


@dataclass(frozen=True, slots=True)
class ProgramStatusPublishRequest:
    """Exact committed subject and stable data-root publication request."""

    repository: Path
    source_commit: str
    data_root: Path


@dataclass(frozen=True, slots=True)
class ProgramStatusPublishResult:
    """Non-secret identity returned after a successful atomic publication."""

    source_commit: str
    source_tree: str
    program_tree: str
    bundle_id: str
    installed_artifact: str
    changed: bool


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _raw_digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _git(repository: Path, *args: str, text: bool = True) -> str | bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(repository), *args],
            check=True,
            capture_output=True,
            text=text,
            encoding="utf-8" if text else None,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_GIT_READ_FAILED",
            "The exact committed subject could not be read.",
            "verify_repository_and_committed_subject",
        ) from exc
    return result.stdout


def _git_blob(repository: Path, commit: str, path: str) -> bytes:
    value = _git(repository, "show", f"{commit}:{path}", text=False)
    assert isinstance(value, bytes)
    return value


def _strict_json(raw: bytes, path: str) -> dict[str, Any]:
    duplicate = False

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        nonlocal duplicate
        result: dict[str, Any] = {}
        for key, value in items:
            duplicate = duplicate or key in result
            result[key] = value
        return result

    try:
        if raw.startswith(b"\xef\xbb\xbf"):
            raise ValueError("BOM")
        value = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=pairs,
            parse_constant=lambda _value: (_ for _ in ()).throw(ValueError()),
        )
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_SOURCE_INVALID",
            f"{path} is not strict UTF-8 JSON.",
            "repair_committed_source",
        ) from exc
    if duplicate or not isinstance(value, dict):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_SOURCE_INVALID",
            f"{path} must be an object without duplicate keys.",
            "repair_committed_source",
        )
    return value


def _evidence(identifier: str, path: str, raw: bytes) -> dict[str, str]:
    return {"id": identifier, "path": path, "sha256": _raw_digest(raw)}


def _action(
    identifier: str,
    label: str,
    purpose: str,
    evidence: list[dict[str, str]],
    *,
    eligible: bool = True,
    blocker: str | None = None,
) -> dict[str, Any]:
    return {
        "id": identifier,
        "label": label[:500],
        "purpose": purpose,
        "eligibility": "eligible" if eligible else "blocked",
        "authority_state": "authorized" if eligible else "not_authorized",
        "requires_human_approval": False,
        "blocker": None if eligible else blocker,
        "evidence": evidence,
    }


def _task_counts(raw: bytes) -> tuple[int, int]:
    matches = list(TASK_RE.finditer(raw.decode("utf-8", errors="strict")))
    identifiers = [match.group("id") for match in matches]
    if len(identifiers) != len(set(identifiers)):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_TASK_ID_DUPLICATE",
            "A registered task graph contains duplicate task IDs.",
            "repair_registered_task_graph",
        )
    return sum(match.group("done").lower() == "x" for match in matches), len(matches)


def _unavailable_series(
    identifier: str,
    label: str,
    unit: str,
    counting_rule: str,
    source_classification: str,
    feature_id: str | None,
    evidence: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "id": identifier,
        "label": label,
        "unit": unit,
        "counting_rule": counting_rule,
        "source_classification": source_classification,
        "availability": "unavailable",
        "feature_id": feature_id,
        "decision_use": "Use committed checkpoints to detect meaningful movement and stalls.",
        "current_limitation": "No canonical committed observation series is recorded yet.",
        "next_action": _action(
            "RECORD_CANONICAL_OBSERVATION",
            "Record the next canonical committed observation",
            "metric_guidance",
            evidence,
        ),
        "latest_change": None,
        "omitted_observations": 0,
        "unavailable_reason": "No canonical committed observation series is recorded yet.",
        "observations": [],
    }


def _graph_context(evidence: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "meaning": "Shows evidence-backed movement without estimating calendar duration.",
        "latest_change": None,
        "current_limitation": "No canonical history is recorded yet.",
        "next_action": _action(
            "RECORD_CANONICAL_OBSERVATION",
            "Record a canonical committed observation",
            "metric_guidance",
            evidence,
        ),
    }


def _atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        if hasattr(os, "O_DIRECTORY"):
            directory_descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_descriptor)
            finally:
                os.close(directory_descriptor)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _load_subject(repository: Path, commit: str) -> dict[str, Any]:
    resolved = str(_git(repository, "rev-parse", f"{commit}^{{commit}}")).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", resolved):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_SUBJECT_INVALID",
            "The requested source did not resolve to one commit.",
            "use_exact_committed_subject",
        )
    validator = subprocess.run(
        [
            sys.executable,
            str(repository / "scripts" / "validate-engineering-process-program.py"),
            "validate",
            "--source",
            resolved,
            "--format",
            "json",
        ],
        cwd=repository,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if validator.returncode != 0:
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_SUBJECT_VALIDATION_FAILED",
            "The exact committed program subject did not pass the authoritative validator.",
            "repair_committed_program_subject",
        )
    paths = (
        DASHBOARD_PATH,
        STATE_PATH,
        LIFECYCLE_PATH,
        WORK_REGISTRY_PATH,
        USE_CASE_REGISTRY_PATH,
        TEST_LEDGER_PATH,
        CUSTOMER_CATALOG_PATH,
        SOURCE_CATALOG_PATH,
        BUNDLE_SCHEMA_PATH,
        DASHBOARD_SCHEMA_PATH,
    )
    blobs = {path: _git_blob(repository, resolved, path) for path in paths}
    return {
        "commit": resolved,
        "tree": str(_git(repository, "show", "-s", "--format=%T", resolved)).strip(),
        "program_tree": str(
            _git(repository, "rev-parse", f"{resolved}:{PROGRAM_ROOT}")
        ).strip(),
        "generated_at": str(
            _git(repository, "show", "-s", "--format=%cI", resolved)
        ).strip(),
        "blobs": blobs,
        "dashboard": _strict_json(blobs[DASHBOARD_PATH], DASHBOARD_PATH),
        "state": _strict_json(blobs[STATE_PATH], STATE_PATH),
        "lifecycle": _strict_json(blobs[LIFECYCLE_PATH], LIFECYCLE_PATH),
        "work_registry": _strict_json(blobs[WORK_REGISTRY_PATH], WORK_REGISTRY_PATH),
        "use_case_registry": _strict_json(
            blobs[USE_CASE_REGISTRY_PATH], USE_CASE_REGISTRY_PATH
        ),
        "ledger": _strict_json(blobs[TEST_LEDGER_PATH], TEST_LEDGER_PATH),
        "source_catalog": _strict_json(blobs[SOURCE_CATALOG_PATH], SOURCE_CATALOG_PATH),
        "bundle_schema": _strict_json(blobs[BUNDLE_SCHEMA_PATH], BUNDLE_SCHEMA_PATH),
        "dashboard_schema": _strict_json(
            blobs[DASHBOARD_SCHEMA_PATH], DASHBOARD_SCHEMA_PATH
        ),
    }


def _registered_task_counts(
    repository: Path,
    subject: Mapping[str, Any],
    feature_id: str,
) -> tuple[list[str], int, int, int, int]:
    registered: list[str] = []
    program_completed = program_total = feature_completed = feature_total = 0
    for source in subject["work_registry"].get("task_sources", []):
        if not isinstance(source, Mapping) or not isinstance(
            source.get("tasks_path"), str
        ):
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_WORK_REGISTRY_INVALID",
                "Every task source needs an exact tasks_path.",
                "repair_work_registry",
            )
        task_path = str(source["tasks_path"])
        completed, total = _task_counts(
            _git_blob(repository, str(subject["commit"]), task_path)
        )
        registered.append(task_path)
        program_completed += completed
        program_total += total
        if source.get("feature_id") == feature_id:
            feature_completed, feature_total = completed, total
    return (
        registered,
        program_completed,
        program_total,
        feature_completed,
        feature_total,
    )


def _use_case_counts(subject: Mapping[str, Any]) -> tuple[list[Any], list[str]]:
    use_cases = subject["use_case_registry"].get("use_cases")
    if not isinstance(use_cases, list):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_USE_CASE_REGISTRY_INVALID",
            "The governed use-case registry must contain an array.",
            "repair_use_case_registry",
        )
    identifiers = [item.get("id") for item in use_cases if isinstance(item, Mapping)]
    if len(identifiers) != len(use_cases) or len(identifiers) != len(set(identifiers)):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_USE_CASE_REGISTRY_INVALID",
            "Governed use-case IDs must be present and unique.",
            "repair_use_case_registry",
        )
    process_ids = [
        str(item["process_100_id"])
        for item in use_cases
        if isinstance(item, Mapping) and item.get("process_100_id") is not None
    ]
    valid_process_ids = {f"EPP-PROC-{number:03d}" for number in range(1, 101)}
    if (
        len(process_ids) != len(set(process_ids))
        or not set(process_ids) <= valid_process_ids
    ):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_PROCESS_ID_INVALID",
            "Process IDs must be unique and range from EPP-PROC-001 through 100.",
            "repair_use_case_registry",
        )
    return use_cases, process_ids


def _build_supplement(repository: Path, subject: Mapping[str, Any]) -> dict[str, Any]:
    blobs = subject["blobs"]
    state = subject["state"]
    lifecycle = subject["lifecycle"]
    dashboard = subject["dashboard"]
    feature_id = str(state.get("current_feature") or "EPP-F01B")
    state_ref = _evidence("program-state", STATE_PATH, blobs[STATE_PATH])
    dashboard_ref = _evidence("dashboard", DASHBOARD_PATH, blobs[DASHBOARD_PATH])
    registered, program_done, program_total, feature_done, feature_total = (
        _registered_task_counts(repository, subject, feature_id)
    )
    use_cases, process_ids = _use_case_counts(subject)
    story_numbers = {
        int(match.group("number"))
        for match in STORY_RE.finditer(blobs[CUSTOMER_CATALOG_PATH].decode("utf-8"))
    }
    if story_numbers != set(range(1, 101)):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_CUSTOMER_CATALOG_INVALID",
            "The customer catalog must contain exactly EPP-US-001 through 100.",
            "repair_customer_story_catalog",
        )
    ledger = subject["ledger"]
    runs = ledger.get("runs")
    if not isinstance(runs, list) or _digest(runs) != ledger.get("runs_sha256"):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_TEST_LEDGER_INVALID",
            "The test ledger runs digest does not reconcile.",
            "repair_test_run_ledger",
        )
    next_action_record = (state.get("next_eligible_actions") or [{}])[0]
    action_id = str(
        next_action_record.get("action", "CONTINUE_CURRENT_FEATURE_IMPLEMENTATION")
    )
    action_label = str(
        next_action_record.get(
            "reason", "Continue the authorized current feature implementation."
        )
    )
    current_action = _action(
        action_id, action_label, "current_program_action", [state_ref]
    )
    history_definitions = (
        (
            "customer_capability",
            "Customer capability",
            "accepted_customer_scenarios",
            "distinct_committed_customer_acceptance",
            "product_acceptance",
            None,
        ),
        (
            "quality",
            "Quality",
            "passing_required_checks_ratio",
            "required_candidate_checks",
            "test_evidence",
            None,
        ),
        (
            "process_automation",
            "Process automation",
            "demonstrated_lifecycle_capabilities",
            "distinct_committed_lifecycle_demonstrations",
            "automation_capability",
            None,
        ),
        (
            "governance",
            "Governance",
            "passing_program_gates_ratio",
            "authoritative_program_health_gates",
            "program_gate",
            None,
        ),
        (
            "product_readiness",
            "Product readiness",
            "passing_readiness_gates_ratio",
            "authoritative_readiness_area_gates",
            "readiness_gate",
            None,
        ),
        (
            "benchmark_readiness",
            "Benchmark readiness",
            "passing_readiness_gates_ratio",
            "authoritative_readiness_area_gates",
            "readiness_gate",
            None,
        ),
        (
            "commercial_readiness",
            "Commercial readiness",
            "passing_readiness_gates_ratio",
            "authoritative_readiness_area_gates",
            "readiness_gate",
            None,
        ),
        (
            "program_health",
            "Program health",
            "passing_readiness_gates_ratio",
            "authoritative_readiness_area_gates",
            "readiness_gate",
            None,
        ),
        (
            "benchmark_qualified",
            "Benchmark qualified",
            "qualified_processes_of_100",
            "governed_qualification_only",
            "benchmark_qualification",
            None,
        ),
        (
            "program_tasks",
            "Program tasks",
            "completed_program_tasks_ratio",
            "closed_registered_task_sources",
            "program_task",
            None,
        ),
        (
            "feature_tasks",
            "Feature tasks",
            "completed_feature_tasks_ratio",
            "exact_feature_task_ids",
            "feature_task",
            feature_id,
        ),
        (
            "integration_delivery",
            "Integration delivery",
            "completed_integration_gates_of_8",
            "ordered_integration_gate_completion",
            "integration_gate",
            None,
        ),
    )
    graph_context = _graph_context([state_ref])
    benchmark_blocker = "Benchmark execution is not authorized and remains at 0/100."
    lane_blocker = "Push, PR, merge, and dev integration are not authorized."
    lease = state.get("active_mutating_lease")
    policy_limits = lifecycle.get("wip_limits", {})
    observed_at = str(subject["generated_at"])
    evidence_pairs = (
        ("dashboard", DASHBOARD_PATH),
        ("program-state", STATE_PATH),
        ("source-catalog", SOURCE_CATALOG_PATH),
        ("work-registry", WORK_REGISTRY_PATH),
        ("use-case-registry", USE_CASE_REGISTRY_PATH),
        ("test-run-ledger", TEST_LEDGER_PATH),
    )
    return {
        "history": [
            _unavailable_series(*definition, [state_ref])
            for definition in history_definitions
        ],
        "customer_catalog": {
            "proposed_total": 100,
            "source_path": CUSTOMER_CATALOG_PATH,
            "source_digest": _raw_digest(blobs[CUSTOMER_CATALOG_PATH]),
            "maturity_counts": {
                "fully_defined": 5,
                "ready_to_specify": 5,
                "shaped": 15,
                "candidate": 45,
                "discovery_shaped": 15,
                "discovery": 14,
                "discovery_separate_t4_authority_required": 1,
            },
        },
        "use_cases": {
            "source_path": USE_CASE_REGISTRY_PATH,
            "source_digest": _raw_digest(blobs[USE_CASE_REGISTRY_PATH]),
            "all": {
                "total": len(use_cases),
                "not_started": len(use_cases),
                "in_progress": 0,
                "implemented": 0,
                "independently_verified": 0,
                "remaining": len(use_cases),
            },
            "process_100": {
                "population_target": 100,
                "defined": len(process_ids),
                "in_progress": 0,
                "implemented": 0,
                "tested": 0,
                "independently_verified": 0,
                "benchmark_qualified": int(dashboard["benchmark_summary"]["counted"]),
            },
            "items": [],
            "graph_context": graph_context,
        },
        "test_history": {
            "availability": "unavailable",
            "counting_rule": "latest_terminal_attempt_per_commit_suite_id_population_id",
            "pass_rate_rule": "passed_divided_by_passed_plus_failed_else_unavailable",
            "identity_digest_rule": "wright_test_id_set_v1_lf_then_utf8_byte_lexicographic_unique_nfc_ids_length_colon_bytes_lf_sha256",
            "run_key_rule": "wright_test_run_key_v1_lf_then_length_framed_nfc_utf8_commit_suite_population_attempt_sha256",
            "runs_digest_rule": "wright_json_c14n_v1_nfc_sha256_complete_runs_array_in_stored_order",
            "selection_attestation": {
                "source_path": TEST_LEDGER_PATH,
                "source_digest": _raw_digest(blobs[TEST_LEDGER_PATH]),
                "ledger_revision": int(ledger["ledger_revision"]),
                "prior_ledger_runs_sha256": None,
                "runs_sha256": str(ledger["runs_sha256"]),
                "publisher_verified_append_only": True,
                "selected_run_ids": [],
            },
            "graph_context": graph_context,
            "unavailable_reason": "No canonical committed test run exists yet.",
            "checkpoints": [],
        },
        "benchmark_context": {
            "phase": "on_hold",
            "hold_state": "on_hold",
            "hold_reason": benchmark_blocker,
            "dependencies": [],
            "authorization_state": "not_authorized",
            "next_qualifying_action": _action(
                "AUTHORIZE_BENCHMARK_EXECUTION",
                "Authorize benchmark execution only after roadmap dependencies pass",
                "benchmark_qualifying_action",
                [dashboard_ref],
                eligible=False,
                blocker=benchmark_blocker,
            ),
            "evidence": [dashboard_ref],
        },
        "work": {
            "current_milestone": "Deliver the browser-accessible program status page",
            "active_feature": feature_id,
            "lease": dict(lease) if isinstance(lease, Mapping) else None,
            "program_tasks": {
                "completed": program_done,
                "total": program_total,
                "remaining": program_total - program_done,
                "registered_sources": registered,
                "undecomposed_roadmap_items": [],
            },
            "tasks": {
                "feature_id": feature_id,
                "completed": feature_done,
                "total": feature_total,
                "remaining": feature_total - feature_done,
            },
            "active_assignments": list(
                subject["work_registry"].get("active_assignments", [])
            ),
            "checkpoints": [],
            "blockers": [],
            "current_next_action": current_action,
            "lanes": [
                {
                    "kind": "integration",
                    "branch": "077-control-plane-validator",
                    "milestone": "EPP-F01 integrated to dev",
                    "latest_capability": "Committed control-plane validation is available on dev.",
                    "blocker": lane_blocker,
                    "next_action": _action(
                        "REQUEST_INTEGRATION_AUTHORITY",
                        "Request authority before external integration",
                        "lane_next_action",
                        [state_ref],
                        eligible=False,
                        blocker=lane_blocker,
                    ),
                    "observed_at": observed_at,
                    "evidence": [state_ref],
                    "target_branch": "dev",
                    "frozen_candidate": None,
                    "last_pushed_commit": None,
                    "last_pushed_at": None,
                    "pull_request": None,
                    "phase": "merged",
                    "checks": None,
                    "ci_started_at": None,
                    "first_actionable_failure": None,
                    "dev_sync": "integrated",
                    "merge_gate": "passed historically",
                    "authority_state": "not_authorized",
                    "events": [],
                },
                {
                    "kind": "continued_development",
                    "branch": str(lease.get("branch", "unavailable"))
                    if isinstance(lease, Mapping)
                    else "unavailable",
                    "milestone": "Browser program status",
                    "latest_capability": "Read-only API and browser surface implemented; committed publisher is in progress.",
                    "blocker": None,
                    "next_action": _action(
                        "CONTINUE_CURRENT_FEATURE_IMPLEMENTATION",
                        "Continue local EPP-F01B implementation",
                        "lane_next_action",
                        [state_ref],
                    ),
                    "observed_at": observed_at,
                    "evidence": [state_ref],
                    "base_commit": str(state["baseline"]["commit"]),
                    "authority_state": "authorized",
                },
            ],
        },
        "governance": {
            "corrections": [],
            "findings": [],
            "risks": [],
            "decisions": [],
            "verification": [],
            "limits": {
                "wip_max": int(policy_limits["wip_max"]),
                "repair_max": int(policy_limits["repair_max"]),
                "push_max": int(policy_limits["push_max"]),
            },
            "flow": {
                "active_feature_count": 1,
                "active_lease_count": 1 if lease else 0,
                "roadmap_blocker_count": 0,
                "open_p0_decision_count": len(state.get("open_p0_decisions", [])),
                "open_p0_risk_count": 0,
            },
        },
        "evidence_index": [
            {
                "id": identifier,
                "label": identifier.replace("-", " ").title(),
                "path": path,
                "sha256": _raw_digest(blobs[path]),
                "summary": "Exact committed identity used to derive this status bundle.",
                "freshness": "current",
                "recovery": None,
                "availability": "checkout_available",
                "exact_url": None,
            }
            for identifier, path in evidence_pairs
        ],
    }


def publish_program_status(
    request: ProgramStatusPublishRequest,
) -> ProgramStatusPublishResult:
    """Publish one deterministic bundle from one exact committed subject."""

    repository = request.repository.resolve()
    data_root = request.data_root.resolve()
    LOGGER.info("program-status publication started source=%s", request.source_commit)
    try:
        subject = _load_subject(repository, request.source_commit)
        source_catalog = subject["source_catalog"]
        if (
            source_catalog.get("schema_version") != SCHEMA_VERSION
            or len(source_catalog.get("sources", {})) != 20
        ):
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_SOURCE_CATALOG_INVALID",
                "The frozen source catalog must contain exactly 20 named sources.",
                "repair_frozen_source_catalog",
            )
        supplement = _build_supplement(repository, subject)
        blobs = subject["blobs"]
        dashboard_ref = _evidence("dashboard", DASHBOARD_PATH, blobs[DASHBOARD_PATH])
        source = {
            "commit": subject["commit"],
            "tree": subject["tree"],
            "program_tree": subject["program_tree"],
            "snapshot_path": DASHBOARD_PATH,
            "snapshot_raw_sha256": _raw_digest(blobs[DASHBOARD_PATH]),
            "raw_identity_verification": "publisher_git_blob_attested",
            "raw_identity_evidence": dashboard_ref,
            "dashboard_canonical_sha256": _digest(subject["dashboard"]),
            "source_catalog_path": SOURCE_CATALOG_PATH,
            "source_catalog_sha256": _raw_digest(blobs[SOURCE_CATALOG_PATH]),
            "validation_transition": str(subject["state"]["last_transition"]),
            "validation_verdict": "passed",
        }
        bundle: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "bundle_id": _digest(
                {
                    "source": source,
                    "dashboard": subject["dashboard"],
                    "supplement": supplement,
                }
            ),
            "generated_at": subject["generated_at"],
            "source": source,
            "dashboard": subject["dashboard"],
            "supplement": supplement,
        }
        dashboard_schema = subject["dashboard_schema"]
        dashboard_id = dashboard_schema.get("$id")
        if not isinstance(dashboard_id, str):
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_SCHEMA_INVALID",
                "The dashboard schema has no stable $id.",
                "repair_frozen_schema",
            )
        registry = Registry().with_resource(
            dashboard_id, Resource.from_contents(dashboard_schema)
        )
        errors = sorted(
            Draft202012Validator(
                subject["bundle_schema"],
                registry=registry,
                format_checker=FormatChecker(),
            ).iter_errors(bundle),
            key=lambda error: list(error.absolute_path),
        )
        if errors:
            first = errors[0]
            pointer = "/" + "/".join(str(item) for item in first.absolute_path)
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_BUNDLE_INVALID",
                f"Generated bundle failed its frozen schema at {pointer}: {first.message}",
                "repair_publisher_derivation",
            )
        raw = _canonical_bytes(bundle)
        installed = data_root / CURRENT_FILENAME
        try:
            changed = installed.read_bytes() != raw
        except FileNotFoundError:
            changed = True
        if changed:
            _atomic_write(installed, raw)
        publisher_state = {
            "state": "active",
            "mode": "manual",
            "observed_commit": subject["commit"],
            "last_attempt_at": subject["generated_at"],
            "last_success_at": subject["generated_at"],
            "failure_code": None,
            "recovery": None,
        }
        _atomic_write(data_root / PUBLISHER_FILENAME, _canonical_bytes(publisher_state))
    except ProgramStatusPublishError:
        LOGGER.warning("program-status publication rejected")
        raise
    except OSError as exc:
        LOGGER.warning("program-status atomic installation failed")
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_INSTALL_FAILED",
            "The validated bundle could not be atomically installed.",
            "retry_after_inspecting_data_root",
        ) from exc
    LOGGER.info(
        "program-status publication completed source=%s changed=%s",
        subject["commit"],
        changed,
    )
    return ProgramStatusPublishResult(
        source_commit=str(subject["commit"]),
        source_tree=str(subject["tree"]),
        program_tree=str(subject["program_tree"]),
        bundle_id=str(bundle["bundle_id"]),
        installed_artifact=CURRENT_FILENAME,
        changed=changed,
    )
