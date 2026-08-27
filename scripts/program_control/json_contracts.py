"""Strict JSON, schema, canonicalization, and compatibility primitives."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError, ValidationError


class ContractError(ValueError):
    """Base class for bounded contract failures."""


class DuplicateKeyError(ContractError):
    """Raised when a JSON object contains a duplicate member name."""


class UnsupportedVersionError(ContractError):
    """Raised when a producer version is not explicitly supported."""

    def __init__(self, kind: str, version: str) -> None:
        super().__init__(kind)
        self.kind = kind
        self.version = version


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError("duplicate JSON object key")
        result[key] = value
    return result


def strict_loads(raw: bytes | str) -> Any:
    """Decode UTF-8 JSON and reject BOMs, duplicate keys, and non-finite numbers."""

    if isinstance(raw, bytes):
        if raw.startswith(b"\xef\xbb\xbf"):
            raise ContractError("UTF-8 BOM is not permitted")
        try:
            text = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise ContractError("JSON is not valid UTF-8") from exc
    else:
        text = raw
        if text.startswith("\ufeff"):
            raise ContractError("UTF-8 BOM is not permitted")

    def reject_constant(_value: str) -> None:
        raise ContractError("non-finite JSON number is not permitted")

    try:
        return json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=reject_constant,
        )
    except json.JSONDecodeError as exc:
        raise ContractError("malformed JSON") from exc


def strict_load(path: Path) -> Any:
    return strict_loads(path.read_bytes())


def canonical_json_bytes(value: Any) -> bytes:
    """Return Wright JSON canonicalization v1 bytes."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def deterministic_json_bytes(value: Any) -> bytes:
    """Return stable human-inspectable JSON bytes with LF and a trailing newline."""

    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_digest(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def validate_schema(schema: Mapping[str, Any], instance: Any) -> list[ValidationError]:
    """Validate with Draft 2020-12 and return deterministically sorted errors."""

    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return sorted(
        validator.iter_errors(instance),
        key=lambda error: (
            tuple(str(part) for part in error.absolute_path),
            error.validator or "",
        ),
    )


def check_schema(schema: Mapping[str, Any]) -> None:
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ContractError("invalid Draft 2020-12 schema") from exc


def parse_version(version: Any) -> tuple[int, int]:
    if not isinstance(version, str):
        raise UnsupportedVersionError("SCHEMA_VERSION_INVALID", "")
    parts = version.split(".")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        raise UnsupportedVersionError("SCHEMA_VERSION_INVALID", version)
    return int(parts[0]), int(parts[1])


def require_compatible_version(
    version: Any,
    supported: Mapping[int, frozenset[int]] | None = None,
) -> tuple[int, int]:
    """Accept only explicitly declared major/minor pairs."""

    table = supported or {1: frozenset({0}), 2: frozenset({0})}
    major, minor = parse_version(version)
    if major not in table:
        raise UnsupportedVersionError("SCHEMA_MAJOR_UNSUPPORTED", str(version))
    if minor not in table[major]:
        raise UnsupportedVersionError("SCHEMA_MINOR_UNSUPPORTED", str(version))
    return major, minor


def load_and_validate(
    raw: bytes,
    schema: Mapping[str, Any],
    version_policy: Callable[[Any], tuple[int, int]] = require_compatible_version,
) -> Any:
    value = strict_loads(raw)
    if not isinstance(value, dict):
        raise ContractError("top-level JSON value must be an object")
    version_policy(value.get("schema_version"))
    errors = validate_schema(schema, value)
    if errors:
        raise ContractError("JSON does not satisfy its schema")
    return value
