"""Run actual reference retrieval and collection through a clean selected MCP."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
import time

from tool_registry import McpServer
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_service import GatewayService, SUPPORTED_PROTOCOL_VERSION
from tool_registry.runners.stdio import StdioRunner

ROOT = Path(__file__).resolve().parents[1]


async def run(args):
    root = Path(args.output).resolve()
    if root.exists():
        raise ValueError("Choose a fresh qualification directory")
    operation = ROOT / "scripts/engineering_evidence_mcp.py"
    for route in ("direct", "gateway"):
        source = root / route / "inputs/operation.py"
        source.parent.mkdir(parents=True)
        source.write_bytes(operation.read_bytes())
    spec = importlib.util.spec_from_file_location("qualification", ROOT / "scripts/qualify_stdio_mcp.py")
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    command = ["docker", "run", "--rm", "-i", "--entrypoint", "python",
               "-v", f"{root.as_posix()}:/work",
               "-v", f"{operation.as_posix()}:/opt/engineering_evidence_mcp.py:ro",
               "-e", "WRIGHT_EVIDENCE_WORKSPACE=/work",
               "-e", 'WRIGHT_EVIDENCE_ORIGINS=["https://sendcutsend.com"]',
               args.image, "/opt/engineering_evidence_mcp.py"]
    runner = StdioRunner(command, cwd=str(ROOT), operation_timeout=240)
    result = {"environment": "clean-selected-container", "image": args.image,
              "operation_sha256": hashlib.sha256(operation.read_bytes()).hexdigest(), "routes": [],
              "status": "running", "campaign_execution": False}
    try:
        await runner.start()
        tools = await runner.list_tools()
        (root / "tools.json").write_text(json.dumps(tools, indent=2))
        now = int(time.time())
        server = McpServer(server_id="engineering-evidence-probe", name="Evidence probe", type="stdio",
            command=command, is_active=True, is_installed=True, status="active", created_at=now,
            updated_at=now, risk_level="read-only", default_enabled=False)
        gateway = GatewayService(workspaces=helpers._Workspaces(root, server.server_id),
            catalog=helpers._Catalog(server, tools), lifecycle=helpers._Lifecycle(runner),
            audit=helpers._Audit(), notifier=GatewayNotificationHub(), operation_timeout=240, maximum_timeout=240)
        gateway.open_session(session_id="qualification", principal_id="wright-validator",
                             workspace_id="qualification-workspace", transport="stdio")
        gateway.initialize_session("qualification", protocol_version=SUPPORTED_PROTOCOL_VERSION,
                                  client_name="evidence-probe", client_version="1", client_capabilities={})
        if len(gateway.list_tools("qualification")) != 3:
            raise ValueError("All three selected operations must be discoverable")
        urls = json.loads((ROOT / "tests/datasets/engineering-workflows/bindings/sheet-metal-supplier-handoff.json").read_text())["supplier_sources"]
        for route in ("direct", "gateway"):
            arguments = {"operation_source_document": route + "/inputs/operation.py",
                         "output_root": route + "/artifacts", "urls": urls}
            async def call(name, payload):
                if route == "direct":
                    returned = await runner.call_tool(name, payload)
                    if returned.get("isError"):
                        raise ValueError("Direct operation failed: " + str(returned))
                    return returned
                returned = await gateway.call_tool("qualification", route + "-" + name,
                    server.server_id + "__" + name, payload)
                if returned.is_error:
                    raise ValueError("Gateway operation failed: " + str(returned.structured_content))
                return {"content": list(returned.content), "structuredContent": returned.structured_content}
            fetched = await call("retrieve_public_references", arguments)
            (root / route / "retrieval-result.json").write_text(json.dumps(fetched, indent=2, default=str))
            actual = fetched.get("structuredContent")
            if actual is None:
                actual = json.loads(next(c["text"] for c in fetched["content"] if c.get("type") == "text"))
            if len(json.dumps(actual, indent=2)) > 4000:
                raise ValueError("Retrieval observation exceeds the compact contract")
            for content in fetched.get("content", []):
                if content.get("type") == "text" and len(content["text"]) > 4000:
                    raise ValueError("Native retrieval text block exceeds 4000 characters")
            manifest_path = root / route / "artifacts/supplier-evidence.json"
            if hashlib.sha256(manifest_path.read_bytes()).hexdigest() != actual["evidence_sha256"]:
                raise ValueError("Returned evidence hash differs from retained manifest")
            read_arguments = {k:v for k,v in arguments.items() if k != "urls"} | {
                "source_index": 1, "expected_evidence_sha256": actual["evidence_sha256"],
                "offset": 0, "max_chars": 3000}
            pages = []
            for page_number in range(2):
                read = await call("read_reference_text", read_arguments)
                page = read.get("structuredContent") or json.loads(next(c["text"] for c in read["content"] if c.get("type") == "text"))
                full = (root / route / "artifacts/supplier-source-1.txt").read_text(encoding="utf-8")
                if page["text"] != full[page["start_offset"]:page["end_offset"]]:
                    raise ValueError("Paged excerpt differs from actual retained source text")
                if len(json.dumps(page, indent=2)) > 4000 or any(len(c.get("text", "")) > 4000 for c in read["content"]):
                    raise ValueError("Paged observation exceeds 4000 characters")
                pages.append(page)
                if page["next_offset"] is None:
                    break
                read_arguments["offset"] = page["next_offset"]
            searched = await call("read_reference_text", read_arguments | {"offset": 0, "query": "bending", "max_chars": 1200})
            pages.append(searched.get("structuredContent") or json.loads(next(c["text"] for c in searched["content"] if c.get("type") == "text")))
            (root / route / "paged-text-results.json").write_text(json.dumps(pages, indent=2))
            files = [{"path": route + "/artifacts/supplier-evidence.json", "role": "retrieved source metadata"}]
            files += [{"path": route + f"/artifacts/supplier-source-{i+1}.html", "role": "official reference"} for i in range(len(urls))]
            files += [{"path": route + f"/artifacts/supplier-source-{i+1}.txt", "role": "complete extracted reference text"} for i in range(len(urls))]
            collected = await call("collect_artifact_manifest", {k:v for k,v in arguments.items() if k != "urls"} | {"files": files})
            (root / route / "collection-result.json").write_text(json.dumps(collected, indent=2, default=str))
            final = json.loads((root / route / "artifacts/final-artifact-manifest.json").read_text())
            if len(final["files"]) != 2 * len(urls) + 1 or any(f["bytes"] <= 0 for f in final["files"]):
                raise ValueError("Actual retrieved output files are incomplete")
            result["routes"].append({"route": route, "status": "passed", "files": len(final["files"]),
                                     "tool_count": 3, "paged_reads": len(pages), "maximum_retrieval_characters": len(json.dumps(actual, indent=2)),
                                     "maximum_excerpt_characters": max(len(json.dumps(p, indent=2)) for p in pages)})
        result["status"] = "passed"
    except Exception as error:
        result.update(status="failed", error_type=type(error).__name__, error=str(error)[:3000])
        raise
    finally:
        await runner.stop()
        (root / "qualification.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", required=True)
    print(json.dumps(asyncio.run(run(parser.parse_args())), indent=2))
