"""Wright's bounded, exact JSON profile, shared by native and legacy readers."""

from __future__ import annotations

import json
import unicodedata
from collections.abc import Mapping
from typing import Any

MAX_SAFE_INTEGER = 2**53 - 1


def _validate(value: object, *, safe_integers: bool, depth: int = 0) -> None:
    if depth > 64:
        raise ValueError("JSON nesting exceeds 64 levels")
    if isinstance(value, str):
        value.encode("utf-8", errors="strict")
        if unicodedata.normalize("NFC", value) != value:
            raise ValueError("strings must already be NFC")
    elif value is None or isinstance(value, bool):
        return
    elif isinstance(value, int):
        if safe_integers and abs(value) > MAX_SAFE_INTEGER:
            raise ValueError("integer exceeds the cross-language safe range")
    elif isinstance(value, list):
        for item in value:
            _validate(item, safe_integers=safe_integers, depth=depth + 1)
    elif isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("object keys must be strings")
            _validate(key, safe_integers=safe_integers, depth=depth + 1)
            _validate(item, safe_integers=safe_integers, depth=depth + 1)
    else:
        raise ValueError("unsupported exact JSON value")


def strict_json_loads(
    raw: bytes, *, max_bytes: int = 1024 * 1024, safe_integers: bool = True
) -> Any:
    """Reject ambiguous input rather than normalize it into an accepted document."""
    if len(raw) > max_bytes:
        raise ValueError("JSON exceeds the byte limit")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF-8 BOM is not permitted")

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate object key")
            result[key] = value
        return result

    def integer(token: str) -> int:
        if token == "-0":
            raise ValueError("negative zero is not permitted")
        return int(token)

    def reject_number(_token: str) -> int:
        raise ValueError("only integer number tokens are permitted")

    try:
        value = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=pairs,
            parse_int=integer,
            parse_float=reject_number,
            parse_constant=reject_number,
        )
        _validate(value, safe_integers=safe_integers)
    except RecursionError as exc:
        raise ValueError("JSON nesting exceeds the limit") from exc
    return value


def canonical_json_bytes(value: object, *, safe_integers: bool = True) -> bytes:
    """Sort object keys by UTF-8 bytes, retain array order and exact scalar values."""
    _validate(value, safe_integers=safe_integers)

    def ordered(item: object) -> object:
        if isinstance(item, Mapping):
            return {
                key: ordered(item[key])
                for key in sorted(item, key=lambda key: key.encode("utf-8"))
            }
        if isinstance(item, list):
            return [ordered(child) for child in item]
        return item

    return json.dumps(
        ordered(value), ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
