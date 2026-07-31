"""No-dependency graph helpers designed for novice authoring."""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any

from .display import display
from .models import DisplayHandle, NativeGraph


_MAXIMUM_GRAPH_POINTS = 100_000


def _text(value: str, label: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{label} must not be empty")
    return normalized


def _numbers(values: Iterable[Any], label: str) -> tuple[float, ...]:
    normalized: list[float] = []
    for value in values:
        if isinstance(value, bool):
            raise TypeError(f"{label} values must be numbers")
        try:
            number = float(value)
        except (TypeError, ValueError) as error:
            raise TypeError(f"{label} values must be numbers") from error
        if not math.isfinite(number):
            raise ValueError(f"{label} values must be finite")
        normalized.append(number)
    if not normalized:
        raise ValueError(f"{label} requires at least one value")
    if len(normalized) > _MAXIMUM_GRAPH_POINTS:
        raise ValueError(f"{label} exceeds {_MAXIMUM_GRAPH_POINTS} points")
    return tuple(normalized)


def _bar_x(values: Iterable[Any]) -> tuple[float | str, ...]:
    normalized: list[float | str] = []
    for value in values:
        if isinstance(value, str):
            item = value.strip()
            if not item:
                raise ValueError("x category labels must not be empty")
            normalized.append(item)
        else:
            normalized.extend(_numbers((value,), "x"))
    if not normalized:
        raise ValueError("x requires at least one value")
    if len(normalized) > _MAXIMUM_GRAPH_POINTS:
        raise ValueError(f"x exceeds {_MAXIMUM_GRAPH_POINTS} points")
    return tuple(normalized)


def _xy_graph(
    kind: str,
    *,
    x: Iterable[Any],
    y: Iterable[Any],
    title: str,
    x_label: str,
    y_label: str,
    description: str,
    display_id: str | None,
    durability: str,
) -> DisplayHandle:
    normalized_x = _bar_x(x) if kind == "bar" else _numbers(x, "x")
    normalized_y = _numbers(y, "y")
    if len(normalized_x) != len(normalized_y):
        raise ValueError("x and y must have the same length")
    normalized_title = _text(title, "title")
    graph = NativeGraph(
        kind=kind,  # type: ignore[arg-type]
        x=normalized_x,
        y=normalized_y,
        title=normalized_title,
        x_label=_text(x_label, "x_label"),
        y_label=_text(y_label, "y_label"),
        description=_text(description, "description"),
    )
    return display(
        graph,
        title=normalized_title,
        description=graph.description,
        display_id=display_id,
        durability=durability,
    )


def line(
    *,
    x: Iterable[Any],
    y: Iterable[Any],
    title: str,
    x_label: str,
    y_label: str,
    description: str,
    display_id: str | None = None,
    durability: str = "durable",
) -> DisplayHandle:
    """Display a labeled line graph using Python sequences only."""

    return _xy_graph(
        "line",
        x=x,
        y=y,
        title=title,
        x_label=x_label,
        y_label=y_label,
        description=description,
        display_id=display_id,
        durability=durability,
    )


def bar(
    *,
    x: Iterable[Any],
    y: Iterable[Any],
    title: str,
    x_label: str,
    y_label: str,
    description: str,
    display_id: str | None = None,
    durability: str = "durable",
) -> DisplayHandle:
    """Display a labeled bar graph using Python sequences only."""

    return _xy_graph(
        "bar",
        x=x,
        y=y,
        title=title,
        x_label=x_label,
        y_label=y_label,
        description=description,
        display_id=display_id,
        durability=durability,
    )


def scatter(
    *,
    x: Iterable[Any],
    y: Iterable[Any],
    title: str,
    x_label: str,
    y_label: str,
    description: str,
    display_id: str | None = None,
    durability: str = "durable",
) -> DisplayHandle:
    """Display a labeled scatter graph using Python sequences only."""

    return _xy_graph(
        "scatter",
        x=x,
        y=y,
        title=title,
        x_label=x_label,
        y_label=y_label,
        description=description,
        display_id=display_id,
        durability=durability,
    )


def histogram(
    *,
    values: Iterable[Any],
    bins: int = 10,
    title: str,
    x_label: str,
    y_label: str,
    description: str,
    display_id: str | None = None,
    durability: str = "durable",
) -> DisplayHandle:
    if isinstance(bins, bool) or not isinstance(bins, int) or not 1 <= bins <= 1_000:
        raise ValueError("bins must be an integer between 1 and 1000")
    normalized_title = _text(title, "title")
    graph = NativeGraph(
        kind="histogram",
        values=_numbers(values, "values"),
        bins=bins,
        title=normalized_title,
        x_label=_text(x_label, "x_label"),
        y_label=_text(y_label, "y_label"),
        description=_text(description, "description"),
    )
    return display(
        graph,
        title=normalized_title,
        description=graph.description,
        display_id=display_id,
        durability=durability,
    )
