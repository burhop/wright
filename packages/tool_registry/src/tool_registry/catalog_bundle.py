from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .canonical_catalog import load_canonical_entries
from .catalog_models import CatalogEntry
from .catalog_platforms import (
    SelectionMode,
    platform_selection_reason,
    resolve_platform_profile,
)


@dataclass(frozen=True)
class BundleCatalogIssue:
    server_id: str
    catalog_id: str | None
    reason: str


def _entries_by_id(entries: list[CatalogEntry]) -> dict[str, CatalogEntry]:
    return {entry.id: entry for entry in entries}


def bundle_catalog_issues(
    bundle: dict[str, Any],
    *,
    entries: list[CatalogEntry] | None = None,
    target: str | None = None,
    mode: SelectionMode | None = None,
    require_docker: bool | None = None,
) -> list[BundleCatalogIssue]:
    target_platform = target or bundle.get("target_platform")
    if not isinstance(target_platform, str) or not target_platform.strip():
        return []

    policy = (
        bundle.get("catalog_policy")
        if isinstance(bundle.get("catalog_policy"), dict)
        else {}
    )
    selection_mode = mode or policy.get("mode") or "candidate"
    docker_required = require_docker
    if docker_required is None:
        docker_required = bool(policy.get("require_docker", True))

    profile = resolve_platform_profile(target_platform)
    catalog_entries = _entries_by_id(entries or load_canonical_entries())
    issues: list[BundleCatalogIssue] = []
    for server in bundle.get("mcp_servers", []):
        if (
            not isinstance(server, dict)
            or server.get("availability") != "local_enabled"
        ):
            continue
        server_id = server.get("id")
        catalog_id = server.get("catalog_id") or server_id
        if not isinstance(server_id, str) or not isinstance(catalog_id, str):
            issues.append(
                BundleCatalogIssue(
                    server_id=str(server_id),
                    catalog_id=None,
                    reason="local_enabled MCP server must declare id and catalog_id",
                )
            )
            continue
        catalog_entry = catalog_entries.get(catalog_id)
        if catalog_entry is None:
            issues.append(
                BundleCatalogIssue(
                    server_id=server_id,
                    catalog_id=catalog_id,
                    reason="catalog entry not found",
                )
            )
            continue
        reason = platform_selection_reason(
            catalog_entry,
            profile,
            mode=selection_mode,
            require_docker=docker_required,
        )
        if reason:
            issues.append(
                BundleCatalogIssue(
                    server_id=server_id,
                    catalog_id=catalog_id,
                    reason=reason,
                )
            )
    return issues


def validate_bundle_catalog_compatibility(
    bundle: dict[str, Any],
    *,
    entries: list[CatalogEntry] | None = None,
    target: str | None = None,
    mode: SelectionMode | None = None,
    require_docker: bool | None = None,
) -> None:
    issues = bundle_catalog_issues(
        bundle,
        entries=entries,
        target=target,
        mode=mode,
        require_docker=require_docker,
    )
    if issues:
        details = "; ".join(
            f"{issue.server_id} -> {issue.catalog_id}: {issue.reason}"
            for issue in issues
        )
        raise ValueError(f"MCP bundle catalog compatibility failed: {details}")
