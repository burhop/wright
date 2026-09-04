"""Build and atomically install a validated program-status bundle from Git."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import logging
import os
import posixpath
import re
import subprocess
import sys
import tempfile
import time
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, Mapping
from urllib.parse import urlsplit

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
TASK_DETAIL_RE = re.compile(
    r"^- \[(?P<done>[ xX])\] (?P<id>T[0-9]{3})(?: \[[^\]]+\])* (?P<title>.+)$",
    re.MULTILINE,
)
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


def _normalize_canonical_numbers(value: object) -> object:
    """Make JSON numbers portable across Python and browser runtimes."""

    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, list):
        return [_normalize_canonical_numbers(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize_canonical_numbers(item) for key, item in value.items()}
    return value


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        _normalize_canonical_numbers(value),
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
    authority_override: str | None = None,
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
    resolved_authority_state = authority_override or authority_state
    return {
        "id": identifier,
        "label": label[:500],
        "purpose": purpose,
        "eligibility": eligibility,
        "authority_state": resolved_authority_state,
        "requires_human_approval": requires_human_approval,
        "blocker": action_blocker,
        "evidence": evidence,
    }


def _verify_test_ledger_append_only(
    repository: Path, subject: Mapping[str, Any]
) -> str | None:
    ledger = subject["ledger"]
    runs = ledger.get("runs")

    def strings_are_canonical(node: Any) -> bool:
        if isinstance(node, str):
            return "\x00" not in node and unicodedata.normalize("NFC", node) == node
        if isinstance(node, Mapping):
            return all(
                strings_are_canonical(key) and strings_are_canonical(value)
                for key, value in node.items()
            )
        if isinstance(node, list):
            return all(strings_are_canonical(value) for value in node)
        return True

    if not isinstance(runs, list) or _digest(runs) != ledger.get("runs_sha256"):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_TEST_LEDGER_INVALID",
            "The test ledger runs digest does not reconcile.",
            "repair_test_run_ledger",
        )
    if not strings_are_canonical(runs):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_TEST_LEDGER_INVALID",
            "Test ledger strings must already be NFC and contain no NUL.",
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


def _framed_digest(prefix: str, values: list[str]) -> str:
    framed = bytearray(f"{prefix}\n".encode())
    for value in values:
        if "\x00" in value or unicodedata.normalize("NFC", value) != value:
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_TEST_LEDGER_INVALID",
                "Digest input strings must already be NFC and contain no NUL.",
                "repair_test_run_ledger",
            )
        encoded = value.encode("utf-8")
        framed.extend(str(len(encoded)).encode())
        framed.extend(b":")
        framed.extend(encoded)
        framed.extend(b"\n")
    return hashlib.sha256(framed).hexdigest()


def _test_case_set_digest(test_case_ids: list[str]) -> str:
    if any(
        "\x00" in item or unicodedata.normalize("NFC", item) != item
        for item in test_case_ids
    ) or len(test_case_ids) != len(set(test_case_ids)):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_TEST_LEDGER_INVALID",
            "A test population contains duplicate NFC-normalized identities.",
            "repair_test_run_ledger",
        )
    return _framed_digest(
        "wright-test-id-set-v1",
        sorted(test_case_ids, key=lambda item: item.encode("utf-8")),
    )


def _test_run_key(run: Mapping[str, Any]) -> str:
    return _framed_digest(
        "wright-test-run-key-v1",
        [
            str(run["commit"]),
            str(run["suite_id"]),
            str(run["population_id"]),
            str(run["attempt"]),
        ],
    )


def _project_test_history(
    ledger: Mapping[str, Any], current_commit: str
) -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]]]:
    runs = ledger["runs"]
    run_ids = [str(run["run_id"]) for run in runs]
    run_keys = [str(run["run_key"]) for run in runs]
    if len(run_ids) != len(set(run_ids)) or len(run_keys) != len(set(run_keys)):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_TEST_LEDGER_INVALID",
            "Test run IDs and canonical run keys must be unique.",
            "repair_test_run_ledger",
        )
    latest: dict[tuple[str, str, str], Mapping[str, Any]] = {}
    for run in runs:
        test_ids = list(run["test_case_ids"])
        counts = run["counts"]
        if (
            str(run["run_key"]) != _test_run_key(run)
            or str(run["test_case_set_sha256"]) != _test_case_set_digest(test_ids)
            or counts["total"] != len(test_ids)
            or sum(counts[name] for name in ("passed", "failed", "skipped", "not_run"))
            != counts["total"]
        ):
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_TEST_LEDGER_INVALID",
                f"Test run {run['run_id']} does not reconcile.",
                "repair_test_run_ledger",
            )
        if not run["terminal"]:
            continue
        key = (str(run["commit"]), str(run["suite_id"]), str(run["population_id"]))
        previous = latest.get(key)
        if previous is None or run["attempt"] > previous["attempt"]:
            latest[key] = run
        elif run["attempt"] == previous["attempt"] and run != previous:
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_TEST_LEDGER_INVALID",
                "A test population has conflicting latest terminal attempts.",
                "repair_test_run_ledger",
            )

    by_commit: dict[str, list[Mapping[str, Any]]] = {}
    for run in latest.values():
        by_commit.setdefault(str(run["commit"]), []).append(run)
    checkpoints: list[dict[str, Any]] = []
    selected_ids: list[str] = []
    evidence_details: list[dict[str, Any]] = []
    for commit, selected_runs in by_commit.items():
        components = [
            run for run in selected_runs if run["aggregate_role"] == "component"
        ]
        seen_cases: set[str] = set()
        for run in components:
            cases = {
                unicodedata.normalize("NFC", item) for item in run["test_case_ids"]
            }
            if seen_cases & cases:
                raise ProgramStatusPublishError(
                    "PROGRAM_STATUS_TEST_LEDGER_INVALID",
                    "Selected component test populations overlap.",
                    "repair_test_run_ledger",
                )
            seen_cases.update(cases)
        counts = {
            name: 0 for name in ("total", "passed", "failed", "skipped", "not_run")
        }
        categories: dict[str, dict[str, int] | None] = {
            name: None for name in ("unit", "integration", "e2e", "benchmark")
        }
        suite_sources: list[dict[str, Any]] = []
        for run in sorted(selected_runs, key=lambda item: str(item["run_key"])):
            selected_ids.append(str(run["run_id"]))
            references = []
            for index, evidence in enumerate(run["evidence"]):
                reference = {
                    "id": f"test:{run['run_id']}:{index + 1}",
                    "path": evidence["path"],
                    "sha256": evidence["sha256"],
                }
                references.append(reference)
                evidence_details.append(
                    {
                        **reference,
                        "label": f"Test run {run['run_id']}",
                        "summary": "Exact committed evidence for a canonical test run.",
                        "freshness": "current" if commit == current_commit else "stale",
                        "recovery": None,
                        "availability": "identity_only",
                        "exact_url": None,
                    }
                )
            projected = {
                key: run[key]
                for key in (
                    "suite_id",
                    "population_id",
                    "run_id",
                    "run_key",
                    "attempt",
                    "observed_at",
                    "terminal",
                    "aggregate_role",
                    "category",
                    "test_case_ids",
                    "test_case_set_sha256",
                    "counts",
                )
            }
            projected["evidence"] = references
            suite_sources.append(projected)
            if run["aggregate_role"] == "component":
                for name in counts:
                    counts[name] += run["counts"][name]
                category = str(run["category"])
                if categories[category] is None:
                    categories[category] = {name: 0 for name in counts}
                assert categories[category] is not None
                for name in counts:
                    categories[category][name] += run["counts"][name]
        denominator = counts["passed"] + counts["failed"]
        checkpoints.append(
            {
                "commit": commit,
                "observed_at": max(str(run["observed_at"]) for run in selected_runs),
                "counts": counts,
                "pass_rate": counts["passed"] / denominator if denominator else None,
                "categories": categories,
                "suite_sources": suite_sources,
            }
        )
    checkpoints.sort(key=lambda item: (item["observed_at"], item["commit"]))
    return checkpoints, sorted(selected_ids), evidence_details


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
        "specs/078-process-definition-view/contracts",
        "specs/079-wright-native-authoring/contracts",
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
) -> tuple[list[str], int, int, int, int, list[dict[str, Any]], list[str]]:
    registered: list[str] = []
    task_sources = subject["work_registry"].get("task_sources", [])
    if not isinstance(task_sources, list):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_WORK_REGISTRY_INVALID",
            "The work registry task_sources value must be an array.",
            "repair_work_registry",
        )
    source_feature_ids = [
        source.get("feature_id")
        for source in task_sources
        if isinstance(source, Mapping)
    ]
    source_paths = [
        source.get("tasks_path")
        for source in task_sources
        if isinstance(source, Mapping)
    ]
    roadmap_ids = [
        source.get("roadmap_item_id")
        for source in task_sources
        if isinstance(source, Mapping)
    ]
    if (
        len(source_feature_ids) != len(task_sources)
        or len(source_feature_ids) != len(set(source_feature_ids))
        or len(source_paths) != len(set(source_paths))
        or len(roadmap_ids) != len(set(roadmap_ids))
    ):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_WORK_REGISTRY_INVALID",
            "Task source feature, path, and roadmap identities must be present and unique.",
            "repair_work_registry",
        )
    active_sources = [
        source
        for source in task_sources
        if isinstance(source, Mapping) and source.get("active_feature") is True
    ]
    if len(active_sources) != 1 or active_sources[0].get("feature_id") != feature_id:
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_WORK_REGISTRY_INVALID",
            "Exactly one task source must match the current active feature.",
            "repair_work_registry",
        )
    program_completed = program_total = feature_completed = feature_total = 0
    task_records_by_feature: dict[str, dict[str, dict[str, Any]]] = {}
    task_raw_by_feature: dict[str, bytes] = {}
    for source in task_sources:
        if not isinstance(source, Mapping) or not isinstance(
            source.get("tasks_path"), str
        ):
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_WORK_REGISTRY_INVALID",
                "Every task source needs an exact tasks_path.",
                "repair_work_registry",
            )
        task_path = str(source["tasks_path"])
        task_raw = _git_blob(repository, str(subject["commit"]), task_path)
        records = _task_records(task_raw)
        completed = sum(1 for record in records.values() if record["completed"])
        total = len(records)
        source_feature = str(source["feature_id"])
        task_records_by_feature[source_feature] = records
        task_raw_by_feature[source_feature] = task_raw
        registered.append(task_path)
        program_completed += completed
        program_total += total
        if source.get("feature_id") == feature_id:
            feature_completed, feature_total = completed, total
    roadmap_path, _roadmap_raw, roadmap = _exact_catalog_json(subject, "roadmap")
    roadmap_items = roadmap.get("items")
    if not isinstance(roadmap_items, list):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_WORK_REGISTRY_INVALID",
            "The roadmap must expose its contracted items array.",
            "repair_work_registry",
        )
    roadmap_by_id = {
        str(item["id"]): item for item in roadmap_items if isinstance(item, Mapping)
    }
    if len(roadmap_by_id) != len(roadmap_items) or not set(roadmap_ids) <= set(
        roadmap_by_id
    ):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_WORK_REGISTRY_INVALID",
            "Every registered task source must bind one unique existing roadmap item.",
            "repair_work_registry",
        )
    undecomposed = [
        roadmap_id
        for roadmap_id, item in roadmap_by_id.items()
        if item.get("spec_kit_feature") is True and roadmap_id not in set(roadmap_ids)
    ]
    assignments_raw = subject["work_registry"].get("active_assignments")
    if not isinstance(assignments_raw, list):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_WORK_REGISTRY_INVALID",
            "The work registry active_assignments value must be an array.",
            "repair_work_registry",
        )
    assignment_agents = [
        item.get("agent_id") for item in assignments_raw if isinstance(item, Mapping)
    ]
    assignment_tasks = [
        (item.get("feature_id"), item.get("task_id"))
        for item in assignments_raw
        if isinstance(item, Mapping)
    ]
    if (
        len(assignment_agents) != len(assignments_raw)
        or len(assignment_agents) != len(set(assignment_agents))
        or len(assignment_tasks) != len(set(assignment_tasks))
    ):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_WORK_REGISTRY_INVALID",
            "Active assignment agent and feature-task identities must be unique.",
            "repair_work_registry",
        )
    lease = subject["state"].get("active_mutating_lease")
    projected_assignments: list[dict[str, Any]] = []
    for item in assignments_raw:
        assert isinstance(item, Mapping)
        assigned_feature = str(item["feature_id"])
        task_id = str(item["task_id"])
        record = task_records_by_feature.get(assigned_feature, {}).get(task_id)
        task_raw = task_raw_by_feature.get(assigned_feature)
        task_path = next(
            (
                str(source["tasks_path"])
                for source in task_sources
                if source.get("feature_id") == assigned_feature
            ),
            None,
        )
        if (
            record is None
            or task_raw is None
            or task_path is None
            or record["completed"]
            or item.get("task_title") != record["title"]
        ):
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_ASSIGNMENT_INVALID",
                "An active assignment must bind one exact incomplete registered task and title.",
                "repair_work_registry",
            )
        if assigned_feature == feature_id and (
            not isinstance(lease, Mapping)
            or item.get("branch") != lease.get("branch")
            or item.get("worktree_id") != lease.get("worktree_id")
        ):
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_ASSIGNMENT_INVALID",
                "The current-feature assignment must match the active lease branch and worktree.",
                "repair_work_registry",
            )
        matching_evidence = [
            evidence
            for evidence in item.get("evidence", [])
            if isinstance(evidence, Mapping)
            and evidence.get("path") == task_path
            and evidence.get("sha256") == _raw_digest(task_raw)
        ]
        if len(matching_evidence) != 1:
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_ASSIGNMENT_INVALID",
                "An active assignment needs exactly one matching committed task-source identity.",
                "repair_work_registry",
            )
        projected_assignments.append(
            {
                key: item.get(key)
                for key in (
                    "agent_id",
                    "feature_id",
                    "task_id",
                    "task_title",
                    "task_state",
                    "branch",
                    "worktree_id",
                    "lane",
                    "why_this_matters",
                    "observed_at",
                )
            }
            | {
                "evidence": [
                    _evidence(
                        f"assignment-{item['agent_id']}-{task_id}", task_path, task_raw
                    )
                ]
            }
        )
    return (
        registered,
        program_completed,
        program_total,
        feature_completed,
        feature_total,
        projected_assignments,
        undecomposed,
    )


def _task_records(raw: bytes) -> dict[str, dict[str, Any]]:
    text = raw.decode("utf-8")
    records: dict[str, dict[str, Any]] = {}
    for match in TASK_DETAIL_RE.finditer(text):
        task_id = match.group("id")
        if task_id in records:
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_WORK_REGISTRY_INVALID",
                f"Task identity {task_id} is duplicated.",
                "repair_registered_task_source",
            )
        records[task_id] = {
            "completed": match.group("done").lower() == "x",
            "title": match.group("title").strip(),
        }
    if not records:
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_WORK_REGISTRY_INVALID",
            "A registered task source contains no task identities.",
            "repair_registered_task_source",
        )
    return records


def _walk_subject_records(value: Any) -> list[Mapping[str, Any]]:
    records: list[Mapping[str, Any]] = []
    if isinstance(value, Mapping):
        records.append(value)
        for child in value.values():
            records.extend(_walk_subject_records(child))
    elif isinstance(value, list):
        for child in value:
            records.extend(_walk_subject_records(child))
    return records


def _record_subject_ids(record: Mapping[str, Any]) -> set[str]:
    identifiers: set[str] = set()
    for key, value in record.items():
        if isinstance(value, str) and (
            key == "id" or key.endswith("_id") or key in {"action", "task"}
        ):
            identifiers.add(value)
    return identifiers


def _resolved_verdict(record: Mapping[str, Any]) -> str | None:
    aliases = {
        "pass": "passed",
        "passed": "passed",
        "fail": "failed",
        "failed": "failed",
        "in_progress": "in_progress",
        "active": "in_progress",
        "skipped": "skipped",
        "not_run": "not_run",
        "inconclusive": "inconclusive",
    }
    for key in ("verdict", "result", "status", "state"):
        value = record.get(key)
        if isinstance(value, str) and value.lower() in aliases:
            return aliases[value.lower()]
    return None


def _resolve_use_case_subject(
    source_name: str, raw: bytes, subject_id: str
) -> Mapping[str, Any] | None:
    if source_name in {"customer_story_catalog", "feature_tasks"}:
        text = raw.decode("utf-8")
        if not re.search(
            rf"(?<![A-Za-z0-9_-]){re.escape(subject_id)}(?![A-Za-z0-9_-])", text
        ):
            return None
        if source_name == "feature_tasks":
            task = re.search(
                rf"^- \[(?P<done>[ xX])\] {re.escape(subject_id)}\b",
                text,
                re.MULTILINE,
            )
            return {
                "id": subject_id,
                "verdict": (
                    "passed"
                    if task is not None and task.group("done").lower() == "x"
                    else "in_progress"
                ),
            }
        return {"id": subject_id}
    try:
        value = _strict_json(raw, f"catalog source {source_name}")
    except ProgramStatusPublishError:
        return None
    matches = [
        record
        for record in _walk_subject_records(value)
        if subject_id in _record_subject_ids(record)
    ]
    if len(matches) != 1:
        return None
    return matches[0]


def _project_use_case_evidence(
    subject: Mapping[str, Any], use_case_id: str, stage_name: str, records: Any
) -> list[dict[str, Any]]:
    if not isinstance(records, list):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_USE_CASE_REGISTRY_INVALID",
            f"{use_case_id} {stage_name} evidence must be an array.",
            "repair_use_case_registry",
        )
    projected: list[dict[str, Any]] = []
    for index, evidence in enumerate(records):
        if not isinstance(evidence, Mapping):
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_USE_CASE_EVIDENCE_INVALID",
                f"{use_case_id} has a non-object {stage_name} evidence record.",
                "repair_use_case_registry",
            )
        source_name = evidence.get("source_name")
        path = evidence.get("path")
        expected_digest = evidence.get("sha256")
        candidates = subject.get("catalog_sources", {}).get(source_name, [])
        matching = [
            raw
            for candidate_path, raw in candidates
            if candidate_path == path and _raw_digest(raw) == expected_digest
        ]
        if len(matching) != 1:
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_USE_CASE_EVIDENCE_INVALID",
                f"{use_case_id} {stage_name} evidence is outside its exact catalog path or digest.",
                "repair_use_case_registry",
            )
        resolved = _resolve_use_case_subject(
            str(source_name), matching[0], str(evidence.get("subject_id", ""))
        )
        if resolved is None:
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_USE_CASE_EVIDENCE_INVALID",
                f"{use_case_id} {stage_name} subject does not resolve exactly once.",
                "repair_use_case_registry",
            )
        declared_verdict = str(evidence.get("verdict"))
        resolved_verdict = _resolved_verdict(resolved)
        if (
            declared_verdict not in {"not_applicable"}
            and resolved_verdict != declared_verdict
        ):
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_USE_CASE_EVIDENCE_INVALID",
                f"{use_case_id} {stage_name} verdict disagrees with its resolved subject.",
                "repair_use_case_registry",
            )
        for field in (
            "acceptance_subject_id",
            "evidence_author",
            "independent_verifier",
        ):
            resolved_value = resolved.get(field)
            if resolved_value is not None and resolved_value != evidence.get(field):
                raise ProgramStatusPublishError(
                    "PROGRAM_STATUS_USE_CASE_EVIDENCE_INVALID",
                    f"{use_case_id} {stage_name} {field} disagrees with its resolved subject.",
                    "repair_use_case_registry",
                )
        projected.append(
            {
                key: evidence.get(key)
                for key in (
                    "evidence_class",
                    "source_name",
                    "subject_id",
                    "verdict",
                    "acceptance_subject_id",
                    "evidence_author",
                    "independent_verifier",
                )
            }
            | {
                "evidence": _evidence(
                    f"use-case-{use_case_id}-{stage_name}-{index + 1}",
                    str(path),
                    matching[0],
                )
            }
        )
    return projected


def _derive_use_cases(
    subject: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[str], dict[str, dict[str, int]]]:
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
    projected_items: list[dict[str, Any]] = []
    all_implemented = all_verified = all_in_progress = all_not_started = 0
    process_defined = process_progress = process_implemented = 0
    process_tested = process_verified = process_qualified = 0
    for item in use_cases:
        assert isinstance(item, Mapping)
        use_case_id = str(item["id"])
        projected: dict[str, Any] = {
            key: item[key]
            for key in ("id", "title", "customer_outcome", "process_100_id")
        }
        evidence_identity_stages: dict[tuple[str, str, str], str] = {}
        for stage_name in (
            "definition_evidence",
            "progress_evidence",
            "acceptance_evidence",
            "test_evidence",
            "independent_verification_evidence",
            "benchmark_qualification_evidence",
        ):
            projected[stage_name] = _project_use_case_evidence(
                subject, use_case_id, stage_name, item.get(stage_name)
            )
            for evidence in projected[stage_name]:
                identity = (
                    str(evidence["source_name"]),
                    str(evidence["subject_id"]),
                    str(evidence["evidence"]["sha256"]),
                )
                previous = evidence_identity_stages.get(identity)
                if previous is not None and previous != stage_name:
                    raise ProgramStatusPublishError(
                        "PROGRAM_STATUS_USE_CASE_RELATION_INVALID",
                        f"{use_case_id} reuses one evidence identity across incompatible stages.",
                        "repair_use_case_registry",
                    )
                evidence_identity_stages[identity] = stage_name

        acceptance_ids = {
            str(record["subject_id"]) for record in projected["acceptance_evidence"]
        }
        for record in projected["independent_verification_evidence"]:
            if (
                record["acceptance_subject_id"] not in acceptance_ids
                or record["evidence_author"] == record["independent_verifier"]
            ):
                raise ProgramStatusPublishError(
                    "PROGRAM_STATUS_USE_CASE_RELATION_INVALID",
                    f"{use_case_id} independent verification is not bound and independent.",
                    "repair_use_case_registry",
                )
        for record in projected["benchmark_qualification_evidence"]:
            if (
                item.get("process_100_id") is None
                or record["subject_id"] != item.get("process_100_id")
                or record["acceptance_subject_id"] not in acceptance_ids
                or record["evidence_author"] == record["independent_verifier"]
            ):
                raise ProgramStatusPublishError(
                    "PROGRAM_STATUS_USE_CASE_RELATION_INVALID",
                    f"{use_case_id} benchmark qualification lacks its exact process and acceptance binding.",
                    "repair_use_case_registry",
                )

        implemented = bool(projected["acceptance_evidence"])
        verified = bool(projected["independent_verification_evidence"])
        in_progress = not implemented and bool(projected["progress_evidence"])
        all_implemented += int(implemented)
        all_verified += int(verified)
        all_in_progress += int(in_progress)
        all_not_started += int(not implemented and not in_progress)
        if item.get("process_100_id") is not None:
            process_defined += int(bool(projected["definition_evidence"]))
            process_progress += int(in_progress)
            process_implemented += int(implemented)
            process_tested += int(
                any(
                    record["verdict"] == "passed"
                    for record in projected["test_evidence"]
                )
            )
            process_verified += int(verified)
            process_qualified += int(
                bool(projected["benchmark_qualification_evidence"])
            )
        projected_items.append(projected)

    dashboard_qualified = int(subject["dashboard"]["benchmark_summary"]["counted"])
    if process_qualified != dashboard_qualified:
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_USE_CASE_RELATION_INVALID",
            "Per-process qualification evidence disagrees with the authoritative dashboard.",
            "repair_use_case_registry",
        )
    funnels = {
        "all": {
            "total": len(use_cases),
            "not_started": all_not_started,
            "in_progress": all_in_progress,
            "implemented": all_implemented,
            "independently_verified": all_verified,
            "remaining": len(use_cases) - all_implemented,
        },
        "process_100": {
            "population_target": 100,
            "defined": process_defined,
            "in_progress": process_progress,
            "implemented": process_implemented,
            "tested": process_tested,
            "independently_verified": process_verified,
            "benchmark_qualified": process_qualified,
        },
    }
    return projected_items, process_ids, funnels


def _exact_catalog_json(
    subject: Mapping[str, Any], source_name: str
) -> tuple[str, bytes, Mapping[str, Any]]:
    records = subject.get("catalog_sources", {}).get(source_name, [])
    if not isinstance(records, list) or len(records) != 1:
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_GOVERNANCE_SOURCE_INVALID",
            f"Governance source {source_name} must resolve to one exact record.",
            "repair_frozen_source_catalog",
        )
    path, raw = records[0]
    value = _strict_json(raw, path)
    return path, raw, value


def _overdue(due_at: Any, status: str, observed_at: str) -> bool:
    if not isinstance(due_at, str) or status in {"decided", "closed", "resolved"}:
        return False
    try:
        due = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
        observed = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_GOVERNANCE_SOURCE_INVALID",
            "A governance due date is not an ISO-8601 timestamp.",
            "repair_governance_register",
        ) from exc
    return due < observed


def _project_governance_registers(
    subject: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    risk_path, risk_raw, risk_register = _exact_catalog_json(subject, "risk_register")
    decision_path, decision_raw, decision_register = _exact_catalog_json(
        subject, "decision_register"
    )
    risks_raw = risk_register.get("risks")
    decisions_raw = decision_register.get("records")
    if not isinstance(risks_raw, list) or not isinstance(decisions_raw, list):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_GOVERNANCE_SOURCE_INVALID",
            "Risk and decision registers must expose their contracted arrays.",
            "repair_governance_register",
        )
    observed_at = str(subject["generated_at"])
    risk_ref = _evidence("risk-register", risk_path, risk_raw)
    decision_ref = _evidence("decision-register", decision_path, decision_raw)
    risks: list[dict[str, Any]] = []
    for item in risks_raw:
        if not isinstance(item, Mapping):
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_GOVERNANCE_SOURCE_INVALID",
                "Every risk must be an object.",
                "repair_governance_register",
            )
        status = str(item["status"])
        priority = str(item["priority"])
        risks.append(
            {
                "id": str(item["id"]),
                "severity": priority
                if priority in {"P0", "P1", "P2", "P3"}
                else "unknown",
                "status": status,
                "owner": item.get("owner_role"),
                "overdue": _overdue(
                    (item.get("review") or {}).get("due_at"), status, observed_at
                ),
                "blocks": priority == "P0" and status == "open",
                "summary": str(item["title"]),
                "evidence": [risk_ref],
            }
        )
    decisions: list[dict[str, Any]] = []
    for item in decisions_raw:
        if not isinstance(item, Mapping):
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_GOVERNANCE_SOURCE_INVALID",
                "Every decision must be an object.",
                "repair_governance_register",
            )
        status = str(item["status"])
        blocks = item.get("blocks")
        decisions.append(
            {
                "id": str(item["id"]),
                "status": status,
                "owner": item.get("owner_role"),
                "overdue": _overdue(
                    (item.get("due") or {}).get("due_at"), status, observed_at
                ),
                "blocks": status == "open"
                and isinstance(blocks, list)
                and bool(blocks),
                "summary": str(item["question"]),
                "evidence": [decision_ref],
            }
        )
    if len({item["id"] for item in risks}) != len(risks) or len(
        {item["id"] for item in decisions}
    ) != len(decisions):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_GOVERNANCE_SOURCE_INVALID",
            "Risk and decision identities must be unique within each register.",
            "repair_governance_register",
        )
    return risks, decisions


def _checkout_evidence_detail(
    reference: Mapping[str, Any], label: str, summary: str
) -> dict[str, Any]:
    return {
        **reference,
        "label": label,
        "summary": summary,
        "freshness": "current",
        "recovery": None,
        "availability": "checkout_available",
        "exact_url": None,
    }


def _validate_evidence_details(bundle: Mapping[str, Any]) -> None:
    source_commit = str(bundle["source"]["commit"])
    details = bundle["supplement"]["evidence_index"]
    for detail in details:
        path = str(detail["path"])
        if not re.fullmatch(
            r"[A-Za-z0-9_-][A-Za-z0-9._-]*(?:/[A-Za-z0-9_-][A-Za-z0-9._-]*)*",
            path,
        ) or any(segment in {"", ".", ".."} for segment in path.split("/")):
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_EVIDENCE_PATH_INVALID",
                "An evidence detail path is not canonical.",
                "repair_evidence_index",
            )
        exact_url = detail.get("exact_url")
        if exact_url is None:
            if detail.get("availability") == "exact_github":
                raise ProgramStatusPublishError(
                    "PROGRAM_STATUS_EVIDENCE_URL_INVALID",
                    "Exact-GitHub evidence has no exact URL.",
                    "repair_evidence_index",
                )
            continue
        parsed = urlsplit(str(exact_url))
        expected_path = f"/burhop/wright/blob/{source_commit}/{path}"
        if (
            parsed.scheme != "https"
            or parsed.netloc != "github.com"
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port is not None
            or parsed.query
            or parsed.fragment
            or parsed.path != expected_path
            or detail.get("availability") != "exact_github"
        ):
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_EVIDENCE_URL_INVALID",
                "An evidence URL is not the exact Wright commit/path URL.",
                "repair_evidence_index",
            )


def _project_correction_graph(
    subject: Mapping[str, Any],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    corrections_raw = subject.get("catalog_sources", {}).get("correction_evidence", [])
    verifications_raw = subject.get("catalog_sources", {}).get(
        "verification_evidence", []
    )
    approvals_raw = subject.get("catalog_sources", {}).get("approval_evidence", [])
    if not all(
        isinstance(records, list)
        for records in (corrections_raw, verifications_raw, approvals_raw)
    ):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_GOVERNANCE_SOURCE_INVALID",
            "Correction, verification, and approval sources must be closed collections.",
            "repair_governance_evidence",
        )
    verifications_by_path: list[tuple[str, bytes, Mapping[str, Any]]] = [
        (path, raw, _strict_json(raw, path)) for path, raw in verifications_raw
    ]
    approvals_by_path: dict[str, tuple[bytes, Mapping[str, Any]]] = {
        path: (raw, _strict_json(raw, path)) for path, raw in approvals_raw
    }
    corrections: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    verifications: list[dict[str, Any]] = []
    details: dict[str, dict[str, Any]] = {}
    for correction_path, correction_raw in corrections_raw:
        correction = _strict_json(correction_raw, correction_path)
        correction_id = correction.get("correction_id")
        if not isinstance(correction_id, str):
            continue
        matches: list[tuple[str, bytes, Mapping[str, Any]]] = []
        for verification_path, verification_raw, verification in verifications_by_path:
            artifact_digests = (verification.get("subject") or {}).get(
                "artifact_digests", []
            )
            if (
                verification.get("kind") == "independent"
                and (verification.get("actor") or {}).get("independent") is True
                and any(
                    isinstance(artifact, Mapping)
                    and artifact.get("path") == correction_path
                    for artifact in artifact_digests
                )
            ):
                matches.append((verification_path, verification_raw, verification))
        if not matches:
            continue
        if len(matches) != 1:
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_GOVERNANCE_RELATION_INVALID",
                f"{correction_id} has an ambiguous independent verification relation.",
                "repair_governance_evidence",
            )
        verification_path, verification_raw, verification = matches[0]
        verification_id = verification.get("evidence_id")
        actor = verification.get("actor")
        if not isinstance(verification_id, str) or not isinstance(actor, Mapping):
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_GOVERNANCE_RELATION_INVALID",
                f"{correction_id} verification lacks its exact identity or actor.",
                "repair_governance_evidence",
            )
        authority = correction.get("authority")
        approval_paths = (
            authority.get("proposed_approval_records", [])
            if isinstance(authority, Mapping)
            else []
        )
        selected_approvals: list[tuple[str, bytes, Mapping[str, Any]]] = []
        for approval_path in approval_paths:
            selected = approvals_by_path.get(str(approval_path))
            if selected is not None:
                selected_approvals.append((str(approval_path), *selected))
        if not selected_approvals or any(
            not str(approval.get("decision", "")).startswith("approved")
            for _path, _raw, approval in selected_approvals
        ):
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_GOVERNANCE_RELATION_INVALID",
                f"{correction_id} lacks its exact approved authority record.",
                "repair_governance_evidence",
            )
        approval_path, approval_raw, approval = selected_approvals[0]
        approval_id = approval.get("approval_id")
        approver = approval.get("approver")
        verifier = actor.get("identity")
        if (
            not isinstance(approval_id, str)
            or not isinstance(approver, str)
            or not isinstance(verifier, str)
            or approver == verifier
        ):
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_GOVERNANCE_RELATION_INVALID",
                f"{correction_id} authority and verifier identities are not independent.",
                "repair_governance_evidence",
            )
        claims = correction.get("claims")
        if not isinstance(claims, list) or not claims:
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_GOVERNANCE_RELATION_INVALID",
                f"{correction_id} has no bounded claim population.",
                "repair_governance_evidence",
            )
        claim_ids = [
            claim.get("claim_id") for claim in claims if isinstance(claim, Mapping)
        ]
        if (
            len(claim_ids) != len(claims)
            or len(claim_ids) != len(set(claim_ids))
            or not all(isinstance(claim_id, str) for claim_id in claim_ids)
        ):
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_GOVERNANCE_RELATION_INVALID",
                f"{correction_id} claim identities must be present and unique.",
                "repair_governance_evidence",
            )
        correction_ref = _evidence(
            f"correction-{correction_id}", correction_path, correction_raw
        )
        verification_ref = _evidence(
            f"verification-{verification_id}", verification_path, verification_raw
        )
        approval_ref = _evidence(f"approval-{approval_id}", approval_path, approval_raw)
        for reference, label, summary in (
            (
                correction_ref,
                correction_id,
                "Exact committed bounded correction profile.",
            ),
            (
                verification_ref,
                verification_id,
                "Exact committed independent verification record.",
            ),
            (approval_ref, approval_id, "Exact committed human approval record."),
        ):
            detail = _checkout_evidence_detail(reference, label, summary)
            previous = details.get(str(reference["id"]))
            if previous is not None and previous != detail:
                raise ProgramStatusPublishError(
                    "PROGRAM_STATUS_EVIDENCE_ID_COLLISION",
                    f"Governance evidence ID {reference['id']} is not unique.",
                    "repair_governance_evidence",
                )
            details[str(reference["id"])] = detail
        verified_at = verification.get("created_at")
        verdict = str(verification.get("verdict"))
        if not isinstance(verified_at, str) or verdict not in {
            "passed",
            "failed",
            "inconclusive",
        }:
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_GOVERNANCE_RELATION_INVALID",
                f"{verification_id} lacks a supported verdict or timestamp.",
                "repair_governance_evidence",
            )
        subject_commit = (verification.get("subject") or {}).get("git_commit")
        verification_subject = (
            f"git:{subject_commit}"
            if isinstance(subject_commit, str)
            else str(correction.get("stable_cause_id", correction_id))
        )
        claim_id_strings = [str(claim_id) for claim_id in claim_ids]
        corrections.append(
            {
                "profile_id": correction_id,
                "path": correction_path,
                "digest": _raw_digest(correction_raw),
                "correction_class": str(
                    correction.get("stable_cause_id", "bounded_correction")
                ),
                "authority_status": "approved",
                "approval_id": approval_id,
                "expected_claim_ids": claim_id_strings,
                "verified_claim_ids": claim_id_strings if verdict == "passed" else [],
                "finding_ids": claim_id_strings,
                "resolved_finding_ids": (
                    claim_id_strings if verdict == "passed" else []
                ),
                "unresolved_finding_ids": (
                    [] if verdict == "passed" else claim_id_strings
                ),
                "verification_ids": [verification_id],
                "verification_subject": verification_subject,
                "verified_at": verified_at,
                "evidence": [correction_ref, verification_ref, approval_ref],
            }
        )
        for claim in claims:
            assert isinstance(claim, Mapping)
            claim_id = str(claim["claim_id"])
            findings.append(
                {
                    "id": claim_id,
                    "status": "resolved" if verdict == "passed" else "open",
                    "severity": "P0",
                    "summary": str(
                        claim.get("classification", "Bounded correction claim")
                    ).replace("_", " "),
                    "blocking": verdict != "passed",
                    "opened_at": None,
                    "resolved_at": verified_at if verdict == "passed" else None,
                    "correction_profile_id": (
                        correction_id if verdict == "passed" else None
                    ),
                    "resolution_verification_id": (
                        verification_id if verdict == "passed" else None
                    ),
                    "recovery": (
                        None
                        if verdict == "passed"
                        else "Repair the exact bounded claim and re-verify independently."
                    ),
                    "evidence": [correction_ref, verification_ref],
                }
            )
        verifications.append(
            {
                "id": verification_id,
                "author": approver,
                "verifier": verifier,
                "independent": True,
                "subject": verification_subject,
                "verdict": verdict,
                "blocking": verdict != "passed",
                "finding_ids": claim_id_strings,
                "correction_profile_ids": [correction_id],
                "verified_at": verified_at,
                "evidence": [verification_ref, correction_ref, approval_ref],
            }
        )
    correction_ids = [item["profile_id"] for item in corrections]
    finding_ids = [item["id"] for item in findings]
    verification_ids = [item["id"] for item in verifications]
    if any(
        len(values) != len(set(values))
        for values in (correction_ids, finding_ids, verification_ids)
    ):
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_GOVERNANCE_RELATION_INVALID",
            "Projected correction, finding, and verification identities must be unique.",
            "repair_governance_evidence",
        )
    return (
        corrections,
        findings,
        verifications,
        [details[key] for key in sorted(details)],
    )


def _project_delivery_lanes(
    subject: Mapping[str, Any],
    state_ref: dict[str, str],
    feature_tasks_ref: dict[str, str],
    feature_done: int,
    feature_total: int,
    customer_capability_evidence: list[dict[str, str]] | None = None,
    accepted_use_cases: int = 0,
    verified_use_cases: int = 0,
) -> tuple[dict[str, Any], dict[str, Any]]:
    state = subject["state"]
    lease = state.get("active_mutating_lease")
    roadmap_path, roadmap_raw, roadmap = _exact_catalog_json(subject, "roadmap")
    roadmap_ref = _evidence("roadmap", roadmap_path, roadmap_raw)
    roadmap_by_id = {
        str(item["id"]): item
        for item in roadmap.get("items", [])
        if isinstance(item, Mapping)
    }
    current_feature = str(state.get("current_feature") or "")
    current_item = roadmap_by_id.get(current_feature)
    if current_item is None:
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_LANE_SOURCE_INVALID",
            "The current feature has no exact roadmap item.",
            "repair_delivery_lane_sources",
        )

    delivery_states = {
        "AUTHOR_VERIFIED": "local gate",
        "CANDIDATE_FROZEN": "local gate",
        "INDEPENDENTLY_VERIFIED": "local gate",
        "PUSH_AUTHORIZATION_PENDING": "local gate",
        "PR_READY": "PR open",
        "DEV_MERGE_READY": "merge ready",
        "DEV_INTEGRATED": "merged",
        "DEV_DEPLOYMENT_VERIFIED": "dev deployment verified",
    }
    transition_records: list[tuple[int, str, bytes, Mapping[str, Any]]] = []
    for path, raw in subject["catalog_sources"].get("transition_evidence", []):
        transition = _strict_json(raw, path)
        if (
            transition.get("feature_id") == "EPP-F01"
            and transition.get("to_state") in delivery_states
        ):
            transition_records.append(
                (int(transition["new_revision"]), path, raw, transition)
            )
    transition_records.sort(key=lambda item: item[0])
    if not transition_records:
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_LANE_SOURCE_INVALID",
            "No catalog-admitted EPP-F01 delivery transition exists.",
            "repair_delivery_lane_sources",
        )
    last_revision = 0
    events: list[dict[str, Any]] = []
    pull_requests: set[tuple[int, str]] = set()
    merged_dev: str | None = None
    for revision, path, raw, transition in transition_records:
        if revision <= last_revision:
            raise ProgramStatusPublishError(
                "PROGRAM_STATUS_LANE_SOURCE_INVALID",
                "Delivery transitions are not in strict revision order.",
                "repair_delivery_lane_sources",
            )
        last_revision = revision
        reference = _evidence(f"lane-{transition['transition_id']}", path, raw)
        events.append(
            {
                "kind": str(transition["to_state"]),
                "commit": str(transition["git"]["source_commit"]),
                "observed_at": str(transition["finished_at"]),
                "result": str(transition["action"])[:300],
                "evidence": [reference],
            }
        )
        for check in transition.get("checks", []):
            if not isinstance(check, Mapping):
                continue
            for value in check.get("evidence", []):
                if not isinstance(value, str):
                    continue
                pull_match = re.fullmatch(
                    r"https://github\.com/burhop/wright/pull/([1-9][0-9]*)", value
                )
                if pull_match:
                    pull_requests.add((int(pull_match.group(1)), value))
                merged_match = re.fullmatch(r"merged_dev:([0-9a-f]{40})", value)
                if merged_match:
                    merged_dev = merged_match.group(1)
    if len(pull_requests) > 1:
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_LANE_SOURCE_INVALID",
            "Delivery transitions disagree on pull-request identity.",
            "repair_delivery_lane_sources",
        )
    last_transition = transition_records[-1][3]
    last_event = events[-1]
    pr_number, pr_url = next(iter(pull_requests)) if pull_requests else (None, None)
    integration_item = roadmap_by_id.get("EPP-F01")
    if integration_item is None:
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_LANE_SOURCE_INVALID",
            "The integrated feature has no roadmap item.",
            "repair_delivery_lane_sources",
        )
    integration = {
        "kind": "integration",
        "branch": "unavailable",
        "milestone": str(integration_item["title"]),
        "latest_capability": (
            "Verified integration evidence: " + str(last_event["result"])
        )[:500],
        "blocker": None,
        "next_action": _action(
            "INTEGRATION_COMPLETE",
            "No integration action is required; EPP-F01 is deployed to dev.",
            "lane_next_action",
            last_event["evidence"],
            authority_override="not_required",
        ),
        "observed_at": str(last_transition["finished_at"]),
        "evidence": [roadmap_ref, *last_event["evidence"]],
        "target_branch": str(state["baseline"]["ref"]),
        "frozen_candidate": None,
        "last_pushed_commit": None,
        "last_pushed_at": None,
        "pull_request": (
            {"number": pr_number, "url": pr_url} if pr_number and pr_url else None
        ),
        "phase": delivery_states[str(last_transition["to_state"])],
        "checks": None,
        "ci_started_at": None,
        "first_actionable_failure": None,
        "dev_sync": f"merged to {merged_dev}" if merged_dev else None,
        "merge_gate": (
            "passed historically"
            if last_transition.get("classification") == "passed"
            else None
        ),
        "authority_state": "not_required",
        "events": events,
    }

    next_action_record = (state.get("next_eligible_actions") or [{}])[0]
    action_id = str(next_action_record.get("action", "NO_ELIGIBLE_ACTION"))
    action_reason = str(
        next_action_record.get(
            "reason", "No committed next-action reason is available."
        )
    )
    requires_approval = bool(next_action_record.get("requires_human_approval", False))
    if isinstance(lease, Mapping):
        branch = str(lease["branch"])
        base_commit = str(lease["dev_baseline"]["commit"])
        authority_state = "authorized"
        blocker = None
    else:
        branch = "unavailable"
        base_commit = str(state["baseline"]["commit"])
        authority_state = "not_authorized" if requires_approval else "unavailable"
        blocker = action_reason
    capability_evidence = customer_capability_evidence or []
    latest_capability = (
        (
            "Committed customer acceptance evidence: "
            f"{accepted_use_cases} accepted and {verified_use_cases} independently "
            f"verified {current_feature} use case; benchmark qualification remains "
            "independent."
        )
        if accepted_use_cases
        else (
            "Unavailable: no committed customer acceptance evidence demonstrates "
            f"a customer-visible {current_feature} capability yet."
        )
    )
    development = {
        "kind": "continued_development",
        "branch": branch,
        "milestone": str(current_item["title"]),
        "latest_capability": latest_capability,
        "blocker": blocker,
        "next_action": _action(
            action_id,
            action_reason,
            "lane_next_action",
            [state_ref],
            eligible=isinstance(lease, Mapping) and not requires_approval,
            blocker=action_reason,
            requires_human_approval=requires_approval,
        ),
        "observed_at": str(subject["generated_at"]),
        "evidence": [
            state_ref,
            roadmap_ref,
            feature_tasks_ref,
            *capability_evidence,
        ],
        "base_commit": base_commit,
        "authority_state": authority_state,
    }
    return integration, development


def _milestone_scope_identity(
    repository: Path, commit: str, paths: list[str]
) -> tuple[str, bool]:
    """Cover exact blobs/trees, including absence, without working-tree timestamps."""
    rows = []
    for path in sorted(set(paths)):
        if not re.fullmatch(
            r"(?:apps|packages|scripts|tests|src|specs|docs|docker)(?:/[A-Za-z0-9_.-]+)*",
            path,
        ) or any(part in {".", "..", ""} for part in path.split("/")):
            raise ValueError("unsafe milestone coverage path")
        raw = _git(repository, "ls-tree", commit, "--", path)
        rows.append([path, str(raw).strip() or "missing"])
    return _digest(rows), bool(rows) and all(row[1] != "missing" for row in rows)


def _milestone_scope_digest(repository: Path, commit: str, paths: list[str]) -> str:
    return _milestone_scope_identity(repository, commit, paths)[0]


def _project_native_milestone(
    repository: Path, subject: Mapping[str, Any]
) -> dict[str, Any] | None:
    source = subject["work_registry"].get("milestone")
    if source is None:
        return None
    if source["feature_id"] != subject["state"]["current_feature"]:
        raise ValueError("native milestone is not the active feature")
    commit = str(subject["commit"])
    checks = {row["id"]: row for row in source["checks"]}
    attestations = []
    for evidence in source["evidence"]:
        paths = checks[evidence["check_id"]]["source_paths"]
        tested = evidence["tested_commit"]
        tree = str(_git(repository, "rev-parse", f"{tested}^{{tree}}")).strip()
        tested_scope, tested_available = _milestone_scope_identity(
            repository, tested, paths
        )
        current_scope, current_available = _milestone_scope_identity(
            repository, commit, paths
        )
        artifacts_match = True
        for artifact in evidence["artifacts"]:
            mode = str(
                _git(repository, "ls-tree", artifact["commit"], "--", artifact["path"])
            )
            artifacts_match = artifacts_match and mode.startswith(
                ("100644 blob ", "100755 blob ")
            )
            artifacts_match = (
                artifacts_match
                and _raw_digest(
                    _git_blob(repository, artifact["commit"], artifact["path"])
                )
                == artifact["sha256"]
            )
        attestations.append(
            {
                "evidence_id": evidence["id"],
                "tested_scope_sha256": tested_scope,
                "current_scope_sha256": current_scope,
                "coverage_available": tested_available and current_available,
                "commit_tree_matches": tree == evidence["tested_tree"],
                "artifacts_match": artifacts_match,
            }
        )
    # Integration requires a real merge object on the recorded dev baseline and
    # a recorded PR head which is a parent of that merge. Deployment has its own check.
    delivery = source["delivery"]
    merged = delivery["merged_commit"]
    delivery_attested = False
    if merged and delivery["pull_requests"]:
        baseline = str(subject["state"]["baseline"]["commit"])
        parents = str(_git(repository, "show", "-s", "--format=%P", merged)).split()
        ancestor = (
            subprocess.run(
                ["git", "merge-base", "--is-ancestor", merged, baseline],
                cwd=repository,
                capture_output=True,
            ).returncode
            == 0
        )
        delivery_attested = (
            ancestor
            and len(parents) > 1
            and any(pr["head_commit"] in parents for pr in delivery["pull_requests"])
        )
        integrated_checks = [
            row for row in checks.values() if row["stage"] == "integration"
        ]
        delivery_attested = delivery_attested and bool(integrated_checks)
        for check in integrated_checks:
            merged_scope, merged_available = _milestone_scope_identity(
                repository, merged, check["source_paths"]
            )
            current_scope, current_available = _milestone_scope_identity(
                repository, commit, check["source_paths"]
            )
            delivery_attested = (
                delivery_attested
                and merged_available
                and current_available
                and merged_scope == current_scope
            )
    module_path = (
        repository / "packages/tool_registry/src/tool_registry/milestone_status.py"
    )
    spec = importlib.util.spec_from_file_location(
        "_wright_milestone_projection", module_path
    )
    if spec is None or spec.loader is None:
        raise ValueError("native milestone projection module is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.derive_milestone(
        source,
        _task_records(_git_blob(repository, commit, source["tasks_path"])),
        source_commit=commit,
        observed_at=str(subject["generated_at"]),
        attestations=attestations,
        delivery_attested=delivery_attested,
    )


def _build_supplement(repository: Path, subject: Mapping[str, Any]) -> dict[str, Any]:
    blobs = subject["blobs"]
    native_milestone = _project_native_milestone(repository, subject)
    state = subject["state"]
    lifecycle = subject["lifecycle"]
    feature_id = str(state.get("current_feature") or "EPP-F02")
    state_ref = _evidence("program-state", STATE_PATH, blobs[STATE_PATH])
    dashboard_ref = _evidence("dashboard", DASHBOARD_PATH, blobs[DASHBOARD_PATH])
    (
        registered,
        program_done,
        program_total,
        feature_done,
        feature_total,
        active_assignments,
        undecomposed_roadmap_items,
    ) = _registered_task_counts(repository, subject, feature_id)
    use_case_items, _process_ids, use_case_funnels = _derive_use_cases(subject)
    customer_capability_evidence = [
        record["evidence"]
        for item in use_case_items
        for record in item["acceptance_evidence"]
    ]
    use_case_evidence_details: dict[str, dict[str, Any]] = {}
    for item in use_case_items:
        for stage_name in (
            "definition_evidence",
            "progress_evidence",
            "acceptance_evidence",
            "test_evidence",
            "independent_verification_evidence",
            "benchmark_qualification_evidence",
        ):
            for record in item[stage_name]:
                reference = record["evidence"]
                detail = _checkout_evidence_detail(
                    reference,
                    f"{item['id']} {stage_name.replace('_', ' ')}",
                    "Exact committed evidence for one governed use-case stage.",
                )
                previous = use_case_evidence_details.get(str(reference["id"]))
                if previous is not None and previous != detail:
                    raise ProgramStatusPublishError(
                        "PROGRAM_STATUS_EVIDENCE_ID_COLLISION",
                        f"Use-case evidence ID {reference['id']} is not unique.",
                        "repair_use_case_evidence_identity",
                    )
                use_case_evidence_details[str(reference["id"])] = detail
    risks, decisions = _project_governance_registers(subject)
    corrections, findings, verifications, governance_evidence_details = (
        _project_correction_graph(subject)
    )
    story_maturity = _customer_story_maturity(blobs[CUSTOMER_CATALOG_PATH])
    ledger = subject["ledger"]
    prior_ledger_runs_sha256 = _verify_test_ledger_append_only(repository, subject)
    test_checkpoints, selected_run_ids, test_evidence_details = _project_test_history(
        ledger, str(subject["commit"])
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
    active_task_source = next(
        source
        for source in subject["work_registry"]["task_sources"]
        if source.get("active_feature") is True
    )
    feature_tasks_path = str(active_task_source["tasks_path"])
    feature_tasks_ref = _evidence(
        "active-feature-tasks",
        feature_tasks_path,
        _git_blob(repository, str(subject["commit"]), feature_tasks_path),
    )
    integration_lane, development_lane = _project_delivery_lanes(
        subject,
        state_ref,
        feature_tasks_ref,
        feature_done,
        feature_total,
        customer_capability_evidence,
        int(use_case_funnels["all"]["implemented"]),
        int(use_case_funnels["all"]["independently_verified"]),
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
        "specs/078-process-definition-view/tasks.md",
    )
    history_by_id["feature_tasks"] = _observations_for_path(
        repository,
        str(subject["commit"]),
        feature_task_path,
        _task_counts,
        "feature_tasks",
        "feature_task",
    )
    program_task_evidence = [
        _evidence(
            f"program-task-source:{index}",
            path,
            _git_blob(repository, str(subject["commit"]), path),
        )
        for index, path in enumerate(registered, start=1)
    ]
    history_by_id["program_tasks"] = [
        {
            "commit": str(subject["commit"]),
            "transition_id": None,
            "parent_commit": None,
            "observed_at": str(subject["generated_at"]),
            "value": program_done,
            "denominator": program_total,
            "label": "program_tasks",
            "source_classification": "program_task",
            "change_reason": "Current closed registered task-source checkpoint",
            "evidence": program_task_evidence,
        }
    ]
    history_by_id["integration_delivery"] = [
        {
            "commit": event["commit"],
            "transition_id": event["evidence"][0]["id"].removeprefix("lane-"),
            "parent_commit": (
                integration_lane["events"][index - 1]["commit"] if index else None
            ),
            "observed_at": event["observed_at"],
            "value": index + 1,
            "denominator": len(integration_lane["events"]),
            "label": "integration_delivery",
            "source_classification": "integration_gate",
            "change_reason": event["result"],
            "evidence": event["evidence"],
        }
        for index, event in enumerate(integration_lane["events"])
    ]
    if test_checkpoints:
        history_by_id["quality"] = [
            {
                "commit": checkpoint["commit"],
                "transition_id": None,
                "parent_commit": None,
                "observed_at": checkpoint["observed_at"],
                "label": "quality",
                "value": checkpoint["counts"]["passed"],
                "denominator": (
                    checkpoint["counts"]["passed"] + checkpoint["counts"]["failed"]
                ),
                "source_classification": "test_evidence",
                "change_reason": "Canonical committed test checkpoint",
                "evidence": [
                    reference
                    for source in checkpoint["suite_sources"]
                    for reference in source["evidence"]
                ],
            }
            for checkpoint in test_checkpoints
        ]
    historical_evidence: dict[str, dict[str, Any]] = {}
    selected_test_evidence = {item["id"]: item for item in test_evidence_details}
    for observations in history_by_id.values():
        for observation in observations:
            for reference in observation["evidence"]:
                selected_test_detail = selected_test_evidence.get(reference["id"])
                if selected_test_detail is not None:
                    if any(
                        selected_test_detail[key] != reference[key]
                        for key in ("id", "path", "sha256")
                    ):
                        raise ProgramStatusPublishError(
                            "PROGRAM_STATUS_EVIDENCE_ID_COLLISION",
                            f"Test history evidence ID {reference['id']} does not match its selected suite source.",
                            "repair_history_evidence_identity",
                        )
                    continue
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
    roadmap_path, roadmap_raw, roadmap = _exact_catalog_json(subject, "roadmap")
    roadmap_ref = _evidence("roadmap", roadmap_path, roadmap_raw)
    benchmark_path, benchmark_raw, _benchmark = _exact_catalog_json(
        subject, "benchmark_coverage"
    )
    benchmark_ref = _evidence("benchmark-coverage", benchmark_path, benchmark_raw)
    roadmap_by_id = {
        str(item["id"]): item
        for item in roadmap.get("items", [])
        if isinstance(item, Mapping)
    }
    benchmark_dependency_ids = sorted(
        {
            str(dependency)
            for item in roadmap_by_id.values()
            if item.get("kind") == "benchmark"
            for dependency in item.get("depends_on", [])
        }
    )
    status_projection = {
        "complete": "satisfied",
        "active": "pending",
        "proposed": "pending",
        "blocked": "blocked",
    }
    benchmark_dependencies = []
    for dependency_id in benchmark_dependency_ids:
        item = roadmap_by_id.get(dependency_id)
        status = (
            status_projection.get(str(item.get("status")), "unavailable")
            if item is not None
            else "unavailable"
        )
        benchmark_dependencies.append(
            {
                "id": dependency_id,
                "label": (
                    str(item.get("title"))
                    if item is not None
                    else f"Unavailable roadmap dependency {dependency_id}"
                ),
                "status": status,
                "blocking": status != "satisfied",
                "evidence": [roadmap_ref],
            }
        )
    pending_dependency_ids = [
        item["id"] for item in benchmark_dependencies if item["blocking"]
    ]
    benchmark_blocker = (
        "Benchmark execution is not authorized and remains at 0/100; roadmap "
        "dependencies still pending: " + ", ".join(pending_dependency_ids) + "."
    )
    lease = state.get("active_mutating_lease")
    policy_limits = lifecycle.get("wip_limits", {})
    risk_path, risk_raw = subject["catalog_sources"]["risk_register"][0]
    decision_path, decision_raw = subject["catalog_sources"]["decision_register"][0]
    evidence_pairs = (
        ("dashboard", DASHBOARD_PATH, blobs[DASHBOARD_PATH]),
        ("program-state", STATE_PATH, blobs[STATE_PATH]),
        ("source-catalog", SOURCE_CATALOG_PATH, blobs[SOURCE_CATALOG_PATH]),
        ("roadmap", roadmap_path, roadmap_raw),
        ("benchmark-coverage", benchmark_path, benchmark_raw),
        ("work-registry", WORK_REGISTRY_PATH, blobs[WORK_REGISTRY_PATH]),
        (
            "active-feature-tasks",
            feature_tasks_path,
            _git_blob(repository, str(subject["commit"]), feature_tasks_path),
        ),
        ("use-case-registry", USE_CASE_REGISTRY_PATH, blobs[USE_CASE_REGISTRY_PATH]),
        ("test-run-ledger", TEST_LEDGER_PATH, blobs[TEST_LEDGER_PATH]),
        ("risk-register", risk_path, risk_raw),
        ("decision-register", decision_path, decision_raw),
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
            "all": use_case_funnels["all"],
            "process_100": use_case_funnels["process_100"],
            "items": use_case_items,
            "graph_context": graph_context,
        },
        "test_history": {
            "availability": "available" if test_checkpoints else "unavailable",
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
                "selected_run_ids": selected_run_ids,
            },
            "graph_context": graph_context,
            "unavailable_reason": (
                None
                if test_checkpoints
                else "No canonical committed test run exists yet."
            ),
            "checkpoints": test_checkpoints,
        },
        "benchmark_context": {
            "phase": "on_hold",
            "hold_state": "on_hold",
            "hold_reason": benchmark_blocker,
            "dependencies": benchmark_dependencies,
            "authorization_state": "not_authorized",
            "next_qualifying_action": _action(
                "AUTHORIZE_BENCHMARK_EXECUTION",
                "Authorize benchmark execution only after roadmap dependencies pass",
                "benchmark_qualifying_action",
                [dashboard_ref, roadmap_ref, benchmark_ref],
                eligible=False,
                blocker=benchmark_blocker,
            ),
            "evidence": [dashboard_ref, roadmap_ref, benchmark_ref],
        },
        "work": {
            **({"milestone": native_milestone} if native_milestone is not None else {}),
            "current_milestone": development_lane["milestone"],
            "active_feature": feature_id,
            "lease": dict(lease) if isinstance(lease, Mapping) else None,
            "program_tasks": {
                "completed": program_done,
                "total": program_total,
                "remaining": program_total - program_done,
                "registered_sources": registered,
                "undecomposed_roadmap_items": undecomposed_roadmap_items,
            },
            "tasks": {
                "feature_id": feature_id,
                "completed": feature_done,
                "total": feature_total,
                "remaining": feature_total - feature_done,
            },
            "active_assignments": active_assignments,
            "checkpoints": [],
            "blockers": [],
            "current_next_action": current_action,
            "lanes": [integration_lane, development_lane],
        },
        "governance": {
            "corrections": corrections,
            "findings": findings,
            "risks": risks,
            "decisions": decisions,
            "verification": verifications,
            "limits": {
                "wip_max": int(policy_limits["wip_max"]),
                "repair_max": int(policy_limits["repair_max"]),
                "push_max": int(policy_limits["push_max"]),
            },
            "flow": {
                "active_feature_count": 1,
                "active_lease_count": 1 if lease else 0,
                "roadmap_blocker_count": 0,
                "open_p0_decision_count": sum(
                    1
                    for item in decisions
                    if item["status"] == "open" and item["id"].startswith("DEC-P0-")
                ),
                "open_p0_risk_count": sum(
                    1
                    for item in risks
                    if item["status"] == "open" and item["severity"] == "P0"
                ),
            },
        },
        "evidence_index": [
            {
                "id": identifier,
                "label": identifier.replace("-", " ").title(),
                "path": path,
                "sha256": _raw_digest(raw),
                "summary": "Exact committed identity used to derive this status bundle.",
                "freshness": "current",
                "recovery": None,
                "availability": "checkout_available",
                "exact_url": None,
            }
            for identifier, path, raw in evidence_pairs
        ]
        + [historical_evidence[key] for key in sorted(historical_evidence)]
        + [use_case_evidence_details[key] for key in sorted(use_case_evidence_details)]
        + governance_evidence_details
        + test_evidence_details,
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
        _validate_evidence_details(bundle)
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
