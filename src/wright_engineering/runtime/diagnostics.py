"""Bounded, allowlisted, secret-safe lifecycle diagnostics."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any, Callable, Collection


_SENSITIVE_KEY = re.compile(
    r"(?:token|secret|password|passwd|api[_-]?key|authorization|credential)",
    re.IGNORECASE,
)
_ASSIGNMENT = re.compile(
    r"(?i)\b(token|secret|password|passwd|api[_-]?key|authorization)\s*[=:]\s*[^\s,;]+"
)


def redact(value: Any, *, max_string_length: int = 4096) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]"
            if _SENSITIVE_KEY.search(str(key))
            else redact(item, max_string_length=max_string_length)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple, set)):
        return [redact(item, max_string_length=max_string_length) for item in value]
    if isinstance(value, str):
        cleaned = _ASSIGNMENT.sub(lambda match: f"{match.group(1)}=[REDACTED]", value)
        if len(cleaned) > max_string_length:
            return cleaned[: max_string_length - 1] + "…"
        return cleaned
    return value


def bounded_details(
    values: Mapping[str, Any],
    *,
    allowed: Collection[str],
    max_value_length: int = 1024,
) -> dict[str, Any]:
    selected = {key: values[key] for key in allowed if key in values}
    return redact(selected, max_string_length=max_value_length)


def safe_probe(name: str, probe: Callable[[], object] | None) -> dict[str, Any]:
    """Run one bounded diagnostic probe without exposing exception content."""
    if probe is None:
        return {"ok": False, "code": f"{name}_not_configured"}
    try:
        result = probe()
        if isinstance(result, Mapping):
            return redact(dict(result), max_string_length=1024)
        return {"ok": bool(result)}
    except Exception as exc:
        return {
            "ok": False,
            "code": f"{name}_probe_failed",
            "error_type": type(exc).__name__,
        }


def run_named_probes(
    names: Collection[str], probes: Mapping[str, Callable[[], object]]
) -> dict[str, dict[str, Any]]:
    return {name: safe_probe(name, probes.get(name)) for name in names}


def core_checks_ok(
    checks: Mapping[str, object], *, require_running_health: bool
) -> bool:
    core_names = {
        "manifest",
        "compatibility",
        "runtime_containment",
        "process_ownership",
        "api",
        "ui",
        "data_permissions",
    }
    for name, value in checks.items():
        if name not in core_names:
            continue
        if name in {"api", "ui"} and not require_running_health:
            continue
        if isinstance(value, Mapping) and not bool(value.get("ok")):
            return False
    return True
