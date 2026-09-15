"""Actual selected renderer probe using clean Wright GatewayService, no model call."""
import argparse
import asyncio
import base64
import json
from pathlib import Path
import shutil
import time

from core.redaction import redact_validation_payload
from tool_registry import McpServer
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_service import GatewayService, SUPPORTED_PROTOCOL_VERSION
from tool_registry.runners.stdio import StdioRunner
import qualify_stdio_mcp as helpers


async def run(args):
    root = Path(args.workspace)
    attempt = root / "campaign/pi-visual-qualification" / args.attempt
    inputs = attempt / "inputs"
    inputs.mkdir(parents=True)
    for name in ("pi_reference_mcp.py", "pi_reference_visual_mcp.py"):
        shutil.copyfile(Path(__file__).parent / name, inputs / name)
    source = (inputs / "pi_reference_visual_mcp.py").relative_to(root).as_posix()
    output = (attempt / "artifacts/research").relative_to(root).as_posix()
    command = json.loads(args.command_json) if args.command_json else ["/tmp/pi-visual-env/bin/python", "/operations/pi_reference_visual_mcp.py"]
    runner = StdioRunner(command, env={"WRIGHT_PI_REFERENCE_WORKSPACE": str(root)}, operation_timeout=300)
    records = []
    try:
        await runner.start()
        listed = await runner.list_tools()
        assert len(listed) == 3
        now = int(time.time())
        server = McpServer(server_id="pi-primary-visual-prerequisite", name="Pi visual prerequisite", type="stdio", command=command, is_installed=True, is_active=True, status="active", created_at=now, updated_at=now)
        gateway = GatewayService(workspaces=helpers._Workspaces(root, server.server_id), catalog=helpers._Catalog(server, listed), lifecycle=helpers._Lifecycle(runner), audit=helpers._Audit(), notifier=GatewayNotificationHub(), operation_timeout=300)
        gateway.open_session(session_id="visual-session", principal_id="visual-prerequisite", workspace_id="visual-workspace", transport="stdio")
        gateway.initialize_session("visual-session", protocol_version=SUPPORTED_PROTOCOL_VERSION, client_name="pi-visual-probe", client_version="1", client_capabilities={})
        records.append({"stage": "gateway_discovery", "tools": [t.name for t in gateway.list_tools("visual-session")]})

        async def call(name, arguments):
            result = await gateway.call_tool("visual-session", str(len(records)), server.server_id + "__" + name, arguments)
            if result.is_error:
                raise ValueError(result.meaningful_fallback())
            images = [block for block in result.content if block.get("type") == "image"]
            text = [block["text"] for block in result.content if block.get("type") == "text"]
            records.append({"stage": name, "arguments": arguments, "text": text, "structured": result.structured_content,
                            "images": [{"mime": block["mimeType"], "encoded_bytes": len(block["data"]), "decoded_bytes": len(base64.b64decode(block["data"], validate=True))} for block in images]})
            return result

        await call("retrieve_pi_primary_references", {"operation_source_document": source, "output_directory": output})
        for document, view in (("manufacturer-drawing.pdf", "full"), ("manufacturer-drawing.pdf", "top_left"), ("manufacturer-drawing.pdf", "bottom_right"), ("insert-dimensions.jpg", "full"), ("insert-installation.jpg", "full")):
            result = await call("observe_pi_primary_page", {"operation_source_document": source, "research_directory": output, "document_name": document, "page_number": 1, "view": view})
            assert sum(block.get("type") == "image" for block in result.content) == 1
        await call("read_pi_primary_text", {"operation_source_document": source, "research_directory": output, "document_name": "insert-product.html", "page_number": 1, "offset": 0})
        report = {"status": "passed_clean_wright_gateway_actual_rendering", "scope": "Actual source bytes/rendered image transport, not model interpretation or campaign execution", "records": records, "campaign_credit": 0}
    except Exception as failure:
        report = {"status": "failed", "error": str(failure), "records": records}
        raise
    finally:
        await runner.stop()
        (attempt / "qualification.json").write_text(json.dumps(redact_validation_payload(report), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "records": len(records), "evidence": str(attempt / "qualification.json")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default="/qualification")
    parser.add_argument("--attempt", required=True)
    parser.add_argument("--command-json")
    asyncio.run(run(parser.parse_args()))
