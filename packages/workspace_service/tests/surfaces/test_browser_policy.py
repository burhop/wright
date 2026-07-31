from __future__ import annotations

import pytest

from workspace_service.surfaces.browser_policy import (
    BrowserPolicyError,
    BrowserPolicyProjector,
    SourceProfile,
)


pytestmark = pytest.mark.workspace_surfaces


def test_active_html_is_locked_without_script_origin_or_bridge_authority() -> None:
    policy = BrowserPolicyProjector().project(SourceProfile.ACTIVE_HTML)
    assert policy.sandbox == ()
    assert policy.bridge_enabled is False
    assert policy.referrer_policy == "no-referrer"
    assert "default-src 'none'" in policy.content_security_policy
    assert "camera=()" in policy.permissions_policy


def test_managed_javascript_apps_get_compatible_but_distinct_origin_policy() -> None:
    policy = BrowserPolicyProjector().project(SourceProfile.MANAGED_APP)
    assert set(policy.sandbox) == {"allow-forms", "allow-same-origin", "allow-scripts"}
    assert policy.bridge_enabled is True
    assert policy.popup_enabled is False
    assert policy.download_enabled is False
    assert policy.top_navigation_enabled is False
    assert "connect-src 'self' ws: wss:" in policy.content_security_policy


def test_sensitive_features_require_declared_and_effectively_allowed_grants() -> None:
    projector = BrowserPolicyProjector()
    policy = projector.project(
        SourceProfile.MANAGED_APP,
        declared_capabilities={"popup", "download", "clipboard-write"},
        allowed_capabilities={"popup", "clipboard-write"},
    )
    assert "allow-popups" in policy.sandbox
    assert "allow-downloads" not in policy.sandbox
    assert policy.popup_enabled is True
    assert policy.download_enabled is False
    assert "clipboard-write=(self)" in policy.permissions_policy
    assert "camera=()" in policy.permissions_policy

    with pytest.raises(BrowserPolicyError, match="not declared"):
        projector.project(
            SourceProfile.MANAGED_APP,
            declared_capabilities=set(),
            allowed_capabilities={"camera"},
        )


def test_external_urls_never_receive_proxy_or_bridge_promotion() -> None:
    policy = BrowserPolicyProjector().project(SourceProfile.EXTERNAL_URL)
    assert policy.embedded is False
    assert policy.proxied is False
    assert policy.bridge_enabled is False
    assert policy.sandbox == ()
