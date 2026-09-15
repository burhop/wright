"""Explicit clean Wright / selected CalculiX recorded backend and resource probe."""
from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import time
import urllib.request
import urllib.error

from core.redaction import redact_mapping
from tool_registry import McpServer
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_service import GatewayService, SUPPORTED_PROTOCOL_VERSION


class CurrentHttpRunner:
    """Qualification-only explicit stateless 2026 transport, no production patch."""
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.sequence = 0

    async def rpc(self, method, params=None):
        self.sequence += 1
        params = {**(params or {}), "_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28",
                                            "io.modelcontextprotocol/clientCapabilities": {}}}
        request = urllib.request.Request(self.endpoint, method="POST",
            data=json.dumps({"jsonrpc": "2.0", "id": self.sequence, "method": method, "params": params}).encode(),
            headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
                     "MCP-Protocol-Version": "2026-07-28", "Mcp-Method": method})
        if "name" in params:
            request.add_header("Mcp-Name", params["name"])
        if "uri" in params:
            request.add_header("Mcp-Name", params["uri"])
        def receive():
            try:
                with urllib.request.urlopen(request, timeout=150) as response:
                    result = json.load(response)
            except urllib.error.HTTPError as error:
                raise ValueError(error.read().decode()) from error
            if "error" in result:
                raise ValueError(str(result["error"]))
            return result["result"]
        return await asyncio.to_thread(receive)

    async def start(self):
        return await self.rpc("server/discover")

    def is_running(self):
        return True

    async def stop(self):
        pass

    async def list_tools(self):
        return (await self.rpc("tools/list"))["tools"]

    async def call_tool(self, name, arguments, progress_callback=None):
        result = await self.rpc("tools/call", {"name": name, "arguments": arguments})
        if result.get("isError"):
            raise ValueError(str(result))
        return result


async def run(args):
    spec = importlib.util.spec_from_file_location("probe_helpers", args.helpers)
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)
    root = Path(args.evidence_root) / args.attempt
    if root.exists():
        raise ValueError("Qualification attempt already exists")
    root.mkdir(parents=True)
    runner = CurrentHttpRunner(args.endpoint)
    discovery = await runner.start()
    tools = await runner.list_tools()
    (root / "tools.json").write_text(json.dumps(tools, indent=2))
    now = int(time.time())
    server = McpServer(server_id="casys-calculix-probe", name="Casys CalculiX probe", type="sse",
                       command=args.endpoint, is_active=True, is_installed=True, status="active",
                       created_at=now, updated_at=now)
    gateway = GatewayService(workspaces=h._Workspaces(root, server.server_id), catalog=h._Catalog(server, tools),
                             lifecycle=h._Lifecycle(runner), audit=h._Audit(), notifier=GatewayNotificationHub(), operation_timeout=150)
    gateway.open_session(session_id="qualification", principal_id="wright-validator", workspace_id="qualification-workspace", transport="stdio")
    gateway.initialize_session("qualification", protocol_version=SUPPORTED_PROTOCOL_VERSION, client_name="calculix-probe", client_version="1", client_capabilities={})
    assert "casys-calculix-probe__calculix_solve_static_recorded" in [t.name for t in gateway.list_tools("qualification")]
    step_sha = hashlib.sha256(Path(args.input_step).read_bytes()).hexdigest()
    base = {"step_path": "/exports/qualification/probe.step", "expected_step_sha256": step_sha,
            "mesh_size_mm": 3, "element_order": 2, "material": {"e_mpa": 69000, "nu": .33},
            "selections": [{"name": "FIXED", "box": {"min": [-.001, -.001, -.001], "max": [.001, 10.001, 4.001]}},
                           {"name": "LOADED", "box": {"min": [19.999, -.001, -.001], "max": [20.001, 10.001, 4.001]}}],
            "fixed": ["FIXED"], "loads": [{"selection": "LOADED", "force_n": [0, 0, -1]}]}
    outcomes = []
    for route in ("direct", "gateway"):
        arguments = {**base, "request_id": "wright-" + args.attempt + "-" + route}
        if route == "direct":
            response = await runner.call_tool("calculix_solve_static_recorded", arguments)
            structured = response.get("structuredContent")
        else:
            response = await gateway.call_tool("qualification", route, "casys-calculix-probe__calculix_solve_static_recorded", arguments)
            if response.is_error:
                raise ValueError(str(response.content))
            structured = response.structured_content
        if not structured or not structured.get("run"):
            raise ValueError("Missing actual recorded solver result: " + str(structured))
        (root / (route + "-result.json")).write_text(json.dumps(structured, indent=2))
        target = root / route
        target.mkdir()
        artifacts = []
        for item in structured["run"]["artifacts"]:
            result = await runner.rpc("resources/read", {"uri": item["uri"]})
            content = result["contents"][0]
            data = content["text"].encode() if "text" in content else base64.b64decode(content["blob"])
            assert len(data) == item["bytes"] and hashlib.sha256(data).hexdigest() == item["sha256"]
            (target / item["name"]).write_bytes(data)
            artifacts.append({k: item[k] for k in ("name", "bytes", "sha256", "uri")})
        dat = (target / "job.dat").read_text()
        assert "displacements" in dat and "stresses" in dat
        outcomes.append({"route": route, "run_id": structured["run"]["runId"], "artifacts": artifacts})
    evidence = {"status": "passed", "scope": "clean Wright HTTP2026 direct and GatewayService recorded static/resources",
                "clean_wright_image": "sha256:512b001cbffd0551969630eaf618d9d4fb72987bdfb6422d9d444d8ad2e8ee73",
                "selected_image": "ghcr.io/casys-ai/mcp-calculix@sha256:82ce8628279e03c8f492f156bb928e5703ea1fcb2d7c465826faf38f7389a778",
                "discovery": discovery, "tool_count": len(tools), "outcomes": outcomes, "campaign_runs": 0,
                "limitations": ["Qualification-only current-protocol adapter, production integration uses upstream compatible stdio.",
                                "Actual DAT has full U/S fields; this probe does not check engineering correctness or output RF."]}
    (root / "evidence.json").write_text(json.dumps(redact_mapping(evidence), indent=2) + "\n")
    print(json.dumps({"status": "passed", "tools": len(tools), "evidence": str(root / "evidence.json")}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="http://127.0.0.1:3015/mcp")
    parser.add_argument("--attempt", required=True)
    parser.add_argument("--helpers", required=True)
    parser.add_argument("--evidence-root", required=True)
    parser.add_argument("--input-step", required=True)
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
