"""Reconcile the retained MCP gateway run after its controller disconnected.

Never starts a run, enrolls authority or resubmits the inspection proposal.
"""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

from data_vault import GatewayRepository, WorkspaceRepository
from data_vault.secret_provider import FileSecretProvider
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main(state):
    original = json.loads((state / "mcp-gateway-probe.json").read_text())
    if not original.get("answer_1", {}).get("accepted") or original.get("answer_2"):
        raise ValueError(
            "Only the observed accepted first-decision disconnect is qualified here"
        )
    output = state / "mcp-gateway-reconciliation.json"
    if output.exists():
        raise ValueError("Inspect existing reconciliation evidence; do not replay it")
    workspace = original["workspace"]
    scope = {
        "workspace_id": workspace["workspace_id"],
        "session_id": workspace["session_id"],
    }
    run_id = original["start_receipt"]["run_id"]
    read_args = dict(
        scope,
        path=original["source"]["path"],
        source_digest=original["source"]["storage_digest"],
        run_id=run_id,
    )
    evidence = {"run_id": run_id, "replayed_first_decision": False, "calls": []}
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[
            str(Path(__file__).with_name("mcp_bridge.py")),
            "--state-dir",
            str(state),
        ],
    )
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            async def call(tool_name, **arguments):
                result = await session.call_tool(tool_name, arguments)
                evidence["calls"].append(
                    {"tool": tool_name, "is_error": result.isError}
                )
                output.write_text(json.dumps(evidence, indent=2))
                if result.isError:
                    raise ValueError(str(result.content))
                return result.structuredContent or json.loads(result.content[0].text)

            before = await call("wright_process_read", **read_args)
            evidence["before"] = before
            if before["state"] != "running":
                raise ValueError("The retained run is no longer awaiting this decision")
            tasks = (await call("wright_reasoning_pending", **scope))["tasks"]
            task = next(
                t
                for t in tasks
                if t["request"]["run_id"] == run_id and t["request"]["ordinal"] == 2
            )
            if task["request"]["kind"] != "action":
                raise ValueError("The retained task is not an action decision")
            observed = [
                json.loads(message["content"])
                for message in task["request"]["payload"]["messages"]
                if message["role"] == "tool"
            ]
            if len(observed) != 1 or observed[0]["status"] != "succeeded":
                raise ValueError(
                    "The first inspection did not produce exactly one observed successful result"
                )
            evidence["pending"] = task
            answer = json.loads((state / "desktop-gateway-action-2.json").read_text())
            if (
                answer["request_id"],
                answer["request_digest"],
                answer["binding_digest"],
            ) != (
                task["request"]["request_id"],
                task["request_digest"],
                task["binding_digest"],
            ):
                raise ValueError("The answer belongs to another retained task")
            evidence["answer_receipt"] = await call(
                "wright_reasoning_action", **scope, **answer
            )
            async with asyncio.timeout(30):
                while True:
                    after = await call("wright_process_read", **read_args)
                    if after["state"] != "running":
                        break
                    await asyncio.sleep(0.1)
            evidence["after"] = after
            repository = WorkspaceRepository(
                str(state / "wright.sqlite"),
                secrets=FileSecretProvider(state / "credentials.json"),
            )
            root = Path(repository.get_by_session(scope["session_id"])["local_path"])
            evidence["input_unchanged"] = (
                hashlib.sha256(
                    (root / "inputs/requirements.md").read_bytes()
                ).hexdigest()
                == original["private_setup"]["input_sha256"]
            )
            with sqlite3.connect(
                f"file:{state / 'wright.sqlite'}?mode=ro", uri=True
            ) as database:
                sessions = database.execute(
                    "SELECT DISTINCT session_id FROM gateway_audit_events WHERE workspace_id = ?",
                    (scope["workspace_id"],),
                ).fetchall()
            audit = GatewayRepository(str(state / "wright.sqlite"))
            events = [e for (sid,) in sessions for e in audit.list_audit(sid)]
            (state / "mcp-gateway-audit.json").write_text(json.dumps(events, indent=2))
            evidence["successful_dispatches"] = sum(
                e["operation"] == "tool.call" and e["outcome"] == "succeeded"
                for e in events
            )
            output.write_text(json.dumps(evidence, indent=2))
            print(
                json.dumps(
                    {
                        "state": after["state"],
                        "run_id": run_id,
                        "successful_dispatches": evidence["successful_dispatches"],
                        "input_unchanged": evidence["input_unchanged"],
                    }
                ),
                flush=True,
            )
            if (
                after["state"] != "completed"
                or evidence["successful_dispatches"] != 1
                or not evidence["input_unchanged"]
            ):
                raise ValueError("Same-run reconciliation did not qualify")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", required=True, type=Path)
    args = parser.parse_args()
    asyncio.run(main(args.state_dir.resolve(strict=True)))
