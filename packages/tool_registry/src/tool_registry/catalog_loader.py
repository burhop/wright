from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .catalog_models import CatalogEntry, TIER_ORDER, default_platform_support_dict
from .catalog_models import validation_summary_dict


def normalize_mcp_seed_entry(
    entry: dict[str, Any], metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    merged = dict(entry)
    merged.setdefault("verification_state", "user_reported_url_needed")
    merged.setdefault("installability_tier", "might_work")
    merged.setdefault("risk_level", "low")
    merged.setdefault("deployment_mode", "unknown")
    merged.setdefault("platform_support", default_platform_support_dict())
    merged.setdefault("host_software_required", [])
    merged.setdefault("credentials_required", [])
    merged.setdefault("default_enabled", True)
    merged.setdefault("approval_gates", [])
    merged.setdefault("validation_result", validation_summary_dict())
    merged.setdefault("follow_up_url", None)
    merged.setdefault("install_blocked_reason", None)
    if metadata:
        merged.update(metadata)
    if merged["risk_level"] in {"medium", "high", "safety-critical"}:
        merged["default_enabled"] = False
    return merged


def catalog_entry_to_mcp_seed(entry: CatalogEntry) -> dict[str, Any]:
    command = entry.command
    if entry.transport == "webmcp" and command == []:
        command = None

    return normalize_mcp_seed_entry(
        {
            "server_id": entry.id,
            "name": entry.name,
            "type": entry.transport,
            "command": command,
            "category": entry.domains[0] if entry.domains else "utilities",
            "image_url": entry.image_url,
            "description": entry.description,
            "source_url": entry.source_url,
            "env_vars": entry.env_vars,
            "instructions": None,
            "installed_version": None,
            "verification_state": entry.verification_state,
            "installability_tier": entry.installability_tier,
            "risk_level": entry.risk_level,
            "deployment_mode": entry.deployment_mode,
            "platform_support": {
                key: value.model_dump() for key, value in entry.platform_support.items()
            },
            "host_software_required": entry.host_software_required,
            "credentials_required": entry.credentials_required,
            "default_enabled": entry.default_enabled,
            "approval_gates": entry.approval_gates,
            "validation_result": entry.validation_result.model_dump(),
            "follow_up_url": entry.follow_up_url,
            "install_blocked_reason": entry.install_blocked_reason,
        }
    )


def load_catalog_entries(catalog_path: str | Path) -> list[CatalogEntry]:
    path = Path(catalog_path)
    if not path.exists():
        raise FileNotFoundError(f"Catalog file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    entries: list[CatalogEntry] = []
    seen_ids: set[str] = set()
    for entry_dict in data.get("servers", []):
        entry = CatalogEntry.model_validate(entry_dict)
        if entry.id in seen_ids:
            raise ValueError(f"Duplicate catalog entry ID found: {entry.id}")
        seen_ids.add(entry.id)
        entries.append(entry)
    return entries


def sort_catalog_entries(entries: list[Any]) -> list[Any]:
    return sorted(
        entries,
        key=lambda entry: (
            TIER_ORDER.get(getattr(entry, "installability_tier", None), 99),
            getattr(entry, "name", "").lower(),
        ),
    )
