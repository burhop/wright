"""Serve Wright's verified Rivet 2 canvas artifact without runtime mutation."""

from __future__ import annotations

import argparse
import asyncio
import ipaddress
import json
import secrets
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import unquote, urlsplit

from agent_adapters.hermes_config import resolve_hermes_api_settings
from agent_adapters.hermes_openai_bridge import (
    HermesBridgeError,
    HermesOpenAICompatibilityBridge,
    HermesOpenAIBridgeSettings,
)


@dataclass(slots=True)
class RivetAiHost:
    bridge: HermesOpenAICompatibilityBridge | None
    token: str | None
    expires_at: datetime | None
    maximum_request_bytes: int
    token_ttl_seconds: int
    _token_lock: threading.Lock = field(
        default_factory=threading.Lock,
        init=False,
        repr=False,
    )

    @property
    def available(self) -> bool:
        return self.bridge is not None and self.bridge.available

    def accepts_token(self, supplied: str) -> bool:
        with self._token_lock:
            now = datetime.now(UTC)
            accepted = (
                self.available
                and self.token is not None
                and self.expires_at is not None
                and now < self.expires_at
                and secrets.compare_digest(supplied, self.token)
            )
            if accepted:
                # Graph Builder may make many sequential model calls. Keep an
                # actively used, loopback-only lease alive so a draft cannot
                # fail halfway through merely because its initial five-minute
                # window elapsed. Idle and invalid credentials are never
                # renewed.
                self.expires_at = now + timedelta(seconds=self.token_ttl_seconds)
            return accepted

    def config(self) -> dict[str, Any]:
        if not self.available:
            return {"available": False, "reason": "hermes_unavailable"}
        with self._token_lock:
            now = datetime.now(UTC)
            if self.token is None or self.expires_at is None or now >= self.expires_at:
                self.token = secrets.token_urlsafe(32)
            # Fetching config marks the beginning of a browser operation. Give
            # it a complete lease even when the token already existed, then
            # accepts_token extends that lease on each valid AI request.
            self.expires_at = now + timedelta(seconds=self.token_ttl_seconds)
        return {
            "available": True,
            "provider": "custom",
            "model": "wright-hermes",
            "baseUrl": "/wright-ai/v1",
            "token": self.token,
            "expiresAt": self.expires_at.isoformat().replace("+00:00", "Z"),
        }


class RivetCanvasHandler(SimpleHTTPRequestHandler):
    """Static host with a bounded health endpoint and SPA route fallback."""

    server_version = "WrightRivetCanvas/2"

    def __init__(self, *args, directory: str, ai_host: RivetAiHost, **kwargs) -> None:
        self._artifact_root = Path(directory).resolve()
        self._ai_host = ai_host
        super().__init__(*args, directory=directory, **kwargs)

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Permissions-Policy",
            "camera=(), geolocation=(), microphone=(), payment=(), usb=()",
        )
        super().end_headers()

    def _send_health(self, *, include_body: bool) -> None:
        body = json.dumps({"status": "ok", "mode": "rivet2-canvas"}).encode()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if include_body:
            self.wfile.write(body)

    def _send_json(
        self,
        status: HTTPStatus,
        value: Mapping[str, Any] | dict[str, Any],
        *,
        include_body: bool = True,
    ) -> None:
        body = json.dumps(value, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if include_body:
            self.wfile.write(body)

    def _send_ai_error(self, error: HermesBridgeError) -> None:
        self._send_json(HTTPStatus(error.status_code), error.envelope())

    def _is_loopback_client(self) -> bool:
        try:
            return ipaddress.ip_address(self.client_address[0]).is_loopback
        except ValueError:
            return False

    def _ai_token_is_valid(self) -> bool:
        supplied = self.headers.get("X-Rivet-AI-Token", "").strip()
        if not supplied:
            # Keep direct-host compatibility for local diagnostics. Embedded
            # browser traffic uses the dedicated header because Wright's
            # surface boundary strips generic Authorization credentials.
            authorization = self.headers.get("Authorization", "")
            prefix = "Bearer "
            supplied = (
                authorization[len(prefix) :]
                if authorization.startswith(prefix)
                else ""
            )
        return self._ai_host.accepts_token(supplied)

    def _is_spa_route(self) -> bool:
        request_path = unquote(urlsplit(self.path).path)
        relative = request_path.lstrip("/")
        candidate = (self._artifact_root / relative).resolve()
        if (
            candidate != self._artifact_root
            and self._artifact_root not in candidate.parents
        ):
            return False
        return not candidate.exists() and Path(request_path).suffix == ""

    def _serve_index(self, *, include_body: bool) -> None:
        index = self._artifact_root / "index.html"
        body = index.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if include_body:
            self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        request_path = urlsplit(self.path).path
        if request_path == "/health":
            self._send_health(include_body=True)
            return
        if request_path == "/wright-ai/config":
            self._send_json(HTTPStatus.OK, self._ai_host.config())
            return
        if request_path.startswith("/wright-ai/"):
            self._send_json(
                HTTPStatus.NOT_FOUND,
                HermesBridgeError(
                    "invalid_request", "AI route was not found.", status_code=404
                ).envelope(),
            )
            return
        if self._is_spa_route():
            self._serve_index(include_body=True)
            return
        super().do_GET()

    def do_HEAD(self) -> None:  # noqa: N802 - stdlib handler API
        request_path = urlsplit(self.path).path
        if request_path == "/health":
            self._send_health(include_body=False)
            return
        if request_path == "/wright-ai/config":
            self._send_json(HTTPStatus.OK, self._ai_host.config(), include_body=False)
            return
        if request_path.startswith("/wright-ai/"):
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {"error": {"code": "invalid_request"}},
                include_body=False,
            )
            return
        if self._is_spa_route():
            self._serve_index(include_body=False)
            return
        super().do_HEAD()

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        if urlsplit(self.path).path != "/wright-ai/v1/chat/completions":
            self._send_json(
                HTTPStatus.NOT_FOUND,
                HermesBridgeError(
                    "invalid_request", "AI route was not found.", status_code=404
                ).envelope(),
            )
            return
        if not self._is_loopback_client():
            self._send_ai_error(
                HermesBridgeError(
                    "invalid_token", "AI request is not authorized.", status_code=403
                )
            )
            return
        if not self._ai_token_is_valid():
            self._send_ai_error(
                HermesBridgeError(
                    "invalid_token",
                    "AI request token is invalid or expired.",
                    status_code=401,
                )
            )
            return
        content_type = (
            self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        )
        if content_type != "application/json":
            self._send_ai_error(
                HermesBridgeError(
                    "invalid_request",
                    "Content-Type must be application/json.",
                    status_code=415,
                )
            )
            return
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            length = -1
        if length < 0 or length > self._ai_host.maximum_request_bytes:
            self._send_ai_error(
                HermesBridgeError(
                    "invalid_request",
                    "AI request body exceeds the configured limit.",
                    status_code=413,
                )
            )
            return
        try:
            payload = json.loads(self.rfile.read(length))
        except (UnicodeError, json.JSONDecodeError):
            self._send_ai_error(
                HermesBridgeError(
                    "invalid_request", "AI request body must be valid JSON."
                )
            )
            return
        if not isinstance(payload, dict) or self._ai_host.bridge is None:
            self._send_ai_error(
                HermesBridgeError(
                    "hermes_unavailable", "Hermes AI is unavailable.", status_code=503
                )
            )
            return
        request_id = secrets.token_hex(16)
        if payload.get("stream") is True:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()

            async def relay() -> None:
                async for chunk in self._ai_host.bridge.stream(
                    payload, request_id=request_id
                ):
                    self.wfile.write(chunk.encode())
                    self.wfile.flush()

            try:
                asyncio.run(relay())
            except (BrokenPipeError, ConnectionResetError):
                return
            except HermesBridgeError as error:
                self.wfile.write(
                    f"data: {json.dumps(error.envelope(), separators=(',', ':'))}\n\ndata: [DONE]\n\n".encode()
                )
            finally:
                self.close_connection = True
            return
        try:
            result = asyncio.run(
                self._ai_host.bridge.complete(payload, request_id=request_id)
            )
        except HermesBridgeError as error:
            self._send_ai_error(error)
            return
        self._send_json(HTTPStatus.OK, result)

    def _method_not_allowed(self) -> None:
        if urlsplit(self.path).path.startswith("/wright-ai/"):
            self._send_json(
                HTTPStatus.METHOD_NOT_ALLOWED,
                HermesBridgeError(
                    "invalid_request", "HTTP method is not allowed.", status_code=405
                ).envelope(),
            )
            return
        self.send_error(HTTPStatus.NOT_IMPLEMENTED)

    do_PUT = _method_not_allowed  # type: ignore[assignment]  # noqa: N815
    do_PATCH = _method_not_allowed  # type: ignore[assignment]  # noqa: N815
    do_DELETE = _method_not_allowed  # type: ignore[assignment]  # noqa: N815
    do_OPTIONS = _method_not_allowed  # type: ignore[assignment]  # noqa: N815

    def log_message(self, format: str, *args: object) -> None:
        return


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the Wright Rivet 2 canvas")
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--ai-enabled", action="store_true")
    parser.add_argument("--ai-token-ttl", default=300, type=int)
    parser.add_argument("--ai-request-bytes", default=2 * 1024 * 1024, type=int)
    parser.add_argument("--ai-timeout", default=300.0, type=float)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    if not root.is_dir() or not (root / "index.html").is_file():
        raise SystemExit(f"Rivet canvas artifact is unavailable: {root}")

    if args.ai_enabled and args.host not in {"127.0.0.1", "::1", "localhost"}:
        raise SystemExit("Rivet AI bridge may bind only to loopback")
    if (
        not 1 <= args.ai_token_ttl <= 3600
        or not 1024 <= args.ai_request_bytes <= 10 * 1024 * 1024
    ):
        raise SystemExit("Rivet AI bridge limits are invalid")

    ai_host = RivetAiHost(
        None,
        None,
        None,
        args.ai_request_bytes,
        args.ai_token_ttl,
    )
    if args.ai_enabled:
        hermes = resolve_hermes_api_settings()
        bridge = HermesOpenAICompatibilityBridge(
            HermesOpenAIBridgeSettings(
                base_url=hermes.base_url,
                api_key=hermes.api_key,
                timeout_seconds=args.ai_timeout,
            )
        )
        if bridge.available:
            ai_host = RivetAiHost(
                bridge,
                None,
                None,
                args.ai_request_bytes,
                args.ai_token_ttl,
            )

    def handler(*handler_args, **handler_kwargs):
        return RivetCanvasHandler(
            *handler_args,
            directory=str(root),
            ai_host=ai_host,
            **handler_kwargs,
        )

    server = ThreadingHTTPServer((args.host, args.port), handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
