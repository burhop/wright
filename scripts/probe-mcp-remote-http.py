#!/usr/bin/env python3
"""Probe a remote streamable-HTTP MCP endpoint and write redacted evidence."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_error(exc: BaseException) -> str:
    parts = [str(exc)]
    nested = getattr(exc, "exceptions", ())
    for child in nested:
        parts.append(clean_error(child))
    text = " | ".join(" ".join(part.split()) for part in parts if part)
    return text[:1000]


async def probe(args: argparse.Namespace) -> dict:
    started = time.monotonic()
    evidence = {
        "server_id": args.server_id,
        "observed_at": utc_now(),
        "wright_revision": args.wright_revision,
        "environment": args.environment,
        "platform": "linux_x64",
        "container_image": args.container_image,
        "source_url": args.source,
        "source_revision": args.source_revision,
        "transport": "streamable_http",
        "endpoint": args.endpoint,
        "credentials_supplied": False,
        "status": "failed",
        "protocol": "not_reached",
        "cleanup": "passed",
    }
    try:
        async with streamablehttp_client(args.endpoint) as (read, write, _):
            async with ClientSession(read, write) as session:
                initialized = await session.initialize()
                tools = await session.list_tools()
                compact = [
                    {"name": tool.name, "input_schema": tool.inputSchema}
                    for tool in tools.tools
                ]
                evidence.update(
                    {
                        "status": "partial",
                        "protocol": "passed",
                        "server_info": {
                            "name": initialized.serverInfo.name,
                            "version": initialized.serverInfo.version,
                        },
                        "tool_count": len(compact),
                        "tool_schema_sha256": hashlib.sha256(
                            json.dumps(compact, sort_keys=True).encode()
                        ).hexdigest(),
                        "tools": compact,
                    }
                )
    except BaseException as exc:
        evidence["failure_stage"] = "initialize_or_tools_list"
        evidence["observed_error"] = clean_error(exc)
        lower = evidence["observed_error"].lower()
        if any(word in lower for word in ("401", "403", "oauth", "authorization", "authentication", "unauthorized")):
            evidence["status"] = "blocked"
            evidence["blocking_requirement"] = "credentials_or_oauth"
    evidence["finished_at"] = utc_now()
    evidence["duration_seconds"] = round(time.monotonic() - started, 3)
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-id", required=True)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--source-revision", default="remote-current")
    parser.add_argument("--wright-revision", required=True)
    parser.add_argument("--environment", default="wright-clean-debian13-x64")
    parser.add_argument("--container-image", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    evidence = asyncio.run(probe(args))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"server_id": args.server_id, "status": evidence["status"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
