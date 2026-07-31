from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from workspace_service.surfaces.external_urls import (
    ExternalUrlApprovalError,
    ExternalUrlApprovalService,
)
from workspace_service.surfaces.service import ActorRole, SurfaceActor


pytestmark = pytest.mark.workspace_surfaces
NOW = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)


def _actor(**overrides) -> SurfaceActor:
    values = {
        "user_id": "user-1",
        "workspace_id": "workspace-1",
        "session_id": "session-1",
        "role": ActorRole.ENGINEER,
    }
    values.update(overrides)
    return SurfaceActor(**values)


def test_explicit_approval_is_exact_direct_only_and_unprivileged() -> None:
    service = ExternalUrlApprovalService(
        clock=lambda: NOW, id_factory=lambda: "approval-1"
    )
    approval = service.approve(
        actor=_actor(),
        url="HTTPS://Docs.Example.Test:443/guide?tab=1#intro",
        acknowledged=True,
        reason="Open the vendor documentation",
    )
    assert approval.normalized_url == "https://docs.example.test/guide?tab=1#intro"
    assert approval.direct_navigation is True
    assert approval.proxied is False
    assert approval.wright_credentials is False
    assert approval.bridge_enabled is False
    assert approval.managed_lifecycle is False
    assert (
        service.authorize(
            actor=_actor(), approval_id="approval-1", url=approval.normalized_url
        )
        == approval
    )

    with pytest.raises(ExternalUrlApprovalError, match="scope"):
        service.authorize(
            actor=_actor(user_id="user-2"),
            approval_id="approval-1",
            url=approval.normalized_url,
        )
    with pytest.raises(ExternalUrlApprovalError, match="destination"):
        service.authorize(
            actor=_actor(),
            approval_id="approval-1",
            url="https://docs.example.test/other",
        )


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "javascript:alert(1)",
        "https://user:pass@example.test/",
        "http://127.0.0.1:8000/",
        "http://[::1]/",
        "http://169.254.169.254/latest/meta-data/",
        "https://example.test\\@evil.test/",
    ],
)
def test_unsafe_external_destinations_are_rejected(url: str) -> None:
    service = ExternalUrlApprovalService(clock=lambda: NOW)
    with pytest.raises(ExternalUrlApprovalError):
        service.approve(
            actor=_actor(), url=url, acknowledged=True, reason="Open documentation"
        )


def test_approval_requires_disclosure_and_expires() -> None:
    current = [NOW]
    service = ExternalUrlApprovalService(
        clock=lambda: current[0], id_factory=lambda: "approval-1", ttl_seconds=60
    )
    with pytest.raises(ExternalUrlApprovalError, match="acknowledgement"):
        service.approve(
            actor=_actor(),
            url="https://docs.example.test/",
            acknowledged=False,
            reason="Open documentation",
        )
    approval = service.approve(
        actor=_actor(),
        url="https://docs.example.test/",
        acknowledged=True,
        reason="Open documentation",
    )
    current[0] = NOW + timedelta(seconds=61)
    with pytest.raises(ExternalUrlApprovalError, match="expired"):
        service.authorize(
            actor=_actor(),
            approval_id=approval.approval_id,
            url=approval.normalized_url,
        )
