"""Source-free validation and reading for immutable program-status bundles."""

from __future__ import annotations

import copy
import hashlib
import json
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
