"""Application service for local previewed support-diagnostic exports."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from core.logging import get_logger
from core.tracing import traced
from .support_diagnostics import (
    CatalogSnapshotDiagnostic,
    CleanupState,
    DiagnosticCategory,
    DiagnosticDisposition,
    DiagnosticFailure,
    DiagnosticPolicyError,
    DiagnosticScope,
    DiagnosticStatus,
    DiagnosticSummary,
    ProviderDiagnostic,
    ProviderStatus,
    StateInventory,
    StorageDiagnostic,
    SupportDiagnosticSnapshot,
    build_snapshot,
    canonical_json_bytes,
    digest_value,
    require_safe_identifier,
)


logger = get_logger(__name__)

DEFAULT_PREVIEW_TTL = timedelta(minutes=5)
_COUNT_QUERIES: tuple[tuple[str, tuple[str, ...], str, bool], ...] = (
    ("capabilities", ("mcp_servers",), "SELECT COUNT(*) FROM mcp_servers", False),
    (
        "workspaces",
        ("engineering_workspaces",),
        "SELECT COUNT(*) FROM engineering_workspaces",
        False,
    ),
    (
        "bindings",
        (
            "workspace_workflow_capability_bindings",
            "workspace_workflow_binding_sets",
        ),
        """
        SELECT COUNT(*) FROM workspace_workflow_capability_bindings AS bindings
        JOIN workspace_workflow_binding_sets AS binding_sets
          ON binding_sets.binding_set_id = bindings.binding_set_id
        WHERE binding_sets.workspace_id = ?
        """,
        True,
    ),
    (
        "run_manifests",
        ("workspace_workflow_run_manifests", "workspace_workflow_runs"),
        """
        SELECT COUNT(*) FROM workspace_workflow_run_manifests AS manifests
        JOIN workspace_workflow_runs AS runs ON runs.run_id = manifests.run_id
        WHERE runs.workspace_id = ?
        """,
        True,
    ),
    (
        "scenario_reports",
        ("engineering_scenario_runs",),
        "SELECT COUNT(*) FROM engineering_scenario_runs WHERE workspace_id = ?",
        True,
    ),
    (
        "model_packages",
        ("model_installations",),
        "SELECT COUNT(*) FROM model_installations",
        False,
    ),
    (
        "model_bindings",
        ("model_capability_bindings",),
        "SELECT COUNT(*) FROM model_capability_bindings WHERE workspace_id = ?",
        True,
    ),
    (
        "model_cache",
        ("model_content_objects",),
        "SELECT COUNT(*) FROM model_content_objects",
        False,
    ),
    (
        "model_evidence",
        ("model_test_evidence",),
        "SELECT COUNT(*) FROM model_test_evidence",
        False,
    ),
)


class SupportDiagnosticError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class SupportDiagnosticPreview:
    snapshot: SupportDiagnosticSnapshot
    confirmation_token: str
    filename: str

    @property
    def expires_at(self) -> datetime:
        return self.snapshot.expires_at


@dataclass(frozen=True, slots=True)
class SupportDiagnosticExport:
    content: bytes
    filename: str


@dataclass(slots=True)
class _ExportGrant:
    token_digest: str
    principal_digest: str
    workspace_id: str
    scope_digest: str
    state_digest: str
    snapshot_digest: str
    expires_at: datetime
    filename: str
    content: bytes
    state: str = "previewed"


class SupportDiagnosticService:
    """Construct exact local snapshots and consume preview grants once."""

    def __init__(
        self,
        database_path: str | os.PathLike[str],
        *,
        clock: Callable[[], datetime] | None = None,
        token_factory: Callable[[int], str] | None = None,
        principal_digest_key: bytes | None = None,
        preview_ttl: timedelta = DEFAULT_PREVIEW_TTL,
    ) -> None:
        self.database_path = Path(database_path)
        self._clock = clock or (lambda: datetime.now(UTC))
        self._token_factory = token_factory or secrets.token_urlsafe
        self._digest_key = principal_digest_key or secrets.token_bytes(32)
        self._preview_ttl = preview_ttl
        self._grants: dict[str, _ExportGrant] = {}
        self._lock = threading.Lock()

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def _private_digest(self, value: str) -> str:
        digest = hmac.new(self._digest_key, value.encode("utf-8"), hashlib.sha256)
        return f"sha256:{digest.hexdigest()}"

    @staticmethod
    def _readonly_connection(path: Path) -> sqlite3.Connection:
        connection = sqlite3.connect(
            f"file:{path.resolve().as_posix()}?mode=ro", uri=True
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        return connection

    def _workspace_exists(self, workspace_id: str) -> bool:
        if not self.database_path.exists():
            return False
        with self._readonly_connection(self.database_path) as connection:
            row = connection.execute(
                "SELECT 1 FROM engineering_workspaces WHERE workspace_id = ?",
                (workspace_id,),
            ).fetchone()
        return row is not None

    def _scope_allowed(self, workspace_id: str, scope: DiagnosticScope) -> bool:
        with self._readonly_connection(self.database_path) as connection:
            if scope.session_id:
                session = connection.execute(
                    """
                    SELECT 1 FROM engineering_workspaces
                    WHERE workspace_id = ? AND session_id = ?
                    UNION ALL
                    SELECT 1 FROM workspace_agent_sessions
                    WHERE workspace_id = ? AND session_id = ?
                    LIMIT 1
                    """,
                    (
                        workspace_id,
                        scope.session_id,
                        workspace_id,
                        scope.session_id,
                    ),
                ).fetchone()
                if session is None:
                    return False
            if scope.scenario_run_id:
                run = connection.execute(
                    """
                    SELECT 1 FROM engineering_scenario_runs
                    WHERE workspace_id = ? AND scenario_run_id = ?
                    """,
                    (workspace_id, scope.scenario_run_id),
                ).fetchone()
                if run is None:
                    return False
        return True

    @staticmethod
    def _existing_tables(connection: sqlite3.Connection) -> set[str]:
        return {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    def _counts(self, workspace_id: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        with self._readonly_connection(self.database_path) as connection:
            existing = self._existing_tables(connection)
            for label, tables, query, workspace_scoped in _COUNT_QUERIES:
                if not set(tables) <= existing:
                    counts[label] = 0
                    continue
                if workspace_scoped:
                    row = connection.execute(query, (workspace_id,)).fetchone()
                else:
                    row = connection.execute(query).fetchone()
                counts[label] = min(int(row[0]), 1_000_000)
        return counts

    def _catalog_snapshot(self) -> CatalogSnapshotDiagnostic:
        with self._readonly_connection(self.database_path) as connection:
            existing = self._existing_tables(connection)
            if {"catalog_state", "catalog_snapshots"} <= existing:
                row = connection.execute(
                    """
                    SELECT s.channel, s.sequence, s.payload_sha256,
                           s.verification_state
                    FROM catalog_state AS state
                    JOIN catalog_snapshots AS s
                      ON s.snapshot_id = state.active_snapshot_id
                    WHERE state.state_id = 1
                    """
                ).fetchone()
                if row:
                    return CatalogSnapshotDiagnostic(
                        channel=str(row["channel"]),
                        sequence=int(row["sequence"]),
                        digest=f"sha256:{row['payload_sha256']}",
                        state="active",
                    )
        return CatalogSnapshotDiagnostic(
            channel="bundled",
            sequence=0,
            digest=digest_value("wright-bundled-catalog"),
            state="bundled",
        )

    def _inventory(self, workspace_id: str) -> StateInventory:
        counts = self._counts(workspace_id)
        catalog = self._catalog_snapshot()
        with self._readonly_connection(self.database_path) as connection:
            existing = self._existing_tables(connection)
            row = connection.execute(
                "SELECT COALESCE(MAX(version), 0) FROM wright_schema_migrations"
            ).fetchone()
            data_schema = int(row[0])
            identity_digests: dict[str, str] = {}
            identity_queries = (
                (
                    "model_catalog_material",
                    {"model_catalog_snapshots"},
                    """SELECT catalog_digest FROM model_catalog_snapshots
                       WHERE activated_at IS NOT NULL
                       ORDER BY activated_at DESC, sequence DESC LIMIT 1""",
                    (),
                ),
                (
                    "model_installation_material",
                    {"model_installations"},
                    """SELECT installation_digest FROM model_installations
                       WHERE active_revision = 1
                       ORDER BY installation_digest LIMIT 1000""",
                    (),
                ),
                (
                    "model_binding_material",
                    {"model_capability_bindings"},
                    """SELECT binding_digest FROM model_capability_bindings
                       WHERE workspace_id = ? AND state IN ('enabled','stale','blocked')
                       ORDER BY binding_digest LIMIT 1000""",
                    (workspace_id,),
                ),
                (
                    "workflow_binding_material",
                    {"workspace_workflow_binding_sets"},
                    """SELECT binding_set_digest FROM workspace_workflow_binding_sets
                       WHERE workspace_id = ? ORDER BY binding_set_digest LIMIT 1000""",
                    (workspace_id,),
                ),
                (
                    "scenario_material",
                    {"engineering_scenario_runs"},
                    """SELECT report_digest FROM engineering_scenario_runs
                       WHERE workspace_id = ? AND report_digest IS NOT NULL
                       ORDER BY created_at DESC, report_digest LIMIT 200""",
                    (workspace_id,),
                ),
                (
                    "mcp_validation_material",
                    {"mcp_validation_evidence"},
                    """SELECT COALESCE(schema_digest, evidence_id)
                       FROM mcp_validation_evidence
                       ORDER BY capability_id, evidence_id LIMIT 1000""",
                    (),
                ),
            )
            for label, tables, query, arguments in identity_queries:
                if not tables <= existing:
                    continue
                values = [str(item[0]) for item in connection.execute(query, arguments)]
                identity_digests[label] = digest_value(
                    canonical_json_bytes({"identities": values})
                )
        root_available = self.database_path.parent.exists()
        root_writable = root_available and os.access(self.database_path.parent, os.W_OK)
        material = {
            "data_schema": data_schema,
            "catalog": catalog.model_dump(mode="json"),
            "counts": counts,
            "identities": identity_digests,
        }
        identity_digests["program_material"] = digest_value(
            canonical_json_bytes(material)
        )
        return StateInventory(
            data_schema=int(material["data_schema"]),
            catalog_snapshot=catalog,
            counts=counts,
            digests=identity_digests,
            storage=(
                StorageDiagnostic(
                    root="data",
                    persistence="native-data-root",
                    available=root_available,
                    writable=root_writable,
                ),
                StorageDiagnostic(
                    root="catalog",
                    persistence="bundled-read-only",
                    available=True,
                    writable=False,
                ),
            ),
        )

    def _failures(
        self, workspace_id: str, scope: DiagnosticScope
    ) -> tuple[DiagnosticFailure, ...]:
        clauses = [
            "workspace_id = ?",
            "state IN ('blocked','failed','cancelled','error')",
        ]
        arguments: list[Any] = [workspace_id]
        if scope.session_id:
            clauses.append("session_id = ?")
            arguments.append(scope.session_id)
        if scope.scenario_run_id:
            clauses.append("scenario_run_id = ?")
            arguments.append(scope.scenario_run_id)
        with self._readonly_connection(self.database_path) as connection:
            rows = connection.execute(
                f"""
                SELECT state, cleanup_state
                FROM engineering_scenario_runs
                WHERE {" AND ".join(clauses)}
                ORDER BY created_at DESC
                LIMIT 64
                """,
                tuple(arguments),
            ).fetchall()
        failures: list[DiagnosticFailure] = []
        for row in rows:
            state = str(row["state"])
            cleanup_raw = str(row["cleanup_state"])
            cleanup = (
                CleanupState.CLEAN
                if cleanup_raw == "clean"
                else CleanupState.RESIDUE_POSSIBLE
                if cleanup_raw == "residue"
                else CleanupState.UNKNOWN
            )
            failures.append(
                DiagnosticFailure(
                    stage="engineering-scenario",
                    provider_kind="rivet",
                    reason=f"SCENARIO_{state.upper()}",
                    cleanup=cleanup,
                    recovery=(
                        "INSPECT_BEFORE_RETRY"
                        if cleanup != CleanupState.CLEAN
                        else "REVIEW_PROVIDER_STATUS"
                    ),
                )
            )
        return tuple(failures)

    @staticmethod
    def _runtime_version() -> str:
        try:
            return version("wright-engineering")
        except PackageNotFoundError:
            return "development"

    def _providers(
        self, inventory: StateInventory, failures: tuple[DiagnosticFailure, ...]
    ) -> tuple[ProviderDiagnostic, ...]:
        failure_kinds = {failure.provider_kind for failure in failures}
        return (
            ProviderDiagnostic(
                kind="runtime",
                provider_id="wright-runtime",
                status=ProviderStatus.READY,
                identity_digest=digest_value(
                    f"{self._runtime_version()}:{inventory.data_schema}"
                ),
            ),
            ProviderDiagnostic(
                kind="rivet",
                provider_id="wright-rivet",
                status=(
                    ProviderStatus.FAILED
                    if "rivet" in failure_kinds
                    else ProviderStatus.READY
                ),
                identity_digest=digest_value(
                    f"rivet:{inventory.counts.get('run_manifests', 0)}"
                ),
            ),
            ProviderDiagnostic(
                kind="storage",
                provider_id="wright-data-vault",
                status=(
                    ProviderStatus.READY
                    if inventory.storage[0].available and inventory.storage[0].writable
                    else ProviderStatus.BLOCKED
                ),
                identity_digest=inventory.digests["program_material"],
            ),
        )

    @traced("support_diagnostics.preview")
    def preview(
        self,
        *,
        principal_id: str,
        workspace_id: str,
        scope: Mapping[str, Any] | DiagnosticScope | None = None,
    ) -> SupportDiagnosticPreview:
        try:
            require_safe_identifier(principal_id, code="INVALID_PRINCIPAL")
            require_safe_identifier(workspace_id)
            resolved_scope = (
                scope
                if isinstance(scope, DiagnosticScope)
                else DiagnosticScope.model_validate(scope or {})
            )
        except (DiagnosticPolicyError, ValueError) as exc:
            raise SupportDiagnosticError("INVALID_DIAGNOSTIC_SCOPE") from exc
        if not self._workspace_exists(workspace_id):
            raise SupportDiagnosticError("WORKSPACE_NOT_FOUND")
        if not self._scope_allowed(workspace_id, resolved_scope):
            raise SupportDiagnosticError("DIAGNOSTIC_SCOPE_FORBIDDEN")

        now = self._now()
        expires_at = now + self._preview_ttl
        inventory = self._inventory(workspace_id)
        failures = self._failures(workspace_id, resolved_scope)
        providers = self._providers(inventory, failures)
        categories = (
            DiagnosticCategory(
                name="program-state",
                disposition=DiagnosticDisposition.INCLUDED,
                item_count=sum(inventory.counts.values()),
                reason="INCLUDED",
            ),
            DiagnosticCategory(
                name="provider-status",
                disposition=DiagnosticDisposition.INCLUDED,
                item_count=len(providers),
                reason="INCLUDED",
            ),
            DiagnosticCategory(
                name="failure-summaries",
                disposition=DiagnosticDisposition.INCLUDED,
                item_count=len(failures),
                reason="INCLUDED",
            ),
            DiagnosticCategory(
                name="raw-engineering-payloads",
                disposition=DiagnosticDisposition.OMITTED,
                item_count=0,
                reason="PROPRIETARY_CONTENT_FORBIDDEN",
            ),
            DiagnosticCategory(
                name="secrets-and-authority",
                disposition=DiagnosticDisposition.REDACTED,
                item_count=0,
                reason="REUSABLE_AUTHORITY_FORBIDDEN",
            ),
            DiagnosticCategory(
                name="private-paths",
                disposition=DiagnosticDisposition.REDACTED,
                item_count=0,
                reason="PRIVATE_PATHS_FORBIDDEN",
            ),
        )
        snapshot_id = self._token_factory(18)
        confirmation_token = self._token_factory(32)
        principal_digest = self._private_digest(principal_id)
        snapshot = build_snapshot(
            {
                "schema_version": "1.0",
                "snapshot_id": snapshot_id,
                "created_at": now,
                "expires_at": expires_at,
                "workspace_id": workspace_id,
                "principal_digest": principal_digest,
                "scope": resolved_scope,
                "summary": DiagnosticSummary(
                    status=(
                        DiagnosticStatus.DEGRADED
                        if failures
                        else DiagnosticStatus.HEALTHY
                    ),
                    reason="FAILURES_RECORDED" if failures else "READY",
                    next_action=(
                        "INSPECT_RECOVERY"
                        if failures
                        else "CONTINUE_ENGINEERING_JOURNEY"
                    ),
                ),
                "providers": providers,
                "state_inventory": inventory,
                "failures": failures,
                "categories": categories,
            }
        )
        content = snapshot.export_bytes()
        filename_workspace = re_safe_filename(workspace_id)
        filename = (
            f"wright-support-{filename_workspace}-{now.strftime('%Y%m%dT%H%M%SZ')}.json"
        )
        scope_digest = digest_value(
            canonical_json_bytes(
                resolved_scope.model_dump(mode="json", exclude_none=True)
            )
        )
        token_digest = self._private_digest(confirmation_token)
        grant = _ExportGrant(
            token_digest=token_digest,
            principal_digest=principal_digest,
            workspace_id=workspace_id,
            scope_digest=scope_digest,
            state_digest=inventory.digests["program_material"],
            snapshot_digest=snapshot.snapshot_digest,
            expires_at=expires_at,
            filename=filename,
            content=content,
        )
        with self._lock:
            self._expire_locked(now)
            self._grants[token_digest] = grant
        logger.info(
            "support_diagnostic_preview_created",
            workspace_digest=self._private_digest(workspace_id),
            snapshot_digest=snapshot.snapshot_digest,
            provider_count=len(providers),
            failure_count=len(failures),
            export_bytes=len(content),
        )
        return SupportDiagnosticPreview(snapshot, confirmation_token, filename)

    def _expire_locked(self, now: datetime) -> None:
        for grant in self._grants.values():
            if grant.state == "previewed" and now >= grant.expires_at:
                grant.state = "expired"

    @traced("support_diagnostics.export")
    def export(
        self,
        *,
        principal_id: str,
        workspace_id: str,
        snapshot_digest: str,
        confirmation_token: str,
    ) -> SupportDiagnosticExport:
        token_digest = self._private_digest(confirmation_token)
        principal_digest = self._private_digest(principal_id)
        now = self._now()
        with self._lock:
            self._expire_locked(now)
            grant = self._grants.get(token_digest)
            if grant is None:
                raise SupportDiagnosticError("DIAGNOSTIC_EXPORT_DENIED")
            if grant.state == "expired":
                raise SupportDiagnosticError("DIAGNOSTIC_PREVIEW_EXPIRED")
            comparisons = (
                hmac.compare_digest(grant.token_digest, token_digest),
                hmac.compare_digest(grant.principal_digest, principal_digest),
                hmac.compare_digest(grant.workspace_id, workspace_id),
                hmac.compare_digest(grant.snapshot_digest, snapshot_digest),
            )
            if grant.state != "previewed" or not all(comparisons):
                raise SupportDiagnosticError("DIAGNOSTIC_EXPORT_DENIED")
        current_state_digest = (
            self._inventory(workspace_id).digests["program_material"]
            if self._workspace_exists(workspace_id)
            else ""
        )
        with self._lock:
            self._expire_locked(self._now())
            grant = self._grants.get(token_digest)
            if grant is not None and grant.state == "expired":
                raise SupportDiagnosticError("DIAGNOSTIC_PREVIEW_EXPIRED")
            if grant is None or grant.state != "previewed":
                raise SupportDiagnosticError("DIAGNOSTIC_EXPORT_DENIED")
            if not hmac.compare_digest(grant.state_digest, current_state_digest):
                grant.state = "invalidated"
                raise SupportDiagnosticError("DIAGNOSTIC_PREVIEW_STALE")
            grant.state = "consumed"
            content = grant.content
            filename = grant.filename
        logger.info(
            "support_diagnostic_export_consumed",
            workspace_digest=self._private_digest(workspace_id),
            snapshot_digest=snapshot_digest,
            export_bytes=len(content),
        )
        return SupportDiagnosticExport(content=content, filename=filename)

    def invalidate_all(self) -> None:
        with self._lock:
            for grant in self._grants.values():
                if grant.state == "previewed":
                    grant.state = "invalidated"


def re_safe_filename(value: str) -> str:
    cleaned = "".join(
        character if character.isalnum() or character in "-_" else "-"
        for character in value
    )
    return cleaned[:64] or "workspace"
