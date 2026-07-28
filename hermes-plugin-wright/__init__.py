"""One-release compatibility delegate for legacy Git-installed Wright users."""

from __future__ import annotations

try:
    from wright_engineering.hermes_plugin import register
except ImportError as exc:  # pragma: no cover - exercised in legacy installs
    raise RuntimeError(
        "This legacy Wright plugin mirror now delegates to the public "
        "wright-engineering distribution. Install Wright through Hermes' "
        "supported package-plugin channel and retry."
    ) from exc


__all__ = ["register"]
