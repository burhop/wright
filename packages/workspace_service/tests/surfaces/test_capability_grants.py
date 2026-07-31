from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from data_vault import upgrade_database
from workspace_service.surfaces.grants import (
    CapabilityGrantError,
    CapabilityGrantService,
    CapabilityPolicy,
    CapabilityRequest,
)
from workspace_service.surfaces.service import ActorRole, SurfaceActor


pytestmark = pytest.mark.workspace_surfaces
NOW = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)


def _actor(*, user: str = "user-1", role: ActorRole = ActorRole.ENGINEER):
    return SurfaceActor(
        user_id=user,
        workspace_id="workspace-1",
        session_id="session-1",
        role=role,
    )


def _service(tmp_path: Path, *, policy: CapabilityPolicy | None = None):
    tmp_path.mkdir(parents=True, exist_ok=True)
    database = tmp_path / "state.db"
    upgrade_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace-1', 'session-1', '/workspace/one', 1, 1)"""
        )
        connection.commit()
    current = [NOW]
    service = CapabilityGrantService(
        database,
        clock=lambda: current[0],
        id_factory=lambda: (
            f"grant-{len(service.repository.list(user_id='user-1', workspace_id='workspace-1', source_id='app', source_version='1.0')) + 1}"
        ),
        policy=policy or CapabilityPolicy(),
    )
    return current, service


def _request(**overrides) -> CapabilityRequest:
    values = {
        "source_id": "app",
        "source_version": "1.0",
        "instance_id": "instance-1",
        "capability": "workspace.read_selection",
        "operation": "read",
        "constraints": {"maximumItems": 10},
        "risk_tier": "low",
        "persistence": "remembered_exact",
        "duration_seconds": 600,
        "declared": True,
        "decision": "allow",
        "reason": "Use the selected rows in this chart",
    }
    values.update(overrides)
    return CapabilityRequest(**values)


def test_low_risk_grant_is_exactly_scoped_and_expires(tmp_path: Path) -> None:
    clock, service = _service(tmp_path)
    grant = service.decide(actor=_actor(), request=_request())
    assert grant.expires_at == NOW + timedelta(seconds=600)
    assert (
        service.authorize(actor=_actor(), request=_request()).grant_id == grant.grant_id
    )

    with pytest.raises(CapabilityGrantError, match="grant scope"):
        service.authorize(actor=_actor(), request=_request(source_version="2.0"))
    with pytest.raises(CapabilityGrantError, match="grant scope"):
        service.authorize(actor=_actor(user="user-2"), request=_request())
    clock[0] = NOW + timedelta(seconds=601)
    with pytest.raises(CapabilityGrantError, match="expired"):
        service.authorize(actor=_actor(), request=_request())


def test_high_risk_and_mutating_grants_cannot_be_remembered(tmp_path: Path) -> None:
    _clock, service = _service(tmp_path)
    for risk in ("high", "mutating"):
        with pytest.raises(CapabilityGrantError, match="instance or operation"):
            service.decide(
                actor=_actor(),
                request=_request(risk_tier=risk, persistence="remembered_exact"),
            )

    operation = service.decide(
        actor=_actor(),
        request=_request(risk_tier="mutating", persistence="operation"),
    )
    assert (
        service.authorize(
            actor=_actor(),
            request=_request(risk_tier="mutating", persistence="operation"),
        ).grant_id
        == operation.grant_id
    )
    with pytest.raises(CapabilityGrantError, match="consumed"):
        service.authorize(
            actor=_actor(),
            request=_request(risk_tier="mutating", persistence="operation"),
        )


def test_revocation_denial_and_stricter_policy_override_allow(tmp_path: Path) -> None:
    _clock, service = _service(tmp_path)
    grant = service.decide(actor=_actor(), request=_request())
    service.revoke(actor=_actor(), grant_id=grant.grant_id)
    with pytest.raises(CapabilityGrantError, match="revoked"):
        service.authorize(actor=_actor(), request=_request())

    service.decide(actor=_actor(), request=_request(decision="deny"))
    with pytest.raises(CapabilityGrantError, match="denied"):
        service.authorize(actor=_actor(), request=_request())

    _clock, narrowed = _service(
        tmp_path / "narrowed",
        policy=CapabilityPolicy(
            denied_capabilities=frozenset({"workspace.read_selection"})
        ),
    )
    with pytest.raises(CapabilityGrantError, match="policy"):
        narrowed.decide(actor=_actor(), request=_request())


def test_engineer_self_grant_and_administrator_only_operations(tmp_path: Path) -> None:
    _clock, service = _service(tmp_path)
    service.decide(actor=_actor(), request=_request())
    for capability in ("target.attach", "policy.broaden"):
        with pytest.raises(CapabilityGrantError, match="administrator"):
            service.decide(actor=_actor(), request=_request(capability=capability))
        assert (
            service.decide(
                actor=_actor(role=ActorRole.ADMIN),
                request=_request(capability=capability),
            ).decision
            == "allow"
        )

    with pytest.raises(CapabilityGrantError, match="declared"):
        service.decide(actor=_actor(), request=_request(declared=False))
