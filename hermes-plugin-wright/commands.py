"""Hermes `/wright` projection using only Python's standard library."""

from __future__ import annotations

import asyncio
import json
import importlib.metadata
import importlib.util
import re
import shlex
import subprocess
import sys
import os
import time
import secrets
import tempfile
from pathlib import Path
from urllib.parse import urlsplit
from typing import Any
import urllib.request

from .bootstrap import BootstrapError, invoke_lifecycle


WRIGHT_HELP_TEXT = """Wright Engineering Workspace

Usage: /wright <command>

  start       Install when needed and start the managed Wright runtime
  status      Show lifecycle and health state
  doctor      Run bounded installation diagnostics
  setup-browser  Prepare this Hermes profile for local Wright browser chat
  stop        Stop only the verified Wright runtime
  update      Stage and activate an exact compatible update
  rollback    Return to a compatible retained predecessor
  uninstall   Remove Wright runtime code while preserving user data
  purge       Explicitly remove disclosed Wright-owned data
"""


def _profile_env() -> tuple[Path, dict[str, str]]:
    profile = Path(os.environ.get("HERMES_HOME") or Path.home() / ".hermes").expanduser()
    path = profile / ".env"
    if path.is_symlink():
        raise ValueError("The Hermes .env is a symbolic link; use Hermes setup for this profile.")
    values = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.strip().removeprefix("export ").partition("=")
            if separator and key and not key.startswith("#"):
                values[key.strip()] = value.strip().strip("\"'")
    return path, values


def setup_browser() -> str:
    """Prepare only the invoking profile; Hermes continues to own its API server."""
    try:
        path, values = _profile_env()
        if not path.parent.is_dir():
            return "Hermes profile was not found. Run Hermes setup before configuring browser chat."
        explicit = os.environ.get("HERMES_API_BASE_URL") or values.get("HERMES_API_BASE_URL")
        if explicit and urlsplit(explicit).hostname not in {"localhost", "127.0.0.1", "::1"}:
            return "This profile uses a custom remote Hermes API. Its settings were preserved; start or repair that configured service using its normal setup."
        if explicit:
            return "This profile already specifies a Hermes API URL. Its settings were preserved; start that configured API server and restart Wright."
        host = os.environ.get("API_SERVER_HOST") or values.get("API_SERVER_HOST") or "127.0.0.1"
        if host not in {"localhost", "127.0.0.1"}:
            return "This profile has a non-loopback API host. Use Hermes setup to review it; Wright's local setup left it unchanged."
        port = os.environ.get("API_SERVER_PORT") or values.get("API_SERVER_PORT") or "8642"
        if not port.isdigit() or not 1024 <= int(port) <= 65535:
            return "The configured Hermes API port is invalid; correct it in Hermes setup."
        server_key = os.environ.get("API_SERVER_KEY") or values.get("API_SERVER_KEY", "")
        client_key = os.environ.get("HERMES_API_KEY") or values.get("HERMES_API_KEY", "")
        if server_key and client_key and server_key != client_key:
            return "The Hermes API client and server keys disagree. Review them in Hermes setup; Wright left both values unchanged."
        existing_key = server_key or client_key
        if any(character.isspace() for character in existing_key) or any(character in existing_key for character in "\"'#"):
            return "The existing API key needs Hermes's own configuration editor. Wright left its value unchanged."
        if existing_key and len(existing_key) < 16:
            return "The existing Hermes API key is too short. Replace it through Hermes setup, then retry. Its value was preserved."
        enabled = os.environ.get("API_SERVER_ENABLED") or values.get("API_SERVER_ENABLED", "")
        if enabled.lower() in {"false", "0", "no"}:
            return "This profile explicitly disables the Hermes API. Enable it through Hermes setup before retrying; Wright left that choice unchanged."
        additions = {
            "API_SERVER_ENABLED": "true",
            "API_SERVER_HOST": host,
            "API_SERVER_PORT": port,
            "API_SERVER_KEY": existing_key or secrets.token_urlsafe(32),
        }
        additions = {key: value for key, value in additions.items() if not values.get(key)}
        if additions:
            previous = path.read_text(encoding="utf-8") if path.is_file() else ""
            remaining = dict(additions)
            lines = []
            for line in previous.splitlines(keepends=True):
                key, separator, _ = line.strip().removeprefix("export ").partition("=")
                key = key.strip()
                if separator and key in additions:
                    lines.append(f"{key}={additions[key]}\n")
                    remaining.pop(key, None)
                else:
                    lines.append(line)
            previous = "".join(lines)
            if previous and not previous.endswith("\n"):
                previous += "\n"
            previous += "\n# Local browser access prepared by /wright setup-browser\n"
            previous += "".join(f"{key}={value}\n" for key, value in remaining.items())
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(previous)
            try:
                temporary.chmod(0o600)
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)
        if os.name == "nt":
            profile_path = str(path.parent).replace("'", "''")
            gateway_command = f"$env:HERMES_HOME = '{profile_path}'; hermes gateway run"
        else:
            gateway_command = shlex.join(["env", f"HERMES_HOME={path.parent}", "hermes", "gateway", "run"])
        readiness = host_mcp_readiness()
        dependency_note = readiness + "\n" if readiness else ""
        result = (
            "Local browser connection settings are prepared for this Hermes profile. "
            "The private API key is stored in its .env and is not displayed.\n"
            f"{dependency_note}"
            f"Next: open a second terminal and run `{gateway_command}`. "
            "Keep that terminal running. If the MCP dependency above is missing, install it "
            "using the displayed command before starting the gateway, then restart Hermes.\n"
            "Next: run `/wright start` and open its workspace URL. "
            "If Wright was already running before setup, run `/wright stop` first "
            "so the next start reads the connection settings. Refresh any existing Wright browser page.\n"
            "If Hermes reports that its API platform is disabled in config.yaml, enable it using Hermes setup. "
            "This command does not start services or change model, account, tool or approval settings."
        )
        return result
    except (OSError, ValueError) as error:
        return f"Browser setup could not prepare this profile ({type(error).__name__}). Use Hermes setup; no credential value is shown."


def host_mcp_readiness() -> str:
    """Report the consumer SDK prerequisite without installing or importing Wright."""
    if importlib.util.find_spec("mcp") is not None:
        return ""
    note = (
        "HOST READINESS [missing_mcp_client]: This Hermes environment has no MCP "
        "client SDK, so a configured wrightgateway cannot expose tools to Hermes. "
        "Wright's separate runtime does not supply Hermes dependencies. "
    )
    try:
        version = importlib.metadata.version("hermes-agent")
    except importlib.metadata.PackageNotFoundError:
        return (
            note
            + "Enable the MCP extra using your Hermes installation's supported setup, then restart Hermes."
        )
    if not re.fullmatch(r"[A-Za-z0-9.!+_-]+", version):
        return (
            note
            + "Use your Hermes installation's supported MCP setup, then restart Hermes."
        )
    command = [sys.executable, "-m", "pip", "install", f"hermes-agent[mcp]=={version}"]
    display = (
        subprocess.list2cmdline(command) if os.name == "nt" else shlex.join(command)
    )
    return (
        note
        + "For this pip-managed Hermes environment, review and run: "
        + display
        + ". This installs Hermes's MCP extra while retaining its version; restart Hermes afterward. "
        "For a checkout/uv-managed installation, use its supported MCP-extra setup instead. "
        "No dependency was installed by /wright. Browser chat also requires a separately running Hermes gateway."
    )


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
    progress=None,
) -> str:
    arguments = raw_args.strip().split()
    if not arguments:
        return WRIGHT_HELP_TEXT
    command = arguments[0].lower()
    argument = arguments[1] if len(arguments) > 1 else None
    if command == "setup-browser":
        return setup_browser()
    if command == "open":
        port = int(os.environ.get("WRIGHT_NATIVE_PORT", "8000"))
        return f"Wright UI: http://wright.localhost:{port}/"
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
        operation = asyncio.create_task(asyncio.to_thread(invoker, command, argument))
        if command == "start" and progress is not None:
            progress(
                "Preparing Wright. First startup installs its private runtime; "
                "keep this terminal open. The workspace URL will appear when ready."
            )
            started = time.monotonic()
            while not operation.done():
                done, _ = await asyncio.wait({operation}, timeout=15)
                if not done:
                    elapsed = round(time.monotonic() - started)
                    progress(f"Wright is still preparing ({elapsed}s elapsed).")
        result = await operation
    except BootstrapError as exc:
        return f"ERROR [bootstrap_failed] Wright could not run: {exc}"
    projected = project_result(result)
    if command in {"start", "doctor"}:
        readiness = host_mcp_readiness()
        if readiness:
            projected += "\n" + readiness
        projected += (
            "\nBROWSER CHAT: Wright's runtime and Hermes tool access are separate from "
            "the browser agent connection. If the browser says Hermes is unavailable, "
            "run `/wright setup-browser` to prepare this profile's local connection, "
            "then follow its gateway and restart steps."
        )
    return projected


def register_commands(ctx: Any) -> None:
    async def handler(raw_args: str, **_: object) -> str:
        progress = (
            (lambda text: print(text, flush=True))
            if sys.stdout.isatty()
            else None
        )
        return await handle_wright(raw_args, progress=progress)

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
