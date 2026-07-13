from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import __version__
from .appliance import ApplianceError, appliance_status, config_diagnostic
from .diagnostics import run_diagnostics
from .mcp_bridge import serve_stdio


DOCKER_IMAGE = "burhop/wright"
GHCR_IMAGE = "ghcr.io/burhop/wright"
DOCS_URL = "https://burhop.github.io/wright/"
SUPPORT_EMAIL = "wright@makerengineer.com"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="wright",
        description="Public-alpha helper for the Wright local-first engineering appliance.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"wright-engineering {__version__}",
    )
    subcommands = parser.add_subparsers(dest="command")
    doctor = subcommands.add_parser(
        "doctor", help="Run dependency-safe local diagnostics."
    )
    doctor.add_argument(
        "--strict",
        action="store_true",
        help="Fail when an optional appliance prerequisite is missing.",
    )
    appliance = subcommands.add_parser(
        "appliance", help="Inspect a running Wright appliance."
    )
    appliance_subcommands = appliance.add_subparsers(
        dest="appliance_command", required=True
    )
    appliance_status_parser = appliance_subcommands.add_parser("status")
    appliance_status_parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    config = subcommands.add_parser(
        "config", help="Inspect configuration without secrets."
    )
    config.add_argument("--api-url", default="http://127.0.0.1:8000")
    config.add_argument("--token-env", default="WRIGHT_API_TOKEN")
    config.add_argument("--dry-run", action="store_true", required=True)
    mcp = subcommands.add_parser(
        "mcp", help="Run the direct provider-neutral MCP bridge."
    )
    mcp_subcommands = mcp.add_subparsers(dest="mcp_command", required=True)
    serve = mcp_subcommands.add_parser("serve")
    serve.add_argument("--stdio", action="store_true", required=True)
    serve.add_argument("--workspace", type=Path, required=True)
    serve.add_argument("--api-url", default="http://127.0.0.1:8000")
    serve.add_argument("--session-id", default="wright-engineering")
    serve.add_argument("--token-env", default="WRIGHT_API_TOKEN")

    args = parser.parse_args(argv)
    if args.command is None:
        print("Wright public alpha")
        print(f"Docker Hub image: {DOCKER_IMAGE}:<tag>")
        print(f"GHCR image: {GHCR_IMAGE}:<tag>")
        print(f"Docs: {DOCS_URL}")
        print(f"Support: {SUPPORT_EMAIL}")
        print("Docker remains the primary end-user install path for alpha.")
        return 0
    if args.command == "doctor":
        diagnostics = run_diagnostics()
        for item in diagnostics:
            print(f"{'PASS' if item.ok else 'WARN'} {item.name}: {item.detail}")
        if args.strict and not all(
            item.ok for item in diagnostics if item.name != "api-token"
        ):
            return 1
        return 0
    if args.command == "appliance" and args.appliance_command == "status":
        try:
            print(json.dumps(appliance_status(args.api_url), sort_keys=True))
        except ApplianceError as exc:
            print(str(exc))
            return 1
        return 0
    if args.command == "config":
        print(
            json.dumps(config_diagnostic(args.api_url, args.token_env), sort_keys=True)
        )
        return 0
    if args.command == "mcp" and args.mcp_command == "serve":
        return serve_stdio(
            workspace=args.workspace,
            api_url=args.api_url,
            session_id=args.session_id,
            token_env=args.token_env,
        )
    parser.error(f"unknown command: {args.command}")
    return 2
