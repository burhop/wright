"""Inbound security policy for Wright's local control plane."""

from __future__ import annotations

import hmac
import hashlib
import ipaddress
import os
from dataclasses import dataclass

from fastapi import HTTPException, Request, WebSocket, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response


PUBLIC_PATHS = frozenset(
    {
        "/",
        "/api/auth/session",
        "/api/auth/session/status",
        "/api/health",
        "/api/runtime/identity",
        "/api/agent/health",
        "/api/inference/health",
        "/api/setup/status",
    }
)
SESSION_COOKIE = "wright_session"


def _csv_env(name: str, default: str) -> tuple[str, ...]:
    return tuple(
        item.strip().rstrip("/")
        for item in os.getenv(name, default).split(",")
        if item.strip()
    )


@dataclass(frozen=True)
class SecuritySettings:
    mode: str
    api_token: str | None
    allowed_origins: tuple[str, ...]
    bind_host: str
    native_runtime: bool = False

    @classmethod
    def from_env(cls) -> "SecuritySettings":
        testing = os.getenv("WRIGHT_TESTING") == "1"
        mode = os.getenv(
            "WRIGHT_AUTH_MODE", "compat" if testing else "enforced"
        ).lower()
        return cls(
            mode=mode,
            api_token=os.getenv("WRIGHT_API_TOKEN") or None,
            allowed_origins=_csv_env(
                "WRIGHT_ALLOWED_ORIGINS",
                "http://127.0.0.1:5173,http://localhost:5173",
            ),
            bind_host=os.getenv("WRIGHT_BIND_HOST", "127.0.0.1"),
            native_runtime=os.getenv("WRIGHT_NATIVE_RUNTIME") == "1",
        )

    @property
    def enforced(self) -> bool:
        return self.mode == "enforced"

    def validate(self) -> None:
        if self.mode not in {"enforced", "compat"}:
            raise RuntimeError("WRIGHT_AUTH_MODE must be 'enforced' or 'compat'")
        if any(origin == "*" for origin in self.allowed_origins):
            raise RuntimeError("WRIGHT_ALLOWED_ORIGINS must not contain a wildcard")
        if self.enforced and not self.api_token:
            raise RuntimeError(
                "WRIGHT_API_TOKEN is required when authentication is enforced"
            )
        try:
            loopback = ipaddress.ip_address(self.bind_host).is_loopback
        except ValueError:
            loopback = self.bind_host.lower() == "localhost"
        if not loopback and (not self.enforced or not self.api_token):
            raise RuntimeError(
                "Remote bind requires enforced authentication and WRIGHT_API_TOKEN"
            )

    def origin_allowed(self, origin: str | None) -> bool:
        return origin is None or origin.rstrip("/") in self.allowed_origins

    def token_valid(self, candidate: str | None) -> bool:
        return bool(
            self.api_token
            and candidate
            and hmac.compare_digest(candidate, self.api_token)
        )

    def browser_session_token(self) -> str | None:
        if not self.api_token:
            return None
        return hmac.new(
            self.api_token.encode("utf-8"),
            b"wright-browser-session-v1",
            hashlib.sha256,
        ).hexdigest()

    def browser_session_valid(self, candidate: str | None) -> bool:
        expected = self.browser_session_token()
        return bool(expected and candidate and hmac.compare_digest(candidate, expected))


def _host_name(value: str) -> str:
    value = value.strip().lower()
    if value.startswith("["):
        return value[1:].partition("]")[0]
    return value.rsplit(":", 1)[0]


def _loopback_host(value: str) -> bool:
    host = _host_name(value)
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def native_browser_bootstrap_allowed(
    request: Request, settings: SecuritySettings
) -> bool:
    """Allow the packaged loopback UI to receive a derived HttpOnly session."""
    if not (settings.native_runtime and settings.enforced and settings.api_token):
        return False
    if request.method != "GET" or request.url.path != "/":
        return False
    if not _loopback_host(request.headers.get("host", "")):
        return False
    client_host = request.client.host if request.client else ""
    if client_host and not _loopback_host(client_host):
        return False
    fetch_mode = request.headers.get("sec-fetch-mode")
    return fetch_mode in {None, "navigate"}


def _bearer(value: str | None) -> str | None:
    if not value:
        return None
    scheme, _, token = value.partition(" ")
    return token if scheme.lower() == "bearer" and token else None


class ControlPlaneSecurityMiddleware(BaseHTTPMiddleware):
    """Fail closed before protected HTTP handlers are invoked."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        settings: SecuritySettings = request.app.state.security_settings
        if not settings.origin_allowed(request.headers.get("origin")):
            return JSONResponse(
                status_code=403, content={"detail": "Origin is not allowed"}
            )
        if (
            settings.enforced
            and request.method != "OPTIONS"
            and (request.url.path.startswith("/api/") or request.url.path == "/mcp")
            and request.url.path not in PUBLIC_PATHS
        ):
            bearer = _bearer(request.headers.get("authorization"))
            browser_session = request.cookies.get(SESSION_COOKIE)
            if not (
                settings.token_valid(bearer)
                or settings.browser_session_valid(browser_session)
            ):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Authentication required"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            request.state.principal_role = "admin"
        response = await call_next(request)
        if native_browser_bootstrap_allowed(request, settings):
            browser_session = settings.browser_session_token()
            if browser_session is not None:
                response.set_cookie(
                    SESSION_COOKIE,
                    browser_session,
                    httponly=True,
                    secure=os.getenv("WRIGHT_COOKIE_SECURE", "0") == "1",
                    samesite="strict",
                    path="/api",
                )
        return response


def require_admin(request: Request) -> None:
    settings: SecuritySettings = request.app.state.security_settings
    if settings.enforced and getattr(request.state, "principal_role", None) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Administrator role required"
        )


def authorize_websocket(websocket: WebSocket, settings: SecuritySettings) -> str | None:
    """Validate a WebSocket before acceptance; return a protocol to echo, if any."""
    if not settings.origin_allowed(websocket.headers.get("origin")):
        raise HTTPException(status_code=403, detail="Origin is not allowed")
    if not settings.enforced:
        return None
    token = _bearer(websocket.headers.get("authorization"))
    browser_session = websocket.cookies.get(SESSION_COOKIE)
    selected = None
    for protocol in websocket.headers.get("sec-websocket-protocol", "").split(","):
        protocol = protocol.strip()
        if protocol.startswith("wright.bearer."):
            token = protocol.removeprefix("wright.bearer.")
            selected = protocol
            break
    if not (
        settings.token_valid(token) or settings.browser_session_valid(browser_session)
    ):
        raise HTTPException(status_code=401, detail="Authentication required")
    return selected
