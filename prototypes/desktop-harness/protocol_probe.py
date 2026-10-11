"""Exercise actual MCP lifecycle and Wright owners, awaiting this desktop's reply.

This is an isolated protocol client, not a connected desktop-plugin claim.
"""

import argparse
import asyncio
import json
from pathlib import Path
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from reasoning_probe import SOURCE


async def main(state):
    probe_file = state / "protocol-probe.json"
    if probe_file.exists():
        raise ValueError("Use fresh protocol evidence; do not replay an existing probe")
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[
            str(Path(__file__).with_name("mcp_bridge.py")),
            "--state-dir",
            str(state),
        ],
    )
    evidence = {
        "transport": "MCP stdio protocol client; desktop plugin not installed",
        "calls": [],
    }

    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            initialized = await session.initialize()
            evidence["protocol_version"] = initialized.protocolVersion
            listed = await session.list_tools()
            evidence["tools"] = [item.name for item in listed.tools]

            async def call(tool_name, **arguments):
                result = await session.call_tool(tool_name, arguments)
                evidence["calls"].append({"tool": tool_name, "is_error": result.isError})
                probe_file.write_text(json.dumps(evidence, indent=2))
                if result.isError:
                    raise RuntimeError(str(result.content))
                return result.structuredContent or json.loads(result.content[0].text)

            workspace = await call(
                "wright_workspace_create", name="Desktop MCP Inspection Proof"
            )
            evidence["workspace"] = workspace
            scope = {
                "workspace_id": workspace["workspace_id"],
                "session_id": workspace["session_id"],
            }
            source_path = "workflows/desktop-inspection.workflow.wflow"
            source = SOURCE.replace(
                '"output_format":"markdown"',
                '"authoring_template":"ai-prompt","output_format":"markdown"',
            )
            document = await call(
                "wright_workflow_create", **scope, path=source_path, source=source
            )
            evidence["source"] = document
            prepared = await call(
                "wright_process_prepare",
                **scope,
                path=source_path,
                source_digest=document["storage_digest"],
                bindings=[],
            )
            evidence["input_snapshot"] = prepared
            receipt = await call(
                "wright_process_start",
                **scope,
                path=source_path,
                source_digest=document["storage_digest"],
                input_snapshot_id=prepared["snapshot_id"],
                input_digest=prepared["digest"],
                request_id="desktop-mcp-inspection-start-01",
            )
            evidence["start_receipt"] = receipt
            while True:
                pending = await call("wright_reasoning_pending", **scope)
                if pending["tasks"]:
                    break
                await asyncio.sleep(0.1)
            evidence["pending"] = pending
            probe_file.write_text(json.dumps(evidence, indent=2))
            print(
                json.dumps(
                    {
                        "stage": "awaiting_desktop",
                        "workspace": workspace,
                        "pending": pending,
                    },
                    indent=2,
                ),
                flush=True,
            )
            answer_file = state / "desktop-protocol-answer.json"
            while not answer_file.exists():
                await asyncio.sleep(0.25)
            answer = json.loads(answer_file.read_text())
            evidence["answer_receipt"] = await call(
                "wright_reasoning_answer", **scope, **answer
            )
            async with asyncio.timeout(30):
                while True:
                    snapshot = await call(
                        "wright_process_read",
                        **scope,
                        path=source_path,
                        source_digest=document["storage_digest"],
                        run_id=receipt["run_id"],
                    )
                    if snapshot["state"] in {
                        "completed",
                        "failed",
                        "cancelled",
                        "waiting_human",
                        "reconciliation_required",
                        "interrupted",
                    }:
                        break
                    await asyncio.sleep(0.1)
            evidence["final_snapshot"] = snapshot
            probe_file.write_text(json.dumps(evidence, indent=2))
            print(
                json.dumps(
                    {
                        "stage": snapshot["state"],
                        "run_id": receipt["run_id"],
                        "evidence": str(probe_file),
                    }
                ),
                flush=True,
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", required=True, type=Path)
    args = parser.parse_args()
    asyncio.run(main(args.state_dir.resolve()))
