from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import BinaryIO
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class McpBridgeError(RuntimeError):
    """Stable, redacted public bridge failure."""


def _response_payload(content_type: str, body: bytes) -> bytes | None:
    if not body:
        return None
    if "text/event-stream" in content_type:
        data = [line[6:] for line in body.splitlines() if line.startswith(b"data: ")]
        return data[-1] if data else None
    return body


def serve_stdio(
    *,
    workspace: Path,
    api_url: str = "http://127.0.0.1:8000",
    session_id: str = "wright-engineering",
    token_env: str = "WRIGHT_API_TOKEN",
    stdin: BinaryIO | None = None,
    stdout: BinaryIO | None = None,
) -> int:
    """Bridge newline-delimited MCP STDIO messages to Wright Streamable HTTP."""
    source = stdin or sys.stdin.buffer
    sink = stdout or sys.stdout.buffer
    token = os.environ.get(token_env)
    if not token:
        raise McpBridgeError(
            f"required bearer token environment variable is not set: {token_env}"
        )
    transport_session: str | None = None
    endpoint = f"{api_url.rstrip('/')}/mcp"
    workspace_identity = str(workspace)
    for raw_line in source:
        if not raw_line.strip():
            continue
        try:
            message = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise McpBridgeError("invalid JSON on MCP STDIO input") from exc
        protocol = "2025-11-25"
        if message.get("method") == "initialize":
            protocol = str(message.get("params", {}).get("protocolVersion", protocol))
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Origin": "http://127.0.0.1",
            "MCP-Protocol-Version": protocol,
            "X-Wright-Session-Id": session_id,
            "X-Wright-Workspace-Id": workspace_identity,
        }
        if transport_session:
            headers["Mcp-Session-Id"] = transport_session
        request = Request(
            endpoint, data=json.dumps(message).encode(), headers=headers, method="POST"
        )
        try:
            with urlopen(request, timeout=130) as response:  # noqa: S310 - explicit operator URL
                transport_session = response.headers.get(
                    "Mcp-Session-Id", transport_session
                )
                payload = _response_payload(
                    response.headers.get("Content-Type", ""), response.read()
                )
        except (HTTPError, URLError, TimeoutError) as exc:
            raise McpBridgeError(
                f"Wright MCP transport failed: {type(exc).__name__}"
            ) from exc
        if payload:
            sink.write(payload.rstrip(b"\r\n") + b"\n")
            sink.flush()
    return 0
