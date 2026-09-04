"""Headless native HTTP client; all authority and execution stay in the service."""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from urllib.parse import quote, urlsplit

import httpx
from core.canonical_json import strict_json_loads


def _file(path: str, maximum: int = 1100 * 1024):
    with Path(path).open("rb") as stream:
        return strict_json_loads(stream.read(maximum + 1), max_bytes=maximum)


def main(argv: list[str] | None = None, *, client=None) -> int:
    parser = argparse.ArgumentParser(
        description="Use Wright's native process runtime over HTTP."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--session-id", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser(
        "check", help="Validate a native definition and exact tool bindings."
    )
    check.add_argument("definition")
    check.add_argument("--bindings")
    run = commands.add_parser(
        "run", help="Submit the saved process using its current token."
    )
    run.add_argument("process_id")
    run.add_argument("--expected-token", required=True)
    run.add_argument(
        "--request-id",
        required=True,
        help="Reuse only when retrying identical content.",
    )
    run.add_argument("--bindings")
    run.add_argument("--timeout-seconds", type=int, default=60)
    run.add_argument("--derived-from-run-id")
    for name in ("inspect", "cancel"):
        command = commands.add_parser(name)
        command.add_argument("run_id")
    args = parser.parse_args(argv)
    connection = None
    try:
        address = urlsplit(args.base_url)
        if (
            address.scheme not in {"http", "https"}
            or not address.hostname
            or address.username
            or address.password
            or address.query
            or address.fragment
        ):
            raise ValueError(
                "Base URL must be an HTTP endpoint without credentials, query or fragment."
            )
        prefix = args.base_url.rstrip("/") + "/api/native-processes"
        headers = {"X-Trace-Id": f"native-cli-{uuid.uuid4().hex}"}
        token = os.getenv("WRIGHT_API_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        payload = None
        if args.command == "check":
            route, method = "/check", "POST"
            payload = {
                "definition": _file(args.definition),
                "bindings": _file(args.bindings) if args.bindings else {},
            }
        elif args.command == "run":
            route, method = (
                "/documents/" + quote(args.process_id, safe="") + "/runs",
                "POST",
            )
            payload = {
                "expected_token": args.expected_token,
                "request_id": args.request_id,
                "bindings": _file(args.bindings) if args.bindings else {},
                "timeout_seconds": args.timeout_seconds,
                "derived_from_run_id": args.derived_from_run_id,
            }
        else:
            route = "/runs/" + quote(args.run_id, safe="")
            method = "GET"
            if args.command == "cancel":
                route, method = route + "/cancel", "POST"
        connection = client or httpx.Client(
            timeout=15, follow_redirects=False, trust_env=False
        )
        response = connection.request(
            method,
            prefix + route,
            params={"session_id": args.session_id},
            json=payload,
            headers=headers,
        )
        if len(response.content) > 4 * 1024 * 1024:
            raise ValueError("Native response exceeds the CLI output limit.")
        result = response.json()
        success = 200 <= response.status_code < 300
        print(
            json.dumps(result, ensure_ascii=False, allow_nan=False),
            file=sys.stdout if success else sys.stderr,
        )
        if not success:
            return 1
        return 2 if args.command == "check" and not result.get("ready") else 0
    except (OSError, ValueError, httpx.HTTPError):
        print(
            json.dumps(
                {
                    "code": "NATIVE_CLI_ERROR",
                    "message": "Unable to read the request or reach the native runtime.",
                    "recovery": "Check the input file, base URL and WRIGHT_API_TOKEN configuration.",
                }
            ),
            file=sys.stderr,
        )
        return 1
    finally:
        if connection is not None and client is None:
            connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
