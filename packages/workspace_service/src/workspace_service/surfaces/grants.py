"""Risk-tiered, exact-scope capability-grant policy and consumption."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from data_vault import SurfaceGrantRecord, SurfaceGrantRepository

from .service import ActorRole, SurfaceActor


RiskTier = Literal["low", "high", "mutating"]
GrantPersistence = Literal["remembered_exact", "instance", "operation"]
GrantDecision = Literal["allow", "deny"]


class CapabilityGrantError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class CapabilityPolicy:
    allowed_capabilities: frozenset[str] | None = None
    denied_capabilities: frozenset[str] = frozenset()
    administrator_only_capabilities: frozenset[str] = frozenset(
        {"target.attach", "policy.broaden", "policy.change_deployment"}
    )
    maximum_duration_seconds: int = 30 * 24 * 60 * 60


@dataclass(frozen=True, slots=True)
class CapabilityRequest:
    source_id: str
    source_version: str
    instance_id: str | None
    capability: str
    operation: str
    constraints: dict[str, Any]
    risk_tier: RiskTier
    persistence: GrantPersistence
    duration_seconds: int
    declared: bool
    decision: GrantDecision
    reason: str


class CapabilityGrantService:
    def __init__(
        self,
        db_path: str | Path,
        *,
        policy: CapabilityPolicy | None = None,
        clock=lambda: datetime.now(UTC),
        id_factory=lambda: str(uuid.uuid4()),
    ) -> None:
        self.repository = SurfaceGrantRepository(db_path)
        self.policy = policy or CapabilityPolicy()
        self.clock = clock
        self.id_factory = id_factory

    def _validate(self, *, actor: SurfaceActor, request: CapabilityRequest) -> None:
        if not request.declared:
            raise CapabilityGrantError("Capability was not declared by the source")
        if request.capability in self.policy.denied_capabilities or (
            self.policy.allowed_capabilities is not None
            and request.capability not in self.policy.allowed_capabilities
        ):
            raise CapabilityGrantError("Capability is denied by effective policy")
        if (
            request.capability in self.policy.administrator_only_capabilities
            and actor.role is not ActorRole.ADMIN
        ):
            raise CapabilityGrantError("Capability requires an administrator")
        if request.risk_tier not in {"low", "high", "mutating"}:
            raise CapabilityGrantError("Capability risk tier is invalid")
        if request.persistence not in {"remembered_exact", "instance", "operation"}:
            raise CapabilityGrantError("Capability persistence is invalid")
        if (
            request.risk_tier in {"high", "mutating"}
            and request.persistence == "remembered_exact"
        ):
            raise CapabilityGrantError(
                "High-risk capabilities require instance or operation persistence"
            )
        if request.persistence == "instance" and not request.instance_id:
            raise CapabilityGrantError("Instance grants require an instance")
        if not 1 <= request.duration_seconds <= self.policy.maximum_duration_seconds:
            raise CapabilityGrantError("Capability duration exceeds effective policy")
        if not request.source_id or not request.source_version:
            raise CapabilityGrantError("Capability source scope is invalid")
        if (
            not request.capability
            or not request.operation
            or not request.reason.strip()
        ):
            raise CapabilityGrantError("Capability disclosure is incomplete")
        try:
            encoded = json.dumps(request.constraints, allow_nan=False)
        except (TypeError, ValueError) as error:
            raise CapabilityGrantError("Capability constraints are invalid") from error
        if len(encoded.encode("utf-8")) > 16 * 1024:
            raise CapabilityGrantError("Capability constraints are too large")

    def decide(
        self, *, actor: SurfaceActor, request: CapabilityRequest
    ) -> SurfaceGrantRecord:
        self._validate(actor=actor, request=request)
        now = self.clock()
        record = SurfaceGrantRecord(
            grant_id=self.id_factory(),
            user_id=actor.user_id,
            workspace_id=actor.workspace_id,
            source_id=request.source_id,
            source_version=request.source_version,
            instance_id=(
                request.instance_id
                if request.persistence in {"instance", "operation"}
                else None
            ),
            capability=request.capability,
            operation=request.operation,
            constraints=request.constraints,
            risk_tier=request.risk_tier,
            persistence=request.persistence,
            decision=request.decision,
            decision_source=(
                "administrator" if actor.role is ActorRole.ADMIN else "user"
            ),
            expires_at=now + timedelta(seconds=request.duration_seconds),
            created_at=now,
        )
        return self.repository.create(record)

    def authorize(
        self, *, actor: SurfaceActor, request: CapabilityRequest
    ) -> SurfaceGrantRecord:
        self._validate(actor=actor, request=request)
        now = self.clock()
        records = self.repository.list(
            user_id=actor.user_id,
            workspace_id=actor.workspace_id,
            source_id=request.source_id,
            source_version=request.source_version,
        )
        candidates = [
            item
            for item in records
            if item.capability == request.capability
            and item.operation == request.operation
            and item.constraints == request.constraints
            and item.risk_tier == request.risk_tier
            and (
                item.persistence == "remembered_exact"
                or item.instance_id == request.instance_id
            )
        ]
        if not candidates:
            raise CapabilityGrantError("No capability grant matches the grant scope")
        active = [
            item
            for item in candidates
            if item.revoked_at is None
            and (item.expires_at is None or item.expires_at >= now)
        ]
        if any(item.decision == "deny" for item in active):
            raise CapabilityGrantError("Capability is denied by an active decision")
        allowed = [item for item in active if item.decision == "allow"]
        if not allowed:
            if any(item.revoked_at is not None for item in candidates):
                raise CapabilityGrantError("Capability grant was revoked")
            raise CapabilityGrantError("Capability grant expired")
        grant = allowed[-1]
        if grant.persistence == "operation":
            if grant.used_at is not None:
                raise CapabilityGrantError("Capability operation grant was consumed")
            consumed = self.repository.consume_operation(grant, used_at=now)
            if consumed is None:
                raise CapabilityGrantError("Capability operation grant was consumed")
            return consumed
        return grant

    def revoke(self, *, actor: SurfaceActor, grant_id: str) -> SurfaceGrantRecord:
        record = self.repository.get(
            grant_id=grant_id,
            user_id=actor.user_id,
            workspace_id=actor.workspace_id,
        )
        if record is None:
            raise CapabilityGrantError("Capability grant not found")
        return self.repository.revoke(record, revoked_at=self.clock())


__all__ = [
    "CapabilityGrantError",
    "CapabilityGrantService",
    "CapabilityPolicy",
    "CapabilityRequest",
]
