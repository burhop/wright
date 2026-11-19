"""Native wire values shared by source, bundles and run records."""

from __future__ import annotations

import hashlib
import json
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

Identifier = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)
]
Digest = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


def canonical_json(value: object) -> str:
    """wright-json-v1: sorted keys, compact UTF-8 JSON, finite numbers only."""
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="python")

    def model_value(item):
        if isinstance(item, BaseModel):
            return item.model_dump(mode="python")
        raise TypeError("Unsupported JSON value")

    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
            default=model_value,
        )
        encoded.encode("utf-8")
        return encoded
    except (TypeError, UnicodeError, RecursionError) as exc:
        raise ValueError("Value must be finite, serializable UTF-8 JSON") from exc


def canonical_digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class Contract(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, validate_default=True, allow_inf_nan=False
    )
