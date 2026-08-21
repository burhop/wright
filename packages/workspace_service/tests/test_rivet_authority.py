from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from workspace_service.rivet_authority import (
    AuthorityClaims,
    RivetAuthorityError,
    RivetRunAuthorityService,
)


HEX = "b" * 64


def claims(now: datetime) -> AuthorityClaims:
    return AuthorityClaims(
        run_id="run-1",
        generation=1,
        workspace_id="workspace-1",
        session_id="session-1",
        workflow_id="workflow-1",
        workflow_revision=1,
        workflow_digest=HEX,
        graph_id="Main",
        review_digest=HEX,
        binding_set_digest=HEX,
        audience="http://127.0.0.1:43123/internal/rivet-mcp/v1",
        node_bindings={"wright:abcdefghijklmnop": HEX},
        issued_at=now,
        expires_at=now + timedelta(minutes=5),
    )


def test_authority_is_opaque_scoped_and_stores_only_digest():
    now = datetime(2026, 8, 13, tzinfo=UTC)
    service = RivetRunAuthorityService(clock=lambda: now)
    grant = service.mint(claims(now))
    assert len(grant.token) >= 43
    assert grant.token not in repr(service.snapshot(grant.authority_id))
    record = service.validate(
        grant.token,
        audience=grant.claims.audience,
        run_id="run-1",
        generation=1,
        node_handle="wright:abcdefghijklmnop",
        binding_digest=HEX,
    )
    assert record.authority_id == grant.authority_id
    with pytest.raises(RivetAuthorityError, match="scope"):
        service.validate(
            grant.token,
            audience=grant.claims.audience,
            run_id="other",
            generation=1,
        )


def test_authority_expires_revokes_and_cannot_survive_restart():
    now = datetime(2026, 8, 13, tzinfo=UTC)
    current = now
    service = RivetRunAuthorityService(clock=lambda: current)
    grant = service.mint(claims(now))
    service.revoke(grant.authority_id, reason="cancelled")
    with pytest.raises(RivetAuthorityError, match="revoked"):
        service.validate(
            grant.token,
            audience=grant.claims.audience,
            run_id="run-1",
            generation=1,
        )
    replacement = RivetRunAuthorityService(clock=lambda: current)
    with pytest.raises(RivetAuthorityError, match="unavailable"):
        replacement.validate(
            grant.token,
            audience=grant.claims.audience,
            run_id="run-1",
            generation=1,
        )

    expiring = RivetRunAuthorityService(clock=lambda: current)
    short = expiring.mint(
        AuthorityClaims(
            **{**claims(now).__dict__, "expires_at": now + timedelta(seconds=1)}
        )
    )
    current = now + timedelta(seconds=2)
    with pytest.raises(RivetAuthorityError, match="expired"):
        expiring.validate(
            short.token,
            audience=short.claims.audience,
            run_id="run-1",
            generation=1,
        )
