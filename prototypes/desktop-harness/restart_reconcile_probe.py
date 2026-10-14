"""Observe an existing interrupted protocol run; never create a replacement run.

Run only after protocol_probe.py reached its pending request and the owned API
was killed and reopened with the same profile. A late-answer control deliberately
tests admission to a dead owner's request. Failure is retained, never relabelled
as a successful recovery or automatically replayed.
"""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from checkpoint_probe import panel_request


async def main(state, *, native_working_view=False):
    destination = state / "restart-reconciliation.json"
    if destination.exists():
        raise ValueError("Retain this observation; do not replay its late answer")
    original = json.loads((state / "protocol-probe.json").read_text())
    if original.get("native_working_view", False) != native_working_view:
        raise ValueError("Retain the original probe routing")
    fault = json.loads((state / "restart-fault.json").read_text())
    if fault["signal"] != "SIGKILL":
        raise ValueError("This probe requires the recorded abrupt API fault")
    versions = json.loads((state / "desktop-versions.json").read_text())
    if versions != fault["versions"]:
        raise ValueError("The reopened API profile differs; reconcile drift first")
    workspace = original["workspace"]
    scope = {key: workspace[key] for key in ("workspace_id", "session_id")}
    receipt = original["start_receipt"]
    reference = {
        **scope,
        "path": original["source"]["path"],
        "source_digest": original["source"]["storage_digest"],
        "run_id": receipt["run_id"],
    }
    evidence = {"calls": [], "transport": "SDK MCP protocol; not installed desktop"}

    async with stdio_client(
        StdioServerParameters(
            command=sys.executable,
            args=[
                str(Path(__file__).with_name("mcp_bridge.py")),
                "--state-dir",
                str(state),
                *(
                    ["--native-editor", "--native-working-view"]
                    if native_working_view
                    else []
                ),
            ],
        )
    ) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            async def call(name, **arguments):
                actual, payload = (
                    panel_request(name, arguments)
                    if native_working_view
                    else (name, arguments)
                )
                result = await session.call_tool(actual, payload)
                evidence["calls"].append(
                    {
                        "tool": actual,
                        "logical_operation": name,
                        "is_error": bool(result.isError),
                    }
                )
                destination.write_text(json.dumps(evidence, indent=2))
                if result.isError:
                    return {
                        "is_error": True,
                        "content": [
                            item.model_dump(mode="json") for item in result.content
                        ],
                    }
                document = result.structuredContent or json.loads(
                    result.content[0].text
                )
                if actual in ("wright_process_ui_read", "wright_process_ui_update"):
                    if document.get("ok") is not True:
                        return {"is_error": True, "content": document}
                    return document["document"]
                return document

            evidence["before_reply"] = await call("wright_process_read", **reference)
            assert evidence["before_reply"]["state"] == "reconciliation_required"
            pending = await call("wright_reasoning_pending", **scope)
            evidence["pending_before"] = pending
            task = next(
                item
                for item in pending["tasks"]
                if item["request"]["run_id"] == receipt["run_id"]
            )
            assert task["request_digest"] == fault["request_digest"]
            # Replay the exact stable start request solely to read its durable
            # receipt. Wright must attach, never allocate or execute another run.
            evidence["reattached_receipt"] = await call(
                "wright_process_start",
                **scope,
                path=reference["path"],
                source_digest=reference["source_digest"],
                input_snapshot_id=receipt["input_snapshot_id"],
                input_digest=receipt["input_digest"],
                request_id=receipt["request_id"],
            )
            assert evidence["reattached_receipt"] == receipt
            reply = json.loads((state / "desktop-late-answer.json").read_text())
            evidence["late_reply"] = await call(
                "wright_reasoning_answer",
                **scope,
                request_id=task["request"]["request_id"],
                request_digest=task["request_digest"],
                binding_digest=task["binding_digest"],
                response_id="desktop-abrupt-restart-late-answer-control-01",
                reply=json.dumps(reply),
            )
            evidence["after_reply"] = await call("wright_process_read", **reference)
            evidence["pending_after"] = await call("wright_reasoning_pending", **scope)

    with sqlite3.connect(
        f"file:{state / 'wright.sqlite'}?mode=ro", uri=True
    ) as database:
        evidence["handoff_counts"] = {
            table: database.execute(
                f"SELECT COUNT(*) FROM {table} WHERE workspace_id=? AND session_id=?",
                (scope["workspace_id"], scope["session_id"]),
            ).fetchone()[0]
            for table in (
                "desktop_reasoning_requests",
                "desktop_reasoning_responses",
                "desktop_reasoning_terminal_receipts",
            )
        }
    evidence["run_logs"] = [
        str(path.relative_to(state))
        for path in (state / "workspaces").glob("*/runs/**/*.json")
    ]
    evidence["outputs"] = [
        str(path.relative_to(state))
        for path in (state / "workspaces").glob("*/outputs/**/*")
        if path.is_file()
    ]
    evidence["run_artifacts_unchanged"] = all(
        hashlib.sha256((state / path).read_bytes()).hexdigest() == digest
        for path, digest in fault["run_artifacts_before"].items()
    )
    assert len(evidence["run_logs"]) == 1
    assert evidence["outputs"] == []
    assert evidence["run_artifacts_unchanged"]
    assert evidence["after_reply"]["state"] == "reconciliation_required"
    denied = bool(evidence["late_reply"].get("is_error"))
    evidence["qualification"] = {
        "same_run_no_replay": "passed",
        "retained_pending_request": "passed",
        "late_reply_to_dead_owner": "denied"
        if denied
        else "FAILED: accepted without a live consumer",
        "automatic_reasoning_restart": "unsupported; requires reconciliation",
        "installed_desktop_plugin": "unverified",
    }
    destination.write_text(json.dumps(evidence, indent=2))
    print(
        json.dumps(
            {"evidence": str(destination), **evidence["qualification"]}, indent=2
        )
    )
    return 0 if denied else 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument("--native-working-view", action="store_true")
    options = parser.parse_args()
    raise SystemExit(
        asyncio.run(
            main(
                options.state_dir.resolve(strict=True),
                native_working_view=options.native_working_view,
            )
        )
    )
