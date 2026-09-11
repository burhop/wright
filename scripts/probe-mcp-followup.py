#!/usr/bin/env python3
"""Record a bounded direct-protocol probe for one reviewed follow-up MCP."""

from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import traceback

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def _text(result) -> str:
    values = []
    for item in result.content:
        value = (
            item.get("text") if isinstance(item, dict) else getattr(item, "text", None)
        )
        if value is not None:
            values.append(value)
    return "\n".join(values)


def _digest(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


async def _probe(args, workspace: Path, report: dict, errlog) -> None:
    environment = dict(os.environ)
    environment.update(item.split("=", 1) for item in args.env)
    parameters = StdioServerParameters(
        command=args.command[0],
        args=args.command[1:],
        env=environment,
        cwd=str(workspace),
    )
    async with stdio_client(parameters, errlog=errlog) as (read, write):
        async with ClientSession(read, write) as client:
            initialized = await client.initialize()
            listed = await client.list_tools()
            tools = sorted(listed.tools, key=lambda item: item.name)
            report.update(
                protocol="passed",
                startup="passed",
                server_info=initialized.serverInfo.model_dump(mode="json"),
                tool_count=len(tools),
                tool_schema_sha256=_digest(
                    [item.model_dump(mode="json") for item in tools]
                ),
                tools=[
                    {
                        "name": item.name,
                        "description": item.description,
                        "input_schema": item.inputSchema,
                    }
                    for item in tools
                ],
            )
            if not args.safe_tool:
                report.update(status="partial", task="not_run")
                return
            selected = next(
                (item for item in tools if item.name == args.safe_tool), None
            )
            if selected is None:
                raise ValueError(f"Reviewed safe tool is unavailable: {args.safe_tool}")
            result = await client.call_tool(
                args.safe_tool, json.loads(args.safe_arguments)
            )
            text = _text(result)
            report["task"] = {
                "tool": args.safe_tool,
                "arguments_sha256": _digest(json.loads(args.safe_arguments)),
                "is_error": bool(result.isError),
                "content": text[:4000],
            }
            if args.expected_blocker:
                if args.expected_blocker.casefold() not in text.casefold():
                    raise AssertionError("Expected blocker was not reported by the MCP")
                report.update(
                    status="blocked",
                    failure_stage="domain_task",
                    blocker=args.expected_blocker,
                )
            elif result.isError:
                report.update(status="failed", failure_stage="domain_task")
            else:
                report.update(status="partial", failure_stage=None)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", required=True)
    parser.add_argument("--server-id", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--wright-revision", required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--container-image")
    parser.add_argument("--installed-item", action="append", default=[])
    parser.add_argument("--prerequisite", action="append", default=[])
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("--safe-tool")
    parser.add_argument("--safe-arguments", default="{}")
    parser.add_argument("--expected-blocker")
    parser.add_argument("--recovery-step", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("a reviewed server command is required after --")
    for value in args.env:
        if "=" not in value:
            parser.error("--env must use NAME=VALUE")

    started = time.monotonic()
    report = {
        "server_id": args.server_id,
        "observed_at": datetime.now(UTC).isoformat(),
        "wright_revision": args.wright_revision,
        "environment": args.environment,
        "platform": args.platform,
        "container_image": args.container_image,
        "source_url": args.source,
        "source_revision": args.source_revision,
        "source_sha256": args.source_sha256,
        "installed_items": args.installed_item,
        "prerequisites": args.prerequisite,
        "recovery_steps": args.recovery_step,
        "implementation_mode": "native_vendor_binary",
        "status": "running",
    }
    try:
        with tempfile.TemporaryDirectory(prefix="wright-followup-mcp-") as temporary:
            stderr_path = Path(temporary) / "server-stderr.txt"
            try:
                with stderr_path.open("w", encoding="utf-8") as errlog:
                    asyncio.run(
                        asyncio.wait_for(
                            _probe(args, Path(temporary), report, errlog), timeout=120
                        )
                    )
            finally:
                if stderr_path.exists():
                    stderr = stderr_path.read_text(encoding="utf-8", errors="replace")
                    for item in args.env:
                        stderr = stderr.replace(item.split("=", 1)[1], "[REDACTED]")
                    report["server_stderr"] = stderr[-4000:]
        report["cleanup"] = "passed"
    except Exception as error:
        report.update(
            status="failed",
            failure_stage=report.get("failure_stage", "startup_or_protocol"),
            error=type(error).__name__,
            diagnostic=str(error)[:1000],
            traceback="".join(traceback.format_exception(error))[-4000:],
            cleanup="passed",
        )
    report["finished_at"] = datetime.now(UTC).isoformat()
    report["duration_seconds"] = round(time.monotonic() - started, 3)
    report["duration_source"] = "monotonic_clock"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"server_id": args.server_id, "status": report["status"]}))
    return 0 if report["status"] in {"partial", "blocked"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
