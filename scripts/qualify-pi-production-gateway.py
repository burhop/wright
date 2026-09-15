"""Explicit selected production-transport GatewayService prerequisite, never a Pi dataset run."""
import argparse
import asyncio
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
for source in (ROOT/"packages").glob("*/src"):
    sys.path.insert(0, str(source))

async def run(args):
    from core.redaction import redact_mapping
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    from tool_registry import McpServer
    from tool_registry.gateway_notifications import GatewayNotificationHub
    from tool_registry.gateway_service import GatewayService, SUPPORTED_PROTOCOL_VERSION
    from tool_registry.runners.stdio import StdioRunner

    spec = importlib.util.spec_from_file_location("pi_native_gateway_helpers", ROOT/"scripts/qualify_stdio_mcp.py")
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    workspace = Path(args.workspace).resolve()
    attempt = workspace/"campaign/pi-production-qualification"/args.attempt
    inputs, output = attempt/"inputs", attempt/"artifacts"
    inputs.mkdir(parents=True)
    output.mkdir()
    for source in [ROOT/"scripts"/name for name in ("pi_cfd_operations.py", "pi_cfd_mcp.py", "pi_reference_mcp.py")]+[ROOT/"scripts/pi_foam_boundary/wrightPrghFanPressure.C"]:
        shutil.copyfile(source, inputs/source.name)
    contracts = []
    prior = ROOT/".local-run/feature-081-live/pi-fixed-qualification"
    for ordinal, original_case in enumerate(("probe-002", "probe-fan-001")):
        document = json.loads((prior/original_case/"contract.json").read_text())
        for region in document["regions"]:
            destination = output/f"prerequisite-{'ab'[ordinal]}-{region['name']}.step"
            shutil.copyfile(prior/region["step"], destination)
            region["step"] = destination.relative_to(workspace).as_posix()
        target = output/f"thermal-contract-{'ab'[ordinal]}.json"
        target.write_text(json.dumps(document, indent=2))
        contracts.append(target.relative_to(workspace).as_posix())
    identities = json.loads(Path(args.registration).read_text())["server_map"]
    base = ["docker", "exec", "-i", "-e", "PYTHONPATH="]
    interpreter = "/opt/conda/envs/FoamAgent/bin/python"
    commands = {
        "references": base+["-e", "WRIGHT_PI_REFERENCE_WORKSPACE=/demo", "wright-081-pi-runtime", interpreter, "/operations/pi_reference_mcp.py"],
        "cfd": base+["-e", "WRIGHT_PI_CFD_WORKSPACE=/demo", "-e", "WRIGHT_PI_CFD_FOAM_ROOT=/workspace", "wright-081-pi-runtime", interpreter, "/operations/pi_cfd_mcp.py"],
    }
    runners = []
    gateways = {}
    records = []
    relative = attempt.relative_to(workspace).as_posix()
    try:
        for alias, command in commands.items():
            identity = identities["wright-campaign-pi-"+alias]
            runner = StdioRunner(command, cwd=str(ROOT), operation_timeout=600)
            runners.append(runner)
            await runner.start()
            tools = await runner.list_tools()
            now = int(time.time())
            server = McpServer(server_id=identity, name="Pi production "+alias, type="stdio", command=command, is_active=True, is_installed=True, status="active", created_at=now, updated_at=now)
            gateway = GatewayService(workspaces=helpers._Workspaces(workspace, identity), catalog=helpers._Catalog(server, tools), lifecycle=helpers._Lifecycle(runner), audit=helpers._Audit(), notifier=GatewayNotificationHub(), operation_timeout=600)
            gateway.open_session(session_id="qualification", principal_id="wright-validator", workspace_id="qualification-workspace", transport="stdio")
            gateway.initialize_session("qualification", protocol_version=SUPPORTED_PROTOCOL_VERSION, client_name="pi-production-probe", client_version="1", client_capabilities={})
            gateways[alias] = (gateway, identity)
            records.append({"stage": "gateway_discovery", "server_id": identity, "tools": [tool.name for tool in gateway.list_tools("qualification")], "command": command})
        async def call(alias, name, arguments):
            gateway, identity = gateways[alias]
            result = await gateway.call_tool("qualification", name, identity+"__"+name, arguments)
            if result.is_error:
                raise ValueError(str(result.content))
            records.append({"stage": name, "result": result.structured_content})
            return result
        reference_args = {"operation_source_document": relative+"/inputs/pi_reference_mcp.py", "output_directory": relative+"/artifacts/research"}
        await call("references", "retrieve_pi_manufacturer_references", reference_args)
        for filename, page in (("manufacturer-drawing.pdf", 1), ("manufacturer-product-brief.pdf", 3), ("manufacturer-cooler-drawing.pdf", 1)):
            await call("references", "read_pi_reference_page", {"operation_source_document": reference_args["operation_source_document"], "research_directory": reference_args["output_directory"], "document_name": filename, "page_number": page, "offset": 0})
        arguments = {"operation_source_document": relative+"/inputs/pi_cfd_operations.py", "output_directory": relative+"/artifacts"}
        await call("cfd", "prepare_pi_cfd_comparison", {**arguments, "contract_documents": contracts})
        preparation = json.loads((output/"cfd-preparation.json").read_text())
        # Real existing Foam-Agent HTTP tool; only this independent scratch case is dispatched.
        async with streamablehttp_client("http://127.0.0.1:7860/mcp") as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("run", {"request": {"case_dir": preparation["foam_case_dir"], "timeout": 240}})
                if result.isError or (result.structuredContent or {}).get("errors"):
                    raise ValueError(str(result))
                records.append({"stage": "production_foam_agent_run", "result": result.model_dump(mode="json")})
        await call("cfd", "collect_pi_cfd_comparison", arguments)
        comparison = json.loads((output/"cfd-comparison.json").read_text())
        evidence = {"status": "passed_production_transport_gateway_pipeline", "scope": "Independent OCC prerequisite geometry through real selected companion and native Foam run; not Pi campaign", "records": records, "variants": comparison["variants"], "field_archive_sha256": comparison["field_archive_sha256"], "campaign_credit": 0, "content_validity_credit": 0}
        Path(args.evidence).write_text(json.dumps(redact_mapping(evidence), indent=2, default=str)+"\n", encoding="utf-8")
        print(json.dumps({"status": evidence["status"], "evidence": args.evidence}))
    finally:
        for runner in reversed(runners):
            await runner.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--registration", required=True)
    parser.add_argument("--attempt", required=True)
    parser.add_argument("--evidence", required=True)
    asyncio.run(run(parser.parse_args()))
