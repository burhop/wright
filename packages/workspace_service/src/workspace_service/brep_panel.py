"""Validation and readiness policy for the embedded BREP application panel."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from urllib.parse import parse_qs, urlsplit


BREP_PANEL_MODULE_URL = "http://127.0.0.1:5190/src/CAD.ts"
BREP_APPLICATION_STATUS_TOOL = "brep.app.status"
BREP_SOURCE_URL = "https://github.com/mmiscool/brep-mcp"


class BrepPanelError(RuntimeError):
    """A stable, user-facing BREP panel integration failure."""


@dataclass(frozen=True)
class BrepPanelStatus:
    control_url: str
    module_url: str
    connected: bool


def is_brep_application_server(server: Any) -> bool:
    """Identify the visible-application BREP MCP, excluding headless lookalikes."""

    source_url = str(getattr(server, "source_url", "") or "").rstrip("/").lower()
    return source_url == BREP_SOURCE_URL or (
        str(getattr(server, "name", "") or "").strip().lower() == "brep mcp"
        and "brep-mcp" in source_url
    )


def select_brep_application_server(servers: Sequence[Any]) -> Any:
    matches = [
        server
        for server in servers
        if bool(getattr(server, "is_installed", False))
        and is_brep_application_server(server)
    ]
    if not matches:
        raise BrepPanelError("The visible-application BREP MCP is not installed.")
    if len(matches) != 1:
        raise BrepPanelError(
            "More than one visible-application BREP MCP is installed; keep one exact registration."
        )
    return matches[0]


def panel_environment(
    current: Mapping[str, str] | None,
    *,
    module_url: str = BREP_PANEL_MODULE_URL,
) -> dict[str, str]:
    """Return the persisted process environment for Wright panel ownership."""

    _validate_loopback_url(module_url, label="BREP module URL")
    if urlsplit(module_url).port == 5173:
        raise BrepPanelError("BREP must not use Wright's development port 5173.")
    return {
        **{str(key): str(value) for key, value in (current or {}).items()},
        "BREP_CAD_MODULE_URL": module_url,
        "BREP_MCP_APP_PORT": "0",
        "BREP_MCP_AUTO_OPEN": "0",
    }


def parse_brep_status_result(result: Mapping[str, Any]) -> BrepPanelStatus:
    payload: Mapping[str, Any] | None = None
    structured = result.get("structuredContent")
    if isinstance(structured, Mapping):
        payload = structured
    if payload is None:
        for item in result.get("content", []):
            if not isinstance(item, Mapping) or item.get("type") != "text":
                continue
            text = item.get("text")
            if not isinstance(text, str):
                continue
            try:
                decoded = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(decoded, Mapping):
                payload = decoded
                break
    if payload is None:
        raise BrepPanelError("BREP MCP did not return an application status object.")

    control_url = payload.get("controlUrl")
    module_url = payload.get("moduleUrl")
    if not isinstance(control_url, str) or not isinstance(module_url, str):
        raise BrepPanelError("BREP MCP returned incomplete application URLs.")
    _validate_loopback_url(control_url, label="BREP control URL", require_token=True)
    _validate_loopback_url(module_url, label="BREP module URL")
    if urlsplit(module_url).port == 5173:
        raise BrepPanelError("BREP is still configured on Wright's port 5173.")
    return BrepPanelStatus(
        control_url=control_url,
        module_url=module_url,
        connected=payload.get("connected") is True,
    )


def wait_for_brep_module(
    module_url: str,
    *,
    timeout_seconds: float = 180.0,
    poll_seconds: float = 0.5,
) -> None:
    """Wait for only the validated loopback CAD module, without host proxies."""

    _validate_loopback_url(module_url, label="BREP module URL")
    deadline = time.monotonic() + timeout_seconds
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request = urllib.request.Request(module_url, method="GET")
    while True:
        try:
            with opener.open(request, timeout=min(3.0, timeout_seconds)) as response:
                if 200 <= response.status < 300:
                    return
        except (OSError, urllib.error.URLError):
            pass
        if time.monotonic() >= deadline:
            raise BrepPanelError(
                f"BREP did not become ready within {timeout_seconds:g} seconds."
            )
        time.sleep(poll_seconds)


def _validate_loopback_url(
    value: str,
    *,
    label: str,
    require_token: bool = False,
) -> None:
    parts = urlsplit(value)
    if parts.scheme != "http" or parts.hostname not in {
        "127.0.0.1",
        "localhost",
        "::1",
    }:
        raise BrepPanelError(f"{label} must be an HTTP loopback URL.")
    try:
        port = parts.port
    except ValueError as error:
        raise BrepPanelError(f"{label} has an invalid port.") from error
    if port is None:
        raise BrepPanelError(f"{label} must declare an explicit port.")
    if require_token:
        tokens = parse_qs(parts.query).get("token", [])
        if len(tokens) != 1 or len(tokens[0]) < 24:
            raise BrepPanelError(
                "BREP control URL is missing its per-process authorization token."
            )


__all__ = [
    "BREP_APPLICATION_STATUS_TOOL",
    "BREP_PANEL_MODULE_URL",
    "BrepPanelError",
    "BrepPanelStatus",
    "panel_environment",
    "parse_brep_status_result",
    "select_brep_application_server",
    "wait_for_brep_module",
]
