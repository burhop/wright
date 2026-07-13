"""Inbound security policy for Wright's local control plane."""

from __future__ import annotations

import hmac
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
        "/api/health",
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
            if not settings.token_valid(
                _bearer(request.headers.get("authorization"))
                or request.cookies.get(SESSION_COOKIE)
            ):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Authentication required"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            request.state.principal_role = "admin"
        return await call_next(request)


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
    token = token or websocket.cookies.get(SESSION_COOKIE)
    selected = None
    for protocol in websocket.headers.get("sec-websocket-protocol", "").split(","):
        protocol = protocol.strip()
        if protocol.startswith("wright.bearer."):
            token = protocol.removeprefix("wright.bearer.")
            selected = protocol
            break
    if not settings.token_valid(token):
        raise HTTPException(status_code=401, detail="Authentication required")
    return selected
