from __future__ import annotations

import pytest

from api.surface_proxy_security import (
    ProxySecurityError,
    filter_request_headers,
    filter_response_headers,
    validate_redirect,
)
from workspace_service.surfaces.target_policy import ResolvedTargetPin


pytestmark = pytest.mark.workspace_surfaces


def _pin() -> ResolvedTargetPin:
    return ResolvedTargetPin(
        scheme="https",
        numeric_address="203.0.113.7",
        port=8443,
        source_hostname="app.example.test",
        host_header="app.example.test:8443",
        server_name="app.example.test",
        base_path="/ui/",
        resolved_answers=("203.0.113.7",),
        ownership="attached_verified",
        ownership_proof="operator-approved",
    )


def test_request_strips_wright_forwarded_csrf_and_hop_by_hop_authority() -> None:
    filtered = filter_request_headers(
        [
            ("Authorization", "Bearer secret"),
            ("Cookie", "wright_surface=session; theme=dark; app_session=target"),
            ("X-Wright-Workspace-ID", "workspace-1"),
            ("X-CSRF-Token", "control-token"),
            ("Forwarded", "for=127.0.0.1;host=wright.local"),
            ("X-Forwarded-For", "127.0.0.1"),
            ("Connection", "keep-alive, x-private"),
            ("X-Private", "remove-me"),
            ("Host", "preview.test"),
            ("Accept", "text/html"),
        ],
        pin=_pin(),
    )
    lowered = {name.lower(): value for name, value in filtered}
    assert lowered["host"] == "app.example.test:8443"
    assert lowered["cookie"] == "theme=dark; app_session=target"
    assert lowered["accept"] == "text/html"
    for forbidden in (
        "authorization",
        "x-wright-workspace-id",
        "x-csrf-token",
        "forwarded",
        "x-forwarded-for",
        "connection",
        "x-private",
    ):
        assert forbidden not in lowered


def test_response_cookies_are_host_only_and_internal_names_are_denied() -> None:
    filtered = filter_response_headers(
        [
            ("Set-Cookie", "app_session=abc; Domain=.example.test; Path=/; HttpOnly"),
            ("Set-Cookie", "wright_surface=replace; Path=/"),
            ("Connection", "close"),
            ("Content-Security-Policy", "default-src 'self'"),
            ("X-Frame-Options", "SAMEORIGIN"),
        ]
    )
    assert ("Set-Cookie", "app_session=abc; Path=/; HttpOnly") in filtered
    assert all("wright_surface=" not in value for _name, value in filtered)
    assert ("Content-Security-Policy", "default-src 'self'") in filtered
    assert ("X-Frame-Options", "SAMEORIGIN") in filtered
    assert all(name.lower() != "connection" for name, _value in filtered)


def test_redirects_are_limited_to_the_pinned_target_and_rebased() -> None:
    assert validate_redirect("dashboard?tab=1", pin=_pin()) == "/ui/dashboard?tab=1"
    assert validate_redirect("/login", pin=_pin()) == "/login"
    assert (
        validate_redirect(
            "https://app.example.test:8443/ui/results#chart", pin=_pin()
        )
        == "/ui/results#chart"
    )
    with pytest.raises(ProxySecurityError, match="redirect target"):
        validate_redirect("https://evil.example/steal", pin=_pin())
    with pytest.raises(ProxySecurityError, match="credentials"):
        validate_redirect("https://user:pass@app.example.test:8443/", pin=_pin())
