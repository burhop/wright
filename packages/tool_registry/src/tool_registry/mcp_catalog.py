from __future__ import annotations

from copy import deepcopy
from typing import Any

from .catalog_models import (
    DEFAULT_PLATFORM_SUPPORT,
    REQUIRED_PLATFORM_KEYS,
    TIER_ORDER,
    validation_summary_dict,
)


def platform_support(
    overrides: dict[str, dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    support = deepcopy(DEFAULT_PLATFORM_SUPPORT)
    for key, value in (overrides or {}).items():
        if key in support:
            support[key].update(value)
    return support


def validation_summary(
    status: str = "not_tested",
    message: str = "Not yet validated in this environment",
    environment: str | None = None,
    missing_dependencies: list[str] | None = None,
) -> dict[str, Any]:
    return validation_summary_dict(status, message, environment, missing_dependencies)


def tier_sort_key(server: Any) -> tuple[int, str]:
    tier = getattr(server, "installability_tier", None)
    name = getattr(server, "name", "") or getattr(server, "display_name", "")
    if isinstance(server, dict):
        tier = server.get("installability_tier")
        name = server.get("name") or server.get("display_name") or ""
    return (TIER_ORDER.get(tier, 99), str(name).lower())


def is_install_blocked(server: Any) -> bool:
    tier = getattr(server, "installability_tier", None)
    if isinstance(server, dict):
        tier = server.get("installability_tier")
    return tier in {"blocked", "non_working"}
