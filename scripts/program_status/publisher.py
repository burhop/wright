"""Build and atomically install a validated program-status bundle from Git."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import posixpath
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
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
SOURCE_CATALOG_SCHEMA_PATH: Final = (
    "specs/077-browser-program-status/contracts/"
    "program-status-source-catalog.schema.json"
)
BUNDLE_SCHEMA_PATH: Final = (
    "specs/077-browser-program-status/contracts/program-status-bundle.schema.json"
)
DASHBOARD_SCHEMA_PATH: Final = f"{PROGRAM_ROOT}/schemas/dashboard.schema.json"
TASK_RE = re.compile(r"^- \[(?P<done>[ xX])\] (?P<id>T[0-9]{3})\b", re.MULTILINE)
STORY_HEADING_RE = re.compile(r"^### EPP-US-(?P<number>[0-9]{3})\b", re.MULTILINE)
STORY_TABLE_RE = re.compile(
    r"^\| EPP-US-(?P<number>[0-9]{3}) \|.*\| (?P<maturity>[^|]+?) \|$",
    re.MULTILINE,
)


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
    mode: str = "manual"


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
    requires_human_approval: bool = False,
) -> dict[str, Any]:
    if requires_human_approval:
        eligibility = "requires_approval"
        authority_state = "not_authorized"
        action_blocker = blocker or label
    elif eligible:
        eligibility = "eligible"
        authority_state = "authorized"
        action_blocker = None
    else:
        eligibility = "blocked"
        authority_state = "not_authorized"
        action_blocker = blocker
    return {
        "id": identifier,
        "label": label[:500],
        "purpose": purpose,
        "eligibility": eligibility,
        "authority_state": authority_state,
        "requires_human_approval": requires_human_approval,
        "blocker": action_blocker,
        "evidence": evidence,
    }


def _verify_test_ledger_append_only(
    repository: Path, subject: Mapping[str, Any]
) -> str | None:
    ledger = subject["ledger"]
    runs = ledger.get("runs")
    if not isinstance(runs, list) or _digest(runs) != ledger.get("runs_sha256"):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_TEST_LEDGER_INVALID",
            "The test ledger runs digest does not reconcile.",
            "repair_test_run_ledger",
        )
    revision = ledger.get("ledger_revision")
    prior = ledger.get("prior_ledger")
    if prior is None:
        if revision != 1:
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_TEST_LEDGER_INVALID",
                "Only ledger revision 1 may omit prior-ledger identity.",
                "repair_test_run_ledger",
            )
        return None
    if (
        not isinstance(prior, Mapping)
        or revision != prior.get("ledger_revision", 0) + 1
    ):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_TEST_LEDGER_INVALID",
            "The prior-ledger revision does not form one append-only step.",
            "repair_test_run_ledger",
        )
    try:
        prior_raw = _git_blob(repository, str(prior["commit"]), TEST_LEDGER_PATH)
        prior_ledger = _strict_json(prior_raw, TEST_LEDGER_PATH)
    except (KeyError, ProgramStatusPublishError) as exc:
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_TEST_LEDGER_INVALID",
            "The prior-ledger committed identity cannot be resolved.",
            "repair_test_run_ledger",
        ) from exc
    prior_runs = prior_ledger.get("runs")
    if (
        prior_ledger.get("ledger_revision") != prior["ledger_revision"]
        or prior_ledger.get("runs_sha256") != prior["runs_sha256"]
        or not isinstance(prior_runs, list)
        or _digest(prior_runs) != prior["runs_sha256"]
        or runs[: len(prior_runs)] != prior_runs
    ):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_TEST_LEDGER_INVALID",
            "The test ledger does not preserve its exact committed prior prefix.",
            "repair_test_run_ledger",
        )
    return str(prior["runs_sha256"])


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


def _customer_story_maturity(raw: bytes) -> dict[str, int]:
    text = raw.decode("utf-8", errors="strict")
    definitions: dict[int, str] = {}
    for match in STORY_HEADING_RE.finditer(text):
        number = int(match.group("number"))
        if number in definitions:
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_CUSTOMER_CATALOG_INVALID",
                f"EPP-US-{number:03d} is defined more than once.",
                "repair_customer_story_catalog",
            )
        definitions[number] = "fully_defined"
    maturity_names = {
        "Ready to specify": "ready_to_specify",
        "Shaped": "shaped",
        "Candidate": "candidate",
        "Discovery shaped": "discovery_shaped",
        "Discovery": "discovery",
        "Discovery; separate T4 authority required": (
            "discovery_separate_t4_authority_required"
        ),
    }
    for match in STORY_TABLE_RE.finditer(text):
        number = int(match.group("number"))
        maturity = maturity_names.get(match.group("maturity"))
        if maturity is None or number in definitions:
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_CUSTOMER_CATALOG_INVALID",
                f"EPP-US-{number:03d} has a duplicate or unknown maturity.",
                "repair_customer_story_catalog",
            )
        definitions[number] = maturity
    if set(definitions) != set(range(1, 101)):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_CUSTOMER_CATALOG_INVALID",
            "The customer catalog must define exactly EPP-US-001 through 100.",
            "repair_customer_story_catalog",
        )
    result = {name: 0 for name in maturity_names.values()}
    result["fully_defined"] = 0
    for maturity in definitions.values():
        result[maturity] += 1
    return result


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


def _available_series(
    identifier: str,
    label: str,
    unit: str,
    counting_rule: str,
    source_classification: str,
    feature_id: str | None,
    observations: list[dict[str, Any]],
    evidence: list[dict[str, str]],
    limitation: str,
) -> dict[str, Any]:
    latest = observations[-1]
    previous = observations[-2]["value"] if len(observations) > 1 else None
    return {
        "id": identifier,
        "label": label,
        "unit": unit,
        "counting_rule": counting_rule,
        "source_classification": source_classification,
        "availability": "available",
        "feature_id": feature_id,
        "decision_use": "Use exact committed changes to choose the next bounded action.",
        "current_limitation": limitation,
        "next_action": _action(
            "CONTINUE_EVIDENCE_BACKED_DELIVERY",
            "Continue the next evidence-backed delivery task",
            "metric_guidance",
            evidence,
        ),
        "latest_change": {
            "commit": latest["commit"],
            "observed_at": latest["observed_at"],
            "from_value": previous,
            "to_value": latest["value"],
            "reason": latest["change_reason"] or latest["label"],
        },
        "omitted_observations": 0,
        "unavailable_reason": None,
        "observations": observations,
    }


def _path_commits(
    repository: Path, commit: str, path: str
) -> list[tuple[str, str, str]]:
    output = str(
        _git(
            repository,
            "log",
            "--format=%H%x09%cI%x09%s",
            "--max-count=250",
            commit,
            "--",
            path,
        )
    )
    rows: list[tuple[str, str, str]] = []
    for line in reversed(output.splitlines()):
        parts = line.split("\t", 2)
        if len(parts) == 3:
            rows.append((parts[0], parts[1], parts[2]))
    return rows


def _observations_for_path(
    repository: Path,
    commit: str,
    path: str,
    value_reader: Any,
    label: str,
    source_classification: str,
) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    previous_value: tuple[int | float, int | float | None] | None = None
    previous_commit: str | None = None
    for row_commit, observed_at, subject in _path_commits(repository, commit, path):
        raw = _git_blob(repository, row_commit, path)
        value, denominator = value_reader(raw)
        current_value = (value, denominator)
        if current_value == previous_value:
            previous_commit = row_commit
            continue
        observations.append(
            {
                "commit": row_commit,
                "transition_id": None,
                "parent_commit": previous_commit,
                "observed_at": observed_at,
                "value": current_value[0],
                "denominator": current_value[1],
                "label": label,
                "source_classification": source_classification,
                "change_reason": subject[:500],
                "evidence": [_evidence(f"{label}:{row_commit[:12]}", path, raw)],
            }
        )
        previous_value = current_value
        previous_commit = row_commit
    return observations


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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _write_publisher_state(
    data_root: Path,
    *,
    state: str,
    mode: str,
    observed_commit: str | None,
    last_attempt_at: str | None,
    last_success_at: str | None,
    failure_code: str | None,
    recovery: str | None,
) -> None:
    _atomic_write(
        data_root / PUBLISHER_FILENAME,
        _canonical_bytes(
            {
                "state": state,
                "mode": mode,
                "observed_commit": observed_commit,
                "last_attempt_at": last_attempt_at,
                "last_success_at": last_success_at,
                "failure_code": failure_code,
                "recovery": recovery,
            }
        ),
    )


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
        SOURCE_CATALOG_SCHEMA_PATH,
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
        "source_catalog_schema": _strict_json(
            blobs[SOURCE_CATALOG_SCHEMA_PATH], SOURCE_CATALOG_SCHEMA_PATH
        ),
        "bundle_schema": _strict_json(blobs[BUNDLE_SCHEMA_PATH], BUNDLE_SCHEMA_PATH),
        "dashboard_schema": _strict_json(
            blobs[DASHBOARD_SCHEMA_PATH], DASHBOARD_SCHEMA_PATH
        ),
    }


def _load_closed_catalog_sources(
    repository: Path, subject: Mapping[str, Any]
) -> dict[str, list[tuple[str, bytes]]]:
    """Resolve and validate only the inputs admitted by the frozen catalog."""

    catalog = subject["source_catalog"]
    catalog_schema = subject["source_catalog_schema"]
    catalog_errors = list(
        Draft202012Validator(
            catalog_schema, format_checker=FormatChecker()
        ).iter_errors(catalog)
    )
    if catalog_errors:
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_SOURCE_CATALOG_INVALID",
            "The frozen source catalog does not validate against its exact schema.",
            "repair_frozen_source_catalog",
        )
    sources = catalog.get("sources")
    if not isinstance(sources, Mapping) or len(sources) != 20:
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_SOURCE_CATALOG_INVALID",
            "The frozen source catalog must contain exactly 20 named sources.",
            "repair_frozen_source_catalog",
        )
    commit = str(subject["commit"])
    listed_raw = _git(
        repository,
        "ls-tree",
        "-r",
        "--name-only",
        commit,
        "--",
        PROGRAM_ROOT,
        "specs/076-control-plane-validator/contracts",
        "specs/077-browser-program-status/contracts",
    )
    assert isinstance(listed_raw, str)
    repository_paths = tuple(path for path in listed_raw.splitlines() if path)
    schema_paths = tuple(
        path for path in repository_paths if path.endswith(".schema.json")
    )
    schemas_by_id: dict[str, Mapping[str, Any]] = {}
    schema_ids_by_path: dict[str, str] = {}
    registry = Registry()
    for schema_path in schema_paths:
        schema = _strict_json(_git_blob(repository, commit, schema_path), schema_path)
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str):
            continue
        if schema_id in schemas_by_id and schemas_by_id[schema_id] != schema:
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_SCHEMA_INVALID",
                f"Schema identity {schema_id} is not unique.",
                "repair_frozen_schema",
            )
        Draft202012Validator.check_schema(schema)
        schemas_by_id[schema_id] = schema
        schema_ids_by_path[schema_path] = schema_id
        registry = registry.with_resource(schema_id, Resource.from_contents(schema))

    selected: dict[str, list[tuple[str, bytes]]] = {}
    for source_name, rule in sources.items():
        if not isinstance(rule, Mapping):
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_SOURCE_CATALOG_INVALID",
                f"Source rule {source_name} is not an object.",
                "repair_frozen_source_catalog",
            )
        if rule["path_kind"] == "exact":
            candidates = [str(rule["path"])]
        else:
            try:
                pattern = re.compile(str(rule["path_pattern"]))
            except re.error as exc:
                raise ProgramStatusPublishError(
                    "PROGRAM_STATUS_SOURCE_CATALOG_INVALID",
                    f"Source rule {source_name} has an invalid path pattern.",
                    "repair_frozen_source_catalog",
                ) from exc
            candidates = [path for path in repository_paths if pattern.fullmatch(path)]
        records: list[tuple[str, bytes]] = []
        allowed_schema_ids = set(rule["schema_ids"])
        for path in candidates:
            raw = _git_blob(repository, commit, path)
            if path.endswith(".json") and not str(rule["parser_contract"]).endswith(
                "LEGACY_IDENTITY_V1"
            ):
                value = _strict_json(raw, path)
                schema_id = value.get("$schema")
                if isinstance(schema_id, str) and schema_id.startswith(("./", "../")):
                    resolved_schema_path = posixpath.normpath(
                        posixpath.join(posixpath.dirname(path), schema_id)
                    )
                    schema_id = schema_ids_by_path.get(resolved_schema_path)
                if schema_id is None and len(allowed_schema_ids) == 1:
                    schema_id = next(iter(allowed_schema_ids))
                if (
                    schema_id not in allowed_schema_ids
                    or schema_id not in schemas_by_id
                ):
                    raise ProgramStatusPublishError(
                        "PROGRAM_STATUS_SOURCE_CATALOG_BOUNDARY",
                        f"{path} is not bound to an admitted source schema.",
                        "repair_catalog_source_binding",
                    )
                if rule["path_kind"] == "exact" and list(
                    Draft202012Validator(
                        schemas_by_id[str(schema_id)],
                        registry=registry,
                        format_checker=FormatChecker(),
                    ).iter_errors(value)
                ):
                    raise ProgramStatusPublishError(
                        "PROGRAM_STATUS_SOURCE_INVALID",
                        f"{path} fails its catalog-admitted schema.",
                        "repair_committed_source",
                    )
            records.append((path, raw))
        selected[str(source_name)] = records
    return selected


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
    story_maturity = _customer_story_maturity(blobs[CUSTOMER_CATALOG_PATH])
    ledger = subject["ledger"]
    prior_ledger_runs_sha256 = _verify_test_ledger_append_only(repository, subject)
    next_action_record = (state.get("next_eligible_actions") or [{}])[0]
    action_id = str(
        next_action_record.get("action", "CONTINUE_CURRENT_FEATURE_IMPLEMENTATION")
    )
    action_label = str(
        next_action_record.get(
            "reason", "Continue the authorized current feature implementation."
        )
    )
    requires_human_approval = bool(
        next_action_record.get("requires_human_approval", False)
    )
    current_action = _action(
        action_id,
        action_label,
        "current_program_action",
        [state_ref],
        eligible=not requires_human_approval,
        blocker=action_label if requires_human_approval else None,
        requires_human_approval=requires_human_approval,
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
    history_by_id: dict[str, list[dict[str, Any]]] = {}

    def dashboard_area(area: str) -> Any:
        def read(raw: bytes) -> tuple[int, int]:
            value = _strict_json(raw, DASHBOARD_PATH)["areas"][area]
            return int(value["passed_gates"]), int(value["required_gates"])

        return read

    for history_id, area in (
        ("product_readiness", "product_readiness"),
        ("benchmark_readiness", "benchmark_readiness"),
        ("commercial_readiness", "commercial_readiness"),
        ("program_health", "program_health"),
        ("governance", "program_health"),
    ):
        history_by_id[history_id] = _observations_for_path(
            repository,
            str(subject["commit"]),
            DASHBOARD_PATH,
            dashboard_area(area),
            history_id,
            "program_gate" if history_id == "governance" else "readiness_gate",
        )

    def benchmark_count(raw: bytes) -> tuple[int, int]:
        value = _strict_json(raw, DASHBOARD_PATH)["benchmark_summary"]
        return int(value["counted"]), int(value["target"])

    history_by_id["benchmark_qualified"] = _observations_for_path(
        repository,
        str(subject["commit"]),
        DASHBOARD_PATH,
        benchmark_count,
        "benchmark_qualified",
        "benchmark_qualification",
    )
    feature_task_path = next(
        (
            str(item["tasks_path"])
            for item in subject["work_registry"].get("task_sources", [])
            if isinstance(item, Mapping) and item.get("feature_id") == feature_id
        ),
        "specs/077-browser-program-status/tasks.md",
    )
    history_by_id["feature_tasks"] = _observations_for_path(
        repository,
        str(subject["commit"]),
        feature_task_path,
        _task_counts,
        "feature_tasks",
        "feature_task",
    )
    historical_evidence: dict[str, dict[str, Any]] = {}
    for observations in history_by_id.values():
        for observation in observations:
            for reference in observation["evidence"]:
                detail = {
                    **reference,
                    "label": str(observation["label"]).replace("_", " ").title(),
                    "summary": (
                        "Exact committed identity for historical observation "
                        f"{observation['commit'][:12]}."
                    ),
                    "freshness": (
                        "current"
                        if observation["commit"] == subject["commit"]
                        else "stale"
                    ),
                    "recovery": None,
                    "availability": "identity_only",
                    "exact_url": None,
                }
                previous = historical_evidence.get(reference["id"])
                if previous is not None and previous != detail:
                    raise ProgramStatusPublishError(
                        "PROGRAM_STATUS_EVIDENCE_ID_COLLISION",
                        f"Historical evidence ID {reference['id']} is not unique.",
                        "repair_history_evidence_identity",
                    )
                historical_evidence[reference["id"]] = detail
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
            (
                _available_series(
                    *definition,
                    history_by_id[definition[0]],
                    [state_ref],
                    "History contains exact commits only; unsupported categories remain unavailable.",
                )
                if history_by_id.get(definition[0])
                else _unavailable_series(*definition, [state_ref])
            )
            for definition in history_definitions
        ],
        "customer_catalog": {
            "proposed_total": 100,
            "source_path": CUSTOMER_CATALOG_PATH,
            "source_digest": _raw_digest(blobs[CUSTOMER_CATALOG_PATH]),
            "maturity_counts": story_maturity,
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
                "prior_ledger_runs_sha256": prior_ledger_runs_sha256,
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
        ]
        + [historical_evidence[key] for key in sorted(historical_evidence)],
    }


def publish_program_status(
    request: ProgramStatusPublishRequest,
) -> ProgramStatusPublishResult:
    """Publish one deterministic bundle from one exact committed subject."""

    repository = request.repository.resolve()
    data_root = request.data_root.resolve()
    if request.mode not in {"manual", "committed_watch", "package_install"}:
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_MODE_INVALID",
            "Publisher mode is not part of the closed contract.",
            "use_supported_publisher_mode",
        )
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
        subject["catalog_sources"] = _load_closed_catalog_sources(repository, subject)
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
        observed_at = _now()
        _write_publisher_state(
            data_root,
            state="active",
            mode=request.mode,
            observed_commit=str(subject["commit"]),
            last_attempt_at=observed_at,
            last_success_at=observed_at,
            failure_code=None,
            recovery=None,
        )
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


def watch_program_status(
    request: ProgramStatusPublishRequest,
    *,
    poll_seconds: float = 2.0,
    max_polls: int | None = None,
) -> ProgramStatusPublishResult | None:
    """Publish when committed HEAD changes and maintain a separate heartbeat."""

    if poll_seconds <= 0:
        raise ValueError("poll_seconds must be positive")
    watch_request = ProgramStatusPublishRequest(
        repository=request.repository,
        source_commit="HEAD",
        data_root=request.data_root,
        mode="committed_watch",
    )
    last_observed: str | None = None
    last_success_at: str | None = None
    last_result: ProgramStatusPublishResult | None = None
    polls = 0
    while max_polls is None or polls < max_polls:
        polls += 1
        attempted_at = _now()
        try:
            observed = str(
                _git(request.repository.resolve(), "rev-parse", "HEAD^{commit}")
            ).strip()
            if observed != last_observed:
                last_result = publish_program_status(watch_request)
                last_observed = observed
                last_success_at = attempted_at
            else:
                _write_publisher_state(
                    request.data_root.resolve(),
                    state="active",
                    mode="committed_watch",
                    observed_commit=observed,
                    last_attempt_at=attempted_at,
                    last_success_at=last_success_at,
                    failure_code=None,
                    recovery=None,
                )
        except ProgramStatusPublishError as exc:
            _write_publisher_state(
                request.data_root.resolve(),
                state="failed",
                mode="committed_watch",
                observed_commit=last_observed,
                last_attempt_at=attempted_at,
                last_success_at=last_success_at,
                failure_code=exc.code,
                recovery=exc.recovery_class,
            )
        if max_polls is None or polls < max_polls:
            time.sleep(poll_seconds)
    return last_result
