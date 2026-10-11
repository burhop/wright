"""Real MCP checkpoint/reconnect probe; replies come from this desktop chat.

Uses the existing declared-human-input fixture unchanged. The comparison and
selection are synthetic digital test data, not engineering approval. This script
transports requests; it does not generate model replies or execute workflows.
"""

import argparse
import asyncio
from contextlib import asynccontextmanager
import json
from pathlib import Path
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@asynccontextmanager
async def connection(state, evidence, evidence_file):
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
            initialized = await session.initialize()
            evidence.setdefault("connections", []).append(initialized.protocolVersion)

            async def call(tool_name, *, expect_error=False, **arguments):
                result = await session.call_tool(tool_name, arguments)
                evidence["calls"].append(
                    {"tool": tool_name, "is_error": bool(result.isError)}
                )
                evidence_file.write_text(json.dumps(evidence, indent=2))
                if bool(result.isError) != expect_error:
                    raise RuntimeError(str(result.content))
                if result.isError:
                    return {"error": result.content[0].text}
                return result.structuredContent or json.loads(result.content[0].text)

            yield call


async def await_reply(state, evidence, evidence_file, call, scope, stage):
    async with asyncio.timeout(1800):
        while True:
            pending = await call("wright_reasoning_pending", **scope)
            if pending["tasks"]:
                break
            await asyncio.sleep(1)
        evidence[stage + "_pending"] = pending
        evidence_file.write_text(json.dumps(evidence, indent=2))
        print(json.dumps({"stage": stage, "pending": pending}, indent=2), flush=True)
        reply_file = state / ("checkpoint-" + stage + "-answer.json")
        while not reply_file.exists():
            await asyncio.sleep(0.25)
        reply = json.loads(reply_file.read_text())
        evidence[stage + "_answer_receipt"] = await call(
            "wright_reasoning_answer", **scope, **reply
        )


async def read_until(call, arguments, states):
    async with asyncio.timeout(30):
        while True:
            snapshot = await call("wright_process_read", **arguments)
            if snapshot["state"] in states:
                return snapshot
            await asyncio.sleep(0.25)


async def main(state, phase):
    evidence_file = state / "checkpoint-probe.json"
    if phase == "start":
        if evidence_file.exists():
            raise ValueError(
                "Do not replay a checkpoint probe; inspect its retained state"
            )
        evidence = {
            "transport": "MCP stdio protocol client; installed desktop plugin unverified",
            "test_data": "Existing synthetic comparison fixture; no engineering approval",
            "calls": [],
        }
        evidence_file.write_text(json.dumps(evidence, indent=2))
        async with connection(state, evidence, evidence_file) as call:
            workspace = await call(
                "wright_workspace_create", name="Desktop Checkpoint Proof"
            )
            evidence["workspace"] = workspace
            scope = {k: workspace[k] for k in ("workspace_id", "session_id")}
            fixture = (
                Path(__file__).parents[2]
                / "specs/083-process-working-interfaces/fixtures/declared-human-input.workflow.wflow"
            )
            source = await call(
                "wright_workflow_create",
                **scope,
                path="workflows/desktop-checkpoint.workflow.wflow",
                source=fixture.read_text(),
            )
            evidence["fixture_path"] = str(fixture)
            evidence["source"] = source
            prepared = await call(
                "wright_process_prepare",
                **scope,
                path=source["path"],
                source_digest=source["storage_digest"],
                bindings=[],
            )
            evidence["input_snapshot"] = prepared
            receipt = await call(
                "wright_process_start",
                **scope,
                path=source["path"],
                source_digest=source["storage_digest"],
                input_snapshot_id=prepared["snapshot_id"],
                input_digest=prepared["digest"],
                request_id="desktop-checkpoint-start-01",
            )
            evidence["start_receipt"] = receipt
            await await_reply(state, evidence, evidence_file, call, scope, "first")
            read_args = {
                **scope,
                "path": source["path"],
                "source_digest": source["storage_digest"],
                "run_id": receipt["run_id"],
            }
            checkpoint = await read_until(
                call, read_args, {"waiting_human", "failed", "completed"}
            )
            evidence["checkpoint_snapshot"] = checkpoint
            if checkpoint["state"] != "waiting_human":
                raise ValueError("The existing declared checkpoint was not reached")
        evidence["stage"] = "disconnected_at_checkpoint"
    else:
        evidence = json.loads(evidence_file.read_text())
        if evidence.get("stage") != "disconnected_at_checkpoint":
            raise ValueError("Reconcile the retained probe before any continuation")
        workspace, source, receipt = (
            evidence[k] for k in ("workspace", "source", "start_receipt")
        )
        scope = {k: workspace[k] for k in ("workspace_id", "session_id")}
        read_args = {
            **scope,
            "path": source["path"],
            "source_digest": source["storage_digest"],
            "run_id": receipt["run_id"],
        }
        async with connection(state, evidence, evidence_file) as call:
            snapshot = await call("wright_process_read", **read_args)
            evidence["reconnected_snapshot"] = snapshot
            if (
                snapshot["state"] != "waiting_human"
                or snapshot["context"]["run_id"] != receipt["run_id"]
            ):
                raise ValueError("The same waiting run was not reconciled")
            if snapshot["outputs"] != evidence["checkpoint_snapshot"]["outputs"]:
                raise ValueError("Prior outputs changed during the pause")
            interaction = next(
                i
                for i in snapshot["interactions"]
                if i["kind"] == "input" and i["state"] == "waiting"
            )
            respond_args = {
                **scope,
                "path": source["path"],
                "source_digest": source["storage_digest"],
                "checkpoint_id": interaction["checkpoint_id"],
                "subject_digest": interaction["subject_digest"],
            }
            evidence["invalid_selection_denial"] = await call(
                "wright_process_respond",
                **respond_args,
                value={"selection": "c"},
                request_id="desktop-checkpoint-invalid-01",
                expect_error=True,
            )
            after_denial = await call("wright_process_read", **read_args)
            if after_denial["state"] != "waiting_human":
                raise ValueError("Invalid selection changed the run state")
            if phase == "ui-continue":
                evidence["stage"] = "connected_waiting_for_ui"
                evidence_file.write_text(json.dumps(evidence, indent=2))
                print(
                    json.dumps(
                        {
                            "stage": "connected_waiting_for_ui",
                            "run_id": receipt["run_id"],
                        }
                    ),
                    flush=True,
                )
                # The normal working view owns the declared-input submission.
                # This helper keeps MCP live and only relays the next model task.
            else:
                choice = json.loads((state / "checkpoint-test-choice.json").read_text())
                evidence["test_choice"] = choice
                evidence["continuation_receipt"] = await call(
                    "wright_process_respond",
                    **respond_args,
                    value=choice,
                    request_id="desktop-checkpoint-selection-01",
                )
            await await_reply(state, evidence, evidence_file, call, scope, "second")
            final = await read_until(
                call,
                read_args,
                {"completed", "failed", "cancelled", "reconciliation_required"},
            )
            evidence["final_snapshot"] = final
            if (
                final["state"] != "completed"
                or final["context"]["run_id"] != receipt["run_id"]
            ):
                raise ValueError("Continuation did not complete the same durable run")
        evidence["stage"] = "completed"
    evidence_file.write_text(json.dumps(evidence, indent=2))
    print(
        json.dumps(
            {
                "stage": evidence["stage"],
                "run_id": evidence["start_receipt"]["run_id"],
                "evidence": str(evidence_file),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument(
        "--phase", choices=("start", "continue", "ui-continue"), required=True
    )
    args = parser.parse_args()
    asyncio.run(main(args.state_dir.resolve(strict=True), args.phase))
