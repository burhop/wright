"""Bounded, lazy value adapters for the public Wright display API."""

from __future__ import annotations

import base64
import io
import json
import math
import re
from dataclasses import dataclass
from typing import Any

from .models import DisplayRepresentation, NativeGraph


@dataclass(frozen=True, slots=True)
class AdapterLimits:
    maximum_graph_points: int = 100_000
    maximum_encoded_bytes: int = 16 * 1024 * 1024
    maximum_json_depth: int = 32
    maximum_json_items: int = 1_000_000


_ALLOWED_MIME = {
    "text/plain": "utf-8",
    "text/html": "utf-8",
    "image/png": "base64",
    "image/jpeg": "base64",
    "image/svg+xml": "utf-8",
    "application/vnd.wright.table+json": "json",
    "application/vnd.plotly.v1+json": "json",
}
_HTML_START = re.compile(
    r"^\s*<(?:!doctype|html|body|main|section|article|div|p|h[1-6]|table|ul|ol|pre|strong|em)\b",
    re.IGNORECASE,
)


def _json_metrics(value: Any, *, depth: int = 1) -> tuple[int, int]:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("display JSON numbers must be finite")
    if value is None or isinstance(value, (str, int, float, bool)):
        return depth, 1
    if isinstance(value, dict):
        maximum = depth
        count = 1
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("display JSON object keys must be strings")
            child_depth, child_count = _json_metrics(item, depth=depth + 1)
            maximum = max(maximum, child_depth)
            count += child_count
        return maximum, count
    if isinstance(value, (list, tuple)):
        maximum = depth
        count = 1
        for item in value:
            child_depth, child_count = _json_metrics(item, depth=depth + 1)
            maximum = max(maximum, child_depth)
            count += child_count
        return maximum, count
    raise ValueError(f"display JSON contains unsupported {type(value).__name__}")


def _require_bounded_json(value: Any, limits: AdapterLimits) -> Any:
    depth, items = _json_metrics(value)
    if depth > limits.maximum_json_depth:
        raise ValueError("display JSON exceeds the maximum depth")
    if items > limits.maximum_json_items:
        raise ValueError("display JSON exceeds the maximum item count")
    encoded = json.dumps(
        value, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    ).encode("utf-8")
    if len(encoded) > limits.maximum_encoded_bytes:
        raise ValueError("display representation exceeds the maximum encoded bytes")
    return value


def _require_bounded(representations, limits: AdapterLimits):
    bounded: list[DisplayRepresentation] = []
    for representation in representations:
        if representation.encoding == "json":
            _require_bounded_json(representation.data, limits)
            encoded_length = len(
                json.dumps(
                    representation.data,
                    ensure_ascii=False,
                    allow_nan=False,
                    separators=(",", ":"),
                ).encode("utf-8")
            )
        else:
            encoded_length = len(str(representation.data).encode("utf-8"))
        if encoded_length > limits.maximum_encoded_bytes:
            raise ValueError("display representation exceeds the maximum encoded bytes")
        bounded.append(representation)
    return tuple(bounded)


def _native_graph(value: NativeGraph, limits: AdapterLimits):
    point_count = len(value.values) if value.kind == "histogram" else len(value.y)
    if point_count > limits.maximum_graph_points:
        raise ValueError("native graph exceeds the maximum points")
    if value.kind == "histogram":
        trace = {"type": "histogram", "x": list(value.values), "nbinsx": value.bins}
        table = {"columns": [value.x_label], "data": [[item] for item in value.values]}
    else:
        trace = {
            "type": "bar" if value.kind == "bar" else "scatter",
            "mode": "markers" if value.kind == "scatter" else "lines",
            "x": list(value.x),
            "y": list(value.y),
        }
        table = {
            "columns": [value.x_label, value.y_label],
            "data": [[x, y] for x, y in zip(value.x, value.y, strict=True)],
        }
    plotly = {
        "data": [trace],
        "layout": {
            "title": {"text": value.title},
            "xaxis": {"title": {"text": value.x_label}},
            "yaxis": {"title": {"text": value.y_label}},
        },
    }
    return (
        DisplayRepresentation(
            "application/vnd.plotly.v1+json", "json", plotly, fallback_rank=0
        ),
        DisplayRepresentation(
            "application/vnd.wright.table+json", "json", table, fallback_rank=10
        ),
        DisplayRepresentation("text/plain", "utf-8", value.description, fallback_rank=20),
    )


def _matplotlib_like(value: Any):
    stream = io.BytesIO()
    value.savefig(stream, format="png")
    return (
        DisplayRepresentation(
            "image/png", "base64", base64.b64encode(stream.getvalue()).decode("ascii")
        ),
    )


def _plotly_like(value: Any):
    return (
        DisplayRepresentation(
            "application/vnd.plotly.v1+json", "json", value.to_plotly_json()
        ),
    )


def _pandas_like(value: Any):
    split = value.to_dict(orient="split")
    table = {"columns": list(split["columns"]), "data": list(split["data"])}
    return (DisplayRepresentation("application/vnd.wright.table+json", "json", table),)


def _pil_like(value: Any):
    stream = io.BytesIO()
    value.save(stream, format="PNG")
    return (
        DisplayRepresentation(
            "image/png",
            "base64",
            base64.b64encode(stream.getvalue()).decode("ascii"),
            metadata={"mode": str(value.mode), "size": list(value.size)},
        ),
    )


def _mime_bundle(value: Any, *, active_html: bool):
    bundle = value._repr_mimebundle_(include=None, exclude=None)
    if isinstance(bundle, tuple):
        bundle = bundle[0]
    if not isinstance(bundle, dict):
        raise ValueError("_repr_mimebundle_ must return a mapping")
    representations: list[DisplayRepresentation] = []
    for rank, (media_type, data) in enumerate(bundle.items()):
        encoding = _ALLOWED_MIME.get(str(media_type))
        if encoding is None:
            continue
        representations.append(
            DisplayRepresentation(
                str(media_type),
                encoding,  # type: ignore[arg-type]
                data,
                active_html=bool(active_html and media_type == "text/html"),
                fallback_rank=rank,
            )
        )
    if not representations:
        raise ValueError("_repr_mimebundle_ returned no supported representations")
    return tuple(representations)


def adapt_display_value(
    value: Any,
    *,
    active_html: bool = False,
    limits: AdapterLimits | None = None,
) -> tuple[DisplayRepresentation, ...]:
    """Adapt a Python value without importing any optional dependency."""

    effective = limits or AdapterLimits()
    if isinstance(value, NativeGraph):
        representations = _native_graph(value, effective)
    elif callable(getattr(value, "savefig", None)):
        representations = _matplotlib_like(value)
    elif callable(getattr(value, "to_plotly_json", None)):
        representations = _plotly_like(value)
    elif hasattr(value, "columns") and callable(getattr(value, "to_dict", None)):
        representations = _pandas_like(value)
    elif (
        hasattr(value, "mode")
        and hasattr(value, "size")
        and callable(getattr(value, "save", None))
    ):
        representations = _pil_like(value)
    elif isinstance(value, str) and value.lstrip().lower().startswith("<svg"):
        representations = (
            DisplayRepresentation("image/svg+xml", "utf-8", value),
        )
    elif callable(getattr(value, "_repr_mimebundle_", None)):
        representations = _mime_bundle(value, active_html=active_html)
    elif isinstance(value, list) and value and all(
        isinstance(row, dict) for row in value
    ):
        columns = list(value[0])
        if not all(list(row) == columns for row in value):
            raise ValueError("table rows must use the same ordered columns")
        representations = (
            DisplayRepresentation(
                "application/vnd.wright.table+json",
                "json",
                {
                    "columns": columns,
                    "data": [[row[column] for column in columns] for row in value],
                },
            ),
        )
    elif isinstance(value, str):
        representations = (
            DisplayRepresentation(
                "text/html" if active_html or _HTML_START.match(value) else "text/plain",
                "utf-8",
                value,
                active_html=active_html,
            ),
        )
    else:
        representations = (
            DisplayRepresentation("text/plain", "utf-8", repr(value)),
        )
    return _require_bounded(representations, effective)
