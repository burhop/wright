"""Route opaque preview subdomains away from the Wright control plane."""

from __future__ import annotations

from starlette.types import ASGIApp, Receive, Scope, Send


class SurfaceHostDispatchMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        preview_app: ASGIApp,
        preview_domain: str,
    ) -> None:
        self.app = app
        self.preview_app = preview_app
        self.preview_domain = preview_domain.lower().rstrip(".")

    def _is_preview_host(self, scope: Scope) -> bool:
        raw_host = next(
            (value for name, value in scope.get("headers", ()) if name == b"host"),
            b"",
        )
        try:
            authority = raw_host.decode("ascii").lower()
        except UnicodeDecodeError:
            return False
        hostname = authority.rsplit(":", 1)[0].rstrip(".")
        suffix = f".{self.preview_domain}"
        if not hostname.endswith(suffix):
            return False
        label = hostname[: -len(suffix)]
        return label.startswith("s-") and len(label) > 2 and "." not in label

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in {"http", "websocket"} and self._is_preview_host(scope):
            await self.preview_app(scope, receive, send)
            return
        await self.app(scope, receive, send)


__all__ = ["SurfaceHostDispatchMiddleware"]
