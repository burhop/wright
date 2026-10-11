"""Observe leased MCP loss and reconcile an existing live run, without replay.

The observation phase never registers a replacement connection. Completion
initializes MCP, reads the exact retained task, and submits an actual desktop
answer once. No start, provider fallback, model worker or executor is included.
"""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from mcp_bridge import WrightDesktopClient


def counts(state):
    with sqlite3.connect(
        f"file:{state / 'wright.sqlite'}?mode=ro", uri=True
    ) as database:
        return {
            table: database.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "engineering_workspaces",
                "desktop_reasoning_requests",
                "desktop_reasoning_responses",
                "desktop_reasoning_terminal_receipts",
            )
        }


async def main(state, phase):
    probe = json.loads((state / "protocol-probe.json").read_text())
    fault = json.loads((state / "lease-fault.json").read_text())
    scope = {key: probe["workspace"][key] for key in ("workspace_id", "session_id")}
    reference = {
        **scope,
        "path": probe["source"]["path"],
        "source_digest": probe["source"]["storage_digest"],
        "run_id": fault["run_id"],
    }
    destination = state / f"lease-{phase}.json"
    if destination.exists():
        raise ValueError(
            "Retain existing evidence; never replay this observation or answer"
        )
    if phase == "observe":
        try:
            terminal = (
                Path(f"/proc/{fault['bridge_pid']}/stat")
                .read_text()
                .split(") ", 1)[1]
                .split()[0]
            )
            if terminal != "Z":
                raise ValueError("The owned MCP child is not confirmed terminal")
        except FileNotFoundError:
            terminal = "missing"
        client = WrightDesktopClient(state)
        try:
            async with asyncio.timeout(35):
                while True:
                    connection = await client.call("GET", "/api/desktop/connection")
                    if not connection["connected"]:
                        break
                    await asyncio.sleep(0.2)
            pending = await client.call("GET", "/api/desktop/reasoning", params=scope)
            assert (
                len(pending) == 1
                and pending[0]["request_digest"] == fault["request_digest"]
            )
            snapshot = await client.call(
                "GET",
                "/api/workspace/process-interfaces/runs/" + fault["run_id"],
                params={
                    "session_id": scope["session_id"],
                    "path": reference["path"],
                    "expected_storage_digest": reference["source_digest"],
                },
            )
            assert snapshot["state"] == "running"
            before = counts(state)
            try:
                await client.call(
                    "POST",
                    "/api/desktop/workspaces",
                    json={"name": "Lease-expired denial control"},
                )
            except ValueError as error:
                assert "(503)" in str(error)
                denial = str(error)
            else:
                raise AssertionError("An expired connection created a workspace")
            assert counts(state) == before
            assert before == {
                "engineering_workspaces": 1,
                "desktop_reasoning_requests": 1,
                "desktop_reasoning_responses": 0,
                "desktop_reasoning_terminal_receipts": 0,
            }
            unchanged = all(
                hashlib.sha256((state / path).read_bytes()).hexdigest() == digest
                for path, digest in fault["run_artifacts_before"].items()
            )
            assert unchanged
            evidence = {
                "mcp_terminal_observation": terminal,
                "connection_after": connection,
                "run_id": fault["run_id"],
                "run_state": snapshot["state"],
                "request_digest": fault["request_digest"],
                "mutation_denial": denial,
                "counts": before,
                "run_artifacts_unchanged": unchanged,
                "elapsed_since_signal_at_read": time.monotonic()
                - fault["monotonic_at_signal"],
                "timing_limit": "first observer may start after preparation delay; this is not a measured expiry latency",
                "installed_desktop_chat_closure": "unverified; MCP child loss only",
            }
        finally:
            await client.http.aclose()
    else:
        observed = json.loads((state / "lease-observe.json").read_text())
        assert observed["run_id"] == fault["run_id"]
        evidence = {
            "calls": [],
            "run_id": fault["run_id"],
            "transport": "actual MCP protocol; installed desktop unverified",
        }
        async with stdio_client(
            StdioServerParameters(
                command=sys.executable,
                args=[
                    str(Path(__file__).with_name("mcp_bridge.py")),
                    "--state-dir",
                    str(state),
                ],
            )
        ) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                async def call(name, **arguments):
                    result = await session.call_tool(name, arguments)
                    evidence["calls"].append(
                        {"tool": name, "is_error": bool(result.isError)}
                    )
                    destination.write_text(json.dumps(evidence, indent=2))
                    if result.isError:
                        raise ValueError(str(result.content))
                    return result.structuredContent or json.loads(
                        result.content[0].text
                    )

                before = await call("wright_process_read", **reference)
                assert before["state"] == "running"
                pending = await call("wright_reasoning_pending", **scope)
                assert len(pending["tasks"]) == 1
                task = pending["tasks"][0]
                assert task["request_digest"] == fault["request_digest"]
                evidence["retained_task"] = task
                evidence["answer_receipt"] = await call(
                    "wright_reasoning_answer",
                    **scope,
                    **json.loads((state / "lease-desktop-answer.json").read_text()),
                )
                async with asyncio.timeout(30):
                    while True:
                        final = await call("wright_process_read", **reference)
                        if final["state"] != "running":
                            break
                        await asyncio.sleep(0.1)
                assert final["state"] == "completed"
                evidence["final_snapshot"] = final
        evidence["counts"] = counts(state)
        assert evidence["counts"] == {
            "engineering_workspaces": 1,
            "desktop_reasoning_requests": 1,
            "desktop_reasoning_responses": 1,
            "desktop_reasoning_terminal_receipts": 1,
        }
        evidence["qualification"] = (
            "same live run completed after lease loss/reconnect; response submitted and consumed once"
        )
    destination.write_text(json.dumps(evidence, indent=2))
    print(
        json.dumps({"phase": phase, "evidence": str(destination), "status": "passed"})
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument("--phase", required=True, choices=("observe", "complete"))
    options = parser.parse_args()
    asyncio.run(main(options.state_dir.resolve(strict=True), options.phase))
