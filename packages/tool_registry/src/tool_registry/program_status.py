"""Source-free validation and reading for immutable program-status bundles."""

from __future__ import annotations

import copy
import hashlib
import json
import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Final, Mapping

from jsonschema import Draft202012Validator, FormatChecker  # type: ignore[import-untyped]
from referencing import Registry, Resource


MAX_PROGRAM_STATUS_BYTES: Final = 4 * 1024 * 1024
CURRENT_FILENAME: Final = "current.json"
PUBLISHER_FILENAME: Final = "publisher.json"
SOURCE_CATALOG_FILENAME: Final = "program-status-source-catalog.json"
SOURCE_CATALOG_SCHEMA_FILENAME: Final = "program-status-source-catalog.schema.json"
WORK_REGISTRY_SCHEMA_FILENAME: Final = "work-registry.schema.json"
USE_CASE_REGISTRY_SCHEMA_FILENAME: Final = "use-case-registry.schema.json"
TEST_RUN_LEDGER_SCHEMA_FILENAME: Final = "test-run-ledger.schema.json"
SCHEMA_VERSION: Final = "1.0.0"


class ProgramStatusErrorCode(StrEnum):
    UNAVAILABLE = "PROGRAM_STATUS_UNAVAILABLE"
    IDENTITY_MISMATCH = "PROGRAM_STATUS_IDENTITY_MISMATCH"
    INVALID = "PROGRAM_STATUS_INVALID"
    READ_FAILED = "PROGRAM_STATUS_READ_FAILED"
    PUBLISHER_UNAVAILABLE = "PROGRAM_STATUS_PUBLISHER_UNAVAILABLE"
    PUBLISHER_INVALID = "PROGRAM_STATUS_PUBLISHER_INVALID"
    PUBLISHER_READ_FAILED = "PROGRAM_STATUS_PUBLISHER_READ_FAILED"


class ProgramStatusReadError(RuntimeError):
    """Typed, support-safe read failure."""

    def __init__(self, code: ProgramStatusErrorCode, recovery_class: str) -> None:
        super().__init__(code.value)
        self.code = code
        self.recovery_class = recovery_class


@dataclass(frozen=True, slots=True)
class ProgramStatusDocument:
    """Validated immutable bytes with copy-on-read parsed content."""

    bundle_id: str
    source_commit: str
    generated_at: str
    canonical_bytes: bytes
    source_kind: str

    def as_dict(self) -> dict[str, Any]:
        value = json.loads(self.canonical_bytes)
        if not isinstance(value, dict):  # pragma: no cover - constructor invariant
            raise AssertionError("validated program status must be an object")
        return copy.deepcopy(value)


@dataclass(frozen=True, slots=True)
class ProgramStatusPublisherState:
    state: str
    mode: str
    observed_commit: str | None
    last_attempt_at: str | None
    last_success_at: str | None
    failure_code: str | None
    recovery: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "mode": self.mode,
            "observed_commit": self.observed_commit,
            "last_attempt_at": self.last_attempt_at,
            "last_success_at": self.last_success_at,
            "failure_code": self.failure_code,
            "recovery": self.recovery,
        }


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


def _git_normalized_digest(raw: bytes) -> str:
    normalized = raw.replace(b"\r\n", b"\n")
    if b"\r" in normalized:
        raise ValueError("catalog contains a non-Git line ending")
    return hashlib.sha256(normalized).hexdigest()


def _framed_digest(prefix: str, values: list[str]) -> str:
    framed = bytearray(f"{prefix}\n".encode())
    for value in values:
        if "\x00" in value or unicodedata.normalize("NFC", value) != value:
            raise ValueError("digest inputs must be NFC without NUL")
        encoded = value.encode("utf-8")
        framed.extend(str(len(encoded)).encode())
        framed.extend(b":")
        framed.extend(encoded)
        framed.extend(b"\n")
    return hashlib.sha256(framed).hexdigest()


def _test_case_set_digest(test_case_ids: list[str]) -> str:
    if len(test_case_ids) != len(set(test_case_ids)):
        raise ValueError("duplicate test case identity")
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


def _strict_json(raw: bytes) -> Any:
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("BOM is not permitted")
    seen_duplicate = False

    def object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        nonlocal seen_duplicate
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                seen_duplicate = True
            result[key] = value
        return result

    value = json.loads(
        raw.decode("utf-8", errors="strict"),
        object_pairs_hook=object_pairs,
        parse_constant=lambda _value: (_ for _ in ()).throw(ValueError()),
    )
    if seen_duplicate:
        raise ValueError("duplicate object key")
    return value


def _read_bounded(path: Path, missing: ProgramStatusErrorCode) -> bytes:
    try:
        with path.open("rb") as handle:
            raw = handle.read(MAX_PROGRAM_STATUS_BYTES + 1)
    except FileNotFoundError as exc:
        raise ProgramStatusReadError(missing, "install_or_publish") from exc
    except OSError as exc:
        read_code = (
            ProgramStatusErrorCode.PUBLISHER_READ_FAILED
            if missing is ProgramStatusErrorCode.PUBLISHER_UNAVAILABLE
            else ProgramStatusErrorCode.READ_FAILED
        )
        raise ProgramStatusReadError(read_code, "inspect_local_data_root") from exc
    if len(raw) > MAX_PROGRAM_STATUS_BYTES:
        invalid_code = (
            ProgramStatusErrorCode.PUBLISHER_INVALID
            if missing is ProgramStatusErrorCode.PUBLISHER_UNAVAILABLE
            else ProgramStatusErrorCode.INVALID
        )
        raise ProgramStatusReadError(invalid_code, "replace_bounded_artifact")
    return raw


class ProgramStatusReader:
    """Read installed state first and use packaged fallback only when absent."""

    def __init__(
        self,
        installed_root: Path,
        packaged_root: Path,
        *,
        schema_root: Path | None = None,
    ) -> None:
        self.installed_root = installed_root
        self.packaged_root = packaged_root
        self.schema_root = schema_root or packaged_root

    def _schemas(self) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
        try:
            bundle = _strict_json(
                _read_bounded(
                    self.schema_root / "program-status-bundle.schema.json",
                    ProgramStatusErrorCode.UNAVAILABLE,
                )
            )
            dashboard = _strict_json(
                _read_bounded(
                    self.schema_root / "dashboard.schema.json",
                    ProgramStatusErrorCode.UNAVAILABLE,
                )
            )
        except ProgramStatusReadError:
            raise
        except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
            raise ProgramStatusReadError(
                ProgramStatusErrorCode.INVALID, "reinstall_program_status_schemas"
            ) from exc
        if not isinstance(bundle, Mapping) or not isinstance(dashboard, Mapping):
            raise ProgramStatusReadError(
                ProgramStatusErrorCode.INVALID, "reinstall_program_status_schemas"
            )
        return bundle, dashboard

    def _validate_source_contracts(self, source: Mapping[str, Any]) -> None:
        """Validate the frozen source boundary used by full EPP-F01B bundles."""

        catalog_digest = source.get("source_catalog_sha256")
        catalog_path = source.get("source_catalog_path")
        if catalog_digest is None and catalog_path is None:
            # Small legacy/synthetic contracts predate the closed source boundary.
            return
        if catalog_path != (
            "specs/077-browser-program-status/contracts/"
            "program-status-source-catalog.json"
        ):
            raise ProgramStatusReadError(
                ProgramStatusErrorCode.IDENTITY_MISMATCH,
                "reinstall_program_status_contracts",
            )
        try:
            catalog_raw = _read_bounded(
                self.schema_root / SOURCE_CATALOG_FILENAME,
                ProgramStatusErrorCode.UNAVAILABLE,
            )
            if _git_normalized_digest(catalog_raw) != catalog_digest:
                raise ProgramStatusReadError(
                    ProgramStatusErrorCode.IDENTITY_MISMATCH,
                    "reinstall_program_status_contracts",
                )
            catalog = _strict_json(catalog_raw)
            schema_files = (
                SOURCE_CATALOG_SCHEMA_FILENAME,
                WORK_REGISTRY_SCHEMA_FILENAME,
                USE_CASE_REGISTRY_SCHEMA_FILENAME,
                TEST_RUN_LEDGER_SCHEMA_FILENAME,
            )
            schemas = {
                filename: _strict_json(
                    _read_bounded(
                        self.schema_root / filename,
                        ProgramStatusErrorCode.UNAVAILABLE,
                    )
                )
                for filename in schema_files
            }
            if not isinstance(catalog, Mapping) or any(
                not isinstance(schema, Mapping) for schema in schemas.values()
            ):
                raise ValueError("source contracts must be objects")
            for schema in schemas.values():
                Draft202012Validator.check_schema(schema)
            catalog_errors = list(
                Draft202012Validator(
                    schemas[SOURCE_CATALOG_SCHEMA_FILENAME],
                    format_checker=FormatChecker(),
                ).iter_errors(catalog)
            )
            if catalog_errors:
                raise ValueError("source catalog schema validation failed")
            if (
                catalog.get("schema_version") != SCHEMA_VERSION
                or len(catalog.get("sources", {})) != 20
            ):
                raise ValueError("source catalog identity is incomplete")
        except ProgramStatusReadError:
            raise
        except (
            KeyError,
            TypeError,
            UnicodeError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            raise ProgramStatusReadError(
                ProgramStatusErrorCode.INVALID,
                "reinstall_program_status_contracts",
            ) from exc

    @staticmethod
    def _validate_relations(value: Mapping[str, Any]) -> None:
        """Fail closed on cross-field claims that JSON Schema cannot express."""

        supplement = value["supplement"]
        work = supplement["work"]
        for name in ("program_tasks", "tasks"):
            counts = work[name]
            if counts["completed"] + counts["remaining"] != counts["total"]:
                raise ValueError(f"{name} arithmetic does not reconcile")
        if work["tasks"]["feature_id"] != work["active_feature"]:
            raise ValueError("active feature and feature task identity disagree")
        registered = work["program_tasks"]["registered_sources"]
        if len(registered) != len(set(registered)):
            raise ValueError("registered task sources must be unique")

        assignments = work["active_assignments"]
        assignment_ids = [item["agent_id"] for item in assignments]
        if len(assignment_ids) != len(set(assignment_ids)):
            raise ValueError("active assignment identities must be unique")
        if len(assignments) > value["supplement"]["governance"]["limits"]["wip_max"]:
            raise ValueError("active assignments exceed the governed WIP limit")

        use_cases = supplement["use_cases"]
        all_counts = use_cases["all"]
        if (
            all_counts["not_started"]
            + all_counts["in_progress"]
            + all_counts["implemented"]
            != all_counts["total"]
            or all_counts["remaining"]
            != all_counts["total"] - all_counts["implemented"]
            or all_counts["independently_verified"] > all_counts["implemented"]
        ):
            raise ValueError("all-use-case funnel does not reconcile")
        items = use_cases["items"]
        item_ids = [item["id"] for item in items]
        if len(item_ids) != len(set(item_ids)) or len(items) != all_counts["total"]:
            raise ValueError("use-case inventory does not reconcile")
        process_items = [item for item in items if item["process_100_id"] is not None]
        expected_process_ids = {f"EPP-PROC-{number:03d}" for number in range(1, 101)}
        process_ids = [item["process_100_id"] for item in process_items]
        if len(process_ids) != len(set(process_ids)) or not set(process_ids) <= (
            expected_process_ids
        ):
            raise ValueError("process use-case identity is outside EPP-PROC-001..100")
        derived_all = {
            "total": len(items),
            "not_started": 0,
            "in_progress": 0,
            "implemented": 0,
            "independently_verified": 0,
            "remaining": 0,
        }
        derived_process = {
            "population_target": 100,
            "defined": 0,
            "in_progress": 0,
            "implemented": 0,
            "tested": 0,
            "independently_verified": 0,
            "benchmark_qualified": 0,
        }
        stage_names = (
            "definition_evidence",
            "progress_evidence",
            "acceptance_evidence",
            "test_evidence",
            "independent_verification_evidence",
            "benchmark_qualification_evidence",
        )
        for item in items:
            stage_identities: set[tuple[str, str, str]] = set()
            for stage_name in stage_names:
                for stage in item[stage_name]:
                    identity = (
                        stage["source_name"],
                        stage["subject_id"],
                        stage["evidence"]["sha256"],
                    )
                    if identity in stage_identities:
                        raise ValueError(
                            "use-case evidence is reused across incompatible stages"
                        )
                    stage_identities.add(identity)
            acceptance_ids = {
                stage["subject_id"] for stage in item["acceptance_evidence"]
            }
            for stage in item["independent_verification_evidence"]:
                if (
                    stage["acceptance_subject_id"] not in acceptance_ids
                    or stage["evidence_author"] == stage["independent_verifier"]
                ):
                    raise ValueError(
                        "use-case verification is not acceptance-bound and independent"
                    )
            for stage in item["benchmark_qualification_evidence"]:
                if (
                    stage["subject_id"] != item["process_100_id"]
                    or stage["acceptance_subject_id"] not in acceptance_ids
                    or stage["evidence_author"] == stage["independent_verifier"]
                    or not item["independent_verification_evidence"]
                ):
                    raise ValueError(
                        "benchmark qualification is not process/acceptance/verification bound"
                    )
            implemented = bool(item["acceptance_evidence"])
            verified = bool(item["independent_verification_evidence"])
            in_progress = not implemented and bool(item["progress_evidence"])
            derived_all["implemented"] += int(implemented)
            derived_all["independently_verified"] += int(verified)
            derived_all["in_progress"] += int(in_progress)
            derived_all["not_started"] += int(not implemented and not in_progress)
            if item["process_100_id"] is not None:
                derived_process["defined"] += int(bool(item["definition_evidence"]))
                derived_process["in_progress"] += int(in_progress)
                derived_process["implemented"] += int(implemented)
                derived_process["tested"] += int(
                    any(stage["verdict"] == "passed" for stage in item["test_evidence"])
                )
                derived_process["independently_verified"] += int(verified)
                derived_process["benchmark_qualified"] += int(
                    bool(item["benchmark_qualification_evidence"])
                )
        derived_all["remaining"] = derived_all["total"] - derived_all["implemented"]
        if derived_all != all_counts:
            raise ValueError("all-use-case funnel is not derived from its inventory")
        process = use_cases["process_100"]
        process_stages = (
            "defined",
            "in_progress",
            "implemented",
            "tested",
            "independently_verified",
            "benchmark_qualified",
        )
        if process["population_target"] != 100 or any(
            process[name] > process["population_target"] for name in process_stages
        ):
            raise ValueError("100-process funnel exceeds its governed population")
        if process != derived_process:
            raise ValueError("100-process funnel is not derived from its inventory")
        if (
            process["benchmark_qualified"] > process["independently_verified"]
            or process["independently_verified"] > process["implemented"]
            or process["benchmark_qualified"]
            != value["dashboard"]["benchmark_summary"]["counted"]
        ):
            raise ValueError("100-process governed relations do not reconcile")

        governance = supplement["governance"]
        corrections = governance["corrections"]
        findings = governance["findings"]
        verifications = governance["verification"]
        correction_by_id = {item["profile_id"]: item for item in corrections}
        finding_by_id = {item["id"]: item for item in findings}
        verification_by_id = {item["id"]: item for item in verifications}
        if (
            len(correction_by_id) != len(corrections)
            or len(finding_by_id) != len(findings)
            or len(verification_by_id) != len(verifications)
        ):
            raise ValueError(
                "correction, finding, and verification identities must be unique"
            )
        for correction in corrections:
            expected = set(correction["expected_claim_ids"])
            verified = set(correction["verified_claim_ids"])
            correction_findings = set(correction["finding_ids"])
            resolved = set(correction["resolved_finding_ids"])
            unresolved = set(correction["unresolved_finding_ids"])
            correction_verifications = set(correction["verification_ids"])
            if (
                not verified <= expected
                or correction_findings != expected
                or resolved & unresolved
                or resolved | unresolved != correction_findings
                or not correction_verifications
                or not correction_verifications <= set(verification_by_id)
                or not correction_findings <= set(finding_by_id)
            ):
                raise ValueError("correction claim relations do not reconcile")
            for finding_id in correction_findings:
                finding = finding_by_id[finding_id]
                if finding_id in resolved and (
                    finding["status"] != "resolved"
                    or finding["correction_profile_id"] != correction["profile_id"]
                    or finding["resolution_verification_id"]
                    not in correction_verifications
                ):
                    raise ValueError("resolved finding relation is not reciprocal")
                if finding_id in unresolved and finding["status"] == "resolved":
                    raise ValueError("unresolved finding is marked resolved")
            for verification_id in correction_verifications:
                verification = verification_by_id[verification_id]
                if correction["profile_id"] not in verification[
                    "correction_profile_ids"
                ] or not correction_findings <= set(verification["finding_ids"]):
                    raise ValueError(
                        "correction verification relation is not reciprocal"
                    )
        for verification in verifications:
            if (
                verification["independent"] is not True
                or verification["author"] == verification["verifier"]
                or not set(verification["finding_ids"]) <= set(finding_by_id)
                or not set(verification["correction_profile_ids"])
                <= set(correction_by_id)
            ):
                raise ValueError("independent verification relation is invalid")

        history_ids = [series["id"] for series in supplement["history"]]
        if len(history_ids) != len(set(history_ids)):
            raise ValueError("history metric identities must be unique")
        for series in supplement["history"]:
            observations = series["observations"]
            if series["availability"] == "unavailable" and observations:
                raise ValueError("unavailable history must not contain observations")
            commits = [observation["commit"] for observation in observations]
            if len(commits) != len(set(commits)):
                raise ValueError("history contains duplicate committed checkpoints")
            for observation in observations:
                if not 0 <= observation["value"] <= observation["denominator"]:
                    raise ValueError("history observation is outside its denominator")

        test_history = supplement["test_history"]
        checkpoints = test_history["checkpoints"]
        if test_history["availability"] == "unavailable" and checkpoints:
            raise ValueError("unavailable test history must not contain checkpoints")
        selected = test_history["selection_attestation"]["selected_run_ids"]
        checkpoint_ids = [
            source["run_id"]
            for checkpoint in checkpoints
            for source in checkpoint["suite_sources"]
        ]
        if len(checkpoint_ids) != len(set(checkpoint_ids)) or set(selected) != set(
            checkpoint_ids
        ):
            raise ValueError("selected test runs do not match test checkpoints")
        for checkpoint in checkpoints:
            counts = checkpoint["counts"]
            component_counts = {
                name: 0 for name in ("total", "passed", "failed", "skipped", "not_run")
            }
            category_counts: dict[str, dict[str, int] | None] = {
                name: None for name in ("unit", "integration", "e2e", "benchmark")
            }
            seen_cases: set[str] = set()
            source_times: list[str] = []
            for source in checkpoint["suite_sources"]:
                source_times.append(source["observed_at"])
                source_counts = source["counts"]
                test_ids = source["test_case_ids"]
                if (
                    source["terminal"] is not True
                    or source["run_key"]
                    != _test_run_key({**source, "commit": checkpoint["commit"]})
                    or source["test_case_set_sha256"] != _test_case_set_digest(test_ids)
                    or source_counts["total"] != len(test_ids)
                    or sum(
                        source_counts[name]
                        for name in ("passed", "failed", "skipped", "not_run")
                    )
                    != source_counts["total"]
                ):
                    raise ValueError("selected test source does not reconcile")
                if source["aggregate_role"] == "summary_only":
                    continue
                if seen_cases & set(test_ids):
                    raise ValueError("selected component test identities overlap")
                seen_cases.update(test_ids)
                for name in component_counts:
                    component_counts[name] += source_counts[name]
                category = source["category"]
                if category_counts[category] is None:
                    category_counts[category] = {name: 0 for name in component_counts}
                assert category_counts[category] is not None
                for name in component_counts:
                    category_counts[category][name] += source_counts[name]
            if (
                counts != component_counts
                or checkpoint["categories"] != category_counts
            ):
                raise ValueError("test checkpoint aggregation does not reconcile")
            if source_times and checkpoint["observed_at"] != max(source_times):
                raise ValueError(
                    "test checkpoint time is not the latest selected source"
                )
            denominator = counts["passed"] + counts["failed"]
            expected_rate = None if denominator == 0 else counts["passed"] / denominator
            actual_rate = checkpoint["pass_rate"]
            if (actual_rate is None) != (expected_rate is None) or (
                actual_rate is not None
                and expected_rate is not None
                and abs(actual_rate - expected_rate) > 1e-12
            ):
                raise ValueError("test checkpoint pass rate does not reconcile")

        evidence_index = supplement["evidence_index"]
        indexed = [
            (item["id"], item["path"], item["sha256"]) for item in evidence_index
        ]
        if len(indexed) != len(set(indexed)):
            raise ValueError("evidence index contains duplicate exact identities")
        index_set = set(indexed)

        test_result_prefix = "test-results/"
        test_source_set = {
            (reference["id"], reference["path"], reference["sha256"])
            for checkpoint in checkpoints
            for source in checkpoint["suite_sources"]
            for reference in source["evidence"]
            if reference["path"].startswith(test_result_prefix)
        }
        indexed_test_results = {
            (item["id"], item["path"], item["sha256"])
            for item in evidence_index
            if item["path"].startswith(test_result_prefix)
        }
        if indexed_test_results != test_source_set:
            raise ValueError(
                "test-result evidence details must exactly match selected test sources"
            )

        def walk(
            node: Any,
            *,
            path: tuple[str | int, ...] = (),
            in_index: bool = False,
        ) -> None:
            if isinstance(node, Mapping):
                if (
                    not in_index
                    and {"id", "path", "sha256"} <= node.keys()
                    and (node["id"], node["path"], node["sha256"]) not in index_set
                ):
                    raise ValueError("evidence reference has no exact indexed detail")
                if (
                    not in_index
                    and {"id", "path", "sha256"} <= node.keys()
                    and str(node["path"]).startswith(test_result_prefix)
                    and not (
                        len(path) == 8
                        and path[0:3] == ("supplement", "test_history", "checkpoints")
                        and isinstance(path[3], int)
                        and path[4] == "suite_sources"
                        and isinstance(path[5], int)
                        and path[6] == "evidence"
                        and isinstance(path[7], int)
                    )
                ):
                    raise ValueError(
                        "test-result evidence is outside a selected test suite source"
                    )
                for key, child in node.items():
                    walk(
                        child,
                        path=(*path, str(key)),
                        in_index=in_index or key == "evidence_index",
                    )
            elif isinstance(node, list):
                for index, child in enumerate(node):
                    walk(child, path=(*path, index), in_index=in_index)

        walk(value)

    def _validate_bundle(self, raw: bytes, source_kind: str) -> ProgramStatusDocument:
        try:
            value = _strict_json(raw)
            if (
                not isinstance(value, Mapping)
                or value.get("schema_version") != SCHEMA_VERSION
            ):
                raise ValueError("unsupported bundle version")
            bundle_schema, dashboard_schema = self._schemas()
            dashboard_id = dashboard_schema.get("$id")
            if not isinstance(dashboard_id, str):
                raise ValueError("dashboard schema identity is absent")
            registry = Registry().with_resource(
                dashboard_id, Resource.from_contents(dashboard_schema)
            )
            errors = list(
                Draft202012Validator(
                    bundle_schema,
                    registry=registry,
                    format_checker=FormatChecker(),
                ).iter_errors(value)
            )
            if errors:
                raise ValueError("bundle schema validation failed")
            source = value["source"]
            dashboard = value["dashboard"]
            supplement = value["supplement"]
            self._validate_source_contracts(source)
            if _digest(dashboard) != source["dashboard_canonical_sha256"]:
                raise ProgramStatusReadError(
                    ProgramStatusErrorCode.IDENTITY_MISMATCH,
                    "republish_exact_committed_subject",
                )
            raw_evidence = source["raw_identity_evidence"]
            if (
                raw_evidence["path"] != source["snapshot_path"]
                or raw_evidence["sha256"] != source["snapshot_raw_sha256"]
            ):
                raise ProgramStatusReadError(
                    ProgramStatusErrorCode.IDENTITY_MISMATCH,
                    "republish_exact_committed_subject",
                )
            expected_bundle_id = _digest(
                {"source": source, "dashboard": dashboard, "supplement": supplement}
            )
            if value["bundle_id"] != expected_bundle_id:
                raise ProgramStatusReadError(
                    ProgramStatusErrorCode.IDENTITY_MISMATCH,
                    "republish_exact_committed_subject",
                )
            if source.get("source_catalog_sha256") is not None:
                self._validate_relations(value)
            canonical = _canonical_bytes(value)
            return ProgramStatusDocument(
                bundle_id=expected_bundle_id,
                source_commit=str(source["commit"]),
                generated_at=str(value["generated_at"]),
                canonical_bytes=canonical,
                source_kind=source_kind,
            )
        except ProgramStatusReadError:
            raise
        except (
            KeyError,
            TypeError,
            UnicodeError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            raise ProgramStatusReadError(
                ProgramStatusErrorCode.INVALID, "republish_or_reinstall"
            ) from exc

    def read_bundle(self) -> ProgramStatusDocument:
        installed = self.installed_root / CURRENT_FILENAME
        try:
            raw = _read_bounded(installed, ProgramStatusErrorCode.UNAVAILABLE)
        except ProgramStatusReadError as exc:
            if exc.code is not ProgramStatusErrorCode.UNAVAILABLE:
                raise
            raw = _read_bounded(
                self.packaged_root / CURRENT_FILENAME,
                ProgramStatusErrorCode.UNAVAILABLE,
            )
            return self._validate_bundle(raw, "packaged_fallback")
        return self._validate_bundle(raw, "installed")

    def read_publisher(self) -> ProgramStatusPublisherState:
        raw = _read_bounded(
            self.installed_root / PUBLISHER_FILENAME,
            ProgramStatusErrorCode.PUBLISHER_UNAVAILABLE,
        )
        try:
            value = _strict_json(raw)
            if not isinstance(value, Mapping):
                raise ValueError("publisher state must be an object")
            bundle_schema, _dashboard_schema = self._schemas()
            publisher = bundle_schema["$defs"]["publisher"]
            publisher_schema = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$defs": bundle_schema["$defs"],
                **publisher,
            }
            if list(
                Draft202012Validator(
                    publisher_schema, format_checker=FormatChecker()
                ).iter_errors(value)
            ):
                raise ValueError("publisher schema validation failed")
            return ProgramStatusPublisherState(
                state=str(value["state"]),
                mode=str(value["mode"]),
                observed_commit=value["observed_commit"],
                last_attempt_at=value["last_attempt_at"],
                last_success_at=value["last_success_at"],
                failure_code=value["failure_code"],
                recovery=value["recovery"],
            )
        except (
            KeyError,
            TypeError,
            UnicodeError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            raise ProgramStatusReadError(
                ProgramStatusErrorCode.PUBLISHER_INVALID,
                "restart_or_repair_publisher",
            ) from exc
