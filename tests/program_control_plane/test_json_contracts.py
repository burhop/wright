"""Raw JSON, schema, format, and explicit-version compatibility contracts."""

from __future__ import annotations

import pytest

from program_control.json_contracts import (
    ContractError,
    DuplicateKeyError,
    UnsupportedVersionError,
    load_and_validate,
    require_compatible_version,
    strict_loads,
    validate_schema,
)


SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "observed_at", "name"],
    "properties": {
        "schema_version": {"const": "1.0"},
        "observed_at": {"type": "string", "format": "date-time"},
        "name": {"type": "string", "minLength": 1},
    },
}


@pytest.mark.parametrize(
    "raw",
    [
        b'{"schema_version":"1.0",',
        b"\xef\xbb\xbf{}",
        b'{"value":NaN}',
        b'{"value":"\xff"}',
    ],
)
def test_raw_malformed_non_finite_bom_and_non_utf8_are_rejected(raw: bytes) -> None:
    with pytest.raises(ContractError):
        strict_loads(raw)


def test_duplicate_object_members_are_rejected_at_every_depth() -> None:
    with pytest.raises(DuplicateKeyError):
        strict_loads(b'{"outer":{"same":1,"same":2}}')


@pytest.mark.parametrize(
    "raw",
    [
        b'{"schema_version":"1.0","observed_at":"2026-01-02T03:04:05Z"}',
        b'{"schema_version":"1.0","observed_at":"2026-01-02T03:04:05Z","name":"ok","extra":true}',
        b'{"schema_version":"1.0","observed_at":"not-a-date","name":"ok"}',
    ],
)
def test_missing_extra_and_invalid_format_fields_fail_schema(raw: bytes) -> None:
    with pytest.raises(ContractError):
        load_and_validate(raw, SCHEMA)


@pytest.mark.parametrize("raw", [b"[]", b"null", b'"value"'])
def test_top_level_non_objects_are_rejected(raw: bytes) -> None:
    with pytest.raises(ContractError):
        load_and_validate(raw, SCHEMA)


def test_draft_2020_12_format_checker_is_active() -> None:
    value = {
        "schema_version": "1.0",
        "observed_at": "2026-01-02 03:04:05",
        "name": "invalid timestamp",
    }
    assert validate_schema(SCHEMA, value)


@pytest.mark.parametrize(
    ("version", "kind"),
    [("3.0", "SCHEMA_MAJOR_UNSUPPORTED"), ("2.1", "SCHEMA_MINOR_UNSUPPORTED")],
)
def test_unknown_major_and_undeclared_minor_are_distinct(
    version: str, kind: str
) -> None:
    with pytest.raises(UnsupportedVersionError) as raised:
        require_compatible_version(version)
    assert raised.value.kind == kind


def test_only_explicit_compatibility_pairs_are_accepted() -> None:
    assert require_compatible_version("1.0") == (1, 0)
    assert require_compatible_version("2.0") == (2, 0)
