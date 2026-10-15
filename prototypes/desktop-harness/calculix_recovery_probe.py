"""Read-only recovery of existing qualification runs through native MCP stdio."""

import argparse
import asyncio
import base64
import hashlib
import json
import os
from datetime import timedelta
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import AnyUrl

IMAGE = "ghcr.io/casys-ai/mcp-calculix@sha256:82ce8628279e03c8f492f156bb928e5703ea1fcb2d7c465826faf38f7389a778"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def saved_files(root):
    return {
        str(p.relative_to(root)): digest(p.read_bytes())
        for p in sorted(root.rglob("*"))
        if p.is_file() and not p.name.endswith(".lock")
    }


async def run(state, attempt):
    output = state / attempt
    output.mkdir()
    before = saved_files(state / "runs")
    args = [
        "run",
        "--name",
        "wright-calculix-" + attempt,
        "-i",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--memory",
        "4g",
        "--cpus",
        "2",
        "--pids-limit",
        "256",
        "--tmpfs",
        "/tmp:rw,exec,nosuid,size=1g",
        "--env",
        "DENO_DIR=/tmp/deno",
        "--env",
        "CALCULIX_RUNS_DIRECTORY=/runs",
        "--mount",
        f"type=bind,source={state / 'runs'},target=/runs",
        IMAGE,
        "stdio",
    ]
    evidence = {
        "status": "started",
        "boundary": "official Python MCP SDK to native provider stdio; no solve calls",
        "calls": [],
    }
    try:
        with (output / "stderr.log").open("w") as log:
            async with stdio_client(
                StdioServerParameters(command="docker", args=args), errlog=log
            ) as (read, write):
                async with ClientSession(
                    read, write, read_timeout_seconds=timedelta(seconds=120)
                ) as client:
                    initialized = await client.initialize()
                    evidence["initialize"] = initialized.model_dump(mode="json")
                    listed = await client.list_tools()
                    (output / "tools.json").write_text(listed.model_dump_json(indent=2))
                    for route in ("direct", "gateway"):
                        original = json.loads(
                            (state / "arm64-001" / (route + "-result.json")).read_text()
                        )["run"]
                        for key, value in (
                            ("run_id", original["runId"]),
                            ("request_id", original["requestId"]),
                        ):
                            result = await client.call_tool(
                                "calculix_run_get", {key: value}
                            )
                            assert not result.isError
                            record = result.structuredContent
                            assert (
                                record["status"] == "completed"
                                and record["run"] == original
                            )
                            evidence["calls"].append(
                                {
                                    "tool": "calculix_run_get",
                                    "arguments": {key: value},
                                    "run_id": record["runId"],
                                    "ledger_matches": True,
                                }
                            )
                        for item in original["artifacts"]:
                            result = await client.read_resource(AnyUrl(item["uri"]))
                            assert len(result.contents) == 1
                            content = result.contents[0]
                            data = (
                                base64.b64decode(content.blob)
                                if hasattr(content, "blob")
                                else content.text.encode()
                            )
                            assert (
                                len(data) == item["bytes"]
                                and digest(data) == item["sha256"]
                            )
                    evidence["verified_resources"] = 18
        assert saved_files(state / "runs") == before
        evidence.update(status="passed", durable_files_unchanged=True, solve_calls=0)
    except BaseException as error:

        def leaves(exc):
            if isinstance(exc, BaseExceptionGroup):
                return [
                    message for child in exc.exceptions for message in leaves(child)
                ]
            return [str(exc)]

        evidence.update(
            status="failed",
            errors=leaves(error),
            durable_files_unchanged=saved_files(state / "runs") == before,
            solve_calls=0,
        )
        raise
    finally:
        (output / "receipt.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({"status": evidence["status"], "output": str(output)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--attempt", required=True)
    options = parser.parse_args()
    if not options.attempt.replace("-", "").isalnum():
        parser.error("Use a simple fresh attempt identifier")
    asyncio.run(run(options.state.resolve(), options.attempt))
