from __future__ import annotations

import base64
import hashlib
import json
import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from .capability_models import (
    CapabilityCompatibility,
    CapabilityList,
    CapabilitySnapshotSummary,
    CapabilityUserState,
    CapabilityView,
)
from .canonical_catalog import LEGACY_SERVER_IDS
from .catalog_models import CatalogEntry, PlatformSupportRecord
from .compatibility import evaluate_compatibility
from .models import McpServer

EVIDENCE_RANK = {
    "official_production": 0,
    "official_preview": 1,
    "verified_community": 2,
    "community_candidate": 3,
    "documentation_only": 4,
    "api_wrapper_candidate": 5,
    "user_reported_source_needed": 6,
    "blocked_validation": 7,
    "excluded_or_stale": 8,
}
INSTALLABILITY_RANK = {"tested": 0, "might_work": 1, "blocked": 2, "non_working": 3}
BUNDLED_UPDATED_AT = datetime(2026, 8, 12, tzinfo=UTC)


class CapabilityCursorError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class CapabilityFilters:
    search: str | None = None
    domains: frozenset[str] = field(default_factory=frozenset)
    platforms: frozenset[str] = field(default_factory=frozenset)
    evidence_classes: frozenset[str] = field(default_factory=frozenset)
    compatibility: frozenset[str] = field(default_factory=frozenset)
    risks: frozenset[str] = field(default_factory=frozenset)
    localities: frozenset[str] = field(default_factory=frozenset)
    hosts: frozenset[str] = field(default_factory=frozenset)
    validation: frozenset[str] = field(default_factory=frozenset)
    installed: bool | None = None


def _canonical_digest(entries: Sequence[CatalogEntry]) -> str:
    payload = [entry.model_dump(mode="json") for entry in entries]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def bundled_snapshot_summary(
    entries: Sequence[CatalogEntry],
) -> CapabilitySnapshotSummary:
    return CapabilitySnapshotSummary(
        snapshot_id=f"bundled-{_canonical_digest(entries)[:20]}",
        channel="bundled",
        sequence=1,
        offline=True,
        updated_at=BUNDLED_UPDATED_AT,
    )


def _catalog_server_id(entry: CatalogEntry) -> str:
    return LEGACY_SERVER_IDS.get(entry.id, entry.id)


def _server_index(servers: Iterable[McpServer]) -> dict[str, McpServer]:
    return {server.server_id: server for server in servers}


def _has_user_owned_state(
    server: McpServer,
    workspace_membership: Mapping[str, list[dict[str, str]]],
) -> bool:
    return bool(
        server.is_installed
        or server.is_active
        or server.status != "inactive"
        or server.error_message
        or server.installed_version
        or any((server.credentials_configured or {}).values())
        or workspace_membership.get(server.server_id)
        or workspace_membership.get(server.name)
    )


def load_workspace_membership(
    database_path: str | Path,
) -> dict[str, list[dict[str, str]]]:
    membership: dict[str, list[dict[str, str]]] = {}
    try:
        with sqlite3.connect(str(database_path)) as connection:
            rows = connection.execute(
                """SELECT workspace_id, workspace_name, enabled_tools
                   FROM engineering_workspaces WHERE enabled_tools IS NOT NULL"""
            ).fetchall()
    except sqlite3.OperationalError:
        return membership
    for workspace_id, workspace_name, raw in rows:
        try:
            enabled = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            continue
        if not isinstance(enabled, list):
            continue
        workspace = {
            "workspace_id": str(workspace_id),
            "label": str(workspace_name or workspace_id),
        }
        for identity in enabled:
            if isinstance(identity, str):
                membership.setdefault(identity, []).append(workspace)
    return membership


def _user_state(
    server: McpServer | None, workspace_membership: Mapping[str, list[dict[str, str]]]
) -> CapabilityUserState:
    if server is None:
        return CapabilityUserState()
    configured = server.credentials_configured or {}
    workspaces = workspace_membership.get(server.server_id) or workspace_membership.get(
        server.name, []
    )
    return CapabilityUserState(
        server_id=server.server_id,
        installed=server.is_installed,
        active=server.is_active,
        process_status=server.status,
        explicit_disabled=server.is_installed and not server.is_active,
        installed_version=server.installed_version,
        credentials_configured={
            str(name): bool(value) for name, value in configured.items()
        },
        enabled_workspaces=sorted(workspaces, key=lambda item: item["workspace_id"]),
    )


def _available_actions(
    entry: CatalogEntry,
    compatibility: CapabilityCompatibility,
    user: CapabilityUserState,
) -> list[str]:
    actions = ["view_details", "observe"]
    if entry.installability_tier not in {"blocked", "non_working"}:
        actions.append("plan_onboarding")
    if user.installed:
        actions.append("manage_installation")
        actions.append("enable_in_workspace")
    if entry.source_url:
        actions.append("open_source")
    return actions


def _catalog_view(
    entry: CatalogEntry,
    server: McpServer | None,
    observation,
    workspace_membership: Mapping[str, list[dict[str, str]]],
) -> CapabilityView:
    compatibility = evaluate_compatibility(entry, observation)
    user = _user_state(server, workspace_membership)
    return CapabilityView(
        capability_id=entry.id,
        canonical_id=entry.id,
        name=entry.name,
        vendor=entry.vendor,
        description=entry.description,
        domains=entry.domains,
        tags=entry.tags,
        aliases=sorted(entry.aliases),
        capability_summary=entry.capability_summary,
        evidence_class=entry.evidence_class or "community_candidate",
        transport=entry.transport,
        locality=entry.locality,
        risk_level=entry.risk_level,
        installability_tier=entry.installability_tier,
        compatibility=compatibility,
        source_records=[
            record.model_dump(mode="json") for record in entry.source_records
        ],
        requirements={
            "runtime": entry.runtime_requirements.model_dump(mode="json"),
            "dependencies": entry.dependencies.model_dump(mode="json"),
            "host_software": entry.host_software_required,
            "credentials": entry.credentials_required,
            "license": entry.license,
            "approval_gates": entry.approval_gates,
        },
        validation_result=entry.validation_result.model_dump(mode="json"),
        user_state=user,
        custom=False,
        available_actions=_available_actions(entry, compatibility, user),
    )


def _custom_entry(server: McpServer, observation) -> CatalogEntry:
    support = {
        key: value
        if isinstance(value, PlatformSupportRecord)
        else PlatformSupportRecord.model_validate(
            value.model_dump() if hasattr(value, "model_dump") else value
        )
        for key, value in server.platform_support.items()
    }
    return CatalogEntry(
        id=server.server_id,
        name=server.name,
        vendor="User configured",
        description=server.description or "Locally registered custom MCP server.",
        domains=[server.category],
        tags=["custom"],
        transport=server.transport_variant or server.type,
        command=server.command or [],
        source_url=server.source_url,
        locality="remote" if server.type == "sse" else "local",
        weight="light",
        verification_state="user_reported_url_needed",
        evidence_class="user_reported_source_needed",
        installability_tier=server.installability_tier,
        risk_level=server.risk_level,
        deployment_mode=server.deployment_mode,
        platform_support=support,
        host_software_required=server.host_software_required,
        credentials_required=server.credentials_required,
        default_enabled=server.default_enabled,
        approval_gates=server.approval_gates,
        validation_result=server.validation_result.model_dump(),
    )


def build_capability_views(
    entries: Sequence[CatalogEntry],
    servers: Sequence[McpServer],
    observation,
    *,
    workspace_membership: Mapping[str, list[dict[str, str]]] | None = None,
    known_catalog_ids: frozenset[str] = frozenset(),
) -> list[CapabilityView]:
    membership = workspace_membership or {}
    indexed = _server_index(servers)
    consumed: set[str] = set()
    views: list[CapabilityView] = []
    for entry in entries:
        identities = [_catalog_server_id(entry), entry.id, *entry.aliases]
        server = next((indexed[key] for key in identities if key in indexed), None)
        if server:
            consumed.add(server.server_id)
        views.append(_catalog_view(entry, server, observation, membership))

    for server in servers:
        if server.server_id in consumed:
            continue
        if server.server_id in known_catalog_ids and not _has_user_owned_state(
            server, membership
        ):
            continue
        entry = _custom_entry(server, observation)
        view = _catalog_view(entry, server, observation, membership)
        view.custom = True
        views.append(view)

    compatible_by_domain: dict[str, list[str]] = {}
    for view in views:
        if view.compatibility.status == "compatible":
            for domain in view.domains:
                compatible_by_domain.setdefault(domain, []).append(view.capability_id)
    for view in views:
        if view.compatibility.status == "compatible":
            continue
        candidates: list[str] = []
        for domain in view.domains:
            candidates.extend(compatible_by_domain.get(domain, []))
        view.alternatives = sorted(set(candidates) - {view.capability_id})[:3]

    return sorted(
        views,
        key=lambda view: (
            EVIDENCE_RANK.get(view.evidence_class, 99),
            INSTALLABILITY_RANK.get(view.installability_tier, 99),
            view.name.casefold(),
            view.canonical_id,
        ),
    )


def _search_text(view: CapabilityView) -> str:
    source_text = " ".join(
        f"{source.get('url', '')} {source.get('notes', '')}"
        for source in view.source_records
    )
    requirements = json.dumps(view.requirements, sort_keys=True)
    return " ".join(
        [
            view.name,
            view.vendor,
            view.description,
            *view.aliases,
            *view.domains,
            *view.tags,
            *view.capability_summary,
            source_text,
            requirements,
        ]
    ).casefold()


def _matches(view: CapabilityView, filters: CapabilityFilters) -> bool:
    if filters.search and filters.search.casefold() not in _search_text(view):
        return False
    if filters.domains and not filters.domains.intersection(view.domains):
        return False
    if filters.platforms and view.compatibility.platform_key not in filters.platforms:
        return False
    if filters.evidence_classes and view.evidence_class not in filters.evidence_classes:
        return False
    if filters.compatibility and view.compatibility.status not in filters.compatibility:
        return False
    if filters.risks and view.risk_level not in filters.risks:
        return False
    if filters.localities and view.locality not in filters.localities:
        return False
    hosts = set(view.requirements.get("host_software", []))
    if filters.hosts and not filters.hosts.intersection(hosts):
        return False
    validation = str(view.validation_result.get("status", "not_tested"))
    if filters.validation and validation not in filters.validation:
        return False
    if filters.installed is not None and view.user_state.installed != filters.installed:
        return False
    return True


def _decode_cursor(cursor: str | None) -> int:
    if cursor is None:
        return 0
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii") + b"===").decode("ascii")
        offset = int(raw)
    except (ValueError, UnicodeError) as error:
        raise CapabilityCursorError("Invalid capability cursor") from error
    if offset < 0:
        raise CapabilityCursorError("Invalid capability cursor")
    return offset


def _encode_cursor(offset: int) -> str:
    return (
        base64.urlsafe_b64encode(str(offset).encode("ascii"))
        .decode("ascii")
        .rstrip("=")
    )


def paginate_capabilities(
    entries: Sequence[CatalogEntry],
    views: Sequence[CapabilityView],
    *,
    filters: CapabilityFilters | None = None,
    limit: int = 100,
    cursor: str | None = None,
    snapshot: CapabilitySnapshotSummary | None = None,
) -> CapabilityList:
    selected = [
        view for view in views if _matches(view, filters or CapabilityFilters())
    ]
    offset = _decode_cursor(cursor)
    page = selected[offset : offset + limit]
    next_offset = offset + len(page)
    return CapabilityList(
        snapshot=snapshot or bundled_snapshot_summary(entries),
        capabilities=page,
        next_cursor=_encode_cursor(next_offset)
        if next_offset < len(selected)
        else None,
        total=len(selected),
    )


def find_capability(
    views: Sequence[CapabilityView], identity: str
) -> CapabilityView | None:
    matches = [
        view
        for view in views
        if identity in {view.capability_id, view.canonical_id, *view.aliases}
        or identity == view.user_state.server_id
    ]
    return matches[0] if len(matches) == 1 else None
