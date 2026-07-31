"""Least-privilege browser policy projection for every surface source profile."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import AbstractSet


class SourceProfile(str, Enum):
    SAFE_DISPLAY = "safe_display"
    ACTIVE_HTML = "active_html"
    MANAGED_APP = "managed_app"
    ATTACHED_APP = "attached_app"
    MCP_APP = "mcp_app"
    EXTERNAL_URL = "external_url"


class BrowserPolicyError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class BrowserPolicyProjection:
    sandbox: tuple[str, ...]
    content_security_policy: str
    permissions_policy: str
    referrer_policy: str
    embedded: bool
    proxied: bool
    bridge_enabled: bool
    popup_enabled: bool
    download_enabled: bool
    top_navigation_enabled: bool


_FEATURES = frozenset(
    {
        "popup",
        "popup-escape",
        "download",
        "top-navigation",
        "clipboard-read",
        "clipboard-write",
        "camera",
        "microphone",
        "geolocation",
        "fullscreen",
        "modals",
    }
)


class BrowserPolicyProjector:
    def project(
        self,
        profile: SourceProfile,
        *,
        declared_capabilities: AbstractSet[str] = frozenset(),
        allowed_capabilities: AbstractSet[str] = frozenset(),
    ) -> BrowserPolicyProjection:
        undeclared = set(allowed_capabilities) - set(declared_capabilities)
        if undeclared:
            raise BrowserPolicyError("Allowed browser capability was not declared")
        unknown = set(declared_capabilities) - _FEATURES
        if unknown:
            raise BrowserPolicyError("Declared browser capability is unsupported")
        effective = set(declared_capabilities) & set(allowed_capabilities)

        denied_permissions = {
            "camera",
            "microphone",
            "geolocation",
            "clipboard-read",
            "clipboard-write",
            "fullscreen",
        }
        permission_parts = [
            f"{feature}={'(self)' if feature in effective else '()'}"
            for feature in sorted(denied_permissions)
        ]
        permissions_policy = ", ".join(permission_parts)

        if profile in {SourceProfile.SAFE_DISPLAY, SourceProfile.ACTIVE_HTML}:
            csp = (
                "default-src 'none'; img-src data: blob:; "
                "style-src 'unsafe-inline'; font-src data:"
            )
            return BrowserPolicyProjection(
                sandbox=(),
                content_security_policy=csp,
                permissions_policy=permissions_policy,
                referrer_policy="no-referrer",
                embedded=True,
                proxied=False,
                bridge_enabled=False,
                popup_enabled=False,
                download_enabled=False,
                top_navigation_enabled=False,
            )

        if profile is SourceProfile.EXTERNAL_URL:
            return BrowserPolicyProjection(
                sandbox=(),
                content_security_policy="default-src 'none'",
                permissions_policy=permissions_policy,
                referrer_policy="no-referrer",
                embedded=False,
                proxied=False,
                bridge_enabled=False,
                popup_enabled=False,
                download_enabled=False,
                top_navigation_enabled=False,
            )

        sandbox = {"allow-scripts", "allow-same-origin"}
        if profile in {SourceProfile.MANAGED_APP, SourceProfile.ATTACHED_APP}:
            sandbox.add("allow-forms")
        if "popup" in effective:
            sandbox.add("allow-popups")
        if "popup-escape" in effective:
            sandbox.update({"allow-popups", "allow-popups-to-escape-sandbox"})
        if "download" in effective:
            sandbox.add("allow-downloads")
        if "top-navigation" in effective:
            sandbox.add("allow-top-navigation-by-user-activation")
        if "modals" in effective:
            sandbox.add("allow-modals")
        csp = (
            "default-src 'self'; script-src 'self' blob:; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
            "font-src 'self' data:; connect-src 'self' ws: wss:; "
            "worker-src 'self' blob:; object-src 'none'; base-uri 'self'"
        )
        return BrowserPolicyProjection(
            sandbox=tuple(sorted(sandbox)),
            content_security_policy=csp,
            permissions_policy=permissions_policy,
            referrer_policy="no-referrer",
            embedded=True,
            proxied=True,
            bridge_enabled=True,
            popup_enabled="popup" in effective or "popup-escape" in effective,
            download_enabled="download" in effective,
            top_navigation_enabled="top-navigation" in effective,
        )


__all__ = [
    "BrowserPolicyError",
    "BrowserPolicyProjection",
    "BrowserPolicyProjector",
    "SourceProfile",
]
