"""Activation and revocation registry for immutable live-app target pins."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from workspace_service.surfaces.endpoints import EndpointOwnershipProof
from workspace_service.surfaces.health import ProbeResult
from workspace_service.surfaces.target_policy import ResolvedTargetPin, TargetPolicy


class TargetPinError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class ActiveTargetPin:
    instance_id: str
    generation: int
    target: ResolvedTargetPin
    activated_at: datetime


class TargetPinRegistry:
    def __init__(
        self,
        *,
        policy: TargetPolicy,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._policy = policy
        self._clock = clock or (lambda: datetime.now(UTC))
        self._pins: dict[tuple[str, int], ActiveTargetPin] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _require_ready(readiness: ProbeResult) -> None:
        if not readiness.ok:
            raise TargetPinError(
                "SURFACE_TARGET_NOT_READY",
                "Target pin cannot activate before readiness succeeds",
            )

    def _activate(
        self,
        *,
        instance_id: str,
        generation: int,
        target: ResolvedTargetPin,
    ) -> ActiveTargetPin:
        key = (instance_id, generation)
        with self._lock:
            current = self._pins.get(key)
            if current is not None:
                if current.target != target:
                    raise TargetPinError(
                        "SURFACE_TARGET_PIN_CONFLICT",
                        "Active runtime generation already has a different immutable target",
                    )
                return current
            active = ActiveTargetPin(
                instance_id=instance_id,
                generation=generation,
                target=target,
                activated_at=self._clock(),
            )
            self._pins[key] = active
            return active

    def activate_launched(
        self,
        *,
        instance_id: str,
        generation: int,
        readiness: ProbeResult,
        ownership: EndpointOwnershipProof,
        scheme: str,
    ) -> ActiveTargetPin:
        self._require_ready(readiness)
        if ownership.instance_id != instance_id or ownership.generation != generation:
            raise TargetPinError(
                "SURFACE_TARGET_OWNERSHIP_MISMATCH",
                "Listener ownership does not match the target runtime generation",
            )
        listener = ownership.listener
        target = self._policy.pin_launched(
            scheme=scheme,
            address=listener.address,
            port=listener.port,
            instance_id=instance_id,
            generation=generation,
        )
        return self._activate(
            instance_id=instance_id, generation=generation, target=target
        )

    def activate_attached(
        self,
        *,
        instance_id: str,
        generation: int,
        readiness: ProbeResult,
        approved_target: ResolvedTargetPin,
    ) -> ActiveTargetPin:
        self._require_ready(readiness)
        if approved_target.ownership != "attached_verified":
            raise TargetPinError(
                "SURFACE_TARGET_OWNERSHIP_MISMATCH",
                "Attached target is missing verified approval and ownership proof",
            )
        return self._activate(
            instance_id=instance_id,
            generation=generation,
            target=approved_target,
        )

    def resolve(self, *, instance_id: str, generation: int) -> ActiveTargetPin:
        with self._lock:
            pin = self._pins.get((instance_id, generation))
        if pin is None:
            raise TargetPinError(
                "SURFACE_TARGET_PIN_REVOKED",
                "Target pin is not active for this runtime generation",
            )
        return pin

    def revoke(self, *, instance_id: str, generation: int) -> bool:
        with self._lock:
            return self._pins.pop((instance_id, generation), None) is not None

    def revoke_instance(self, *, instance_id: str) -> int:
        with self._lock:
            keys = [key for key in self._pins if key[0] == instance_id]
            for key in keys:
                del self._pins[key]
            return len(keys)


__all__ = ["ActiveTargetPin", "TargetPinError", "TargetPinRegistry"]
