"""Opt-in selected-container native Wright gateway check using actual qualification artifacts."""
import argparse
import asyncio
import importlib.util
import json
from pathlib import Path
import time

from tool_registry import McpServer
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_service import GatewayService, SUPPORTED_PROTOCOL_VERSION
from tool_registry.runners.stdio import StdioRunner


async def run(args):
    root = Path(args.root)
    spec = importlib.util.spec_from_file_location("probe_helpers", root / "scripts/qualify_stdio_mcp.py")
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    case = args.case.rstrip("/")
    runner = StdioRunner(["/tmp/harness-env/bin/python", str(root / "scripts/harness_engineering_mcp.py")],
                         env={"PYTHONPATH": "", "WRIGHT_HARNESS_WORKSPACE": str(root)}, cwd=str(root), operation_timeout=150)
    try:
        await runner.start()
        tools = await runner.list_tools()
        now = int(time.time())
        server = McpServer(server_id="harness-probe", name="Harness selected probe", type="stdio", command=["selected"],
                           is_active=True, is_installed=True, status="active", created_at=now, updated_at=now)
        audit = helpers._Audit()
        gateway = GatewayService(workspaces=helpers._Workspaces(root, server.server_id), catalog=helpers._Catalog(server, tools),
                                 lifecycle=helpers._Lifecycle(runner), audit=audit, notifier=GatewayNotificationHub(), operation_timeout=150)
        gateway.open_session(session_id="qualification", principal_id="wright-validator", workspace_id="qualification-workspace", transport="stdio")
        gateway.initialize_session("qualification", protocol_version=SUPPORTED_PROTOCOL_VERSION, client_name="harness-probe", client_version="1", client_capabilities={})
        advertised = [tool.name for tool in gateway.list_tools("qualification")]
        arguments = {"input_directory": case+"/inputs", "research_directory": case+"/artifacts/research",
                     "generated_directory": case+"/artifacts/generated", "output_directory": case+"/artifacts/gateway-verified",
                     "operation_source_document": case+"/inputs/harness_engineering_operations.py"}
        result = await gateway.call_tool("qualification", "verify-actual-native-harness", "harness-probe__verify_harness_package", arguments)
        if result.is_error:
            raise ValueError(str(result.content))
        report = json.loads((root/arguments["output_directory"]/"verification.json").read_text())
        assert not report["netlist_and_numeric_failures"]
        assert report["release"] == "hold_for_missing_application_evidence"
        evidence = {"status": "passed_actual_gateway_execution", "scope": "Native GatewayService initialize/list/call; actual independent check of case03 native files",
                    "advertised_tools": advertised, "arguments": arguments, "result": result.structured_content,
                    "audit_events": audit.events, "campaign_runs": 0, "engineering_validation_complete": False}
        (root/args.output).write_text(json.dumps(evidence, indent=2, default=str)+"\n")
        print(json.dumps({"status": evidence["status"], "tools": len(advertised), "output": args.output}))
    finally:
        await runner.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--output", required=True)
    asyncio.run(run(parser.parse_args()))
