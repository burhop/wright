"""Production registry and host adapters for managed surface applications."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlunsplit

import httpx
from data_vault import connect_state_db

from ..config import WorkspaceSurfaceSettings
from .endpoints import LoopbackEndpointAllocator, PsutilListenerInspector
from .health import HealthProber, ProbeResponse
from .live_app_manager import LiveAppManager, LiveAppManagerError
from .manifests import WorkspaceManifestStore
from .manifests import DiscoveredManifest
from .process_posix import PosixProcessAdapter
from .process_supervisor import ProcessSupervisor
from .process_windows import WindowsProcessAdapter
from .revocation import RevocationCoordinator
from .target_pins import TargetPinRegistry
from .target_policy import TargetPolicy
from .limits import SurfaceLimitPolicy


class SqliteLiveAppPersistence:
    """Durably snapshot runtime intent, identity, limits, and active target pins."""

    def __init__(
        self,
        db_path: str | Path,
        *,
        supervisor: ProcessSupervisor,
        target_pins: TargetPinRegistry,
        limit_policy: SurfaceLimitPolicy,
        platform_hint: str,
    ) -> None:
        self.db_path = str(db_path)
        self.supervisor = supervisor
        self.target_pins = target_pins
        self.limit_policy = limit_policy
        self.platform_hint = platform_hint

    @staticmethod
    def _json(value) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"))

    def __call__(self, instance, declaration: DiscoveredManifest) -> None:
        identity = None
        if instance.runtime_id is not None and instance.ownership == "launched":
            try:
                snapshot = self.supervisor.snapshot(instance.runtime_id)
            except Exception:
                snapshot = None
            if snapshot is not None:
                value = snapshot.identity
                identity = {
                    "adapter": value.adapter,
                    "pid": value.pid,
                    "creationTime": value.creation_time,
                    "containmentId": value.containment_id,
                    "containmentMode": value.containment_mode,
                    "executable": value.executable,
                    "commandDigest": value.command_digest,
                }
        target = None
        try:
            active = self.target_pins.resolve(
                instance_id=instance.instance_id, generation=instance.generation
            )
        except Exception:
            active = None
        if active is not None:
            value = active.target
            target = {
                "scheme": value.scheme,
                "numericAddress": value.numeric_address,
                "port": value.port,
                "sourceHostname": value.source_hostname,
                "hostHeader": value.host_header,
                "serverName": value.server_name,
                "basePath": value.base_path,
                "ownership": value.ownership,
                "ownershipProof": value.ownership_proof,
            }
        limits = self.limit_policy.compose(
            declared=declaration.manifest.limits.as_policy_mapping()
        ).as_mapping()
        lifetime = {
            "policy": instance.lifetime_policy,
            "leaseExpiresAt": (
                instance.lease_expires_at.isoformat()
                if instance.lease_expires_at is not None
                else None
            ),
            "idleSeconds": instance.idle_seconds,
            "lastActivityAt": instance.last_activity_at.isoformat(),
        }
        now = datetime.now(UTC).isoformat()
        durable_id = f"surface-runtime:{instance.instance_id}"
        platform = instance.platform or self.platform_hint
        with connect_state_db(self.db_path) as connection:
            current = connection.execute(
                "SELECT revision, created_at FROM surface_runtimes WHERE instance_id=?",
                (instance.instance_id,),
            ).fetchone()
            revision = 1 if current is None else int(current["revision"]) + 1
            created_at = now if current is None else str(current["created_at"])
            connection.execute(
                """INSERT INTO surface_runtimes (
                    runtime_id, instance_id, surface_id, workspace_id,
                    generation, ownership, platform, state,
                    process_identity_json, manifest_hash, lifetime_json,
                    limits_json, target_pin_json, revision, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(instance_id) DO UPDATE SET
                    generation=excluded.generation,
                    ownership=excluded.ownership,
                    platform=excluded.platform,
                    state=excluded.state,
                    process_identity_json=excluded.process_identity_json,
                    manifest_hash=excluded.manifest_hash,
                    lifetime_json=excluded.lifetime_json,
                    limits_json=excluded.limits_json,
                    target_pin_json=excluded.target_pin_json,
                    revision=excluded.revision,
                    updated_at=excluded.updated_at""",
                (
                    durable_id,
                    instance.instance_id,
                    instance.surface_id,
                    instance.workspace_id,
                    instance.generation,
                    instance.ownership,
                    platform,
                    instance.state,
                    None if identity is None else self._json(identity),
                    instance.manifest_hash,
                    self._json(lifetime),
                    self._json(limits),
                    None if target is None else self._json(target),
                    revision,
                    created_at,
                    now,
                ),
            )
            connection.commit()


class HttpxProbeTransport:
    """Bounded health transport that connects only to an already pinned address."""

    def __init__(self, *, client: httpx.AsyncClient | None = None) -> None:
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=None, follow_redirects=False)

    async def request(self, *, target, probe, timeout_seconds: float) -> ProbeResponse:
        host = (
            f"[{target.numeric_address}]"
            if ":" in target.numeric_address
            else target.numeric_address
        )
        url = urlunsplit(
            (
                target.scheme,
                f"{host}:{target.port}",
                probe.path,
                "",
                "",
            )
        )
        request = self._client.build_request(
            probe.method,
            url,
            headers={"Host": target.host_header, "Accept": "*/*"},
        )
        if target.server_name:
            request.extensions["sni_hostname"] = target.server_name.encode("ascii")
        response = await asyncio.wait_for(
            self._client.send(request, stream=True), timeout=timeout_seconds
        )
        body_bytes = 0
        try:
            async with asyncio.timeout(timeout_seconds):
                async for chunk in response.aiter_raw():
                    body_bytes = min(4096, body_bytes + len(chunk))
                    if body_bytes >= 4096:
                        break
            return ProbeResponse(status=response.status_code, body_bytes=body_bytes)
        finally:
            await response.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()


class LiveAppRuntimeRegistry:
    """Own one isolated manager graph per active workspace."""

    def __init__(
        self,
        db_path: str | Path,
        *,
        settings: WorkspaceSurfaceSettings,
        revocation: RevocationCoordinator,
        monitor_seconds: float = 2.0,
    ) -> None:
        if monitor_seconds <= 0:
            raise ValueError("runtime monitor interval must be positive")
        self.db_path = str(db_path)
        self.settings = settings
        self.revocation = revocation
        self.monitor_seconds = monitor_seconds
        self._transport = HttpxProbeTransport()
        self._managers: dict[str, LiveAppManager] = {}
        self._monitor_task: asyncio.Task[None] | None = None
        self._accepting = True
        self._shutdown = False

    def _workspace_root(self, workspace_id: str) -> Path:
        with connect_state_db(self.db_path) as connection:
            row = connection.execute(
                "SELECT local_path FROM engineering_workspaces WHERE workspace_id=?",
                (workspace_id,),
            ).fetchone()
        if row is None:
            raise LiveAppManagerError(
                "SURFACE_WORKSPACE_NOT_FOUND",
                "Managed application workspace was not found",
            )
        root = Path(str(row["local_path"])).resolve()
        if not root.is_dir():
            raise LiveAppManagerError(
                "SURFACE_WORKSPACE_UNAVAILABLE",
                "Managed application workspace directory is unavailable",
            )
        return root

    def _public_origin(self, _workspace_id: str, instance_id: str) -> str:
        digest = hashlib.sha256(instance_id.encode("utf-8")).hexdigest()[:32]
        hostname = f"r-{digest}.{self.settings.preview.domain}"
        default_port = 443 if self.settings.preview.scheme == "https" else 80
        authority = (
            hostname
            if self.settings.preview.public_port == default_port
            else f"{hostname}:{self.settings.preview.public_port}"
        )
        return urlunsplit((self.settings.preview.scheme, authority, "", "", ""))

    def manager_for(self, workspace_id: str) -> LiveAppManager:
        if not self._accepting:
            raise LiveAppManagerError(
                "SURFACE_RUNTIME_SHUTTING_DOWN",
                "Managed application runtime is shutting down",
            )
        manager = self._managers.get(workspace_id)
        if manager is not None:
            return manager
        root = self._workspace_root(workspace_id)
        target_policy = TargetPolicy()
        target_pins = TargetPinRegistry(policy=target_policy)
        platform_hint = "windows_job" if os.name == "nt" else "posix"
        adapter = WindowsProcessAdapter() if os.name == "nt" else PosixProcessAdapter()
        supervisor = ProcessSupervisor(adapter=adapter)
        limit_policy = SurfaceLimitPolicy(self.settings.policy)
        persistence = SqliteLiveAppPersistence(
            self.db_path,
            supervisor=supervisor,
            target_pins=target_pins,
            limit_policy=limit_policy,
            platform_hint=platform_hint,
        )
        manager = LiveAppManager(
            manifests=WorkspaceManifestStore(root),
            allocator=LoopbackEndpointAllocator(
                address=self.settings.preview.bind_host
            ),
            supervisor=supervisor,
            health=HealthProber(transport=self._transport),
            target_pins=target_pins,
            target_policy=target_policy,
            limit_policy=limit_policy,
            listener_inspector=PsutilListenerInspector(),
            secret_resolver=lambda _workspace_id, _manifest: {},
            public_origin=self._public_origin,
            platform_hint=platform_hint,
            persistence=persistence,
        )
        self._managers[workspace_id] = manager
        return manager

    def _fail_closed_persisted_authority(self) -> None:
        now = datetime.now(UTC).isoformat()
        with connect_state_db(self.db_path) as connection:
            tables = {
                str(row["name"])
                for row in connection.execute(
                    """SELECT name FROM sqlite_master WHERE type='table'
                    AND name IN ('surface_presentations', 'surface_runtimes',
                                 'workspace_surfaces')"""
                ).fetchall()
            }
            if tables != {
                "surface_presentations",
                "surface_runtimes",
                "workspace_surfaces",
            }:
                return
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    """UPDATE surface_presentations
                    SET state='closed', bootstrap_nonce_hash=NULL,
                        presentation_cookie_hash=NULL, closed_at=?
                    WHERE state NOT IN ('closed', 'expired')""",
                    (now,),
                )
                surface_transitions = [
                    (
                        str(row["surface_id"]),
                        str(row["reconciled_lifecycle"]),
                        str(row["diagnostic_code"]),
                        str(row["diagnostic_message"]),
                    )
                    for row in connection.execute(
                        """SELECT surface_id,
                            CASE
                                WHEN SUM(CASE
                                    WHEN state NOT IN ('stopped', 'failed')
                                    THEN 1 ELSE 0 END) > 0 THEN 'failed'
                                WHEN SUM(CASE
                                    WHEN state='failed'
                                    THEN 1 ELSE 0 END) > 0 THEN 'failed'
                                ELSE 'stopped'
                            END AS reconciled_lifecycle,
                            CASE
                                WHEN SUM(CASE
                                    WHEN state NOT IN ('stopped', 'failed')
                                    THEN 1 ELSE 0 END) > 0
                                    THEN 'SURFACE_RECONCILE_OWNERSHIP_UNPROVABLE'
                                WHEN SUM(CASE
                                    WHEN state='failed'
                                    THEN 1 ELSE 0 END) > 0
                                    THEN 'SURFACE_RECONCILE_OWNERSHIP_UNPROVABLE'
                                ELSE 'SURFACE_RECONCILE_RUNTIME_STOPPED'
                            END AS diagnostic_code,
                            CASE
                                WHEN SUM(CASE
                                    WHEN state NOT IN ('stopped', 'failed')
                                    THEN 1 ELSE 0 END) > 0
                                    THEN 'Runtime authority was revoked during startup reconciliation.'
                                WHEN SUM(CASE
                                    WHEN state='failed'
                                    THEN 1 ELSE 0 END) > 0
                                    THEN 'Runtime authority was revoked during startup reconciliation.'
                                ELSE 'Runtime was stopped during startup reconciliation.'
                            END AS diagnostic_message
                        FROM surface_runtimes
                        GROUP BY surface_id"""
                    ).fetchall()
                ]
                connection.execute(
                    """UPDATE surface_runtimes SET state='failed',
                        target_pin_json=NULL, revision=revision+1, updated_at=?
                    WHERE state NOT IN ('stopped', 'failed')""",
                    (now,),
                )
                for (
                    surface_id,
                    reconciled_lifecycle,
                    diagnostic_code,
                    diagnostic_message,
                ) in surface_transitions:
                    connection.execute(
                        """UPDATE workspace_surfaces SET lifecycle=?,
                            diagnostic_summary_json=?, revision=revision+1,
                            updated_at=? WHERE surface_id=?
                            AND lifecycle NOT IN ('stopped', 'failed')""",
                        (
                            reconciled_lifecycle,
                            json.dumps(
                                {
                                    "code": diagnostic_code,
                                    "message": diagnostic_message,
                                    "retryable": True,
                                },
                                sort_keys=True,
                                separators=(",", ":"),
                            ),
                            now,
                            surface_id,
                        ),
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    async def reconcile_startup(self) -> None:
        self._fail_closed_persisted_authority()
        if self._monitor_task is None:
            self._monitor_task = asyncio.create_task(
                self._monitor(), name="surface-runtime-monitor"
            )

    async def _monitor(self) -> None:
        try:
            while True:
                await asyncio.sleep(self.monitor_seconds)
                for workspace_id, manager in tuple(self._managers.items()):
                    await manager.expire_due()
                    for instance in manager.list(workspace_id=workspace_id):
                        if instance.state not in {"ready", "unhealthy"}:
                            continue
                        try:
                            checked = await manager.check_health(instance.instance_id)
                        except LiveAppManagerError:
                            continue
                        if checked.state == "failed":
                            self.revocation.runtime_replaced(
                                workspace_id=workspace_id,
                                instance_id=checked.instance_id,
                            )
        except asyncio.CancelledError:
            raise

    async def begin_shutdown(self) -> None:
        if not self._accepting:
            return
        self._accepting = False
        for workspace_id, manager in tuple(self._managers.items()):
            self.revocation.workspace_closed(workspace_id=workspace_id)
            manager.revoke_all_routes()

    async def shutdown(self) -> None:
        if self._shutdown:
            return
        await self.begin_shutdown()
        if self._monitor_task is not None:
            self._monitor_task.cancel()
            await asyncio.gather(self._monitor_task, return_exceptions=True)
            self._monitor_task = None
        for workspace_id, manager in tuple(self._managers.items()):
            await manager.shutdown_workspace(workspace_id)
        await self._transport.aclose()
        self._shutdown = True


__all__ = [
    "HttpxProbeTransport",
    "LiveAppRuntimeRegistry",
    "SqliteLiveAppPersistence",
]
