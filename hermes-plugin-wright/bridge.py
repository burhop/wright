"""Removed repository bridge retained only for an actionable migration error."""

from __future__ import annotations


WRIGHT_API_BASE = "http://127.0.0.1:8000"
WRIGHT_UI_URL = f"{WRIGHT_API_BASE}/"


class LegacyBridgeRemoved(RuntimeError):
    pass


def migration_required() -> None:
    raise LegacyBridgeRemoved(
        "The repository-backed Wright bridge was removed. Install the public "
        "wright-engineering plugin through Hermes and use /wright start."
    )


__all__ = [
    "LegacyBridgeRemoved",
    "WRIGHT_API_BASE",
    "WRIGHT_UI_URL",
    "migration_required",
]
