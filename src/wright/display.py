"""Public value-to-display entry point."""

from __future__ import annotations

from typing import Any

from .adapters import adapt_display_value
from .client import DisplayClient, get_display_client
from .models import DisplayHandle, NativeGraph


def display(
    value: Any,
    *,
    title: str | None = None,
    description: str | None = None,
    active_html: bool = False,
    display_id: str | None = None,
    durability: str = "durable",
    client: DisplayClient | None = None,
) -> DisplayHandle:
    if durability not in {"durable", "session", "ephemeral"}:
        raise ValueError("durability must be durable, session, or ephemeral")
    normalized_title = title.strip() if title else None
    normalized_description = description.strip() if description else None
    if isinstance(value, NativeGraph):
        normalized_title = normalized_title or value.title
        normalized_description = normalized_description or value.description
    if not normalized_description:
        normalized_description = normalized_title or f"Displayed {type(value).__name__} value."
    representations = adapt_display_value(value, active_html=active_html)
    return (client or get_display_client()).send(
        representations,
        title=normalized_title,
        description=normalized_description,
        display_id=display_id,
        durability=durability,
    )
