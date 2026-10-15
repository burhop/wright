"""Actual MCP action handoff through Wright's confined file-read runtime.

Private local setup seeds demonstration data and enrolls the existing exact
integration policy. Neither enrollment nor arbitrary file access is an MCP tool.
This protocol client relays actual desktop decisions; it contains no model.
"""

import argparse
import asyncio
import hashlib
import json
import sqlite3
from pathlib import Path
import sys

from data_vault import GatewayRepository, WorkspaceRepository
from data_vault.secret_provider import FileSecretProvider
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from workspace_service.workflow_integration_policy import (
    WorkflowIntegrationPolicyService,
)

from gateway_probe import INPUT, SOURCE
from checkpoint_probe import panel_request


async def main(
    state,
    qualified_read,
    *,
    native_working_view=False,
    enrolled_tasks=False,
    direct_tool=False,
):
    proof = state / "mcp-gateway-probe.json"
    if proof.exists():
        raise ValueError("Use fresh evidence; never replay an existing probe")
    established = json.loads((qualified_read / "probe.json").read_text())
    if (
        json.loads((qualified_read / "qualification.json").read_text())["status"]
        != "completed"
    ):
        raise ValueError("The prerequisite confined gateway proof did not complete")
    versions = json.loads((state / "desktop-versions.json").read_text())
    profile = "enrolled_mcp_tasks" if enrolled_tasks else "confined_inspection"
    if not versions.get(profile):
        raise ValueError(f"Required qualification profile is not enabled: {profile}")
    source = (
        SOURCE.replace('"max_tool_calls":1', '"max_tool_calls":2')
        if enrolled_tasks
        else SOURCE
    )
    if direct_tool:
        if not enrolled_tasks:
            raise ValueError("Direct tool proof requires the explicit enrolled profile")
        tool = established["allowed_tool"]
        settings = {
            "authoring_template": "mcp-tool",
            "mcp_server": tool["server_id"],
            "mcp_tool": tool["name"],
            "mcp_schema_digest": tool["schema_digest"],
            "mcp_arguments": json.dumps(
                {"relativePath": "inputs/requirements.md", "includeText": True}
            ),
            "output_format": "json",
            "output_filename": "outputs/probe/direct-inspection.json",
        }
        source += (
            '\ntask direct_inspect\n  name: "Declared direct input inspection"\n'
            '  purpose: "Inspect an exact enrolled input"\n  group: null\n  instructions: "Inspect only the specified file"\n'
            "  step_type: work\n  performed_by: configured_tool\n  tool: null\n"
            "  reusable_step: null\n  inputs: []\n"
            '  outputs: [{"key":"result","name":"Inspection","kind":"structured_result","item":null,"required":true,"quantity":"one","description":"Observed file evidence"}]\n'
            "  settings: " + json.dumps(settings) + "\nend\n"
        )
    if direct_tool:
        source += '\nconnection inspect_then_direct\n  type: order\n  from: "inspect"\n  to: "direct_inspect"\n  label: "Then inspect the same enrolled input directly"\n  when: null\nend\n'
    evidence = {
        "transport": "MCP protocol client; installed desktop plugin unverified",
        "calls": [],
        "native_working_view": native_working_view,
        "qualification_profile": profile,
        "direct_tool": direct_tool,
    }
    parameters = StdioServerParameters(
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
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            initialized = await session.initialize()
            evidence["protocol_version"] = initialized.protocolVersion
            evidence["tools"] = [
                tool.name for tool in (await session.list_tools()).tools
            ]

            async def call(tool_name, *, expect_error=False, **arguments):
                name, payload = (
                    panel_request(tool_name, arguments)
                    if native_working_view
                    else (tool_name, arguments)
                )
                result = await session.call_tool(name, payload)
                document = (
                    None
                    if result.isError
                    else (
                        result.structuredContent or json.loads(result.content[0].text)
                    )
                )
                owner_denied = (
                    name in ("wright_process_ui_read", "wright_process_ui_update")
                    and document
                    and document.get("ok") is False
                )
                evidence["calls"].append(
                    {
                        "tool": name,
                        "logical_operation": tool_name,
                        "is_error": result.isError,
                        "owner_denied": bool(owner_denied),
                    }
                )
                proof.write_text(json.dumps(evidence, indent=2))
                if bool(result.isError or owner_denied) != expect_error:
                    raise ValueError(
                        f"Unexpected {tool_name} outcome: {result.content}"
                    )
                if expect_error:
                    if owner_denied:
                        return document
                    return [item.model_dump(mode="json") for item in result.content]
                return (
                    document["document"]
                    if name in ("wright_process_ui_read", "wright_process_ui_update")
                    else document
                )

            workspace = await call(
                "wright_workspace_create", name="Desktop MCP Gateway Proof"
            )
            evidence["workspace"] = workspace
            scope = {
                "workspace_id": workspace["workspace_id"],
                "session_id": workspace["session_id"],
            }
            document = await call(
                "wright_workflow_create",
                **scope,
                path="workflows/desktop-gateway.workflow.wflow",
                source=source,
            )
            evidence["source"] = document
            # Explicit private fixture setup, never a model-generated read or
            # permission grant. Source and input hashes remain canonical.
            repo = WorkspaceRepository(
                str(state / "wright.sqlite"),
                secrets=FileSecretProvider(state / "credentials.json"),
            )
            root = Path(
                repo.get_by_session(workspace["session_id"])["local_path"]
            ).resolve(strict=True)
            if not root.is_relative_to(state / "workspaces"):
                raise ValueError("Fixture setup is outside the private prototype")
            (root / "inputs").mkdir(exist_ok=True)
            (root / "inputs/requirements.md").write_text(INPUT)
            input_hash = hashlib.sha256(INPUT.encode()).hexdigest()
            prepared = await call(
                "wright_process_prepare",
                **scope,
                path=document["path"],
                source_digest=document["storage_digest"],
                bindings=[],
            )
            evidence["input_snapshot"] = prepared
            start = dict(
                scope,
                path=document["path"],
                source_digest=document["storage_digest"],
                input_snapshot_id=prepared["snapshot_id"],
                input_digest=prepared["digest"],
            )
            evidence["no_grant_denial"] = await call(
                "wright_process_start",
                **start,
                request_id="desktop-gateway-no-grant",
                expect_error=True,
            )
            if (
                native_working_view
                and evidence["no_grant_denial"].get("http_status") != 403
                or not native_working_view
                and "(403)" not in json.dumps(evidence["no_grant_denial"])
            ):
                raise ValueError(
                    "The no-grant control did not prove an authority denial"
                )
            policies = WorkflowIntegrationPolicyService(
                str(state / "wright.sqlite"), enabled=True
            )
            grant = policies.enroll(
                campaign_id="desktop-harness-digital-prototype",
                dataset_id="confined-file-read",
                dataset_digest=input_hash,
                workspace_id=workspace["workspace_id"],
                source_path=document["path"],
                source_digest=document["storage_digest"],
                input_files={"inputs/requirements.md": input_hash},
                output_root="outputs/probe",
                allowed_tools=[established["allowed_tool"]],
                approval_mode="manual",
            )
            evidence["private_setup"] = {
                "integration_policy_digest": grant,
                "input_sha256": input_hash,
                "authority": "local test enrollment; no engineering approval",
            }
            receipt = await call(
                "wright_process_start",
                **start,
                request_id="desktop-gateway-permitted-start",
                integration_policy_digest=grant,
            )
            evidence["start_receipt"] = receipt
            read_args = dict(
                scope,
                path=document["path"],
                source_digest=document["storage_digest"],
                run_id=receipt["run_id"],
            )
            for ordinal in (1, 2):
                async with asyncio.timeout(30):
                    while True:
                        pending = await call("wright_reasoning_pending", **scope)
                        if any(
                            item["request"]["run_id"] == receipt["run_id"]
                            and item["request"]["ordinal"] == ordinal
                            for item in pending["tasks"]
                        ):
                            break
                        await asyncio.sleep(0.1)
                task = next(
                    item
                    for item in pending["tasks"]
                    if item["request"]["run_id"] == receipt["run_id"]
                    and item["request"]["ordinal"] == ordinal
                )
                if (
                    task["request"]["kind"] != "action"
                    or task["request"]["ordinal"] != ordinal
                ):
                    raise ValueError("Unexpected desktop request identity")
                evidence[f"pending_{ordinal}"] = task
                proof.write_text(json.dumps(evidence, indent=2))
                print(
                    json.dumps(
                        {
                            "stage": "awaiting_desktop_action",
                            "ordinal": ordinal,
                            "workspace": workspace,
                            "task": task,
                        },
                        indent=2,
                    ),
                    flush=True,
                )
                answer_file = state / f"desktop-gateway-action-{ordinal}.json"
                async with asyncio.timeout(550):
                    while not answer_file.exists():
                        await asyncio.sleep(0.25)
                evidence[f"answer_{ordinal}"] = await call(
                    "wright_reasoning_action",
                    **scope,
                    **json.loads(answer_file.read_text()),
                )
            async with asyncio.timeout(30):
                while True:
                    snapshot = await call("wright_process_read", **read_args)
                    if snapshot["state"] != "running":
                        break
                    await asyncio.sleep(0.1)
            evidence["final_snapshot"] = snapshot
            evidence["input_unchanged"] = (
                hashlib.sha256(
                    (root / "inputs/requirements.md").read_bytes()
                ).hexdigest()
                == input_hash
            )
            # Retain observable gateway events separately; do not treat tool
            # discovery as proof that a tool was dispatched.
            audit = GatewayRepository(str(state / "wright.sqlite"))
            with sqlite3.connect(
                f"file:{state / 'wright.sqlite'}?mode=ro", uri=True
            ) as database:
                sessions = database.execute(
                    "SELECT DISTINCT session_id FROM gateway_audit_events WHERE workspace_id = ?",
                    (workspace["workspace_id"],),
                ).fetchall()
            events = [
                event
                for (session_id,) in sessions
                for event in audit.list_audit(session_id)
            ]
            (state / "mcp-gateway-audit.json").write_text(json.dumps(events, indent=2))
            evidence["dispatch_count"] = sum(
                e["operation"] == "tool.call" and e["outcome"] == "succeeded"
                for e in events
            )
            proof.write_text(json.dumps(evidence, indent=2))
            print(
                json.dumps(
                    {
                        "stage": snapshot["state"],
                        "run_id": receipt["run_id"],
                        "dispatch_count": evidence["dispatch_count"],
                        "input_unchanged": evidence["input_unchanged"],
                    }
                ),
                flush=True,
            )
            if (
                snapshot["state"] != "completed"
                or evidence["dispatch_count"] != (2 if direct_tool else 1)
                or not evidence["input_unchanged"]
            ):
                raise ValueError("The confined MCP journey was not qualified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument("--qualified-read", required=True, type=Path)
    parser.add_argument("--native-working-view", action="store_true")
    parser.add_argument("--enrolled-tasks", action="store_true")
    parser.add_argument("--direct-tool", action="store_true")
    args = parser.parse_args()
    asyncio.run(
        main(
            args.state_dir.resolve(strict=True),
            args.qualified_read.resolve(strict=True),
            native_working_view=args.native_working_view,
            enrolled_tasks=args.enrolled_tasks,
            direct_tool=args.direct_tool,
        )
    )
