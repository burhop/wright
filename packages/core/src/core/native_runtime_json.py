"""Bounded runtime data JSON, separate from canonical process definitions.

Runtime text is literal Unicode and tool data may contain finite fractions.
Neither is normalized into the stricter native document identity profile.
"""

from __future__ import annotations

import json
import math
from typing import Any


def _validate(value: Any, depth: int = 0) -> None:
    if depth > 64:
        raise ValueError("Runtime JSON nesting exceeds 64 levels")
    if isinstance(value, str):
        value.encode("utf-8", errors="strict")
    elif value is None or isinstance(value, (bool, int)):
        return
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Runtime JSON numbers must be finite")
    elif isinstance(value, list):
        for item in value:
            _validate(item, depth + 1)
    elif isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("Runtime JSON keys must be strings")
            _validate(key, depth + 1)
            _validate(item, depth + 1)
    else:
        raise ValueError("Unsupported runtime JSON value")


def runtime_json_loads(raw: bytes, *, max_bytes: int = 1024 * 1024) -> Any:
    if len(raw) > max_bytes or raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("Runtime JSON exceeds its limit or contains a BOM")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate runtime JSON key")
            result[key] = value
        return result

    try:
        value = json.loads(
            raw.decode("utf-8", errors="strict"), object_pairs_hook=pairs
        )
        _validate(value)
        return value
    except RecursionError as error:
        raise ValueError("Runtime JSON nesting exceeds its limit") from error


def runtime_json_bytes(value: Any, *, max_bytes: int = 1024 * 1024) -> bytes:
    _validate(value)
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    if len(raw) > max_bytes:
        raise ValueError("Runtime JSON exceeds its byte limit")
    return raw
