"""Fail-closed startup reconciliation for persisted live-app intent."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol


@dataclass(frozen=True, slots=True)
class PersistedRuntime:
    runtime_id: str
    instance_id: str
    workspace_id: str
    generation: int
    state: str
    ownership: str
    platform: str
    authority_expires_at: datetime | None
    revision: int = 1


@dataclass(frozen=True, slots=True)
class ReconciliationEvidence:
    classification: str
    generation: int | None
    pid: int | None
    creation_time: float | None
    containment_id: str | None
    executable_matches: bool
    listener_address: str | None
    listener_port: int | None
    listener_owned: bool

    def __post_init__(self) -> None:
        if self.classification not in {"exact", "stale-owned", "unprovable"}:
            raise ValueError("runtime reconciliation classification is invalid")


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    runtime_id: str
    instance_id: str
    state: str
    diagnostic_code: str
    fresh_authority: bool


class ReconciliationStore(Protocol):
    def list_nonterminal(self) -> Sequence[PersistedRuntime]: ...

    def transition(
        self,
        record: PersistedRuntime,
        *,
        state: str,
        diagnostic_code: str,
        fresh_authority: bool = False,
    ) -> PersistedRuntime: ...


class ReconciliationEvidenceProvider(Protocol):
    async def inspect(self, record: PersistedRuntime) -> ReconciliationEvidence: ...


class ReconciliationAuthority(Protocol):
    def revoke(self, record: PersistedRuntime) -> None: ...

    def issue(
        self, record: PersistedRuntime, evidence: ReconciliationEvidence
    ) -> None: ...


class StaleRuntimeStopper(Protocol):
    async def stop_stale_owned(
        self, record: PersistedRuntime, *, deadline: datetime
    ) -> bool: ...


class RuntimeReconciler:
    def __init__(
        self,
        *,
        store: ReconciliationStore,
        evidence: ReconciliationEvidenceProvider,
        authority: ReconciliationAuthority,
        stopper: StaleRuntimeStopper,
        workspace_valid: Callable[[PersistedRuntime], bool],
        source_valid: Callable[[PersistedRuntime], bool],
        clock: Callable[[], datetime] | None = None,
        cleanup_seconds: int = 5,
    ) -> None:
        if cleanup_seconds < 1 or cleanup_seconds > 30:
            raise ValueError("reconciliation cleanup bound must be 1 to 30 seconds")
        self._store = store
        self._evidence = evidence
        self._authority = authority
        self._stopper = stopper
        self._workspace_valid = workspace_valid
        self._source_valid = source_valid
        self._clock = clock or (lambda: datetime.now(UTC))
        self._cleanup_seconds = cleanup_seconds

    def _transition(
        self,
        record: PersistedRuntime,
        *,
        state: str,
        code: str,
        fresh_authority: bool = False,
    ) -> tuple[PersistedRuntime, ReconciliationResult]:
        updated = self._store.transition(
            record,
            state=state,
            diagnostic_code=code,
            fresh_authority=fresh_authority,
        )
        return updated, ReconciliationResult(
            runtime_id=updated.runtime_id,
            instance_id=updated.instance_id,
            state=updated.state,
            diagnostic_code=code,
            fresh_authority=fresh_authority,
        )

    async def _one(self, original: PersistedRuntime) -> ReconciliationResult:
        self._authority.revoke(original)
        record, _ = self._transition(
            original,
            state="reconciling",
            code="SURFACE_RECONCILING",
        )
        if not self._workspace_valid(record):
            return self._transition(
                record,
                state="failed",
                code="SURFACE_RECONCILE_WORKSPACE_INVALID",
            )[1]
        if not self._source_valid(record):
            return self._transition(
                record,
                state="failed",
                code="SURFACE_RECONCILE_SOURCE_INVALID",
            )[1]
        try:
            evidence = await self._evidence.inspect(record)
        except Exception:
            return self._transition(
                record,
                state="failed",
                code="SURFACE_RECONCILE_OWNERSHIP_UNPROVABLE",
            )[1]

        if evidence.classification == "stale-owned":
            complete = await self._stopper.stop_stale_owned(
                record,
                deadline=self._clock() + timedelta(seconds=self._cleanup_seconds),
            )
            return self._transition(
                record,
                state="stopped" if complete else "failed",
                code=(
                    "SURFACE_RECONCILE_STALE_STOPPED"
                    if complete
                    else "SURFACE_RECONCILE_STALE_CLEANUP_INCOMPLETE"
                ),
            )[1]
        if evidence.classification == "unprovable":
            return self._transition(
                record,
                state="failed",
                code="SURFACE_RECONCILE_OWNERSHIP_UNPROVABLE",
            )[1]
        if evidence.generation != record.generation:
            return self._transition(
                record,
                state="failed",
                code="SURFACE_RECONCILE_GENERATION_MISMATCH",
            )[1]
        if (
            evidence.pid is None
            or evidence.creation_time is None
            or evidence.containment_id is None
            or not evidence.executable_matches
        ):
            return self._transition(
                record,
                state="failed",
                code="SURFACE_RECONCILE_OWNERSHIP_UNPROVABLE",
            )[1]
        if (
            not evidence.listener_owned
            or evidence.listener_address is None
            or evidence.listener_port is None
        ):
            return self._transition(
                record,
                state="failed",
                code="SURFACE_RECONCILE_ENDPOINT_OCCUPIED",
            )[1]

        self._authority.issue(record, evidence)
        return self._transition(
            record,
            state="ready",
            code="SURFACE_RECONCILE_READY",
            fresh_authority=True,
        )[1]

    async def reconcile(self) -> tuple[ReconciliationResult, ...]:
        results = []
        for record in self._store.list_nonterminal():
            results.append(await self._one(record))
        return tuple(results)


__all__ = [
    "PersistedRuntime",
    "ReconciliationEvidence",
    "ReconciliationResult",
    "RuntimeReconciler",
]
