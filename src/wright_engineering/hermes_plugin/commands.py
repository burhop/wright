"""Thin Hermes command projection for Wright lifecycle results."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any
import urllib.error
import urllib.request

from wright_engineering.runtime.lifecycle import NativeLifecycle
from wright_engineering.runtime.models import LifecycleResult


HELP = """Wright Engineering Workspace

Usage: /wright <command>

  start       Install when needed and start the managed Wright runtime
  status      Show lifecycle and health state
  doctor      Run bounded installation diagnostics
  stop        Stop only the verified Wright runtime
  update      Stage and activate an exact compatible update
  rollback    Return to a compatible retained predecessor
  uninstall   Remove runtime code while preserving user data
  purge       Explicitly remove disclosed Wright-owned data
"""


def project_result(result: LifecycleResult) -> str:
    marker = "OK" if result.ok else "ERROR"
    lines = [f"{marker} [{result.code}] {result.summary}"]
    if result.details:
        lines.append(json.dumps(result.details, sort_keys=True))
    lines.extend(f"Next: {item}" for item in result.remediation)
    return "\n".join(lines)


async def handle_wright(
    raw_args: str,
    *,
    lifecycle: NativeLifecycle | None = None,
    api_client: NativeApiClient | None = None,
) -> str:
    arguments = raw_args.strip().split()
    if not arguments:
        return HELP
    runtime = lifecycle or NativeLifecycle.default()
    api = api_client or NativeApiClient()
    command = arguments[0].lower()
    if command == "start":
        result = await asyncio.to_thread(runtime.start)
    elif command == "status":
        result = await asyncio.to_thread(runtime.status)
    elif command == "doctor":
        result = await asyncio.to_thread(runtime.doctor)
    elif command == "stop":
        result = await asyncio.to_thread(runtime.stop)
    elif command == "update":
        requested_version = arguments[1] if len(arguments) > 1 else None
        result = await asyncio.to_thread(runtime.update, requested_version)
    elif command == "rollback":
        requested_version = arguments[1] if len(arguments) > 1 else None
        result = await asyncio.to_thread(runtime.rollback, requested_version)
    elif command == "uninstall":
        result = await asyncio.to_thread(runtime.uninstall)
    elif command == "purge":
        confirmation = arguments[1] if len(arguments) > 1 else None
        result = await asyncio.to_thread(runtime.purge, confirmation)
    elif command == "open":
        return "Wright UI: http://127.0.0.1:8000/"
    elif command in {"catalog", "info", "install"}:
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
        entry_id = arguments[1] if len(arguments) > 1 else ""
        if not entry_id:
            return f"Missing catalog ID. Usage: `/wright {command} <id>`"
        entry = next(
            (
                item
                for item in entries
                if (item.get("server_id") or item.get("id")) == entry_id
            ),
            None,
        )
        if entry is None:
            return f"Catalog entry '{entry_id}' was not found."
        if command == "info":
            return json.dumps(entry, sort_keys=True)
        installed = await asyncio.to_thread(api.install, entry_id)
        return f"Installed {entry_id}: {json.dumps(installed, sort_keys=True)}"
    else:
        return f"Command '{command}' is not available in this candidate yet.\n\n{HELP}"
    return project_result(result)


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


def register_commands(ctx: Any) -> None:
    async def handler(raw_args: str, **_: object) -> str:
        return await handle_wright(raw_args)

    ctx.register_command(
        name="wright",
        handler=handler,
        description="Install and operate the native Wright engineering workspace.",
        args_hint="<subcommand> [args...]",
    )
