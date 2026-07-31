from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from workspace_service.surfaces.endpoints import (
    EndpointOwnershipProof,
    ListenerIdentity,
)
from workspace_service.surfaces.health import ProbeResult
from workspace_service.surfaces.target_pins import TargetPinError, TargetPinRegistry
from workspace_service.surfaces.target_policy import TargetPolicy


pytestmark = pytest.mark.workspace_surfaces


def _ready(ok: bool = True) -> ProbeResult:
    return ProbeResult(
        ok=ok,
        attempts=1,
        elapsed_seconds=0.1,
        failure_kind=None if ok else "timeout",
        diagnostic_code=None if ok else "SURFACE_READINESS_TIMEOUT",
        message="ready" if ok else "not ready",
        observed_status=200 if ok else None,
    )


def _ownership(*, generation: int = 1) -> EndpointOwnershipProof:
    return EndpointOwnershipProof(
        instance_id="instance-1",
        generation=generation,
        listener=ListenerIdentity("127.0.0.1", 43123, 101, 50.0),
    )


def test_launched_pin_requires_readiness_and_exact_listener_ownership() -> None:
    registry = TargetPinRegistry(policy=TargetPolicy())
    with pytest.raises(TargetPinError, match="readiness"):
        registry.activate_launched(
            instance_id="instance-1",
            generation=1,
            readiness=_ready(False),
            ownership=_ownership(),
            scheme="http",
        )
    with pytest.raises(TargetPinError, match="ownership"):
        registry.activate_launched(
            instance_id="instance-1",
            generation=1,
            readiness=_ready(),
            ownership=_ownership(generation=2),
            scheme="http",
        )


def test_pin_is_immutable_idempotent_and_revocation_removes_route_authority() -> None:
    registry = TargetPinRegistry(policy=TargetPolicy())
    first = registry.activate_launched(
        instance_id="instance-1",
        generation=1,
        readiness=_ready(),
        ownership=_ownership(),
        scheme="http",
    )
    repeated = registry.activate_launched(
        instance_id="instance-1",
        generation=1,
        readiness=_ready(),
        ownership=_ownership(),
        scheme="http",
    )
    assert first == repeated
    assert registry.resolve(instance_id="instance-1", generation=1) == first
    with pytest.raises(FrozenInstanceError):
        first.generation = 2  # type: ignore[misc]

    assert registry.revoke(instance_id="instance-1", generation=1) is True
    assert registry.revoke(instance_id="instance-1", generation=1) is False
    with pytest.raises(TargetPinError, match="not active"):
        registry.resolve(instance_id="instance-1", generation=1)
