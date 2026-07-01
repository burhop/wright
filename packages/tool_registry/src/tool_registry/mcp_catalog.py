from __future__ import annotations

from copy import deepcopy
from typing import Any

REQUIRED_PLATFORM_KEYS = (
    "windows_11_x64",
    "linux_x64",
    "linux_arm64",
    "macos_x64",
    "macos_arm64",
)

TIER_ORDER = {
    "tested": 0,
    "might_work": 1,
    "blocked": 2,
    "non_working": 3,
}

DEFAULT_PLATFORM_SUPPORT = {
    "windows_11_x64": {
        "status": "unknown",
        "tested": False,
        "notes": "not tested",
    },
    "linux_x64": {
        "status": "unknown",
        "tested": False,
        "notes": "first container target; not yet tested",
    },
    "linux_arm64": {
        "status": "unknown",
        "tested": False,
        "notes": "not tested; Linux x64 support does not imply ARM64 support",
    },
    "macos_x64": {
        "status": "unknown",
        "tested": False,
        "notes": "not tested",
    },
    "macos_arm64": {
        "status": "unknown",
        "tested": False,
        "notes": "not tested",
    },
}


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
    return {
        "status": status,
        "message": message,
        "environment": environment,
        "missing_dependencies": missing_dependencies or [],
    }


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
