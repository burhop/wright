"""Serialized lifecycle manager for managed live applications."""

from __future__ import annotations

import asyncio
import os
import secrets
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from typing import Any

from core.surfaces.live_app_manifest import (
    AttachLaunch,
    CommandLaunch,
    ManifestPlaceholders,
)

from workspace_service.surfaces.endpoints import EndpointError
from workspace_service.surfaces.health import ProbeResult, ProbeTarget, RestartBudget
from workspace_service.surfaces.limits import SurfaceLimitError
from workspace_service.surfaces.manifests import (
    AttachApproval,
    DiscoveredManifest,
    ManifestDiscoveryError,
)
from workspace_service.surfaces.process_supervisor import ProcessSupervisorError
from workspace_service.surfaces.target_pins import TargetPinError
from workspace_service.surfaces.target_policy import (
    ResolvedTargetPin,
    TargetPolicyError,
)


class LiveAppManagerError(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        instance: "LiveAppInstance | None" = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.instance = instance
        self.retryable = retryable


@dataclass(frozen=True, slots=True)
class LiveAppStartRequest:
    workspace_id: str
    surface_id: str
    manifest_id: str
    user_id: str
    session_id: str
    idempotency_key: str
    initial_generation: int = 1
    attach_approval: AttachApproval | None = None


@dataclass(frozen=True, slots=True)
class LiveAppFailure:
    code: str
    message: str
    retryable: bool


@dataclass(frozen=True, slots=True)
class LiveAppInstance:
    instance_id: str
    workspace_id: str
    surface_id: str
    manifest_id: str
    manifest_hash: str
    generation: int
    revision: int
    state: str
    sharing: str
    ownership: str
    platform: str | None
    runtime_id: str | None
    lifetime_policy: str
    lease_expires_at: datetime | None
    idle_seconds: int | None
    last_activity_at: datetime
    started_at: datetime | None
    ready_at: datetime | None
    ended_at: datetime | None
    last_health: ProbeResult | None
    failure: LiveAppFailure | None


@dataclass(frozen=True, slots=True)
class LiveAppRoutingPolicy:
    instance_id: str
    generation: int
    http: bool
    websocket: bool
    sse: bool
    limits: Any


@dataclass(frozen=True, slots=True)
class LiveAppRoute:
    policy: LiveAppRoutingPolicy
    target: ResolvedTargetPin


@dataclass(frozen=True, slots=True)
class _StartContext:
    request: LiveAppStartRequest
    declaration: DiscoveredManifest


_ACTIVE_STATES = frozenset({"starting", "ready", "unhealthy", "stopping"})
_SAFE_BASE_ENVIRONMENT = frozenset(
    {
        "PATH",
        "SYSTEMROOT",
        "WINDIR",
        "COMSPEC",
        "PATHEXT",
        "TEMP",
        "TMP",
        "TMPDIR",
        "HOME",
        "USERPROFILE",
        "LOCALAPPDATA",
        "LANG",
        "LC_ALL",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
    }
)


class LiveAppManager:
    def __init__(
        self,
        *,
        manifests: Any,
        allocator: Any,
        supervisor: Any,
        health: Any,
        target_pins: Any,
        target_policy: Any,
        limit_policy: Any,
        listener_inspector: Any,
        secret_resolver: Callable[[str, Any], Mapping[str, str]],
        public_origin: Callable[[str, str], str],
        id_factory: Callable[[], str] | None = None,
        clock: Callable[[], datetime] | None = None,
        monotonic: Callable[[], float] | None = None,
        administrator_limits: Mapping[str, int | float] | None = None,
        maximum_endpoint_attempts: int = 5,
        inherited_listener: Callable[[str], bool] | None = None,
        platform_hint: str | None = None,
        persistence: Callable[[LiveAppInstance, DiscoveredManifest], None]
        | None = None,
    ) -> None:
        if not 1 <= maximum_endpoint_attempts <= 5:
            raise ValueError("endpoint launch attempts must be between one and five")
        self._manifests = manifests
        self._allocator = allocator
        self._supervisor = supervisor
        self._health = health
        self._target_pins = target_pins
        self._target_policy = target_policy
        self._limit_policy = limit_policy
        self._listener_inspector = listener_inspector
        self._secret_resolver = secret_resolver
        self._public_origin = public_origin
        self._id_factory = id_factory or (lambda: secrets.token_urlsafe(24))
        self._clock = clock or (lambda: datetime.now(UTC))
        self._monotonic = monotonic
        self._administrator_limits = dict(administrator_limits or {})
        self._maximum_endpoint_attempts = maximum_endpoint_attempts
        self._inherited_listener = inherited_listener or (lambda _framework: False)
        self._platform_hint = platform_hint
        self._persistence = persistence
        self._instances: dict[str, LiveAppInstance] = {}
        self._contexts: dict[str, _StartContext] = {}
        self._source_instances: dict[tuple[str, str, str], str] = {}
        self._request_results: dict[tuple[str, str], str] = {}
        self._operation_results: dict[tuple[str, str, str], LiveAppInstance] = {}
        self._source_locks: dict[tuple[str, str, str], asyncio.Lock] = {}
        self._instance_locks: dict[str, asyncio.Lock] = {}
        self._start_semaphores: dict[str, asyncio.Semaphore] = {}
        self._restart_budgets: dict[str, RestartBudget] = {}
        self._presentations: dict[str, int] = {}
        self._routing_limits: dict[tuple[str, int], Any] = {}
        self._registry_lock = asyncio.Lock()

    @staticmethod
    def _validate_request(request: LiveAppStartRequest) -> None:
        if not all(
            (
                request.workspace_id,
                request.surface_id,
                request.manifest_id,
                request.user_id,
                request.session_id,
                request.idempotency_key,
            )
        ):
            raise LiveAppManagerError(
                "SURFACE_LIFECYCLE_REQUEST_INVALID",
                "Live-app start request is missing required scope or idempotency",
            )
        if (
            isinstance(request.initial_generation, bool)
            or not isinstance(request.initial_generation, int)
            or request.initial_generation < 1
        ):
            raise LiveAppManagerError(
                "SURFACE_LIFECYCLE_REQUEST_INVALID",
                "Live-app start generation must be a positive integer",
            )

    async def _source_lock(self, key: tuple[str, str, str]) -> asyncio.Lock:
        async with self._registry_lock:
            return self._source_locks.setdefault(key, asyncio.Lock())

    async def _instance_lock(self, instance_id: str) -> asyncio.Lock:
        async with self._registry_lock:
            return self._instance_locks.setdefault(instance_id, asyncio.Lock())

    def _effective_limits(self, declaration: DiscoveredManifest):
        return self._limit_policy.compose(
            declared=declaration.manifest.limits.as_policy_mapping(),
            administrator=self._administrator_limits,
            clock=self._clock,
        )

    def _new_instance(
        self, request: LiveAppStartRequest, declaration: DiscoveredManifest
    ) -> LiveAppInstance:
        instance_id = self._id_factory()
        if not instance_id or instance_id in self._instances:
            raise LiveAppManagerError(
                "SURFACE_INSTANCE_ID_INVALID",
                "Live-app instance ID is empty or collided",
            )
        now = self._clock()
        lifetime = declaration.manifest.lifetime
        instance = LiveAppInstance(
            instance_id=instance_id,
            workspace_id=request.workspace_id,
            surface_id=request.surface_id,
            manifest_id=request.manifest_id,
            manifest_hash=declaration.manifest.canonical_hash,
            generation=request.initial_generation,
            revision=1,
            state="declared",
            sharing=declaration.manifest.presentation.sharing,
            ownership=(
                "launched"
                if isinstance(declaration.manifest.launch, CommandLaunch)
                else "attached_verified"
            ),
            platform=self._platform_hint,
            runtime_id=None,
            lifetime_policy=lifetime.policy,
            lease_expires_at=(
                now + timedelta(seconds=lifetime.lease_seconds)
                if lifetime.lease_seconds is not None
                else None
            ),
            idle_seconds=lifetime.idle_seconds,
            last_activity_at=now,
            started_at=None,
            ready_at=None,
            ended_at=None,
            last_health=None,
            failure=None,
        )
        self._instances[instance_id] = instance
        self._contexts[instance_id] = _StartContext(request, declaration)
        self._presentations[instance_id] = 0
        limits = self._effective_limits(declaration)
        self._restart_budgets[instance_id] = RestartBudget(
            maximum_restarts=int(limits.restart_attempts),
            window_seconds=int(limits.restart_window_seconds),
            monotonic=self._monotonic,
        )
        self._persist(instance)
        return instance

    def _persist(self, instance: LiveAppInstance) -> None:
        if self._persistence is not None:
            self._persistence(
                instance, self._contexts[instance.instance_id].declaration
            )

    def _replace(self, instance_id: str, **changes: Any) -> LiveAppInstance:
        current = self._instances[instance_id]
        updated = replace(current, revision=current.revision + 1, **changes)
        self._instances[instance_id] = updated
        self._persist(updated)
        return updated

    def get(self, instance_id: str) -> LiveAppInstance:
        try:
            return self._instances[instance_id]
        except KeyError as error:
            raise LiveAppManagerError(
                "SURFACE_INSTANCE_NOT_FOUND", "Live-app instance was not found"
            ) from error

    def list(self, *, workspace_id: str) -> tuple[LiveAppInstance, ...]:
        return tuple(
            sorted(
                (
                    item
                    for item in self._instances.values()
                    if item.workspace_id == workspace_id
                ),
                key=lambda item: (
                    item.started_at or item.last_activity_at,
                    item.instance_id,
                ),
            )
        )

    def routing_policy(
        self, instance_id: str, *, generation: int
    ) -> LiveAppRoutingPolicy:
        instance = self.get(instance_id)
        if instance.generation != generation or instance.state not in {
            "ready",
            "unhealthy",
        }:
            raise LiveAppManagerError(
                "SURFACE_STATE_STALE_GENERATION",
                "Live-app route generation is not currently available",
                instance=instance,
            )
        key = (instance_id, generation)
        limits = self._routing_limits.get(key)
        if limits is None:
            limits = self._effective_limits(self._contexts[instance_id].declaration)
            self._routing_limits[key] = limits
        transports = self._contexts[instance_id].declaration.manifest.transports
        return LiveAppRoutingPolicy(
            instance_id=instance_id,
            generation=generation,
            http=transports.http,
            websocket=transports.websocket,
            sse=transports.sse,
            limits=limits,
        )

    def resolve_route(self, instance_id: str, *, generation: int) -> LiveAppRoute:
        policy = self.routing_policy(instance_id, generation=generation)
        try:
            active = self._target_pins.resolve(
                instance_id=instance_id, generation=generation
            )
        except TargetPinError as error:
            raise LiveAppManagerError(
                error.code,
                str(error),
                instance=self.get(instance_id),
            ) from error
        return LiveAppRoute(policy=policy, target=active.target)

    def presentation_projection(self, instance_id: str) -> tuple[dict[str, Any], ...]:
        self.get(instance_id)
        presentation = self._contexts[instance_id].declaration.manifest.presentation
        return tuple(
            {
                "kind": kind,
                "eligible": enabled,
                "reason": (
                    "Declared by the managed application."
                    if enabled
                    else f"The managed application does not declare {kind} presentation."
                ),
            }
            for kind, enabled in (
                ("panel", presentation.panel),
                ("browser", presentation.browser),
            )
        )

    def logs(self, instance_id: str, *, after_sequence: int = 0, limit: int = 200):
        instance = self.get(instance_id)
        if instance.runtime_id is None or instance.ownership != "launched":
            raise LiveAppManagerError(
                "SURFACE_LOGS_UNAVAILABLE",
                "Captured logs are unavailable for this managed application",
                instance=instance,
            )
        return self._supervisor.logs(
            instance.runtime_id, after_sequence=after_sequence, limit=limit
        )

    async def check_health(self, instance_id: str) -> LiveAppInstance:
        lock = await self._instance_lock(instance_id)
        async with lock:
            current = self.get(instance_id)
            if current.state not in {"ready", "unhealthy"}:
                raise LiveAppManagerError(
                    "SURFACE_LIFECYCLE_CONFLICT",
                    f"Health cannot be checked from {current.state}",
                    instance=current,
                )
            declaration = self._contexts[instance_id].declaration
            probe = declaration.manifest.health
            if probe is None:
                return current
            if current.runtime_id and current.ownership == "launched":
                process = self._supervisor.snapshot(current.runtime_id)
                if process.status not in {"running", "starting"}:
                    failure = LiveAppFailure(
                        "SURFACE_PROCESS_EXITED",
                        "Managed process exited while the application was active",
                        True,
                    )
                    self._target_pins.revoke(
                        instance_id=instance_id, generation=current.generation
                    )
                    self._routing_limits.pop((instance_id, current.generation), None)
                    return self._replace(
                        instance_id,
                        state="failed",
                        ended_at=self._clock(),
                        failure=failure,
                    )
            route = self.resolve_route(instance_id, generation=current.generation)
            result = await self._health.check(
                target=ProbeTarget(
                    scheme=route.target.scheme,
                    numeric_address=route.target.numeric_address,
                    port=route.target.port,
                    host_header=route.target.host_header,
                    server_name=route.target.server_name,
                ),
                probe=probe,
            )
            return self._replace(
                instance_id,
                state="ready" if result.ok else "unhealthy",
                last_health=result,
                failure=None,
            )

    async def start(self, request: LiveAppStartRequest) -> LiveAppInstance:
        self._validate_request(request)
        prior_id = self._request_results.get(
            (request.workspace_id, request.idempotency_key)
        )
        if prior_id is not None:
            return self.get(prior_id)
        try:
            declaration = self._manifests.authorize(
                request.manifest_id, attach_approval=request.attach_approval
            )
        except (ManifestDiscoveryError, SurfaceLimitError) as error:
            raise LiveAppManagerError(
                error.code,
                str(error),
                retryable=False,
            ) from error
        source_key = (
            request.workspace_id,
            request.surface_id,
            declaration.manifest.canonical_hash,
        )
        lock = await self._source_lock(source_key)
        async with lock:
            prior_id = self._request_results.get(
                (request.workspace_id, request.idempotency_key)
            )
            if prior_id is not None:
                return self.get(prior_id)
            if declaration.manifest.presentation.sharing == "shared":
                shared_id = self._source_instances.get(source_key)
                if shared_id is not None:
                    shared = self.get(shared_id)
                    if shared.state in _ACTIVE_STATES:
                        self._request_results[
                            (request.workspace_id, request.idempotency_key)
                        ] = shared_id
                        return shared
            try:
                limits = self._effective_limits(declaration)
            except SurfaceLimitError as error:
                raise LiveAppManagerError(
                    error.code, str(error), retryable=False
                ) from error
            if isinstance(declaration.manifest.launch, CommandLaunch):
                owned = sum(
                    1
                    for item in self._instances.values()
                    if item.workspace_id == request.workspace_id
                    and item.ownership == "launched"
                    and item.state in _ACTIVE_STATES
                )
                if owned >= int(limits.owned_apps_per_workspace):
                    raise LiveAppManagerError(
                        "SURFACE_LIMIT_OWNED_APPS",
                        "Workspace has reached its managed live-app limit",
                    )
            instance = self._new_instance(request, declaration)
            self._request_results[(request.workspace_id, request.idempotency_key)] = (
                instance.instance_id
            )
            if declaration.manifest.presentation.sharing == "shared":
                self._source_instances[source_key] = instance.instance_id
            semaphore = self._start_semaphores.setdefault(
                request.workspace_id,
                asyncio.Semaphore(int(limits.concurrent_starts_per_workspace)),
            )
            async with semaphore:
                return await self._launch_locked(instance.instance_id)

    @staticmethod
    def _safe_environment(declared: Mapping[str, str]) -> dict[str, str]:
        environment = {
            name: value
            for name, value in os.environ.items()
            if name.upper() in _SAFE_BASE_ENVIRONMENT
        }
        environment.update(declared)
        return environment

    @staticmethod
    def _platform(identity_adapter: str) -> str:
        if identity_adapter == "posix-process-group":
            return "posix"
        if identity_adapter == "windows-job-object":
            return "windows_job"
        if identity_adapter in {"docker", "container"}:
            return "container"
        return "remote_adapter"

    async def _launch_locked(self, instance_id: str) -> LiveAppInstance:
        context = self._contexts[instance_id]
        declaration = context.declaration
        manifest = declaration.manifest
        limits = self._effective_limits(declaration)
        current = self.get(instance_id)
        current = self._replace(
            instance_id,
            state="starting",
            started_at=self._clock(),
            ready_at=None,
            ended_at=None,
            failure=None,
            runtime_id=None,
            platform=self._platform_hint,
            last_health=None,
        )
        if isinstance(manifest.launch, AttachLaunch):
            return await self._launch_attach(current, context, limits.as_mapping())

        last_error: BaseException | None = None
        for attempt in range(self._maximum_endpoint_attempts):
            current = self.get(instance_id)
            reservation = self._allocator.reserve(
                instance_id=instance_id,
                generation=current.generation,
                inherit_listener=self._inherited_listener(manifest.launch.framework),
            )
            runtime_id: str | None = None
            try:
                public_origin = self._public_origin(current.workspace_id, instance_id)
                resolved = manifest.resolve_command(
                    ManifestPlaceholders(
                        bind_host=reservation.address,
                        port=reservation.port,
                        public_origin=public_origin,
                        base_path="/",
                        instance_id=instance_id,
                    ),
                    secrets=self._secret_resolver(current.workspace_id, manifest),
                )
                if not reservation.inherit_listener:
                    reservation.release_immediately_before_spawn()
                runtime = await self._supervisor.start(
                    workspace_id=current.workspace_id,
                    instance_id=instance_id,
                    generation=current.generation,
                    argv=resolved.argv,
                    cwd=str(declaration.working_directory),
                    environment=self._safe_environment(resolved.environment),
                    secret_environment_names=resolved.secret_environment_names,
                    redaction_query_names=manifest.redaction_query_names,
                    limits=limits.as_mapping(),
                    idempotency_key=(
                        f"{context.request.idempotency_key}:generation:{current.generation}"
                    ),
                    listener_handle=reservation.listener_handle,
                )
                runtime_id = runtime.runtime_id
                current = self._replace(
                    instance_id,
                    runtime_id=runtime_id,
                    platform=self._platform(runtime.identity.adapter),
                )
                readiness = await self._health.wait_ready(
                    target=ProbeTarget(
                        scheme="http",
                        numeric_address=reservation.address,
                        port=reservation.port,
                        host_header=f"{reservation.address}:{reservation.port}",
                        server_name=None,
                    ),
                    probe=manifest.readiness,
                    process_alive=lambda: (
                        self._supervisor.snapshot(runtime_id).status
                        in {"running", "starting"}
                    ),
                    ownership_valid=lambda: True,
                )
                if not readiness.ok:
                    raise LiveAppManagerError(
                        readiness.diagnostic_code or "SURFACE_READINESS_FAILED",
                        readiness.message,
                        instance=current,
                        retryable=True,
                    )
                ownership = reservation.prove_listener_ownership(
                    runtime=self._supervisor.runtime_identity(runtime_id),
                    inspector=self._listener_inspector,
                )
                self._target_pins.activate_launched(
                    instance_id=instance_id,
                    generation=current.generation,
                    readiness=readiness,
                    ownership=ownership,
                    scheme="http",
                )
                reservation.close()
                now = self._clock()
                return self._replace(
                    instance_id,
                    state="ready",
                    ready_at=now,
                    last_activity_at=now,
                    last_health=readiness,
                )
            except EndpointError as error:
                last_error = error
                if error.code != "SURFACE_TARGET_OWNERSHIP_MISMATCH":
                    await self._fail_launch(
                        instance_id, runtime_id, error.code, str(error)
                    )
                    break
                await self._cleanup_attempt(instance_id, runtime_id)
                reservation.close()
                if attempt + 1 >= self._maximum_endpoint_attempts:
                    break
                self._replace(
                    instance_id,
                    generation=self.get(instance_id).generation + 1,
                    runtime_id=None,
                    platform=self._platform_hint,
                )
            except (LiveAppManagerError, TargetPinError, TargetPolicyError) as error:
                last_error = error
                await self._fail_launch(
                    instance_id,
                    runtime_id,
                    getattr(error, "code", "SURFACE_START_FAILED"),
                    str(error),
                )
                reservation.close()
                break
            except ProcessSupervisorError as error:
                last_error = error
                await self._fail_launch(
                    instance_id,
                    runtime_id,
                    error.code,
                    str(error),
                )
                reservation.close()
                break
            except BaseException as error:
                if isinstance(error, asyncio.CancelledError):
                    await self._cleanup_attempt(instance_id, runtime_id)
                    reservation.close()
                    raise
                last_error = error
                detail = f"{type(error).__name__}: {error}"
                await self._fail_launch(
                    instance_id,
                    runtime_id,
                    "SURFACE_START_FAILED",
                    detail if detail.strip() else "Managed application could not start",
                )
                reservation.close()
                break

        failed = self.get(instance_id)
        if failed.state != "failed":
            code = getattr(last_error, "code", "SURFACE_TARGET_OWNERSHIP_MISMATCH")
            failed = self._replace(
                instance_id,
                state="failed",
                ended_at=self._clock(),
                failure=LiveAppFailure(
                    code,
                    "Application endpoint ownership could not be established",
                    True,
                ),
            )
        raise LiveAppManagerError(
            failed.failure.code if failed.failure else "SURFACE_START_FAILED",
            failed.failure.message if failed.failure else "Managed application failed",
            instance=failed,
            retryable=failed.failure.retryable if failed.failure else True,
        )

    async def _launch_attach(
        self,
        instance: LiveAppInstance,
        context: _StartContext,
        limits: Mapping[str, int | float],
    ) -> LiveAppInstance:
        del limits
        launch = context.declaration.manifest.launch
        assert isinstance(launch, AttachLaunch)
        try:
            target = self._target_policy.pin_approved_attach(
                launch.url,
                administrator_approved=context.request.attach_approval is not None,
                ownership_proof=launch.ownership_proof or "operator-approved",
            )
            readiness = await self._health.wait_ready(
                target=ProbeTarget(
                    target.scheme,
                    target.numeric_address,
                    target.port,
                    target.host_header,
                    target.server_name,
                ),
                probe=context.declaration.manifest.readiness,
                process_alive=lambda: True,
                ownership_valid=lambda: (
                    self._target_policy.revalidate(target) == target
                ),
            )
            if not readiness.ok:
                raise LiveAppManagerError(
                    readiness.diagnostic_code or "SURFACE_READINESS_FAILED",
                    readiness.message,
                    retryable=True,
                )
            self._target_pins.activate_attached(
                instance_id=instance.instance_id,
                generation=instance.generation,
                readiness=readiness,
                approved_target=target,
            )
            now = self._clock()
            return self._replace(
                instance.instance_id,
                state="ready",
                runtime_id=f"attach:{instance.instance_id}:{instance.generation}",
                platform="remote_adapter",
                ready_at=now,
                last_activity_at=now,
                last_health=readiness,
            )
        except (LiveAppManagerError, TargetPinError, TargetPolicyError) as error:
            failed = self._replace(
                instance.instance_id,
                state="failed",
                ended_at=self._clock(),
                failure=LiveAppFailure(
                    getattr(error, "code", "SURFACE_ATTACH_FAILED"), str(error), True
                ),
            )
            raise LiveAppManagerError(
                failed.failure.code,
                failed.failure.message,
                instance=failed,
                retryable=True,
            ) from error

    async def _cleanup_attempt(self, instance_id: str, runtime_id: str | None) -> None:
        current = self.get(instance_id)
        self._target_pins.revoke(instance_id=instance_id, generation=current.generation)
        self._routing_limits.pop((instance_id, current.generation), None)
        if runtime_id is not None:
            await self._supervisor.stop(
                runtime_id=runtime_id,
                generation=current.generation,
                deadline=self._clock()
                + timedelta(
                    seconds=int(
                        self._effective_limits(
                            self._contexts[instance_id].declaration
                        ).ordinary_stop_timeout_seconds
                    )
                ),
            )

    async def _fail_launch(
        self,
        instance_id: str,
        runtime_id: str | None,
        code: str,
        message: str,
    ) -> None:
        await self._cleanup_attempt(instance_id, runtime_id)
        self._replace(
            instance_id,
            state="failed",
            ended_at=self._clock(),
            failure=LiveAppFailure(code, message, True),
        )

    async def _stop_locked(self, instance_id: str) -> LiveAppInstance:
        current = self.get(instance_id)
        if current.state == "stopped":
            return current
        if current.state == "stopping":
            return current
        current = self._replace(instance_id, state="stopping")
        # Route and presentation authority is revoked before process signalling.
        self._target_pins.revoke(instance_id=instance_id, generation=current.generation)
        self._routing_limits.pop((instance_id, current.generation), None)
        if current.runtime_id and current.ownership == "launched":
            limits = self._effective_limits(self._contexts[instance_id].declaration)
            report = await self._supervisor.stop(
                runtime_id=current.runtime_id,
                generation=current.generation,
                deadline=self._clock()
                + timedelta(seconds=int(limits.ordinary_stop_timeout_seconds)),
            )
            if report.stop_result is not None and not report.stop_result.complete:
                return self._replace(
                    instance_id,
                    state="failed",
                    ended_at=self._clock(),
                    failure=LiveAppFailure(
                        "SURFACE_STOP_INCOMPLETE",
                        "Managed process cleanup did not reconcile every descendant and listener",
                        True,
                    ),
                )
        return self._replace(
            instance_id,
            state="stopped",
            ended_at=self._clock(),
            failure=None,
        )

    async def stop(self, instance_id: str, *, idempotency_key: str) -> LiveAppInstance:
        if not idempotency_key:
            raise LiveAppManagerError(
                "SURFACE_LIFECYCLE_REQUEST_INVALID", "Stop requires idempotency"
            )
        operation = (instance_id, "stop", idempotency_key)
        if operation in self._operation_results:
            return self._operation_results[operation]
        lock = await self._instance_lock(instance_id)
        async with lock:
            if operation in self._operation_results:
                return self._operation_results[operation]
            stopped = await self._stop_locked(instance_id)
            self._operation_results[operation] = stopped
            return stopped

    async def compensate_uncommitted(
        self,
        instance_id: str,
        *,
        generation: int,
        correlation_id: str,
    ) -> LiveAppInstance:
        """Fail closed when a ready runtime cannot be committed to its surface.

        Compensation is deliberately narrower than a normal stop or restart. It
        may act only on the exact generation returned to the control service, so
        a late descriptor failure can never stop a newer runtime generation.
        """

        if not correlation_id or len(correlation_id) > 64:
            raise LiveAppManagerError(
                "SURFACE_COMPENSATION_REQUEST_INVALID",
                "Runtime compensation requires a bounded correlation reference",
            )
        lock = await self._instance_lock(instance_id)
        async with lock:
            current = self.get(instance_id)
            if current.generation != generation:
                raise LiveAppManagerError(
                    "SURFACE_COMPENSATION_GENERATION_MISMATCH",
                    "Runtime generation changed before compensation could be applied",
                    instance=current,
                )
            if current.state in {"failed", "stopped"}:
                return current
            if current.state not in {"ready", "unhealthy"}:
                raise LiveAppManagerError(
                    "SURFACE_COMPENSATION_STATE_MISMATCH",
                    f"Runtime compensation is not available from {current.state}",
                    instance=current,
                )
            stopped = await self._stop_locked(instance_id)
            if stopped.state != "stopped":
                return stopped
            return self._replace(
                instance_id,
                state="failed",
                ended_at=self._clock(),
                failure=LiveAppFailure(
                    "SURFACE_DESCRIPTOR_COMMIT_FAILED",
                    (
                        "Managed runtime was stopped because its authoritative "
                        f"surface state could not be committed. Reference {correlation_id}."
                    ),
                    True,
                ),
            )

    async def restart(
        self,
        instance_id: str,
        *,
        idempotency_key: str,
        automatic: bool = False,
    ) -> LiveAppInstance:
        operation = (instance_id, "restart", idempotency_key)
        if operation in self._operation_results:
            return self._operation_results[operation]
        lock = await self._instance_lock(instance_id)
        async with lock:
            if operation in self._operation_results:
                return self._operation_results[operation]
            current = self.get(instance_id)
            if current.state not in {"ready", "unhealthy", "failed", "stopped"}:
                raise LiveAppManagerError(
                    "SURFACE_LIFECYCLE_CONFLICT",
                    f"Cannot restart live app from {current.state}",
                    instance=current,
                )
            if automatic and not self._restart_budgets[instance_id].consume():
                raise LiveAppManagerError(
                    "SURFACE_RESTART_BUDGET_EXHAUSTED",
                    "Automatic restart budget is exhausted for this app",
                    instance=current,
                )
            if current.state in {"ready", "unhealthy"}:
                current = await self._stop_locked(instance_id)
                if current.state != "stopped":
                    raise LiveAppManagerError(
                        "SURFACE_STOP_INCOMPLETE",
                        "App could not be cleaned up before restart",
                        instance=current,
                    )
            self._replace(
                instance_id,
                generation=current.generation + 1,
                state="declared",
                runtime_id=None,
                platform=self._platform_hint,
                failure=None,
                ended_at=None,
            )
            result = await self._launch_locked(instance_id)
            self._operation_results[operation] = result
            return result

    async def retry(self, instance_id: str, *, idempotency_key: str) -> LiveAppInstance:
        if self.get(instance_id).state not in {"failed", "stopped"}:
            raise LiveAppManagerError(
                "SURFACE_LIFECYCLE_CONFLICT",
                "Retry applies only to failed or stopped apps",
                instance=self.get(instance_id),
            )
        return await self.restart(
            instance_id, idempotency_key=idempotency_key, automatic=False
        )

    def record_activity(self, instance_id: str, event: str) -> LiveAppInstance:
        current = self.get(instance_id)
        declared_events = self._contexts[
            instance_id
        ].declaration.manifest.lifetime.activity_events
        if event not in declared_events or current.state not in {"ready", "unhealthy"}:
            return current
        return self._replace(instance_id, last_activity_at=self._clock())

    def record_route_activity(self, instance_id: str) -> LiveAppInstance:
        declared_events = self._contexts[
            instance_id
        ].declaration.manifest.lifetime.activity_events
        for event in ("presentation-traffic", "application-request"):
            if event in declared_events:
                return self.record_activity(instance_id, event)
        return self.get(instance_id)

    def revoke_all_routes(self) -> int:
        revoked = 0
        for instance_id in tuple(self._instances):
            revoked += self._target_pins.revoke_instance(instance_id=instance_id)
        self._routing_limits.clear()
        return revoked

    async def presentation_opened(self, instance_id: str) -> LiveAppInstance:
        self._presentations[instance_id] = self._presentations.get(instance_id, 0) + 1
        return self.record_activity(instance_id, "presentation-open")

    async def presentation_closed(self, instance_id: str) -> LiveAppInstance:
        self._presentations[instance_id] = max(
            0, self._presentations.get(instance_id, 0) - 1
        )
        current = self.get(instance_id)
        if (
            current.lifetime_policy == "presentation"
            and not self._presentations[instance_id]
        ):
            return await self.stop(
                instance_id,
                idempotency_key=f"lifetime:presentation:{current.generation}",
            )
        return current

    async def expire_due(self) -> tuple[LiveAppInstance, ...]:
        now = self._clock()
        due = []
        for item in tuple(self._instances.values()):
            if item.state not in {"ready", "unhealthy"}:
                continue
            if item.lifetime_policy == "lease" and item.lease_expires_at is not None:
                if now >= item.lease_expires_at:
                    due.append(item)
            elif item.lifetime_policy == "idle" and item.idle_seconds is not None:
                if now >= item.last_activity_at + timedelta(seconds=item.idle_seconds):
                    due.append(item)
        return tuple(
            await asyncio.gather(
                *(
                    self.stop(
                        item.instance_id,
                        idempotency_key=f"lifetime:expiry:{item.generation}",
                    )
                    for item in due
                )
            )
        )

    async def shutdown_workspace(
        self, workspace_id: str
    ) -> tuple[LiveAppInstance, ...]:
        targets = [
            item
            for item in self._instances.values()
            if item.workspace_id == workspace_id and item.state in _ACTIVE_STATES
        ]
        return tuple(
            await asyncio.gather(
                *(
                    self.stop(
                        item.instance_id,
                        idempotency_key=f"workspace-shutdown:{item.generation}",
                    )
                    for item in targets
                )
            )
        )


__all__ = [
    "LiveAppFailure",
    "LiveAppInstance",
    "LiveAppManager",
    "LiveAppManagerError",
    "LiveAppRoute",
    "LiveAppRoutingPolicy",
    "LiveAppStartRequest",
]
