"""Hermes `/wright` projection using only Python's standard library."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any
import urllib.request

from .bootstrap import BootstrapError, invoke_lifecycle


WRIGHT_HELP_TEXT = """Wright Engineering Workspace

Usage: /wright <command>

  start       Install when needed and start the managed Wright runtime
  status      Show lifecycle and health state
  doctor      Run bounded installation diagnostics
  stop        Stop only the verified Wright runtime
  update      Stage and activate an exact compatible update
  rollback    Return to a compatible retained predecessor
  uninstall   Remove Wright runtime code while preserving user data
  purge       Explicitly remove disclosed Wright-owned data
"""


def project_result(result: dict[str, object]) -> str:
    marker = "OK" if result.get("ok") is True else "ERROR"
    code = result.get("code", "unknown")
    summary = result.get("summary", "Wright returned no summary.")
    lines = [f"{marker} [{code}] {summary}"]
    details = result.get("details")
    if isinstance(details, dict) and details:
        lines.append(json.dumps(details, sort_keys=True))
    remediation = result.get("remediation")
    if isinstance(remediation, list):
        lines.extend(f"Next: {item}" for item in remediation if isinstance(item, str))
    return "\n".join(lines)


class NativeApiClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        self.base_url = base_url.rstrip("/")

    def _request(self, path: str, *, method: str = "GET") -> object:
        token = os.environ.get("WRIGHT_API_TOKEN", "").strip()
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        request = urllib.request.Request(
            f"{self.base_url}{path}", method=method, headers=headers
        )
        with urllib.request.urlopen(request, timeout=3.0) as response:
            return json.load(response)

    def list_catalog(self) -> list[dict[str, object]]:
        payload = self._request("/api/mcp/servers")
        if not isinstance(payload, dict) or not isinstance(
            payload.get("servers"), list
        ):
            raise ValueError("catalog_response_invalid")
        return [item for item in payload["servers"] if isinstance(item, dict)]

    def install(self, server_id: str) -> dict[str, object]:
        payload = self._request(f"/api/mcp/servers/{server_id}/install", method="POST")
        if not isinstance(payload, dict):
            raise ValueError("install_response_invalid")
        return payload


async def handle_wright(
    raw_args: str,
    *,
    invoker=invoke_lifecycle,
    api_client: NativeApiClient | None = None,
) -> str:
    arguments = raw_args.strip().split()
    if not arguments:
        return WRIGHT_HELP_TEXT
    command = arguments[0].lower()
    argument = arguments[1] if len(arguments) > 1 else None
    if command == "open":
        return "Wright UI: http://127.0.0.1:8000/"
    if command in {"catalog", "info", "install"}:
        api = api_client or NativeApiClient()
        try:
            entries = await asyncio.to_thread(api.list_catalog)
        except Exception:
            return (
                "Wright's packaged API is not reachable. Run `/wright start` and retry."
            )
        if command == "catalog":
            return (
                "\n".join(
                    f"- {item.get('server_id') or item.get('id')}: {item.get('name')}"
                    for item in entries
                )
                or "The packaged catalog is empty."
            )
        if not argument:
            return f"Missing catalog ID. Usage: `/wright {command} <id>`"
        entry = next(
            (
                item
                for item in entries
                if (item.get("server_id") or item.get("id")) == argument
            ),
            None,
        )
        if entry is None:
            return f"Catalog entry '{argument}' was not found."
        if command == "info":
            return json.dumps(entry, sort_keys=True)
        installed = await asyncio.to_thread(api.install, argument)
        return f"Installed {argument}: {json.dumps(installed, sort_keys=True)}"
    try:
        result = await asyncio.to_thread(invoker, command, argument)
    except BootstrapError as exc:
        return f"ERROR [bootstrap_failed] Wright could not run: {exc}"
    return project_result(result)


def register_commands(ctx: Any) -> None:
    async def handler(raw_args: str, **_: object) -> str:
        return await handle_wright(raw_args)

    ctx.register_command(
        name="wright",
        handler=handler,
        description="Install and operate the managed Wright engineering workspace.",
        args_hint="<subcommand> [args...]",
    )


__all__ = [
    "WRIGHT_HELP_TEXT",
    "handle_wright",
    "project_result",
    "register_commands",
]
